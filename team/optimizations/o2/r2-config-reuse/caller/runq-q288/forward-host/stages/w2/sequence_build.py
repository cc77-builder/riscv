"""Link the sequence harness to the already qualified W2 consumer object.

This helper builds and checks static identity only. It rechecks the completed
eight-dump API qualification, preserves the core object and all four kernels,
and creates the separate ten-dump sequence image. It runs no reference or EMU.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, re, shutil, signal, struct, subprocess

HERE = Path(__file__).resolve().parent
CONTRACT = 'r2-s3-forward-consumer-w2-sequence-v1'
PREFIX = 'consumer-w2-sequence'
STATIC_PASS = 'W2_SEQUENCE_STATIC_PASS_NOT_RUNTIME'
S = 3691424
KERNELS = ('q288_fused_rvv4', 'q288_tail_vdot', 'q768_fr', 'q768_ta')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


a = load('w2_sequence_api_support', HERE / 'api.py')
b = a.b
REPO = a.REPO
need, read, save, digest, command = a.need, a.read, a.save, a.digest, a.command


def build(output, parent, campaign):
    record = read(parent / 'result.json')
    parent_state = read(parent / 'state.json')
    need(record['contract'] == a.CONTRACT and record['status'] == parent_state['status'] == a.STATIC_PASS and
         parent_state.get('finished') and parent_state['result_sha256'] == digest(parent / 'result.json'),
         'closed actual API build with its original result identity')
    qualified, campaign_state = read(campaign / 'results.json'), read(campaign / 'state.json')
    need(qualified['contract'] == campaign_state['contract'] == a.CONTRACT and
         qualified['status'] == campaign_state['status'] == 'SHARED_W2_API_REFERENCE_CAMPAIGN_PASS' and
         campaign_state.get('finished') and campaign_state.get('active_pid') is None and
         not campaign_state.get('active') and not campaign_state.get('cleanup_unknown'),
         'closed actual eight-dump API qualification')
    case = campaign / 'api'
    receipt = read(case / 'result.json')
    need(campaign_state['records'] == [receipt] and receipt['name'] == 'api' and receipt['status'] == a.PASS and
         receipt.get('started') and receipt.get('finished') and len(qualified['records']) == 1 and
         all(receipt.get(k) == value for k, value in qualified['records'][0].items()),
         'complete API case receipt and the earlier summary fields')
    need(S == a.S, 'same complete consumer state layout')
    am = Path(record['am_home'])
    protected = (REPO, parent, campaign, am, Path(record['qualified_build']), Path(record['qualified_campaign']))
    need(not output.exists() and not any(output.is_relative_to(p) for p in protected),
         'fresh sequence build outside all qualified source and evidence roots')
    runtime = read(campaign / 'runtime-inputs.json')
    case_runtime = read(case / 'runtime-inputs.json')
    need(case_runtime == {**runtime, str(case / 'image.bin'): digest(case / 'image.bin')},
         'API case runtime pins add only its actual image')
    argv = receipt['command']
    need(len(argv) == 9 and Path(argv[0]).name == 'reference-runner' and argv[0] in runtime and
         runtime.get(argv[1]) == '8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9' and
         argv[2:] == [str(case / 'image.bin'), str(case), 'builtin', str(a.r.MAX_CALLS), '600',
                      str(parent / 'dump-plan.txt'), '1'] and receipt['cwd'] == str(case),
         'original bounded API invocation uses this exact build and case')
    external = dict(record['external_pins'])

    def pin(path, value):
        path = str(Path(path).resolve())
        need(path not in external or external[path] == value, 'no inherited input rebinding')
        need(digest(path) == value, 'unchanged qualified input: ' + path)
        external[path] = value

    for path, value in case_runtime.items():
        pin(path, value)
    for group, root in (('artifacts', parent), ('fixtures', parent / 'fixture'),
                        ('actual_source_pins', parent / 'source'), ('source_pins', parent / 'source/repo')):
        for name, value in record[group].items():
            need(runtime.get(str(root / name)) == value, 'actual API runtime/build binding: ' + name)
            pin(root / name, value)
    for path in (parent / 'result.json', parent / 'tools.json'):
        need(runtime.get(str(path)) == digest(path), 'same API build metadata actually qualified')
    checked = a.validate(parent, case, record, receipt)
    need(checked == qualified['validation'] == read(case / 'validation.json') and checked['status'] == a.PASS and
         receipt['validation_sha256'] == digest(case / 'validation.json'), 'recomputed complete actual API decision')
    for path in campaign.rglob('*'):
        if path.is_file():
            pin(path, digest(path))
    pin(parent / 'state.json', digest(parent / 'state.json'))
    b.old.f.executable(parent / (a.PREFIX + '.elf'), parent / (a.PREFIX + '.bin'),
                       parent / 'metadata.stdout.log', record['tls_errno_offset'])
    parent_functions = b.old.p.kernel_bytes(parent / (a.PREFIX + '.elf'), KERNELS)
    need(set(parent_functions) == set(record['kernel_identity']['functions']) == set(KERNELS),
         'all four actual qualified parent functions')
    for name, raw in parent_functions.items():
        wanted = record['kernel_identity']['functions'][name]
        need(len(raw) == wanted['bytes'] and hashlib.sha256(raw).hexdigest() == wanted['sha256'],
             'actual qualified parent kernel: ' + name)
    core_sha = record['qualified_consumer_object_sha256']
    need(digest(parent / 'source/consumer-w2.o') == core_sha == record['kernel_identity']['consumer_object_sha256'],
         'original API core object identity')
    need(subprocess.check_output(['git', '-C', am, 'rev-parse', 'HEAD'], text=True).strip() ==
         '086a238062fdfb3281b745a537b361983d0154b5', 'original AM revision')
    need(not subprocess.check_output(['git', '-C', am, 'status', '--porcelain', '--untracked-files=no'],
                                    text=True).strip(), 'official AM unchanged')
    pins = dict(record['source_pins'])
    paths = [*a.module_files(), HERE / 'api.py', HERE / 'sequence_build.py',
             HERE / 'sequence.c', HERE / 'sequence-CONTRACT.md']
    for path in paths:
        rel, value = str(path.relative_to(REPO)), digest(path)
        need(rel not in pins or pins[rel] == value, 'no frozen project source rebinding')
        if str(path) in runtime:
            need(runtime[str(path)] == value, 'same helper source used by qualified API')
        pins[rel] = value
    for rel, value in pins.items():
        need(digest(REPO / rel) == value, 'complete frozen project source')
    for path, value in external.items():
        need(digest(path) == value, 'complete frozen external input')
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
            need(digest(dest) == value, 'exact project source snapshot')
        for name, value in record['fixtures'].items():
            shutil.copyfile(parent / 'fixture' / name, fixture / name)
            need(digest(fixture / name) == value, 'exact qualified model and gold copy')
        prefix = b''.join((fixture / f'host-state-p{position}.bin').read_bytes() for position in range(3))
        need(all((fixture / f'host-state-p{position}.bin').stat().st_size == S for position in range(3)) and
             len(prefix) == 3 * S, 'three complete original host states in p0 p1 p2 order')
        (fixture / 'prefix_gold.bin').write_bytes(prefix)
        for name in ('entry.S', 'w2.S', 'fused.S', 'q288.c', 'q288.h', 'split.h', 'caller.h',
                     'consumer.h', 'consumer_w2.h', 'w2.h', 'consumer-w2.o'):
            shutil.copyfile(parent / 'source' / name, source / name)
        shutil.copyfile(source / 'repo' / HERE.relative_to(REPO) / 'sequence.c', source / 'main.c')
        make = (parent / 'source/Makefile').read_bytes()
        before, after = b'NAME = consumer-w2-api', b'NAME = consumer-w2-sequence'
        need(make.count(before) == 1 and after not in make, 'one exact API makefile name')
        renamed = make.replace(before, after)
        need(renamed.replace(after, before) == make and b'consumer.c' not in renamed and
             renamed.count(b'LINK_FILES += $(CURDIR)/consumer-w2.o $(MATH_ARCHIVE)') == 1,
             'only name changes; qualified core is linked without recompilation')
        (source / 'Makefile').write_bytes(renamed)
        embedded = [*a.MODELS, ('prefix_gold', 'prefix_gold.bin')]
        asm = ['.section .rodata.fixture,"a"', '.balign 16']
        for label, name in embedded:
            asm += [f'.global fixture_{label}', f'fixture_{label}:', f'.incbin "{fixture / name}"',
                    f'.global fixture_{label}_end', f'fixture_{label}_end:', '.balign 16']
        (source / 'fixture.S').write_text('\n'.join(asm) + '\n')
        actual = {str(p.relative_to(source)): digest(p) for p in source.rglob('*')
                  if p.is_file() and not p.is_relative_to(source / 'repo')}
        fixtures = {p.name: digest(p) for p in fixture.iterdir() if p.is_file()}
        for filename, values in (('source-pins.json', pins), ('external-pins.json', external),
                                 ('actual-source-pins.json', actual), ('parent-api-validation.json', checked)):
            save(output / filename, values)
        tools = read(parent / 'tools.json')
        save(output / 'tools.json', tools)
        for tool in tools.values():
            need(digest(tool['path']) == tool['sha256'], 'same qualified GNU build tool')
        keys = ('CFLAGS', 'CPPFLAGS', 'CXXFLAGS', 'ASFLAGS', 'LDFLAGS', 'CC_OPT', 'MAKEFLAGS', 'MFLAGS',
                'CC', 'AS', 'LD', 'OBJCOPY', 'OBJDUMP', 'ARCH', 'MARCH', 'LIBS', 'PREBUILD')
        clean = ['env', *[v for key in keys for v in ('-u', key)], 'AM_HOME=' + str(am), 'LINUX_GNU_TOOLCHAIN=1']
        archives = [path for path in external if Path(path).name == 'libm.a']
        need(len(archives) == 1, 'same fixed static libm')
        command([*clean, tools['make']['path'], '--trace', '--output-sync=target', '-C', source,
                 'ARCH=riscv64-xs', 'MARCH=rv64gv', 'CROSS_COMPILE=' + tools['gcc']['path'][:-3],
                 'FORWARD_OBJ_ROOT=' + str(output / 'objects'), 'BINARY=' + str(output / PREFIX),
                 'MATH_ARCHIVE=' + archives[0], 'FULL_ERRNO_OFFSET=' + str(record['tls_errno_offset']),
                 '-o', 'am', '-o', 'klib', '-j1', 'image'], output, 'target-build', timeout=300)
        command([tools['readelf']['path'], '-W', '-h', '-A', '-l', '-s', '-r', output / (PREFIX + '.elf')],
                output, 'metadata')
        command([tools['objdump']['path'], '-drwC', output / (PREFIX + '.elf')], output, 'disassembly')
        elf, inspection = b.old.f.executable(output / (PREFIX + '.elf'), output / (PREFIX + '.bin'),
                                            output / 'metadata.stdout.log', record['tls_errno_offset'])
        functions = b.old.p.kernel_bytes(output / (PREFIX + '.elf'), KERNELS)
        need(functions == parent_functions, 'all four complete actual functions retain the parent bytes')
        compare_address, compare_size, *_ = elf.symbols['compare']
        # GNU prints local .L/.LVL labels inside a function. Use its actual ELF
        # extent, not the next printed label, when checking the complete body.
        rows = [match for match in re.finditer(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',
                (output / 'disassembly.stdout.log').read_text(), re.M)
                if compare_address <= int(match[1], 16) < compare_address + compare_size]
        words = struct.unpack('<' + str(compare_size // 4) + 'I', elf.read(compare_address, compare_size))
        need(compare_size % 4 == 0 and len(rows) == len(words) and
             all(int(match[2], 16) == word for match, word in zip(rows, words)) and
             not any('memcpy' in match[3] for match in rows) and sum(word & 0x707f == 0x3003 for word in words) >= 2,
             'actual full-state comparison uses direct word loads, no repeated memcpy calls')
        comparison = dict(address=hex(compare_address), bytes=compare_size,
            sha256=hashlib.sha256(elf.read(compare_address, compare_size)).hexdigest(),
            direct_word_loads=True, memcpy_calls=0)
        need(digest(source / 'consumer-w2.o') == core_sha and
             not list((output / 'objects').rglob('consumer*.o')), 'same full core object and no core compilation')
        identity = dict(record['kernel_identity'], qualified_api_elf_sha256=record['artifacts'][a.PREFIX + '.elf'],
                        whole_function_bytes_equal=True, consumer_object_sha256=core_sha)
        save(output / 'kernel-identity.json', identity)
        image = (output / (PREFIX + '.bin')).read_bytes()
        plans = []
        observed = (('sequence_report', 'report.bin', 512), ('sequence_states', 'states.bin', 3 * (S + 32)),
                    ('sequence_flags', 'flags.bin', 256 * 3 * 8), ('sequence_tokens', 'tokens.bin', 256 * 4))
        for symbol, name, size in observed:
            address, length, *_ = elf.symbols[symbol]
            need(length == size and image[address - 0x80000000:address - 0x80000000 + size] == bytes(size),
                 'complete zero initialized sequence storage: ' + symbol)
            if symbol == 'sequence_states':
                need(address % 16 == 0, 'all complete state comparison spans are aligned')
            plans.append((name, address, size))
        for label, name in embedded:
            address = elf.symbols['fixture_' + label][0]
            need(address % 16 == 0, 'all linked immutable fixtures are aligned')
            raw = (fixture / name).read_bytes()
            need(elf.symbols['fixture_' + label + '_end'][0] - address == len(raw) and
                 elf.read(address, len(raw)) == raw, 'whole actual immutable fixture: ' + label)
            dump = 'prefix-gold-after.bin' if label == 'prefix_gold' else name.replace('.bin', '-after.bin')
            plans.append((dump, address, len(raw)))
        need(len(plans) == len({name for name, _, _ in plans}) == 10, 'exact ten sequence memory dumps')
        (output / 'dump-plan.txt').write_text(''.join(f'{name} {address:x} {size}\n' for name, address, size in plans))
        address, length, *_ = elf.symbols['sequence_control']
        offset = address - 0x80000000
        need(length == 8 and address % 4 == 0 and 0 <= offset <= len(image) - 8 and
             elf.read(address, 8) == image[offset:offset + 8] == struct.pack('<2I', 0, 256),
             'actual uint32 control pair is exactly normal 0 and all 256 positions')
        for path, value in external.items():
            need(digest(path) == value, 'external input unchanged after build')
        for rel, value in pins.items():
            need(digest(REPO / rel) == digest(source / 'repo' / rel) == value, 'source unchanged after build')
        for name, value in actual.items():
            need(digest(source / name) == value, 'actual source unchanged after build')
        for name, value in fixtures.items():
            need(digest(fixture / name) == value, 'fixture unchanged after build')
        for tool in tools.values():
            need(digest(tool['path']) == tool['sha256'], 'tool unchanged after build')
        need(not subprocess.check_output(['git', '-C', am, 'status', '--porcelain', '--untracked-files=no'],
                                        text=True).strip(), 'official AM remains unchanged')
        inspection.update(contract=CONTRACT, status=STATIC_PASS, source_pins=pins, external_pins=external,
                          actual_source_pins=actual, fixtures=fixtures, kernel_identity=identity, am_home=str(am),
                          qualified_api_build=str(parent), qualified_api_campaign=str(campaign),
                          qualified_consumer_object_sha256=core_sha, dump_plan=plans, control_offset=offset,
                          state_compare_machine_check=comparison,
                          prefix_gold_positions=[0, 1, 2], prefix_gold_bytes=3 * S,
                          artifacts={name: digest(output / name) for name in
                                     (PREFIX + '.elf', PREFIX + '.bin', 'dump-plan.txt', 'kernel-identity.json',
                                      'parent-api-validation.json', 'metadata.stdout.log', 'disassembly.stdout.log')},
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


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('W2 sequence build signal')))
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('parent', 'campaign', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output.resolve(), args.parent.resolve(), args.campaign.resolve())
    print(json.dumps({key: result[key] for key in ('contract', 'status', 'image_bytes', 'heap_start')}, indent=2))
