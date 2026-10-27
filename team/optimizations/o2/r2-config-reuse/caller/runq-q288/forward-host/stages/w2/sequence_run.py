"""Bounded full-range correctness for the unchanged W2 consumer object.

The separate team adapter differs only in its API-call budget ceiling. All
official reference code, arithmetic and terminal decisions remain unchanged.
This is reference correctness; no target timing or new EMU is involved.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, re, resource, shlex, shutil
import signal, struct, sys, types

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


b = load('w2_sequence_build_support', HERE / 'sequence_build.py')
a = b.a
need, read, save, digest, command = b.need, b.read, b.save, b.digest, b.command
CONTRACT, REPO, S = b.CONTRACT, b.REPO, b.S
CASES = [('negative', True, 1000000000, 120), ('normal', False, 48000000000, 2400)]
CAP_BEFORE, CAP_AFTER = 'UINT64_C(10000000000)', 'UINT64_C(48000000000)'
PARENT_SOURCE = '6ea9a43ddfa4420f00c7e62f101035e1e7fbf85610e607c4d7762b96c803bd2b'
MAGIC = 0x5232573253455131


def verify(files):
    for path, value in files.items():
        need(digest(path) == value, 'unchanged frozen input: ' + path)


def adapter(output, parent):
    need(not output.exists() and not any(output.is_relative_to(p) for p in (REPO, parent)), 'new isolated adapter')
    original = read(parent / 'build.json')
    need(original['status'] == 'REFERENCE_ADAPTER_BUILD_PASS' and
         original['inputs_sha256'] == digest(parent / 'inputs.json'), 'original actually built team adapter')
    files = dict(read(parent / 'inputs.json')['files'])
    for name, value in original['artifacts'].items():
        files[str(parent / name)] = value
    for name in ('build.json', 'inputs.json'):
        files[str(parent / name)] = digest(parent / name)
    files[str(HERE / 'sequence_run.py')] = digest(HERE / 'sequence_run.py')
    files[str(HERE / 'sequence-CONTRACT.md')] = digest(HERE / 'sequence-CONTRACT.md')
    verify(files)
    raw = (parent / 'reference_runner.c').read_bytes()
    need(hashlib.sha256(raw).hexdigest() == PARENT_SOURCE and raw == (HERE.parent / 'target/reference_runner.c').read_bytes(),
         'exact unchanged team adapter source, independent of official NEMU')
    text = raw.decode()
    need(text.count(CAP_BEFORE) == 1 and CAP_AFTER not in text, 'one sole budget ceiling literal')
    derived = text.replace(CAP_BEFORE, CAP_AFTER)
    need(derived.replace(CAP_AFTER, CAP_BEFORE).encode() == raw, 'complete source reverses exactly')
    old_command = read(parent / 'compile.command.json')
    need(old_command['exit_code'] == 0 and old_command['status'] == 'exited' and
         old_command['direct_child_reaped'] is True and old_command['process_group_absent_after_exit'] is True,
         'original successful compiler receipt')
    compiler = Path(shutil.which(old_command['argv'][0])).resolve()
    files[str(compiler)] = digest(compiler)
    output.mkdir(parents=True)
    state = dict(contract=CONTRACT, status='BUILDING', started=a.b.old.f.h.now(), cpu_affinity=sorted(os.sched_getaffinity(0)))
    save(output / 'state.json', state)
    try:
        (output / 'parent').mkdir()
        for name in (*original['artifacts'], 'inputs.json', 'build.json'):
            shutil.copyfile(parent / name, output / 'parent' / name)
        (output / 'reference_runner.c').write_text(derived)
        shutil.copyfile(parent / 'nemu.config', output / 'nemu.config')
        replacements = {str(parent / name): str(output / name) for name in ('reference_runner.c', 'runner.d', 'reference-runner')}
        argv = [str(compiler), *[replacements.get(v, v) for v in old_command['argv'][1:]]]
        need(all(old_command['argv'].count(path) == 1 for path in replacements) and
             argv[-2:] == ['-o', str(output / 'reference-runner')], 'only explicit source/output/compiler path changes')
        proof = dict(parent_source_sha256=PARENT_SOURCE, source_sha256=digest(output / 'reference_runner.c'),
            exact_parent_reverse=True, changed_occurrences=1, old_max_api_calls=10000000000,
            new_max_api_calls=48000000000, original_argv=old_command['argv'], actual_argv=argv)
        save(output / 'derivation.json', proof)
        command(argv, output, 'compile', timeout=60)
        dependencies = lambda p: set(shlex.split(p.read_text().replace('\\\n', ' ').split(':', 1)[1]))
        expected = {replacements.get(v, v) for v in dependencies(parent / 'runner.d')}
        need(dependencies(output / 'runner.d') == expected, 'identical actual non-system compiler dependencies apart from derived source')
        for path in expected:
            files[path] = digest(path)
        verify(files)
        save(output / 'inputs.json', dict(files=files, parent_adapter=str(parent),
             scope='new 48G team-adapter budget only; original normal reference unchanged'))
        artifacts = {p.relative_to(output).as_posix(): digest(p) for p in output.rglob('*') if p.is_file() and
                     p.name not in ('state.json', 'inputs.json')}
        # The parent inputs.json is also an ordinary inherited artifact.
        artifacts['parent/inputs.json'] = digest(output / 'parent/inputs.json')
        result = dict(contract=CONTRACT, status='W2_SEQUENCE_ADAPTER_BUILD_PASS', parent_adapter=str(parent),
            inputs_sha256=digest(output / 'inputs.json'), artifacts=artifacts, derivation=proof,
            compiler=dict(path=str(compiler), sha256=digest(compiler)), max_api_calls=48000000000,
            original_reference_unchanged=True, reference_runs=0, performance_qualified=False)
        save(output / 'build.json', result)
        state.update(status=result['status'], result_sha256=digest(output / 'build.json'))
        return result
    except BaseException as error:
        state.update(status='FAILED', error=repr(error))
        raise
    finally:
        state['finished'] = a.b.old.f.h.now()
        save(output / 'state.json', state)


def inputs(build, adapted, original_adapter, identity_path):
    record = read(build / 'result.json')
    need(record['contract'] == CONTRACT and record['status'] == b.STATIC_PASS, 'distinct actual sequence build')
    parent, files, identity, checker = a.inputs(Path(record['qualified_api_build']), original_adapter, identity_path)
    need(record['qualified_consumer_object_sha256'] == parent['qualified_consumer_object_sha256'], 'unchanged qualified core object')

    def pin(path, value):
        path = str(Path(path).resolve())
        need(path not in files or files[path] == value, 'no runtime identity rebinding')
        files[path] = value

    for path, value in record['external_pins'].items():
        pin(path, value)
    for rel, value in record['source_pins'].items():
        pin(REPO / rel, value); pin(build / 'source/repo' / rel, value)
    for group, folder in (('actual_source_pins', build / 'source'), ('fixtures', build / 'fixture'), ('artifacts', build)):
        for name, value in record[group].items():
            pin(folder / name, value)
    adapted_build = read(adapted / 'build.json')
    adapted_state = read(adapted / 'state.json')
    need(adapted_build['contract'] == CONTRACT and adapted_build['status'] == adapted_state['status'] ==
         'W2_SEQUENCE_ADAPTER_BUILD_PASS' and adapted_state.get('finished') and
         adapted_build['parent_adapter'] == str(original_adapter) and adapted_build['max_api_calls'] == 48000000000 and
         adapted_build['inputs_sha256'] == digest(adapted / 'inputs.json'), 'separate completed budget-only adapter')
    need((adapted / 'reference_runner.c').read_text().replace(CAP_AFTER, CAP_BEFORE).encode() ==
         (original_adapter / 'reference_runner.c').read_bytes() and
         digest(original_adapter / 'reference_runner.c') == PARENT_SOURCE, 'whole exact budget-only source derivation')
    for path, value in read(adapted / 'inputs.json')['files'].items():
        pin(path, value)
    for name, value in adapted_build['artifacts'].items():
        pin(adapted / name, value)
    compiled = read(adapted / 'compile.command.json')
    need(compiled['exit_code'] == 0 and compiled['status'] == 'exited' and
         compiled.get('direct_child_reaped') is True and compiled.get('process_group_absent_after_exit') is True and
         compiled['argv'] == adapted_build['derivation']['actual_argv'], 'actual completed new adapter compilation')
    for path in (build / 'result.json', build / 'tools.json', adapted / 'build.json', adapted / 'inputs.json',
                 adapted / 'state.json', HERE / 'sequence_run.py', *a.module_files()):
        pin(path, digest(path))
    for tool in read(build / 'tools.json').values():
        pin(tool['path'], tool['sha256'])
    a.b.old.f.executable(build / (b.PREFIX + '.elf'), build / (b.PREFIX + '.bin'),
        build / 'metadata.stdout.log', record['tls_errno_offset'])
    functions = a.b.old.p.kernel_bytes(build / (b.PREFIX + '.elf'), b.KERNELS)
    need(len(functions) == 4, 'all four actual sequence kernels')
    for name, raw in functions.items():
        need(len(raw) == record['kernel_identity']['functions'][name]['bytes'] and
             hashlib.sha256(raw).hexdigest() == record['kernel_identity']['functions'][name]['sha256'], 'exact whole sequence kernel')
    checker.verify_files(files)
    return record, files, identity, checker


def image(build, record, negative):
    raw = bytearray((build / (b.PREFIX + '.bin')).read_bytes())
    offset = record['control_offset']
    need(raw[offset:offset + 8] == struct.pack('<2I', 0, 256), 'actual fixed sequence controls')
    raw[offset:offset + 4] = struct.pack('<I', int(negative))
    return raw, dict(base_sha256=record['artifacts'][b.PREFIX + '.bin'], offset=offset,
        controls=[int(negative), 256], sha256=hashlib.sha256(raw).hexdigest())


def validate(build, dest, record, receipt, negative):
    calls, seconds = (1000000000, 120) if negative else (48000000000, 2400)
    need(receipt.get('process_started') is True and receipt.get('direct_child_reaped') is True and
         receipt.get('process_group_absent_after_exit') is True and not receipt.get('residual_process_group') and
         not receipt.get('timed_out') and receipt['exit_code'] == (2 if negative else 0) and
         receipt['max_api_calls'] == calls and receipt['wall_limit_seconds'] == seconds,
         'complete actually bounded reference process')
    expected, controls = image(build, record, negative)
    need((dest / 'image.bin').read_bytes() == expected and read(dest / 'image-control.json') == controls,
         'same actual ELF with only the declared negative control changed')
    terminal, abi = read(dest / 'reference-result.json'), read(dest / 'abi.json')
    need(terminal['state'] == 2 and terminal['reason'] == ('bad_trap' if negative else 'good_trap') and
         terminal['halt_ret'] == (94 if negative else 0) and 0 < terminal['retired'] <= terminal['api_calls'] <= calls and
         terminal['memory_dumps'] == 10 and terminal['xiangshan_cycles_measured'] is False, 'exact reference terminal decision')
    need(abi['register_bytes'] == abi['header_span'] == 1400 and abi['initial_pc'] == 0x10000000 and
         abi['initial_mode'] == 3, 'original reset and complete register ABI')
    text = re.sub(r'\x1b\[[0-9;]*m', '', (dest / 'stdout.log').read_text())
    need(not (dest / 'stderr.log').read_bytes() and not any(v in text.lower() for v in
         ('pma check failed', 'critical error', 'reference_adapter_reject', 'abort')), 'no unexplained reference failure')
    traps = [line for line in text.splitlines() if 'HIT ' in line and ' TRAP' in line]
    need(len(traps) <= 1, 'at most one canonical trap')
    for line in traps:
        match = re.fullmatch(r'(?:\[[^\]\r\n]+\]\s*)?nemu: HIT (GOOD|BAD) TRAP at pc = (0x[0-9a-fA-F]+)', line)
        need(match is not None and match[1] == ('BAD' if negative else 'GOOD') and
             int(match[2], 16) == terminal['halt_pc'], 'console and actual terminal agree')
    sizes = {name: size for name, _, size in record['dump_plan']}
    need(len(sizes) == 10 and sizes['report.bin'] == 512 and sizes['states.bin'] == 3 * (S + 32) and
         sizes['flags.bin'] == 6144 and sizes['tokens.bin'] == 1024 and sizes['prefix-gold-after.bin'] == 3 * S,
         'complete fixed sequence dump schema')
    sizes.update({'initial-registers.bin': 1400, 'final-registers.bin': 1400,
                  'initial-csrs.bin': 32768, 'final-csrs.bin': 32768})
    need({path.name for path in dest.glob('*.bin')} == set(sizes) | {'image.bin'}, 'exact complete raw binary inventory')
    for name, size in sizes.items():
        need((dest / name).stat().st_size == size, 'complete raw output: ' + name)
    for _, name in a.MODELS:
        need(digest(dest / name.replace('.bin', '-after.bin')) == record['fixtures'][name], 'whole original model unchanged')
    need(digest(dest / 'prefix-gold-after.bin') == record['fixtures']['prefix_gold.bin'], 'complete independent host prefix unchanged')
    report = struct.unpack('<64Q', (dest / 'report.bin').read_bytes())
    expected_report = [0] * 64
    expected_report[:10] = [MAGIC, 1, int(negative), 94 if negative else 0, 256, 0 if negative else 255,
                           0 if negative else 256, 3 if negative else 768, 1 if negative else 512, 152476 if negative else 0]
    expected_report[10:12] = [report[10], 16]
    expected_report[12], expected_report[14], expected_report[16] = (4, 0, 1) if negative else (0, 3, 3)
    need(tuple(expected_report) == report and report[10] & 0x6000 and report[10] & 0x600,
         'actual complete position/call/comparison/guard/host-prefix/invalid-call report')
    flags = list(struct.iter_unpack('<3Q', (dest / 'flags.bin').read_bytes()))
    completed = 1 if negative else 256
    need(all(row[0] == row[1] == row[2] and row[0] >> 5 == 0 for row in flags[:completed]) and
         not any(any(row) for row in flags[completed:]), 'every actual RNE/flags triple and unused extent')
    api_flags = read(build / 'parent-api-validation.json')['expected_flags']
    prefix_flags = [api_flags[i] for i in (0, 2, 4)]
    need(all(flags[pos] == (prefix_flags[pos],) * 3 for pos in range(min(3, completed))), 'prefix flags equal qualified original paths')
    tokens = list(struct.unpack('<256i', (dest / 'tokens.bin').read_bytes()))
    plan = [1, 7, 19] + [(pos * 7919 + 1) % 32000 for pos in range(3, 256)]
    need(tokens == ([1] + [0] * 255 if negative else plan), 'complete actual token sequence and no negative continuation')
    raw = (dest / 'states.bin').read_bytes()
    guard = struct.pack('<2Q', *[0xb5e9c13f6a0742d8] * 2)
    states = []
    for which in range(3):
        part = raw[which * (S + 32):(which + 1) * (S + 32)]
        need(part[:16] == part[-16:] == guard, 'all three complete state guards')
        states.append(part[16:-16])
    if negative:
        gold = (build / 'fixture/host-state-p0.bin').read_bytes()
        bad = bytearray(gold); bad[152476] ^= 1
        need(states[0] == states[1] == gold and states[2] == bad, 'real last-logit bit failure, exact scalar and FR recovery input')
    else:
        need(states[0] == states[1] == states[2] and any(states[0]), 'all complete final scalar/FR/TA states agree')
    wanted_calls = list(range(1, 257)) + list(range(1000000, terminal['api_calls'] + 1, 1000000))
    if wanted_calls[-1] != terminal['api_calls']:
        wanted_calls.append(terminal['api_calls'])
    observed = []
    with (dest / 'steps.jsonl').open() as source:
        for line in source:
            need(len(line) <= 4096, 'bounded original adapter step row')
            row = json.loads(line)
            need(row['critical'] is False and row['mode'] == 3 and 0 <= row['retired'] <= row['call'], 'original progress row has no critical failure')
            observed.append(row['call'])
    need(observed == wanted_calls and row['state'] == 2 and row['pc'] == terminal['pc'] and
         row['retired'] == terminal['retired'], 'complete original adapter progress sampling and terminal row')
    return dict(contract=CONTRACT, status='EXPECTED_W2_SEQUENCE_REJECTION' if negative else 'W2_SEQUENCE_256_REFERENCE_PASS',
        negative=negative, positions_compared=0 if negative else 256, report=list(report), flags=[list(v) for v in flags],
        tokens=tokens, final_state_sha256=[hashlib.sha256(v).hexdigest() for v in states],
        raw_sha256={name: digest(dest / name) for name in (*sizes, 'steps.jsonl')},
        api_calls=terminal['api_calls'], retired=terminal['retired'], step_rows=len(observed),
        target_emu_runs=0, performance_qualified=False, independent_full_sequence_replay=False)


def run(build, adapted, original_adapter, identity_path, output):
    need(not output.exists() and len(os.sched_getaffinity(0)) == 1, 'new single-core sequence campaign')
    record, files, identity, checker = inputs(build, adapted, original_adapter, identity_path)
    a.old.r.parent.outside_inputs(output, [REPO, build, adapted, original_adapter, identity_path.parent,
        Path(record['qualified_api_build']), Path(record['qualified_api_campaign']), Path(record['am_home'])])
    _, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
    limit = 128 * 1024 * 1024
    need(hard == resource.RLIM_INFINITY or hard >= limit, 'whole image and dump size budget')
    resource.setrlimit(resource.RLIMIT_FSIZE, (limit, hard))
    output.mkdir(parents=True)
    save(output / 'runtime-inputs.json', files)
    a.old.snapshot_runtime(output, files)
    shutil.copyfile(identity_path, output / 'parent-identity.json')
    state = dict(contract=CONTRACT, status='RUNNING', started=a.b.old.f.h.now(), active_pid=None,
        cpu_affinity=sorted(os.sched_getaffinity(0)), records=[], target_emu_runs=0, performance_qualified=False)
    persist = lambda: save(output / 'state.json', state)
    persist(); validations = {}
    try:
        for label, negative, calls, seconds in CASES:
            dest = output / label; dest.mkdir()
            raw, controls = image(build, record, negative)
            (dest / 'image.bin').write_bytes(raw); del raw
            save(dest / 'image-control.json', controls)
            argv = [str(adapted / 'reference-runner'), identity['configuration']['reference'], str(dest / 'image.bin'),
                str(dest), 'builtin', str(calls), str(seconds), str(build / 'dump-plan.txt'), '1']
            receipt = dict(name=label, negative=negative, command=argv, cwd=str(dest), started=a.b.old.f.h.now(),
                process_started=False, exit_code=None, status='RUNNING', max_api_calls=calls,
                wall_limit_seconds=seconds, external_timeout_seconds=seconds + 30,
                cpu_affinity=sorted(os.sched_getaffinity(0)), max_output_file_bytes=limit)
            state['records'].append(receipt)

            def progress():
                state['active_pid'] = receipt.get('pid') if not receipt.get('process_group_absent_after_exit') else None
                save(dest / 'result.json', receipt); persist()

            progress()
            try:
                checker.verify_files(files)
                with (dest / 'stdout.log').open('wb') as stdout, (dest / 'stderr.log').open('wb') as stderr:
                    a.old.previous.spawn(argv, dest, stdout, stderr, receipt, progress, dict(os.environ), seconds + 30)
                checked = validate(build, dest, record, receipt, negative)
                save(dest / 'validation.json', checked)
                checker.verify_files(files)
                receipt.update(status=checked['status'], validation_sha256=digest(dest / 'validation.json'))
                validations[label] = checked
            except BaseException as error:
                receipt.update(status='FAILED', error=repr(error)); raise
            finally:
                receipt['finished'] = a.b.old.f.h.now(); progress()
            print(label, receipt['status'], flush=True)
        state['status'] = 'W2_SEQUENCE_REFERENCE_CAMPAIGN_PASS'
        save(output / 'results.json', dict(contract=CONTRACT, status=state['status'], records=state['records'],
            validations=validations, target_emu_runs=0, performance_qualified=False,
            independent_full_sequence_replay=False))
    except BaseException as error:
        state.update(status='FAILED', error=repr(error)); raise
    finally:
        state['finished'] = a.b.old.f.h.now(); persist()
    return state


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('W2 sequence signal')))
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    ap = sub.add_parser('adapter')
    for name in ('parent', 'output'):
        ap.add_argument('--' + name, type=Path, required=True)
    rp = sub.add_parser('run')
    for name in ('build', 'adapter', 'original-adapter', 'identity', 'output'):
        rp.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    os.sched_setaffinity(0, [min(os.sched_getaffinity(0))])
    result = adapter(args.output.resolve(), args.parent.resolve()) if args.action == 'adapter' else run(
        args.build.resolve(), args.adapter.resolve(), args.original_adapter.resolve(), args.identity.resolve(), args.output.resolve())
    print(json.dumps({key: result[key] for key in ('contract', 'status')}, indent=2))
