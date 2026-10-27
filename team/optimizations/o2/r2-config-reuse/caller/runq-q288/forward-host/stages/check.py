"""Execute complete host consumers; target qualification is explicitly absent."""
from pathlib import Path
import argparse
import csv
import datetime
import hashlib
import importlib.util
import json
import os
import platform
import re
import signal
import shutil
import subprocess
import sys
import time
import tempfile
import traceback

HERE = Path(__file__).resolve().parent
Q = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288')
CONTRACT = 'r2-s3-runq-forward-stages-v1'
BASE = 'b1d3f136dafae81cf76d2c1f35079cb1465ce7af'
spec = importlib.util.spec_from_file_location('forward_stage_generator', HERE/'generate.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
need, sha = gen.need, gen.sha


def save(path, value):
    path = Path(path)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                     prefix=path.name+'.', suffix='.tmp', delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(json.dumps(value, indent=2, ensure_ascii=False)+'\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def identity(repo):
    need(HERE == (repo/Q/'forward-host/stages').resolve(), 'selected source checkout owns executed script')
    relative = [Q/'forward-host/upstream/runq.c', Q/'forward-host/upstream/LICENSE',
                Q/'forward-host/observe.c', Q/'q288.h', Q/'acc8/q288.c',
                Q.parent/'caller.h', Q.parent/'split/split.h']
    relative += [Q/'forward-host/stages'/name for name in ('generate.py', 'driver.c', 'check.py', 'CONTRACT.md')]
    pins = {p.as_posix(): sha((repo/p).read_bytes()) for p in relative}
    need(pins[(Q/'forward-host/upstream/runq.c').as_posix()] == gen.UPSTREAM_SHA, 'unchanged complete upstream')
    need(pins[(Q/'forward-host/observe.c').as_posix()] == gen.OBSERVE_SHA, 'unchanged fixture helper/observer')
    return pins


def command(argv, out, name, expected=0, timeout=180, environment=None):
    argv = [str(v) for v in argv]
    record = dict(argv=argv, started_at=now(), status='started', timeout_seconds=timeout,
                  environment_overrides=environment or {})
    save(out/(name+'.command.json'), record)
    started = time.monotonic()
    process = None
    try:
        with (out/(name+'.stdout.log')).open('wb') as stdout, (out/(name+'.stderr.log')).open('wb') as stderr:
            process = subprocess.Popen(argv, stdout=stdout, stderr=stderr, start_new_session=True,
                                       env={**os.environ, **(environment or {})})
            record['process_id'] = process.pid
            code = process.wait(timeout=timeout)
        record.update(status='exited', exit_code=code, direct_child_reaped=True)
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            record['process_group_absent_after_exit'] = True
        else:
            os.killpg(process.pid, signal.SIGKILL)
            record.update(status='residual_process_group', process_group_kill_sent=True)
            raise RuntimeError('command left a live process group after its direct child exited')
    except subprocess.TimeoutExpired:
        record.update(status='timeout')
        try:
            os.killpg(process.pid, signal.SIGKILL)
            record['process_group_kill_sent'] = True
        except ProcessLookupError:
            record['process_group_already_absent'] = True
        process.wait()
        record.update(exit_code=process.returncode, direct_child_reaped=True)
        raise
    except BaseException as error:
        if record['status'] != 'residual_process_group':
            record.update(status='launch_error' if process is None else 'interrupted',
                          interruption_type=type(error).__name__, error=str(error))
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
                record['process_group_kill_sent'] = True
            except ProcessLookupError:
                record['process_group_already_absent'] = True
            process.wait()
            record.update(exit_code=process.returncode, direct_child_reaped=True)
        raise
    finally:
        record.update(ended_at=now(), elapsed_seconds=time.monotonic()-started)
        save(out/(name+'.command.json'), record)
    need(json.loads((out/(name+'.command.json')).read_text()) == record, 'durable command receipt readback')
    need(code == expected, name+' expected exit '+str(expected)+', got '+str(code))
    return record


def read_run(root, name, positions, validation):
    records = [json.loads(line) for line in (root/(name+'.stdout.log')).read_text().splitlines()]
    calls = [r for r in records if r.get('event') == 'call']
    wanted = [(p, m) for p in range(positions) for m in (1, 2, 3, 0)]
    need([(r['position'], r['method']) for r in calls] == wanted, 'every whole forward actually completed in order')
    complete = records[-1]
    need(complete == dict(event='complete', status='FORWARD_STAGES_PASS', positions=positions,
                          validation=int(validation), state_bytes=3691424, target_emu_runs=0), 'complete final execution receipt')
    passed = [r['position'] for r in records if r.get('event') == 'position_pass']
    need(passed == list(range(positions)), 'all continuous positions checked')
    for call in calls:
        traced = call['method'] in (1, 2)
        need(call['boundaries'] == (120 if traced else 0), 'exact traced/untraced boundary count')
        need(call['checked_quantizers'] == (25 if validation and call['method'] else 0), 'validation absent in timing build')
        need(0 <= call['stage_span_ns'] <= call['outer_ns'], 'stage span inside full call')
    groups = {}
    with (root/name/'stages.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    expected = gen.expected_events()[:-1]
    for row in rows:
        row = {k:int(v) for k,v in row.items()}
        groups.setdefault((row['position'], row['method']), []).append(row)
    need(set(groups) == {(p,m) for p in range(positions) for m in (1,2)}, 'all traced invocations have raw intervals')
    for key, intervals in groups.items():
        need(len(intervals) == 119, 'all half-open stage intervals')
        for i, interval in enumerate(intervals):
            stage, layer = expected[i]
            need((interval['index'], interval['tag'], interval['layer']) == (i, gen.STAGES.index(stage), layer), 'raw stage labels and layer route')
            need(interval['end_ns'] >= interval['start_ns'], 'monotonic raw interval')
            if i:
                need(intervals[i-1]['end_ns'] == interval['start_ns'], 'no gaps or overlapping adjacent intervals')
        delta = intervals[-1]['end_ns']-intervals[0]['start_ns']
        need(sum(v['end_ns']-v['start_ns'] for v in intervals) == delta, 'raw intervals independently close')
        call = next(v for v in calls if (v['position'],v['method']) == key)
        need(delta == call['stage_span_ns'], 'raw intervals match reported complete span')
    snapshots = {}
    for pos in sorted(set([0,1,2,positions-1])):
        first = (root/name/f'state-m0-p{pos}.bin').read_bytes()
        need(len(first) == 3691424, 'complete exported state byte count')
        for method in range(4):
            filename = f'state-m{method}-p{pos}.bin'
            value = (root/name/filename).read_bytes()
            need(value == first, 'independent raw state comparison')
            snapshots[filename] = sha(value)
    return dict(status=complete['status'], positions=positions, whole_forward_calls=len(calls),
                compared_state_spans=positions*3*16, traced_calls=positions*2,
                half_open_intervals=len(rows), snapshots=snapshots, calls=calls,
                validation=validation, host_timing_only=True, performance_qualified=False)


def run(repo, output, extended, sanitize, ownership):
    pins = identity(repo)
    need(not output.exists() and not output.is_relative_to(repo), 'fresh output outside source')
    output.mkdir(parents=True)
    ownership['created'] = True
    save(output/'source-pins.json', pins)
    for relative in pins:
        target=output/'source'/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(repo/relative,target)
        need(sha(target.read_bytes()) == pins[relative], 'initial source snapshot verified')
    certificate = gen.generate(repo/Q/'forward-host/upstream/runq.c', output/'forward.inc')
    save(output/'generation.json', certificate)
    gcc = shutil.which('gcc');need(gcc, 'host GNU compiler')
    flags = ['-std=gnu11','-O2','-ffp-contract=off','-fno-fast-math','-fexcess-precision=standard',
             '-fno-tree-vectorize','-fno-tree-slp-vectorize','-fno-inline','-fno-ipa-cp',
             '-fno-ipa-sra','-fno-ipa-icf','-fno-lto','-ffunction-sections','-fdata-sections',
             '-Wno-unknown-pragmas','-I'+str(output),'-I'+str(repo/Q),
             '-I'+str(repo/Q.parent),'-I'+str(repo/Q.parent/'split')]
    commands = []
    commands.append(command([gcc,'--version'],output,'compiler-version'))
    source = [HERE/'driver.c',repo/Q/'acc8/q288.c']
    for kind, validation in (('validate',1),('timing',0)):
        commands.append(command([gcc,*flags,f'-DSTAGES_VALIDATE={validation}',*source,
                                 '-Wl,--gc-sections,--build-id=none','-lm','-o',output/kind],output,'compile-'+kind))
    commands.append(command(['ldd',output/'validate'],output,'ldd'))
    dependencies = {str(Path(p).resolve()):sha(Path(p).read_bytes())
                    for p in re.findall(r'(/[^\s()]+)',(output/'ldd.stdout.log').read_text()) if Path(p).is_file()}
    commands.append(command(['nm','-u',output/'timing'],output,'undefined-symbols'))
    commands.append(command(['objdump','-drwC',output/'timing'],output,'disassembly'))
    results = {}

    def execute(name, binary, positions, validation, control=0, expected=0, rejection=None, environment=None):
        (output/name).mkdir()
        commands.append(command([output/binary,output/name,str(positions),str(control)],output,name,expected,
                                timeout=600,environment=environment))
        if rejection:
            need(rejection in (output/(name+'.stderr.log')).read_text(), 'specific rejection: '+rejection)
            return dict(status='EXPECTED_REJECTION',control=control,exit_code=expected,reason=rejection)
        return read_run(output,name,positions,validation)

    results['normal'] = execute('normal','validate',3,True)
    results['extended'] = execute('extended','validate',extended,True)
    controls = [(1,'drop-stage','exact boundary count'),
                (2,'wrong-layer','exact stage and layer sequence'),
                (3,'bad-angle','complete state equality'),
                (4,'historical-kv','all other KV rows unchanged'),
                (5,'aliased-state','independent state spans')]
    for control, name, reason in controls:
        results[name] = execute(name,'validate',3,True,control,2,reason)
    results['timing'] = execute('host-timing','timing',3,False)
    results['replay'] = execute('replay','validate',3,True)
    need(results['normal']['snapshots'] == results['replay']['snapshots'], 'new-process complete raw-state replay')
    need(results['normal']['snapshots'] == results['timing']['snapshots'], 'timing build preserves validation state bytes')
    for key, value in results['normal']['snapshots'].items():
        need(results['extended']['snapshots'][key] == value, 'extended prefix is unchanged')
    if sanitize:
        commands.append(command([gcc,*flags,'-DSTAGES_VALIDATE=1','-fsanitize=address,undefined,float-cast-overflow',
                                 '-fno-sanitize-recover=all',
                                 '-fno-omit-frame-pointer',*source,'-Wl,--gc-sections,--build-id=none',
                                 '-lm','-o',output/'sanitized'],output,'compile-sanitized'))
        results['sanitized'] = execute('sanitized-run','sanitized',3,True,
                                      environment={'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1',
                                                   'UBSAN_OPTIONS':'halt_on_error=1:print_stacktrace=1'})
        need(not (output/'sanitized-run.stderr.log').read_bytes(), 'sanitizers emitted no diagnostics')
        need(results['normal']['snapshots'] == results['sanitized']['snapshots'], 'sanitizers preserve all state bytes')
    need(identity(repo) == pins, 'all source files unchanged during execution')
    need(all(sha(Path(p).read_bytes()) == value for p,value in dependencies.items()), 'host runtime unchanged during execution')
    receipts={p.name:json.loads(p.read_text()) for p in output.glob('*.command.json')}
    need(len(receipts)==len(commands), 'all command receipts are present')
    need(all(v in list(receipts.values()) for v in commands), 'every final receipt equals executed command record')
    need(all(v['status']=='exited' for v in receipts.values()), 'no unknown started/running receipt at success')
    result = dict(status='HOST_FORWARD_STAGES_AND_ROPE_CANDIDATE_PASS',contract=CONTRACT,
                  base_commit=BASE,source_files=pins,generation=certificate,results=results,commands=commands,
                  platform=platform.platform(),python=platform.python_version(),cpu_affinity=sorted(os.sched_getaffinity(0)),
                  compiler_sha256=sha(Path(gcc).read_bytes()),dynamic_libraries=dependencies,
                  binary_sha256={name:sha((output/name).read_bytes()) for name in ('validate','timing')},
                  timing_unit='host_process_cpu_nanoseconds',target_emu_runs=0,target_runtime_ready=False,
                  sanitizer_scope={'requested':sanitize,'address':sanitize,'undefined':sanitize,
                                   'float_cast_overflow':sanitize,'leak_detection':'NOT_TESTED: explicitly disabled in this mode; initial executor limitation recorded separately'},
                  performance_qualified=False,trained_model_quality_qualified=False,
                  candidate_status='HOST_FUNCTIONAL_ONLY_TARGET_BLOCKED',completed_at=now())
    save(output/'result.json',result)
    return result


if __name__ == '__main__':
    def interrupted(signum, frame):
        raise InterruptedError('runner signal '+str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--extended-positions',type=int,default=256)
    parser.add_argument('--sanitize',action='store_true')
    args=parser.parse_args()
    need(3 <= args.extended_positions <= 256, 'extended positions in [3,256]')
    os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])
    output=args.output.resolve()
    ownership = {'created':False}
    try:
        result=run(args.repo.resolve(),output,args.extended_positions,args.sanitize,ownership)
        print(json.dumps({k:result[k] for k in ('status','contract','target_emu_runs','target_runtime_ready','performance_qualified')},indent=2))
    except BaseException:
        if ownership['created']:
            save(output/'failure.json',dict(status='FAIL',time=now(),traceback=traceback.format_exc()))
        raise
