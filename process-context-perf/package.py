#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Stage only the frozen, accepted performance artifact after every gate passes.

Run after measurements and native audits finish, on a non-benchmark CPU:
    taskset -c 1 python3 package.py --output /absolute/new/artifact-directory

This never builds, benchmarks, publishes, or includes discarded checkpoints.
The output must not exist. Raw BenchmarkDotNet Full JSON remains plain text.
"""

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

import analyze
import report
from monitor_summary import summarize


WORK = Path(__file__).resolve().parent
DEFAULT_MONITOR_SCRIPT = (WORK / "host_monitor.py" if (WORK / "host_monitor.py").is_file()
                          else Path("/tmp/process-context-host-monitor.py"))
ACCEPTED = (
    "no-listener-net10",
    "activity-net10-root",
    "activity-net10-rootemptylinks",
    "activity-net10-rootexistinglink",
    "activity-net10-rootalreadylinked",
    "activity-net10-dropped",
    "activity-net10-dropreadinglinks",
    "activity-net10-ambientparent",
    "activity-net10-suppliedcontext",
    "activity-net10-suppliedparentid",
    "activity-net10-suppliedemptyparentid",
    "activity-net10-createonly",
    "activity-net10-createthenstart",
    "activity-net10-propagationonly",
    "activity-net8-root",
    "activity-net8-nolisteners",
    "activity-net8-dropped",
    "activity-net8-ambientparent",
    "activity-net8-suppliedcontext",
    "activity-net8-createonly",
    "activity-net9-root",
    "activity-net9-nolisteners",
    "activity-net9-dropped",
    "activity-net9-ambientparent",
    "activity-net9-suppliedcontext",
    "activity-net9-createonly",
    "controls-net10-root",
    "controls-net10-nolisteners",
    "tiering-off-net10-root",
    "tiering-off-net10-nolisteners",
    "tiering-off-net10-ambientparent",
    "sdk-net10-root",
    "sdk-net10-nolisteners",
    "sdk-net10-createonly",
    "no-listener-repeat-net10",
    "activity-repeat-net10-root",
    "activity-repeat-net10-ambientparent",
    "activity-repeat-net10-dropped",
    "activity-repeat-net10-suppliedcontext",
    "link-sampling-root-net10",
    "link-sampling-existing-net10",
)
PRIMARY_FILES = (
    "Program.cs", "ProcessContextPerf.csproj", "PERFORMANCE-METHODOLOGY.md",
    "manifest.json", "manifest.initial.json", "preflight.json", "initial-host-provenance.json",
    "host-constraints.json", "analyze.py", "report.py", "native_audit.py",
    "run.py", "preflight.py", "manifest.py", "suite.py", "progress.py",
    "package.py", "monitor_summary.py",
)
SIBLING_FILES = {
    "process-context-link-sampling-perf": ("LinkSamplingPerf.csproj", "LinkSamplingBenchmarks.cs"),
    "process-context-provenance": ("Provenance.csproj", "Program.cs"),
}
ANALYSIS_FILES = (
    "processes.json", "processes.csv", "comparisons.json", "comparisons.csv",
    "native-audit.json", "native-audit.csv", "drift-audit.json",
)
LEGACY = "no-listener-net10"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def regular_file(path):
    require(path.is_file() and not path.is_symlink(), f"Missing or symbolic-link input: {path}")


def check_hash(path, expected):
    regular_file(path)
    require(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected),
            f"Invalid SHA-256 for {path}")
    require(sha256(path) == expected, f"Input hash changed; refresh its analysis/audit: {path}")


def report_gate():
    # Use a temporary output so the completeness gate does not change source reports.
    with tempfile.TemporaryDirectory(prefix="process-context-report-gate-") as temporary:
        completed = subprocess.run(
            [sys.executable, str(WORK / "report.py"), "--require-complete",
             "--output", str(Path(temporary) / "RESULTS.md")],
            cwd=WORK, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        require(completed.returncode == 0,
                "report.py --require-complete failed; no artifact was staged:\n" + completed.stdout)


def validate_checkpoint(checkpoint):
    run = WORK / "results" / checkpoint.name
    state = report.load_checkpoint(run.parent, checkpoint)
    require(state["status"] == "analyzed", f"Checkpoint is not analyzed: {checkpoint.name}")
    metadata = read_json(run / "run.json")
    require(metadata.get("analysisExitCode", 0) == 0, f"Analysis failed: {checkpoint.name}")
    start, end = metadata.get("start"), metadata.get("end")
    require(all(isinstance(value, (int, float)) and not isinstance(value, bool)
                and math.isfinite(value) for value in (start, end)) and end > start,
            f"Invalid checkpoint time window: {checkpoint.name}")
    require(all(key.startswith("PROCESS_BENCH_") for key in metadata.get("environment", {})),
            f"Unexpected captured environment fields: {checkpoint.name}")

    # This also rechecks the existing helper proofs and captured DLL/PDB hashes.
    _, source_inputs, provenance, _ = analyze.benchmark_sources(run, metadata["arguments"], metadata)
    expected_status = ("legacy_current_source_unbound" if checkpoint.name == LEGACY
                       else "captured_binary_and_csharp_sources_bound_by_helper")
    require(provenance["status"] == expected_status,
            f"Unexpected source/assembly proof status: {checkpoint.name}: {provenance['status']}")
    analysis = read_json(run / "analysis" / "processes.json")
    require(analysis.get("source_provenance") == provenance,
            f"Source/assembly proof analysis is stale: {checkpoint.name}")
    full = run / "bdn" / "results" / f"{checkpoint.benchmark_type}-report-full.json"
    expected_inputs = {run / "run.json", run / "console.log", full, *source_inputs}
    observed_inputs = set()
    for item in analysis["inputs"]:
        path = Path(item["path"])
        require(path in expected_inputs and path not in observed_inputs,
                f"Unexpected or duplicate analyzed input: {checkpoint.name}: {path}")
        check_hash(path, item["sha256"])
        observed_inputs.add(path)
    require(observed_inputs == expected_inputs, f"Incomplete analyzed input inventory: {checkpoint.name}")

    audit_path = run / "analysis" / "native-audit.json"
    regular_file(audit_path)
    audit = read_json(audit_path)
    cells = {(row["method"], row["profile"], row["block"]) for row in state["processes"]}
    rows = audit.get("processes", [])
    require(audit.get("schema_version") == 1 and audit.get("suite") == checkpoint.name
            and audit.get("expected_cells") == audit.get("audited_cells") == len(cells)
            and len(rows) == len(cells) and audit.get("warning_or_error_count") == 0,
            f"Native audit is incomplete or contains warnings/errors: {checkpoint.name}")
    expected_audit_inputs = {run / "run.json", run / "console.log", run / "analysis" / "processes.json"}
    audit_inputs = set()
    for item in audit["inputs"]:
        path = Path(item["path"])
        require(path in expected_audit_inputs and path not in audit_inputs,
                f"Unexpected or duplicate native audit input: {checkpoint.name}: {path}")
        check_hash(path, item["sha256"])
        audit_inputs.add(path)
    require(audit_inputs == expected_audit_inputs, f"Stale native audit inputs: {checkpoint.name}")
    seen, pids, raw = set(), set(), []
    for row in rows:
        cell = row["method"], row["profile"], row["block"]
        pid = row["pid"]
        require(cell in cells and cell not in seen and pid not in pids
                and row["suite"] == checkpoint.name and row["runtime"] == checkpoint.runtime
                and row["benchmark_type"] == checkpoint.benchmark_type and row["exit_code"] == 0
                and row["warning_or_error_count"] == 0 and row["warnings_or_errors"] == [],
                f"Invalid native-audit process cell: {checkpoint.name}: {cell}")
        seen.add(cell)
        pids.add(pid)
        attached, hooked = row["profile"] != "NoAgent", row["profile"].startswith("Automatic")
        require(row["profiler_attached"] == attached and row["activity_hook_expected"] == hooked
                and bool(row["activity_hook_enqueued_count"]) == hooked
                and bool(row["activity_hook_rewrite_finished_count"]) == hooked,
                f"Native hook evidence disagrees with profile: {checkpoint.name}: {cell}")
        archived = row["archived_native_file"]
        if attached:
            require(isinstance(archived, str), f"Missing archived native log: {checkpoint.name}: {cell}")
            relative = Path(archived)
            require(relative.parent == Path("analysis/raw-native-logs")
                    and re.fullmatch(rf"otel-dotnet-auto-{pid}-[^/]+-Native\.log", relative.name),
                    f"Unsafe archived native-log path: {archived}")
            check_hash(run / relative, row["native_sha256"])
            raw.append(run / relative)
        else:
            require(archived is None and row["native_file"] is None and row["native_sha256"] is None,
                    f"Unexpected profiler log for NoAgent: {checkpoint.name}: {cell}")
    require(seen == cells, f"Incomplete audited process coverage: {checkpoint.name}")
    require(audit["automatic_hook_installed"] == sum(row["activity_hook_expected"] for row in rows)
            and audit["attached_hook_absent"] == sum(row["profiler_attached"] and not row["activity_hook_expected"] for row in rows)
            and audit["no_agent_native_log_absent"] == sum(not row["profiler_attached"] for row in rows),
            f"Native-audit aggregate counts disagree: {checkpoint.name}")

    drift_path = run / "analysis" / "drift-audit.json"
    regular_file(drift_path)
    drift = read_json(drift_path)
    require(drift.get("schema_version") == 2 and drift.get("suite") == checkpoint.name
            and drift.get("quarter_size") == 5 and drift.get("all_measurements_retained") is True,
            f"Invalid drift audit or measurement retention: {checkpoint.name}")
    drift_cells = [(row["method"], row["profile"], row["block"]) for row in drift["processes"]]
    require(len(drift_cells) == len(cells) and set(drift_cells) == cells,
            f"Drift-audit process coverage differs: {checkpoint.name}")
    check_hash(run / "analysis" / "processes.json", drift.get("process_analysis_sha256"))
    check_hash(audit_path, drift.get("native_audit_sha256"))
    process_lookup = {(row["method"], row["profile"], row["block"]): row for row in state["processes"]}
    audit_lookup = {(row["method"], row["profile"], row["block"]): row for row in rows}
    for row in drift["processes"]:
        cell = row["method"], row["profile"], row["block"]
        require(row.get("pid") == audit_lookup[cell]["pid"], f"Drift-audit PID differs: {checkpoint.name}: {cell}")
        stage_flags = []
        for stage in ("actual", "result"):
            values = process_lookup[cell][stage + "_ns_per_op"]
            require(len(values) == 20, f"Wrong drift-audit stage input count: {checkpoint.name}: {cell}/{stage}")
            first, last = statistics.median(values[:5]), statistics.median(values[-5:])
            change = last - first
            percent = 100 * change / first if first else None
            expected_stage = {"first_quarter_median_ns": first, "last_quarter_median_ns": last,
                              "change_ns": change, "change_percent": percent}
            observed_stage = row.get(stage)
            require(isinstance(observed_stage, dict), f"Missing drift-audit stage: {checkpoint.name}: {cell}/{stage}")
            for key, expected in expected_stage.items():
                value = observed_stage.get(key)
                require(value is None if expected is None else
                        isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
                        and math.isclose(value, expected, rel_tol=1e-9, abs_tol=1e-8),
                        f"Drift-audit value differs: {checkpoint.name}: {cell}/{stage}/{key}")
            flag = abs(percent) >= 2 if percent is not None else abs(change) >= 1
            require(observed_stage.get("inspection_flag") is flag,
                    f"Drift-audit inspection flag differs: {checkpoint.name}: {cell}/{stage}")
            stage_flags.append(flag)
        require(row.get("inspection_flag") is any(stage_flags),
                f"Combined drift-audit inspection flag differs: {checkpoint.name}: {cell}")
    drift_inputs = set()
    for item in drift.get("inputs", []):
        path = Path(item["path"])
        if not path.is_absolute():
            path = run / path
        require(path in expected_inputs | {run / "analysis" / "processes.json", audit_path}
                and path not in drift_inputs,
                f"Unexpected or duplicate drift-audit input: {checkpoint.name}: {path}")
        check_hash(path, item["sha256"])
        drift_inputs.add(path)
    # Inspection flags are descriptive; their values never select/exclude runs.

    files = [run / "run.json", run / "console.log", full]
    files += [run / "analysis" / name for name in ANALYSIS_FILES]
    files += [path for path in source_inputs if path.is_relative_to(run)] + raw
    require(len(set(files)) == len(files), f"Duplicate packaged input: {checkpoint.name}")
    for path in files:
        regular_file(path)
    return state, files, {"name": checkpoint.name, "start": start, "end": end}


def copy_file(source, destination):
    regular_file(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def write_json(path, document):
    path.write_text(json.dumps(document, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def build_package(output, monitor, license_path, monitor_script=DEFAULT_MONITOR_SCRIPT):
    require(output.is_absolute(), "--output must be an absolute path")
    require(not output.exists() and not output.is_symlink(), f"--output must be a unique, nonexistent path: {output}")
    require(output.parent.is_dir(), f"Output parent directory does not exist: {output.parent}")
    require(not output.is_relative_to(WORK) and all(not output.is_relative_to(WORK.parent / name)
                for name in SIBLING_FILES), "Place the artifact outside all three source project directories")
    plan = report.checkpoint_plan()
    require(tuple(item.name for item in plan) == ACCEPTED and len(ACCEPTED) == 41,
            "report.py checkpoint plan differs from the frozen 41-checkpoint publication allowlist")
    report_gate()
    checked = [validate_checkpoint(checkpoint) for checkpoint in plan]
    states, windows = [item[0] for item in checked], [item[2] for item in checked]
    for name in PRIMARY_FILES:
        regular_file(WORK / name)
    for directory, names in SIBLING_FILES.items():
        for name in names:
            regular_file(WORK.parent / directory / name)
    regular_file(license_path)
    require("Apache License" in license_path.read_text(encoding="utf-8"), "Expected the repository's Apache LICENSE")
    regular_file(monitor_script)
    # Capture one complete JSONL prefix, so summary, gzip, and hash describe the
    # same bytes even if the independent monitor continues appending afterwards.
    monitor_bytes = monitor.read_bytes()
    require(bool(monitor_bytes) and monitor_bytes.endswith(b"\n"),
            "Monitor snapshot ends in a partial record; retry after the next flush")
    with tempfile.TemporaryDirectory(prefix="process-context-monitor-snapshot-") as temporary:
        snapshot = Path(temporary) / monitor.name
        snapshot.write_bytes(monitor_bytes)
        monitor_report = summarize(snapshot, windows)
    monitor_report["monitor"]["source_path"] = "host-monitor.jsonl.gz"
    monitor_report["packaged_snapshot"] = {
        "original_source": str(monitor), "artifact": "host-monitor.jsonl.gz",
        "uncompressed_sha256": hashlib.sha256(monitor_bytes).hexdigest(),
        "note": "Summary and deterministic gzip retain the same complete-record snapshot bytes.",
    }
    require(monitor_report.get("complete_coverage") is True
            and monitor_report.get("complete_metric_coverage") is True,
            "Host monitor does not completely cover every accepted checkpoint and requested metric; "
            "inspect monitor_summary.py output, or wait for the next monitor sample")

    # Nothing is staged until the report, all 41 native audits, and monitor coverage pass.
    with tempfile.TemporaryDirectory(prefix=".process-context-artifact-", dir=output.parent) as temporary:
        stage = Path(temporary)
        primary = stage / WORK.name
        for name in PRIMARY_FILES:
            copy_file(WORK / name, primary / name)
        for directory, names in SIBLING_FILES.items():
            for name in names:
                copy_file(WORK.parent / directory / name, stage / directory / name)
        for _, files, window in checked:
            for source in files:
                copy_file(source, primary / source.relative_to(WORK))
        copy_file(monitor_script, primary / "host_monitor.py")
        copy_file(license_path, stage / "LICENSE")
        write_json(primary / "host-monitor-summary.json", monitor_report)
        with (primary / "host-monitor.jsonl.gz").open("wb") as compressed:
            with gzip.GzipFile(filename="", mode="wb", fileobj=compressed, mtime=0) as target:
                target.write(monitor_bytes)

        # Regenerate with staged paths so every report link remains local after relocation.
        completed = subprocess.run(
            [sys.executable, str(primary / "report.py"), "--require-complete"],
            cwd=primary, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        require(completed.returncode == 0, "Staged report completeness check failed:\n" + completed.stdout)
        regular_file(primary / "RESULTS.md")
        regular_file(primary / "RESULTS.json")
        write_json(stage / "PACKAGE-MANIFEST.json", {
            "schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
            "checkpoint_count": len(ACCEPTED), "accepted_checkpoints": list(ACCEPTED),
            "process_count": sum(len(state["processes"]) for state in states),
            "instrumentation_commit": read_json(WORK / "manifest.json")["sourceCommit"],
            "report_require_complete": True, "native_audits_passed": len(ACCEPTED),
            "legacy_source_unbound_checkpoint": LEGACY,
            "monitor_scope": "Accepted checkpoint start/end windows, including build/setup; not isolated Actual iterations.",
            "raw_monitor": "process-context-perf/host-monitor.jsonl.gz",
            "raw_monitor_uncompressed_sha256": hashlib.sha256(monitor_bytes).hexdigest(),
            "monitor_collector_sha256": sha256(monitor_script),
            "exclusions": ["discarded/pilot/incomplete checkpoints", "stale BenchmarkDotNet log files",
                           "generated build trees", "unrestricted environment captures", "production repository checkout"],
        })
        (stage / "README.md").write_text(
            "# ActivitySource process-context propagation performance artifact\n\n"
            "- [Results and accepted checkpoint inventory](process-context-perf/RESULTS.md)\n"
            "- [Full-precision combined results](process-context-perf/RESULTS.json)\n"
            "- [Methodology, controls, uncertainty, and reproduction](process-context-perf/PERFORMANCE-METHODOLOGY.md)\n"
            "- [Environment and binary manifest](process-context-perf/manifest.json)\n"
            "- [Host constraints](process-context-perf/host-constraints.json)\n"
            "- [Host monitor summary](process-context-perf/host-monitor-summary.json)\n"
            "- [Accepted package inventory](PACKAGE-MANIFEST.json)\n\n"
            "The three source project directories retain their original sibling layout. "
            "Run reproduction commands from `process-context-perf/`. The production "
            "instrumentation checkout must be obtained and built separately at the recorded commit.\n\n"
            "Accepted raw Full JSON reports, console output, per-process native logs, "
            "source snapshots, and captured benchmark DLL/PDB proofs are included. "
            "The initial no-listener cohort has the disclosed legacy source-binding limitation; "
            "pooling it does not strengthen that provenance. Host monitoring covers complete "
            "checkpoint windows and does not establish exclusive CPU use. Discarded pilots "
            "are retained locally and excluded from this publication.\n\n"
            "Verify staged file bytes from this directory with `sha256sum -c SHA256SUMS`. "
            "The checksum file covers every other packaged file.\n",
            encoding="utf-8",
        )
        staged_files = sorted(path for path in stage.rglob("*") if path.is_file())
        (stage / "SHA256SUMS").write_text("".join(
            f"{sha256(path)}  {path.relative_to(stage).as_posix()}\n" for path in staged_files
        ), encoding="utf-8")
        # Exclusive creation prevents an existing publication directory being overwritten.
        output.mkdir(exist_ok=False)
        for child in stage.iterdir():
            child.rename(output / child.name)
    return len(staged_files) + 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--monitor", type=Path, default=Path("/tmp/process-context-host-monitor-20261109.jsonl"))
    parser.add_argument("--monitor-script", type=Path, default=DEFAULT_MONITOR_SCRIPT)
    parser.add_argument("--license", type=Path, default=Path(os.environ.get("PROCESS_BENCH_REPO",
                        str(WORK.parent / "opentelemetry-dotnet-instrumentation"))) / "LICENSE")
    args = parser.parse_args()
    try:
        require(args.output.is_absolute(), "--output must be an absolute path")
        require(not args.output.exists() and not args.output.is_symlink(),
                f"--output must be a unique, nonexistent path: {args.output}")
        output = args.output.resolve()
        count = build_package(output, args.monitor.resolve(), args.license.resolve(), args.monitor_script.resolve())
        print(f"Staged {count} files from exactly {len(ACCEPTED)} accepted checkpoints at {output}")
        print("SHA256SUMS is frozen. No Git branch, commit, or remote publication was created.")
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"Packaging failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
