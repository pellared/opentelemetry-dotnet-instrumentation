#!/usr/bin/env python3
"""Audit profiler hook installation for every measured PID in completed runs.

Usage: taskset -c 1 python3 native_audit.py results/checkpoint [other_checkpoint ...]
Reads existing analysis/processes.json and native logs; never launches benchmarks.
Copies unchanged native log bytes to analysis/raw-native-logs for review.
"""

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

from analyze import AnalysisError, job_key, read_json, require, source_info


INTEGRATION = "OpenTelemetry.AutoInstrumentation.Instrumentations.Process.Integrations.ActivitySourceCreateActivityIntegration"


def environment_value(display, name):
    match = re.search(r"(?:EnvironmentVariables=|,)" + re.escape(name) + r"=([^,]*)", display)
    require(match is not None, f"Missing job environment variable: {name}")
    return match[1]


def measured_pids(console):
    current, records, seen = None, [], set()
    with console.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if line.startswith("// Benchmark: "):
                display = line.removeprefix("// Benchmark: ")
                profile, block = job_key(display)
                full_method = display.split(":", 1)[0]
                current = (full_method.rsplit(".", 1)[-1], profile, block)
            match = re.match(r"// Benchmark Process (\d+) has exited with code (-?\d+)\.", line)
            if match:
                require(current is not None, "Process exit without an active benchmark")
                pid, exit_code = int(match[1]), int(match[2])
                require(pid not in seen, f"Repeated measured PID: {pid}")
                require(exit_code == 0, f"Measured PID {pid} exited with {exit_code}")
                seen.add(pid)
                records.append((*current, pid, exit_code))
    return records


def audit(run_dir):
    run_dir = run_dir.resolve()
    metadata_path, console_path = run_dir / "run.json", run_dir / "console.log"
    metadata = read_json(metadata_path)
    require(metadata.get("exitCode") == 0 and "end" in metadata, f"Run not successfully completed: {run_dir}")
    analysis_path = run_dir / "analysis" / "processes.json"
    analysis = read_json(analysis_path)
    require(analysis["run_metadata"] == metadata, "Analysis run metadata differs from completed run.json; re-run analyze.py")
    expected = {(p["method"], p["profile"], p["block"]): p for p in analysis["processes"]}
    require(len(expected) == len(analysis["processes"]), "Duplicate analyzed process cells")
    exits = measured_pids(console_path)
    require(len(exits) == len(expected) and {row[:3] for row in exits} == set(expected),
            "Measured PID coverage differs from validated process cells")
    require(len({row[:3] for row in exits}) == len(exits), "Multiple measured PIDs for one process cell")
    rows, raw_logs = [], {}
    for method, profile, block, pid, exit_code in exits:
        process = expected[method, profile, block]
        display = process["display_info"]
        profiling = environment_value(display, "CORECLR_ENABLE_PROFILING")
        require(profiling in ("0", "1"), f"Unexpected profiling value: {profiling}")
        attached = profiling == "1"
        process_enabled = environment_value(display, "OTEL_DOTNET_AUTO_TRACES_PROCESS_INSTRUMENTATION_ENABLED") == "true"
        mode = environment_value(display, "OTEL_DOTNET_AUTO_TRACES_PROCESS_INSTRUMENTATION_CONTEXT_EXTRACTION_MODE")
        incoming = environment_value(display, "TRACEPARENT")
        if incoming:
            require(re.fullmatch(r"00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}", incoming) is not None
                    and incoming[3:35] != "0" * 32 and incoming[36:52] != "0" * 16,
                    f"Unsupported incoming fixture: {profile}")
        hook_expected = attached and process_enabled and mode in ("parent", "link") and bool(incoming)
        require(hook_expected == profile.startswith("Automatic"), f"Profile/job hook expectations disagree: {profile}")
        directory = Path(environment_value(display, "OTEL_DOTNET_AUTO_LOG_DIRECTORY"))
        files = sorted(directory.glob(f"otel-dotnet-auto-{pid}-*-Native.log"))
        context = f"{method}/{profile}/B{block:02d}/PID{pid}"
        if attached:
            require(len(files) == 1, f"{context}: expected one native log, found {len(files)} in {directory}")
        else:
            require(not files, f"{context}: profiling disabled but native profiler log exists")
        row = {
            "suite": metadata["arguments"]["name"], "runtime": metadata["arguments"]["runtime"],
            "benchmark_type": process.get("benchmark_type", "ActivityFactoryBenchmarks"),
            "method": method, "profile": profile, "block": block, "pid": pid,
            "exit_code": exit_code, "profiler_attached": attached,
            "activity_hook_expected": hook_expected,
            "job_native_log_directory": str(directory), "native_file": None,
            "native_sha256": None, "archived_native_file": None,
            "activity_hook_enqueued_count": 0, "activity_hook_rewrite_finished_count": 0,
            "warning_or_error_count": 0, "enqueue_evidence": [], "rewrite_evidence": [],
            "warnings_or_errors": [],
        }
        if files:
            path = files[0]
            raw = path.read_bytes()
            lines = raw.decode("utf-8", errors="replace").splitlines()
            enqueue = [line for line in lines if "Method enqueued for ReJIT for System.Diagnostics.ActivitySource.CreateActivity(9 params)." in line]
            rewrite = [line for line in lines if "CallTarget_RewriterCallback() Finished: System.Diagnostics.ActivitySource.CreateActivity()" in line
                       and f"IntegrationType={INTEGRATION}" in line and "Arguments=9]" in line]
            warnings = [line for line in lines if "[error]" in line.lower() or "[warn]" in line.lower()
                        or "[warning]" in line.lower()]
            require(bool(enqueue) == hook_expected and bool(rewrite) == hook_expected,
                    f"{context}: expected hook={hook_expected}, enqueued={len(enqueue)}, rewritten={len(rewrite)}")
            # Each source log must identify the measured PID, not just have its filename.
            require(any(re.search(r"\[" + str(pid) + r"\|\d+\]", line) for line in lines),
                    f"{context}: native log does not identify measured PID")
            archive = run_dir / "analysis" / "raw-native-logs" / path.name
            row.update(native_file=str(path.resolve()), native_sha256=hashlib.sha256(raw).hexdigest(),
                       archived_native_file=str(archive.relative_to(run_dir)),
                       activity_hook_enqueued_count=len(enqueue), activity_hook_rewrite_finished_count=len(rewrite),
                       warning_or_error_count=len(warnings), enqueue_evidence=enqueue,
                       rewrite_evidence=rewrite, warnings_or_errors=warnings)
            raw_logs[archive] = raw
        rows.append(row)
    inputs = [source_info(metadata_path), source_info(console_path), source_info(analysis_path)]
    result = {
        "schema_version": 1, "suite": metadata["arguments"]["name"], "inputs": inputs,
        "expected_cells": len(expected), "audited_cells": len(rows),
        "automatic_hook_installed": sum(row["activity_hook_expected"] for row in rows),
        "attached_hook_absent": sum(row["profiler_attached"] and not row["activity_hook_expected"] for row in rows),
        "no_agent_native_log_absent": sum(not row["profiler_attached"] for row in rows),
        "warning_or_error_count": sum(row["warning_or_error_count"] for row in rows),
        "scope": "Per-measured-PID native log evidence for the nine-argument ActivitySource.CreateActivity hook. "
                 "Enqueue plus finished rewriter events prove profiler rewrite evidence, not an invocation count. "
                 "Assembly/source proof is separately scoped to the captured benchmark application assembly.",
        "processes": rows,
    }
    for archive, raw in raw_logs.items():
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_bytes(raw)
    output = run_dir / "analysis"
    (output / "native-audit.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    flat = [{key: value for key, value in row.items() if not isinstance(value, list)} for row in rows]
    with (output / "native-audit.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(flat[0]))
        writer.writeheader()
        writer.writerows(flat)
    print(f"{result['suite']}: native audit passed {len(rows)} PIDs; "
          f"{result['automatic_hook_installed']} installed, {result['attached_hook_absent']} attached without hook, "
          f"{result['no_agent_native_log_absent']} without profiler/log, "
          f"{result['warning_or_error_count']} warnings/errors")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", type=Path, nargs="+")
    args = parser.parse_args()
    try:
        for directory in args.run_dirs:
            audit(directory)
    except (AnalysisError, KeyError, OSError, json.JSONDecodeError) as error:
        print(f"Native audit failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
