#!/usr/bin/env python3
"""Validate and summarize completed blocked BenchmarkDotNet Full JSON runs.

Usage: taskset -c 1 python3 analyze.py results/no-listener-net10 [other_run ...]
Each run gets analysis/{processes,comparisons}.{json,csv}; raw inputs are read only.
Confidence intervals use paired block differences, never pooled iterations.
"""

import argparse
import csv
import fnmatch
import gzip
import hashlib
import json
import math
import re
import statistics
import sys
from pathlib import Path


MEASURED_ITERATIONS = 20
WARMUP_ITERATIONS = 40
JOB_RE = re.compile(r":\s*(?P<profile>[A-Za-z][A-Za-z0-9_]*)-B(?P<block>\d+)\(")
METHOD_RE = re.compile(r"\[Benchmark\]\s+public\s+\S+\s+(\w+)\s*\(")
# Two-sided 95% Student t quantiles, degrees of freedom 1..30.
T95 = (
    None, 12.706204736, 4.302652730, 3.182446305, 2.776445105,
    2.570581836, 2.446911851, 2.364624252, 2.306004135, 2.262157163,
    2.228138852, 2.200985160, 2.178812830, 2.160368656, 2.144786688,
    2.131449546, 2.119905299, 2.109815578, 2.100922040, 2.093024054,
    2.085963447, 2.079613845, 2.073873068, 2.068657610, 2.063898562,
    2.059538553, 2.055529439, 2.051830516, 2.048407142, 2.045229642,
    2.042272456,
)


class AnalysisError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise AnalysisError(message)


def read_json(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, mode="rt", encoding="utf-8-sig") as stream:
        return json.load(stream)


def source_info(path):
    return {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def benchmark_sources(run_dir, arguments, metadata):
    """Verify captured source and optional helper-produced PE/PDB binding."""
    benchmark_type = arguments.get("type", "ActivityFactoryBenchmarks")
    source_names = {"ActivityFactoryBenchmarks": "Program.cs", "LinkSamplingBenchmarks": "LinkSamplingBenchmarks.cs"}
    require(benchmark_type in source_names, f"Unsupported benchmark type: {benchmark_type}")
    snapshot_hashes = metadata.get("sourceSnapshotSha256")
    if snapshot_hashes is None:
        require(benchmark_type == "ActivityFactoryBenchmarks", "LinkSamplingBenchmarks requires captured source snapshots")
        program = run_dir.parent.parent / "Program.cs"
        return program, [program], {"status": "legacy_current_source_unbound"}, (
            "Legacy run: the current Program.cs hash is used for method coverage only. "
            "run.json has no captured source hashes, so this does not establish build-time source binding.")
    require(isinstance(snapshot_hashes, dict) and bool(snapshot_hashes), "Invalid source snapshot hash manifest")
    inputs, snapshots = [], {}
    source_dir = run_dir / "source"
    for name, expected_hash in snapshot_hashes.items():
        require(Path(name).name == name and name not in (".", ".."), f"Unsafe snapshot filename: {name}")
        require(isinstance(expected_hash, str) and re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash),
                f"Invalid SHA256 for snapshot: {name}")
        path = source_dir / name
        require(path.is_file(), f"Missing source snapshot: {path}")
        require(source_info(path)["sha256"] == expected_hash.lower(), f"Source snapshot hash mismatch: {path}")
        snapshots[name], inputs = path, inputs + [path]
    require(source_names[benchmark_type] in snapshots, f"Missing source snapshot for {benchmark_type}")
    require("Program.cs" in snapshots, "Missing captured launch configuration Program.cs")
    proof_dir = run_dir / "provenance"
    csharp_sources = {name: path for name, path in snapshots.items() if path.suffix == ".cs"}
    proofs = [proof_dir / (Path(name).stem + ".json") for name in csharp_sources]
    provenance = {"status": "source_snapshots_verified", "snapshots_sha256": snapshot_hashes}
    if any(path.exists() for path in proofs):
        require(all(path.is_file() for path in proofs), "Incomplete source-to-binary provenance reports")
        identity, verified = None, []
        for name, path in csharp_sources.items():
            proof_path = proof_dir / (Path(name).stem + ".json")
            proof = read_json(proof_path)
            require(proof.get("schemaVersion") == 1 and proof.get("pdbMatchesApplication") is True
                    and proof.get("sourceMatchesDocument") is True, f"Invalid provenance proof: {proof_path}")
            require(Path(proof["sourcePath"]).name == name and Path(proof["documentName"]).name == name,
                    f"Provenance source document mismatch: {proof_path}")
            require(proof["sourceSha256"] == snapshot_hashes[name].lower(), f"Provenance source hash mismatch: {proof_path}")
            algorithm = {"SHA256": "sha256", "SHA1": "sha1"}.get(proof["documentHashAlgorithm"])
            require(algorithm is not None, f"Unsupported PDB source checksum: {proof_path}")
            require(hashlib.new(algorithm, path.read_bytes()).hexdigest() == proof["documentHash"],
                    f"PDB source checksum mismatch: {proof_path}")
            require(proof["peCodeViewPdbGuid"] == proof["portablePdbGuid"]
                    and proof["peCodeViewPdbStamp"] == proof["portablePdbStamp"]
                    and proof["peCodeViewPdbAge"] == 1, f"PE/PDB identity mismatch: {proof_path}")
            app = proof_dir / Path(proof["appPath"]).name
            pdb = proof_dir / Path(proof["pdbPath"]).name
            require(app.suffix == ".dll" and pdb.suffix == ".pdb" and app.stem == pdb.stem,
                    f"Invalid captured assembly/PDB pair: {proof_path}")
            if arguments.get("app"):
                require(app.name == Path(arguments["app"]).name, f"Captured assembly differs from requested app: {proof_path}")
            require(app.is_file() and source_info(app)["sha256"] == proof["appSha256"],
                    f"Captured assembly hash mismatch: {proof_path}")
            require(pdb.is_file() and source_info(pdb)["sha256"] == proof["pdbSha256"],
                    f"Captured PDB hash mismatch: {proof_path}")
            current_identity = proof["appSha256"], proof["pdbSha256"], proof["assemblyMvid"]
            require(identity in (None, current_identity), "Source proofs refer to different captured binaries")
            identity = current_identity
            inputs += [proof_path, app, pdb]
            verified.append(proof)
        provenance.update(status="captured_binary_and_csharp_sources_bound_by_helper", proofs=verified)
        note = ("Captured C# snapshot hashes match run.json and the helper-reported portable-PDB source checksums. "
                "Helper PE/PDB identities and captured assembly/PDB SHA256 hashes were validated. "
                "The helper establishes C# source binding for the captured benchmark assembly; project snapshots are separately hashed.")
    else:
        note = ("All captured source snapshots match run.json. No source-to-captured-binary helper proof is available; "
                "snapshot hashes alone do not establish build-time source binding.")
    return snapshots[source_names[benchmark_type]], list(dict.fromkeys(inputs)), provenance, note


def job_key(display):
    match = JOB_RE.search(display)
    require(match is not None, f"Missing blocked job identifier: {display}")
    return match["profile"], int(match["block"])


def normalized(row):
    operations, nanoseconds = row["Operations"], row["Nanoseconds"]
    require(operations > 0 and math.isfinite(nanoseconds) and nanoseconds >= 0,
            f"Invalid timing measurement: {row}")
    return nanoseconds / operations


def describe(values):
    require(bool(values), "Cannot describe an empty measurement set")
    return {
        "n": len(values), "mean_ns": statistics.mean(values),
        "median_ns": statistics.median(values), "min_ns": min(values),
        "max_ns": max(values),
        "sd_ns": statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def process_probes(console_path):
    """Read target-process metadata, without using the BDN host environment."""
    if not console_path.exists():
        return {}
    result, current = {}, None
    with console_path.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if line.startswith("// Benchmark: "):
                display = line.removeprefix("// Benchmark: ").strip()
                profile, block = job_key(display)
                method = display.split(":", 1)[0].rsplit(".", 1)[-1]
                current = method, profile, block
            elif line.startswith("BENCH_PROBE "):
                require(current is not None, "BENCH_PROBE without an active benchmark")
                require(current not in result, f"Duplicate process probe: {current}")
                probe = json.loads(line.removeprefix("BENCH_PROBE "))
                require(probe.get("benchmarkCase") == current[1], f"Probe profile mismatch: {current}")
                result[current] = probe
    return result


def expected_methods(filters, program_path):
    require(program_path.is_file(), f"Missing benchmark source: {program_path}")
    available = METHOD_RE.findall(program_path.read_text(encoding="utf-8-sig"))
    require(len(available) == len(set(available)) and available, "Ambiguous benchmark methods in source")
    selected = set()
    for pattern in filters:
        matched = {method for method in available if fnmatch.fnmatchcase(method, pattern)}
        require(bool(matched), f"Method filter has no source match: {pattern}")
        selected.update(matched)
    return sorted(selected), available


def summarize_process(benchmark, runtime, suite, sensitivity, probe, source_path, benchmark_type="ActivityFactoryBenchmarks"):
    display = benchmark["DisplayInfo"]
    profile, block = job_key(display)
    method = benchmark["Method"]
    context = f"{suite}/{method}/{profile}/B{block:02d}"
    require(benchmark.get("Type") == benchmark_type, f"{context}: benchmark type mismatch")
    require(benchmark.get("Parameters", "") in ("", None), f"{context}: unexpected parameters")
    require(benchmark.get("FullName", "").rsplit(".", 1)[-1] == method,
            f"{context}: inconsistent method metadata")
    expected_runtime = ".NET " + runtime.removeprefix("net")
    require(f"Runtime={expected_runtime}," in display, f"{context}: target runtime mismatch")
    for expected in ("OutlierMode=DontRemove", "IterationCount=20", "LaunchCount=1", "WarmupCount=40"):
        require(re.search(r"(?<![A-Za-z])" + re.escape(expected) + r"(?=[,)])", display),
                f"{context}: expected job setting {expected}")

    measurements = benchmark.get("Measurements", [])
    require({row["LaunchIndex"] for row in measurements} == {1}, f"{context}: expected one launch")

    def stage(mode, name):
        return [row for row in measurements if row["IterationMode"] == mode and row["IterationStage"] == name]

    actual, result = stage("Workload", "Actual"), stage("Workload", "Result")
    overhead, warmup = stage("Overhead", "Actual"), stage("Workload", "Warmup")
    for name, rows, expected_count in (
        ("Actual", actual, MEASURED_ITERATIONS), ("Result", result, MEASURED_ITERATIONS),
        ("Warmup", warmup, WARMUP_ITERATIONS),
    ):
        require(len(rows) == expected_count, f"{context}: {len(rows)} {name} rows; expected {expected_count}")
        require([row["IterationIndex"] for row in rows] == list(range(1, expected_count + 1)),
                f"{context}: nonconsecutive {name} iteration indexes")
    require(bool(overhead), f"{context}: no measured overhead")
    operation_counts = {row["Operations"] for row in actual + result + overhead}
    require(len(operation_counts) == 1, f"{context}: inconsistent operation counts")
    actual_values, result_values = list(map(normalized, actual)), list(map(normalized, result))
    overhead_values = list(map(normalized, overhead))
    overhead_total = statistics.median(row["Nanoseconds"] for row in overhead)
    for before, after in zip(actual, result):
        expected = max(0.0, before["Nanoseconds"] - overhead_total) / before["Operations"]
        if expected < 0.1:
            expected = 0.0
        require(math.isclose(normalized(after), expected, rel_tol=1e-10, abs_tol=1e-8),
                f"{context}: Result does not retain matching Actual after overhead subtraction")
    stats = benchmark.get("Statistics") or {}
    require(stats.get("N") == MEASURED_ITERATIONS, f"{context}: report statistics count mismatch")
    require(math.isclose(stats["Mean"], statistics.mean(result_values), rel_tol=1e-10, abs_tol=1e-8),
            f"{context}: report mean mismatch")
    originals = stats.get("OriginalValues", [])
    require(len(originals) == len(result_values) and all(
        math.isclose(x, y, rel_tol=1e-10, abs_tol=1e-8) for x, y in zip(originals, result_values)),
        f"{context}: report original values mismatch")
    memory = benchmark.get("Memory") or {}
    allocated = memory.get("BytesAllocatedPerOperation")
    require(isinstance(allocated, (int, float)) and math.isfinite(allocated) and allocated >= 0,
            f"{context}: missing/invalid allocation measurement")
    if probe:
        require(probe.get("benchmarkType", "ActivityFactoryBenchmarks") == benchmark_type,
                f"{context}: measured benchmark type mismatch")
        require(probe.get("framework", "").startswith(expected_runtime + "."),
                f"{context}: measured process framework mismatch")
        for field, expected in (
            ("affinity", 8), ("serverGc", False), ("defaultIdFormat", "W3C"),
            ("forceDefaultIdFormat", True), ("tiering", sensitivity["tiering"]),
        ):
            require(probe.get(field) == expected,
                    f"{context}: measured process {field}={probe.get(field)!r}; expected {expected!r}")
        require((probe.get("sdk") not in (None, "", "none")) == sensitivity["sdk_provider"],
                f"{context}: measured application SDK provider mode mismatch")
    return {
        "suite": suite, "runtime": runtime, "sensitivity": sensitivity, "benchmark_type": benchmark_type,
        "method": method, "profile": profile, "block": block, "launch_index": 1,
        "actual": describe(actual_values), "result": describe(result_values),
        "overhead_actual": describe(overhead_values),
        "overhead_actual_median_total_ns": overhead_total,
        "operations_per_iteration": actual[0]["Operations"],
        "warmup_iterations": len(warmup),
        "allocated_bytes_per_op": allocated,
        "memory_source": "BenchmarkDotNet Full JSON Memory.BytesAllocatedPerOperation",
        "memory": memory,
        "actual_ns_per_op": actual_values, "result_ns_per_op": result_values,
        "overhead_actual_ns_per_op": overhead_values,
        "bdn_flagged_outliers_retained": stats.get("AllOutliers", []),
        "target_process_probe": probe or None,
        "source_report": str(source_path.resolve()), "display_info": display,
    }


def compare(processes, profiles, methods, blocks):
    lookup = {(p["method"], p["profile"], p["block"]): p for p in processes}
    pairs = [("AutomaticParent", "ManualParent"), ("AutomaticLink", "ManualLink")]
    if "Disabled" in profiles:
        pairs += [(control, "Disabled") for control in ("NoIncoming", "ExtractionOff", "NoAgent")]
    comparisons = []
    for candidate, baseline in pairs:
        if candidate not in profiles or baseline not in profiles:
            continue
        for method in methods:
            paired = []
            for block in range(blocks):
                a, b = lookup[method, candidate, block], lookup[method, baseline, block]
                am, bm = a["result"]["mean_ns"], b["result"]["mean_ns"]
                require(bm > 0, f"Cannot calculate a ratio with zero baseline: {method}/{baseline}")
                paired.append({
                    "block": block, "candidate_mean_ns": am, "baseline_mean_ns": bm,
                    "delta_ns": am - bm, "ratio": am / bm,
                    "candidate_actual_mean_ns": a["actual"]["mean_ns"],
                    "baseline_actual_mean_ns": b["actual"]["mean_ns"],
                    "actual_delta_ns": a["actual"]["mean_ns"] - b["actual"]["mean_ns"],
                    "candidate_overhead_median_ns": a["overhead_actual"]["median_ns"],
                    "baseline_overhead_median_ns": b["overhead_actual"]["median_ns"],
                    "candidate_allocated_bytes_per_op": a["allocated_bytes_per_op"],
                    "baseline_allocated_bytes_per_op": b["allocated_bytes_per_op"],
                    "allocation_delta_bytes_per_op": a["allocated_bytes_per_op"] - b["allocated_bytes_per_op"],
                })
            deltas, ratios = [p["delta_ns"] for p in paired], [p["ratio"] for p in paired]
            n, df = len(deltas), len(deltas) - 1
            require(1 <= df < len(T95), "95% t table supports 2..31 independent blocks")
            mean, sd = statistics.mean(deltas), statistics.stdev(deltas)
            se = sd / math.sqrt(n)
            margin = T95[df] * se
            actual_deltas = [p["actual_delta_ns"] for p in paired]
            actual_mean = statistics.mean(actual_deltas)
            actual_margin = T95[df] * statistics.stdev(actual_deltas) / math.sqrt(n)
            comparisons.append({
                "suite": processes[0]["suite"], "runtime": processes[0]["runtime"],
                "benchmark_type": processes[0].get("benchmark_type", "ActivityFactoryBenchmarks"),
                "sensitivity": processes[0]["sensitivity"], "method": method,
                "candidate": candidate, "baseline": baseline, "independent_blocks": n,
                "degrees_of_freedom": df, "delta_mean_ns": mean, "delta_sd_ns": sd,
                "delta_standard_error_ns": se, "t95_critical": T95[df],
                "delta_ci95_low_ns": mean - margin, "delta_ci95_high_ns": mean + margin,
                "actual_delta_mean_ns": actual_mean,
                "actual_delta_ci95_low_ns": actual_mean - actual_margin,
                "actual_delta_ci95_high_ns": actual_mean + actual_margin,
                "ratio_mean": statistics.mean(ratios), "ratio_min": min(ratios), "ratio_max": max(ratios),
                "candidate_process_mean_ns": statistics.mean(p["candidate_mean_ns"] for p in paired),
                "baseline_process_mean_ns": statistics.mean(p["baseline_mean_ns"] for p in paired),
                "allocation_delta_mean_bytes_per_op": statistics.mean(p["allocation_delta_bytes_per_op"] for p in paired),
                "paired_blocks": paired,
            })
    return comparisons


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        if not rows:
            return
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def process_csv_row(process):
    result = {key: process[key] for key in ("suite", "runtime", "benchmark_type", "method", "profile", "block", "launch_index")}
    result.update(process["sensitivity"])
    result.update({key: process[key] for key in ("operations_per_iteration", "warmup_iterations", "allocated_bytes_per_op")})
    for prefix in ("actual", "result", "overhead_actual"):
        result.update({f"{prefix}_{key}": value for key, value in process[prefix].items()})
    probe = process["target_process_probe"] or {}
    result.update({f"target_{key}": probe.get(key) for key in (
        "framework", "diagnosticSource", "diagnosticSourceFile", "diagnosticSourceLocation", "affinity", "tiering", "sdk")})
    result["source_report"] = process["source_report"]
    return result


def analyze(run_dir, output_dir=None):
    run_dir = run_dir.resolve()
    metadata_path = run_dir / "run.json"
    metadata = read_json(metadata_path)
    require(metadata.get("exitCode") == 0 and "end" in metadata, f"Run is not successfully completed: {run_dir}")
    arguments, environment = metadata["arguments"], metadata["environment"]
    program_path, source_inputs, source_provenance, source_note = benchmark_sources(run_dir, arguments, metadata)
    benchmark_type = arguments.get("type", "ActivityFactoryBenchmarks")
    runtime, suite = arguments["runtime"], arguments["name"]
    require(environment.get("PROCESS_BENCH_RUNTIME") == runtime, "Runtime metadata disagreement")
    profiles = arguments["cases"].split(",")
    require(profiles and len(profiles) == len(set(profiles)), "Duplicate/empty profiles")
    require(environment.get("PROCESS_BENCH_CASES") == arguments["cases"], "Profile metadata disagreement")
    blocks = int(arguments.get("blocks") or 0)
    require(2 <= blocks <= 31, "Expected a blocked run with 2..31 blocks")
    require(int(environment.get("PROCESS_BENCH_BLOCKS", 0)) == blocks, "Block metadata disagreement")
    methods, available = expected_methods(arguments["methods"], program_path)
    sensitivity = {"tiering": arguments.get("tiering") or "default", "sdk_provider": bool(arguments.get("sdk", False))}
    require(environment.get("PROCESS_BENCH_TIERING", "default") == sensitivity["tiering"], "Tiering metadata disagreement")
    require(environment.get("PROCESS_BENCH_SDK") == str(sensitivity["sdk_provider"]).lower(), "SDK provider metadata disagreement")
    report_dir = run_dir / "bdn" / "results"
    reports = sorted(report_dir.glob("*-report-full.json"))
    reports += sorted(path for path in report_dir.glob("*-report-full.json.gz")
                      if not path.with_suffix("").exists())
    require(bool(reports), f"No Full JSON reports: {run_dir}")
    console_path = run_dir / "console.log"
    probes, processes = process_probes(console_path), []
    for report_path in reports:
        report = read_json(report_path)
        require(bool(report.get("Benchmarks")), f"Empty report: {report_path}")
        for benchmark in report["Benchmarks"]:
            profile, block = job_key(benchmark["DisplayInfo"])
            key = benchmark["Method"], profile, block
            if console_path.exists():
                require(key in probes, f"Missing measured process probe: {key}")
            processes.append(summarize_process(benchmark, runtime, suite, sensitivity, probes.get(key), report_path, benchmark_type))
    expected = {(method, profile, block) for method in methods for profile in profiles for block in range(blocks)}
    actual = [(p["method"], p["profile"], p["block"]) for p in processes]
    require(len(actual) == len(set(actual)), "Duplicate process cells in source reports")
    require(set(actual) == expected,
            f"Cell coverage mismatch: missing={sorted(expected - set(actual))}; unexpected={sorted(set(actual) - expected)}")
    if console_path.exists():
        require(set(probes) == expected, "Console probe cell coverage differs from report coverage")
    processes.sort(key=lambda p: (p["method"], p["block"], p["profile"]))
    comparisons = compare(processes, profiles, methods, blocks)
    provenance = {
        "schema_version": 1,
        "run_metadata": metadata,
        "inputs": [source_info(metadata_path)] + [source_info(p) for p in source_inputs] + [source_info(p) for p in reports]
                  + ([source_info(console_path)] if console_path.exists() else []),
        "checks": {"profiles": profiles, "methods": methods, "available_source_methods": available,
                   "blocks": blocks, "expected_processes": len(expected), "actual_processes": len(processes),
                   "actual_rows_per_process": MEASURED_ITERATIONS, "result_rows_per_process": MEASURED_ITERATIONS,
                   "all_actual_rows_retained": True, "warmup_rows_per_process": WARMUP_ITERATIONS,
                   "target_probe_coverage": len(probes), "host_environment_used_for_job_metadata": False},
        "statistical_unit": "One independently launched process mean per profile and block; differences paired by block.",
        "ci_assumptions": "Pointwise two-sided Student t95 on independent block differences; assumes approximately normal block differences. No multiplicity adjustment; four blocks provide limited precision.",
        "runtime_note": "Requested runtime/sensitivity come from run.json; patch/file versions come only from target-process BENCH_PROBE when present.",
        "source_provenance": source_provenance,
        "source_note": source_note,
        "sdk_note": "sdk_provider=false means a minimal application ActivityListener and no application TracerProvider/exporters; attached controls still initialize SDK globals.",
    }
    destination = output_dir.resolve() if output_dir else run_dir / "analysis"
    destination.mkdir(parents=True, exist_ok=True)
    for name, rows in (("processes", processes), ("comparisons", comparisons)):
        (destination / f"{name}.json").write_text(json.dumps({**provenance, name: rows}, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        csv_rows = [process_csv_row(p) for p in rows] if name == "processes" else [
            {**{key: value for key, value in p.items() if key not in ("paired_blocks", "sensitivity")}, **p["sensitivity"]}
            for p in rows
        ]
        write_csv(destination / f"{name}.csv", csv_rows)
    print(f"{suite}: validated {len(processes)} processes ({len(methods)} methods x {len(profiles)} profiles x {blocks} blocks)")
    for p in comparisons:
        print(f"  {p['method']} {p['candidate']}/{p['baseline']}: delta {p['delta_mean_ns']:.3f} ns "
              f"[95% CI {p['delta_ci95_low_ns']:.3f}, {p['delta_ci95_high_ns']:.3f}], "
              f"paired ratio {p['ratio_mean']:.4f} [{p['ratio_min']:.4f}, {p['ratio_max']:.4f}], n={blocks}")
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", type=Path, nargs="+")
    parser.add_argument("--output-dir", type=Path, help="Override destination (one input run only)")
    args = parser.parse_args()
    if args.output_dir and len(args.run_dirs) != 1:
        parser.error("--output-dir requires exactly one input run")
    try:
        for directory in args.run_dirs:
            analyze(directory, args.output_dir)
    except (AnalysisError, KeyError, OSError, json.JSONDecodeError) as error:
        print(f"Analysis failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
