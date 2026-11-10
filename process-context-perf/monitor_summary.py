#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Summarize host monitor counters over explicitly accepted checkpoint windows.

This reader does not run benchmarks or change their inputs. Rates come from
adjacent raw counter snapshots, never from the monitor's precomputed ``deltas``.
Use ``summarize(Path(...), [{"name": ..., "start": ..., "end": ...}])`` or the
CLI, which obtains its exact checkpoint allowlist from report.checkpoint_plan().
"""

import argparse
from bisect import bisect_left, bisect_right
from datetime import datetime, timezone
import gzip
import json
import math
from pathlib import Path
import sys


DEFAULT_MONITOR = Path("/tmp/process-context-host-monitor-20261109.jsonl")
CPU_FIELDS = ("user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal")
METRICS = (
    "cpu3.steal_percent", "cpu11.execution_busy_percent",
    "host_cpu_pressure.some", "host_cpu_pressure.full",
    "session_cpu_pressure.some", "session_cpu_pressure.full",
    "session_cpu_stat.nr_throttled", "session_cpu_stat.throttled_usec",
)
COUNTER_METRICS = set(METRICS[-2:])
EPSILON_SECONDS = 0.000001


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _finite(value, context):
    valid = isinstance(value, (int, float)) and not isinstance(value, bool)
    try:
        valid = valid and math.isfinite(value)
    except OverflowError:
        valid = False
    _require(valid, f"{context}: expected a finite number")
    return value


def _counter(value, context):
    _require(isinstance(value, int) and not isinstance(value, bool) and value >= 0,
             f"{context}: expected a nonnegative integer counter")


def _time(value, context):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        _finite(value, context)
        try:
            return datetime.fromtimestamp(value, timezone.utc)
        except (ValueError, OverflowError, OSError) as error:
            raise ValueError(f"{context}: invalid Unix timestamp") from error
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError(f"{context}: invalid ISO timestamp") from error
    _require(isinstance(value, datetime) and value.tzinfo is not None
             and value.utcoffset() is not None, f"{context}: timestamp must include a timezone")
    return value.astimezone(timezone.utc)


def _iso(timestamp):
    return timestamp.isoformat().replace("+00:00", "Z")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json(text, context):
    try:
        value = json.loads(text, object_pairs_hook=_unique_object,
                           parse_constant=lambda item: (_ for _ in ()).throw(ValueError(f"Nonfinite JSON number: {item}")))
    except ValueError as error:
        raise ValueError(f"{context}: {error}") from error
    _require(isinstance(value, dict), f"{context}: expected a JSON object")
    def check_floats(item):
        if isinstance(item, float):
            _finite(item, context)
        elif isinstance(item, dict):
            for child in item.values():
                check_floats(child)
        elif isinstance(item, list):
            for child in item:
                check_floats(child)
    check_floats(value)
    return value


def _optional_object(parent, key, context):
    value = parent.get(key)
    _require(value is None or isinstance(value, dict), f"{context}.{key}: expected an object or null")
    return value or {}


def _validate_sample(record, context):
    timestamp = _time(record.get("utc"), context + ".utc")
    monotonic = _finite(record.get("monotonic"), context + ".monotonic")
    _require(monotonic >= 0, context + ".monotonic: expected a nonnegative value")
    cpus = _optional_object(record, "cpus_ticks", context)
    for name, counters in cpus.items():
        _require(isinstance(counters, dict), f"{context}.cpus_ticks.{name}: expected an object")
        for key, value in counters.items():
            _counter(value, f"{context}.cpus_ticks.{name}.{key}")
    for family in ("host_cpu_pressure", "session_cpu_pressure"):
        pressure = _optional_object(record, family, context)
        for mode, counters in pressure.items():
            _require(isinstance(counters, dict), f"{context}.{family}.{mode}: expected an object")
            for key, value in counters.items():
                if key == "total":
                    _counter(value, f"{context}.{family}.{mode}.{key}")
                else:
                    _require(_finite(value, f"{context}.{family}.{mode}.{key}") >= 0,
                             f"{context}.{family}.{mode}.{key}: expected a nonnegative value")
    counters = _optional_object(record, "session_cpu_stat", context)
    for key, value in counters.items():
        _counter(value, f"{context}.session_cpu_stat.{key}")
    if "deltas" in record:
        _require(isinstance(record["deltas"], dict), f"{context}.deltas: expected an object")
    return {"utc": timestamp, "monotonic": monotonic, "raw": record}


def _read_monitor(path):
    metadata, samples, intervals, issues = [], [], [], []
    previous = None
    stopped = False
    line_count = 0
    opener = gzip.open if Path(path).suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        for line_count, line in enumerate(stream, 1):
            context = f"{path}:{line_count}"
            _require(bool(line.strip()), context + ": empty JSONL record")
            record = _read_json(line, context)
            kind = record.get("kind")
            if kind == "metadata":
                affinity = record.get("monitor_affinity")
                _require(isinstance(affinity, list) and bool(affinity)
                         and all(isinstance(cpu, int) and not isinstance(cpu, bool) and cpu >= 0 for cpu in affinity)
                         and len(set(affinity)) == len(affinity), context + ": invalid monitor_affinity")
                _require(_finite(record.get("interval_seconds"), context + ".interval_seconds") > 0,
                         context + ": interval_seconds must be positive")
                _counter(record.get("clock_ticks_per_second"), context + ".clock_ticks_per_second")
                _require(record["clock_ticks_per_second"] > 0, context + ": clock ticks must be positive")
                _time(record.get("started_utc"), context + ".started_utc")
                metadata.append(record)
                previous = None  # Never derive deltas across monitor restarts.
                stopped = False
                continue
            _require(bool(metadata), context + ": sample or stop record before metadata")
            if kind == "stopped":
                _time(record.get("utc"), context + ".utc")
                _require(_finite(record.get("elapsed_seconds"), context + ".elapsed_seconds") >= 0,
                         context + ": elapsed_seconds must be nonnegative")
                _require(not stopped, context + ": duplicate stop record")
                stopped = True
                previous = None
                continue
            _require(kind == "sample", context + f": unsupported record kind {kind!r}")
            _require(not stopped, context + ": sample after stopped record without new metadata")
            current = _validate_sample(record, context)
            if samples:
                _require(current["utc"] > samples[-1]["utc"], context + ": sample UTC timestamps must increase")
            samples.append(current)
            if previous is not None:
                _require(current["monotonic"] > previous["monotonic"],
                         context + ": monotonic timestamps must increase within each monitor session")
                interval = _interval(previous, current, issues)
                nominal = metadata[-1]["interval_seconds"]
                interval["long_interval"] = interval["wall_seconds"] > nominal * 1.5
                intervals.append(interval)
            previous = current
    _require(bool(metadata), f"{path}: missing metadata")
    _require(len(samples) >= 2 and bool(intervals), f"{path}: need at least two adjacent samples in one monitor session")
    return metadata, samples, intervals, issues, line_count


def _interval(previous, current, issues):
    wall_seconds = (current["utc"] - previous["utc"]).total_seconds()
    elapsed = current["monotonic"] - previous["monotonic"]
    interval = {"start": previous["utc"], "end": current["utc"],
                "wall_seconds": wall_seconds, "monotonic_seconds": elapsed, "values": {}}

    def unavailable(metric, code, detail):
        interval["values"][metric] = None
        issues.append({"metric": metric, "code": code, "detail": detail,
                       "start": _iso(previous["utc"]), "end": _iso(current["utc"])})

    for cpu, metric in (("cpu3", METRICS[0]), ("cpu11", METRICS[1])):
        before = (previous["raw"].get("cpus_ticks") or {}).get(cpu, {})
        after = (current["raw"].get("cpus_ticks") or {}).get(cpu, {})
        missing = [key for key in CPU_FIELDS if key not in before or key not in after]
        if missing:
            unavailable(metric, "missing_counter", "Missing CPU counters: " + ", ".join(missing))
            continue
        deltas = {key: after[key] - before[key] for key in CPU_FIELDS}
        reset = [key for key, value in deltas.items() if value < 0]
        if reset:
            unavailable(metric, "counter_reset", "Decreasing CPU counters: " + ", ".join(reset))
            continue
        total = sum(deltas.values())  # guest/guest_nice are already included in user/nice.
        if total <= 0:
            unavailable(metric, "zero_cpu_ticks", "CPU total counter did not advance")
            continue
        numerator = deltas["steal"] if cpu == "cpu3" else total - deltas["idle"] - deltas["iowait"] - deltas["steal"]
        interval["values"][metric] = {"rate": 100.0 * numerator / total}
    for family in ("host_cpu_pressure", "session_cpu_pressure"):
        for mode in ("some", "full"):
            metric = family + "." + mode
            before = ((previous["raw"].get(family) or {}).get(mode) or {}).get("total")
            after = ((current["raw"].get(family) or {}).get(mode) or {}).get("total")
            if before is None or after is None:
                unavailable(metric, "missing_counter", "Missing PSI total counter at one or both endpoints")
            elif after < before:
                unavailable(metric, "counter_reset", "PSI total counter decreased")
            else:
                interval["values"][metric] = {"rate": 100.0 * (after - before) / (elapsed * 1_000_000)}
    for field in ("nr_throttled", "throttled_usec"):
        metric = "session_cpu_stat." + field
        before = (previous["raw"].get("session_cpu_stat") or {}).get(field)
        after = (current["raw"].get("session_cpu_stat") or {}).get(field)
        if before is None or after is None:
            unavailable(metric, "missing_counter", "Missing cgroup counter at one or both endpoints")
        elif after < before:
            unavailable(metric, "counter_reset", "Cgroup counter decreased")
        else:
            delta = after - before
            interval["values"][metric] = {"rate": delta / elapsed, "delta": delta}
    return interval


def _union(windows):
    result = []
    for start, end in sorted((item["start"], item["end"]) for item in windows):
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0], max(end, result[-1][1]))
        else:
            result.append((start, end))
    return result


def _statistics(intervals, spans):
    duration = sum((end - start).total_seconds() for start, end in spans)
    covered = 0.0
    overlapping = 0
    long_intervals = 0
    maximum_interval = None
    accumulator = {metric: {"seconds": 0.0, "sum": 0.0, "max": None, "total": 0.0, "intervals": 0}
                   for metric in METRICS}
    for interval in intervals:
        overlap = sum(max(0.0, (min(end, interval["end"]) - max(start, interval["start"])).total_seconds())
                      for start, end in spans)
        if overlap <= 0:
            continue
        covered += overlap
        overlapping += 1
        long_intervals += int(interval["long_interval"])
        maximum_interval = max(maximum_interval or 0.0, interval["wall_seconds"])
        for metric, value in interval["values"].items():
            if value is None:
                continue
            target = accumulator[metric]
            target["seconds"] += overlap
            target["sum"] += value["rate"] * overlap
            target["max"] = max(target["max"] if target["max"] is not None else value["rate"], value["rate"])
            target["intervals"] += 1
            if metric in COUNTER_METRICS:
                target["total"] += value["delta"] * overlap / interval["wall_seconds"]
    metrics = {}
    for metric, values in accumulator.items():
        seconds = values["seconds"]
        result = {"coverage_seconds": seconds, "coverage_fraction": min(1.0, seconds / duration),
                  "complete_coverage": abs(seconds - duration) <= EPSILON_SECONDS,
                  "overlapping_intervals": values["intervals"]}
        mean = values["sum"] / seconds if seconds else None
        if metric in COUNTER_METRICS:
            result.update(estimated_total=values["total"] if seconds else None,
                          weighted_mean_per_second=mean, max_per_second=values["max"],
                          unit="events" if metric.endswith("nr_throttled") else "microseconds")
        else:
            result.update(weighted_mean_percent=mean, max_percent=values["max"])
        metrics[metric] = result
    return {"duration_seconds": duration, "covered_seconds": covered,
            "uncovered_seconds": max(0.0, duration - covered), "coverage_fraction": min(1.0, covered / duration),
            "complete_coverage": abs(covered - duration) <= EPSILON_SECONDS,
            "complete_metric_coverage": all(item["complete_coverage"] for item in metrics.values()),
            "overlapping_intervals": overlapping, "long_intervals": long_intervals,
            "maximum_interval_seconds": maximum_interval, "metrics": metrics}


def _bracket(timestamp, sample_times):
    before = bisect_right(sample_times, timestamp) - 1
    after = bisect_left(sample_times, timestamp)
    return {"sample_at_or_before": _iso(sample_times[before]) if before >= 0 else None,
            "sample_at_or_after": _iso(sample_times[after]) if after < len(sample_times) else None}


def summarize(monitor_path: Path, windows: list[dict]) -> dict:
    """Return JSON-safe interval-weighted monitor statistics and coverage.

    Window start/end accept timezone-aware ISO strings, datetime objects, or
    Unix seconds (the run.json format). Missing counters and resets make metric
    coverage incomplete; structurally malformed records raise ValueError.
    """
    _require(isinstance(windows, list) and bool(windows), "windows must be a nonempty list")
    normalized, names = [], set()
    for index, window in enumerate(windows):
        _require(isinstance(window, dict), f"windows[{index}] must be an object")
        name = window.get("name")
        _require(isinstance(name, str) and bool(name) and name not in names,
                 f"windows[{index}]: name must be a unique nonempty string")
        names.add(name)
        start = _time(window.get("start"), name + ".start")
        end = _time(window.get("end"), name + ".end")
        _require(end > start, name + ": end must be after start")
        normalized.append({"name": name, "start": start, "end": end})
    metadata, samples, intervals, issues, line_count = _read_monitor(Path(monitor_path))
    sample_times = [sample["utc"] for sample in samples]
    output_windows = []
    for window in normalized:
        statistics = _statistics(intervals, [(window["start"], window["end"])])
        output_windows.append({"name": window["name"], "start": _iso(window["start"]), "end": _iso(window["end"]),
                               "start_boundary": _bracket(window["start"], sample_times),
                               "end_boundary": _bracket(window["end"], sample_times), **statistics})
    accepted_spans = _union(normalized)
    aggregate = _statistics(intervals, accepted_spans)
    accepted_issues = [issue for issue in issues if any(_time(issue["start"], "issue start") < end
                      and _time(issue["end"], "issue end") > start for start, end in accepted_spans)]
    return {
        "schema_version": 1,
        "monitor": {"source_path": str(Path(monitor_path).resolve()), "metadata_records": metadata,
                    "all_monitor_sessions_affined_to_cpu1": all(item["monitor_affinity"] == [1] for item in metadata),
                    "line_count": line_count, "sample_count": len(samples), "interval_count": len(intervals),
                    "first_sample_utc": _iso(sample_times[0]), "last_sample_utc": _iso(sample_times[-1]),
                    "metric_issue_count_all_intervals": len(issues)},
        "semantics": {
            "intervals": "Each interval is [previous sample UTC, current sample UTC]; rates are derived from adjacent raw counters. Shared boundaries have zero measure.",
            "weighting": "Rates use overlap seconds as weights. CPU rates use counter-tick ratios; PSI and cgroup rates use monotonic elapsed seconds. PSI avg10/avg60/avg300 and recorded deltas are not used.",
            "boundaries": "Attribution within a partially overlapping interval assumes its measured rate and counter increments were uniform. Cgroup estimated totals prorate increments by wall-time overlap and may be fractional. Maxima are whole-interval rates for any interval with positive overlap, not instantaneous peaks.",
            "scope": "run.json start/end windows include checkpoint build, setup, warmup, measurement, and other launcher activity; they are not restricted to WorkloadActual iterations. Aggregate statistics cover the union of accepted windows, without double-counting overlap.",
            "coverage": "Time coverage and coverage of all eight required metrics are separate. Missing or decreasing counters are unavailable, never zero. Gaps between monitor sessions are uncovered; long within-session sampling intervals remain attributed and are counted explicitly.",
            "isolation": "The monitor's declared affinity is reported as metadata. CPU affinity and these observations do not establish exclusive CPU ownership, an offline SMT sibling, or host isolation. The KVM host is unreserved.",
        },
        "window_count": len(output_windows), "windows": output_windows,
        "aggregate_union": {"spans": [{"start": _iso(start), "end": _iso(end)} for start, end in accepted_spans], **aggregate},
        "complete_coverage": all(item["complete_coverage"] for item in output_windows),
        "complete_metric_coverage": all(item["complete_metric_coverage"] for item in output_windows),
        "metric_issues_in_accepted_windows": accepted_issues,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--monitor", type=Path, default=DEFAULT_MONITOR)
    parser.add_argument("--results", type=Path, default=Path(__file__).resolve().parent / "results")
    parser.add_argument("--output", type=Path, help="Write JSON here; otherwise print to stdout")
    arguments = parser.parse_args(argv)
    # Importing report is read-only; do not discover cohorts by directory globbing.
    sys.dont_write_bytecode = True
    from report import checkpoint_plan
    windows = []
    for checkpoint in checkpoint_plan():
        path = arguments.results / checkpoint.name / "run.json"
        _require(path.is_file(), f"Accepted checkpoint has no run.json: {path}")
        run = _read_json(path.read_text(encoding="utf-8"), str(path))
        _require(type(run.get("exitCode")) is int and run["exitCode"] == 0 and run.get("end") is not None,
                 f"Accepted checkpoint is not complete and successful: {checkpoint.name}")
        _require(isinstance(run.get("arguments"), dict)
                 and run["arguments"].get("name") == checkpoint.name,
                 f"Checkpoint run.json name differs: {checkpoint.name}")
        windows.append({"name": checkpoint.name, "start": run.get("start"), "end": run["end"]})
    result = summarize(arguments.monitor, windows)
    result["checkpoint_selection"] = "Exactly report.checkpoint_plan() without extra repeats or discovered directories; every selected run.json completed successfully."
    encoded = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if arguments.output:
        arguments.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    return 0 if result["complete_coverage"] and result["complete_metric_coverage"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as error:
        print(f"monitor_summary: {error}", file=sys.stderr)
        sys.exit(2)
