"""Bounded mixed-wrapper Q288 target correctness and cost observations."""
from pathlib import Path, PurePosixPath
import argparse
import importlib.util
import json
import os
import shlex
import struct
import tempfile
from types import SimpleNamespace
import zipfile

HERE = Path(__file__).resolve().parent
Q = HERE.parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


base = load('acc8_target_base', Q/'run.py')
gen = load('acc8_target_generate', HERE/'generate.py')
fixture_gen = gen.parent
ROOT, g, parent, old = base.ROOT, base.g, base.parent, base.old
PARENT_DIR = base.PARENT_DIR
CONTRACT, MAX_CYCLES, GENERATED = gen.CONTRACT, gen.MAX_CYCLES, gen.FILES
read, now, digest, adapt = base.read, base.now, base.digest, base.adapt
OWN = ('main.c', 'generate.py', 'run.py', 'archive.py', 'CONTRACT.md')
SCREEN = HERE.parent/'evidence/screen-v1/raw.zip'
SCREEN_SHA = 'b3fc245f9f2f5a63e6ce1e65cf984ca44c5df15910d995f6f65d7e3add247cac'
REFERENCE_ELFS = {
    'baseline/vdot-perf.elf': '7f2c3d6de93f979cc252379a8fe2147e0d7ff121b0a38151f4604ee832884f26',
    'run/build-01/vdot-perf.elf': '8fcb7bb4fda1ce7dcc2cf4c41f83bfed3733cee363df2cf2a3d760a737103888',
}


def sources(repo):
    found = base.sources(repo)
    paths = [HERE/n for n in OWN] + [HERE.parent/'q288.c', HERE.parent/'CONTRACT.md', SCREEN]
    paths += [PARENT_DIR/'archive.py', Q.parent/'fixed-weight/archive.py',
              repo/'team/optimizations/o2/repro/evidence/clean-reproduction-v1/analysis/detached-audit.py']
    found.update({p.relative_to(repo).as_posix(): g.sha(p) for p in paths})
    return found


def generate(repo, out):
    return gen.generate(repo, out)


def reference_images():
    g.require(g.sha(SCREEN) == SCREEN_SHA, 'fixed original/acc8 byte archive')
    images = []
    with zipfile.ZipFile(SCREEN) as z:
        for name, pin in REFERENCE_ELFS.items():
            raw = z.read(name)
            g.require(digest(raw) == pin, 'fixed archived reference ELF')
            images.append(g.ELF(raw))
    return images


def path(elf, row, fixture, dataset=0):
    return base.traced.path(elf, row, fixture, dataset,
        scale_order='group' if row['variant'] == 'acc8' else 'row', profile=True)


def paths_for_plan(elf, manifest):
    fixture = fixture_gen.fixtures()
    paths, details = {}, {}
    for step in manifest['plan']:
        row = manifest['rows'][step['index']]
        key = str(row['id'])+':'+str(step['dataset'])
        if key in details:
            continue
        stream, detail = path(elf, row, fixture, step['dataset'])
        if row['id'] in paths:
            g.require(paths[row['id']] == stream, 'input-independent actual PC/word path')
        else:
            paths[row['id']] = stream
        counters = [i for i, (_, w) in enumerate(stream) if w in base.traced.COUNTERS]
        g.require(len(counters) == 4, 'four exact counter sites')
        details[key] = dict(detail, dataset=step['dataset'],
            expected_csr_instret=counters[3]-counters[0],
            path_sha256=digest(b''.join(struct.pack('<QI', pc, w) for pc, w in stream)))
    return paths, details


def compiled_arrays(elf, manifest):
    f = fixture_gen.fixtures()
    arrays = {
        'q_weights': fixture_gen.bytes8(f['weight']),
        'q_weight_scale': fixture_gen.bytes32(f['weight_scale']),
        'q_inputs': b''.join(fixture_gen.bytes8(x) for x in f['inputs']),
        'q_input_scale': b''.join(fixture_gen.bytes32(x) for x in f['input_scale']),
        'q_golden': b''.join(fixture_gen.bytes32(x) for x in f['golden']),
        'q_order': struct.pack('<10I', *gen.ORDER),
        'q_datasets': struct.pack('<10I', *gen.DATASETS),
        'q_methods': struct.pack('<4I', *gen.METHODS),
        'q_wrappers': struct.pack('<4Q', *(elf.symbols[n][0] for n in gen.WRAPPERS)),
        'split_entries': struct.pack('<6Q', *(elf.symbols[n][0] for n in fixture_gen.NEW)),
    }
    for name, raw in arrays.items():
        g.require(elf.symbol_data(name) == raw, 'compiled array: '+name)
    g.require(tuple(s['index'] for s in manifest['plan'][1:]) == gen.ORDER and
              tuple(s['dataset'] for s in manifest['plan'][1:]) == gen.DATASETS,
              'fixed ten-Q manifest plan')
    return {n: digest(v) for n, v in arrays.items()}


def compiler_commands(log, record):
    result = base.compiler_commands(log, record)
    root = PurePosixPath(record['build_root'])
    gcc = record['toolchain']['gcc']['path']
    src, obj = (str(root/n) for n in ('source/q288_baseline.c', 'objects/q288_baseline.o'))
    found = [shlex.split(s) for s in log.splitlines() if s.startswith(gcc+' ') and src in shlex.split(s)]
    expected = [str(root/'source/q288_baseline.c') if v == str(root/'source/q288.c') else
                str(root/'objects/q288_baseline.o') if v == str(root/'objects/q288.o') else v
                for v in result['q288']]
    g.require(len(found) == 1 and found[0] == expected and found[0][-4:] == ['-c','-o',obj,src],
              'old and acc8 actual separate compilation differs only in source/object path')
    result['q288_baseline'] = found[0]
    return result


def verification(repo, build):
    record = read(build/'build.json')
    g.require(record['contract'] == CONTRACT and record['software_files'] == sources(repo) and record['exit_code'] == 0,
              'target build identity')
    for rel, pin in record['software_files'].items():
        g.require(g.sha(build/'source/repo'/rel) == pin, 'snapshot drift: '+rel)
    g.require(set(record['artifacts']) == {'vdot-perf.elf','vdot-perf.bin','gemv-reference.o'}, 'artifact inventory')
    for name, pin in record['artifacts'].items():
        g.require(g.sha(build/name) == pin, 'artifact drift')
    with tempfile.TemporaryDirectory(prefix='acc8-target-regenerate-') as tmp:
        fresh = Path(tmp)/'source'; manifest = generate(repo, fresh)
        for name in GENERATED:
            g.require((fresh/name).read_bytes() == (build/'source'/name).read_bytes(), 'source regeneration: '+name)
    elf = g.ELF((build/'vdot-perf.elf').read_bytes())
    g.load('acc8_target_executable', repo/'team/optimizations/o2/r2-select/entry_c_api.py').executable(elf)
    g.require(elf.binary() == (build/'vdot-perf.bin').read_bytes(), 'ELF/BIN mismatch')
    g.require(elf.symbol_data('q_fault_probe') == struct.pack('<11I', *fixture_gen.PROBE_WORDS),
              'isolated fault probe exact words')
    g.require(g.sha(build/'gemv-reference.o') == old.OBJECT_SHA, 'old full reference object differs')
    refs = [g.ELF((build/'gemv-reference.o').read_bytes()),
            g.ELF(fixture_gen.raw(repo, str(fixture_gen.S0/'gemv-reference.o.gz'))),
            g.ELF(fixture_gen.raw(repo, str(fixture_gen.FIRST/'evidence/firstdot-v1/library/member-extract/stdout.log')))]
    certs = []
    for i, row in enumerate(fixture_gen.LEAVES):
        reference = refs[1 if i in (1,2) else 2 if i == 4 else 0]
        certs.append(fixture_gen.machine_certificate(reference.symbol_data(row[0]),
                                                     elf.symbol_data(fixture_gen.NEW[i]), i))
    original, acc8 = reference_images()
    bodies = {}
    for name, before, before_name in [('q288_baseline_full', original, 'q288_full'),
                                      ('q288_full', acc8, 'q288_full'), ('q288_pack', original, 'q288_pack')]:
        body = elf.symbol_data(name)
        g.require(body == before.symbol_data(before_name), 'unchanged complete wrapper/pack machine body: '+name)
        bodies[name] = digest(body)
    g.require(elf.symbol_data('q288_pack') == acc8.symbol_data('q288_pack'), 'shared exact pack body')
    for name in fixture_gen.NEW:
        g.require(elf.symbol_data(name) == original.symbol_data(name) == acc8.symbol_data(name), 'all six exact leaf bodies')
    arrays = compiled_arrays(elf, manifest)
    _, details = paths_for_plan(elf, manifest)
    commands = record['commands']
    expected = old.build_commands({k:v['path'] for k,v in record['toolchain'].items()}, PurePosixPath(record['build_root']))
    g.require(len(commands) == 3, 'build command inventory')
    for (label, argv), cmd in zip(expected, commands):
        g.require(cmd.get('process_started') is True and cmd.get('exit_code') == 0 and not cmd.get('timed_out') and
            cmd['command'] == argv and cmd['cwd'] == record['source_root'] and read(build/label/'command.json') == cmd and
            cmd['raw_sha256'] == {n:g.sha(build/label/n) for n in ('stdout.log','stderr.log')}, 'actual build command evidence')
    compiled = compiler_commands((build/'make-command/stdout.log').read_text(), record)
    g.require(record['parent_identity_sha256'] == parent.PARENT_IDENTITY_SHA and record['am_revision'] == old.AM_COMMIT,
              'fixed parent/AM identity')
    return dict(status='ACC8_TARGET_ELF_AND_DATASET_PATH_PASS', contract=CONTRACT,
        image_sha256=g.sha(build/'vdot-perf.bin'), certificates=certs, paths=details,
        unchanged_function_sha256=bodies, compiled_array_sha256=arrays,
        windows=len(manifest['plan']), actual_c_compilation=compiled,
        runtime_not_run=True, performance_qualified=False)


def selection(samples, manifest):
    observations = []
    for sample in samples[1:]:
        row = manifest['rows'][sample['id']]
        observations.append(dict(seq=sample['seq'], variant=row['variant'], leaf=row['leaf'],
            dataset=sample['dataset'], cycles=sample['cycles'], instructions=sample['instructions']))
    differences = {}
    for old_id, new_id, name in ((0,2,'vdot'), (1,3,'rvv4')):
        before = [s['instructions'] for s in samples if s['id'] == old_id]
        after = [s['instructions'] for s in samples if s['id'] == new_id]
        g.require(len(before) == 1 and len(after) == 4 and len(set(after)) == 1,
                  'actual per-wrapper instruction cardinality')
        g.require(before[0]-after[0] == 19354, 'actual unchanged-path instruction reduction')
        differences[name] = before[0]-after[0]
    return dict(decision='TARGET_FUNCTIONAL_AND_COST_DIAGNOSTIC_PASS',
        observations=observations, instruction_differences=differences,
        pack_cycles=samples[0]['cycles'], pack_instructions=samples[0]['instructions'],
        performance_qualified=False, selected_method=None, stable_default_changed=False,
        statistical_scope='fixed order; unequal call histories; replay is not an extra sample',
        application_scope='synthetic prequantized Q; no full-model/token claim')


def normal(repo, build, run, receipt):
    g.require(receipt.get('process_started') is True and receipt.get('exit_code') == 0 and not receipt.get('timed_out'),
              'complete execution required')
    manifest = read(build/'source/manifest.json')
    stdout, stderr = ((run/n).read_text() for n in ('stdout.log','stderr.log'))
    gate = g.load('acc8_target_failures', repo/'team/optimizations/o1/audit/runtime_gate.py')
    fatal = g.load('acc8_target_fatal', repo/'team/optimizations/o2/fullcore/recheck.py')
    observer = g.load('acc8_target_protocol', repo/'team/optimizations/o2/fullcore/analyze.py')
    for stream in (stdout, stderr):
        gate.validate_failure_markers(stream); fatal.reject_fatal_output(stream)
    _, uart = observer.extract_events_and_uart(stderr+stdout)
    gate.validate_failure_markers(uart); fatal.reject_fatal_output(uart)
    plain = gate.normalize_console(uart)
    counter = g.load('acc8_target_counters', repo/'team/workloads/unified-vdot/check.py')
    elf = g.ELF((build/'vdot-perf.elf').read_bytes())
    paths, details = paths_for_plan(elf, manifest)
    counter.walk = lambda path: path
    events = counter.parse_events(stderr)
    samples = counter.trace_windows(events, manifest, paths)
    windows, current = [], None
    for event in events['RETIRE']:
        if event['word'] == base.traced.START: current = []
        if current is not None: current.append(event)
        if event['word'] == base.traced.STOP: windows.append(current); current = None
    for records, step in zip(windows, manifest['plan']):
        stream = paths[step['index']]; pos = 0
        for event in records:
            covered = stream[pos:pos+event['count']]
            if event['count'] > 1:
                g.require(not any(w&127 in (0x63,0x6f,0x67) for _,w in covered), 'control hidden by ROB compression')
            pos += event['count']
    for sample, step in zip(samples, manifest['plan']):
        sample.update({k:step[k] for k in ('dataset','block','role')})
        row = manifest['rows'][step['index']]
        sample.update(kind=row['kind'], variant=row['variant'], leaf=row['leaf'])
        g.require(sample['instructions'] == details[str(row['id'])+':'+str(step['dataset'])]['expected_csr_instret'],
                  'dataset-bound actual CSR instruction count')
    expected = [f'Q_BEGIN contract={CONTRACT} windows=11', 'Q_FUNCTIONAL calls=10 controls=6 outputs=2880']
    expected += [f"QW {s['seq']} {s['cycles']} {s['instructions']}" for s in samples]
    expected += ['Q_END windows=11 full_calls=10 leaf_calls=3240 probe_dots=1 failures=0']
    actual = [line for line in plain.splitlines() if line.startswith(('Q_', 'QW '))]
    g.require(actual == expected and plain.count('HIT GOOD TRAP') == 1, 'raw UART/counter/oracle evidence differs')
    analysis = observer.analyze(stderr+stdout)
    g.require(analysis['status'] == 'O2_TRACE_PASS' and analysis['schema']['slots'] == 2 and
        all(analysis.get(k) == 0 for k in ('pending_count','pending_div_count','unfinished_rob_count')) and
        analysis['counts'].get('COMMIT') == manifest['expected_dots'], 'complete O2 protocol/commit count')
    return dict(status='TARGET_FUNCTIONAL_AND_COST_DIAGNOSTIC_PASS', contract=CONTRACT, windows=len(samples),
        functional_calls=10, timed_q_calls=10, judge_fault_controls=6,
        committed_vdot=analysis['counts']['COMMIT'], counter_enqueues=len(events['COUNTER_ENQUEUE']),
        csr_samples=len(events['CSR_SAMPLE']), samples=samples, selection=selection(samples, manifest),
        hardware_changed=False, stable_default_changed=False, performance_qualified=False)


def build(repo, identity, out):
    with adapt(old, CONTRACT=CONTRACT, sources=sources, generate=generate, verification=verification):
        return old.build(repo, identity, out)


def run(repo, identity, build_dir, out, operation):
    with adapt(base.up, CONTRACT=CONTRACT, MAX_CYCLES=MAX_CYCLES, GENERATED=GENERATED,
               sources=sources, verification=verification,
               gen=SimpleNamespace(NEW=('q_fault_probe',)), normal=normal):
        return base.up.run(repo, identity, build_dir, out, operation)


def elf_controls(build_dir, out):
    positive = verification(ROOT, build_dir)
    out.mkdir(parents=True, exist_ok=False)
    blob = (build_dir/'vdot-perf.elf').read_bytes(); elf = g.ELF(blob)
    manifest = read(build_dir/'source/manifest.json')
    mutations = []
    for name, at, size, replacement in (
        ('q_wrappers', 0, 8, elf.symbols['q288_full'][0]),
        ('q_datasets', 16, 4, 0), ('q_golden', 0, 4, 1)):
        raw = elf.symbol_data(name); offset = blob.find(raw)
        g.require(offset >= 0 and blob.find(raw, offset+1) < 0, 'unique array mutation body')
        changed = bytearray(blob)
        changed[offset+at:offset+at+size] = replacement.to_bytes(size, 'little')
        try:
            compiled_arrays(g.ELF(bytes(changed)), manifest)
        except ValueError as error:
            g.require(str(error) == 'compiled array: '+name, 'specific mixed-image array rejection')
            (out/(name+'.elf')).write_bytes(changed)
            mutations.append(dict(name=name, offset=offset+at, size=size, error=str(error), sha256=digest(changed)))
        else: raise ValueError('array mutant accepted: '+name)
    body = elf.symbol_data('q288_full'); offset = blob.find(body)
    g.require(offset >= 0 and blob.find(body, offset+1) < 0, 'unique acc8 body')
    restores = [(i*4,w) for i,(w,) in enumerate(struct.iter_unpack('<I', body))
                if w&127 == 7 and (w>>12)&7 == 3 and (w>>15)&31 == 2
                and (w>>7)&31 in (8,9,18,19,20,21,22,23)]
    g.require(len(restores) == 8, 'eight actual LP64D floating restores')
    at, word = restores[0]
    mutant = (word&0x000fffff) | ((((word>>20)-8)&4095)<<20)
    changed = bytearray(blob); struct.pack_into('<I', changed, offset+at, mutant)
    try:
        path(g.ELF(bytes(changed)), manifest['rows'][2], fixture_gen.fixtures())
    except ValueError as error:
        g.require(str(error) == 'FP callee-saved registers balanced', 'specific mixed-image ABI rejection')
        (out/'fp-restore.elf').write_bytes(changed)
        mutations.append(dict(name='fp-restore', pc=elf.symbols['q288_full'][0]+at,
            original_word=hex(word), mutated_word=hex(mutant), error=str(error), sha256=digest(changed)))
    else: raise ValueError('FP restore mutant accepted')
    result = dict(status='ACC8_TARGET_MIXED_ELF_CONTROLS_PASS', contract=CONTRACT,
                  positive=positive, mutations=mutations, new_emu_runs=0)
    g.save(out/'result.json', result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--action', choices=('build','verify','elf-controls','run'), required=True)
    p.add_argument('--identity', type=Path)
    p.add_argument('--build', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--operation-id')
    args = p.parse_args(); out = args.output.resolve()
    g.require(not out.exists(), 'fresh target output required')
    identity = (args.identity or ROOT/parent.REPRO/'evidence/clean-reproduction-v1/reports/identity-02.json').resolve()
    cfg = parent.parent_identity(ROOT, identity)['configuration']
    roots = [ROOT, identity.parent] + [cfg[k] for k in ('am_home','hardware_source','build_record')]
    if args.build: roots.append(args.build.resolve())
    parent.outside_inputs(out, roots)
    if os.name == 'posix': os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    if args.action == 'build': result = build(ROOT, identity, out)
    elif args.action == 'verify':
        g.require(args.build is not None, 'build required')
        result = verification(ROOT, args.build.resolve()); g.save(out, result)
    elif args.action == 'elf-controls':
        g.require(args.build is not None, 'build required')
        result = elf_controls(args.build.resolve(), out)
    else:
        g.require(args.build and args.operation_id, 'build/operation required')
        result = run(ROOT, identity, args.build.resolve(), out, args.operation_id)
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
