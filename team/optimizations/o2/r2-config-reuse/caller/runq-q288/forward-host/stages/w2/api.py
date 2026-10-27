"""Build and reference-test the distinct W2 API using its qualified core object.

The core is never recompiled. The old guarded two-state API harness is
mechanically derived; only the API binding, three new init negatives, report
identity/counts and the corrected trap instruction change. Eight actual memory
dumps have a new schema. This does not run an EMU or claim target performance.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, re, resource, shutil
import signal, struct, subprocess, sys, types

HERE = Path(__file__).resolve().parent
CONTRACT = 'r2-s3-forward-consumer-w2-api-v1'
PARENT_MAIN_SHA = '7b9bcbc19c9c0471cb6326d327ecc0c88a016d2428feb68dc371d32b25a66a17'
MAGIC = 0x5232573241503031
PREFIX = 'consumer-w2-api'
STATIC_PASS = 'SHARED_W2_API_STATIC_PASS_NOT_RUNTIME'
PASS = 'SHARED_W2_API_REFERENCE_PASS'
MODELS = (('weights', 'weights.bin'), ('embedding', 'embedding.bin'),
          ('packed', 'packed.bin'), ('tail_scales', 'tail-scales.bin'),
          ('w2_packed', 'w2-packed.bin'))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


r = load('w2_api_consumer_reference', HERE / 'consumer_run.py')
b = r.b
old = r.old
REPO = b.REPO
S = r.STATE_BYTES
need, read, save, digest, command = r.need, r.read, r.save, r.digest, b.command


def derive_main(raw):
    need(hashlib.sha256(raw).hexdigest() == PARENT_MAIN_SHA, 'exact original guarded API harness')
    original = raw.decode('utf-8')
    text = original
    changes = []

    def replace(before, after, count=1):
        nonlocal text
        need(text.count(before) == count, 'unique API derivation site: ' + before[:72])
        text = text.replace(before, after)
        changes.append((before, after, count))

    replace('#include "consumer.h"', '#include "consumer.h"\n#include "consumer_w2.h"')
    replace('extern unsigned char fixture_packed[],fixture_packed_end[],fixture_tail_scales[],fixture_tail_scales_end[];',
            'extern unsigned char fixture_packed[],fixture_packed_end[],fixture_tail_scales[],fixture_tail_scales_end[];\n'
            'extern unsigned char fixture_w2_packed[],fixture_w2_packed_end[];')
    for api in ('init', 'reset', 'forward'):
        before = 'r2_consumer_' + api
        replace(before, 'r2_w2_' + api, text.count(before))
    replace('.word 0x0000006b', '.word 0x0005006b')
    replace('0x5232434150493031', '0x5232573241503031')
    replace('packed,fixture_packed_end-fixture_packed,fixture_tail_scales,fixture_tail_scales_end-fixture_tail_scales);',
            'packed,fixture_packed_end-fixture_packed,fixture_tail_scales,fixture_tail_scales_end-fixture_tail_scales,\n'
            '        fixture_w2_packed,fixture_w2_packed_end-fixture_w2_packed);')
    anchor = 'static void initialize_valid(void) {'
    replace(anchor, '''static int initialize_pack(const void *packed,size_t bytes) {
    return r2_w2_init(fixture_weights,fixture_weights_end-fixture_weights,
        fixture_embedding,fixture_embedding_end-fixture_embedding,
        fixture_packed,fixture_packed_end-fixture_packed,
        fixture_tail_scales,fixture_tail_scales_end-fixture_tail_scales,packed,bytes);
}
''' + anchor)
    anchor = '    rejected(NULL,R2_TA_CACHE,1,0);rejected(a,-1,1,0);rejected(a,5,1,0);'
    replace(anchor, '''    check(initialize_pack(NULL,R2_W2_PACKED_BYTES)==-1,94);++api_report[5];
    rejected(a,R2_TA_CACHE,1,0);initialize_valid();
    check(initialize_pack(fixture_w2_packed,R2_W2_PACKED_BYTES-1)==-1,95);++api_report[5];
    rejected(a,R2_TA_CACHE,1,0);initialize_valid();
    check(initialize_pack(fixture_w2_packed+1,R2_W2_PACKED_BYTES)==-1,96);++api_report[5];
    rejected(a,R2_TA_CACHE,1,0);initialize_valid();
''' + anchor)
    replace('api_report[4]==10 && api_report[5]==2 && api_report[6]==3',
            'api_report[4]==13 && api_report[5]==5 && api_report[6]==6')
    restored = text
    for before, after, count in reversed(changes):
        need(restored.count(after) == count, 'unambiguous complete API reversal')
        restored = restored.replace(after, before)
    need(restored == original, 'all generated API changes reverse to the complete original')
    return text, dict(parent_sha256=PARENT_MAIN_SHA, generated_sha256=hashlib.sha256(text.encode()).hexdigest(),
                      exact_parent_reverse=True, substitutions=len(changes), new_pack_init_negatives=3,
                      rejected_forwards=13, failed_inits=5, successful_inits=6, forward_calls=5, snapshot_pairs=6,
                      trap_word='0x0005006b')


def module_files():
    pending = list(sys.modules.values()) + [r, b, old]
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


def build(output, parent, campaign):
    record = read(parent / 'result.json')
    qualified, campaign_state = read(campaign / 'results.json'), read(campaign / 'state.json')
    need(record['contract'] == b.CONTRACT and record['status'] == 'PURE_W2_CONSUMER_STATIC_ELF_PASS_NOT_RUNTIME',
         'distinct actually built W2 consumer')
    need(qualified['contract'] == b.CONTRACT and qualified['status'] == campaign_state['status'] ==
         'PURE_W2_FORWARD_REFERENCE_CAMPAIGN_PASS' and campaign_state['active_pid'] is None,
         'completed new ten-case W2 consumer qualification')
    need(set(qualified['validations']) == {name for name, _, _ in r.CASES} and
         len(campaign_state['records']) == len(r.CASES) == 10, 'all ten actual parent cases')
    am = Path(record['am_home'])
    need(not output.exists() and not any(output.is_relative_to(p) for p in (REPO, parent, campaign, am)),
         'fresh isolated API build')
    runtime = read(campaign / 'runtime-inputs.json')
    external = dict(record['external_pins'])

    def pin(path, value):
        path = str(Path(path).resolve())
        need(path not in external or external[path] == value, 'no inherited input rebinding')
        need(digest(path) == value, 'unchanged inherited input: ' + path)
        external[path] = value

    for name, value in record['artifacts'].items():
        need(runtime[str(parent / name)] == value, 'same artifact in completed parent reference')
    for group, root in (('artifacts', parent), ('fixtures', parent / 'fixture'),
                        ('actual_source_pins', parent / 'source')):
        for name, value in record[group].items():
            pin(root / name, value)
    for path in (parent / 'result.json', parent / 'tools.json', campaign / 'results.json',
                 campaign / 'state.json', campaign / 'runtime-inputs.json'):
        pin(path, digest(path))
    for name, method, kind in r.CASES:
        dest = campaign / name
        receipt = read(dest / 'result.json')
        actual = r.validate(parent, dest, record, method, kind, receipt)
        need(actual == qualified['validations'][name], 're-audited actual parent case: ' + name)
        for filename, value in actual['raw_sha256'].items():
            pin(dest / filename, value)
        for filename in ('result.json', 'validation.json', 'reference-result.json', 'abi.json',
                         'image-control.json', 'image.bin', 'stdout.log', 'stderr.log',
                         'initial-registers.bin', 'final-registers.bin', 'initial-csrs.bin', 'final-csrs.bin'):
            pin(dest / filename, digest(dest / filename))
    need(subprocess.check_output(['git', '-C', am, 'rev-parse', 'HEAD'], text=True).strip() ==
         '086a238062fdfb3281b745a537b361983d0154b5', 'original AM revision')
    need(not subprocess.check_output(['git', '-C', am, 'status', '--porcelain', '--untracked-files=no'],
                                    text=True).strip(), 'official AM unchanged')
    api_parent = HERE.parent / 'consumer/api_main.c'
    pins = dict(record['source_pins'])
    for path in (*module_files(), HERE / 'api.py', api_parent):
        rel, value = str(path.relative_to(REPO)), digest(path)
        need(rel not in pins or pins[rel] == value, 'no source identity rebinding')
        pins[rel] = value
    for rel, value in pins.items():
        need(digest(REPO / rel) == value, 'current frozen source: ' + rel)
    for path, value in external.items():
        need(digest(path) == value, 'current frozen external input')
    output.mkdir(parents=True)
    state = dict(contract=CONTRACT, status='BUILDING', started=b.old.f.h.now(),
                 cpu_affinity=sorted(os.sched_getaffinity(0)))
    save(output / 'state.json', state)
    try:
        source, fixture = output / 'source', output / 'fixture'
        source.mkdir(); fixture.mkdir()
        for rel, value in pins.items():
            dest = source / 'repo' / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / rel, dest)
            need(digest(dest) == value, 'exact source snapshot')
        for name, value in record['fixtures'].items():
            shutil.copyfile(parent / 'fixture' / name, fixture / name)
            need(digest(fixture / name) == value, 'exact model and gold copy')
        for name in ('entry.S', 'fused.S', 'w2.S', 'q288.c', 'q288.h', 'split.h', 'caller.h',
                     'consumer.h', 'consumer_w2.h', 'w2.h'):
            shutil.copyfile(parent / 'source' / name, source / name)
        shutil.copyfile(parent / 'consumer-w2.o', source / 'consumer-w2.o')
        main, proof = derive_main((source / 'repo' / api_parent.relative_to(REPO)).read_bytes())
        (source / 'main.c').write_text(main)
        save(output / 'api-generation.json', proof)
        make = (parent / 'source/Makefile').read_text()
        for before, after in (('NAME = forward-consumer-w2', 'NAME = ' + PREFIX),
                              ('SRCS = main.c consumer.c w2.S', 'SRCS = main.c w2.S'),
                              ('LINK_FILES += $(MATH_ARCHIVE)',
                               'LINK_FILES += $(CURDIR)/consumer-w2.o $(MATH_ARCHIVE)')):
            need(make.count(before) == 1, 'exact qualified makefile substitution')
            make = make.replace(before, after)
        need('consumer.c' not in make, 'qualified core is linked, never rebuilt')
        (source / 'Makefile').write_text(make)
        asm = ['.section .rodata.fixture,"a"', '.balign 16']
        for label, name in MODELS:
            asm += [f'.global fixture_{label}', f'fixture_{label}:', f'.incbin "{fixture / name}"',
                    f'.global fixture_{label}_end', f'fixture_{label}_end:', '.balign 16']
        (source / 'fixture.S').write_text('\n'.join(asm) + '\n')
        actual = {str(p.relative_to(source)): digest(p) for p in source.rglob('*')
                  if p.is_file() and not p.is_relative_to(source / 'repo')}
        for filename, values in (('source-pins.json', pins), ('external-pins.json', external),
                                 ('actual-source-pins.json', actual)):
            save(output / filename, values)
        tools = read(parent / 'tools.json')
        save(output / 'tools.json', tools)
        for tool in tools.values():
            need(digest(tool['path']) == tool['sha256'], 'same actual qualified build tool')
        keys = ('CFLAGS', 'CPPFLAGS', 'CXXFLAGS', 'ASFLAGS', 'LDFLAGS', 'CC_OPT', 'MAKEFLAGS', 'MFLAGS',
                'CC', 'AS', 'LD', 'OBJCOPY', 'OBJDUMP', 'ARCH', 'MARCH', 'LIBS', 'PREBUILD')
        clean = ['env', *[v for key in keys for v in ('-u', key)], 'AM_HOME=' + str(am), 'LINUX_GNU_TOOLCHAIN=1']
        archives = [p for p in external if Path(p).name == 'libm.a']
        need(len(archives) == 1, 'same fixed libm archive')
        command([*clean, tools['make']['path'], '--trace', '--output-sync=target', '-C', source,
                 'ARCH=riscv64-xs', 'MARCH=rv64gv', 'CROSS_COMPILE=' + tools['gcc']['path'][:-3],
                 'FORWARD_OBJ_ROOT=' + str(output / 'objects'), 'BINARY=' + str(output / PREFIX),
                 'MATH_ARCHIVE=' + archives[0], 'FULL_ERRNO_OFFSET=' + str(record['tls_errno_offset']),
                 '-o', 'am', '-o', 'klib', '-j1', 'image'], output, 'target-build', timeout=300)
        command([tools['readelf']['path'], '-W', '-h', '-A', '-l', '-s', '-r', output / (PREFIX + '.elf')], output, 'metadata')
        command([tools['objdump']['path'], '-drwC', output / (PREFIX + '.elf')], output, 'disassembly')
        elf, inspection = b.old.f.executable(output / (PREFIX + '.elf'), output / (PREFIX + '.bin'),
                                            output / 'metadata.stdout.log', record['tls_errno_offset'])
        functions = b.old.p.kernel_bytes(output / (PREFIX + '.elf'), record['kernel_identity']['functions'])
        need(len(functions) == 4, 'all four qualified kernels actually linked')
        for name, raw in functions.items():
            wanted = record['kernel_identity']['functions'][name]
            need(len(raw) == wanted['bytes'] and hashlib.sha256(raw).hexdigest() == wanted['sha256'],
                 'same complete qualified kernel: ' + name)
        core_sha = record['artifacts']['consumer-w2.o']
        need(digest(source / 'consumer-w2.o') == core_sha == record['kernel_identity']['consumer_object_sha256']
             and not list((output / 'objects').rglob('consumer*.o')), 'exact qualified object, no core recompilation')
        plans, image = [], (output / (PREFIX + '.bin')).read_bytes()
        observed = [('api_report', 'report.bin', 512), ('api_states', 'states.bin', 2 * (S + 32)),
                    ('api_snapshots', 'snapshots.bin', 12 * S)]
        for symbol, name, size in observed:
            address, length, *_ = elf.symbols[symbol]
            need(length == size and image[address - 0x80000000:address - 0x80000000 + size] == bytes(size),
                 'complete zero initialized API storage')
            plans.append((name, address, size))
        for label, name in MODELS:
            address = elf.symbols['fixture_' + label][0]
            raw = (fixture / name).read_bytes()
            need(elf.symbols['fixture_' + label + '_end'][0] - address == len(raw) and
                 elf.read(address, len(raw)) == raw, 'whole actual linked model: ' + label)
            plans.append((name.replace('.bin', '-after.bin'), address, len(raw)))
        need(len(plans) == 8, 'new API has exactly eight memory dumps')
        (output / 'dump-plan.txt').write_text(''.join(f'{name} {address:x} {size}\n' for name, address, size in plans))
        for path, value in external.items():
            need(digest(path) == value, 'external input unchanged after build')
        for rel, value in pins.items():
            need(digest(REPO / rel) == digest(source / 'repo' / rel) == value, 'source unchanged after build')
        for name, value in actual.items():
            need(digest(source / name) == value, 'actual source unchanged after build')
        for name, value in record['fixtures'].items():
            need(digest(fixture / name) == value, 'fixture unchanged after build')
        for tool in tools.values():
            need(digest(tool['path']) == tool['sha256'], 'tool unchanged after build')
        inspection.update(contract=CONTRACT, status=STATIC_PASS, source_pins=pins, external_pins=external,
                          actual_source_pins=actual, fixtures=record['fixtures'], kernel_identity=record['kernel_identity'],
                          api_generation=proof, qualified_consumer_object_sha256=core_sha, am_home=str(am),
                          qualified_build=str(parent), qualified_campaign=str(campaign), dump_plan=plans,
                          artifacts={name: digest(output / name) for name in
                                     (PREFIX + '.elf', PREFIX + '.bin', 'dump-plan.txt', 'api-generation.json',
                                      'metadata.stdout.log', 'disassembly.stdout.log')},
                          reference_runs=0, target_emu_runs=0, performance_qualified=False)
        save(output / 'result.json', inspection)
        state.update(status=STATIC_PASS, result_sha256=digest(output / 'result.json'))
        return inspection
    except BaseException as error:
        state.update(status='FAILED', error=repr(error))
        raise
    finally:
        state['finished'] = b.old.f.h.now()
        save(output / 'state.json', state)


def inputs(build_dir, adapter, identity_path):
    record = read(build_dir / 'result.json')
    need(record['contract'] == CONTRACT and record['status'] == STATIC_PASS, 'distinct eight-dump API build')
    parent, identity, checker, files = r.verify_inputs(Path(record['qualified_build']), adapter, identity_path)
    need(record['qualified_consumer_object_sha256'] == parent['artifacts']['consumer-w2.o'], 'same qualified W2 core')

    def pin(path, value):
        path = str(Path(path).resolve())
        need(path not in files or files[path] == value, 'no runtime identity rebinding')
        files[path] = value

    for path, value in record['external_pins'].items():
        pin(path, value)
    for rel, value in record['source_pins'].items():
        pin(REPO / rel, value); pin(build_dir / 'source/repo' / rel, value)
    for key, root in (('actual_source_pins', build_dir / 'source'), ('fixtures', build_dir / 'fixture'),
                      ('artifacts', build_dir)):
        for name, value in record[key].items():
            pin(root / name, value)
    for path in (build_dir / 'result.json', build_dir / 'tools.json', HERE / 'api.py', *module_files()):
        pin(path, digest(path))
    for tool in read(build_dir / 'tools.json').values():
        pin(tool['path'], tool['sha256'])
    b.old.f.executable(build_dir / (PREFIX + '.elf'), build_dir / (PREFIX + '.bin'),
                       build_dir / 'metadata.stdout.log', record['tls_errno_offset'])
    functions = b.old.p.kernel_bytes(build_dir / (PREFIX + '.elf'), record['kernel_identity']['functions'])
    need(len(functions) == 4, 'all four kernels remain linked')
    for name, raw in functions.items():
        wanted = record['kernel_identity']['functions'][name]
        need(len(raw) == wanted['bytes'] and hashlib.sha256(raw).hexdigest() == wanted['sha256'],
             'actual full API kernel identity')
    checker.verify_files(files)
    return record, files, identity, checker


def validate(build_dir, dest, record, receipt):
    need(receipt.get('process_started') is True and receipt.get('direct_child_reaped') is True and
         receipt.get('process_group_absent_after_exit') is True and not receipt.get('residual_process_group') and
         not receipt.get('timed_out') and receipt['exit_code'] == 0, 'complete owned API reference process')
    result, abi = read(dest / 'reference-result.json'), read(dest / 'abi.json')
    need(result['state'] == 2 and result['reason'] == 'good_trap' and result['halt_ret'] == 0 and
         0 < result['retired'] <= result['api_calls'] <= r.MAX_CALLS and result['memory_dumps'] == 8 and
         result['xiangshan_cycles_measured'] is False, 'actual bounded success and eight actual dumps')
    need(abi['register_bytes'] == abi['header_span'] == 1400 and abi['initial_pc'] == 0x10000000 and
         abi['initial_mode'] == 3, 'original reference reset and register ABI')
    text = (dest / 'stdout.log').read_text()
    need(not (dest / 'stderr.log').read_bytes() and not any(value in text.lower() for value in
         ('pma check failed', 'critical error', 'reference_adapter_reject', 'abort')), 'no reference runtime fault')
    plain = re.sub(r'\x1b\[[0-9;]*m', '', text)
    traps = [line for line in plain.splitlines() if 'HIT ' in line and ' TRAP' in line]
    need(len(traps) <= 1, 'at most one original reference trap line')
    for line in traps:
        match = re.fullmatch(r'(?:\[[^\]\r\n]+\]\s*)?nemu: HIT GOOD TRAP at pc = (0x[0-9a-fA-F]+)', line)
        need(match is not None and int(match[1], 16) == result['halt_pc'], 'canonical actual original good trap')
    sizes = {'report.bin': 512, 'states.bin': 2 * (S + 32), 'snapshots.bin': 12 * S,
             'weights-after.bin': 17101440, 'embedding-after.bin': 36864000,
             'packed-after.bin': 172 * 82944, 'tail-scales-after.bin': 13 * 288 * 9 * 4,
             'w2-packed-after.bin': 6 * 221184, 'initial-registers.bin': 1400, 'final-registers.bin': 1400,
             'initial-csrs.bin': 32768, 'final-csrs.bin': 32768}
    need({name: size for name, _, size in record['dump_plan']} ==
         {name: size for name, size in sizes.items() if name not in
          ('initial-registers.bin', 'final-registers.bin', 'initial-csrs.bin', 'final-csrs.bin')},
         'exact new build dump inventory')
    need({path.name for path in dest.glob('*.bin')} == set(sizes) | {'image.bin'}, 'exact actual raw output inventory')
    for name, size in sizes.items():
        need((dest / name).stat().st_size == size, 'complete actual dump: ' + name)
    need(digest(dest / 'image.bin') == record['artifacts'][PREFIX + '.bin'], 'actual API image has no data mutation')
    for _, name in MODELS:
        need(digest(dest / name.replace('.bin', '-after.bin')) == record['fixtures'][name],
             'complete immutable model unchanged: ' + name)
    report = struct.unpack('<64Q', (dest / 'report.bin').read_bytes())
    need(report[:10] == (MAGIC, 1, 0, 0, 13, 5, 6, 5, 6, 0) and
         report[10] & 0x6000 and report[10] & 0x600 and report[11] == 16 and
         not any(report[12:16]) and not any(report[21:]), 'actual API identity, call counts and report extent')
    gold = [(build_dir / 'fixture' / f'host-state-p{pos}.bin').read_bytes() for pos in range(3)]
    need(all(len(raw) == S for raw in gold), 'complete independent original-host states')
    zero = bytes(S)
    pairs = ((gold[0], zero), (gold[0], gold[0]), (gold[1], gold[0]),
             (gold[1], zero), (gold[1], gold[0]), (gold[2], gold[0]))
    need((dest / 'snapshots.bin').read_bytes() == b''.join(a + c for a, c in pairs),
         'six complete state pairs: interleaving, reset, no cross-state changes')
    guard = struct.pack('<2Q', *[0xb5e9c13f6a0742d8] * 2)
    need((dest / 'states.bin').read_bytes() == guard + gold[2] + guard + guard + gold[0] + guard,
         'both complete final live states and all guards')
    qualification = read(Path(record['qualified_campaign']) / 'results.json')
    need(qualification['contract'] == b.CONTRACT and qualification['status'] ==
         'PURE_W2_FORWARD_REFERENCE_CAMPAIGN_PASS', 'new W2 paths supply the qualified flags')
    values = qualification['validations']
    flags = (values['ta-cache']['flags'][0], values['fr-cache']['flags'][0], values['ta-cache']['flags'][1],
             values['fr-cache']['flags'][0], values['ta-cache']['flags'][2])
    need(report[16:21] == flags and all(v >> 5 == 0 for v in flags), 'five actual flags match new W2-qualified paths')
    return dict(contract=CONTRACT, status=PASS, report=list(report), expected_flags=list(flags),
                raw_sha256={name: digest(dest / name) for name in sizes},
                api_calls=result['api_calls'], retired=result['retired'],
                qualified_consumer_object_sha256=record['qualified_consumer_object_sha256'],
                target_emu_runs=0, performance_qualified=False)


def run(build_dir, adapter, identity_path, output):
    need(not output.exists() and len(os.sched_getaffinity(0)) == 1, 'fresh single-CPU API reference output')
    record, files, identity, checker = inputs(build_dir, adapter, identity_path)
    old.r.parent.outside_inputs(output, [REPO, build_dir, Path(record['qualified_build']),
        Path(record['qualified_campaign']), adapter, identity_path.parent,
        Path(identity['configuration']['hardware_source']), Path(record['am_home'])])
    soft, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
    limit = 128 * 1024 * 1024
    need(hard == resource.RLIM_INFINITY or hard >= limit, 'whole API image and snapshot file budget')
    resource.setrlimit(resource.RLIMIT_FSIZE, (limit, hard))
    output.mkdir(parents=True)
    save(output / 'runtime-inputs.json', files)
    old.snapshot_runtime(output, files)
    shutil.copyfile(identity_path, output / 'parent-identity.json')
    state = dict(contract=CONTRACT, status='RUNNING', started=b.old.f.h.now(), active_pid=None,
                 cpu_affinity=sorted(os.sched_getaffinity(0)), records=[], performance_qualified=False)
    persist = lambda: save(output / 'state.json', state)
    persist()
    dest = output / 'api'
    dest.mkdir()
    shutil.copyfile(build_dir / (PREFIX + '.bin'), dest / 'image.bin')
    casefiles = dict(files)
    casefiles[str(dest / 'image.bin')] = digest(dest / 'image.bin')
    save(dest / 'runtime-inputs.json', casefiles)
    argv = [str(adapter / 'reference-runner'), identity['configuration']['reference'], str(dest / 'image.bin'),
            str(dest), 'builtin', str(r.MAX_CALLS), '600', str(build_dir / 'dump-plan.txt'), '1']
    receipt = dict(name='api', command=argv, cwd=str(dest), started=b.old.f.h.now(), process_started=False,
                   exit_code=None, status='RUNNING', cpu_affinity=sorted(os.sched_getaffinity(0)),
                   max_api_calls=r.MAX_CALLS, wall_limit_seconds=600, external_timeout_seconds=630,
                   max_output_file_bytes=limit)
    state['records'].append(receipt)

    def progress():
        state['active_pid'] = receipt.get('pid') if not receipt.get('process_group_absent_after_exit') else None
        state['active_result'] = str(dest / 'result.json') if state['active_pid'] else None
        save(dest / 'result.json', receipt)
        persist()

    progress()
    try:
        checker.verify_files(casefiles)
        with (dest / 'stdout.log').open('wb') as stdout, (dest / 'stderr.log').open('wb') as stderr:
            old.previous.spawn(argv, dest, stdout, stderr, receipt, progress, dict(os.environ), 630)
        checked = validate(build_dir, dest, record, receipt)
        save(dest / 'validation.json', checked)
        checker.verify_files(casefiles)
        receipt.update(status=PASS, validation_sha256=digest(dest / 'validation.json'))
        state.update(status='SHARED_W2_API_REFERENCE_CAMPAIGN_PASS')
        save(output / 'results.json', dict(contract=CONTRACT, status=state['status'], validation=checked,
            records=state['records'], target_emu_runs=0, performance_qualified=False))
    except BaseException as error:
        receipt.update(status='FAILED', error=repr(error))
        state.update(status='FAILED', error=repr(error))
        raise
    finally:
        receipt['finished'] = state['finished'] = b.old.f.h.now()
        progress()
    return state


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('W2 API signal')))
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    build_parser = sub.add_parser('build')
    for name in ('output', 'parent', 'campaign'):
        build_parser.add_argument('--' + name, type=Path, required=True)
    run_parser = sub.add_parser('run')
    for name in ('build', 'adapter', 'identity', 'output'):
        run_parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    os.sched_setaffinity(0, [min(os.sched_getaffinity(0))])
    if args.action == 'build':
        result = build(args.output.resolve(), args.parent.resolve(), args.campaign.resolve())
    else:
        result = run(args.build.resolve(), args.adapter.resolve(), args.identity.resolve(), args.output.resolve())
    print(json.dumps({key: result[key] for key in ('contract', 'status')}, indent=2))
