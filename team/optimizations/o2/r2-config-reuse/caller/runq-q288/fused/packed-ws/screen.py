"""Compile the new API and certify packed-scale mapping before target runs."""
from pathlib import Path
import argparse
import ctypes as C
import hashlib
import importlib.util
import json
import os
import random
import shutil
import struct
import subprocess
import sys
import zipfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = load('packed_ws_generator', HERE/'generate.py')
verify = load('packed_ws_verifier', HERE/'verify.py')
need, sha = verify.need, verify.sha
OWN = ('q288_ws.h', 'pack.c', 'generate.py', 'verify.py', 'screen.py', 'CONTRACT.md')
SCREEN_REL = gen.Q/'fused/evidence/screen-v1/raw.zip'
SCREEN_SHA = '201d0b2a01ab246338e6bdc80aaa486bed91254522bd8453c61e1d2de6d70df0'
FUSED_ELF_SHA = '6975d57aecd77f9ec6337cbf3aa5b031033e8a7b86dcad4bcd7e78b33b2dc97d'


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def support(repo):
    tail = load('packed_ws_fixed_tail_screen', repo/gen.Q/'fused/phased/tail/screen.py')
    model, helpers = tail.phased.support(repo)
    # Preserve partial tool output on timeout without editing the frozen helper
    # source or changing any successful execution/acceptance behavior.
    original_command = helpers.command
    def command(argv, cwd, index):
        try:
            return original_command(argv, cwd, index)
        except subprocess.TimeoutExpired as error:
            logs = {'stdout': error.stdout or b'', 'stderr': error.stderr or b''}
            for name, raw in logs.items():
                (cwd/f'{index:02}-{name}.log').write_bytes(raw)
            save(cwd/f'{index:02}-command.json', dict(
                argv=[str(v) for v in argv], cwd=str(cwd), exit_code=None,
                timed_out=True, timeout_seconds=error.timeout,
                stdout_sha256=sha(logs['stdout']), stderr_sha256=sha(logs['stderr'])))
            raise
    helpers.command = command
    return tail, model, helpers


def source_files(repo, tail):
    sources = tail.source_files(repo)
    for name in OWN:
        p = HERE/name
        sources[p.relative_to(repo).as_posix()] = sha(p.read_bytes())
    sources[SCREEN_REL.as_posix()] = sha((repo/SCREEN_REL).read_bytes())
    return sources


def baseline_binding(repo, elf, model, tail):
    need(sha((repo/SCREEN_REL).read_bytes()) == SCREEN_SHA, 'unchanged original full-Q screen archive')
    with zipfile.ZipFile(repo/SCREEN_REL) as archive:
        raw = archive.read('screen-03/fused.elf')
    need(sha(raw) == FUSED_ELF_SHA, 'original GNU full-Q reference ELF')
    reference = model.ELF(raw)
    names = ('q288_fused_vdot', 'q288_fused_rvv4')
    for name in names:
        need(elf.symbol_data(name) == reference.symbol_data(name), 'complete original function unchanged: '+name)
    proof = tail.certificate(elf)
    need(sha(elf.symbol_data('q288_tail_vdot')) == 'b318b99344d0ceabb2a5cab6ce671ab2bfcb189e4aacc9ffccb18488165971f3',
         'complete qualified TA function unchanged')
    return dict(status='EXACT_BASELINE_BODY_BINDING_PASS',
                function_sha256={name: sha(elf.symbol_data(name)) for name in (*names, 'q288_tail_vdot')},
                original_tail_certificate=proof)


def pack_host_checks(repo, out, helpers):
    out.mkdir()
    host = shutil.which('gcc')
    need(host, 'host GNU compiler')
    q = repo/gen.Q
    include = ['-I'+str(HERE), '-I'+str(q), '-I'+str(q.parent), '-I'+str(q.parent/'split')]
    argv = [host, '-std=c11', '-O2', '-shared', '-fPIC', '-ffreestanding', '-fno-builtin',
            '-fno-fast-math', '-ffp-contract=off', '-Wall', '-Wextra', '-Werror',
            *include, HERE/'pack.c', '-o', out/'pack.so']
    command = helpers.command(argv, out, 0)
    library = C.CDLL(str(out/'pack.so'))
    class Context(C.Structure):
        _fields_ = [('row_major', C.c_void_p), ('packed_scale', C.c_void_p)]
    library.q288_ws_pack.argtypes = [C.POINTER(Context)]
    library.q288_ws_pack.restype = None
    rng = random.Random(0x5753323838)
    special = [0, 0x80000000, 0x7f800000, 0xff800000, 0x7fc12345, 0x7f812345,
               1, 0x80000001, 0x007fffff, 0x00800000, 0x7f7fffff, 0xff7fffff]
    datasets = [('indices', list(range(2592))),
                ('special-and-random-raw-words', [special[i] if i < len(special) else rng.getrandbits(32) for i in range(2592)])]
    cases = []
    for label, words in datasets:
        expected = []
        for start in range(0, 2592, 72):
            rows = [words[start+9*r:start+9*r+9] for r in range(8)]
            expected.extend(x for column in zip(*rows) for x in column)
        for offset in (0, 4, 8, 12):
            # Keep actual pointers naturally aligned but exercise all 16B phases.
            source = C.create_string_buffer(b'\xa5'*10432, 10432)
            target = C.create_string_buffer(b'\x5a'*10432, 10432)
            source_at = 16 + ((-C.addressof(source)) % 16) + offset
            target_at = 16 + ((-C.addressof(target)) % 16) + offset
            original = struct.pack('<2592I', *words)
            C.memmove(C.addressof(source)+source_at, original, len(original))
            source_before = bytes(source)
            context = Context(C.addressof(source)+source_at, C.addressof(target)+target_at)
            context_before = bytes(context)
            library.q288_ws_pack(C.byref(context))
            actual = bytes(target)[target_at:target_at+10368]
            need(actual == struct.pack('<2592I', *expected), 'native pack bit representation and independent transpose')
            need(bytes(source) == source_before and bytes(context) == context_before, 'pack source/context readonly')
            need(bytes(target)[:target_at] == b'\x5a'*target_at and
                 bytes(target)[target_at+10368:] == b'\x5a'*(10432-target_at-10368), 'pack guards unchanged')
            cases.append(dict(dataset=label, pointer_mod16=offset, words=2592,
                              result_sha256=sha(actual), input_unchanged=True, guards_unchanged=True))
    result = dict(status='COMPILED_HOST_PACK_BITWISE_PASS', command=command,
                  host_library_sha256=sha((out/'pack.so').read_bytes()), cases=cases,
                  fp_arithmetic_qualified=False, note='NaN/Inf words test copying only, not kernel arithmetic')
    save(out/'result.json', result)
    return result


def baseline_numeric(repo, out, elf, tail, model, helpers):
    """Fresh checks of unchanged bodies, explicitly not the new load opcode."""
    out.mkdir()
    q = repo/gen.Q
    headers = {'q288.h': q/'q288.h', 'caller.h': q.parent/'caller.h', 'split.h': q.parent/'split/split.h'}
    library = helpers.oracle_library(q/'oracle.c', headers, out/'oracle')
    fixture = helpers.fixtures(q/'generate.py')
    machine_path = repo/'team/optimizations/o2/r2-safe-tail/machine_model.py'
    classes = [('q288_tail_vdot', tail.checker_class(model, machine_path)),
               ('q288_fused_rvv4', model.machine_class(machine_path))]
    cases = []
    for dataset in (0, 1, 2):
        golden = helpers.native_golden(library, fixture, dataset)
        need(golden == helpers.python_golden(fixture, dataset) == fixture['golden'][dataset],
             'independent original C/Python and frozen golden')
        for name, cls in classes:
            machine = cls(fixture, dataset, poison=0x575300+dataset)
            machine.execute_function(elf, name)
            detail = machine.check(golden) if name == 'q288_tail_vdot' else machine.check_full('rvv4', golden)
            cases.append(dict(function=name, dataset=dataset, **detail))
    result = dict(status='UNCHANGED_BASELINES_ACTUAL_ELF_NUMERIC_PASS', cases=cases,
                  new_candidate_numerically_interpreted=False,
                  candidate_basis='actual three-word certificate plus independent complete address/value equivalence')
    save(out/'result.json', result)
    return result


def screen(repo, out):
    repo, out = Path(repo).resolve(), Path(out).resolve()
    need(not out.exists() and not out.is_relative_to(repo), 'fresh isolated screen output')
    out.mkdir(parents=True)
    tail, model, helpers = support(repo)
    sources = source_files(repo, tail)
    # Capture the exact inputs before compilation, so failed runs retain the
    # same source evidence as successful ones. Verify every copied byte stream.
    for relative, expected in sources.items():
        destination = out/'source-snapshot'/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo/relative, destination)
        need(sha(destination.read_bytes()) == expected, 'verified source snapshot: '+relative)
    save(out/'source-manifest.json', sources)
    generation = gen.generate(repo, out/'generated')
    gcc = shutil.which('riscv64-linux-gnu-gcc')
    need(gcc, 'existing GNU RISC-V compiler')
    flags = [gcc, '-march=rv64gv', '-mabi=lp64d', '-mno-relax', '-mcmodel=medany', '-fno-pic', '-fno-pie', '-fno-lto']
    q = repo/gen.Q
    include = ['-I'+str(HERE), '-I'+str(q), '-I'+str(q.parent), '-I'+str(q.parent/'split')]
    commands = []
    commands.append(helpers.command(flags+['-c', out/'generated/q288-ws.S', '-o', out/'kernels.o'], out, 0))
    commands.append(helpers.command(flags+['-std=c11', '-O2', '-ffreestanding', '-fno-builtin',
        '-fno-tree-vectorize', '-fno-tree-slp-vectorize', '-fno-fast-math', '-ffp-contract=off',
        '-Wall', '-Wextra', '-Werror', *include, '-c', HERE/'pack.c', '-o', out/'pack.o'], out, 1))
    commands.append(helpers.command(flags+['-static', '-no-pie', '-nostdlib', '-nostartfiles',
        '-Wl,--build-id=none,--no-relax,-Ttext=0x80000000,-e,q288_ws_vdot',
        out/'kernels.o', out/'pack.o', '-o', out/'q288-ws.elf'], out, 2))
    elf = model.ELF((out/'q288-ws.elf').read_bytes())
    binding = baseline_binding(repo, elf, model, tail)
    proof = verify.certificate(elf)
    negative = verify.negative_controls(elf)
    host = pack_host_checks(repo, out/'host-pack', helpers)
    baseline = baseline_numeric(repo, out/'baseline-numeric', elf, tail, model, helpers)
    need(source_files(repo, tail) == sources, 'all old and new source bytes unchanged during screen')
    need(all(sha((out/'source-snapshot'/r).read_bytes()) == pin for r, pin in sources.items()),
         'all archived source bytes still match the input manifest')
    result = dict(status='PACKED_WS_STATIC_EQUIVALENCE_SCREEN_PASS', contract=gen.CONTRACT,
                  source_files=sources, generation=generation, commands=commands,
                  elf_sha256=sha(elf.raw), compiler_sha256=sha(Path(gcc).read_bytes()),
                  baseline_binding=binding, equivalence=proof, negative_controls=negative,
                  host_pack=host, baseline_numeric=baseline, new_emu_runs=0,
                  target_runtime_qualified=False, performance_qualified=False)
    save(out/'result.json', result)
    print(json.dumps({k: result[k] for k in ('status', 'contract', 'elf_sha256', 'new_emu_runs',
                                           'target_runtime_qualified', 'performance_qualified')}, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cpu', type=int, default=3)
    args = parser.parse_args()
    if os.name == 'posix':
        need(args.cpu in os.sched_getaffinity(0), 'requested CPU available')
        os.sched_setaffinity(0, {args.cpu})
    screen(args.repo, args.output)
