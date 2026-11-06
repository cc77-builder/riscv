"""Build a common FR/GS32/paired16 core and the guarded first-forward wrapper.

Run from a new controller produced by bind.py. Existing team helpers perform
the compiler, ELF/TLS, norm and original scalar checks; official inputs are not
edited or rebuilt. This module also supplies the narrow reference binding.
"""
from pathlib import Path
from contextlib import contextmanager
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
import types

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


derive = load('first_forward_derivation', HERE / 'derive.py')
need = derive.need
CONTRACT = derive.CONTRACT
PREFIX = 'first-forward-rvv'
CORE = 'consumer-first-forward-rvv.o'
STATIC = 'FIRST_FORWARD_RVV_STATIC_PASS_NOT_RUNTIME'
REFERENCE_PASS = 'FIRST_FORWARD_RVV_REFERENCE_CAMPAIGN_PASS'
MAGIC = derive.MAGIC
GUARD = 0xb5e9c13f6a0742d8
METHODS = derive.METHODS
STAGES = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages')
REFERENCE_SHA = '8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9'
KERNELS = {
    'q288_gs32_rvv': dict(bytes=420, sha256='2d95481faa1c79f7a8a06ef65fc02154e30cf731e6ba5c990a7209c2e90c32ab'),
    'q288_paired16_rvv': dict(bytes=1096, sha256='a06e377e88a230929cc971acf91b0adf3ac27e52fd17ec72956ae7890ed7e73c'),
}


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


BINDING = read(HERE / 'binding.json')
CFG = BINDING['config']
need(BINDING['contract'] == CONTRACT and BINDING['status'] == 'FIRST_FORWARD_RVV_CONTROLLER_BOUND_NOT_RUNTIME',
     'new explicit controller binding')
for path, value in BINDING['input_files'].items():
    need(digest(path) == value, 'fixed controller input: ' + path)
for name, value in BINDING['generated_files'].items():
    need(digest(HERE / name) == value, 'fixed generated controller: ' + name)
old_derive = sys.modules.get('derive')
try:
    sys.modules['derive'] = load('first_forward_gs32_support_derive', Path(CFG['gs32_controller']) / 'derive.py')
    g = load('first_forward_gs32_support_build', Path(CFG['gs32_controller']) / 'build.py')
finally:
    if old_derive is None:
        sys.modules.pop('derive', None)
    else:
        sys.modules['derive'] = old_derive
cr, SUPPORT_FILES = g.support(Path(CFG['parent_campaign']), Path(CFG['support_snapshot']))
c = cr.b
S = c.S
REPO = Path(CFG['repository'])
TOOL_REPO = HERE / 'target-support'
aux = load('first_forward_uart_support', TOOL_REPO / STAGES / 'consumer/aux_build.py')
norm_target = load('first_forward_old_target_support', TOOL_REPO / STAGES / 'norm/target/build.py')
command, pin, verify = c.command, g.pin, g.verify


def modules(*roots):
    pending, seen, paths = list(roots), set(), set()
    while pending:
        item = pending.pop()
        if not isinstance(item, types.ModuleType) or id(item) in seen:
            continue
        seen.add(id(item))
        pending.extend(v for v in vars(item).values() if isinstance(v, types.ModuleType))
        path = getattr(item, '__file__', None)
        if path:
            p = Path(path).resolve()
            if p.is_file() and (p.is_relative_to(REPO) or p.is_relative_to(TOOL_REPO) or p.is_relative_to(Path(CFG['support_snapshot']))):
                paths.add(p)
    return sorted(paths)


@contextmanager
def support_git_metadata():
    """Use the existing frozen helper root and its recorded read-only Git data.

    This is the same source-only snapshot binding used by the qualified GS32
    reference controller. The original root/source/Git-object checks still run.
    """
    snapshot = Path(CFG['support_snapshot'])
    need(c.REPO == snapshot, 'original helper belongs to the declared snapshot')
    closure = read(snapshot / 'support-identity.json')
    saved = {name: os.environ.get(name) for name in ('GIT_DIR', 'GIT_WORK_TREE')}
    try:
        os.environ['GIT_DIR'] = closure['git_metadata_dir']
        os.environ.pop('GIT_WORK_TREE', None)
        yield
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def physical_identity(identity_path, physical=False):
    with support_git_metadata():
        value = cr.old.r.parent.parent_identity(c.REPO, identity_path, physical=False)
    if not physical:
        return value
    # The original hardware checker uses git -C against the hardware and NEMU
    # checkouts. A software-snapshot GIT_DIR must never override those roots.
    need(not any(os.environ.get(name) for name in ('GIT_DIR', 'GIT_WORK_TREE')),
         'physical checkout checks require their own Git discovery')
    p = cr.old.r.parent.t17.p
    files, profile = p.hardware_profile(TOOL_REPO, value['configuration'])
    need(profile == value['hardware_profile'], 'physical T17 hardware profile drift')
    need({name: files[str(Path(value['configuration']['build_record']) / name)] for name in p.META_NAMES}
         == value['metadata_sha256'], 'physical T17 build metadata drift')
    return value, files, profile


def runtime_identity(identity):
    with support_git_metadata():
        return cr.old.r.parent.runtime(c.REPO, identity)


def body(elf, name):
    address, size, *_ = elf.symbols[name]
    return elf.read(address, size)


def signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def branch_target(pc, word):
    offset = ((word >> 31) << 12) | (((word >> 7) & 1) << 11)
    offset |= ((word >> 25) & 63) << 5 | ((word >> 8) & 15) << 1
    return pc + signed(offset, 13)


def jump_target(pc, word):
    offset = ((word >> 31) << 20) | (((word >> 12) & 255) << 12)
    offset |= ((word >> 20) & 1) << 11 | ((word >> 21) & 1023) << 1
    return pc + signed(offset, 21)


def routing(elf, dis):
    """Bounded actual-machine-word pointer review; not whole-program execution."""
    word = lambda pc: struct.unpack('<I', elf.read(pc, 4))[0]
    def pair(pc, reg, operation=0x13):
        a, b = word(pc), word(pc + 4)
        if a & 0xfff != ((reg << 7) | 0x17) or b & 0xfffff != ((reg << 15) | (reg << 7) | operation):
            return None
        return (pc + signed(a & 0xfffff000, 32) + signed(b >> 20, 12)) & ((1 << 64) - 1)
    def evidence(pcs):
        return [dict(pc=hex(pc), bytes=elf.read(pc, 4).hex()) for pc in pcs]
    all_calls = g.calls(dis)
    reviewed = {}
    for name, kernel in (('consumer_fr_cache', 'q288_fused_rvv4'),
                         ('consumer_gs32_cache', 'q288_gs32_rvv'),
                         ('consumer_paired16_cache', 'q288_paired16_rvv')):
        start, size, *_ = elf.symbols[name]
        words = {pc: word(pc) for pc in range(start, start + size, 4)}
        need(all(value & 3 == 3 for value in words.values()), 'whole 32-bit consumer stream')
        calls = [pc for pc, target in all_calls if start <= pc < start + size and target == 'route_matmul']
        need(len(calls) == 8, 'all eight route calls: ' + name)
        targets = [branch_target(pc, value) if value & 127 == 0x63 else jump_target(pc, value)
                   for pc, value in words.items() if value & 127 in (0x63, 0x6f)]
        rows = []
        expected = [kernel] * 6 + ['q288_fused_rvv4', kernel]
        for label, call, wanted in zip(('Q', 'K', 'V', 'Wo', 'W1', 'W3', 'W2', 'classifier'), calls, expected):
            candidates = [pc for pc in range(max(start, call - 64), call - 4, 4)
                          if pair(pc, 15) == elf.symbols[wanted][0]]
            need(candidates, 'actual a5 pointer preparation: ' + name + '/' + label)
            setup = candidates[-1]
            need(pair(call, 1, 0x67) == elf.symbols['route_matmul'][0], 'actual route call destination')
            need(not any(setup < pc <= call + 4 for pc in targets), 'no branch into pointer setup interior')
            for pc in range(setup + 8, call, 4):
                value = word(pc)
                opcode = value & 127
                need(opcode not in (0x63, 0x6f, 0x67) and
                     (opcode in (0x23, 0x27) or (value >> 7) & 31 != 15), 'unmodified straight-line a5')
            rows.append(dict(site=label, pc=hex(call), jalr_pc=hex(call + 4), kernel=wanted,
                kernel_address=hex(elf.symbols[wanted][0]), instruction_evidence=evidence(range(setup, call + 8, 4))))
        reviewed[name] = rows
    start, size, *_ = elf.symbols['route_matmul']
    selectors = []
    for pc in range(start, start + size - 32, 4):
        if (pair(pc, 14) == elf.symbols['q288_fused_rvv4'][0] and
                pair(pc + 8, 15) == elf.symbols['q768_fr'][0] and
                pair(pc + 20, 15) == elf.symbols['q768_ta'][0]):
            need(word(pc + 16) & 0x01fff07f == ((14 << 20) | (20 << 15) | 0x63) and
                 branch_target(pc + 16, word(pc + 16)) == pc + 28,
                 'FR equality skips the alternative W2 pointer load')
            need(word(pc + 32) == 0x000780e7, 'selected W2 pointer actually called')
            selectors.append(evidence(range(pc, pc + 36, 4)))
    need(len(selectors) == 1, 'one actual unchanged W2 FR selector')
    begin, end = (elf.symbols[name][0] for name in ('first_forward_call_begin', 'first_forward_call_end'))
    measured = [(pc, name) for pc, name in all_calls if begin <= pc < end]
    need(len(measured) == 1 and measured[0][1] == 'first_forward_dispatch', 'one common measured dispatch call')
    dispatcher, dispatcher_size, *_ = elf.symbols['first_forward_dispatch']
    dispatch_calls = [(pc, name) for pc, name in all_calls if dispatcher <= pc < dispatcher + dispatcher_size
                      and name in ('r2_w2_forward', 'r2_w2_gs32_forward', 'r2_w2_paired16_forward')]
    need(sorted(name for _, name in dispatch_calls) == ['r2_w2_forward', 'r2_w2_gs32_forward', 'r2_w2_paired16_forward'],
         'three real existing public entries in the dispatcher')
    for name in ('gs32', 'paired16'):
        pc, count, *_ = elf.symbols[f'r2_w2_{name}_forward']
        hits = [(p, n) for p, n in all_calls if pc <= p < pc + count and n == f'consumer_{name}_cache']
        need(len(hits) == 1, 'new public entry reaches its own clone')
    return dict(status='FIRST_FORWARD_RVV_STATIC_ROUTES_CHECKED', route_calls=reviewed,
        w2_fr_selector=selectors[0], measured_call=dict(begin=hex(begin), end=hex(end), pc=hex(measured[0][0])),
        dispatcher=dict(address=hex(dispatcher), bytes=dispatcher_size, sha256=derive.sha(body(elf, 'first_forward_dispatch')),
                        calls=[dict(pc=hex(pc), target=name) for pc, name in dispatch_calls]),
        scope='bounded final-ELF pointer/call check; source reversal and reference runs are separate evidence',
        dynamic_call_count_claimed=False)


def inspect(output, record):
    elf, result = aux.uart_executable(output / (PREFIX + '.elf'), output / (PREFIX + '.bin'),
                                    output / 'metadata.stdout.log', record['tls_errno_offset'])
    for name, expected in record['kernel_identity']['functions'].items():
        raw = body(elf, name)
        need(len(raw) == expected['bytes'] and derive.sha(raw) == expected['sha256'], 'complete fixed kernel: ' + name)
    old_norm, _ = c.n.executable(Path(record['norm_build']) / 'real-norm.elf', Path(record['norm_build']) / 'real-norm.bin')
    result['norm_identity'] = c.norm_link_identity(elf, old_norm)
    result.update(norm_target.traps(elf))
    dis = (output / 'disassembly.stdout.log').read_text()
    result['routing_identity'] = routing(elf, dis)
    norm_calls = [(pc, name) for pc, name in g.calls(dis) if name == 'r2_rmsnorm_rvv']
    for name in ('consumer_fr', 'consumer_ta', 'consumer_fr_cache', 'consumer_ta_cache',
                 'consumer_gs32_cache', 'consumer_paired16_cache'):
        pc, size, *_ = elf.symbols[name]
        need(sum(pc <= call < pc + size for call, _ in norm_calls) == 3, 'three original norm sites: ' + name)
    need(len(norm_calls) == 18, 'exact six consumer norm route scope')
    result['entry_symbols'] = {name: dict(address=hex(elf.symbols[name][0]), bytes=elf.symbols[name][1], sha256=derive.sha(body(elf, name)))
                              for name in ('r2_w2_forward', 'r2_w2_gs32_forward', 'r2_w2_paired16_forward',
                                           'consumer_fr_cache', 'consumer_gs32_cache', 'consumer_paired16_cache')}
    return elf, result


def inputs(build, adapter, identity_path):
    record = read(build / 'result.json')
    need(record['contract'] == CONTRACT and record['status'] == STATIC, 'new combination static identity')
    need(digest(build / 'inputs.json') == record['inputs_sha256'], 'new exact build input manifest')
    files = dict(SUPPORT_FILES)
    for path, value in read(build / 'inputs.json').items():
        pin(files, path, value)
    for group, folder in (('artifacts', build), ('actual_source_pins', build / 'source'), ('fixtures', build / 'fixture')):
        for name, value in record[group].items():
            pin(files, folder / name, value)
    for path in (build / 'result.json', build / 'inputs.json', build / 'tools.json', identity_path):
        pin(files, path)
    for path in HERE.iterdir():
        if path.is_file():
            pin(files, path)
    for name, value in BINDING['generated_files'].items():
        pin(files, HERE / name, value)
    identity = physical_identity(identity_path)
    pin(files, identity['configuration']['reference'], REFERENCE_SHA)
    need(identity['reference_sha256'] == REFERENCE_SHA, 'unchanged original normal reference')
    adapter_record = read(adapter / 'build.json')
    need(adapter_record['status'] == 'REFERENCE_ADAPTER_BUILD_PASS' and
         adapter_record['inputs_sha256'] == digest(adapter / 'inputs.json'), 'original bounded reference adapter')
    for name, value in adapter_record['artifacts'].items():
        pin(files, adapter / name, value)
    for path, value in read(adapter / 'inputs.json')['files'].items():
        pin(files, path, value)
    for name in ('build.json', 'inputs.json'):
        pin(files, adapter / name)
    need((adapter / 'reference_runner.c').read_bytes() ==
         (c.REPO / STAGES / 'target/reference_runner.c').read_bytes(), 'original adapter source byte identity')
    _, checked = inspect(build, record)
    checked = json.loads(json.dumps(checked))
    need(all(record[key] == value for key, value in checked.items()), 'new complete static reinspection')
    _, checker = runtime_identity(identity)
    checker.verify_files(files)
    return record, files, identity, checker


def build(output):
    need(len(os.sched_getaffinity(0)) == 1 and not output.exists(), 'fresh coordinated single-CPU build')
    parent, campaign = Path(CFG['parent_build']), Path(CFG['parent_campaign'])
    parent_record, inherited, scalar = g.parent_inputs(parent, campaign, cr, Path(CFG['scalar_view']))
    files = dict(SUPPORT_FILES)
    files.update(inherited)
    for path, value in BINDING['input_files'].items():
        pin(files, path, value)
    for name, value in BINDING['generated_files'].items():
        pin(files, HERE / name, value)
    for path in [*modules(cr, aux, norm_target), *HERE.iterdir()]:
        if path.is_file():
            pin(files, path)
    am = Path(parent_record['am_home'])
    need(not any(output.is_relative_to(root) for root in (REPO, parent, campaign, am, HERE,
             Path(CFG['gs32_screen']), Path(CFG['paired16_screen']))), 'isolated output outside every input')
    need(subprocess.check_output(['git', '-C', am, 'rev-parse', 'HEAD'], text=True).strip() ==
         '086a238062fdfb3281b745a537b361983d0154b5' and not
         subprocess.check_output(['git', '-C', am, 'status', '--porcelain', '--untracked-files=no'], text=True).strip(),
         'unchanged official AM revision and sources')
    tools = read(parent / 'tools.json')
    for tool in tools.values():
        pin(files, tool['path'], tool['sha256'])
    archives = [path for path in parent_record['external_pins'] if Path(path).name == 'libm.a']
    need(len(archives) == 1, 'same original static libm')
    for path, value in parent_record['external_pins'].items():
        p = Path(path)
        if p.is_relative_to(am) or p.is_relative_to(Path('/usr')) or path == archives[0]:
            pin(files, p, value)
    screens = {
        'gs32': (Path(CFG['gs32_screen']), 'gs32.elf', 'source/gs32.S', 'numeric-01/result.json',
                 '8316e32939385653c1c4f7e257443529c19dc71df8b5991552a2ab1453069daa',
                 '4320150dc48884201f836bd516c11d7b44dfd9fc287999978828d4bd68d193e2', 'GS32_ACTUAL_ELF_NUMERIC_PASS'),
        'paired16': (Path(CFG['paired16_screen']), 'paired16.elf', 'generated/paired16.S', 'screen/result.json',
                     'fb3c030efa7aa347029a69f6aabe82c912cbbb85294b27cf407a01ea58a314f3',
                     '7b1bf0ba021a69aeab466c8e6bce6a1a88072d40d3f18adfe47555df5dcd3c56', 'PAIRED16_ACTUAL_ELF_NUMERIC_PASS'),
    }
    for name, (root, elf, asm, result, elf_sha, asm_sha, status) in screens.items():
        pin(files, root / elf, elf_sha)
        pin(files, root / asm, asm_sha)
        pin(files, root / result)
        screened = read(root / result)
        need(screened['status'] == status and screened['elf_sha256'] == elf_sha, 'actual screened kernel identity')
    frozen_main = Path(CFG['norm_target_build']) / 'source/main.c'
    pin(files, frozen_main, derive.MAIN_SHA)
    output.mkdir(parents=True)
    state = dict(contract=CONTRACT, status='BUILDING', started=c.base.f.h.now(), cpu_affinity=sorted(os.sched_getaffinity(0)),
                 reference_runs=0, target_emu_runs=0, performance_qualified=False)
    save(output / 'state.json', state)
    save(output / 'inputs.json', files)
    try:
        source, fixture = output / 'source', output / 'fixture'
        source.mkdir(); fixture.mkdir()
        for name, value in parent_record['actual_source_pins'].items():
            dest = source / name; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(parent / 'source' / name, dest)
            need(digest(dest) == value, 'whole inherited input: ' + name)
        for name, value in parent_record['fixtures'].items():
            shutil.copyfile(parent / 'fixture' / name, fixture / name)
            need(digest(fixture / name) == value, 'same whole fixture: ' + name)
        generated, core_proof = derive.core((source / 'consumer.c').read_bytes(), (source / 'consumer.inc').read_bytes())
        for name, raw in generated.items():
            (source / name).write_bytes(raw)
        main, main_proof = derive.main(frozen_main.read_bytes())
        (source / 'main.c').write_bytes(main)
        (source / 'entry.S').write_bytes(derive.entry((source / 'entry.S').read_bytes()))
        for name, (root, _, asm, _, _, _, _) in screens.items():
            raw = (root / asm).read_text()
            begin = f'.balign 64\n.global q288_{name}_rvv\n'
            end = f'.size q288_{name}_rvv, .-q288_{name}_rvv\n'
            need(raw.count(begin) == raw.count(end) == 1 and raw.index(end) > raw.index(begin), 'one complete assembly function')
            fragment = raw[raw.index(begin):raw.index(end) + len(end)]
            if name == 'paired16':
                need(fragment.count('q288_paired16_rvv_fallback_begin:') == fragment.count('q288_paired16_rvv_fallback_end:') == 1,
                     'full P guard and embedded fallback retained')
            (source / (name + '.S')).write_text('.option norvc\n.option norelax\n.text\n' + fragment)
        old_argv = read(parent / 'derivation.json')['derived_compile_argv']
        argv = [value.replace(str(parent / 'source'), str(source)) for value in old_argv]
        need(argv.count(str(parent / 'consumer-core.o')) == 1, 'one parent compilation output')
        argv[argv.index(str(parent / 'consumer-core.o'))] = str(output / 'consumer-core.o')
        keys = ('CFLAGS', 'CPPFLAGS', 'CXXFLAGS', 'ASFLAGS', 'LDFLAGS', 'CC_OPT', 'MAKEFLAGS', 'MFLAGS',
                'CC', 'AS', 'LD', 'OBJCOPY', 'OBJDUMP', 'ARCH', 'MARCH', 'LIBS', 'PREBUILD')
        clean = ['env', *[v for k in keys for v in ('-u', k)], 'AM_HOME=' + str(am), 'LINUX_GNU_TOOLCHAIN=1']
        command([*clean, *argv], output, 'consumer-compile', timeout=300)
        for name in screens:
            command([tools['gcc']['path'], '-march=rv64gv', '-mabi=lp64d', '-mno-relax', '-c', source / (name + '.S'),
                     '-o', output / (name + '.o')], output, name + '-compile', timeout=60)
        command([tools['ld']['path'], '-r', '--no-relax', '-o', output / CORE, output / 'consumer-core.o',
                 source / 'candidate.o', source / 'norm.o', output / 'gs32.o', output / 'paired16.o'],
                output, 'consumer-combine', timeout=60)
        shutil.copyfile(output / CORE, source / CORE)
        make = (source / 'Makefile').read_text()
        for before, after in (('NAME = ' + c.PREFIX, 'NAME = ' + PREFIX), (c.CORE, CORE)):
            need(make.count(before) == 1, 'one inherited Makefile substitution')
            make = make.replace(before, after)
        need('consumer.c' not in make and make.count(CORE) == 1, 'only new combined object is linked')
        (source / 'Makefile').write_text(make)
        embedded = [*c.MODELS, ('gold', 'host-state-p0.bin')]
        assembly = ['.section .rodata.fixture,"a"', '.balign 16']
        for label, name in embedded:
            assembly += [f'.global fixture_{label}', f'fixture_{label}:', f'.incbin "{fixture / name}"',
                         f'.global fixture_{label}_end', f'fixture_{label}_end:', '.balign 16']
        (source / 'fixture.S').write_text('\n'.join(assembly) + '\n')
        actual = {str(path.relative_to(source)): digest(path) for path in source.rglob('*') if path.is_file()}
        save(output / 'tools.json', tools)
        command([*clean, tools['make']['path'], '--trace', '--output-sync=target', '-C', source,
                 'ARCH=riscv64-xs', 'MARCH=rv64gv', 'CROSS_COMPILE=' + tools['gcc']['path'][:-3],
                 'FORWARD_OBJ_ROOT=' + str(output / 'objects'), 'BINARY=' + str(output / PREFIX),
                 'MATH_ARCHIVE=' + archives[0], 'FULL_ERRNO_OFFSET=' + str(parent_record['tls_errno_offset']),
                 '-o', 'am', '-o', 'klib', '-j1', 'image'], output, 'target-build', timeout=300)
        for label, args in (('metadata', [tools['readelf']['path'], '-W', '-h', '-A', '-l', '-s', '-r', output / (PREFIX + '.elf')]),
                            ('disassembly', [tools['objdump']['path'], '-drwC', output / (PREFIX + '.elf')]),
                            ('core-disassembly', [tools['objdump']['path'], '-drwC', output / CORE])):
            command(args, output, label)
        pure_dis = (output / 'core-disassembly.stdout.log').read_text()
        need(not any(value in pure_dis for value in ('rdcycle', 'rdinstret', 'consumer_report', 'consumer_times',
             'consumer_snapshots', 'consumer_control', 'checked_matmul', 'checked_quantize')), 'pure shared core without oracle/timing')
        need(not list((output / 'objects').rglob('consumer*.o')) and digest(source / CORE) == digest(output / CORE),
             'new combined core not silently rebuilt')
        record = dict(parent_record)
        record['kernel_identity'] = dict(functions={**parent_record['kernel_identity']['functions'], **KERNELS})
        elf, details = inspect(output, record)
        for name, (root, old_elf, _, _, _, _, _) in screens.items():
            screened_elf = c.base.f.g.ELF((root / old_elf).read_bytes())
            need(body(elf, f'q288_{name}_rvv') == body(screened_elf, f'q288_{name}_rvv'), 'actual full candidate byte identity')
        image = (output / (PREFIX + '.bin')).read_bytes()
        need(len(image) < 128 * 1024 * 1024, 'whole image fits fixed RAM')
        plans = []
        for symbol, name, size in (('target_report', 'report.bin', 512), ('target_guarded', 'guarded-state.bin', S + 32),
                                   ('team_tls_area', 'tls.bin', 96)):
            address, length, *_ = elf.symbols[symbol]
            need(length == size and image[address - 0x80000000:address - 0x80000000 + size] == bytes(size), 'whole initial zero storage')
            plans.append((name, address, size))
        for label, name in embedded:
            address = elf.symbols['fixture_' + label][0]; raw = (fixture / name).read_bytes()
            need(elf.symbols['fixture_' + label + '_end'][0] - address == len(raw) and elf.read(address, len(raw)) == raw,
                 'complete linked model or independent golden')
            plans.append(('gold-after.bin' if label == 'gold' else name.replace('.bin', '-after.bin'), address, len(raw)))
        address, length, *_ = elf.symbols['target_control']; offset = address - 0x80000000
        need(length == 12 and image[offset:offset + 12] == struct.pack('<3I', METHODS['fr'], 0, 1), 'fixed three-word control layout')
        plans.append(('control.bin', address, length))
        (output / 'dump-plan.txt').write_text(''.join(f'{name} {address:x} {size}\n' for name, address, size in plans))
        proof = dict(contract=CONTRACT, core=core_proof, main=main_proof, exact_flags_guard=1, core_recompiled=True,
                     original_compile_argv=old_argv, derived_compile_argv=argv, combined_object_sha256=digest(output / CORE),
                     old_parent_qualification_scope='source and golden provenance only; no inherited new-combination PASS')
        save(output / 'derivation.json', proof)
        save(output / 'routing-review.json', details['routing_identity'])
        save(output / 'parent-scalar-reaudit.json', scalar)
        verify(files)
        for name, value in actual.items():
            need(digest(source / name) == value, 'generated compile input unchanged')
        names = [PREFIX + '.elf', PREFIX + '.bin', CORE, 'consumer-core.o', 'gs32.o', 'paired16.o', 'dump-plan.txt',
                 'derivation.json', 'routing-review.json', 'parent-scalar-reaudit.json', 'metadata.stdout.log',
                 'disassembly.stdout.log', 'core-disassembly.stdout.log']
        details.update(contract=CONTRACT, status=STATIC, parent_build=str(parent), parent_campaign=str(campaign),
            norm_build=parent_record['norm_build'], am_home=str(am), support_snapshot=CFG['support_snapshot'],
            artifacts={name: digest(output / name) for name in names}, actual_source_pins=actual,
            fixtures=parent_record['fixtures'], kernel_identity=record['kernel_identity'], dump_plan=plans,
            control_offset=offset, expected_flags={str(value): 1 for value in METHODS.values()},
            exact_flags_guard=1, inputs_sha256=digest(output / 'inputs.json'), scalar_flags=scalar['flags'],
            methods=METHODS, reference_runs=0, target_emu_runs=0, performance_qualified=False,
            stable_default_changed=False, old_paired16_hold_preserved=True)
        save(output / 'result.json', details)
        state.update(status=STATIC, result_sha256=digest(output / 'result.json'))
        return details
    except BaseException as error:
        state.update(status='FAILED', error=repr(error))
        raise
    finally:
        state['finished'] = c.base.f.h.now(); save(output / 'state.json', state)


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('first-forward build signal')))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output.resolve())
    print(json.dumps({key: result[key] for key in ('contract', 'status', 'image_bytes', 'performance_qualified')}), flush=True)
