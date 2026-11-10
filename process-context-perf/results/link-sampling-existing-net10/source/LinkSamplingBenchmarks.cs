// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

using System.Diagnostics;
using System.Reflection;
using System.Runtime;
using System.Runtime.InteropServices;
using System.Text.Json;
using BenchmarkDotNet.Attributes;

// Reuses the frozen launch configuration and BlockOrderer in LinkProgram.cs.
// Select ManualLink/AutomaticLink and filter to *LinkSamplingBenchmarks*.
public class LinkSamplingBenchmarks : IDisposable
{
    private const string SuppliedId = "00-33333333333333333333333333333333-4444444444444444-01";
    private static readonly ActivityContext Incoming = RemoteContext(ActivityFactoryBenchmarks.IncomingId, "vendor=value");
    private static readonly ActivityContext Supplied = RemoteContext(SuppliedId, "supplied=value");
    private static readonly IEnumerable<ActivityLink> IncomingLinks = Array.AsReadOnly<ActivityLink>([new(Incoming)]);
    private static readonly IEnumerable<ActivityLink> UnrelatedLinks = Array.AsReadOnly<ActivityLink>([new(Supplied)]);
    private static readonly IEnumerable<ActivityLink> CombinedLinks = Array.AsReadOnly<ActivityLink>([new(Supplied), new(Incoming)]);

    private readonly ActivitySource _source = new("ProcessPerf.LinkSampling");
    private ActivityListener? _listener;
    private IEnumerable<ActivityLink>? _rootLinks;
    private IEnumerable<ActivityLink>? _existingLinks;

    [GlobalSetup]
    public void Setup()
    {
        Activity.DefaultIdFormat = ActivityIdFormat.W3C;
        Activity.ForceDefaultIdFormat = true;
        var benchmarkCase = Environment.GetEnvironmentVariable("PROCESS_BENCH_CASE") ?? "ManualLink";
        if (benchmarkCase is not ("ManualLink" or "AutomaticLink"))
        {
            throw new InvalidOperationException("LinkSamplingBenchmarks requires PROCESS_BENCH_CASES=ManualLink,AutomaticLink.");
        }

        var automatic = benchmarkCase == "AutomaticLink";
        _rootLinks = automatic ? null : IncomingLinks;
        _existingLinks = automatic ? UnrelatedLinks : CombinedLinks;
        _listener = new ActivityListener
        {
            ShouldListenTo = source => ReferenceEquals(source, _source),
            Sample = static (ref ActivityCreationOptions<ActivityContext> options) =>
            {
                if (options.Links is { } links)
                {
                    foreach (var link in links)
                    {
                        if (link.Context.TraceId == Incoming.TraceId && link.Context.SpanId == Incoming.SpanId)
                        {
                            return ActivitySamplingResult.AllDataAndRecorded;
                        }
                    }
                }

                return ActivitySamplingResult.AllData;
            },
        };
        ActivitySource.AddActivityListener(_listener);

        // The sampler records the plain probe only after automatic injection is
        // observable. Manual mode must leave this unsupplied probe unrecorded.
        var readiness = Stopwatch.StartNew();
        while (true)
        {
            using var probe = _source.StartActivity("probe");
            var links = probe?.Links.ToArray() ?? [];
            var correct = probe is not null && probe.ParentSpanId == default && probe.TraceId != Incoming.TraceId &&
                          (automatic
                              ? probe.Recorded && links.Length == 1 && links[0].Context == Incoming
                              : !probe.Recorded && links.Length == 0);
            if (correct)
            {
                break;
            }

            if (readiness.Elapsed > TimeSpan.FromSeconds(10))
            {
                throw new InvalidOperationException($"Link-sampling hook probe failed for {benchmarkCase}.");
            }

            Thread.Sleep(10);
        }

        using (var root = _source.StartActivity("validate-root", ActivityKind.Internal, default(ActivityContext), links: _rootLinks))
        {
            Validate(root, hasExistingLink: false);
        }

        using (var existing = _source.StartActivity("validate-existing", ActivityKind.Internal, default(ActivityContext), links: _existingLinks))
        {
            Validate(existing, hasExistingLink: true);
        }

        Require(Activity.Current is null, "validation leaves no current activity");
        Console.WriteLine("BENCH_PROBE " + JsonSerializer.Serialize(new
        {
            benchmarkCase,
            benchmarkType = nameof(LinkSamplingBenchmarks),
            framework = RuntimeInformation.FrameworkDescription,
            diagnosticSource = typeof(ActivitySource).Assembly.GetName().Version?.ToString(),
            diagnosticSourceFile = FileVersionInfo.GetVersionInfo(typeof(ActivitySource).Assembly.Location).FileVersion,
            diagnosticSourceLocation = typeof(ActivitySource).Assembly.Location,
            serverGc = GCSettings.IsServerGC,
            latency = GCSettings.LatencyMode.ToString(),
            tiering = Environment.GetEnvironmentVariable("DOTNET_TieredCompilation") ?? "default",
            defaultIdFormat = Activity.DefaultIdFormat.ToString(),
            forceDefaultIdFormat = Activity.ForceDefaultIdFormat,
            sdk = "none",
            affinity = Process.GetCurrentProcess().ProcessorAffinity.ToInt64(),
            sampler = "records only when incoming trace and span IDs appear in links",
        }));
        WarmActualWorkload();
    }

    [Benchmark]
    public void Root() => _source.StartActivity("job", ActivityKind.Internal, default(ActivityContext), links: _rootLinks)?.Dispose();

    [Benchmark]
    public void RootExistingLink() => _source.StartActivity("job", ActivityKind.Internal, default(ActivityContext), links: _existingLinks)?.Dispose();

    [GlobalCleanup]
    public void Dispose()
    {
        _listener?.Dispose();
        _source.Dispose();
    }

    private void WarmActualWorkload()
    {
        var args = Environment.GetCommandLineArgs();
        var nameIndex = Array.IndexOf(args, "--benchmarkName");
        if (nameIndex < 0)
        {
            return;
        }

        if (nameIndex + 1 >= args.Length)
        {
            throw new InvalidOperationException("Missing --benchmarkName value.");
        }

        var methodName = args[nameIndex + 1].Split('.')[^1];
        if (methodName is not (nameof(Root) or nameof(RootExistingLink)))
        {
            throw new InvalidOperationException($"Unexpected link-sampling workload: {methodName}.");
        }

        var method = GetType().GetMethod(methodName, BindingFlags.Public | BindingFlags.Instance)
                     ?? throw new InvalidOperationException($"Missing workload: {methodName}.");
        var run = method.CreateDelegate<Action>(this);
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

    private static void Validate(Activity? activity, bool hasExistingLink)
    {
        Require(activity is { Recorded: true, IsAllDataRequested: true }, "both controls are recorded");
        Require(activity!.ParentSpanId == default && activity.TraceId != Incoming.TraceId, "linked work remains a new trace");
        var links = activity.Links.ToArray();
        Require(links.Length == (hasExistingLink ? 2 : 1), "link count after activity copies sampling inputs");
        if (hasExistingLink)
        {
            Require(links[0].Context == Supplied, "existing link order and contents");
        }

        Require(links[^1].Context == Incoming, "incoming link flags, remote status and trace state");
    }

    private static ActivityContext RemoteContext(string id, string traceState)
    {
        if (!ActivityContext.TryParse(id, traceState, isRemote: true, out var context))
        {
            throw new InvalidOperationException("Invalid link-sampling fixture context.");
        }

        return context;
    }

    private static void Require(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException($"Link-sampling benchmark correctness failed: {message}.");
        }
    }
}
