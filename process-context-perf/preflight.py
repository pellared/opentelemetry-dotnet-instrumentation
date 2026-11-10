import json
import os
from pathlib import Path
import subprocess

ROOT = Path(os.environ.get('PROCESS_BENCH_REPO', '/home/splunker/opentelemetry-dotnet-instrumentation')).resolve()
WORK = Path(__file__).parent
CASES = ['ManualParent', 'AutomaticParent', 'ManualLink', 'AutomaticLink', 'NoIncoming', 'ExtractionOff', 'NoAgent']

def clean_env():
    allowed = {'PATH', 'HOME', 'USER', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TMPDIR', 'NUGET_PACKAGES', 'DOTNET_ROOT'}
    return {k:v for k,v in os.environ.items() if k in allowed}

def case_env(case, runtime):
    env = clean_env()
    env.update({
        'PROCESS_BENCH_CASE': case,
        'OTEL_DOTNET_AUTO_HOME': str(ROOT / 'bin/tracer-home'),
        'OTEL_DOTNET_AUTO_SETUP_SDK':'false',
        'OTEL_DOTNET_AUTO_TRACES_INSTRUMENTATION_ENABLED':'false',
        'OTEL_DOTNET_AUTO_TRACES_PROCESS_INSTRUMENTATION_ENABLED': 'true' if case.startswith('Automatic') or case in ['NoIncoming', 'ExtractionOff'] else 'false',
        'OTEL_DOTNET_AUTO_TRACES_PROCESS_INSTRUMENTATION_CONTEXT_EXTRACTION_MODE': 'link' if case.endswith('Link') else 'off' if case == 'ExtractionOff' else 'parent',
        'OTEL_DOTNET_AUTO_TRACES_PROCESS_INSTRUMENTATION_CONTEXT_INJECTION_ENABLED': 'false',
        'OTEL_DOTNET_AUTO_METRICS_ENABLED':'false',
        'OTEL_DOTNET_AUTO_LOGS_ENABLED':'false',
        'OTEL_DOTNET_AUTO_LOG_LEVEL':'debug',
        'OTEL_DOTNET_AUTO_LOG_DIRECTORY': str(WORK / 'preflight-logs' / f'{runtime}-{case}'),
        'OTEL_PROPAGATORS':'tracecontext,baggage',
        'OTEL_TRACES_EXPORTER':'none',
        'TRACEPARENT': '' if case == 'NoIncoming' else '00-11111111111111111111111111111111-2222222222222222-01',
        'TRACESTATE':'vendor=value',
    })
    return env

if __name__ == '__main__':
    records = []
    for runtime in ['net8.0','net9.0','net10.0']:
        for case in CASES:
            env = case_env(case, runtime)
            dll = str(WORK / 'bin/Release' / runtime / 'ProcessContextPerf.dll')
            cmd = ['taskset', '-c', '3']
            if case != 'NoAgent':
                cmd += ['bash', str(ROOT / 'instrument.sh')]
            cmd += ['dotnet', dll, '--probe']
            run = subprocess.run(cmd, cwd=WORK, env=env, text=True, capture_output=True, timeout=60)
            if run.returncode != 0:
                raise RuntimeError((runtime,case,run.stdout,run.stderr))
            assert 'BENCH_ALL_PROBES_PASSED' in run.stdout, run.stdout
            record = json.loads(next(line.removeprefix('BENCH_PROBE ') for line in run.stdout.splitlines() if line.startswith('BENCH_PROBE ')))
            record['targetRuntime'] = runtime
            records.append(record)
            print(json.dumps(record), flush=True)
    (WORK / 'preflight.json').write_text(json.dumps(records, indent=2))
