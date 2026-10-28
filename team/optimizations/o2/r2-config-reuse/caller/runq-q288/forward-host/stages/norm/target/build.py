"""Link a guarded first-token UART harness to the qualified W2+norm object."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import struct
import subprocess

HERE = Path(__file__).resolve().parent
STAGES = HERE.parent.parent
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

c = load('first_token_consumer_build', HERE.parent / 'consumer/build.py')
cr = load('first_token_consumer_reference', HERE.parent / 'consumer/run.py')
aux = load('first_token_uart_elf', STAGES / 'consumer/aux_build.py')
need, read, save, digest, command = c.need, c.read, c.save, c.digest, c.command
REPO, S, CORE = c.REPO, c.S, c.CORE
CONTRACT = 'r2-s3-w2-norm-first-token-v1'
PREFIX = 'consumer-w2-norm-first-token'
STATIC = 'NORM_W2_FIRST_TOKEN_STATIC_PASS_NOT_RUNTIME'
REFERENCE_PASS = 'NORM_W2_FIRST_TOKEN_REFERENCE_CAMPAIGN_PASS'
MAIN_SHA = '15d0fd567415783fc7caf90ffb8ff6ac1ef26199354c791af8feee0060a2fd3f'
ENTRY_SHA = '7db6047a7dfea8a4a1cd98ba95b2845c03405d4fc8aee638463e241da6290531'
MAGIC = 0x52324e5447543031
GUARD = 0xb5e9c13f6a0742d8


def derive_main(original):
    need(hashlib.sha256(original).hexdigest() == MAIN_SHA, 'exact frozen team target main')
    text = original.decode(); changes = []
    def change(before, after):
        nonlocal text
        need(text.count(before) == 1 and before != after, 'unique bounded main derivation')
        text = text.replace(before, after); changes.append((before, after))
    change('#include "consumer.h"', '#include "consumer_w2.h"\nextern unsigned char fixture_w2_packed[],fixture_w2_packed_end[];')
    change('struct r2_consumer_state target_state __attribute__((aligned(16)));',
           'struct target_guarded_state { uint64_t before[2]; struct r2_consumer_state state; uint64_t after[2]; };\n'
           'struct target_guarded_state target_guarded __attribute__((aligned(16)));\n'
           '_Static_assert(offsetof(struct target_guarded_state,state)==16 && sizeof(struct target_guarded_state)==R2_CONSUMER_STATE_BYTES+32,"exact state guard layout");\n'
           '#define target_state target_guarded.state\n'
           '#define TARGET_GUARD UINT64_C(0xb5e9c13f6a0742d8)')
    change('__attribute__((noreturn)) static void reject', '__attribute__((noreturn,noinline,noclone)) static void reject')
    change('.word 0x0000006b', '.word 0x0005006b')
    change('0x5232435447543031', '0x52324e5447543031')
    change('    check(r2_consumer_init(fixture_weights',
           '    for(unsigned i=0;i<2;++i)target_guarded.before[i]=target_guarded.after[i]=TARGET_GUARD;\n'
           '    check(r2_w2_init(fixture_weights')
    change('fixture_tail_scales,fixture_tail_scales_end-fixture_tail_scales)==0,84);',
           'fixture_tail_scales,fixture_tail_scales_end-fixture_tail_scales,\n'
           '        fixture_w2_packed,fixture_w2_packed_end-fixture_w2_packed)==0,84);')
    change('r2_consumer_forward(&target_state,', 'r2_w2_forward(&target_state,')
    change(' && flags>>5==0,85);tls_check();', ' && flags==1,85);tls_check();')
    change('    if(negative)((unsigned char*)&target_state.logits[31999])[0]^=1;\n    complete_compare();\n    if(uart) {',
           '    for(unsigned i=0;i<2;++i)check(target_guarded.before[i]==TARGET_GUARD && target_guarded.after[i]==TARGET_GUARD,87);\n'
           '    target_report[21]=1;\n    if(uart) {')
    change('        printf("CONSUMER_PASS bytes=%u flags=%u\\n",R2_CONSUMER_STATE_BYTES,flags);\n    }',
           '    }\n    if(negative)((unsigned char*)&target_state.logits[31999])[0]^=1;\n'
           '    complete_compare();\n    if(uart)printf("CONSUMER_PASS bytes=%u flags=%u\\n",R2_CONSUMER_STATE_BYTES,flags);')
    reverse = text
    for before, after in reversed(changes):
        need(reverse.count(after) == 1, 'unique inverse derivation')
        reverse = reverse.replace(after, before)
    need(reverse.encode() == original, 'exact frozen main recovered by inverse substitutions')
    return text.encode(), dict(parent_main_sha256=MAIN_SHA, substitutions=len(changes),
        exact_inverse=True, state_guards=True, counter_uart_before_comparison=True,
        negative_trap_uses_a0=True, exact_flags_guard=1, core_recompiled=False)


def traps(elf):
    start, size, *_ = elf.symbols['reject']
    pcs = []; pc = start
    while pc < start + size:
        low = struct.unpack('<H', elf.read(pc, 2))[0]
        if low & 3 != 3:
            pc += 2; continue
        word = struct.unpack('<I', elf.read(pc, 4))[0]
        need(word != 0x0000006b, 'failure trap must consume a0')
        if word == 0x0005006b:
            pcs.append(hex(pc))
        pc += 4
    success = elf.symbols['full_success_trap'][0]
    need(len(pcs) == 1 and elf.read(success, 4) == struct.pack('<I', 0x0005006b),
         'one exact a0-consuming failure trap and exact success trap')
    return dict(failure_traps=pcs, success_trap=hex(success), trap_word='0x0005006b')


def inspect(output, record):
    elf, inspection = aux.uart_executable(output / (PREFIX + '.elf'), output / (PREFIX + '.bin'),
                                         output / 'metadata.stdout.log', record['tls_errno_offset'])
    for name, raw in c.base.p.kernel_bytes(output / (PREFIX + '.elf'), record['kernel_identity']['functions']).items():
        wanted = record['kernel_identity']['functions'][name]
        need(len(raw) == wanted['bytes'] and hashlib.sha256(raw).hexdigest() == wanted['sha256'],
             'entire qualified FR/TA function bytes: ' + name)
    original, _ = c.n.executable(Path(record['norm_build']) / 'real-norm.elf', Path(record['norm_build']) / 'real-norm.bin')
    inspection['norm_identity'] = c.norm_link_identity(elf, original)
    inspection.update(traps(elf))
    return elf, inspection


def build(output, parent, campaign):
    record, qualified, state = read(parent / 'result.json'), read(campaign / 'results.json'), read(campaign / 'state.json')
    need(record['contract'] == c.CONTRACT and record['status'] == c.STATIC, 'new combined consumer static identity')
    need(qualified['contract'] == c.CONTRACT and qualified['status'] == state['status'] == c.PASS
         and state['active'] == [] and not state['cleanup_unknown'] and state['reference_runs'] == 8,
         'closed eight-case qualification for this combined object')
    need(all(qualified['validations'][name]['flags'][0] == 1 for name in ('fr-cache', 'ta-cache')),
         'both first-token methods have the exact NX-only flags enforced before positive or negative UART')
    runtime = read(campaign / 'runtime-inputs.json'); external = {}
    c.inherit(external, parent, record)
    for group, root in (('artifacts', parent), ('fixtures', parent / 'fixture'), ('actual_source_pins', parent / 'source')):
        for name, value in record[group].items():
            need(runtime[str(root / name)] == value, 'same actually qualified parent input')
    rechecks = {}
    for label, method, negative in cr.CASES:
        dest = campaign / label
        actual = cr.validate(parent, dest, method, negative, read(dest / 'result.json'))
        need(actual == qualified['validations'][label] == read(dest / 'validation.json'), 'actual new parent raw recheck: ' + label)
        rechecks[label] = actual
        for name, value in actual['raw_sha256'].items():
            c.pin(external, dest / name, value)
        for name in ('result.json', 'validation.json', 'reference-result.json', 'abi.json', 'image-control.json',
                     'image.bin', 'stdout.log', 'stderr.log', 'initial-registers.bin', 'final-registers.bin',
                     'initial-csrs.bin', 'final-csrs.bin'):
            c.pin(external, dest / name)
    for name in ('results.json', 'state.json', 'runtime-inputs.json'):
        c.pin(external, campaign / name)
    am = Path(record['am_home'])
    for folder in ('am/include', 'am/src/nemu/include', 'am/src/xs/include', 'libs/klib/include'):
        for path in (am / folder).rglob('*.h'):
            c.pin(external, path)
    need(subprocess.check_output(['git', '-C', am, 'rev-parse', 'HEAD'], text=True).strip() ==
         '086a238062fdfb3281b745a537b361983d0154b5' and not
         subprocess.check_output(['git', '-C', am, 'status', '--porcelain', '--untracked-files=no'], text=True).strip(),
         'unchanged official AM revision and sources')
    need(not output.exists() and not any(output.is_relative_to(p) for p in (REPO, parent, campaign, am)), 'fresh isolated build output')
    pins = dict(record['source_pins'])
    for path in (*c.module_files(), STAGES / 'consumer/target_main.c', HERE / 'build.py',
                 HERE / 'reference.py', HERE / 'CONTRACT.md'):
        rel, value = str(path.relative_to(REPO)), digest(path)
        need(rel not in pins or pins[rel] == value, 'no source identity rebinding')
        pins[rel] = value
    output.mkdir(parents=True)
    status = dict(contract=CONTRACT, status='BUILDING', started=c.base.f.h.now(), cpu_affinity=sorted(os.sched_getaffinity(0)))
    save(output / 'state.json', status)
    try:
        source, fixture = output / 'source', output / 'fixture'; source.mkdir(); fixture.mkdir()
        for rel, value in pins.items():
            need(digest(REPO / rel) == value, 'unchanged source before build')
            dest = source / 'repo' / rel; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / rel, dest); need(digest(dest) == value, 'exact source snapshot')
        for name, value in record['actual_source_pins'].items():
            dest = source / name; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(parent / 'source' / name, dest); need(digest(dest) == value, 'exact inherited compile input')
        for name, value in record['fixtures'].items():
            shutil.copyfile(parent / 'fixture' / name, fixture / name); need(digest(fixture / name) == value, 'whole frozen fixture')
        shutil.copyfile(parent / CORE, output / CORE); shutil.copyfile(parent / CORE, source / CORE)
        main, proof = derive_main((STAGES / 'consumer/target_main.c').read_bytes())
        (source / 'main.c').write_bytes(main)
        entry = (source / 'entry.S').read_bytes()
        need(hashlib.sha256(entry).hexdigest() == ENTRY_SHA and entry.count(b'.word 0x0000006b') == 1, 'frozen parent entry')
        changed = entry.replace(b'.word 0x0000006b', b'.word 0x0005006b')
        need(changed.replace(b'.word 0x0005006b', b'.word 0x0000006b') == entry, 'exact inverse entry derivation')
        (source / 'entry.S').write_bytes(changed)
        proof.update(parent_entry_sha256=ENTRY_SHA, entry_exact_inverse=True, qualified_core_sha256=digest(output / CORE), parent_rechecked=rechecks)
        save(output / 'derivation.json', proof)
        make = (source / 'Makefile').read_text()
        need(make.count('NAME = ' + c.PREFIX) == 1 and 'consumer.c' not in make and CORE in make, 'exact qualified object link profile')
        (source / 'Makefile').write_text(make.replace('NAME = ' + c.PREFIX, 'NAME = ' + PREFIX))
        embedded = [*c.MODELS, ('gold', 'host-state-p0.bin')]
        asm = ['.section .rodata.fixture,"a"', '.balign 16']
        for label, name in embedded:
            asm.extend([f'.global fixture_{label}', f'fixture_{label}:', f'.incbin "{fixture / name}"',
                        f'.global fixture_{label}_end', f'fixture_{label}_end:', '.balign 16'])
        (source / 'fixture.S').write_text('\n'.join(asm) + '\n')
        actual = {str(p.relative_to(source)): digest(p) for p in source.rglob('*') if p.is_file() and not p.is_relative_to(source / 'repo')}
        tools = read(parent / 'tools.json'); save(output / 'tools.json', tools)
        for tool in tools.values(): need(digest(tool['path']) == tool['sha256'], 'same actual tool')
        keys = ('CFLAGS', 'CPPFLAGS', 'CXXFLAGS', 'ASFLAGS', 'LDFLAGS', 'CC_OPT', 'MAKEFLAGS', 'MFLAGS',
                'CC', 'AS', 'LD', 'OBJCOPY', 'OBJDUMP', 'ARCH', 'MARCH', 'LIBS', 'PREBUILD')
        clean = ['env', *[v for k in keys for v in ('-u', k)], 'AM_HOME=' + str(am), 'LINUX_GNU_TOOLCHAIN=1']
        archives = [p for p in external if Path(p).name == 'libm.a']; need(len(archives) == 1, 'same static libm')
        command([*clean, tools['make']['path'], '--trace', '--output-sync=target', '-C', source,
            'ARCH=riscv64-xs', 'MARCH=rv64gv', 'CROSS_COMPILE=' + tools['gcc']['path'][:-3],
            'FORWARD_OBJ_ROOT=' + str(output / 'objects'), 'BINARY=' + str(output / PREFIX),
            'MATH_ARCHIVE=' + archives[0], 'FULL_ERRNO_OFFSET=' + str(record['tls_errno_offset']),
            '-o', 'am', '-o', 'klib', '-j1', 'image'], output, 'target-build', timeout=300)
        command([tools['readelf']['path'], '-W', '-h', '-A', '-l', '-s', '-r', output / (PREFIX + '.elf')], output, 'metadata')
        command([tools['objdump']['path'], '-drwC', output / (PREFIX + '.elf')], output, 'disassembly')
        elf, inspection = inspect(output, record)
        need(digest(source / CORE) == digest(output / CORE) == record['artifacts'][CORE] and
             not list((output / 'objects').rglob('consumer*.o')), 'same complete core linked without recompilation')
        plans = []; image = (output / (PREFIX + '.bin')).read_bytes()
        for symbol, name, size in (('target_report', 'report.bin', 512), ('target_guarded', 'guarded-state.bin', S + 32),
                                   ('team_tls_area', 'tls.bin', 96)):
            address, length, *_ = elf.symbols[symbol]
            need(length == size and image[address - 0x80000000:address - 0x80000000 + size] == bytes(size), 'complete zero storage: ' + name)
            plans.append((name, address, size))
        for label, name in embedded:
            address = elf.symbols['fixture_' + label][0]; raw = (fixture / name).read_bytes()
            need(elf.symbols['fixture_' + label + '_end'][0] - address == len(raw) and elf.read(address, len(raw)) == raw, 'whole linked model/gold')
            plans.append(('gold-after.bin' if label == 'gold' else name.replace('.bin', '-after.bin'), address, len(raw)))
        address, length, *_ = elf.symbols['target_control']; offset = address - 0x80000000
        need(length == 12 and image[offset:offset + 12] == struct.pack('<3I', 4, 0, 1), 'exact explicit three controls')
        plans.append(('control.bin', address, length))
        (output / 'dump-plan.txt').write_text(''.join(f'{name} {address:x} {size}\n' for name, address, size in plans))
        for path, value in external.items(): need(digest(path) == value, 'external input unchanged after build')
        for rel, value in pins.items(): need(digest(REPO / rel) == digest(source / 'repo' / rel) == value, 'source unchanged after build')
        for name, value in actual.items(): need(digest(source / name) == value, 'actual source unchanged after build')
        for name, value in record['fixtures'].items(): need(digest(fixture / name) == value, 'fixture unchanged after build')
        for tool in tools.values(): need(digest(tool['path']) == tool['sha256'], 'tool unchanged after build')
        inspection.update(contract=CONTRACT, status=STATIC, source_pins=pins, external_pins=external,
            actual_source_pins=actual, fixtures=record['fixtures'], kernel_identity=record['kernel_identity'],
            qualified_build=str(parent), qualified_campaign=str(campaign), qualified_consumer_object_sha256=digest(output / CORE),
            norm_build=record['norm_build'], am_home=str(am), dump_plan=plans, control_offset=offset,
            expected_flags={str(m): qualified['validations'][label]['flags'][0] for m, label in ((3, 'fr-cache'), (4, 'ta-cache'))},
            artifacts={name: digest(output / name) for name in (PREFIX + '.elf', PREFIX + '.bin', CORE,
                'dump-plan.txt', 'derivation.json', 'metadata.stdout.log', 'disassembly.stdout.log')},
            exact_flags_guard=1, target_emu_runs=0, reference_runs=0, performance_qualified=False)
        save(output / 'result.json', inspection); status.update(status=STATIC, result_sha256=digest(output / 'result.json'))
        return inspection
    except BaseException as error:
        status.update(status='FAILED', error=repr(error)); raise
    finally:
        status['finished'] = c.base.f.h.now(); save(output / 'state.json', status)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'parent', 'campaign'): parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(); os.sched_setaffinity(0, [min(os.sched_getaffinity(0))])
    result = build(*(getattr(args, name).resolve() for name in ('output', 'parent', 'campaign')))
    print(json.dumps({k: result[k] for k in ('contract', 'status', 'image_bytes', 'heap_start', 'failure_traps', 'success_trap')}, indent=2))
