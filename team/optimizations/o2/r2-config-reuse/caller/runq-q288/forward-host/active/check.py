"""Active full-forward state validation using qualified TA/FR actual ELF models.

The host reference is unchanged. Each candidate owns its state and produces its
own next input. This is mixed host/finite-model execution, never target timing.
"""
from pathlib import Path
import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import struct
import subprocess
import sys
import time
import traceback
import zipfile

HERE = Path(__file__).resolve().parent
Q = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288')
CONTRACT = 'r2-s3-runq-active-forward-v1'
ELF_SHA = '610c499f46f1fe73074f626d8990bdcbdbc5f78c30ce8fc4a835495b0e392faa'
UPSTREAM_SHA = 'ba9cc681afca79f994f815dfeffc4a61c5b3ca8c5d4d4dcb75c8d375856ba548'
OBSERVE_SHA = '92bd2986e8bca35dc2ed30d0338eac2a0c96ef6a54d766835c793ad6fb9e8236'
CALLBACK = ctypes.CFUNCTYPE(ctypes.c_int, *([ctypes.c_uint]*3+[ctypes.c_void_p]*6))


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def support(repo):
    tail = load('active_tail_screen', repo/Q/'fused/phased/tail/screen.py')
    model, helpers = tail.phased.support(repo)
    return tail, model, helpers


def source_identity(repo):
    need(HERE == (repo/Q/'forward-host/active').resolve(),
         'executed script is inside the selected source checkout')
    tail, _, _ = support(repo)
    pins = tail.source_files(repo)
    extra = [Q/'forward-host/observe.c', Q/'forward-host/upstream/runq.c',
             Q/'forward-host/upstream/LICENSE', Q/'acc8/q288.c']
    extra += [Q/'forward-host/active'/name for name in ('active.c', 'check.py', 'CONTRACT.md')]
    for name in extra:
        pins[name.as_posix()] = sha((repo/name).read_bytes())
    need(pins[(Q/'forward-host/upstream/runq.c').as_posix()] == UPSTREAM_SHA,
         'unchanged complete upstream reference')
    need(pins[(Q/'forward-host/observe.c').as_posix()] == OBSERVE_SHA,
         'unchanged deterministic fixture and passive reference observer')
    upstream = (repo/Q/'forward-host/upstream/runq.c').read_text()
    start = upstream.index('float* forward(')
    original = upstream[start:upstream.index('\n// ----------------------------------------------------------------------------', start)].strip()
    code = (HERE/'active.c').read_text()
    derived = code.split('/* BEGIN DERIVED FORWARD: only the name and explicit team call sites differ. */\n')[1]
    derived = derived.split('/* END DERIVED FORWARD */')[0].strip()
    derived = derived.replace('static float* team_forward(', 'float* forward(')
    derived = derived.replace('team_quantize(', 'quantize(').replace('team_matmul(', 'matmul(')
    for kind, output, weight, dimension in (
        (0, 's->q', 'w->wq + l', 'dim'), (1, 's->k', 'w->wk + l', 'kv_dim'),
        (2, 's->v', 'w->wv + l', 'kv_dim'), (3, 's->xb2', 'w->wo + l', 'dim')):
        old = f'team_project({output}, &s->xq, {weight}, (unsigned)(4*l+{kind}));'
        new = f'matmul({output}, &s->xq, {weight}, dim, {dimension});'
        need(derived.count(old) == 1, 'unique explicit projection route')
        derived = derived.replace(old, new)
    need(derived == original, 'all other forward source bytes/order unchanged')
    return pins


def image(repo, supplied):
    if supplied:
        raw = supplied.read_bytes()
        source = dict(path=str(supplied), kind='explicit qualified target ELF')
    else:
        archive = repo/Q/'fused/phased/tail/target/evidence/target-v1/archive/payload.zip'
        candidates = []
        with zipfile.ZipFile(archive) as z:
            for name in z.namelist():
                if name.endswith('.elf'):
                    value = z.read(name)
                    if sha(value) == ELF_SHA:
                        candidates.append((name, value))
        need(len(candidates) == 1, 'one qualified target ELF in published archive')
        member, raw = candidates[0]
        source = dict(path=str(archive), member=member, archive_sha256=sha(archive.read_bytes()))
    need(sha(raw) == ELF_SHA, 'fixed actual TA target ELF identity')
    return raw, source


def worker(repo, out, library, elf_path, control):
    need(not out.exists(), 'fresh worker output')
    out.mkdir(parents=True)
    pins = source_identity(repo)
    tail, model, helpers = support(repo)
    raw, _ = image(repo, elf_path)
    elf = model.ELF(raw)
    certificate = tail.certificate(elf)
    save(out/'certificate.json', certificate)
    integer = repo/'team/optimizations/o2/r2-safe-tail/machine_model.py'
    machines = (tail.checker_class(model, integer), model.machine_class(integer))
    names = ('q288_tail_vdot', 'q288_fused_rvv4')
    c = ctypes.CDLL(str(library))
    c.active_run.argtypes = [ctypes.c_char_p, ctypes.c_uint, CALLBACK]
    c.active_run.restype = ctypes.c_int
    records = []
    with (out/'callbacks.jsonl').open('w', buffering=1) as journal:
        @CALLBACK
        def project(method, pos, index, weight, packed, ws, x, xs, y):
            try:
                if control == 3 and method == pos == index == 0:
                    journal.write(json.dumps(dict(control='omit-output', method=method, pos=pos, index=index))+'\n')
                    return 0
                need(method in (0, 1) and pos in range(3) and index in range(24), 'callback bounds')
                read = ctypes.string_at
                raw_values = dict(weight=read(weight, 82944), packed=read(packed, 82944),
                                  weight_scale=read(ws, 10368), x=read(x, 288), xs=read(xs, 36))
                s8 = lambda value: list(struct.unpack('<'+'b'*len(value), value))
                u32 = lambda value: list(struct.unpack('<'+'I'*(len(value)//4), value))
                fixture = dict(weight=s8(raw_values['weight']), packed=s8(raw_values['packed']),
                               weight_scale=u32(raw_values['weight_scale']), inputs=[s8(raw_values['x'])],
                               input_scale=[u32(raw_values['xs'])])
                golden = helpers.python_golden(fixture, 0)
                machine = machines[method](fixture, 0, poison=0xA000+method*100+pos*24+index)
                machine.execute_function(elf, names[method])
                detail = machine.check(golden) if method == 0 else machine.check_full('rvv4', golden)
                result = bytes(machine.regions['y'])
                need(len(result) == 1152, 'complete machine result')
                ctypes.memmove(y, result, len(result))
                record = dict(method=method, position=pos, matrix=index, symbol=names[method],
                              input_sha256={name:sha(value) for name,value in raw_values.items()},
                              output_sha256=sha(result), validation=detail)
                records.append(record)
                journal.write(json.dumps(record)+'\n')
                print(f'ACTIVE_CALLBACK method={method} pos={pos} matrix={index}', flush=True)
                return 0
            except BaseException:
                save(out/'callback-failure.json', dict(traceback=traceback.format_exc(), method=method,
                                                       position=pos, matrix=index))
                return 2
        need(c.active_run(os.fsencode(out), control, project) == 0, 'active consumer completed')
    wanted = [(pos, method, index) for pos in range(3) for method in range(1 if control else 2) for index in range(24)]
    need([(r['position'], r['method'], r['matrix']) for r in records] == wanted, 'every actual callback in order')
    need(source_identity(repo) == pins, 'all source identities unchanged')
    comparisons = []
    for pos in range(3):
        for method in range(1 if control else 2):
            row = dict(position=pos, method=method)
            for tag, size in (('logits',128000),('key',1769472),('value',1769472)):
                reference = (out/f'reference-p{pos}-{tag}.bin').read_bytes()
                actual = (out/f'm{method}-p{pos}-{tag}.bin').read_bytes()
                need(len(reference) == len(actual) == size, 'complete state artifact size')
                row[tag+'_equal'] = reference == actual
                if not control:
                    need(reference == actual, 'independent full-state file comparison')
            comparisons.append(row)
    if control == 1:
        need(not comparisons[0]['key_equal'] and not comparisons[1]['key_equal']
             and not comparisons[1]['logits_equal'], 'independent historical K propagation check')
    elif control == 2:
        need(not comparisons[0]['value_equal'] and not comparisons[0]['logits_equal']
             and not comparisons[1]['logits_equal'], 'independent V propagation check')
    result = dict(status='ACTIVE_FORWARD_PASS' if not control else 'ACTIVE_PROPAGATION_NEGATIVE_PASS',
                  contract=CONTRACT, control=control, actual_elf_model_calls=len(records),
                  independent_run_states=2 if control else 3, comparisons=comparisons,
                  actual_candidate_output_drives_forward=True, target_emu_runs=0,
                  performance_qualified=False, trained_model_quality_qualified=False)
    save(out/'result.json', result)
    return result


def command(argv, out, name, expected=0, timeout=1800):
    started=time.time()
    record=dict(argv=[str(v) for v in argv],status='started',timeout_seconds=timeout,started_unix=started)
    receipt=out/(name+'.command.json');save(receipt,record)
    try:
        with (out/(name+'.stdout.log')).open('wb') as stdout, (out/(name+'.stderr.log')).open('wb') as stderr:
            process=subprocess.run(record['argv'], stdout=stdout, stderr=stderr, timeout=timeout)
        record.update(status='exited',exit_code=process.returncode)
    except subprocess.TimeoutExpired:
        record.update(status='timeout')
        raise
    except OSError as error:
        record.update(status='launch_error',error=str(error))
        raise
    finally:
        record['elapsed_seconds']=time.time()-started
        save(receipt,record)
    need(process.returncode==expected, 'command '+name+' expected exit '+str(expected))
    return record


def check(repo, out, elf_input):
    need(not out.exists() and not out.is_relative_to(repo), 'fresh output outside source')
    out.mkdir(parents=True)
    pins=source_identity(repo)
    save(out/'source-pins.json', pins)
    raw, origin=image(repo,elf_input)
    elf_path=out/'qualified-tail.elf';elf_path.write_bytes(raw)
    gcc=shutil.which('gcc');need(gcc,'GNU host compiler')
    flags=['-std=gnu11','-O2','-ffp-contract=off','-fno-fast-math','-fexcess-precision=standard',
           '-fno-tree-vectorize','-fno-tree-slp-vectorize','-fno-inline','-fno-ipa-cp','-fno-ipa-sra',
           '-fno-ipa-icf','-fno-lto','-fPIC','-Wno-unknown-pragmas',
           '-I'+str(repo/Q),'-I'+str(repo/Q.parent),'-I'+str(repo/Q.parent/'split')]
    commands=[]
    commands.append(command([gcc,*flags,'-finstrument-functions','-c',HERE/'active.c','-o',out/'active.o'],out,'compile-active',timeout=120))
    commands.append(command([gcc,*flags,'-c',repo/Q/'acc8/q288.c','-o',out/'acc8.o'],out,'compile-acc8',timeout=120))
    library=out/'active.so'
    commands.append(command([gcc,'-shared','-Wl,--build-id=none,-Bsymbolic',out/'active.o',out/'acc8.o','-lm','-o',library],out,'link',timeout=120))
    library_sha=sha(library.read_bytes())
    ldd=subprocess.run(['ldd',str(library)],capture_output=True,check=True)
    (out/'ldd.stdout.log').write_bytes(ldd.stdout);(out/'ldd.stderr.log').write_bytes(ldd.stderr)
    dynamic={str(Path(name).resolve()):sha(Path(name).read_bytes())
             for name in re.findall(r'(/[^\s()]+)',ldd.stdout.decode()) if Path(name).is_file()}
    worker_args=[sys.executable,'-B',HERE/'check.py','--repo',repo,'--library',library,'--elf',elf_path]
    results=[]
    for control,label in ((0,'normal'),(1,'corrupt-k'),(2,'corrupt-v'),(3,'omit-output')):
        dest=out/label
        commands.append(command([*worker_args,'--output',dest,'--worker',str(control)],out,label,expected=2 if control==3 else 0))
        if control==3:
            need('callback overwrote every output' in (out/(label+'.stderr.log')).read_text(),'specific omitted-write rejection')
            results.append(dict(control=3,status='OMITTED_WRITE_REJECTED',exit_code=2))
        else:
            results.append(json.loads((dest/'result.json').read_text()))
    need(source_identity(repo)==pins,'unchanged full source closure at completion')
    need(sha(library.read_bytes())==library_sha,'unchanged compiled active consumer')
    need(all(sha(Path(p).read_bytes())==value for p,value in dynamic.items()),'unchanged dynamic libraries')
    for name in pins:
        target=out/'source-snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/name,target)
    result=dict(status='ACTIVE_FORWARD_AND_PROPAGATION_CONTROLS_PASS',contract=CONTRACT,
                source_files=pins,elf_sha256=ELF_SHA,elf_origin=origin,
                host_library_sha256=sha(library.read_bytes()),host_compiler_sha256=sha(Path(gcc).read_bytes()),
                dynamic_libraries=dynamic,platform=platform.platform(),python=platform.python_version(),
                cpu_affinity=sorted(os.sched_getaffinity(0)),results=results,commands=commands,
                positive_model_calls=144,negative_model_calls=144,states_in_positive=3,
                candidate_uses_own_inputs=True,reference_unchanged=True,persistent_packs=24,
                pack_bytes=1990656,target_emu_runs=0,performance_qualified=False,
                trained_model_quality_qualified=False)
    save(out/'result.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--elf',type=Path);parser.add_argument('--library',type=Path)
    parser.add_argument('--worker',type=int,choices=range(4))
    args=parser.parse_args();os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])
    repo=args.repo.resolve();out=args.output.resolve()
    if args.worker is not None:
        result=worker(repo,out,args.library.resolve(),args.elf.resolve(),args.worker)
    else:
        result=check(repo,out,args.elf.resolve() if args.elf else None)
    print(json.dumps(result,indent=2))
