import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import time

parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
parser.add_argument('--interval', type=float, default=10)
parser.add_argument('--max-seconds', type=float, default=7200)
args = parser.parse_args()
running = True

def stop(signum, frame):
    global running
    running = False

signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
relative = Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
cgroup = Path('/sys/fs/cgroup') / relative

def key_values(path):
    if not path.exists():
        return None
    return dict((pieces[0], int(pieces[1])) for line in path.read_text().splitlines() if len(pieces := line.split()) == 2)

def pressure(path):
    if not path.exists():
        return None
    result = {}
    for line in path.read_text().splitlines():
        parts = line.split()
        result[parts[0]] = {key: int(value) if key == 'total' else float(value) for key, value in (part.split('=', 1) for part in parts[1:])}
    return result

def capture():
    cpus = {}
    for line in Path('/proc/stat').read_text().splitlines():
        parts = line.split()
        if parts and parts[0] in ['cpu3', 'cpu11']:
            cpus[parts[0]] = dict(zip(['user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'steal', 'guest', 'guest_nice'], map(int, parts[1:])))
    return {
        'utc': datetime.now(timezone.utc).isoformat(),
        'monotonic': time.monotonic(),
        'cpus_ticks': cpus,
        'host_cpu_pressure': pressure(Path('/proc/pressure/cpu')),
        'session_cpu_pressure': pressure(cgroup / 'cpu.pressure'),
        'session_cpu_stat': key_values(cgroup / 'cpu.stat'),
        'loadavg': Path('/proc/loadavg').read_text().strip(),
    }

output = Path(args.output)
output.parent.mkdir(parents=True, exist_ok=True)
started = time.monotonic()
previous = None
with output.open('a', buffering=1) as stream:
    stream.write(json.dumps({'kind': 'metadata', 'pid': os.getpid(), 'monitor_affinity': sorted(os.sched_getaffinity(0)), 'cgroup': str(cgroup), 'interval_seconds': args.interval, 'clock_ticks_per_second': os.sysconf('SC_CLK_TCK'), 'started_utc': datetime.now(timezone.utc).isoformat()}) + '\n')
    print(json.dumps({'started': True, 'pid': os.getpid(), 'monitor_affinity': sorted(os.sched_getaffinity(0)), 'output': str(output)}), flush=True)
    while running and time.monotonic() - started <= args.max_seconds:
        current = capture()
        current['kind'] = 'sample'
        current['deltas'] = {}
        if previous is not None:
            elapsed = current['monotonic'] - previous['monotonic']
            current['interval_seconds'] = elapsed
            for cpu, ticks in current['cpus_ticks'].items():
                diff = {key: value - previous['cpus_ticks'][cpu][key] for key, value in ticks.items()}
                total = sum(diff[key] for key in ['user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'steal'])
                active = total - diff['idle'] - diff['iowait'] - diff['steal']
                current['deltas'][cpu] = {'total_ticks': total, 'execution_busy_percent': 100 * active / total if total else None, 'steal_percent': 100 * diff['steal'] / total if total else None, 'idle_percent': 100 * diff['idle'] / total if total else None, 'iowait_percent': 100 * diff['iowait'] / total if total else None}
            for field in ['host_cpu_pressure', 'session_cpu_pressure']:
                current['deltas'][field] = {mode: {'stall_usec': values['total'] - previous[field][mode]['total'], 'stall_percent': 100 * (values['total'] - previous[field][mode]['total']) / (elapsed * 1_000_000)} for mode, values in current[field].items()}
            current['deltas']['session_cpu_stat'] = {key: value - previous['session_cpu_stat'].get(key, 0) for key, value in current['session_cpu_stat'].items()}
        stream.write(json.dumps(current) + '\n')
        previous = current
        deadline = time.monotonic() + args.interval
        while running and time.monotonic() < deadline:
            time.sleep(min(0.25, deadline - time.monotonic()))
    stream.write(json.dumps({'kind': 'stopped', 'utc': datetime.now(timezone.utc).isoformat(), 'elapsed_seconds': time.monotonic() - started}) + '\n')
