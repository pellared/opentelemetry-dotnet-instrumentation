# ActivitySource process-context propagation: performance methodology

This artifact measures steady-state activity-factory costs for OpenTelemetry
.NET automatic instrumentation commit
`536388a48532750a501e2bf94b36e7b946d69a82`. Numerical findings and the accepted
run inventory belong in the forthcoming [RESULTS.md](RESULTS.md). This document
defines the controls, workloads, execution protocol, provenance, and limits of
those comparisons.

The planned publication uses a short artifact-root `README.md` index. This
methodology and `RESULTS.md` remain in `process-context-perf/`, with the data and
scripts. Reproduction sources retain their original directory names as siblings:

```text
README.md
process-context-perf/
    PERFORMANCE-METHODOLOGY.md
    RESULTS.md
    RESULTS.json
    manifest.json
    results/
process-context-link-sampling-perf/
process-context-provenance/
```

The primary comparison is automatic propagation versus equivalent, cached manual
propagation with the same profiler attached. Comparing a parented activity with
an unrelated root would also change trace-ID generation and potentially
sampling. Such a difference would not isolate the automation cost.

## Controls and hook registration

Each profile runs in a fresh benchmark process. Except for `NoAgent`, the CLR
profiler and startup hook are loaded. The agent's SDK provider setup is disabled,
other trace integrations are disabled, metrics and logging signals are disabled,
child-process injection is disabled, and `OTEL_TRACES_EXPORTER=none`.

| Profile | Process instrumentation | Factory inputs and purpose |
| --- | --- | --- |
| `ManualParent` | Disabled | Supplies the cached incoming remote `ActivityContext` to applicable factory calls. Primary parent control. |
| `AutomaticParent` | Enabled, `parent` mode | Supplies a default parent context; the factory hook supplies the cached incoming parent. |
| `ManualLink` | Disabled | Supplies cached read-only incoming links, including a precombined collection when the caller already has a link. Primary link control. |
| `AutomaticLink` | Enabled, `link` mode | Supplies no incoming link; the hook supplies it, retaining caller links and avoiding a duplicate. |
| `Disabled` | Disabled | Ordinary inputs without manually propagated context. Attached-agent control. |
| `NoIncoming` | Enabled, `parent` mode | `TRACEPARENT` is empty, so no valid incoming trace context is extracted. |
| `ExtractionOff` | Enabled, `off` mode | Valid incoming fields are present, but extraction is disabled. |
| `NoAgent` | Agent and profiler disabled | Ordinary inputs with the same application listener. Runtime-only control. |

The fixture uses incoming trace ID `11111111111111111111111111111111`, span ID
`2222222222222222`, sampled flag `01`, and trace state `vendor=value`. A supplied
context uses trace ID `33333333333333333333333333333333`, span ID
`4444444444444444`, and trace state `supplied=value`. Parsing and construction of
these fixtures and their read-only link collections occur outside measurement.

At this commit, the private nine-argument `ActivitySource.CreateActivity` hook
is registered only after startup extraction yields a valid trace context.
`NoIncoming` and `ExtractionOff` therefore measure an unpatched activity factory,
not an installed hook taking an early exit. With a valid incoming context, the
hook is installed globally; ambient or supplied parents cause its propagation
helper to return without changing those inputs. Those workloads measure the
cost of interception and checks even when no context is added.

Attached profiles still initialize OpenTelemetry SDK globals, including the
default propagators. In this artifact, `sdk=false` means that the application
does not create a `TracerProvider`; it does not mean that no SDK code is loaded.
All profiles explicitly set `Activity.DefaultIdFormat=W3C` and
`Activity.ForceDefaultIdFormat=true`, including `NoAgent`, to prevent SDK
initialization from changing the ID-format algorithm between controls.

## Workloads

The primary fixture owns one minimal `ActivityListener`. Its ordinary recorded
source returns `AllDataAndRecorded` without examining links. Separate sources
exercise `PropagationData`, unconditional `None`, and `None` after counting
links. No exporter, span processor, collector, or application request is involved.

| Method | Work performed per operation |
| --- | --- |
| `Root` | Starts and disposes a recorded activity. Parent/link profiles produce equivalent relationships using manual or automatic inputs. |
| `RootEmptyLinks` | Same operation with a non-null empty caller collection in automatic mode. The manual link control supplies the equivalent cached incoming singleton. |
| `RootExistingLink` | Starts and disposes an activity with one supplied link. The manual link control passes cached `[supplied, incoming]`; automatic link mode appends the incoming link lazily. |
| `RootAlreadyLinked` | Supplies the cached incoming link as an existing caller link, exercising automatic de-duplication. |
| `NoListeners` | Calls the shortest `StartActivity("job")` overload on a source that has never had a listener. It returns null. This method passes no manual parent or links in any profile. |
| `Dropped` | Calls a source whose listener returns `None` without reading links. It returns null. |
| `DropReadingLinks` | The listener enumerates links, stores their count, and returns `None`. The counting/store cost is part of this deliberately different workload. |
| `AmbientParent` | Starts and disposes a child beneath an untimed, active legacy `Activity`. The incoming environment context does not replace this local parent. |
| `SuppliedContext` | Starts and disposes an activity using the supplied remote context in every profile. |
| `SuppliedParentId` | Uses the supplied W3C parent-ID string in every profile. |
| `SuppliedEmptyParentId` | Uses an explicit empty parent-ID string to request an independent root in every profile. |
| `CreateOnly` | Returns a sampled, unstarted activity from `CreateActivity` to BenchmarkDotNet's consumer. It does not start or dispose that activity. |
| `CreateThenStart` | Calls `CreateActivity`, then `Start`, then disposes the activity. Sampling occurs during creation. |
| `PropagationOnly` | Starts and disposes an activity whose listener requests `PropagationData`, rather than recorded data. |

`Root` uses the context-taking overload, passing a default context in automatic
mode. `NoListeners` and `AmbientParent` use the shortest overload. These APIs
share the intercepted private factory. Each started activity is disposed within
the measured operation; the ambient parent is created and disposed outside the
measurement window. Timed ordinary methods do not format IDs, print output, or
run correctness assertions.

Two secondary fixtures address costs that the minimal listener deliberately
does not include:

- With `PROCESS_BENCH_SDK=true`, the application creates an OpenTelemetry
  `TracerProvider` using `ParentBasedSampler(new AlwaysOnSampler())` and subscribes
  it to the recorded source. The custom listener excludes that source. The
  secondary suite measures `Root`, `NoListeners`, and `CreateOnly` on .NET 10,
  without processors or exporters. The never-subscribed source remains
  unsubscribed in this mode.
- The sibling `LinkSamplingBenchmarks` fixture measures `Root` and
  `RootExistingLink` on .NET 10. Its listener enumerates links and returns
  `AllDataAndRecorded` only when it finds the incoming trace/span IDs; otherwise
  it returns `AllData`. Setup verifies that both timed controls are recorded.
  Activity creation subsequently enumerates links to copy them. This exposes
  repeated enumeration of the automatic deferred append iterator. There are no
  per-operation counters in this successful sampling callback.

Null and non-null link inputs are intentionally distinct. Automatic link mode
reuses a cached read-only singleton for null inputs. For supplied collections it
creates a deferred append/de-duplication iterator. A dropping sampler need not
enumerate that iterator, but constructing it can still allocate. The manual
existing-link control uses a precombined cached collection, so its comparison
includes the cost of automatic combination, not merely the bytecode prologue.

## Execution and environment

The recorded environment is Linux x64 on Ubuntu 24.04.4 LTS, kernel
`6.17.0-1017-aws`, under KVM, with an AMD EPYC 7571 CPU model. The guest exposes
sixteen vCPUs arranged as eight cores with two threads each; this is guest
topology. The host's physical-core allocation is unverified. Benchmark processes
are pinned to logical CPU 3 with affinity mask `0x8`. CPU 11 is its SMT sibling.
Affinity does not reserve the
core or offline the sibling. Monitoring uses CPU 1; other analysis is kept
lightweight, with no intentional builds or tests during measurement. The
virtualized host remains unreserved, and governor, turbo, and hardware
performance-counter controls are unavailable.

The build SDK is .NET SDK `10.0.403`; the recorded runtime and DiagnosticSource
versions are:

| Target | Runtime patch | DiagnosticSource assembly version | Observed file version |
| --- | --- | --- | --- |
| .NET 8 | `8.0.33` | `10.0.0.0` | `10.0.25.52411` |
| .NET 9 | `9.0.22` | `10.0.0.0` | `10.0.25.52411` |
| .NET 10 | `10.0.14` | `10.0.0.0` | `10.0.1426.52326` |

The project pins `System.Diagnostics.DiagnosticSource` package `10.0.0`,
BenchmarkDotNet `0.15.8`, and OpenTelemetry `1.20.1`. The target-process probe,
rather than the package reference alone, identifies the actual loaded assembly,
file version, and location. .NET 10 resolves a different DiagnosticSource file
than .NET 8/9. Cross-runtime differences therefore do not isolate CLR changes
alone. Comparisons within a runtime must use matching loaded library versions.
Managed instrumentation, native profiler, and benchmark assemblies use Release
builds. The primary GC configuration is concurrent workstation GC; target probes
record server-GC status and latency mode. Primary jobs retain runtime-default
tiering. A separate .NET 10 sensitivity suite sets
`DOTNET_TieredCompilation=0`; its observations remain separate.

Each cohort launches four fresh processes per method and profile, one per block
(`B00` through `B03`). A block contains one process for each selected profile.
`BlockOrderer` uses seed `5398` to shuffle the initial profile order and
then cyclically rotates that order across blocks. With four primary profiles,
each occupies every position once. The two-profile link-sampling suite repeats
each position twice. Methods are run sequentially, and the suite launcher waits
for one run before starting the next.

After observing between-process variance, exactly one additional four-block
cohort was frozen for each of the .NET 10 `Root`, `AmbientParent`, `Dropped`, and
`SuppliedContext` primary comparisons. These are the
`activity-repeat-net10-<method>` phases in `suite.py`. Their main results combine
eight distinct cohort/block observations, while also showing each four-block
cohort separately. A four-block `NoListeners` repeat was already queued; pooling
it with the initial cohort likewise gives eight blocks, with the legacy source
provenance limitation described below retained in that pooled result. Other
comparisons retain four blocks. There is no further precision-based stopping or
additional repetition planned. These repeats were selected after inspecting
variance, so their uncertainty intervals are nominal and exploratory.

Each worker performs the following outside the reported measurement rows:

1. Initializes fixtures and its listener or application-owned provider.
2. Waits until an ordinary probe exhibits the expected automatic relationship,
   or the expected absence of one in a control. Automatic jobs time out if the
   asynchronous ReJIT effect never becomes observable.
3. Validates equivalent inputs and records a `BENCH_PROBE` JSON line containing
   runtime, loaded DiagnosticSource, GC, tiering, ID format, SDK-provider mode,
   and affinity information.
4. Warms the actual selected workload for approximately ten seconds using a
   bound delegate selected from `--benchmarkName`.
5. Executes BenchmarkDotNet's forty workload warmup iterations, followed by
   twenty workload measurement iterations, with a configured target of 250 ms
   per iteration. Actual iterations may be shorter; raw durations and operation
   counts are retained rather than assuming a fixed elapsed duration.

Blocked jobs set `LaunchCount=1`, `IterationCount=20`, and
`OutlierMode=DontRemove`. Each cohort's four blocks supply four fresh processes;
`PROCESS_BENCH_LAUNCHES` does not add launches in blocked mode. The configured
one-percent relative-error target does not guarantee one-percent precision when
the measurement count is fixed. All twenty measured rows are retained,
including rows BenchmarkDotNet flags as outliers.

The standalone `--probe` path additionally validates all primary workloads,
including supplied-parent precedence, incoming remote flags/trace state,
existing-link order, de-duplication, dropped/null results, and creation-time
sampling. It is separate from timed execution. The linked sibling's frozen
`--probe` entry still runs the primary fixture; the link-sampling fixture
performs its own outcome checks in `GlobalSetup`.

## Analysis and uncertainty

`analyze.py` validates completed BenchmarkDotNet Full JSON reports against
`run.json`, the requested method/profile/block matrix, and worker probe metadata.
It requires forty warmup rows and twenty `Actual` and `Result` rows per process,
consistent operation counts, one launch, and the declared outlier policy.
BenchmarkDotNet's `Result` rows subtract its measured median invocation overhead
from `Actual` rows, with BenchmarkDotNet's small-value clamping. The analyzer
checks that transformation and retains both raw `Actual` and adjusted `Result`
values, plus the measured overhead rows. `DontRemove` does not disable overhead
subtraction.

The statistical unit is a fresh-process mean, not an individual iteration. For
each block `b`, let `A_b` and `M_b` be the arithmetic means of the twenty adjusted
ns/op measurements for an automatic profile and its matching manual control.
Define `d_b = A_b - M_b`. The reported paired difference is the mean of the four
or eight `d_b` values, with a nominal pointwise two-sided 95% Student t interval:

```text
mean(d) ± t(0.975, n - 1) × sample_standard_deviation(d) / sqrt(n)
```

Here `n=4` for a single cohort (three degrees of freedom; critical value
`3.182446305`) and `n=8` for two pooled cohorts (seven degrees of freedom;
critical value `2.364624252`). A pooled observation is identified by both cohort
and block; repeated `B00` labels in separate cohorts denote different processes,
not the same observation. Candidate and control processes are paired within
their original cohort and block before pooling the differences.

The interval assumes approximately independent, approximately normal block
differences. Fresh processes remove shared process state between observations;
they do not prove independence from shared-host noise or exclude cohort effects.
Four or eight blocks offer limited precision, and there is no
multiple-comparison adjustment. These are exploratory, nominal intervals,
particularly because the repeats were chosen after seeing between-process
variance. Eighty or 160 within-profile measurement iterations are not treated as
that many independent experiments. Each cohort remains visible alongside the
pooled estimate. BenchmarkDotNet's per-process `Error` column is not a substitute
for this paired process-level interval.

The analysis also reports the mean and range of the paired ratios
`A_b / M_b`, without presenting that range as a confidence interval. Allocations
come from BenchmarkDotNet's `Memory.BytesAllocatedPerOperation`, with paired
allocation differences reported separately. Candidate and baseline names define
the subtraction direction: in the control suite, `NoAgent - Disabled` is the
runtime-only result minus the attached control, the reverse of an
attached-profiler premium. Intervals spanning zero are reported as unresolved
at this precision, rather than establishing a speedup or zero cost.

The result tables also show a percentage point estimate:
`100 × (candidate aggregate mean − baseline aggregate mean) / baseline aggregate mean`.
This uses unrounded, equal-weight aggregate process means; it is distinct from
the mean of paired ratios reported by the per-cohort analyzer. Raw Actual
percentages use raw Actual means. The confidence intervals remain in ns/op;
no percentage confidence interval is inferred by dividing their endpoints.
A nonpositive or nonfinite baseline is reported as `n/a` (`null` in JSON).

## Provenance and audit scope

`manifest.json` records the implementation commit and clean status, host
environment, tool versions, and SHA-256 hashes of the profiler, managed agent,
harness, and orchestration scripts at capture time. Each new run records its
arguments, command, times, exit status, and copied source/project snapshot hashes
in `run.json` and `source/`. Native and managed logs and BenchmarkDotNet Full JSON
reports remain available alongside the summaries.

`manifest.initial.json` preserves the initial capture; `manifest.json` is
refreshed after the timed suite completes. Compare their production managed
DLL, native profiler, and measured-source hashes to check continuity across
the study. Orchestration and helper hashes can differ because those tools were
developed during setup; per-checkpoint snapshots and proofs retain their own
recorded scope.

The runner captures the benchmark library DLL and portable PDB from the first
executed BenchmarkDotNet target's working directory for that run. The provenance
helper checks the PE CodeView/PDB identity, the captured DLL/PDB hashes, and the
portable-PDB document checksums against the captured C# source. For the sibling
project, both linked `Program.cs` and `LinkSamplingBenchmarks.cs` are checked.
Project-file snapshots have separate hashes; PDB source checksums do not bind
those project files or every build input.

This establishes source binding for the captured benchmark library. It does
not independently establish the complete build provenance of BenchmarkDotNet's
generated workload executable, all generated boilerplate, dependencies, or every
worker binary. The recorded commands, generated execution logs, target probes,
and separately hashed instrumentation artifacts supply additional evidence with
that scope limitation. The initial host-only proof is also distinct from a
capture taken from a BenchmarkDotNet execution directory.

The earlier `results/no-listener-net10` cohort is retained as legacy evidence.
Its `run.json` predates captured source snapshots and executed-library/PDB
proofs. The analyzer marks it `legacy_current_source_unbound`: consulting the
current `Program.cs` establishes method coverage only, not which source built
the historical workload. The later `no-listener-repeat-net10` cohort follows
the captured-artifact protocol. Both cohorts are shown separately; any pooled
eight-block `NoListeners` result explicitly retains the initial cohort's legacy
provenance caveat. Pooling does not upgrade that cohort's source binding.
This caveat describes the original published measurements only. A fresh
`no-listener-net10` run uses the current runner's normal captured-source and
DLL/PDB proof protocol.

Discarded pilots, including warmup-tuning and unsuccessful runs, are preserved
locally for audit and excluded from the published artifact and accepted
comparison inventory. The published artifact includes the accepted raw reports,
captured sources and proofs where available, and the disclosed legacy cohort.

## Reproduction

Start a reproduction in a new directory containing fresh copies of the three
source project directories. Exclude every `results/`, `bin/`, and `obj/`
directory from those copies. Never run the suite in the published artifact or
reuse its accepted run directories: the captured raw corpus remains frozen.
The following commands create that separate workspace, with compilation completed
before timed execution. Use the repository's documented prerequisites to build
the Release profiler distribution from the recorded implementation commit and
verify its identity against the artifact manifest. Adapt absolute paths if the
artifact is relocated; `run.py` and `preflight.py` resolve the repository from
`PROCESS_BENCH_REPO`. Keep the three source directories as siblings, as shown in
the publication layout, because the link-sampling project links the primary
`Program.cs`, and the runner resolves the provenance helper by that layout.

```bash
set -euo pipefail
export PROCESS_PERF_ARTIFACT=/absolute/path/to/published-artifact
export PROCESS_PERF_REPRO=/absolute/path/to/new-reproduction
export PROCESS_BENCH_REPO=/home/splunker/opentelemetry-dotnet-instrumentation
mkdir "$PROCESS_PERF_REPRO"
for PROCESS_PERF_PROJECT in process-context-perf process-context-link-sampling-perf process-context-provenance; do
  rsync -a --exclude=results/ --exclude=bin/ --exclude=obj/ \
    "$PROCESS_PERF_ARTIFACT/$PROCESS_PERF_PROJECT" "$PROCESS_PERF_REPRO/"
done
cd "$PROCESS_PERF_REPRO/process-context-perf"

dotnet build ProcessContextPerf.csproj -c Release
dotnet build ../process-context-link-sampling-perf/LinkSamplingPerf.csproj -c Release
dotnet build ../process-context-provenance/Provenance.csproj -c Release

taskset -c 1 python3 preflight.py
taskset -c 1 python3 manifest.py
taskset -c 1 python3 suite.py
```

The launcher constructs a clean environment from a small allowlist of basic
shell, locale, NuGet, and .NET-root variables, then supplies each profile's
explicit settings. This prevents inherited agent configuration or profiler
settings from silently changing the controls. `suite.py` runs the detailed .NET
10 listener matrix, a smaller .NET 8/9 matrix, no-hook/raw controls, the
tiering-disabled sensitivity, the SDK secondary suite, the repeated no-listener
cohort, and the successful link-sampling supplement. It also schedules the one
additional cohort for each of the four selected primary
.NET 10 methods. The original in-flight coordinator loaded its phase list
before those additional phases were appended; after it finishes, run
`taskset -c 1 python3 suite.py --resume` to execute the appended phases without
repeating completed ones, including the accepted original no-listener cohort.
A fresh reproduction starts with all 41 scheduled checkpoints, including its
own newly captured `no-listener-net10` cohort.
The accepted output list and completion state are recorded separately;
scheduling a phase does not make it a completed result.

`package.py` freezes this original accepted corpus and its provenance policy,
including the original legacy no-listener cohort. Its gates are not a generic
republishing policy for new runs or a different host. Fresh measurements need
their own environment/provenance records and publication policy; do not modify
their metadata to make them appear to be the original corpus.

Individual reproductions can use distinct output names:

```bash
taskset -c 1 python3 run.py repro-root-net10 net10.0 --blocks 4 --methods Root

taskset -c 1 python3 run.py repro-controls-net10 net10.0 --blocks 4 \
  --cases Disabled,NoIncoming,ExtractionOff,NoAgent --methods Root NoListeners

taskset -c 1 python3 run.py repro-sdk-net10 net10.0 --blocks 4 \
  --sdk --methods Root NoListeners CreateOnly

taskset -c 1 python3 run.py repro-link-sampling-net10 net10.0 --blocks 4 \
  --cases ManualLink,AutomaticLink --type LinkSamplingBenchmarks \
  --app ../process-context-link-sampling-perf/bin/Release/net10.0/LinkSamplingPerf.dll \
  --methods Root RootExistingLink

taskset -c 1 python3 analyze.py results/repro-root-net10
```

Run benchmarks sequentially and avoid intentional work on CPU 3 and its SMT
sibling 11. Verify every worker's `BENCH_PROBE` metadata, successful outcome
checks, source-binding reports, and analyzer completion before including a
cohort in [RESULTS.md](RESULTS.md). Preserve the raw reports and use a new output
directory when changing code, dependencies, parameters, or the environment.

These measurements describe warmed, single-threaded factory calls on this host.
They exclude startup extraction and cache construction, exporter/network costs,
application work, child-process creation and environment copying, cold-start
latency, and concurrent throughput. They do not establish application-level
latency percentages or results for Windows, .NET Framework, ARM, other machines,
or arbitrary samplers and caller-provided link enumerables.
