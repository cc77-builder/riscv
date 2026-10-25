"""Four independent, isolated offline checks after the real campaign finishes."""
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('/home/lizufan/riscv-lab/r2s3-split-20261025-0716')
MODULE = ROOT / 'source-v2/team/optimizations/o2/r2-config-reuse/caller/split'
BUILD, RUN = ROOT / 'build-04', ROOT / 'run-02'
PRESERVE = Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/monitor-r2s3-split-20261025-0716/preserve_failed_v1.py')


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def command(label, cpu, argv):
    argv = ['taskset', '-c', str(cpu), *map(str, argv)]
    record = {'argv': argv, 'cpu': cpu, 'started': now()}
    with (ROOT / (label + '-driver.stdout.log')).open('xb') as so, (ROOT / (label + '-driver.stderr.log')).open('xb') as se:
        proc = subprocess.run(argv, stdout=so, stderr=se)
    record.update(exit_code=proc.returncode, finished=now())
    record['logs'] = {stream: hashlib.sha256((ROOT / (label + '-driver.' + stream + '.log')).read_bytes()).hexdigest()
                      for stream in ('stdout', 'stderr')}
    (ROOT / (label + '-driver.json')).write_text(json.dumps(record, indent=2) + '\n')
    print(label, proc.returncode, flush=True)
    if proc.returncode:
        raise RuntimeError(label + ': ' + (ROOT / (label + '-driver.stderr.log')).read_text()[-6000:])
    return record


def sequence(items, cpu):
    return [command(label, cpu, argv) for label, argv in items]


def main():
    cpus = sorted(os.sched_getaffinity(0))[:4]
    assert len(cpus) == 4
    os.sched_setaffinity(0, cpus)
    state = json.loads((RUN / 'state.json').read_text())
    assert state['status'] == 'SPLIT_CAMPAIGN_PASS' and state['new_emu_runs'] == 3
    assert state['active_pid'] is None and state['active_result'] is None and state['finished']
    records = json.loads((RUN / 'completed-runs.json').read_text())
    assert len(records) == 3 and all(r['finished'] for r in records)
    assert all(not Path('/proc/' + str(r['pid'])).exists() for r in records), 'old PID still present; inspect before continuing'
    jobs = [
        [('mutations-v2-01', ['python3', '-B', MODULE / 'mutations.py', '--build', BUILD, '--run', RUN,
                              '--output', ROOT / 'mutations-v2-01.json'])],
        [('library-v2-01', ['python3', '-B', MODULE / 'library.py', '--qualified-build', BUILD,
                            '--output', ROOT / 'library-v2-01'])],
        [('failed-v1-archive-01', ['python3', '-B', PRESERVE, '--root', ROOT,
                                   '--output', ROOT / 'failed-v1-archive-01'])],
        [('archive-v2-01', ['python3', '-B', MODULE / 'archive.py', '--action', 'pack', '--build', BUILD,
                            '--run', RUN, '--output', ROOT / 'archive-v2-01']),
         ('archive-audit-v2-01', ['python3', '-B', MODULE / 'archive.py', '--action', 'audit-archive',
                                  '--archive', ROOT / 'archive-v2-01', '--output', ROOT / 'archive-audit-v2-01.json'])],
    ]
    report = {'started': now(), 'cpu_affinity': cpus, 'new_emu_runs': 0, 'records': [], 'failures': []}
    destination = ROOT / 'postverify-v2-01.json'
    assert not destination.exists()
    destination.write_text(json.dumps(report, indent=2) + '\n')
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(sequence, job, cpu) for job, cpu in zip(jobs, cpus)]
        for future in concurrent.futures.as_completed(futures):
            try:
                report['records'].extend(future.result())
            except Exception as exc:
                report['failures'].append(repr(exc))
            destination.write_text(json.dumps(report, indent=2) + '\n')
    report.update(finished=now(), status='POSTVERIFY_PASS' if not report['failures'] else 'POSTVERIFY_FAILED')
    destination.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    assert not report['failures'], report['failures']


if __name__ == '__main__':
    main()
