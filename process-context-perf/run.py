import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from preflight import WORK, ROOT, clean_env

parser = argparse.ArgumentParser()
parser.add_argument('name')
parser.add_argument('runtime', choices=['net8.0','net9.0','net10.0'])
parser.add_argument('--cases', default='ManualParent,AutomaticParent,ManualLink,AutomaticLink')
parser.add_argument('--methods', nargs='+', default=['*'])
parser.add_argument('--tiering')
parser.add_argument('--sdk', action='store_true')
parser.add_argument('--launches', default='3')
parser.add_argument('--blocks')
parser.add_argument('--app', type=Path, default=WORK / 'bin/Release/net10.0/ProcessContextPerf.dll')
parser.add_argument('--type', default='ActivityFactoryBenchmarks')
args = parser.parse_args()
args.app = args.app.resolve()
output = WORK / 'results' / args.name
output.mkdir(parents=True, exist_ok=True)
env = clean_env()
env.update(PROCESS_BENCH_REPO=str(ROOT), PROCESS_BENCH_RUNTIME=args.runtime, PROCESS_BENCH_CASES=args.cases, PROCESS_BENCH_LAUNCHES=args.launches, PROCESS_BENCH_SDK=str(args.sdk).lower())
if args.tiering is not None:
    env['PROCESS_BENCH_TIERING'] = args.tiering
if args.blocks is not None:
    env['PROCESS_BENCH_BLOCKS'] = args.blocks
command = ['dotnet', str(args.app), '--filter']
command += [f'{args.type}.*' if method == '*' else f'{args.type}.{method}' for method in args.methods]
command += ['--artifacts', str(output / 'bdn')]
arguments = vars(args).copy()
arguments['app'] = str(args.app)
source_dir = output / 'source'
source_dir.mkdir(exist_ok=True)
source_files = [WORK / 'Program.cs', WORK / 'ProcessContextPerf.csproj']
if args.type != 'ActivityFactoryBenchmarks':
    source_files += [args.app.parents[3] / 'LinkSamplingBenchmarks.cs', args.app.parents[3] / 'LinkSamplingPerf.csproj']
for source in source_files:
    snapshot_name = source.name + ('.snapshot' if source.suffix == '.csproj' else '')
    shutil.copyfile(source, source_dir / snapshot_name)
source_hashes = {source.name + ('.snapshot' if source.suffix == '.csproj' else ''):hashlib.sha256(source.read_bytes()).hexdigest() for source in source_files}
metadata = {'arguments':arguments, 'command':command, 'start':time.time(), 'sourceSnapshotSha256':source_hashes, 'environment':{key:value for key,value in env.items() if key.startswith('PROCESS_BENCH_')}}
(output / 'run.json').write_text(json.dumps(metadata, indent=2))
captured = False
with (output / 'console.log').open('w') as log:
    process = subprocess.Popen(command, cwd=args.app.parents[3], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        log.write(line)
        log.flush()
        if not captured and line.startswith('// Execute: dotnet '):
            directory = Path(line.rstrip().rsplit(' in ', 1)[1])
            proof = output / 'provenance'
            proof.mkdir(exist_ok=True)
            for suffix in ('.dll', '.pdb'):
                shutil.copyfile(directory / args.app.with_suffix(suffix).name, proof / args.app.with_suffix(suffix).name)
            captured = True
        if line.startswith(('// Benchmark:', '// Remained ', '// Found ', '// Build Error:', '// ***** BenchmarkRunner: End *****', '// Benchmark Process ', 'Mean =', '// * Errors *', 'No Workload Results', 'BENCH_PROBE')):
            print(line.rstrip(), flush=True)
    code = process.wait()
if code == 0 and not list((output / 'bdn/results').glob('*-report-full.json')):
    code = 1
if code == 0 and not captured:
    code = 1
if code == 0:
    tool = WORK.parent / 'process-context-provenance/bin/Release/net10.0/Provenance.dll'
    for source in [item for item in source_files if item.suffix == '.cs']:
        proof_command = ['dotnet', str(tool), str(output / 'provenance' / args.app.name), str(output / 'provenance' / args.app.with_suffix('.pdb').name), str(source_dir / source.name)]
        with (output / 'provenance' / f'{source.stem}.json').open('w') as log:
            result = subprocess.run(proof_command,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:
            code = result.returncode
metadata.update(end=time.time(), exitCode=code)
(output / 'run.json').write_text(json.dumps(metadata, indent=2))
if code == 0:
    code = subprocess.run([sys.executable, str(WORK / 'analyze.py'), str(output)]).returncode
    if code:
        metadata['analysisExitCode'] = code
        metadata['exitCode'] = code
        (output / 'run.json').write_text(json.dumps(metadata, indent=2))
raise SystemExit(code)
