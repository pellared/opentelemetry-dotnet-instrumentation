using Datadog.Trace.Conventions;
using Datadog.Trace.Propagation;
using Xunit;

namespace Datadog.Trace.OpenTracing.Tests
{
    public class HttpHeaderCodecTests
    {
        // The values are duplicated here to make sure that if they are changed it will break tests
        private const string HttpHeaderTraceId = "x-datadog-trace-id";
        private const string HttpHeaderParentId = "x-datadog-parent-id";
        private const string HttpHeaderSamplingPriority = "x-datadog-sampling-priority";

        private readonly HttpHeadersCodec _codec = new HttpHeadersCodec(new DDSpanContextPropagator(new DatadogTraceIdConvention()));

        [Fact]
        public void Extract_ValidParentAndTraceId_ProperSpanContext()
        {
            var traceId = TraceId.CreateFromInt(10);
            const ulong parentId = 120;

            var headers = new MockTextMap();
            headers.Set(HttpHeaderTraceId, traceId.ToString());
            headers.Set(HttpHeaderParentId, parentId.ToString());

            var spanContext = _codec.Extract(headers) as OpenTracingSpanContext;

            Assert.NotNull(spanContext);
            Assert.Equal(traceId, spanContext.Context.TraceId);
            Assert.Equal(parentId, spanContext.Context.SpanId);
        }

        [Fact]
        public void Extract_WrongHeaderCase_ExtractionStillWorks()
        {
            var traceId = TraceId.CreateFromInt(10);
            const ulong parentId = 120;
            const SamplingPriority samplingPriority = SamplingPriority.UserKeep;

            var headers = new MockTextMap();
            headers.Set(HttpHeaderTraceId.ToUpper(), traceId.ToString());
            headers.Set(HttpHeaderParentId.ToUpper(), parentId.ToString());
            headers.Set(HttpHeaderSamplingPriority.ToUpper(), ((int)samplingPriority).ToString());

            var spanContext = _codec.Extract(headers) as OpenTracingSpanContext;

            Assert.NotNull(spanContext);
            Assert.Equal(traceId, spanContext.Context.TraceId);
            Assert.Equal(parentId, spanContext.Context.SpanId);
        }

        [Fact]
        public void Inject_SpanContext_HeadersWithCorrectInfo()
        {
            const ulong spanId = 10;
            var traceId = TraceId.CreateFromInt(7);
            const SamplingPriority samplingPriority = SamplingPriority.UserKeep;

            var ddSpanContext = new SpanContext(traceId, spanId, samplingPriority);
            var spanContext = new OpenTracingSpanContext(ddSpanContext);
            var headers = new MockTextMap();

            _codec.Inject(spanContext, headers);

            Assert.Equal(spanId.ToString(), headers.Get(HttpHeaderParentId));
            Assert.Equal(traceId.ToString(), headers.Get(HttpHeaderTraceId));
            Assert.Equal(((int)samplingPriority).ToString(), headers.Get(HttpHeaderSamplingPriority));
        }
    }
}
