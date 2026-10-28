"""Build an optional W2 consumer using the frozen RMSNorm output objects."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import signal
import struct
import subprocess
import sys
import types

HERE = Path(__file__).resolve().parent
STAGES = HERE.parent.parent
CONTRACT = 'r2-s3-forward-consumer-w2-norm-v1'
API_CONTRACT = 'r2-s3-forward-consumer-w2-norm-api-v1'
PREFIX = 'forward-consumer-w2-norm'
API_PREFIX = 'consumer-w2-norm-api'
CORE = 'consumer-w2-norm.o'
STATIC = 'NORM_W2_CONSUMER_STATIC_PASS_NOT_RUNTIME'
API_STATIC = 'NORM_W2_API_STATIC_PASS_NOT_RUNTIME'
PASS = 'NORM_W2_FORWARD_REFERENCE_CAMPAIGN_PASS'
API_PASS = 'NORM_W2_API_REFERENCE_CAMPAIGN_PASS'
PARENTS = {
    'consumer.c': '9f1cdab57add8b0088554625a032f0d9c3df98b5046e80fb3f4c8b63e354ec53',
    'consumer.inc': '02f6abae8c48977289c8fb21abac8fc90a71a77259bc10644303a14aa1360367',
}
NORM_OBJECTS = {
    'candidate.o': 'def02af4f87c85ba4ea5ce49cc02938f28afa9fefb69700c2b2a616c3694cb60',
    'norm.o': 'ef52d03e9691fc20289bf039a3a47dbafc81f1a22b964b2206ca8b55f90d0c4e',
}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


w = load('norm_consumer_parent_reference', STAGES / 'w2/consumer_run.py')
a = load('norm_consumer_parent_api', STAGES / 'w2/api.py')
n = load('norm_consumer_norm_build', HERE.parent / 'build.py')
nr = load('norm_consumer_norm_reference', HERE.parent / 'reference.py')
base = w.b.old
REPO = base.REPO
need, read, save, digest, command = base.need, base.read, base.save, base.digest, base.command
S = w.STATE_BYTES
MODELS = a.MODELS


def bind(function, **dependencies):
    """Reuse exact team validator bytecode with explicit isolated dependencies.

    Never mutate a parent module, its source, a historical result or a gate.
    These are path/identity bindings, not substituted numerical verdicts.
    """
    namespace = dict(function.__globals__)
    namespace.update(dependencies)
    return types.FunctionType(function.__code__, namespace, function.__name__,
                              function.__defaults__, function.__closure__)


def module_files():
    pending = [*sys.modules.values(), w, a, n, nr, base]
    seen = set()
    while pending:
        module = pending.pop()
        if not isinstance(module, types.ModuleType) or id(module) in seen:
            continue
        seen.add(id(module))
        pending.extend(v for v in vars(module).values() if isinstance(v, types.ModuleType))
        name = getattr(module, '__file__', None)
        if name:
            path = Path(name).resolve()
            if path.is_relative_to(REPO) and path.is_file():
                yield path


def pin(files, path, value=None):
    path = str(Path(path).resolve())
    value = digest(path) if value is None else value
    need(path not in files or files[path] == value, 'no pinned input rebinding: ' + path)
    need(digest(path) == value, 'unchanged pinned input: ' + path)
    files[path] = value


def inherit(files, root, record):
    for path, value in record['external_pins'].items():
        pin(files, path, value)
    for group, folder in (('artifacts', root), ('fixtures', root / 'fixture'),
                          ('actual_source_pins', root / 'source')):
        for name, value in record[group].items():
            pin(files, folder / name, value)
    for name in ('result.json', 'tools.json', 'target-build.stdout.log'):
        pin(files, root / name)


def derive(source):
    records = {}
    for name, expected in PARENTS.items():
        path = source / name
        original = path.read_bytes()
        need(hashlib.sha256(original).hexdigest() == expected, 'exact W2 source parent: ' + name)
        if name == 'consumer.c':
            before, after, count = b'#include "consumer_w2.h"', b'#include "consumer_w2.h"\n#include "norm.h"', 1
        else:
            before, after, count = b'rmsnorm(', b'r2_rmsnorm_rvv(', 12
        need(original.count(before) == count and after not in original, 'bounded new norm call substitution')
        changed = original.replace(before, after)
        need(changed.count(after) == count and changed.replace(after, before) == original,
             'complete exact source reversal')
        path.write_bytes(changed)
        records[name] = dict(parent_sha256=expected, generated_sha256=digest(path),
                             substitutions=count, exact_parent_reverse=True)
    return dict(contract=CONTRACT, sources=records, optimized_call_sites=12,
                upstream_forward_unchanged=True, method_api_unchanged=True)


def norm_link_identity(elf, original):
    """Allow only the eight link-fixup instruction immediates of frozen norm C."""
    name = 'r2_rmsnorm_rvv'
    old_pc, old_size, *_ = original.symbols[name]
    new_pc, new_size, *_ = elf.symbols[name]
    need(old_size == new_size == 192, 'complete frozen norm C function')
    old_words = list(struct.unpack('<48I', original.read(old_pc, old_size)))
    new_words = list(struct.unpack('<48I', elf.read(new_pc, new_size)))
    relocations = []
    for offset, target in ((0x60, None), (0x70, 'sqrtf'), (0x78, None), (0x94, 'r2_norm_output_rvv')):
        resolved = []
        for image, pc, words in ((original, old_pc, old_words), (elf, new_pc, new_words)):
            hi, lo = words[offset // 4:offset // 4 + 2]
            need(hi & 0x7f == 0x17 and lo & 0x7f == (0x67 if target else 0x07), 'fixed AUIPC/call or float load pair')
            need((hi >> 7) & 31 == (lo >> 15) & 31, 'linked high/low register dependency')
            signed_hi = struct.unpack('<i', struct.pack('<I', hi & 0xfffff000))[0]
            signed_lo = (lo >> 20) - (4096 if lo >> 31 else 0)
            address = pc + offset + signed_hi + signed_lo
            if target:
                need(address == image.symbols[target][0], 'exact linked call target: ' + target)
            else:
                resolved.append(image.read(address, 4))
            words[offset // 4] &= 0x00000fff
            words[offset // 4 + 1] &= 0x000fffff
        if target is None:
            need(resolved[0] == resolved[1], 'same actual norm floating constant')
        relocations.append(dict(offset=offset, target=target,
                                constant_hex=resolved[0].hex() if resolved else None))
    need(old_words == new_words, 'every non-relocation instruction bit unchanged')
    leaf = 'r2_norm_output_rvv'
    old_pc, old_size, *_ = original.symbols[leaf]
    new_pc, new_size, *_ = elf.symbols[leaf]
    need(old_size == new_size == 64 and original.read(old_pc, 64) == elf.read(new_pc, 64),
         'whole norm output leaf bytes unchanged')
    return dict(non_relocation_bits_equal=True, relocations=relocations,
                output_leaf_bytes_equal=True, output_leaf_sha256=hashlib.sha256(elf.read(new_pc, 64)).hexdigest())


def inspect(output, prefix, record, norm_build):
    elf, inspection = base.f.executable(output / (prefix + '.elf'), output / (prefix + '.bin'),
                                        output / 'metadata.stdout.log', record['tls_errno_offset'])
    functions = base.p.kernel_bytes(output / (prefix + '.elf'), record['kernel_identity']['functions'])
    need(len(functions) == 4, 'all four actual K288/K768 kernels')
    for name, raw in functions.items():
        expected = record['kernel_identity']['functions'][name]
        need(len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256'],
             'whole qualified kernel bytes: ' + name)
    original, _ = n.executable(norm_build / 'real-norm.elf', norm_build / 'real-norm.bin')
    identity = norm_link_identity(elf, original)
    text = (output / 'disassembly.stdout.log').read_text()
    calls = [int(m[1], 16) for m in re.finditer(r'\b([0-9a-f]+):\s+R_RISCV_CALL(?:_PLT)?\s+r2_rmsnorm_rvv\b', text)]
    routes = {}
    for name in ('consumer_fr', 'consumer_ta', 'consumer_fr_cache', 'consumer_ta_cache'):
        pc, size, *_ = elf.symbols[name]
        routes[name] = sum(pc <= address < pc + size for address in calls)
        need(routes[name] == 3, 'three actual norm call sites in ' + name)
    pc, size, *_ = elf.symbols['forward']
    need(len(calls) == 12 and not any(pc <= address < pc + size for address in calls),
         'only optimized forward functions route to candidate norm')
    identity.update(static_route_calls=routes, total_static_route_calls=12, dynamic_call_count_claimed=False)
    return elf, inspection, identity


def build(output, parent, norm_build=None, campaign=None, norm_reference=None, api=False):
    record = read(parent / 'result.json')
    prefix, contract, status = (API_PREFIX, API_CONTRACT, API_STATIC) if api else (PREFIX, CONTRACT, STATIC)
    if api:
        need(record['contract'] == CONTRACT and record['status'] == STATIC, 'distinct new norm consumer build')
        qualified, state = read(campaign / 'results.json'), read(campaign / 'state.json')
        need(qualified['contract'] == CONTRACT and qualified['status'] == state['status'] == PASS
             and state['active'] == [] and not state['cleanup_unknown'], 'completed new eight-case qualification')
        need(set(qualified['validations']) == {x[0] for x in w.old.CASES} and state['reference_runs'] == 8,
             'all eight independent new consumer cases')
        norm_build = Path(record['norm_build'])
    else:
        need(record['contract'] == w.b.CONTRACT and record['status'] == 'PURE_W2_CONSUMER_STATIC_ELF_PASS_NOT_RUNTIME',
             'qualified original W2 build')
        qualified, state = read(campaign / 'results.json'), read(campaign / 'state.json')
        need(qualified['contract'] == w.b.CONTRACT and qualified['status'] == state['status'] ==
             'PURE_W2_FORWARD_REFERENCE_CAMPAIGN_PASS' and state['active_pid'] is None, 'finished original W2 qualification')
        need(set(qualified['validations']) == {x[0] for x in w.CASES}, 'ten original W2 cases')
    norm = read(norm_build / 'result.json')
    need(norm['contract'] == n.CONTRACT and norm['status'] == 'NORM_STATIC_CAPTURE_AND_ELF_PASS_NOT_RUNTIME',
         'frozen norm build')
    for name, value in NORM_OBJECTS.items():
        need(norm['artifacts'][name] == digest(norm_build / name) == value, 'frozen norm object: ' + name)
    if not api:
        refs, refstate = read(norm_reference / 'results.json'), read(norm_reference / 'state.json')
        need(refs['contract'] == n.CONTRACT and refs['status'] == refstate['status'] == 'NORM_REFERENCE_CAMPAIGN_PASS'
             and refstate['active_pid'] is None, 'completed norm numerical reference qualification')
        for name in ('negative', 'normal', 'replay'):
            actual = nr.validate(norm_build, norm_reference / name, norm,
                                 read(norm_reference / name / 'result.json'), name == 'negative')
            need(actual == refs['validations'][name] == read(norm_reference / name / 'validation.json'),
                 'actual re-audited norm reference: ' + name)
    am = Path(record['am_home'])
    protected = [REPO, parent, norm_build, campaign, am]
    if norm_reference is not None:
        protected.append(norm_reference)
    need(not output.exists() and not any(output.is_relative_to(root) for root in protected),
         'fresh output outside all fixed inputs')
    need(subprocess.check_output(['git', '-C', am, 'rev-parse', 'HEAD'], text=True).strip() ==
         '086a238062fdfb3281b745a537b361983d0154b5', 'same official AM revision')
    need(not subprocess.check_output(['git', '-C', am, 'status', '--porcelain', '--untracked-files=no'],
                                    text=True).strip(), 'official AM unchanged')
    external = {}
    inherit(external, parent, record); inherit(external, norm_build, norm)
    parent_runtime = read(campaign / 'runtime-inputs.json')
    for group, folder in (('artifacts', parent), ('fixtures', parent / 'fixture'),
                          ('actual_source_pins', parent / 'source')):
        for name, value in record[group].items():
            need(parent_runtime[str(folder / name)] == value, 'qualified campaign consumed this exact parent')
    parent_recheck = {}
    if not api:
        # The unchanged W2 route's historical pack-fault evidence belongs to
        # this precise parent, not merely to a summary with the right label.
        for label, method, kind in w.CASES:
            dest = campaign / label
            actual = w.validate(parent, dest, record, method, kind, read(dest / 'result.json'))
            need(actual == qualified['validations'][label] == read(dest / 'validation.json'),
                 're-audited exact W2 parent case: ' + label)
            parent_recheck[label] = actual
            for filename, value in actual['raw_sha256'].items():
                pin(external, dest / filename, value)
            for filename in ('result.json', 'validation.json', 'reference-result.json', 'abi.json',
                             'image-control.json', 'image.bin', 'stdout.log', 'stderr.log',
                             'initial-registers.bin', 'final-registers.bin', 'initial-csrs.bin', 'final-csrs.bin'):
                pin(external, dest / filename)
        norm_runtime = read(norm_reference / 'runtime-inputs.json')
        for name, value in norm['artifacts'].items():
            need(norm_runtime[str(norm_build / name)] == value, 'norm reference consumed the frozen norm artifacts')
        for label in ('negative', 'normal', 'replay'):
            dest = norm_reference / label
            for filename, value in refs['validations'][label]['raw_sha256'].items():
                pin(external, dest / filename, value)
            for filename in ('result.json', 'validation.json', 'reference-result.json', 'abi.json',
                             'image.bin', 'stdout.log', 'stderr.log'):
                pin(external, dest / filename)
    for root in ([campaign] if api else [campaign, norm_reference]):
        for name in ('results.json', 'state.json', 'runtime-inputs.json'):
            pin(external, root / name)
    pins = {}
    for source in (record['source_pins'], norm['source_pins']):
        for rel, value in source.items():
            need(rel not in pins or pins[rel] == value, 'consistent inherited source')
            pins[rel] = value
    for path in (*module_files(), STAGES / 'consumer/api_main.c',
                 *(HERE / name for name in ('build.py', 'run.py', 'api.py', 'CONTRACT.md'))):
        rel, value = str(path.relative_to(REPO)), digest(path)
        need(rel not in pins or pins[rel] == value, 'no source rebinding')
        pins[rel] = value
    for rel, value in pins.items():
        need(digest(REPO / rel) == value, 'current exact source: ' + rel)
    output.mkdir(parents=True)
    state = dict(contract=contract, status='BUILDING', started=base.f.h.now(),
                 cpu_affinity=sorted(os.sched_getaffinity(0)))
    save(output / 'state.json', state)
    try:
        source, fixture = output / 'source', output / 'fixture'
        source.mkdir(); fixture.mkdir()
        for rel, value in pins.items():
            dest = source / 'repo' / rel; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / rel, dest)
            need(digest(dest) == value, 'exact source snapshot')
        for name, value in record['actual_source_pins'].items():
            dest = source / name; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(parent / 'source' / name, dest)
            need(digest(dest) == value, 'exact inherited compiled source')
        for name, value in record['fixtures'].items():
            shutil.copyfile(parent / 'fixture' / name, fixture / name)
            need(digest(fixture / name) == value, 'complete unchanged fixture')
        tools = read(parent / 'tools.json'); save(output / 'tools.json', tools)
        for tool in tools.values():
            need(digest(tool['path']) == tool['sha256'], 'fixed tool binary')
        keys = ('CFLAGS', 'CPPFLAGS', 'CXXFLAGS', 'ASFLAGS', 'LDFLAGS', 'CC_OPT', 'MAKEFLAGS', 'MFLAGS',
                'CC', 'AS', 'LD', 'OBJCOPY', 'OBJDUMP', 'ARCH', 'MARCH', 'LIBS', 'PREBUILD')
        clean = ['env', *[value for key in keys for value in ('-u', key)],
                 'AM_HOME=' + str(am), 'LINUX_GNU_TOOLCHAIN=1']
        if api:
            shutil.copyfile(parent / CORE, source / CORE)
            shutil.copyfile(parent / CORE, output / CORE)
            main, proof = a.derive_main((STAGES / 'consumer/api_main.c').read_bytes())
            (source / 'main.c').write_text(main)
            proof.update(qualified_consumer_object_sha256=record['artifacts'][CORE], core_recompiled=False)
            make = (source / 'Makefile').read_text()
            need(make.count('NAME = ' + PREFIX) == 1, 'qualified norm makefile')
            make = make.replace('NAME = ' + PREFIX, 'NAME = ' + prefix)
        else:
            proof = derive(source)
            shutil.copyfile(norm_build / 'source/norm.h', source / 'norm.h')
            for name in NORM_OBJECTS:
                shutil.copyfile(norm_build / name, source / name)
            lines = [line for line in (parent / 'target-build.stdout.log').read_text().splitlines()
                     if line.startswith(tools['gcc']['path'] + ' ') and line.endswith(str(parent / 'source/consumer.c'))]
            need(len(lines) == 1, 'one original full compile command')
            argv = shlex.split(lines[0]); original_argv = list(argv)
            argv = [value.replace(str(parent / 'source'), str(source)) for value in argv]
            old_object = str(parent / 'objects/consumer.o')
            need(argv.count(old_object) == 1, 'one original object destination')
            argv[argv.index(old_object)] = str(output / 'consumer-core.o')
            command([*clean, *argv], output, 'consumer-compile', timeout=300)
            command([tools['ld']['path'], '-r', '--no-relax', '-o', output / CORE,
                     output / 'consumer-core.o', source / 'candidate.o', source / 'norm.o'],
                    output, 'consumer-combine', timeout=60)
            shutil.copyfile(output / CORE, source / CORE)
            proof.update(original_compile_argv=original_argv, derived_compile_argv=argv,
                         frozen_norm_objects=NORM_OBJECTS, combined_object_sha256=digest(output / CORE))
            make = (source / 'Makefile').read_text()
            for before, after in (('NAME = forward-consumer-w2', 'NAME = ' + prefix),
                                  ('SRCS = main.c consumer.c w2.S', 'SRCS = main.c w2.S'),
                                  ('LINK_FILES += $(MATH_ARCHIVE)', 'LINK_FILES += $(CURDIR)/' + CORE + ' $(MATH_ARCHIVE)')):
                need(make.count(before) == 1, 'exact makefile change')
                make = make.replace(before, after)
        need('consumer.c' not in make and CORE in make, 'final harness links the exact combined core')
        (source / 'Makefile').write_text(make)
        proof['parent_qualification_rechecked'] = parent_recheck
        save(output / 'derivation.json', proof)
        asm = ['.section .rodata.fixture,"a"', '.balign 16']
        for label, name in MODELS:
            asm.extend([f'.global fixture_{label}', f'fixture_{label}:', f'.incbin "{fixture / name}"',
                        f'.global fixture_{label}_end', f'fixture_{label}_end:', '.balign 16'])
        (source / 'fixture.S').write_text('\n'.join(asm) + '\n')
        actual = {str(path.relative_to(source)): digest(path) for path in source.rglob('*')
                  if path.is_file() and not path.is_relative_to(source / 'repo')}
        archives = [path for path in external if Path(path).name == 'libm.a']
        need(len(archives) == 1, 'same static libm archive')
        command([*clean, tools['make']['path'], '--trace', '--output-sync=target', '-C', source,
                 'ARCH=riscv64-xs', 'MARCH=rv64gv', 'CROSS_COMPILE=' + tools['gcc']['path'][:-3],
                 'FORWARD_OBJ_ROOT=' + str(output / 'objects'), 'BINARY=' + str(output / prefix),
                 'MATH_ARCHIVE=' + archives[0], 'FULL_ERRNO_OFFSET=' + str(record['tls_errno_offset']),
                 '-o', 'am', '-o', 'klib', '-j1', 'image'], output, 'target-build', timeout=300)
        command([tools['readelf']['path'], '-W', '-h', '-A', '-l', '-s', '-r', output / (prefix + '.elf')], output, 'metadata')
        command([tools['objdump']['path'], '-drwC', output / (prefix + '.elf')], output, 'disassembly')
        command([tools['objdump']['path'], '-drwC', output / CORE], output, 'core-disassembly')
        command([tools['nm']['path'], '-u', output / CORE], output, 'core-undefined')
        dis = (output / 'core-disassembly.stdout.log').read_text()
        need(not any(value in dis for value in ('rdcycle', 'rdinstret', 'consumer_report', 'consumer_times',
             'consumer_snapshots', 'consumer_control', 'checked_matmul', 'checked_quantize')),
             'pure core has no observer or oracle dependency')
        need(not list((output / 'objects').rglob('consumer*.o')) and digest(source / CORE) == digest(output / CORE),
             'same combined core is linked, never rebuilt by the harness')
        elf, inspection, norm_identity = inspect(output, prefix, record, norm_build)
        identity = dict(functions=record['kernel_identity']['functions'], whole_function_bytes_equal=True,
                        consumer_object_sha256=digest(output / CORE), pure_object_has_no_observer_dependency=True,
                        norm=norm_identity, frozen_norm_objects=NORM_OBJECTS)
        save(output / 'kernel-identity.json', identity)
        image = (output / (prefix + '.bin')).read_bytes(); plans = []
        observed = [('api_report', 'report.bin', 512), ('api_states', 'states.bin', 2 * (S + 32)),
                    ('api_snapshots', 'snapshots.bin', 12 * S)] if api else [
                    ('consumer_report', 'report.bin', 512), ('consumer_snapshots', 'snapshots.bin', 6 * S),
                    ('consumer_state', 'live-state.bin', S), ('consumer_flags', 'flags.bin', 2048),
                    ('consumer_times', 'times.bin', 8192)]
        for symbol, name, size in observed:
            address, length, *_ = elf.symbols[symbol]
            need(length == size and image[address - 0x80000000:address - 0x80000000 + size] == bytes(size),
                 'complete zero-initialized observation storage')
            plans.append((name, address, size))
        for label, name in MODELS:
            address = elf.symbols['fixture_' + label][0]; raw = (fixture / name).read_bytes()
            need(elf.symbols['fixture_' + label + '_end'][0] - address == len(raw) and elf.read(address, len(raw)) == raw,
                 'complete linked model bytes: ' + name)
            plans.append((name.replace('.bin', '-after.bin'), address, len(raw)))
        (output / 'dump-plan.txt').write_text(''.join(f'{name} {address:x} {size}\n' for name, address, size in plans))
        for path, value in external.items():
            need(digest(path) == value, 'external input unchanged after build')
        for rel, value in pins.items():
            need(digest(REPO / rel) == digest(source / 'repo' / rel) == value, 'source unchanged after build')
        for name, value in actual.items():
            need(digest(source / name) == value, 'compiled source unchanged after build')
        for name, value in record['fixtures'].items():
            need(digest(fixture / name) == value, 'fixture unchanged after build')
        for tool in tools.values():
            need(digest(tool['path']) == tool['sha256'], 'tool unchanged after build')
        artifact_names = [prefix + '.elf', prefix + '.bin', CORE, 'dump-plan.txt', 'derivation.json',
                          'kernel-identity.json', 'metadata.stdout.log', 'disassembly.stdout.log']
        if not api:
            artifact_names.append('consumer-core.o')
        inspection.update(contract=contract, status=status, source_pins=pins, external_pins=external,
                          actual_source_pins=actual, fixtures=record['fixtures'], artifacts={name: digest(output / name) for name in artifact_names},
                          kernel_identity=identity, derivation=proof, dump_plan=plans, am_home=str(am), norm_build=str(norm_build),
                          original_w2_build=record['original_w2_build'] if api else str(parent),
                          qualified_build=str(parent), qualified_campaign=str(campaign),
                          qualified_consumer_object_sha256=digest(output / CORE), reference_runs=0,
                          target_emu_runs=0, performance_qualified=False)
        if not api:
            offset = elf.symbols['consumer_control'][0] - 0x80000000
            need(elf.symbols['consumer_control'][1] == 16 and image[offset:offset + 16] == struct.pack('<4I', 4, 3, 0, 1),
                 'same explicit independent data controls')
            inspection.update(control_offset=offset, w2_packed_offset=elf.symbols['fixture_w2_packed'][0] - 0x80000000,
                              norm_reference=str(norm_reference))
        save(output / 'result.json', inspection)
        state.update(status=status, result_sha256=digest(output / 'result.json'))
        return inspection
    except BaseException as error:
        state.update(status='FAILED', error=repr(error)); raise
    finally:
        state['finished'] = base.f.h.now(); save(output / 'state.json', state)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('norm consumer build signal')))
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'parent', 'campaign', 'norm-build', 'norm-reference'):
        parser.add_argument('--' + name, type=Path, required=name in ('output', 'parent', 'campaign'))
    parser.add_argument('--api', action='store_true')
    args = parser.parse_args()
    need(args.api or args.norm_build is not None and args.norm_reference is not None, 'norm parent and reference required')
    os.sched_setaffinity(0, [min(os.sched_getaffinity(0))])
    result = build(args.output.resolve(), args.parent.resolve(),
                   args.norm_build.resolve() if args.norm_build else None, args.campaign.resolve(),
                   args.norm_reference.resolve() if args.norm_reference else None, args.api)
    print(json.dumps({key: result[key] for key in ('contract', 'status', 'image_bytes', 'performance_qualified')}, indent=2))
