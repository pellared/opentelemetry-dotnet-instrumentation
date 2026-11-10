from pathlib import Path
import json
import report
work=Path(__file__).parent
plan=report.checkpoint_plan()
completed=0
active=[]
failed=[]
for p in plan:
    folder=work/'results'/p.name
    path=folder/'run.json'
    if not path.exists():
        continue
    d=json.loads(path.read_text())
    if d.get('exitCode')==0 and (folder/'analysis/comparisons.json').exists():
        completed+=1
    elif 'end' not in d:
        lines=(folder/'console.log').read_text().splitlines() if (folder/'console.log').exists() else []
        count=sum('has exited with code 0' in s for s in lines)
        active.append(f'{p.name} ({count}/{4*len(p.profiles)} workers complete)')
    else:
        failed.append(p.name)
print(f'Benchmark progress: {completed}/{len(plan)} checkpoints complete; '+('; '.join(active) if active else 'no active checkpoint')+('. Failed: '+', '.join(failed) if failed else '.'))
