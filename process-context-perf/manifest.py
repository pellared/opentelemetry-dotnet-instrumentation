import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from preflight import ROOT, WORK

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

files = [
    ROOT / 'bin/tracer-home/net/OpenTelemetry.AutoInstrumentation.dll',
    ROOT / 'bin/tracer-home/linux-x64/OpenTelemetry.AutoInstrumentation.Native.so',
    WORK / 'Program.cs', WORK / 'ProcessContextPerf.csproj',
    WORK / 'run.py', WORK / 'preflight.py', WORK / 'suite.py',
]
manifest = {
    'capturedUtc':datetime.now(timezone.utc).isoformat(),
    'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'sourceStatus':subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),
    'osRelease':Path('/etc/os-release').read_text(),
    'kernel':platform.release(),
    'lscpu':json.loads(subprocess.check_output(['lscpu','--json'],text=True)),
    'dotnetInfo':subprocess.check_output(['dotnet','--info'],text=True),
    'binaryAndHarnessSha256':{str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.relative_to(WORK)):sha256(path) for path in files},
    'nativeBuildConfiguration':'Release',
    'managedBuildConfiguration':'Release',
    'benchmarkDotNetVersion':'0.15.8',
    'affinityCpu':3,
    'smtSiblingCpu':11,
    'primaryTiering':'runtime default',
    'primaryGc':'Concurrent Workstation',
    'workloadWarmupSeconds':10,
    'bdnWarmupIterations':40,
    'bdnMeasurementIterations':20,
    'bdnIterationTargetMilliseconds':250,
    'blocks':4,
    'outlierPolicy':'DontRemove',
    'blockOrderSeed':5398,
    'primaryControl':'same profiler loaded, PROCESS disabled, cached equivalent manual parent or links',
}
(WORK / 'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'commit':manifest['sourceCommit'],'clean':manifest['sourceStatus']==''},indent=2))
