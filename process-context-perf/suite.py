import argparse
import json
import subprocess
import sys
from pathlib import Path
from preflight import WORK
import time

parser = argparse.ArgumentParser()
parser.add_argument('--resume', action='store_true')
args = parser.parse_args()

phases = [
    ('activity-net10', 'net10.0', ['Root','RootEmptyLinks','RootExistingLink','RootAlreadyLinked','Dropped','DropReadingLinks','AmbientParent','SuppliedContext','SuppliedParentId','SuppliedEmptyParentId','CreateOnly','CreateThenStart','PropagationOnly'], []),
    ('activity-net8', 'net8.0', ['Root','NoListeners','Dropped','AmbientParent','SuppliedContext','CreateOnly'], []),
    ('activity-net9', 'net9.0', ['Root','NoListeners','Dropped','AmbientParent','SuppliedContext','CreateOnly'], []),
    ('controls-net10', 'net10.0', ['Root','NoListeners'], ['--cases','Disabled,NoIncoming,ExtractionOff,NoAgent']),
    ('tiering-off-net10', 'net10.0', ['Root','NoListeners','AmbientParent'], ['--tiering','0']),
    ('sdk-net10', 'net10.0', ['Root','NoListeners','CreateOnly'], ['--sdk']),
]
phases = [
    (f'{name}-{method.lower()}', runtime, [method], extra)
    for name, runtime, methods, extra in phases
    for method in methods
]
# The original initial cohort was recorded before this coordinator was introduced.
# Include it for fresh reproductions; --resume retains the recorded cohort.
phases.insert(0, ('no-listener-net10', 'net10.0', ['NoListeners'], []))
phases += [
    ('no-listener-repeat-net10', 'net10.0', ['NoListeners'], []),
    ('link-sampling-root-net10', 'net10.0', ['Root'], ['--cases','ManualLink,AutomaticLink','--type','LinkSamplingBenchmarks','--app',str(WORK.parent / 'process-context-link-sampling-perf/bin/Release/net10.0/LinkSamplingPerf.dll')]),
    ('link-sampling-existing-net10', 'net10.0', ['RootExistingLink'], ['--cases','ManualLink,AutomaticLink','--type','LinkSamplingBenchmarks','--app',str(WORK.parent / 'process-context-link-sampling-perf/bin/Release/net10.0/LinkSamplingPerf.dll')]),
]
# Additional independent cohorts for the principal cost/early-exit paths.
# Already-running coordinators do not reload this list; run --resume afterwards.
phases += [
    (f'activity-repeat-net10-{method.lower()}', 'net10.0', [method], [])
    for method in ['Root', 'AmbientParent', 'Dropped', 'SuppliedContext']
]
status = []
for name, runtime, methods, extra in phases:
    command = [sys.executable, str(WORK / 'run.py'), name, runtime, '--blocks','4','--methods',*methods,*extra]
    print(json.dumps({'starting':name,'command':command}), flush=True)
    manifest = WORK / 'results' / name / 'run.json'
    if args.resume and manifest.exists():
        while True:
            current = json.loads(manifest.read_text())
            if 'exitCode' in current:
                break
            time.sleep(1)
        if current['arguments']['methods'] != methods or current['arguments']['runtime'] != runtime:
            raise RuntimeError(f'Existing run arguments differ: {name}')
        code = current['exitCode']
        print(json.dumps({'resumed':name,'exitCode':code}),flush=True)
    else:
        with (WORK / f'{name}-progress.log').open('w') as log:
            code = subprocess.run(command,cwd=WORK,stdout=log,stderr=subprocess.STDOUT).returncode
    status.append({'name':name,'exitCode':code})
    (WORK / 'suite-status.json').write_text(json.dumps(status,indent=2))
    print(json.dumps(status[-1]),flush=True)
    if code:
        raise SystemExit(code)
