"""Build one separate GS32 consumer from existing frozen norm/W2 artifacts.

No checkout is created and no official input is rebuilt. The numerical support
is loaded from the already archived reference campaign's runtime-source tree,
so a later fast-forward of the development checkout cannot change its meaning.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import signal
import struct
import subprocess
import sys

import derive

HERE = Path(__file__).resolve().parent
CONTRACT = derive.CONTRACT
PREFIX = 'forward-consumer-gs32'
CORE = 'consumer-w2-gs32.o'
STATIC = 'GS32_CONSUMER_STATIC_PASS_NOT_RUNTIME'
PARENT_PIN = '8ad05a4aa3bee2bd23d14f698c43ebfa445703aa19e2f2951d079b655d76482d'
SCREEN_ELF = '8316e32939385653c1c4f7e257443529c19dc71df8b5991552a2ab1453069daa'
SCREEN_ASM = '4320150dc48884201f836bd516c11d7b44dfd9fc287999978828d4bd68d193e2'
STAGES = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages')
need = derive.need


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def pin(files, path, expected=None):
    path = Path(path).resolve()
    actual = digest(path)
    expected = actual if expected is None else expected
    need(actual == expected and files.get(str(path), expected) == expected,
         'fixed input identity: ' + str(path))
    files[str(path)] = expected


def verify(files):
    for path, expected in files.items():
        need(digest(path) == expected, 'input unchanged: ' + path)


def support(campaign, snapshot=None):
    """Import only byte-identified modules from an existing runtime snapshot."""
    snapshot = campaign / 'runtime-source' if snapshot is None else snapshot
    manifest = read(campaign / 'runtime-inputs.json')
    relative = STAGES / 'norm/consumer/run.py'
    suffix = '/checkout/source/' + relative.as_posix()
    matches = [path for path in manifest if path.endswith(suffix)]
    need(len(matches) == 1, 'one actual parent runtime source origin')
    origin = Path(matches[0]).parents[len(relative.parts) - 1]
    files = {}
    pin(files, campaign / 'runtime-inputs.json')
    if snapshot != campaign / 'runtime-source':
        closure = read(snapshot / 'support-identity.json')
        need(closure['status'] == 'GS32_REFERENCE_SUPPORT_SNAPSHOT_COMPLETE'
             and closure['parent_campaign'] == str(campaign)
             and closure['parent_manifest_sha256'] == digest(campaign / 'runtime-inputs.json'),
             'explicit complete support snapshot provenance')
        pin(files, snapshot / 'support-identity.json')
        for name, value in closure['files'].items():
            rel_path = Path(name)
            need(not rel_path.is_absolute() and '..' not in rel_path.parts, 'support relative file')
            pin(files, snapshot / rel_path, value)
    pin(files, snapshot / relative, manifest[matches[0]])
    spec = importlib.util.spec_from_file_location('gs32_frozen_consumer_reference', snapshot / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    need(module.b.REPO == snapshot, 'support resolves within the frozen snapshot')
    for path in module.b.module_files():
        rel = path.relative_to(snapshot)
        need(str(origin / rel) in manifest, 'module was consumed by original reference: ' + str(rel))
        pin(files, path, manifest[str(origin / rel)])
    return module, files


def parent_inputs(parent, campaign, r, scalar_view=None):
    files = {}
    pin(files, parent / 'result.json', PARENT_PIN)
    record = read(parent / 'result.json')
    need(record['contract'] == r.b.CONTRACT and record['status'] == r.b.STATIC,
         'exact actual norm/W2 parent')
    original_runtime = read(campaign / 'runtime-inputs.json')
    for group, folder in (('actual_source_pins', parent / 'source'),
                          ('fixtures', parent / 'fixture'), ('artifacts', parent)):
        for name, value in record[group].items():
            pin(files, folder / name, value)
            need(original_runtime[str(folder / name)] == value, 'parent campaign consumed exact ' + name)
    for name in ('result.json', 'tools.json', 'derivation.json'):
        pin(files, parent / name)
    qualified, state = read(campaign / 'results.json'), read(campaign / 'state.json')
    need(qualified['status'] == state['status'] == r.b.PASS and state['reference_runs'] == 8
         and not state['active'] and not state['cleanup_unknown'], 'completed original eight-case campaign')
    for name in ('state.json', 'results.json'):
        pin(files, campaign / name)
    scalar = campaign / 'scalar' if scalar_view is None else scalar_view
    if scalar_view is not None:
        restoration = read(scalar / 'restoration.json')
        need(restoration['status'] == 'GS32_ORIGINAL_SCALAR_SUBSET_RESTORED'
             and restoration['original_scalar'] == str(campaign / 'scalar')
             and restoration['archive_sha256'] == 'c10b8332590abeb7c2597e6cd051b81ba86b1de5b9b3070bbebeec3ca0b588c2'
             and restoration['manifest_sha256'] == 'a72b1088cd52787fcba5cae1295fff2bace87c0f3a0f68fe897a60f08a7a9641',
             'explicit byte-restored original scalar view')
        pin(files, restoration['archive'], restoration['archive_sha256'])
        pin(files, restoration['archiver'], restoration['archiver_sha256'])
        pin(files, scalar / 'restoration.json')
        for name, item in restoration['files'].items():
            pin(files, scalar / name, item['sha256'])
    receipt = read(scalar / 'result.json')
    actual = r.validate(parent, scalar, 0, False, receipt)
    need(actual == read(scalar / 'validation.json') == qualified['validations']['scalar'],
         'fresh audit of original scalar raw state/flags/process')
    need(receipt['validation_sha256'] == digest(scalar / 'validation.json')
         and actual['flags'] == [1, 1, 1], 'actual original scalar flag identity')
    for path in scalar.iterdir():
        if path.is_file():
            pin(files, path)
    r.b.inspect(parent, r.b.PREFIX, record, Path(record['norm_build']))
    return record, files, actual


def calls(disassembly):
    return [(int(m[1], 16), m[2]) for m in re.finditer(
        r'\b([0-9a-f]+):\s+R_RISCV_CALL(?:_PLT)?\s+([^\s+]+)', disassembly)]


def inspect(output, record, r, screen):
    b = r.b
    elf, details = b.base.f.executable(output / (PREFIX + '.elf'), output / (PREFIX + '.bin'),
                                      output / 'metadata.stdout.log', record['tls_errno_offset'])
    functions = b.base.p.kernel_bytes(output / (PREFIX + '.elf'), record['kernel_identity']['functions'])
    for name, raw in functions.items():
        expected = record['kernel_identity']['functions'][name]
        need(len(raw) == expected['bytes'] and derive.sha(raw) == expected['sha256'],
             'complete preserved assembly function: ' + name)
    screened = b.base.f.g.ELF((screen / 'gs32.elf').read_bytes())
    def body(image, name):
        pc, size, *_ = image.symbols[name]
        return image.read(pc, size)
    gs32 = body(elf, 'q288_gs32_rvv')
    need(gs32 == body(screened, 'q288_gs32_rvv'), 'complete GS32 body equals qualified v2')
    norm, _ = b.n.executable(Path(record['norm_build']) / 'real-norm.elf',
                            Path(record['norm_build']) / 'real-norm.bin')
    norm_identity = b.norm_link_identity(elf, norm)
    dis = (output / 'disassembly.stdout.log').read_text()
    targets = calls(dis)
    norm_calls = [(pc, name) for pc, name in targets if name == 'r2_rmsnorm_rvv']
    routes = {}
    for name in ('consumer_fr', 'consumer_ta', 'consumer_fr_cache', 'consumer_ta_cache', 'consumer_gs32_cache'):
        pc, size, *_ = elf.symbols[name]
        routes[name] = sum(pc <= address < pc + size for address, _ in norm_calls)
        need(routes[name] == 3, 'three unchanged norm call sites: ' + name)
    need(len(norm_calls) == 15, 'only five optimized consumers call norm candidate')
    begin = elf.symbols['gs32_forward_call_begin'][0]
    end = elf.symbols['gs32_forward_call_end'][0]
    observed = [(pc, name) for pc, name in targets if begin <= pc < end]
    need(len(observed) == 1 and observed[0][1] == derive.ENTRY, 'actual measured call uses separate public entry')
    pc, size, *_ = elf.symbols[derive.ENTRY]
    direct = [(p, n) for p, n in targets if pc <= p < pc + size and n == 'consumer_gs32_cache']
    need(len(direct) == 1, 'actual separate entry calls only new cached consumer')
    norm_identity.update(static_route_calls=routes, total_static_route_calls=15,
                         dynamic_call_count_claimed=False)
    identity = dict(preserved_functions=record['kernel_identity']['functions'],
        gs32=dict(bytes=len(gs32), sha256=derive.sha(gs32), screened_elf_sha256=SCREEN_ELF),
        norm=norm_identity, direct_entry_call=dict(begin=hex(begin), end=hex(end),
            pc=hex(observed[0][0]), target=observed[0][1]),
        new_consumer_call_pc=hex(direct[0][0]), route_disassembly_sha256=digest(output / 'disassembly.stdout.log'))
    return elf, details, identity


def build(parent, campaign, screen, output, scalar_view=None):
    need(len(os.sched_getaffinity(0)) == 1, 'one coordinated build CPU')
    r, inputs = support(campaign)
    b = r.b
    record, inherited, scalar = parent_inputs(parent, campaign, r, scalar_view)
    inputs.update(inherited)
    for path in (screen / 'gs32.elf', screen / 'source/gs32.S', screen / 'numeric-01/result.json'):
        pin(inputs, path)
    need(digest(screen / 'gs32.elf') == SCREEN_ELF and digest(screen / 'source/gs32.S') == SCREEN_ASM,
         'fixed screened v2 ELF and actual assembly')
    numeric = read(screen / 'numeric-01/result.json')
    need(numeric['status'] == 'GS32_ACTUAL_ELF_NUMERIC_PASS' and numeric['elf_sha256'] == SCREEN_ELF,
         'screen report binds the actual selected function')
    am = Path(record['am_home'])
    need(not output.exists() and not any(output.is_relative_to(p) for p in
         (parent, campaign, screen, am, HERE)), 'fresh output outside fixed inputs')
    need(subprocess.check_output(['git', '-C', am, 'rev-parse', 'HEAD'], text=True).strip() ==
         '086a238062fdfb3281b745a537b361983d0154b5', 'fixed official AM revision')
    need(not subprocess.check_output(['git', '-C', am, 'status', '--porcelain', '--untracked-files=no'],
                                     text=True).strip(), 'official AM remains unchanged')
    tools = read(parent / 'tools.json')
    for tool in tools.values():
        pin(inputs, tool['path'], tool['sha256'])
    archives = [p for p in record['external_pins'] if Path(p).name == 'libm.a']
    need(len(archives) == 1, 'one original libm archive')
    # These are actual compiler/official library inputs, not unused raw results
    # of every earlier campaign. Parent raw scalar evidence is pinned above.
    for path, value in record['external_pins'].items():
        p = Path(path)
        if p.is_relative_to(am) or p.is_relative_to(Path('/usr')) or path == archives[0]:
            pin(inputs, p, value)
    for name in ('build.py', 'run.py', 'derive.py', 'consumer_gs32.h', 'CONTRACT.md'):
        pin(inputs, HERE / name)
    output.mkdir(parents=True)
    state = dict(contract=CONTRACT, status='BUILDING', started=b.base.f.h.now(),
                 cpu_affinity=sorted(os.sched_getaffinity(0)), target_emu_runs=0)
    save(output / 'state.json', state)
    save(output / 'inputs.json', inputs)
    try:
        source, fixture = output / 'source', output / 'fixture'
        source.mkdir(); fixture.mkdir(); (output / 'controller').mkdir()
        for name in ('build.py', 'run.py', 'derive.py', 'consumer_gs32.h', 'CONTRACT.md'):
            shutil.copyfile(HERE / name, output / 'controller' / name)
        for name, value in record['actual_source_pins'].items():
            dest = source / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(parent / 'source' / name, dest)
            need(digest(dest) == value, 'unchanged inherited compile input: ' + name)
        for name, value in record['fixtures'].items():
            shutil.copyfile(parent / 'fixture' / name, fixture / name)
            need(digest(fixture / name) == value, 'unchanged independent fixture: ' + name)
        shutil.copyfile(HERE / 'consumer_gs32.h', source / 'consumer_gs32.h')
        proof = derive.derive(source)
        raw = (screen / 'source/gs32.S').read_text()
        begin = '.balign 64\n.global q288_gs32_rvv\n'
        need(raw.count(begin) == 1, 'one complete candidate assembly entry')
        assembly = '.option norvc\n.option norelax\n.text\n' + raw[raw.index(begin):]
        need('q288_fused_rvv4' not in assembly, 'only GS32 added, no duplicate original FR')
        (source / 'gs32.S').write_text(assembly)
        old_argv = read(parent / 'derivation.json')['derived_compile_argv']
        argv = [value.replace(str(parent / 'source'), str(source)) for value in old_argv]
        need(argv.count(str(parent / 'consumer-core.o')) == 1, 'exact parent compile object destination')
        argv[argv.index(str(parent / 'consumer-core.o'))] = str(output / 'consumer-core.o')
        keys = ('CFLAGS', 'CPPFLAGS', 'CXXFLAGS', 'ASFLAGS', 'LDFLAGS', 'CC_OPT', 'MAKEFLAGS', 'MFLAGS',
                'CC', 'AS', 'LD', 'OBJCOPY', 'OBJDUMP', 'ARCH', 'MARCH', 'LIBS', 'PREBUILD')
        clean = ['env', *[v for k in keys for v in ('-u', k)], 'AM_HOME=' + str(am), 'LINUX_GNU_TOOLCHAIN=1']
        b.command([*clean, *argv], output, 'consumer-compile', timeout=300)
        b.command([tools['gcc']['path'], '-march=rv64gv', '-mabi=lp64d', '-mno-relax', '-c',
                   str(source / 'gs32.S'), '-o', str(output / 'gs32.o')], output, 'gs32-compile', timeout=60)
        b.command([tools['ld']['path'], '-r', '--no-relax', '-o', output / CORE,
                   output / 'consumer-core.o', source / 'candidate.o', source / 'norm.o', output / 'gs32.o'],
                  output, 'consumer-combine', timeout=60)
        shutil.copyfile(output / CORE, source / CORE)
        make = (source / 'Makefile').read_text()
        for before, after in (('NAME = ' + b.PREFIX, 'NAME = ' + PREFIX), (b.CORE, CORE)):
            make = derive.replace_once(make, before, after)
        need('consumer.c' not in make and make.count(CORE) == 1, 'harness links only the new combined object')
        (source / 'Makefile').write_text(make)
        fixture_asm = ['.section .rodata.fixture,"a"', '.balign 16']
        for label, name in b.MODELS:
            fixture_asm += [f'.global fixture_{label}', f'fixture_{label}:', f'.incbin "{fixture / name}"',
                            f'.global fixture_{label}_end', f'fixture_{label}_end:', '.balign 16']
        (source / 'fixture.S').write_text('\n'.join(fixture_asm) + '\n')
        actual = {str(p.relative_to(source)): digest(p) for p in source.rglob('*') if p.is_file()}
        save(output / 'tools.json', tools)
        b.command([*clean, tools['make']['path'], '--trace', '--output-sync=target', '-C', source,
            'ARCH=riscv64-xs', 'MARCH=rv64gv', 'CROSS_COMPILE=' + tools['gcc']['path'][:-3],
            'FORWARD_OBJ_ROOT=' + str(output / 'objects'), 'BINARY=' + str(output / PREFIX),
            'MATH_ARCHIVE=' + archives[0], 'FULL_ERRNO_OFFSET=' + str(record['tls_errno_offset']),
            '-o', 'am', '-o', 'klib', '-j1', 'image'], output, 'target-build', timeout=300)
        for label, args in (('metadata', [tools['readelf']['path'], '-W', '-h', '-A', '-l', '-s', '-r', output / (PREFIX + '.elf')]),
                            ('disassembly', [tools['objdump']['path'], '-drwC', output / (PREFIX + '.elf')]),
                            ('core-disassembly', [tools['objdump']['path'], '-drwC', output / CORE]),
                            ('core-undefined', [tools['nm']['path'], '-u', output / CORE])):
            b.command(args, output, label)
        core_dis = (output / 'core-disassembly.stdout.log').read_text()
        need(not any(value in core_dis for value in ('rdcycle', 'rdinstret', 'consumer_report',
             'consumer_times', 'consumer_snapshots', 'consumer_control', 'checked_matmul', 'checked_quantize')),
             'pure combined consumer has no observer or oracle dependency')
        need(not list((output / 'objects').rglob('consumer*.o')) and digest(source / CORE) == digest(output / CORE),
             'the exact new combined core is linked, never silently rebuilt')
        elf, details, identity = inspect(output, record, r, screen)
        plans = []
        image = (output / (PREFIX + '.bin')).read_bytes()
        for symbol, name, size in (('consumer_report', 'report.bin', 512),
            ('consumer_snapshots', 'snapshots.bin', 6 * b.S), ('consumer_state', 'live-state.bin', b.S),
            ('consumer_flags', 'flags.bin', 2048), ('consumer_times', 'times.bin', 8192)):
            address, length, *_ = elf.symbols[symbol]
            need(length == size and image[address - 0x80000000:address - 0x80000000 + size] == bytes(size),
                 'complete actual zero observation state: ' + symbol)
            plans.append((name, address, size))
        for label, name in b.MODELS:
            address = elf.symbols['fixture_' + label][0]
            data = (fixture / name).read_bytes()
            need(elf.symbols['fixture_' + label + '_end'][0] - address == len(data)
                 and elf.read(address, len(data)) == data, 'actual entire linked model: ' + name)
            plans.append((name.replace('.bin', '-after.bin'), address, len(data)))
        (output / 'dump-plan.txt').write_text(''.join(f'{name} {address:x} {size}\n' for name, address, size in plans))
        control = elf.symbols['consumer_control'][0] - 0x80000000
        need(elf.symbols['consumer_control'][1] == 16 and image[control:control + 16] ==
             struct.pack('<4I', derive.ENTRY_TAG, 3, 0, 1), 'independent entry tag, never old method 5')
        proof.update(original_compile_argv=old_argv, derived_compile_argv=argv,
                     combined_object_sha256=digest(output / CORE), frozen_norm_objects=b.NORM_OBJECTS)
        save(output / 'derivation.json', proof); save(output / 'kernel-identity.json', identity)
        save(output / 'parent-scalar-reaudit.json', scalar)
        names = [PREFIX + '.elf', PREFIX + '.bin', CORE, 'consumer-core.o', 'gs32.o', 'dump-plan.txt',
                 'derivation.json', 'kernel-identity.json', 'parent-scalar-reaudit.json',
                 'metadata.stdout.log', 'disassembly.stdout.log', 'core-disassembly.stdout.log']
        verify(inputs)
        for name, value in actual.items():
            need(digest(source / name) == value, 'generated compile input unchanged: ' + name)
        details.update(contract=CONTRACT, status=STATIC, entry=derive.ENTRY, entry_tag=derive.ENTRY_TAG,
            parent_build=str(parent), parent_campaign=str(campaign), support_snapshot=str(b.REPO),
            screen=str(screen), am_home=str(am), artifacts={name: digest(output / name) for name in names},
            actual_source_pins=actual, fixtures=record['fixtures'], kernel_identity=identity, derivation=proof,
            control_offset=control, w2_packed_offset=elf.symbols['fixture_w2_packed'][0] - 0x80000000,
            scalar_flags=scalar['flags'], dump_plan=plans, inputs_sha256=digest(output / 'inputs.json'),
            static_route_disassembly_review_required=True, reference_runs=0, target_emu_runs=0,
            performance_qualified=False, stable_default_changed=False)
        save(output / 'result.json', details)
        state.update(status=STATIC, result_sha256=digest(output / 'result.json'))
        return details
    except BaseException as error:
        state.update(status='FAILED', error=repr(error))
        raise
    finally:
        state['finished'] = b.base.f.h.now(); save(output / 'state.json', state)


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('GS32 consumer build')))
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('parent', 'campaign', 'screen', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--scalar-view', type=Path)
    args = parser.parse_args()
    result = build(*(getattr(args, name).resolve() for name in ('parent', 'campaign', 'screen', 'output')),
                   args.scalar_view.resolve() if args.scalar_view else None)
    print(json.dumps({key: result[key] for key in ('contract', 'status', 'image_bytes', 'performance_qualified')}), flush=True)
