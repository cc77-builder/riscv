"""Real GNU ELF plus bounded exact-value/address screen; no EMU or cycles."""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import struct
import sys
import time

import generate
import model

HERE = Path(__file__).resolve().parent
FUSED = generate.REL
Q = FUSED.parent
HELPER_SHA = '39bfbe63942d15ad5bee4e32e08153c2edf56cc8ce2058f74c199550f16cf5ae'
need = model.need
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def helpers(repo):
    path = repo / FUSED / 'screen.py'
    need(sha(path.read_bytes()) == HELPER_SHA, 'unchanged full-Q independent oracle/check helpers')
    parent, _ = generate.load_parent(repo)
    fp = model.pinned_model(repo)
    previous = {name: sys.modules.get(name) for name in ('generate', 'model')}
    sys.modules.update(generate=parent, model=fp)
    try:
        spec = importlib.util.spec_from_file_location('rowlane32_parent_screen', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        for name, value in previous.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value
    return module, fp, parent


def source_paths(repo):
    paths = [Q/'generate.py', Q/'oracle.c', Q/'q288.h', Q.parent/'caller.h',
             Q.parent/'split/split.h', model.INTEGER,
             Path('team/optimizations/o2/r2-config-reuse/public/gemv.S')]
    paths += [FUSED/name for name in ('generate.py', 'model.py', 'screen.py', 'CONTRACT.md')]
    paths += [FUSED/'rowlane32'/name for name in ('generate.py', 'model.py', 'screen.py', 'CONTRACT.md')]
    return {str(path): sha((repo/path).read_bytes()) for path in paths}


def verify_inputs(repo, out):
    recorded = json.loads((out/'input-sha256.json').read_text())
    need(source_paths(repo) == recorded, 'all frozen screen inputs unchanged')
    build = json.loads((out/'build-result.json').read_text())
    need(build['status'] == 'ROWLANE32_GNU_BUILD_PASS' and
         sha((out/'rowlane32.elf').read_bytes()) == build['elf_sha256'], 'actual screened ELF identity')
    return build


def build(repo, out):
    need(not out.exists() and not out.is_relative_to(repo), 'fresh output outside checkout')
    out.mkdir(parents=True)
    pins = source_paths(repo)
    save(out/'input-sha256.json', pins)
    for name in pins:
        target = out/'source-snapshot'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo/name, target)
    helper, fp, parent = helpers(repo)
    generated = generate.generate(repo, out/'source')
    # Compile the unchanged original full-Q generator separately, then compare
    # the entire retained FR function, not only its integer block.
    parent.generate(repo, out/'reference-source')
    gcc, objdump = shutil.which('riscv64-linux-gnu-gcc'), shutil.which('riscv64-linux-gnu-objdump')
    need(gcc and objdump, 'existing GNU RISC-V compiler and objdump')
    prefix = [gcc, '-march=rv64gv', '-mabi=lp64d', '-mno-relax']
    commands = []
    def run(argv):
        commands.append(helper.command(argv, out, len(commands)))
    run([gcc, '--version'])
    run(prefix + ['-c', out/'source/rowlane32.S', '-o', out/'rowlane32.o'])
    link = ['-static', '-no-pie', '-nostdlib', '-nostartfiles', '-Wl,--build-id=none,--no-relax,-Ttext=0x80000000']
    run(prefix + link + ['-Wl,-e,'+generate.NAME, out/'rowlane32.o', '-o', out/'rowlane32.elf'])
    run(prefix + ['-c', out/'reference-source/fused.S', '-o', out/'unchanged-fused.o'])
    run(prefix + link + ['-Wl,-e,q288_fused_rvv4', out/'unchanged-fused.o', '-o', out/'unchanged-fused.elf'])
    run(prefix + ['-c', repo/parent.PUBLIC, '-o', out/'public-reference.o'])
    disassembly_index = len(commands)
    run([objdump, '-drwC', out/'rowlane32.elf'])
    elf, reference = fp.ELF((out/'rowlane32.elf').read_bytes()), fp.ELF((out/'unchanged-fused.elf').read_bytes())
    baseline = elf.symbol_data('q288_fused_rvv4')
    need(baseline == reference.symbol_data('q288_fused_rvv4'), 'unchanged complete FR machine words')
    public = fp.ELF((out/'public-reference.o').read_bytes())
    name = 'config_reuse_gemv_8x32_reuse_rvv'
    certificate = fp.core_certificate(elf, {name: public.symbol_data(name).hex()}, 'rvv4')
    need(source_paths(repo) == pins, 'all source inputs unchanged across actual build')
    result = dict(status='ROWLANE32_GNU_BUILD_PASS', contract=generate.CONTRACT,
                  elf_sha256=sha(elf.raw), object_sha256=sha((out/'rowlane32.o').read_bytes()),
                  candidate_symbol=generate.NAME, candidate_bytes=len(elf.symbol_data(generate.NAME)),
                  candidate_machine_sha256=sha(elf.symbol_data(generate.NAME)),
                  unchanged_fr_sha256=sha(baseline), unchanged_fr_bytes=len(baseline),
                  unchanged_fr_integer_certificate=certificate, generation=generated,
                  commands=commands, disassembly_file=f'{disassembly_index:02}-stdout.log',
                  gcc_sha256=sha(Path(gcc).read_bytes()), objdump_sha256=sha(Path(objdump).read_bytes()),
                  cpu_affinity=sorted(os.sched_getaffinity(0)),
                  target_runtime_qualified=False, performance_qualified=False, new_emu_runs=0)
    save(out/'build-result.json', result)
    return result


def repack(fixture):
    result = copy.deepcopy(fixture)
    result['packed'] = generate.pack_q288(result['weight'])
    return result


def numeric(repo, out):
    identity = verify_inputs(repo, out)
    run = out/'numeric'
    run.mkdir(exist_ok=False)
    helper, fp, _ = helpers(repo)
    headers = {'q288.h': repo/Q/'q288.h', 'caller.h': repo/Q.parent/'caller.h',
               'split.h': repo/Q.parent/'split/split.h'}
    lib = helper.oracle_library(repo/Q/'oracle.c', headers, run/'oracle')
    primitive = helper.fp_primitive_checks(lib)
    base = helper.fixtures(repo/Q/'generate.py')
    cases = [('x'+str(d), base, d) for d in (0, 1, 0, 2)]
    for name, weight, vector in (
            ('min-min', [-128]*82944, [-128]*288),
            ('max-max', [127]*82944, [127]*288),
            ('min-max', [-128]*82944, [127]*288),
            ('zero-weight', [0]*82944, base['inputs'][0])):
        f = copy.deepcopy(base)
        f['weight'], f['inputs'][0] = weight, vector
        f['packed'] = [weight[(8*t+r)*288+g*32+k] for t in range(36) for g in range(9) for r in range(8) for k in range(32)]
        cases.append((name, f, 0))
    elf = fp.ELF((out/'rowlane32.elf').read_bytes())
    old_class, new_class = fp.machine_class(repo/model.INTEGER), model.machine_class(repo)
    machines, results = {}, []
    for i, (name, f, d) in enumerate(cases):
        golden = helper.native_golden(lib, f, d)
        need(golden == helper.python_golden(f, d), 'independent native C and Python full-Q golden')
        if i < 4:
            need(golden == f['golden'][d], 'frozen fixture golden identity')
        if i == 0:
            need(golden[0] == 0, 'original strict FMA witness')
        aligned = (0, 0) if i < 4 else ((i*3) % 16, (i*7) % 16)
        row = dict(case=name, index=i, dataset=d, golden_bits=golden, byte_alignment=aligned, methods={})
        for kind, cls, fixture, symbol in (
                ('unchanged_fr', old_class, f, 'q288_fused_rvv4'),
                ('rowlane32_w8', new_class, repack(f), generate.NAME)):
            machine = cls(fixture, d, poison=0x32000+i, alignment=aligned)
            if i in (1, 2, 3):
                previous = machines[kind]
                need(machine.regions['packed'] == previous.regions['packed'], 'same packed buffer for x0/x1/x0/x2')
                machine.regions['packed'] = previous.regions['packed']
                machine.v = [bytearray(v) for v in previous.v]
            machine.execute_function(elf, symbol)
            checked = machine.check_full('rvv4', golden) if kind == 'unchanged_fr' else machine.check_full(golden)
            checked['packed_sha256'] = sha(bytes(v & 255 for v in fixture['packed']))
            row['methods'][kind] = checked
            machines[kind] = machine
        results.append(row)
        save(run/f'{i:02}-{name}.json', row)
    verify_inputs(repo, out)
    result = dict(status='ROWLANE32_ACTUAL_ELF_NUMERIC_PASS', elf_sha256=identity['elf_sha256'],
                  cases=results, primitives=primitive, fma_witness=dict(strict=0, fused=0xa3800000),
                  finite_value_model_only=True, fflags_modeled=False, new_emu_runs=0,
                  target_runtime_qualified=False, performance_qualified=False)
    save(run/'result.json', result)
    return result


def controls(repo, out):
    identity = verify_inputs(repo, out)
    run = out/'elf-controls'
    run.mkdir(exist_ok=False)
    helper, fp, _ = helpers(repo)
    original_fixture = helper.fixtures(repo/Q/'generate.py')
    fixture = repack(original_fixture)
    cls = model.machine_class(repo)
    elf = fp.ELF((out/'rowlane32.elf').read_bytes())
    address, _, offset = elf.symbols[generate.NAME]
    words = [w for w, in struct.iter_unpack('<I', elf.symbol_data(generate.NAME))]
    find = lambda predicate: next(i for i, w in enumerate(words) if predicate(w))
    avl = find(lambda w: w & 0x000fffff == 0x00000e93 and w >> 20 == 32)
    wstep = find(lambda w: w & 0x000fffff == 0x00060613 and w >> 20 == 32)
    xload = find(lambda w: w & 0x000fffff == 0x00058f03 and w >> 20 == 0)
    sext = find(lambda w: w & 127 == 0x57 and (w >> 26, (w >> 12) & 7) == (0x12, 2))
    mac = find(lambda w: w & 127 == 0x57 and (w >> 26, (w >> 12) & 7) == (0x3d, 6))
    zero = max(i for i, w in enumerate(words) if w & 127 == 0x57 and (w >> 26, (w >> 12) & 7) == (0x17, 3))
    csr = find(lambda w: w == 0x00f3d073)
    mul = find(lambda w: w & 127 == 0x57 and (w >> 26, (w >> 12) & 7) == (0x24, 1))
    changes = [
        ('short-vl', avl, lambda w: (w & 0x000fffff) | (31 << 20)),
        ('wrong-weight-step', wstep, lambda w: (w & 0x000fffff) | (64 << 20)),
        ('wrong-x-byte', xload, lambda w: (w & 0x000fffff) | (1 << 20)),
        ('unsigned-extension', sext, lambda w: (w & ~(31 << 15)) | (6 << 15)),
        ('wrong-widening-source', mac, lambda w: (w & ~(31 << 20)) | (24 << 20)),
        ('unaligned-widening-destination', mac, lambda w: (w & ~(31 << 7)) | (1 << 7)),
        ('missing-slot-high-zero', zero, lambda w: 0x00000013),
        ('missing-vcsr-reset', csr, lambda w: 0x00000013),
        ('callee-saved-clobber', len(words)-2, lambda w: (w & ~(31 << 7)) | (8 << 7)),
    ]
    mutants = []
    for name, index, change in changes:
        before, after = words[index], change(words[index])
        need(before != after, 'actual ELF word mutation')
        raw = bytearray(elf.raw)
        struct.pack_into('<I', raw, offset+4*index, after)
        mutants.append((name, bytes(raw), dict(pc=hex(address+4*index), original_words=[hex(before)], mutated_words=[hex(after)])))
    need(words[mul+1] & 127 == 7 and words[mul+2] >> 26 == 0x24 and (words[mul+2] >> 12) & 7 == 5,
         'exact valid three-word scale-order control')
    reordered = [words[mul+1], words[mul+2], words[mul]]
    raw = bytearray(elf.raw)
    struct.pack_into('<3I', raw, offset+4*mul, *reordered)
    mutants.append(('wrong-rounding-order', bytes(raw), dict(pc=hex(address+4*mul), original_words=[hex(v) for v in words[mul:mul+3]], mutated_words=[hex(v) for v in reordered])))
    results = []
    for name, raw, detail in mutants:
        (run/(name+'.elf')).write_bytes(raw)
        machine = cls(fixture, 0, poison=0x320771)
        try:
            machine.execute_function(fp.ELF(raw), generate.NAME).check_full(fixture['golden'][0])
        except ValueError as error:
            if name == 'wrong-rounding-order':
                need(str(error) == 'actual ELF full-Q bitwise output', 'specific scale-rounding witness')
            results.append(dict(name=name, mutated_elf_sha256=sha(raw), error=str(error),
                                executed_instructions=len(machine.path), fp_element_counts=dict(machine.fp_counts), **detail))
        else:
            raise ValueError('actual ELF mutant accepted: '+name)
    # Same context type does not make the old packed format compatible.
    machine = cls(original_fixture, 0, poison=0x320772)
    try:
        machine.execute_function(elf, generate.NAME).check_full(original_fixture['golden'][0])
    except ValueError as error:
        need(str(error) == 'actual ELF full-Q bitwise output', 'specific incompatible packed-layout rejection')
        layout_control = dict(status='REJECTED', error=str(error), packed_sha256=sha(bytes(v & 255 for v in original_fixture['packed'])))
    else:
        raise ValueError('old packed layout accepted as row32')
    verify_inputs(repo, out)
    result = dict(status='ROWLANE32_ACTUAL_ELF_REJECTIONS_PASS', elf_sha256=identity['elf_sha256'], controls=results,
                  incompatible_layout=layout_control, new_emu_runs=0, target_runtime_qualified=False, performance_qualified=False)
    save(run/'result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--phase', choices=('build', 'numeric', 'controls'), required=True)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.output.resolve()
    need(not out.is_relative_to(repo), 'isolated run output')
    started = time.time()
    try:
        result = globals()[args.phase](repo, out)
    except Exception as error:
        if out.is_dir():
            save(out/f'failure-{args.phase}-{time.time_ns()}.json', dict(status='FAIL', error=repr(error), elapsed_seconds=time.time()-started))
        raise
    print(json.dumps({key: value for key, value in result.items() if key not in ('cases', 'commands', 'controls')}, indent=2))
