using System.Diagnostics;
using System.Collections.Immutable;
using System.Reflection;
using System.Runtime;
using System.Runtime.InteropServices;
using System.Text.Json;
using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Configs;
using BenchmarkDotNet.Diagnosers;
using BenchmarkDotNet.Environments;
using BenchmarkDotNet.Exporters;
using BenchmarkDotNet.Exporters.Json;
using BenchmarkDotNet.Filters;
using BenchmarkDotNet.Jobs;
using BenchmarkDotNet.Order;
using BenchmarkDotNet.Running;
using BenchmarkDotNet.Reports;
using Perfolizer.Horology;
using Perfolizer.Mathematics.OutlierDetection;
using OpenTelemetry;
using OpenTelemetry.Trace;

if (args.Contains("--probe"))
{
    using var benchmark = new ActivityFactoryBenchmarks();
    benchmark.Setup();
    benchmark.ProbeAll();
    return;
}

var root = Environment.GetEnvironmentVariable("PROCESS_BENCH_REPO") ?? throw new InvalidOperationException("Set PROCESS_BENCH_REPO.");
var home = Path.Combine(root, "bin/tracer-home");
var runtimeName = Environment.GetEnvironmentVariable("PROCESS_BENCH_RUNTIME") ?? "net10.0";
var runtime = runtimeName switch
{
    "net8.0" => CoreRuntime.Core80,
    "net9.0" => CoreRuntime.Core90,
    "net10.0" => CoreRuntime.Core10_0,
    _ => throw new InvalidOperationException(runtimeName),
};
var selectedCases = (Environment.GetEnvironmentVariable("PROCESS_BENCH_CASES") ?? "ManualParent,AutomaticParent,ManualLink,AutomaticLink").Split(',');
var blockCount = int.Parse(Environment.GetEnvironmentVariable("PROCESS_BENCH_BLOCKS") ?? "1");
var blocked = Environment.GetEnvironmentVariable("PROCESS_BENCH_BLOCKS") is not null;
var config = ManualConfig.Create(DefaultConfig.Instance)
    .AddDiagnoser(MemoryDiagnoser.Default)
    .AddExporter(JsonExporter.Full)
    .WithOrderer(new DefaultOrderer(SummaryOrderPolicy.Method, MethodOrderPolicy.Declared));
if (blocked)
{
    config = config.WithOrderer(new BlockOrderer(selectedCases, blockCount, 5398));
}
for (var block = 0; block < blockCount; block++)
{
foreach (var benchmarkCase in selectedCases)
{
    var automatic = benchmarkCase.StartsWith("Automatic", StringComparison.Ordinal);
    var attached = benchmarkCase != "NoAgent";
    var mode = benchmarkCase.EndsWith("Link", StringComparison.Ordinal) ? "link" : benchmarkCase == "ExtractionOff" ? "off" : "parent";
    var job = Job.Default.WithId(blocked ? $"{benchmarkCase}-B{block:D2}" : benchmarkCase)
        .WithRuntime(runtime)
        .WithAffinity((IntPtr)(1 << 3))
        .WithGcServer(false)
        .WithLaunchCount(blocked ? 1 : int.Parse(Environment.GetEnvironmentVariable("PROCESS_BENCH_LAUNCHES") ?? "3"))
        .WithMinIterationCount(15)
        .WithMaxIterationCount(40)
        .WithWarmupCount(40)
        .WithMinIterationTime(TimeInterval.FromMilliseconds(250))
        .WithIterationTime(TimeInterval.FromMilliseconds(250))
        .WithMaxRelativeError(0.01)
        .WithEnvironmentVariable("PROCESS_BENCH_CASE", benchmarkCase)
        .WithEnvironmentVariable("PROCESS_BENCH_BLOCK", block.ToString())
        .WithEnvironmentVariable("PROCESS_BENCH_SDK", Environment.GetEnvironmentVariable("PROCESS_BENCH_SDK") ?? "false")
        .WithEnvironmentVariable("OTEL_DOTNET_AUTO_HOME", home)
        .WithEnvironmentVariable("CORECLR_ENABLE_PROFILING", attached ? "1" : "0")
        .WithEnvironmentVariable("CORECLR_PROFILER", "{918728DD-259F-4A6A-AC2B-B85E1B658318}")
        .WithEnvironmentVariable("CORECLR_PROFILER_PATH", Path.Combine(home, "linux-x64/OpenTelemetry.AutoInstrumentation.Native.so"))
        .WithEnvironmentVariable("DOTNET_STARTUP_HOOKS", attached ? Path.Combine(home, "net/OpenTelemetry.AutoInstrumentation.StartupHook.dll") : "")
        .WithEnvironmentVariable("OTEL_DOTNET_AUTO_SETUP_SDK", "false")
        .WithEnvironmentVariable("OTEL_DOTNET_AUTO_TRACES_INSTRUMENTATION_ENABLED", "false")
        .WithEnvironmentVariable("OTEL_DOTNET_AUTO_TRACES_PROCESS_INSTRUMENTATION_ENABLED", automatic || benchmarkCase is "NoIncoming" or "ExtractionOff" ? "true" : "false")
        .WithEnvironmentVariable("OTEL_DOTNET_AUTO_TRACES_PROCESS_INSTRUMENTATION_CONTEXT_EXTRACTION_MODE", mode)
        .WithEnvironmentVariable("OTEL_DOTNET_AUTO_TRACES_PROCESS_INSTRUMENTATION_CONTEXT_INJECTION_ENABLED", "false")
        .WithEnvironmentVariable("OTEL_DOTNET_AUTO_METRICS_ENABLED", "false")
        .WithEnvironmentVariable("OTEL_DOTNET_AUTO_LOGS_ENABLED", "false")
        .WithEnvironmentVariable("OTEL_DOTNET_AUTO_LOG_LEVEL", "debug")
        .WithEnvironmentVariable("OTEL_DOTNET_AUTO_LOG_DIRECTORY", Path.GetFullPath("native-logs"))
        .WithEnvironmentVariable("OTEL_PROPAGATORS", "tracecontext,baggage")
        .WithEnvironmentVariable("OTEL_TRACES_EXPORTER", "none")
        .WithEnvironmentVariable("TRACEPARENT", benchmarkCase == "NoIncoming" ? "" : ActivityFactoryBenchmarks.IncomingId)
        .WithEnvironmentVariable("TRACESTATE", "vendor=value");
    if (Environment.GetEnvironmentVariable("PROCESS_BENCH_TIERING") is { } tiering)
    {
        job = job.WithEnvironmentVariable("DOTNET_TieredCompilation", tiering);
    }
    if (blocked)
    {
        job = job.WithIterationCount(20).WithOutlierMode(OutlierMode.DontRemove);
    }
    config.AddJob(job);
}
}
BenchmarkSwitcher.FromAssembly(Assembly.GetExecutingAssembly()).Run(args, config);

public sealed class BlockOrderer(string[] profiles, int blocks, int seed) : IOrderer
{
    private readonly DefaultOrderer _default = new(SummaryOrderPolicy.Method, MethodOrderPolicy.Declared);
    public bool SeparateLogicalGroups => false;

    public IEnumerable<BenchmarkCase> GetExecutionOrder(ImmutableArray<BenchmarkCase> benchmarksCase, IEnumerable<BenchmarkLogicalGroupRule>? order = null)
    {
        var random = new Random(seed);
        foreach (var workload in benchmarksCase.GroupBy(item => item.Descriptor.WorkloadMethod.MetadataToken).OrderBy(group => group.Key))
        {
            var shuffled = profiles.OrderBy(_ => random.Next()).ToArray();
            for (var block = 0; block < blocks; block++)
            {
                for (var position = 0; position < shuffled.Length; position++)
                {
                    var profile = shuffled[(position + block) % shuffled.Length];
                    yield return workload.Single(item => item.Job.Id == $"{profile}-B{block:D2}");
                }
            }
        }
    }

    public IEnumerable<BenchmarkCase> GetSummaryOrder(ImmutableArray<BenchmarkCase> benchmarksCases, Summary summary) => _default.GetSummaryOrder(benchmarksCases, summary);
    public string? GetHighlightGroupKey(BenchmarkCase benchmarkCase) => _default.GetHighlightGroupKey(benchmarkCase);
    public string? GetLogicalGroupKey(ImmutableArray<BenchmarkCase> allBenchmarksCases, BenchmarkCase benchmarkCase) => _default.GetLogicalGroupKey(allBenchmarksCases, benchmarkCase);
    public IEnumerable<IGrouping<string, BenchmarkCase>> GetLogicalGroupOrder(IEnumerable<IGrouping<string, BenchmarkCase>> logicalGroups, IEnumerable<BenchmarkLogicalGroupRule>? order = null) => _default.GetLogicalGroupOrder(logicalGroups, order);
}

public class ActivityFactoryBenchmarks : IDisposable
{
    public const string IncomingId = "00-11111111111111111111111111111111-2222222222222222-01";
    private const string SuppliedId = "00-33333333333333333333333333333333-4444444444444444-01";
    private static readonly ActivityContext Incoming = RemoteContext(IncomingId, "vendor=value");
    private static readonly ActivityContext Supplied = RemoteContext(SuppliedId, "supplied=value");
    private static readonly IEnumerable<ActivityLink> IncomingLinks = Array.AsReadOnly<ActivityLink>([new(Incoming)]);
    private static readonly IEnumerable<ActivityLink> UnrelatedLinks = Array.AsReadOnly<ActivityLink>([new(Supplied)]);
    private static readonly IEnumerable<ActivityLink> CombinedLinks = Array.AsReadOnly<ActivityLink>([new(Supplied), new(Incoming)]);
    private readonly ActivitySource _recorded = new("ProcessPerf.Recorded");
    private readonly ActivitySource _propagation = new("ProcessPerf.Propagation");
    private readonly ActivitySource _drop = new("ProcessPerf.Drop");
    private readonly ActivitySource _dropReadLinks = new("ProcessPerf.DropReadLinks");
    private readonly ActivitySource _unobserved = new("ProcessPerf.Unobserved");
    private ActivityListener? _listener;
    private TracerProvider? _provider;
    private Activity? _outer;
    private ActivityContext _rootParent;
    private IEnumerable<ActivityLink>? _rootLinks;
    private IEnumerable<ActivityLink>? _emptyLinks;
    private IEnumerable<ActivityLink>? _existingLinks;
    private int _observedLinks;

    [GlobalSetup(Targets = [nameof(Root), nameof(RootEmptyLinks), nameof(RootExistingLink), nameof(RootAlreadyLinked), nameof(NoListeners), nameof(Dropped), nameof(DropReadingLinks), nameof(SuppliedContext), nameof(SuppliedParentId), nameof(SuppliedEmptyParentId), nameof(CreateOnly), nameof(CreateThenStart), nameof(PropagationOnly)])]
    public void Setup()
    {
        Initialize();
        WarmActualWorkload();
    }

    private void Initialize()
    {
        Activity.DefaultIdFormat = ActivityIdFormat.W3C;
        Activity.ForceDefaultIdFormat = true;
        var benchmarkCase = Environment.GetEnvironmentVariable("PROCESS_BENCH_CASE") ?? "ManualParent";
        var manualParent = benchmarkCase == "ManualParent";
        var manualLink = benchmarkCase == "ManualLink";
        _rootParent = manualParent ? Incoming : default;
        _rootLinks = manualLink ? IncomingLinks : null;
        _emptyLinks = manualLink ? IncomingLinks : Array.Empty<ActivityLink>();
        _existingLinks = manualLink ? CombinedLinks : UnrelatedLinks;
        var useSdk = Environment.GetEnvironmentVariable("PROCESS_BENCH_SDK") == "true";
        if (useSdk)
        {
            _provider = Sdk.CreateTracerProviderBuilder()
                .AddSource(_recorded.Name)
                .SetSampler(new ParentBasedSampler(new AlwaysOnSampler()))
                .Build();
        }
        _listener = new ActivityListener
        {
            ShouldListenTo = source => source.Name.StartsWith("ProcessPerf.", StringComparison.Ordinal) && source.Name != _unobserved.Name && (!useSdk || source != _recorded),
            Sample = (ref ActivityCreationOptions<ActivityContext> options) => Sample(options.Source, options.Links),
            SampleUsingParentId = (ref ActivityCreationOptions<string> options) => Sample(options.Source, options.Links),
        };
        ActivitySource.AddActivityListener(_listener);
        // Wait for the observable effect of asynchronous ReJIT, never include it in timing.
        var timeout = Stopwatch.StartNew();
        while (true)
        {
            using var probe = _recorded.StartActivity("probe");
            var correct = benchmarkCase switch
            {
                "AutomaticParent" => probe?.ParentSpanId == Incoming.SpanId && probe.TraceId == Incoming.TraceId && probe.HasRemoteParent,
                "AutomaticLink" => probe?.ParentSpanId == default(ActivitySpanId) && probe.Links.SingleOrDefault().Context == Incoming,
                _ => probe?.ParentSpanId == default(ActivitySpanId) && !probe.Links.Any(),
            };
            if (correct)
            {
                break;
            }
            if (timeout.Elapsed > TimeSpan.FromSeconds(10))
            {
                throw new InvalidOperationException($"Hook probe failed for {benchmarkCase}.");
            }
            Thread.Sleep(10);
        }
        Thread.Sleep(200);
        using (var equivalent = _recorded.StartActivity("equivalent", ActivityKind.Internal, _rootParent, links: _rootLinks))
        {
            if (benchmarkCase is "ManualParent" or "AutomaticParent")
            {
                Require(equivalent?.Context.TraceId == Incoming.TraceId && equivalent.ParentSpanId == Incoming.SpanId && equivalent.HasRemoteParent, "parent equivalent");
            }
            if (benchmarkCase is "ManualLink" or "AutomaticLink")
            {
                Require(equivalent?.ParentSpanId == default(ActivitySpanId) && equivalent.Links.Single().Context == Incoming, "link equivalent");
            }
        }
        Console.WriteLine("BENCH_PROBE " + JsonSerializer.Serialize(new
        {
            benchmarkCase,
            framework = RuntimeInformation.FrameworkDescription,
            diagnosticSource = typeof(ActivitySource).Assembly.GetName().Version?.ToString(),
            diagnosticSourceFile = FileVersionInfo.GetVersionInfo(typeof(ActivitySource).Assembly.Location).FileVersion,
            diagnosticSourceLocation = typeof(ActivitySource).Assembly.Location,
            serverGc = GCSettings.IsServerGC,
            latency = GCSettings.LatencyMode.ToString(),
            tiering = Environment.GetEnvironmentVariable("DOTNET_TieredCompilation") ?? "default",
            defaultIdFormat = Activity.DefaultIdFormat.ToString(),
            forceDefaultIdFormat = Activity.ForceDefaultIdFormat,
            sdk = useSdk ? typeof(Sdk).Assembly.GetName().Version?.ToString() : "none",
            affinity = Process.GetCurrentProcess().ProcessorAffinity.ToInt64(),
        }));
    }

    [GlobalSetup(Target = nameof(AmbientParent))]
    public void SetupAmbient()
    {
        Initialize();
        _outer = new Activity("outer").SetIdFormat(ActivityIdFormat.W3C).Start();
        using var child = _recorded.StartActivity("ambient-probe");
        Require(child?.ParentSpanId == _outer.SpanId && child.TraceId == _outer.TraceId, "ambient parent");
        child?.Dispose();
        WarmActualWorkload();
    }

    private void WarmActualWorkload()
    {
        var args = Environment.GetCommandLineArgs();
        var nameIndex = Array.IndexOf(args, "--benchmarkName");
        if (nameIndex < 0)
        {
            return;
        }
        var methodName = args[nameIndex + 1].Split('.')[^1];
        Action run = methodName == nameof(CreateOnly)
            ? () => CreateOnly()
            : GetType().GetMethod(methodName)!.CreateDelegate<Action>(this);
        var elapsed = Stopwatch.StartNew();
        while (elapsed.Elapsed < TimeSpan.FromSeconds(10))
        {
            for (var index = 0; index < 4096; index++)
            {
                run();
            }
        }
        Thread.Sleep(100);
        Console.WriteLine($"BENCH_WARMED {methodName} {elapsed.Elapsed.TotalSeconds:F3}s");
    }

    [GlobalCleanup]
    public void Dispose()
    {
        _outer?.Dispose();
        _listener?.Dispose();
        _provider?.Dispose();
        _recorded.Dispose();
        _propagation.Dispose();
        _drop.Dispose();
        _dropReadLinks.Dispose();
        _unobserved.Dispose();
    }

    [Benchmark]
    public void Root() => _recorded.StartActivity("job", ActivityKind.Internal, _rootParent, links: _rootLinks)?.Dispose();

    [Benchmark]
    public void RootEmptyLinks() => _recorded.StartActivity("job", ActivityKind.Internal, _rootParent, links: _emptyLinks)?.Dispose();

    [Benchmark]
    public void RootExistingLink() => _recorded.StartActivity("job", ActivityKind.Internal, _rootParent, links: _existingLinks)?.Dispose();

    [Benchmark]
    public void RootAlreadyLinked() => _recorded.StartActivity("job", ActivityKind.Internal, _rootParent, links: IncomingLinks)?.Dispose();

    [Benchmark]
    public void NoListeners() => _unobserved.StartActivity("job")?.Dispose();

    [Benchmark]
    public void Dropped() => _drop.StartActivity("job", ActivityKind.Internal, _rootParent, links: _rootLinks)?.Dispose();

    [Benchmark]
    public void DropReadingLinks() => _dropReadLinks.StartActivity("job", ActivityKind.Internal, _rootParent, links: _existingLinks)?.Dispose();

    [Benchmark]
    public void AmbientParent() => _recorded.StartActivity("job")?.Dispose();

    [Benchmark]
    public void SuppliedContext() => _recorded.StartActivity("job", ActivityKind.Internal, Supplied)?.Dispose();

    [Benchmark]
    public void SuppliedParentId() => _recorded.StartActivity("job", ActivityKind.Internal, SuppliedId)?.Dispose();

    [Benchmark]
    public void SuppliedEmptyParentId() => _recorded.StartActivity("job", ActivityKind.Internal, "")?.Dispose();

    [Benchmark]
    public Activity? CreateOnly() => _recorded.CreateActivity("job", ActivityKind.Internal, _rootParent, links: _rootLinks);

    [Benchmark]
    public void CreateThenStart()
    {
        using var activity = _recorded.CreateActivity("job", ActivityKind.Internal, _rootParent, links: _rootLinks);
        activity?.Start();
    }

    [Benchmark]
    public void PropagationOnly() => _propagation.StartActivity("job", ActivityKind.Internal, _rootParent, links: _rootLinks)?.Dispose();

    public void ProbeAll()
    {
        var benchmarkCase = Environment.GetEnvironmentVariable("PROCESS_BENCH_CASE") ?? "ManualParent";
        var expectParent = benchmarkCase is "ManualParent" or "AutomaticParent";
        var expectLink = benchmarkCase is "ManualLink" or "AutomaticLink";
        var samples = 0;
        var starts = 0;
        var stops = 0;
        var lastParent = default(ActivityContext);
        ActivityLink[] lastLinks = [];
        using var validationListener = new ActivityListener
        {
            ShouldListenTo = source => source.Name.StartsWith("ProcessPerf.", StringComparison.Ordinal) && source != _unobserved,
            Sample = (ref ActivityCreationOptions<ActivityContext> options) =>
            {
                samples++;
                lastParent = options.Parent;
                lastLinks = options.Links?.ToArray() ?? [];
                return ActivitySamplingResult.None;
            },
            SampleUsingParentId = static (ref ActivityCreationOptions<string> options) => ActivitySamplingResult.None,
            ActivityStarted = _ => starts++,
            ActivityStopped = _ => stops++,
        };
        ActivitySource.AddActivityListener(validationListener);

        void RequireInputs(int suppliedLinks = 0, bool alreadyLinked = false)
        {
            Require(expectParent ? lastParent == Incoming : lastParent == default, "sampler parent, remote status, flags and tracestate");
            var wanted = suppliedLinks + (expectLink && !alreadyLinked ? 1 : 0);
            Require(lastLinks.Length == wanted, "sampler link count");
            if (suppliedLinks > 0 && !alreadyLinked)
            {
                Require(lastLinks[0].Context == Supplied, "existing link order");
            }
            if (expectLink || alreadyLinked)
            {
                Require(lastLinks[^1].Context == Incoming, "incoming sampler link, remote status, flags and tracestate");
            }
        }

        Root();
        RequireInputs();
        RootEmptyLinks();
        RequireInputs();
        RootExistingLink();
        RequireInputs(suppliedLinks: 1);
        RootAlreadyLinked();
        RequireInputs(suppliedLinks: 1, alreadyLinked: true);
        var beforeSamples = samples;
        Require(_unobserved.StartActivity("no-listener") is null && samples == beforeSamples, "never-subscribed source");
        var beforeStarts = starts;
        var beforeStops = stops;
        Require(_drop.StartActivity("drop", ActivityKind.Internal, _rootParent, links: _rootLinks) is null, "sampler None returns null");
        Require(samples == beforeSamples + 1 && starts == beforeStarts && stops == beforeStops, "dropped callbacks");
        RequireInputs();
        DropReadingLinks();
        Require(_observedLinks == (expectLink ? 2 : 1), "dropping sampler reads expected links");
        RequireInputs(suppliedLinks: 1);
        Require(Activity.Current is null, "root lifetime");
        using (var explicitContext = _recorded.StartActivity("supplied", ActivityKind.Internal, Supplied))
        {
            Require(explicitContext?.TraceId == Supplied.TraceId && explicitContext.ParentSpanId == Supplied.SpanId, "explicit context");
        }
        using (var explicitId = _recorded.StartActivity("supplied", ActivityKind.Internal, SuppliedId))
        {
            Require(explicitId?.TraceId == Supplied.TraceId && explicitId.ParentSpanId == Supplied.SpanId, "explicit parent ID");
        }
        using (var explicitRoot = _recorded.StartActivity("supplied", ActivityKind.Internal, ""))
        {
            Require(explicitRoot?.ParentSpanId == default(ActivitySpanId) && !explicitRoot.Links.Any(), "explicit root ID");
        }
        beforeSamples = samples;
        using (var created = CreateOnly())
        {
            RequireInputs();
            Require(Activity.Current is null && samples == beforeSamples + 1, "creation sampling before start");
            created?.Start();
            Require(samples == beforeSamples + 1 && Activity.Current == created, "start does not resample");
        }
        Require(Activity.Current is null, "unstarted factory lifetime");
        CreateThenStart();
        PropagationOnly();
        using var outer = new Activity("outer").Start();
        using var nested = _recorded.StartActivity("nested");
        Require(nested?.ParentSpanId == outer.SpanId && nested.TraceId == outer.TraceId, "nested parent");
        Console.WriteLine("BENCH_ALL_PROBES_PASSED");
    }

    private ActivitySamplingResult Sample(ActivitySource source, IEnumerable<ActivityLink>? links)
    {
        if (source == _drop)
        {
            return ActivitySamplingResult.None;
        }
        if (source == _dropReadLinks)
        {
            var count = 0;
            if (links is not null)
            {
                foreach (var link in links)
                {
                    count++;
                }
            }
            _observedLinks = count;
            return ActivitySamplingResult.None;
        }
        return source == _propagation ? ActivitySamplingResult.PropagationData : ActivitySamplingResult.AllDataAndRecorded;
    }

    private static ActivityContext RemoteContext(string id, string traceState)
    {
        if (!ActivityContext.TryParse(id, traceState, isRemote: true, out var context))
        {
            throw new InvalidOperationException("Invalid fixture context.");
        }
        return context;
    }

    private static void Require(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException($"Benchmark correctness failed: {message}.");
        }
    }
}
