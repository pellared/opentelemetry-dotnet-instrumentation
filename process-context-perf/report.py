#!/usr/bin/env python3
"""Aggregate completed, validated checkpoint analyses into RESULTS.md.

Run on a non-benchmark CPU:
    taskset -c 1 python3 report.py
    taskset -c 1 python3 report.py --require-complete

This reader never starts benchmarks, invokes the analyzer, or changes raw inputs.
Only explicitly listed checkpoints are included. Discarded pilots are excluded.
"""

import argparse
import hashlib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
import re
from pathlib import Path
import statistics
import sys


PRIMARY_PROFILES = ("ManualParent", "AutomaticParent", "ManualLink", "AutomaticLink")
PRIMARY_NET10_METHODS = (
    "Root", "RootEmptyLinks", "RootExistingLink", "RootAlreadyLinked", "NoListeners",
    "Dropped", "DropReadingLinks", "AmbientParent", "SuppliedContext", "SuppliedParentId",
    "SuppliedEmptyParentId", "CreateOnly", "CreateThenStart", "PropagationOnly",
)
CROSS_RUNTIME_METHODS = ("Root", "NoListeners", "Dropped", "AmbientParent", "SuppliedContext", "CreateOnly")
STUDIES = (
    ("primary-net10", ".NET 10 primary workloads"),
    ("primary-net8", ".NET 8 subset"),
    ("primary-net9", ".NET 9 subset"),
    ("controls-net10", ".NET 10 registration and profiler controls"),
    ("tiering-off-net10", ".NET 10 tiering disabled sensitivity"),
    ("sdk-net10", ".NET 10 application SDK sensitivity"),
    ("link-sampling-net10", ".NET 10 link-aware sampler supplement"),
)
METHOD_DESCRIPTIONS = {
    "Root": "StartActivity with an ActivityContext parent argument and optional links; create, start, and dispose.",
    "RootEmptyLinks": "The root factory with an explicitly empty links collection in automatic mode; the manual link control supplies its cached incoming link.",
    "RootExistingLink": "The root factory with one unrelated existing link; the manual link control supplies both links in a cached collection.",
    "RootAlreadyLinked": "The incoming link is already supplied; automatic link mode must avoid adding it again.",
    "NoListeners": "Ordinary StartActivity(\"job\") on a source with no listeners; returns null.",
    "Dropped": "A listener returns ActivitySamplingResult.None without enumerating links; no Activity is created.",
    "DropReadingLinks": "A listener enumerates the existing/incoming links, then returns None.",
    "AmbientParent": "Ordinary StartActivity(\"job\") with an existing Activity.Current; preserve that parent.",
    "SuppliedContext": "StartActivity with an explicit unrelated ActivityContext parent; preserve it.",
    "SuppliedParentId": "StartActivity with an explicit unrelated W3C parent-ID string; preserve it.",
    "SuppliedEmptyParentId": "StartActivity with an explicit empty parent-ID string; preserve the caller's root choice.",
    "CreateOnly": "CreateActivity returns an unstarted Activity; its construction and sampling are measured, without Start/Stop.",
    "CreateThenStart": "CreateActivity, then Start, then dispose.",
    "PropagationOnly": "A listener returns PropagationData; create/start/dispose without requesting recorded data.",
}
# Two-sided Student t95 critical values for one through eight four-block cohorts.
T95 = {3: 3.182446305, 7: 2.364624252, 11: 2.200985160, 15: 2.131449546,
       19: 2.093024054, 23: 2.068657610, 27: 2.051830516, 31: 2.039513446}
REPEAT_METHODS = ("Root", "AmbientParent", "Dropped", "SuppliedContext")


class ReportError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ReportError(message)


@dataclass(frozen=True)
class Checkpoint:
    name: str
    runtime: str
    method: str
    study: str
    profiles: tuple = PRIMARY_PROFILES
    benchmark_type: str = "ActivityFactoryBenchmarks"
    tiering: str = "default"
    sdk: bool = False


def checkpoint_plan(extra_repeats=()):
    plan = [Checkpoint("no-listener-net10", "net10.0", "NoListeners", "primary-net10")]
    for runtime, methods in (("net10", PRIMARY_NET10_METHODS), ("net8", CROSS_RUNTIME_METHODS), ("net9", CROSS_RUNTIME_METHODS)):
        for method in methods:
            if runtime == "net10" and method == "NoListeners":
                continue
            plan.append(Checkpoint(f"activity-{runtime}-{method.lower()}", runtime + ".0", method, "primary-" + runtime))
    for method in ("Root", "NoListeners"):
        plan.append(Checkpoint(f"controls-net10-{method.lower()}", "net10.0", method, "controls-net10",
                               ("Disabled", "NoIncoming", "ExtractionOff", "NoAgent")))
    for method in ("Root", "NoListeners", "AmbientParent"):
        plan.append(Checkpoint(f"tiering-off-net10-{method.lower()}", "net10.0", method, "tiering-off-net10", tiering="0"))
    for method in ("Root", "NoListeners", "CreateOnly"):
        plan.append(Checkpoint(f"sdk-net10-{method.lower()}", "net10.0", method, "sdk-net10", sdk=True))
    plan.append(Checkpoint("no-listener-repeat-net10", "net10.0", "NoListeners", "primary-net10"))
    for method in REPEAT_METHODS:
        plan.append(Checkpoint(f"activity-repeat-net10-{method.lower()}", "net10.0", method, "primary-net10"))
    methods_by_name = {method.lower(): method for method in PRIMARY_NET10_METHODS}
    for name in extra_repeats:
        match = re.fullmatch(r"activity-repeat(?:-?\d+)?-net10-([a-z]+)", name)
        require(match is not None and match[1] in methods_by_name, f"Invalid extra primary repeat cohort: {name}")
        plan.append(Checkpoint(name, "net10.0", methods_by_name[match[1]], "primary-net10"))
    for suffix, method in (("root", "Root"), ("existing", "RootExistingLink")):
        plan.append(Checkpoint(f"link-sampling-{suffix}-net10", "net10.0", method, "link-sampling-net10",
                               ("ManualLink", "AutomaticLink"), "LinkSamplingBenchmarks"))
    require(len({item.name for item in plan}) == len(plan), "Duplicate planned checkpoint names")
    return plan


def read_json(path):
    with path.open(encoding="utf-8-sig") as stream:
        return json.load(stream)


def numeric(value, context):
    require(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value),
            f"Invalid finite numeric value: {context}")
    return value


def close(left, right, context):
    require(math.isclose(left, right, rel_tol=1e-10, abs_tol=1e-8), f"Inconsistent analysis value: {context}")


def expected_pairs(checkpoint):
    if checkpoint.study == "controls-net10":
        return [(candidate, "Disabled") for candidate in ("NoIncoming", "ExtractionOff", "NoAgent")]
    return [(candidate, baseline) for candidate, baseline in
            (("AutomaticParent", "ManualParent"), ("AutomaticLink", "ManualLink"))
            if candidate in checkpoint.profiles and baseline in checkpoint.profiles]


def load_checkpoint(root, checkpoint):
    run = root / checkpoint.name
    state = {"checkpoint": checkpoint, "status": "pending", "processes": [], "pairs": [], "provenance": "pending"}
    metadata_path = run / "run.json"
    if not metadata_path.exists():
        return state
    metadata = read_json(metadata_path)
    code = metadata.get("exitCode")
    if code is None:
        state["status"] = "running"
        return state
    if code != 0:
        state["status"] = f"failed (exit {code})"
        return state
    arguments = metadata["arguments"]
    require(arguments.get("name") == checkpoint.name and arguments.get("runtime") == checkpoint.runtime
            and arguments.get("methods") == [checkpoint.method], f"Checkpoint arguments differ: {checkpoint.name}")
    require(arguments.get("cases", "").split(",") == list(checkpoint.profiles)
            and int(arguments.get("blocks") or 0) == 4, f"Checkpoint profiles/blocks differ: {checkpoint.name}")
    require(arguments.get("type", "ActivityFactoryBenchmarks") == checkpoint.benchmark_type
            and (arguments.get("tiering") or "default") == checkpoint.tiering
            and bool(arguments.get("sdk", False)) == checkpoint.sdk, f"Checkpoint sensitivity differs: {checkpoint.name}")
    process_path = run / "analysis" / "processes.json"
    comparison_path = run / "analysis" / "comparisons.json"
    if not process_path.exists() or not comparison_path.exists():
        state["status"] = "complete; awaiting analysis"
        return state
    processes_doc, comparisons_doc = read_json(process_path), read_json(comparison_path)
    for document in (processes_doc, comparisons_doc):
        require(document.get("run_metadata") == metadata, f"Analysis metadata is stale: {checkpoint.name}")
        checks = document.get("checks", {})
        require(checks.get("all_actual_rows_retained") is True and checks.get("blocks") == 4
                and checks.get("actual_rows_per_process") == 20 and checks.get("result_rows_per_process") == 20
                and checks.get("warmup_rows_per_process") == 40,
                f"Analysis retention/count checks differ: {checkpoint.name}")
    processes = processes_doc["processes"]
    lookup = {}
    for process in processes:
        key = process["profile"], process["block"]
        require(key not in lookup, f"Duplicate process: {checkpoint.name}/{key}")
        require(process["suite"] == checkpoint.name and process["runtime"] == checkpoint.runtime
                and process["method"] == checkpoint.method and process["launch_index"] == 1
                and process.get("benchmark_type", "ActivityFactoryBenchmarks") == checkpoint.benchmark_type,
                f"Process identity differs: {checkpoint.name}/{key}")
        require(process["sensitivity"] == {"tiering": checkpoint.tiering, "sdk_provider": checkpoint.sdk},
                f"Process sensitivity differs: {checkpoint.name}/{key}")
        for stage in ("actual", "result"):
            values = process[f"{stage}_ns_per_op"]
            require(process[stage]["n"] == len(values) == 20, f"Wrong process iteration count: {checkpoint.name}/{key}")
            close(numeric(process[stage]["mean_ns"], str(key)), statistics.mean(numeric(x, str(key)) for x in values), str(key))
        numeric(process["overhead_actual"]["median_ns"], str(key))
        numeric(process["allocated_bytes_per_op"], str(key))
        lookup[key] = process
    require(set(lookup) == {(profile, block) for profile in checkpoint.profiles for block in range(4)},
            f"Process coverage differs: {checkpoint.name}")
    reported = {(row["candidate"], row["baseline"]): row for row in comparisons_doc["comparisons"]}
    require(len(reported) == len(comparisons_doc["comparisons"]) and set(reported) == set(expected_pairs(checkpoint)),
            f"Comparison coverage differs: {checkpoint.name}")
    pairs = []
    for candidate, baseline in expected_pairs(checkpoint):
        cohort_pairs = []
        for block in range(4):
            a, b = lookup[candidate, block], lookup[baseline, block]
            cohort_pairs.append({
                "cohort": checkpoint.name, "block": block, "block_id": f"{checkpoint.name}/B{block:02d}",
                "candidate": candidate, "baseline": baseline,
                "candidate_mean": a["result"]["mean_ns"], "baseline_mean": b["result"]["mean_ns"],
                "candidate_actual": a["actual"]["mean_ns"], "baseline_actual": b["actual"]["mean_ns"],
                "candidate_overhead": a["overhead_actual"]["median_ns"], "baseline_overhead": b["overhead_actual"]["median_ns"],
                "candidate_bytes": a["allocated_bytes_per_op"], "baseline_bytes": b["allocated_bytes_per_op"],
            })
        row = reported[candidate, baseline]
        require(row["suite"] == checkpoint.name and row["runtime"] == checkpoint.runtime
                and row["method"] == checkpoint.method and row["independent_blocks"] == 4
                and row["degrees_of_freedom"] == 3, f"Comparison identity differs: {checkpoint.name}")
        close(row["delta_mean_ns"], statistics.mean(p["candidate_mean"] - p["baseline_mean"] for p in cohort_pairs), checkpoint.name)
        close(row["candidate_process_mean_ns"], statistics.mean(p["candidate_mean"] for p in cohort_pairs), checkpoint.name)
        close(row["baseline_process_mean_ns"], statistics.mean(p["baseline_mean"] for p in cohort_pairs), checkpoint.name)
        pairs += cohort_pairs
    state.update(status="analyzed", processes=processes, pairs=pairs,
                 provenance=processes_doc.get("source_provenance", {}).get("status", "not recorded"))
    return state


def interval(values):
    n = len(values)
    require(n % 4 == 0 and n - 1 in T95, f"Expected one to eight complete four-block cohorts; found {n} blocks")
    mean = statistics.mean(values)
    margin = T95[n - 1] * statistics.stdev(values) / math.sqrt(n)
    return mean, mean - margin, mean + margin


def percentage_change(candidate, baseline):
    if not math.isfinite(candidate) or not math.isfinite(baseline) or baseline <= 0:
        return None
    return 100 * (candidate - baseline) / baseline


def percentage(value):
    return "n/a" if value is None else f"{value:+.2f}%"


def aggregate(states):
    expected, observed = {}, {}
    for state in states:
        checkpoint = state["checkpoint"]
        for candidate, baseline in expected_pairs(checkpoint):
            key = checkpoint.study, checkpoint.method, candidate, baseline
            expected.setdefault(key, []).append(checkpoint.name)
        if state["status"] != "analyzed":
            continue
        for pair in state["pairs"]:
            key = checkpoint.study, checkpoint.method, pair["candidate"], pair["baseline"]
            observed.setdefault(key, []).append(pair)
    rows = {}
    for key, pairs in observed.items():
        require(len({p["block_id"] for p in pairs}) == len(pairs), f"Duplicate independent blocks: {key}")
        require(len(pairs) == 4 * len({p["cohort"] for p in pairs}), f"Incomplete cohort in comparison: {key}")
        delta = interval([p["candidate_mean"] - p["baseline_mean"] for p in pairs])
        raw = interval([p["candidate_actual"] - p["baseline_actual"] for p in pairs])
        baseline = statistics.mean(p["baseline_mean"] for p in pairs)
        candidate = statistics.mean(p["candidate_mean"] for p in pairs)
        baseline_actual = statistics.mean(p["baseline_actual"] for p in pairs)
        candidate_actual = statistics.mean(p["candidate_actual"] for p in pairs)
        rows[key] = {
            "key": key, "pairs": pairs, "n": len(pairs), "expected_n": 4 * len(expected[key]),
            "baseline": baseline, "candidate": candidate,
            "baseline_actual": baseline_actual, "candidate_actual": candidate_actual,
            "percent_change": percentage_change(candidate, baseline),
            "actual_percent_change": percentage_change(candidate_actual, baseline_actual),
            "delta": delta, "raw_delta": raw,
            "allocation_delta": statistics.mean(p["candidate_bytes"] - p["baseline_bytes"] for p in pairs),
        }
    return rows, expected


def number(value):
    return f"{value:.2f}"


def ci(value):
    return f"{number(value[0])} [{number(value[1])}, {number(value[2])}]"


def value_range(values):
    low, high = min(values), max(values)
    return number(low) if math.isclose(low, high, rel_tol=0, abs_tol=1e-9) else f"{number(low)}–{number(high)}"


def escape(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def link(path, output_dir, label):
    import os
    return f"[{escape(label)}]({Path(os.path.relpath(path, output_dir)).as_posix()})"


def render(states, rows, expected, results_root, output, json_output):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    complete = all(state["status"] == "analyzed" for state in states)
    completed = sum(state["status"] == "analyzed" for state in states)
    process_count = sum(len(state["processes"]) for state in states)
    expected_processes = sum(4 * len(state["checkpoint"].profiles) for state in states)
    lines = ["# ActivitySource process-context factory measurements", "",
             f"{'**Complete**' if complete else '**Partial — pending checkpoints are listed below**'}; generated {now}.", "",
             f"Analyzed {completed}/{len(states)} checkpoints, {process_count}/{expected_processes} processes, "
             f"and {len(rows)}/{len(expected)} comparison rows. Missing results are omitted from numeric tables.", "",
             link(json_output, output.parent, "Machine-readable combined statistics and per-block inputs") + ".", "",
             "Times are ns/op. The main tables use BenchmarkDotNet Result measurements after its measured empty-loop "
             "overhead subtraction. Each number is an equal-weight mean of independently launched process means. "
             "Δ is candidate minus baseline; brackets give a pointwise paired two-sided Student t95 interval on block differences. "
             "The primary baseline has the same profiler attached with PROCESS disabled and cached equivalent manual parent/link input.", "",
             "Δ % = 100 × (candidate mean − baseline mean) / baseline mean, using the unrounded aggregate process means. "
             "Percentages are point estimates, not means of paired percentages; the confidence intervals remain absolute ns/op. "
             "Raw Actual percentages use raw Actual means. A nonpositive or nonfinite baseline produces n/a.", "",
             "Primary profiles use a minimal application ActivityListener with no application TracerProvider or exporters. "
             "Attached profiles still initialize SDK globals. A target-metadata SDK value of none means no application provider; "
             "it does not mean SDK assemblies are absent.", "",
             "Each cohort has four balanced blocks (n=4, df=3). The .NET 10 Root, NoListeners, Dropped, AmbientParent, and "
             "SuppliedContext primary rows combine their original and one additional cohort as distinct cohort/block IDs; "
             "after both finish each uses all eight block differences (n=8, df=7). A partial n column such as 4/8 shows missing "
             "repeat coverage. All 20 Actual iterations per process are retained.", "",
             "One additional four-block cohort for those five workloads was selected after observing between-process variation, "
             "rather than by the direction or significance of a result. That sample plan was then frozen. Intervals are nominal "
             "exploratory intervals; they are not adjusted for the earlier inspection or sequential selection.", ""]
    manifest_path = results_root.parent / "manifest.json"
    if manifest_path.is_file():
        manifest = read_json(manifest_path)
        lines += [f"Instrumentation commit: `{escape(manifest.get('sourceCommit', 'not recorded'))}`. "
                  + link(manifest_path, output.parent, "Environment and binary/harness manifest") + ".", ""]
    else:
        lines += ["Environment/binary manifest has not been captured in this report directory yet.", ""]
    for study, title in STUDIES:
        keys = [key for key in expected if key[0] == study]
        mode_order = {"AutomaticParent": 0, "AutomaticLink": 1, "NoIncoming": 0, "ExtractionOff": 1, "NoAgent": 2}
        keys.sort(key=lambda key: (PRIMARY_NET10_METHODS.index(key[1]), mode_order[key[2]]))
        available = [rows[key] for key in keys if key in rows]
        lines += [f"## {title}", ""]
        if not available:
            lines += [f"Pending: 0/{len(keys)} comparison rows analyzed.", ""]
            continue
        if study == "controls-net10":
            lines += ["These controls compare each candidate with the attached-profiler PROCESS-disabled baseline. "
                      "NoAgent removes the profiler/startup hook; its difference includes whole-agent and JIT effects.", ""]
        elif study == "tiering-off-net10":
            lines += ["Sensitivity only: DOTNET_TieredCompilation=0 in every profile.", ""]
        elif study == "sdk-net10":
            lines += ["Application TracerProvider with ParentBased(AlwaysOn) sampling for the recorded source; no exporters. "
                      "The no-listener source remains unsubscribed.", ""]
        elif study == "link-sampling-net10":
            lines += ["Separate LinkSamplingBenchmarks class: the sampler enumerates links and records only when it sees "
                      "the incoming trace/span IDs. Both manual and automatic cases validate equivalent recorded activities. "
                      "These results are kept separate from the primary listener that does not inspect recorded-source links.", ""]
        lines += ["| Workload | Comparison | Blocks | Baseline → candidate ns/op | Δ ns/op [95% CI] | Δ % | Δ B/op |",
                  "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
        for row in available:
            _, method, candidate, baseline = row["key"]
            mode = "parent" if candidate == "AutomaticParent" else "link" if candidate == "AutomaticLink" else f"{baseline} → {candidate}"
            count = str(row["n"]) if row["n"] == row["expected_n"] else f"{row['n']}/{row['expected_n']}"
            lines.append(f"| {method} | {mode} | {count} | {number(row['baseline'])} → {number(row['candidate'])} "
                         f"| {ci(row['delta'])} | {percentage(row['percent_change'])} | {number(row['allocation_delta'])} |")
        lines += ["", "<details>", "<summary>Process ranges and raw Actual comparisons</summary>", "",
                  "Ranges are minimum–maximum process means, rather than iteration ranges. Overhead ranges use each process's "
                  "median empty-loop overhead. Raw Actual deltas include that loop overhead; they are useful when subtraction "
                  "is a material fraction of the factory time.", "",
                  "| Workload | Comparison | Result process-mean ranges: baseline → candidate | Raw Actual Δ ns/op [95% CI] | Raw Actual Δ % | Overhead median ranges: baseline → candidate | B/op ranges: baseline → candidate |",
                  "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
        for row in available:
            _, method, candidate, baseline = row["key"]
            mode = "parent" if candidate == "AutomaticParent" else "link" if candidate == "AutomaticLink" else f"{baseline} → {candidate}"
            pairs = row["pairs"]
            ranges = lambda field: value_range([p[field] for p in pairs])
            lines.append(f"| {method} | {mode} | {ranges('baseline_mean')} → {ranges('candidate_mean')} "
                         f"| {ci(row['raw_delta'])} | {percentage(row['actual_percent_change'])} | {ranges('baseline_overhead')} → {ranges('candidate_overhead')} "
                         f"| {ranges('baseline_bytes')} → {ranges('candidate_bytes')} |")
        lines += ["", "</details>", "", "<details>",
                  "<summary>All paired process means, with distinct cohort/block IDs</summary>", "",
                  "Values are rounded here; the linked source analysis preserves full precision and all iterations. "
                  "A control-baseline process can appear in more than one comparison.", "",
                  "| Workload | Comparison | Cohort/block | Baseline Result | Candidate Result | Result Δ % | Baseline Actual | Candidate Actual | Actual Δ % | Baseline B/op | Candidate B/op |",
                  "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for row in available:
            _, method, candidate, baseline = row["key"]
            mode = "parent" if candidate == "AutomaticParent" else "link" if candidate == "AutomaticLink" else f"{baseline} → {candidate}"
            for pair in sorted(row["pairs"], key=lambda item: (item["cohort"], item["block"])):
                lines.append(f"| {method} | {mode} | {pair['block_id']} | {number(pair['baseline_mean'])} "
                             f"| {number(pair['candidate_mean'])} | {percentage(percentage_change(pair['candidate_mean'], pair['baseline_mean']))} "
                             f"| {number(pair['baseline_actual'])} | {number(pair['candidate_actual'])} "
                             f"| {percentage(percentage_change(pair['candidate_actual'], pair['baseline_actual']))} "
                             f"| {number(pair['baseline_bytes'])} | {number(pair['candidate_bytes'])} |")
        lines += ["", "</details>", ""]
    probes = {}
    for state in states:
        for process in state["processes"]:
            probe = process.get("target_process_probe") or {}
            key = (process["runtime"], probe.get("framework", "not recorded"),
                   probe.get("diagnosticSourceFile", "not recorded"), probe.get("sdk", "not recorded"))
            probes[key] = True
    lines += ["## Measured target versions", ""]
    if probes:
        lines += ["| Requested runtime | Target framework | DiagnosticSource file version | Application TracerProvider SDK assembly version |",
                  "| --- | --- | --- | --- |"]
        for values in sorted(probes):
            lines.append("| " + " | ".join(escape(value) for value in values) + " |")
    else:
        lines += ["Pending target-process metadata."]
    lines += ["", "## Workload definitions", "", "| Workload | Measured work |", "| --- | --- |"]
    lines += [f"| {method} | {description} |" for method, description in METHOD_DESCRIPTIONS.items()]
    lines += ["", "Manual controls use a parsed remote parent or immutable cached link collections. Automatic profiles "
              "receive startup environment context. Parent-bearing root overloads are matched between manual and automatic "
              "cases. Existing-link controls cache the complete equivalent list; they do not rebuild it inside the timed call.", "",
              "## Interpretation limits", "",
              "- The configured warmup is 10 seconds of the actual target method plus 40 BenchmarkDotNet warmup iterations; "
              "measurement uses 20 iterations with a configured 250 ms target; actual durations may be shorter and are retained, with DontRemove. Startup, extraction, provider "
              "construction, and asynchronous ReJIT readiness are outside the measured operation.",
              "- Each mode has four fresh processes per checkpoint. Four-block intervals have limited precision; repeated-workload "
              "aggregations retain both cohorts and every process, including stable slower regimes. These nominal pointwise intervals assume "
              "approximately normal independent block differences and have no multiplicity adjustment.",
              "- This is a single Linux KVM host using CPU3 affinity and concurrent workstation GC. Its SMT sibling CPU11 is "
              "monitored, together with steal time, CPU pressure, and cgroup throttling. Affinity does not guarantee exclusive "
              "physical-host CPU or fixed frequency. Results do not establish server-GC, other-platform, or production latency guarantees.",
              "- Parent mode can avoid creating a new trace ID; link mode keeps a new trace. Simple-overload, no-agent, and "
              "cross-runtime differences can include runtime/JIT/code-layout work. Treat these as measured use cases rather "
              "than a universal cost for the hook. Empty-loop subtraction is especially material for the no-listener controls.",
              "- MemoryDiagnoser B/op is a per-process report, not a distribution of per-iteration allocation observations. "
              "The report shows allocation deltas and process ranges; it does not infer an allocation confidence interval.",
              "- The primary listener returns fixed sampling decisions. The SDK and link-aware sampler subsets add representative "
              "sampling paths without exporters; they do not model all SDK/exporter/application configurations.",
              "- Source and binary provenance has the exact scope recorded in each checkpoint analysis. This report does not "
              "expand those claims. Discarded pilots and aborted multi-method phases are excluded by an explicit checkpoint allowlist.", "",
              "## Checkpoint coverage and source analyses", "",
              "Cohort names below form part of every block ID. Original and repeat block numbers are never merged as the same process. "
              "The process/comparison files retain the measurements and within-cohort statistics used here.", "",
              "| Checkpoint / cohort | Status | Processes | Source provenance | Analyses |",
              "| --- | --- | ---: | --- | --- |"]
    for state in states:
        checkpoint = state["checkpoint"]
        folder = results_root / checkpoint.name
        name = link(folder / "run.json", output.parent, checkpoint.name) if (folder / "run.json").is_file() else checkpoint.name
        analyses = "pending"
        if state["status"] == "analyzed":
            analyses = link(folder / "analysis" / "processes.json", output.parent, "processes") + ", " \
                + link(folder / "analysis" / "comparisons.json", output.parent, "comparisons")
        lines.append(f"| {name} | {escape(state['status'])} | {len(state['processes'])}/{4 * len(checkpoint.profiles)} "
                     f"| {escape(state['provenance'])} | {analyses} |")
    lines += ["", "Reproduce the report with `taskset -c 1 python3 report.py`; "
              "`--require-complete` exits unsuccessfully until every planned checkpoint has a valid completed analysis.", ""]
    return "\n".join(lines), complete


def aggregate_document(states, rows, expected, root, complete):
    comparisons = []
    checkpoints = {state["checkpoint"].name: state["checkpoint"] for state in states}
    for row in rows.values():
        study, method, candidate, baseline = row["key"]
        pairs = row["pairs"]
        checkpoint = checkpoints[pairs[0]["cohort"]]
        ranges = lambda field: [min(p[field] for p in pairs), max(p[field] for p in pairs)]
        comparisons.append({
            "study": study, "runtime": checkpoint.runtime, "benchmark_type": checkpoint.benchmark_type,
            "sensitivity": {"tiering": checkpoint.tiering, "sdk_provider": checkpoint.sdk},
            "method": method, "candidate": candidate, "baseline": baseline,
            "independent_blocks": row["n"], "expected_blocks": row["expected_n"],
            "degrees_of_freedom": row["n"] - 1, "t95_critical": T95[row["n"] - 1],
            "cohorts": sorted({pair["cohort"] for pair in pairs}),
            "baseline_process_mean_ns": row["baseline"], "candidate_process_mean_ns": row["candidate"],
            "percent_change": row["percent_change"],
            "baseline_actual_process_mean_ns": row["baseline_actual"],
            "candidate_actual_process_mean_ns": row["candidate_actual"],
            "actual_percent_change": row["actual_percent_change"],
            "delta_mean_ns": row["delta"][0], "delta_ci95_low_ns": row["delta"][1], "delta_ci95_high_ns": row["delta"][2],
            "actual_delta_mean_ns": row["raw_delta"][0], "actual_delta_ci95_low_ns": row["raw_delta"][1],
            "actual_delta_ci95_high_ns": row["raw_delta"][2],
            "allocation_delta_mean_bytes_per_op": row["allocation_delta"],
            "baseline_process_mean_range_ns": ranges("baseline_mean"),
            "candidate_process_mean_range_ns": ranges("candidate_mean"),
            "baseline_actual_process_mean_range_ns": ranges("baseline_actual"),
            "candidate_actual_process_mean_range_ns": ranges("candidate_actual"),
            "baseline_overhead_median_range_ns": ranges("baseline_overhead"),
            "candidate_overhead_median_range_ns": ranges("candidate_overhead"),
            "baseline_allocation_range_bytes_per_op": ranges("baseline_bytes"),
            "candidate_allocation_range_bytes_per_op": ranges("candidate_bytes"),
            "paired_blocks": pairs,
        })
    inputs = []
    for state in states:
        if state["status"] != "analyzed":
            continue
        run = root / state["checkpoint"].name
        for path in (run / "run.json", run / "analysis" / "processes.json", run / "analysis" / "comparisons.json"):
            inputs.append({"path_from_results_root": path.relative_to(root).as_posix(),
                           "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {
        "schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(), "complete": complete,
        "statistical_unit": "Independently launched process means, paired by distinct cohort/block ID.",
        "interval": "Nominal pointwise paired two-sided Student t95; no sequential-selection or multiplicity adjustment.",
        "percentage_change": "100 * (candidate aggregate process mean - baseline aggregate process mean) / baseline aggregate process mean; "
                             "point estimate only, not mean paired percentages. Nonpositive/nonfinite baselines produce null.",
        "selection_note": "One extra four-block cohort for Root, NoListeners, Dropped, AmbientParent, and SuppliedContext "
                          "was selected after between-process variation was observed, not by direction/significance; the base plan was frozen.",
        "all_measured_iterations_retained": True,
        "expected_checkpoints": len(states), "analyzed_checkpoints": sum(s["status"] == "analyzed" for s in states),
        "expected_comparisons": len(expected), "available_comparisons": len(rows),
        "expected_processes": sum(4 * len(s["checkpoint"].profiles) for s in states),
        "analyzed_processes": sum(len(s["processes"]) for s in states),
        "report_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "analysis_inputs": inputs,
        "checkpoints": [{**asdict(s["checkpoint"]), "status": s["status"], "source_provenance": s["provenance"]} for s in states],
        "comparisons": comparisons,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=Path(__file__).resolve().parent / "results")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "RESULTS.md")
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--json-output", type=Path, help="Combined JSON destination (default: Markdown path with .json suffix)")
    parser.add_argument("--repeat-cohort", action="append", default=[], metavar="NAME",
                        help="Explicit additional activity-repeat[-N]-net10-METHOD cohort to require and combine")
    args = parser.parse_args()
    try:
        root, output = args.results_dir.resolve(), args.output.resolve()
        states = [load_checkpoint(root, checkpoint) for checkpoint in checkpoint_plan(args.repeat_cohort)]
        rows, expected = aggregate(states)
        json_output = (args.json_output or output.with_suffix(".json")).resolve()
        require(json_output != output, "Markdown and JSON output paths must differ")
        document, complete = render(states, rows, expected, root, output, json_output)
        combined = aggregate_document(states, rows, expected, root, complete)
        output.parent.mkdir(parents=True, exist_ok=True)
        json_output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(document, encoding="utf-8")
        json_output.write_text(json.dumps(combined, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        completed = sum(state["status"] == "analyzed" for state in states)
        print(f"Wrote {output}: {completed}/{len(states)} checkpoints, {len(rows)}/{len(expected)} comparisons; "
              f"{'complete' if complete else 'partial'}.")
        if args.require_complete and not complete:
            print("Incomplete checkpoints: " + ", ".join(state["checkpoint"].name for state in states
                                                         if state["status"] != "analyzed"), file=sys.stderr)
            return 1
        return 0
    except (ReportError, KeyError, OSError, ValueError, TypeError) as error:
        print(f"Report failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
