"""Linux process-group supervisor. No target command is constructed here.

Limits are checked on every /proc sample (50 ms nominal). Resource peaks are
observed samples, not an assertion of kernel-enforced instantaneous ceilings.
"""
from pathlib import Path
import ctypes
import errno
import json
import os
import re
import selectors
import signal
import subprocess
import time
from common import now, save, sha

PAGE_BYTES = os.sysconf('SC_PAGE_SIZE')


def process_info(pid):
    root = Path('/proc') / str(pid)
    raw = (root / 'stat').read_text()
    rest = raw[raw.rfind(')') + 2:].split()
    tids = []
    for task in sorted((root / 'task').iterdir(), key=lambda p: int(p.name)):
        try:
            status = (task / 'status').read_text()
            mask = re.search(r'^Cpus_allowed_list:\s*(.*)$', status, re.M).group(1)
            tids.append({'tid': int(task.name), 'cpu_affinity': mask})
        except (FileNotFoundError, ProcessLookupError):
            pass
    return {'pid': pid, 'ppid': int(rest[1]), 'pgid': int(rest[2]),
            'sid': int(rest[3]), 'state': rest[0], 'start_ticks': int(rest[19]),
            'rss_bytes': max(0, int(rest[21])) * PAGE_BYTES,
            'threads_reported': int(rest[17]), 'tids': tids}


def execution_identity(pid):
    """Read the live kernel process image; do not trust requested argv/env alone."""
    proc=Path('/proc')/str(pid)
    executable=(proc/'exe').resolve(strict=True)
    command=(proc/'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
    raw_env=(proc/'environ').read_bytes().rstrip(b'\0').decode().split('\0')
    environment=dict(item.split('=',1) for item in raw_env if item)
    return {'pid':pid,'process':process_info(pid),'executable':str(executable),
            'executable_sha256':sha(executable),'command':command,'cwd':str((proc/'cwd').resolve(strict=True)),
            'environment':environment,'observed_monotonic':time.monotonic(),
            'measurement':'live /proc exe/cmdline/cwd/environ; captured after Popen exec handoff'}

def mapped_files(pid):
    paths=set()
    try:
        for line in (Path('/proc')/str(pid)/'maps').read_text().splitlines():
            fields=line.split(None,5)
            if len(fields)==6 and fields[5].startswith('/'):
                paths.add(fields[5])
    except (FileNotFoundError,ProcessLookupError):
        pass
    return paths


def group_snapshot(pgid, known=None):
    rows = []
    for item in Path('/proc').iterdir():
        if not item.name.isdigit():
            continue
        try:
            row = process_info(int(item.name))
        except (FileNotFoundError, ProcessLookupError):
            continue
        if row['pgid'] == pgid:
            rows.append(row)
    live = [row for row in rows if row['state'] != 'Z']
    return {'processes': rows, 'live_processes': live,
            'threads': sum(max(row['threads_reported'], len(row['tids'])) for row in live),
            'rss_bytes': sum(row['rss_bytes'] for row in live)}


def reap_group(pgid):
    exits = []
    while True:
        try:
            pid, status = os.waitpid(-pgid, os.WNOHANG)
            if pid == 0:
                break
            exits.append({'pid': pid, 'exit_code': os.waitstatus_to_exitcode(status)})
        except ChildProcessError:
            break
    return exits


def guest_count(stdout_path, stderr_path):
    counts = []
    pattern = re.compile(rb'(?:guest\s+cycle(?:s)?\s+spent|guest_cycles|guestCycle)\s*[:=]\s*(\d+)', re.I)
    for path in (stdout_path, stderr_path):
        with Path(path).open('rb') as stream:
            for line in stream:
                counts.extend(int(match) for match in pattern.findall(line))
    return max(counts) if counts else None


def run_group(command, cwd, env, output, limits, outer_deadline=None, role='HOST_FIXTURE'):
    """Run one child and its entire process group, preserving first violation.

    Returns only after owned process group cleanup has been positively checked.
    A record with cleanup_ok=false must halt the caller's campaign.
    """
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    started_utc = now()
    process = None
    selector = selectors.DefaultSelector()
    old_signals = {}
    stop_reason = None
    interrupt_reason = None
    active_end = None
    trigger_at = None
    samples = 0
    peak_threads = 0
    peak_rss = 0
    observed_bytes = {'stdout': 0, 'stderr': 0}
    retained_bytes = {'stdout': 0, 'stderr': 0}
    known = {}
    adopted_exits = []
    last_snapshot = {'processes': [], 'live_processes': [], 'threads': 0, 'rss_bytes': 0}
    final_snapshot = None
    cleanup_ok = False
    cleanup_error = None
    exception_text = None
    exit_code = None
    identity = None
    maps_evidence = {}
    boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    if ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'PR_SET_CHILD_SUBREAPER')

    def caught(signum, frame):
        nonlocal interrupt_reason
        interrupt_reason = 'SIGNAL_' + signal.Signals(signum).name

    def trigger(reason, snapshot):
        nonlocal stop_reason, trigger_at
        if stop_reason is None:
            stop_reason = reason
            trigger_at = time.monotonic()
            save(out / 'limit-trigger.json', {'reason': reason, 'utc': now(),
                 'monotonic': trigger_at, 'snapshot': snapshot,
                 'observed_bytes': observed_bytes, 'limits': limits})
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    try:
        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            old_signals[signum] = signal.signal(signum, caught)
        affinity = set(limits['cpu_affinity'])
        def child_setup():
            os.sched_setaffinity(0, affinity)
        streams = {name: (out / (name + '.log')).open('wb') for name in observed_bytes}
        with (out / 'telemetry.jsonl').open('x') as telemetry:
            save(out / 'launch.json', {'role': role, 'command': command, 'cwd': str(cwd), 'env': env,
                 'limits': limits, 'utc': started_utc, 'monotonic': started, 'boot_id': boot_id})
            process = subprocess.Popen(command, cwd=cwd, env=env,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                     start_new_session=True, preexec_fn=child_setup)
            identity=execution_identity(process.pid)
            save(out/'execution-identity.json',identity)
            for name in streams:
                pipe = getattr(process, name)
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, name)
            next_sample = 0.0
            while True:
                current = time.monotonic()
                if current >= next_sample:
                    last_snapshot = group_snapshot(process.pid, known)
                    samples += 1
                    for mapped in mapped_files(process.pid):
                        maps_evidence.setdefault(mapped,{'pid':process.pid,'first_observed_monotonic':current})
                    for row in last_snapshot['processes']:
                        known[row['pid']] = row['start_ticks']
                    peak_threads = max(peak_threads, last_snapshot['threads'])
                    peak_rss = max(peak_rss, last_snapshot['rss_bytes'])
                    telemetry.write(json.dumps({'monotonic': current, **last_snapshot}) + '\n')
                    telemetry.flush()
                    next_sample = current + 0.05
                    wrong_mask = [t for row in last_snapshot['live_processes'] for t in row['tids']
                                  if t['cpu_affinity'] != ','.join(map(str, sorted(affinity)))]
                    if wrong_mask:
                        trigger('CPU_AFFINITY_LIMIT', last_snapshot)
                    if last_snapshot['threads'] > limits['thread_cap']:
                        trigger('THREAD_LIMIT', last_snapshot)
                    if last_snapshot['rss_bytes'] > limits['rss_cap_bytes']:
                        trigger('RSS_LIMIT', last_snapshot)
                if interrupt_reason:
                    trigger(interrupt_reason, last_snapshot)
                if outer_deadline is not None and current >= outer_deadline:
                    trigger('OUTER_WALL_LIMIT', last_snapshot)
                if current - started >= limits['wall_seconds']:
                    trigger('WALL_LIMIT', last_snapshot)
                for key, _ in selector.select(0.025):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if not data:
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                        continue
                    name = key.data
                    observed_bytes[name] += len(data)
                    room = max(0, limits['log_cap_bytes'] - sum(retained_bytes.values()))
                    keep = data[:room]
                    streams[name].write(keep)
                    retained_bytes[name] += len(keep)
                    if sum(observed_bytes.values()) > limits['log_cap_bytes']:
                        trigger('LOG_LIMIT', last_snapshot)
                exit_code = process.poll()
                if exit_code is not None and active_end is None:
                    active_end = time.monotonic()
                if exit_code is not None:
                    adopted_exits.extend(reap_group(process.pid))
                    if any(row['exit_code'] != 0 for row in adopted_exits):
                        trigger('CHILD_EXIT_FAILURE', last_snapshot)
                    remaining = group_snapshot(process.pid, known)
                    # A child surviving its leader is a failed run, not a permit
                    # to continue for the remainder of the role budget.
                    if remaining['live_processes']:
                        trigger('CHILD_SURVIVED_LEADER', remaining)
                    if not selector.get_map() and not remaining['live_processes']:
                        break
                if trigger_at is not None and time.monotonic() - trigger_at >= 5:
                    break
    except BaseException as exc:
        exception_text = type(exc).__name__ + ': ' + str(exc)
        trigger('SUPERVISOR_EXCEPTION', last_snapshot)
    finally:
        # Cleanup is bounded and included in campaign wall time, never a new role.
        if process is not None:
            try:
                if process.poll() is None:
                    trigger(stop_reason or 'CLEANUP_REQUIRED', last_snapshot)
                until = min(time.monotonic() + 5, outer_deadline or float('inf'))
                while time.monotonic() <= until:
                    process.poll()
                    adopted_exits.extend(reap_group(process.pid))
                    final_snapshot = group_snapshot(process.pid, known)
                    if not final_snapshot['processes']:
                        cleanup_ok = True
                        break
                    os.killpg(process.pid, signal.SIGKILL)
                    time.sleep(0.025)
                exit_code = process.poll()
                if active_end is None and exit_code is not None:
                    active_end = time.monotonic()
                if not cleanup_ok:
                    cleanup_error = 'owned process group not proven empty'
            except BaseException as exc:
                cleanup_error = type(exc).__name__ + ': ' + str(exc)
        else:
            cleanup_ok = True
        for key in list(selector.get_map().values()):
            key.fileobj.close()
        selector.close()
        for stream in locals().get('streams', {}).values():
            stream.flush(); os.fsync(stream.fileno()); stream.close()
        for signum, handler in old_signals.items():
            signal.signal(signum, handler)
    ended = time.monotonic()
    if not cleanup_ok and stop_reason is None:
        stop_reason = 'CLEANUP_UNKNOWN'
    count = guest_count(out / 'stdout.log', out / 'stderr.log') if process else None
    if count is not None and count > limits.get('guest_cycles', float('inf')):
        stop_reason = stop_reason or 'GUEST_CYCLE_LIMIT'
    record = {'schema': 'sp1-e-g1-c8-run-record-v1', 'role': role, 'started_utc': started_utc,
              'ended_utc': now(), 'boot_id': boot_id, 'started_monotonic': started,
              'ended_monotonic': ended, 'command': command, 'cwd': str(cwd),
              'process_started': process is not None,
              'pid': process.pid if process else None, 'known_pid_start_ticks': known,
              'adopted_child_exits': adopted_exits,
              'exit_code': exit_code, 'stop_reason': stop_reason, 'limit': stop_reason,
              'resource_ok': stop_reason is None, 'cleanup_ok': cleanup_ok,
              'cleanup_error': cleanup_error, 'final_snapshot': final_snapshot,
              'exception': exception_text, 'limits': limits, 'sample_count': samples,
              'peak_threads': peak_threads, 'peak_rss_bytes': peak_rss,
              'observed_bytes': observed_bytes, 'retained_bytes': retained_bytes,
              'raw_truncated': observed_bytes != retained_bytes,
              'guest_cycles': count,
              'active_wall_seconds': (active_end or ended) - started,
              'supervised_wall_seconds': ended - started, 'elapsed_seconds': ended - started,
              'raw_sha256': {name: sha(out / (name + '.log')) for name in observed_bytes},
              'execution_identity':identity,'observed_mapped_files':maps_evidence,
              'measurement_scope': '50ms sampled entire owned PGID; no thread exemptions; actual proc launch identity and observed mappings'}
    save(out / 'record.json', record)
    return record
