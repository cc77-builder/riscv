"""Recompute W2 decisions from byte-restored evidence, without a simulator.

Only captured validators are imported. Raw metadata and evidence stay unchanged;
the two explicit data-path relocations are recorded. Physical runtime identity
is historical evidence and is not re-qualified by this offline operation.
"""
from pathlib import Path
import argparse, copy, hashlib, importlib.util, json, re, shlex, shutil, struct, sys, time, types

HERE = Path(__file__).resolve().parent
REL = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages/w2')
REPO = HERE.parents[8]


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def imported_sources(modules, root, snapshot, original, pins):
    pending, seen, closure = list(modules), set(), {}
    while pending:
        module = pending.pop()
        if not isinstance(module, types.ModuleType) or id(module) in seen:
            continue
        seen.add(id(module))
        pending.extend(v for v in vars(module).values() if isinstance(v, types.ModuleType))
        name = getattr(module, '__file__', None)
        if name:
            path = Path(name).resolve()
            if any(path.is_relative_to(p) for p in (root, original, REPO)):
                need(path.is_relative_to(snapshot), 'no original-machine/current-tree/other-snapshot import')
                rel = path.relative_to(snapshot)
                need(pins.get(str(original / rel)) == sha(path), 'actual imported helper equals frozen runtime source')
                closure[str(rel)] = sha(path)
    return closure


def frozen(root, campaign, build, entry):
    snapshot = campaign / 'runtime-source'
    pins = read(campaign / 'runtime-inputs.json')
    preparation = read(root / 'transport/preparation.json')
    need(preparation['format'] == 'w2-exact-staging-v1', 'explicit original source owner from byte-sealed preparation')
    original = Path(preparation['runtime_original_project_roots'][campaign.name])
    need(original.is_absolute() and str(original / REL / entry) in pins, 'one explicitly pinned runtime validator root')
    captured = {}
    for path in snapshot.rglob('*'):
        if path.is_file():
            rel = path.relative_to(snapshot)
            need(pins.get(str(original / rel)) == sha(path), 'every captured source has its original runtime pin')
            captured[str(rel)] = sha(path)
    need(str(REL / entry) in captured, 'captured entry is present')
    need(captured == preparation['captured_runtime_project_sources'][campaign.name], 'complete explicitly captured project-source inventory')
    build_keys = [Path(name).parent for name, value in pins.items()
                  if name.endswith('/result.json') and value == sha(build / 'result.json')]
    need(len(build_keys) == 1, 'selected build belongs to this actual campaign')
    # The old helpers import runtime_experiment by name. Do not reuse a module
    # or search path from another restored campaign's captured source closure.
    for name, module in list(sys.modules.items()):
        path = getattr(module, '__file__', None)
        if path and Path(path).resolve().is_relative_to(root):
            sys.modules.pop(name, None)
    sys.path[:] = [p for p in sys.path if not Path(p).resolve().is_relative_to(root)]
    validator = load('frozen_w2_' + campaign.name.replace('-', '_'), snapshot / REL / entry)
    owner = validator.REPO if hasattr(validator, 'REPO') else validator.b.REPO
    need(owner == snapshot, 'validator resolves its repository inside this snapshot')
    closure = imported_sources([validator], root, snapshot, original, pins)
    record = read(build / 'result.json')
    original_build = build_keys[0]
    for key, folder, pinned in (('artifacts', build, original_build), ('fixtures', build / 'fixture', original_build / 'fixture'),
                        ('actual_source_pins', build / 'source', original_build / 'source'),
                        ('source_pins', build / 'source/repo', original_build / 'source/repo')):
        for name, value in record[key].items():
            need(sha(folder / name) == value == pins.get(str(pinned / name)), 'restored complete build/runtime binding ' + key + ': ' + name)
    need(sha(build / 'tools.json') == pins.get(str(original_build / 'tools.json')), 'original build tool inventory binding')
    return validator, record, pins, original_build, dict(entry_sha256=sha(snapshot / REL / entry),
        original_project_root=str(original),
        captured_source_count=len(captured), actual_imported_source_sha256=closure)


def records(campaign, labels, status, target=False):
    state = read(campaign / 'state.json')
    need(state['status'] == status and not state.get('active') and state.get('active_pid') is None and
         not state.get('cleanup_unknown') and state.get('finished'), 'closed original campaign')
    items = read(campaign / 'results.json')['records'] if target else state['records']
    need(len(items) == len(labels) and {v['name'] for v in items} == set(labels), 'exact actual case inventory')
    pids = [v.get('pid') for v in items]
    need(all(type(p) is int and p > 0 for p in pids) and len(pids) == len(set(pids)), 'distinct actual process IDs')
    out = {}
    for item in items:
        dest = campaign / ('runs' if target else '') / item['name']
        receipt = read(dest / 'result.json')
        need(receipt == item and receipt.get('direct_child_reaped') is True and
             receipt.get('process_started') is True and receipt.get('process_group_absent_after_exit') is True and
             not receipt.get('residual_process_group') and not receipt.get('timed_out') and
             not any(receipt.get(k) for k in ('cleanup_error', 'cleanup_signal_error', 'stdout_close_error', 'stderr_close_error')) and
             receipt.get('started') and receipt.get('finished'), 'complete final owned-process receipt')
        out[item['name']] = receipt
    return out


def reference_command(receipt, pins, original_build, build, calls, seconds):
    argv = receipt['command']
    dest = Path(receipt['cwd'])
    need(len(argv) == 9 and Path(argv[0]).name == 'reference-runner' and argv[0] in pins and
         pins.get(argv[1]) == '8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9' and
         argv[2:7] == [str(dest / 'image.bin'), str(dest), 'builtin', str(calls), str(seconds)] and
         argv[7:] == [str(original_build / 'dump-plan.txt'), '1'] and
         pins[str(original_build / 'dump-plan.txt')] == sha(build / 'dump-plan.txt'),
         'original reference command, image, bounded execution and exact dump plan')


def same_case(campaign, label, actual, wanted, receipt):
    path = campaign / label / 'validation.json'
    need(actual == read(path) == wanted, 'recomputed complete original decision: ' + label)
    if 'validation_sha256' in receipt:
        need(sha(path) == receipt['validation_sha256'], 'original validation receipt link')


def reference_trap(case):
    terminal = read(case / 'reference-result.json')
    text = re.sub(r'\x1b\[[0-9;]*m', '', (case / 'stdout.log').read_text())
    lines = [line for line in text.splitlines() if 'HIT ' in line and ' TRAP' in line]
    need(len(lines) <= 1, 'at most one canonical reference trap line')
    for line in lines:
        match = re.fullmatch(r'(?:\[[^\]\r\n]+\]\s*)?nemu: HIT (GOOD|BAD) TRAP at pc = (0x[0-9a-fA-F]+)', line)
        need(match is not None and match[1] == ('GOOD' if terminal['reason'] == 'good_trap' else 'BAD') and
             int(match[2], 16) == terminal['halt_pc'], 'reference console and original terminal JSON agree')


def check_core(root, output):
    cases, snapshots = {}, {}
    for label, build_label, entry, expected in (
            ('reference', 'build', 'reference.py', 'W2_REFERENCE_CAMPAIGN_PASS'),
            ('consumer-reference', 'consumer-build', 'consumer_run.py', 'PURE_W2_FORWARD_REFERENCE_CAMPAIGN_PASS')):
        campaign, build = root / label, root / build_label
        validator, record, pins, original_build, snapshots[label] = frozen(root, campaign, build, entry)
        summary = read(campaign / 'results.json')
        need(summary['status'] == expected and summary['contract'] == record['contract'], 'original contract and completion')
        if label == 'reference':
            plan = [('negative', True), ('normal', False), ('replay', False)]
            validator.b.executable(build / 'real-w2.elf', build / 'real-w2.bin')
        else:
            plan = validator.CASES
            validator.b.old.f.executable(build / 'forward-consumer-w2.elf', build / 'forward-consumer-w2.bin',
                build / 'metadata.stdout.log', record['tls_errno_offset'])
            functions = validator.b.old.p.kernel_bytes(build / 'forward-consumer-w2.elf', record['kernel_identity']['functions'])
            need(len(functions) == 4 and record['kernel_identity']['w2_elf_sha256'] == sha(root / 'build/real-w2.elf'),
                 'four actual consumer kernels and same complete W2 parent ELF')
            for name, raw in functions.items():
                need(len(raw) == record['kernel_identity']['functions'][name]['bytes'] and
                     hashlib.sha256(raw).hexdigest() == record['kernel_identity']['functions'][name]['sha256'],
                     'whole actual consumer kernel identity')
        receipts = records(campaign, [v[0] for v in plan], expected)
        need(set(summary['validations']) == set(receipts), 'exact original validation set')
        actual = {}
        for item in plan:
            name, *control = item
            receipt = receipts[name]
            reference_trap(campaign / name)
            if label == 'reference':
                need(receipt['negative'] is control[0], 'actual boundary control')
                reference_command(receipt, pins, original_build, build, 100000000, 300)
                checked = validator.validate(build, campaign / name, record, receipt, *control)
            else:
                need((receipt['method'], receipt['kind']) == tuple(control), 'actual full-consumer controls')
                reference_command(receipt, pins, original_build, build, validator.MAX_CALLS, 600)
                checked = validator.validate(build, campaign / name, record, *control, receipt)
            same_case(campaign, name, checked, summary['validations'][name], receipt)
            actual[name] = checked
            cases[label + '/' + name] = checked['status']
        if label == 'reference':
            need(actual['normal'] == actual['replay'], 'complete boundary reference replay')
        else:
            need(actual['ta-cache'] == actual['recovery'] == actual['replay'], 'complete consumer recovery and replay')
            need(all(actual[name]['flags'] == actual['scalar']['flags'] for name in ('fr', 'ta', 'fr-cache', 'ta-cache')),
                 'five methods retain the actual scalar flags')
    campaign, build = root / 'api-reference', root / 'api-build'
    validator, original, pins, original_build, snapshots['api-reference'] = frozen(root, campaign, build, 'api.py')
    summary = read(campaign / 'results.json')
    expected = 'SHARED_W2_API_REFERENCE_CAMPAIGN_PASS'
    need(summary['status'] == expected and summary['contract'] == original['contract'], 'actual distinct API completion')
    receipt = records(campaign, ['api'], expected)['api']
    reference_trap(campaign / 'api')
    need(len(summary['records']) == 1 and all(receipt.get(k) == v for k, v in summary['records'][0].items()),
         'summary preserves its recorded fields before the final finished timestamp')
    qualified = Path(original['qualified_campaign'])
    for name in ('results.json', 'state.json', 'runtime-inputs.json'):
        need(pins[str(qualified / name)] == sha(root / 'consumer-reference' / name), 'byte-identical qualified consumer lookup')
    record = dict(original, qualified_campaign=str(root / 'consumer-reference'))
    reference_command(receipt, pins, original_build, build, validator.r.MAX_CALLS, 600)
    validator.b.old.f.executable(build / (validator.PREFIX + '.elf'), build / (validator.PREFIX + '.bin'),
        build / 'metadata.stdout.log', record['tls_errno_offset'])
    functions = validator.b.old.p.kernel_bytes(build / (validator.PREFIX + '.elf'), record['kernel_identity']['functions'])
    need(len(functions) == 4, 'four actual API kernel functions')
    for name, raw in functions.items():
        need(len(raw) == record['kernel_identity']['functions'][name]['bytes'] and
             hashlib.sha256(raw).hexdigest() == record['kernel_identity']['functions'][name]['sha256'], 'whole API kernel bytes')
    need(sha(build / 'source/consumer-w2.o') == record['qualified_consumer_object_sha256'] ==
         sha(root / 'consumer-build/consumer-w2.o'), 'same actual qualified consumer object')
    checked = validator.validate(build, campaign / 'api', record, receipt)
    same_case(campaign, 'api', checked, summary['validation'], receipt)
    cases['api-reference/api'] = checked['status']
    need(len(cases) == 14, 'all fourteen actual reference cases rechecked')
    return dict(cases=cases, validator_snapshots=snapshots, data_path_relocations=1,
                extra_historical_receipt_and_console_checks=True,
                stage_performance_qualified=False, full_forward_performance_qualified=False)


def check_target(root, output, failed):
    campaign, build = root / 'target', root / 'build'
    validator, record, pins, original_build, snapshot = frozen(root, campaign, build, 'run.py')
    cfg = read(campaign / 'configuration.json')
    gates = tuple(validator.load('restored_w2_gate_' + str(i), campaign / 'runtime-source' / rel)
                  for i, rel in enumerate(('team/optimizations/o2/fullcore/run_suite.py',
                      'team/optimizations/o1/audit/runtime_gate.py', 'team/optimizations/o2/fullcore/recheck.py',
                      'team/optimizations/o2/fullcore/analyze.py')))
    snapshot['actual_imported_source_sha256'].update(imported_sources(gates, root, campaign / 'runtime-source',
        Path(snapshot['original_project_root']), pins))
    identity = read(campaign / 'parent-identity.json')
    need(cfg == identity['configuration'] and sha(campaign / 'parent-identity.json') in pins.values(),
         'original frozen configuration and runtime identity binding')
    validator.b.executable(build / 'real-w2.elf', build / 'real-w2.bin')
    if failed:
        state = read(campaign / 'state.json')
        need(state['status'] == 'FAILED' and not state['active'] and state['new_emu_runs'] == 1,
             'one closed actually failed negative campaign')
        receipt = read(campaign / 'runs/negative/result.json')
        need(receipt['exit_code'] == 0 and receipt.get('direct_child_reaped') is True and
             receipt.get('process_group_absent_after_exit') is True, 'original unexpected good trap was reaped')
        receipts = {'negative': receipt}
    else:
        summary = read(campaign / 'results.json')
        expected = 'W2_BOUNDARY_DIFFTEST_CAMPAIGN_PASS'
        need(summary['status'] == expected and summary['contract'] == record['contract'], 'original target qualification')
        receipts = records(campaign, ['negative', 'normal', 'recovery', 'replay'], expected, target=True)
    validations = {}
    for label, receipt in receipts.items():
        mode = int(label == 'negative')
        name = 'negative.bin' if mode else 'real-w2.bin'
        need(receipt['mode'] == mode and receipt['command'][2] == str(original_build / name) and
             receipt['image_sha256'] == record['artifacts'][name], 'original actual target image identity')
        expected_command = [str(Path(cfg['hardware_source']) / 'build/emu'), '-i', str(original_build / name),
            '--flash=' + cfg['flash'], '--ram-size=128MB', '--diff=' + cfg['reference'],
            '--max-cycles=12000000', '--seed=1']
        need(receipt['command'] == expected_command and
             all(receipt['files'].get(path) == value for path, value in pins.items()),
             'exact original EMU invocation and all shared frozen inputs')
        extra = {path: value for path, value in receipt['files'].items() if path not in pins}
        actual_aux = campaign / 'runs' / label / 'cwd/build'
        need(set(extra) == {str(Path(receipt['cwd']) / 'build' / p.name) for p in actual_aux.iterdir() if p.is_file()},
             'exact original isolated runtime auxiliary input set')
        for path, value in extra.items():
            need(sha(actual_aux / Path(path).name) == value, 'original isolated auxiliary input bytes')
        dest = output / 'raw-audits' / label
        dest.mkdir(parents=True)
        for filename in ('stderr.log', 'stdout.log'):
            source = campaign / 'runs' / label / filename
            need(sha(source) == receipt['raw_sha256'][filename], 'whole original target log')
            shutil.copyfile(source, dest / filename)
        relocated = copy.deepcopy(receipt)
        relocated['command'][2] = str(build / name)
        if failed:
            try:
                validator.validate(dest, record, build, mode, relocated, cfg, gates)
            except ValueError as error:
                need(str(error) == 'complete expected EMU process', 'original exact false-good gate rejection')
                validations[label] = dict(status='EXPECTED_SAVED_FALSE_GOOD_REJECTED', error=str(error))
            else:
                raise ValueError('original false-good evidence was incorrectly accepted')
        else:
            checked = validator.validate(dest, record, build, mode, relocated, cfg, gates)
            wanted = read(campaign / 'runs' / label / 'validation.json')
            need(checked == wanted and sha(campaign / 'runs' / label / 'validation.json') ==
                 receipt['validation_sha256'], 'same full target decision from raw logs')
            for filename in ('counter-audit.json', 'protocol.json', 'uart.txt', 'counter-source.txt'):
                need(sha(dest / filename) == sha(campaign / 'runs' / label / filename), 'same complete derived target artifact')
            validations[label] = checked
    decision = None
    if not failed:
        need(validations['normal'] == validations['recovery'] == validations['replay'] == summary['validation'],
             'complete target counters, fcsr, output, custom protocol replay')
        decision = validator.performance(validations['normal'])
        need(decision == summary['performance'] == read(campaign / 'performance.json'), 'recomputed same fairness and selection')
    return dict(cases={k: v['status'] for k, v in validations.items()}, validator_snapshots={'target': snapshot},
        data_path_relocations=len(receipts), performance=decision,
        stage_performance_qualified=False if failed else decision['comparison_qualified'],
        full_forward_performance_qualified=False)


def check_sequence(root, output):
    campaign, build, adapted = root / 'reference', root / 'build', root / 'adapter'
    validator, record, pins, original_build, snapshot = frozen(root, campaign, build, 'sequence_run.py')
    expected = 'W2_SEQUENCE_REFERENCE_CAMPAIGN_PASS'
    summary, build_state = read(campaign / 'results.json'), read(build / 'state.json')
    need(summary['status'] == expected and summary['contract'] == record['contract'] == validator.CONTRACT and
         build_state['status'] == record['status'] == validator.b.STATIC_PASS and build_state.get('finished') and
         build_state['result_sha256'] == sha(build / 'result.json'), 'closed distinct sequence build and campaign')
    need(summary['target_emu_runs'] == 0 and summary['performance_qualified'] is False and
         summary['independent_full_sequence_replay'] is False, 'original sequence qualification boundaries')
    parent_build, parent_campaign = Path(record['qualified_api_build']), Path(record['qualified_api_campaign'])
    parent_decision = build / 'parent-api-validation.json'
    need(sha(parent_decision) == pins[str(parent_campaign / 'api/validation.json')] and
         read(parent_decision)['status'] == validator.a.PASS and
         record['kernel_identity']['qualified_api_elf_sha256'] == pins[str(parent_build / (validator.a.PREFIX + '.elf'))],
         'actual qualified API parent decisions and ELF remain bound to their original runtime pins')
    need(sha(build / 'source/consumer-w2.o') == record['qualified_consumer_object_sha256'] ==
         record['kernel_identity']['consumer_object_sha256'] == pins[str(parent_build / 'source/consumer-w2.o')],
         'same complete actual qualified consumer object')
    elf, _ = validator.a.b.old.f.executable(build / (validator.b.PREFIX + '.elf'), build / (validator.b.PREFIX + '.bin'),
        build / 'metadata.stdout.log', record['tls_errno_offset'])
    functions = validator.a.b.old.p.kernel_bytes(build / (validator.b.PREFIX + '.elf'), validator.b.KERNELS)
    need(set(functions) == set(record['kernel_identity']['functions']) == set(validator.b.KERNELS), 'exact four sequence kernels')
    for name, raw in functions.items():
        need(len(raw) == record['kernel_identity']['functions'][name]['bytes'] and
             hashlib.sha256(raw).hexdigest() == record['kernel_identity']['functions'][name]['sha256'], 'complete sequence kernel bytes')
    address, length, *_ = elf.symbols['compare']
    raw = elf.read(address, length)
    words = struct.unpack('<' + str(length // 4) + 'I', raw)
    need(record['state_compare_machine_check'] == dict(address=hex(address), bytes=length,
         sha256=hashlib.sha256(raw).hexdigest(), direct_word_loads=True, memcpy_calls=0) and
         sum(word & 0x707f == 0x3003 for word in words) >= 2, 'same actual complete aligned-word comparator')
    prefix = b''.join((build / f'fixture/host-state-p{pos}.bin').read_bytes() for pos in range(3))
    need(len(prefix) == 3 * validator.S and prefix == (build / 'fixture/prefix_gold.bin').read_bytes(),
         'complete independent host prefix in original position order')
    for pos in range(3):
        name = f'host-state-p{pos}.bin'
        need(sha(build / 'fixture' / name) == pins[str(parent_build / 'fixture' / name)], 'same qualified host prefix state')
    adapter_record, adapter_state = read(adapted / 'build.json'), read(adapted / 'state.json')
    roots = [Path(path).parent for path, value in pins.items() if path.endswith('/build.json') and
             value == sha(adapted / 'build.json')]
    need(len(roots) == 1, 'one actual separately derived adapter')
    original_adapter = roots[0]
    need(adapter_record['contract'] == validator.CONTRACT and adapter_record['status'] == adapter_state['status'] ==
         'W2_SEQUENCE_ADAPTER_BUILD_PASS' and adapter_state.get('finished') and
         adapter_state['result_sha256'] == sha(adapted / 'build.json') and
         sha(adapted / 'state.json') == pins[str(original_adapter / 'state.json')] and
         adapter_record['inputs_sha256'] == sha(adapted / 'inputs.json') == pins[str(original_adapter / 'inputs.json')],
         'actual closed adapter build and metadata identity')
    for name, value in adapter_record['artifacts'].items():
        need(sha(adapted / name) == value == pins[str(original_adapter / name)], 'complete actually used adapter artifact')
    need(all(pins.get(path) == value for path, value in read(adapted / 'inputs.json')['files'].items()),
         'all original adapter build inputs retained in campaign pins')
    parent_adapter = Path(adapter_record['parent_adapter'])
    parent_record = read(adapted / 'parent/build.json')
    need(parent_record['status'] == 'REFERENCE_ADAPTER_BUILD_PASS' and
         parent_record['inputs_sha256'] == sha(adapted / 'parent/inputs.json') and
         sha(adapted / 'parent/build.json') == pins[str(parent_adapter / 'build.json')], 'exact original team adapter build')
    for name, value in parent_record['artifacts'].items():
        need(sha(adapted / 'parent' / name) == value == pins[str(parent_adapter / name)], 'original parent adapter bytes')
    source = (adapted / 'reference_runner.c').read_bytes()
    parent_source = (adapted / 'parent/reference_runner.c').read_bytes()
    before, after = validator.CAP_BEFORE.encode(), validator.CAP_AFTER.encode()
    need(hashlib.sha256(parent_source).hexdigest() == validator.PARENT_SOURCE and
         parent_source.count(before) == source.count(after) == 1 and after not in parent_source and
         source == parent_source.replace(before, after) and source.replace(after, before) == parent_source,
         'only one budget literal differs; complete arithmetic, terminal and exception behavior unchanged')
    compiled, old_compiled = read(adapted / 'compile.command.json'), read(adapted / 'parent/compile.command.json')
    replacements = {str(parent_adapter / name): str(original_adapter / name)
                    for name in ('reference_runner.c', 'runner.d', 'reference-runner')}
    argv = [adapter_record['compiler']['path'], *[replacements.get(v, v) for v in old_compiled['argv'][1:]]]
    proof = dict(parent_source_sha256=validator.PARENT_SOURCE, source_sha256=hashlib.sha256(source).hexdigest(),
        exact_parent_reverse=True, changed_occurrences=1, old_max_api_calls=10000000000,
        new_max_api_calls=48000000000, original_argv=old_compiled['argv'], actual_argv=argv)
    need(proof == adapter_record['derivation'] == read(adapted / 'derivation.json') and compiled['argv'] == argv and
         pins[adapter_record['compiler']['path']] == adapter_record['compiler']['sha256'], 'actual complete budget derivation proof')
    for receipt in (compiled, old_compiled):
        need(receipt['exit_code'] == 0 and receipt['status'] == 'exited' and receipt.get('direct_child_reaped') is True and
             receipt.get('process_group_absent_after_exit') is True, 'actual successful owned compiler process')
    def dependencies(path):
        return set(shlex.split(path.read_text().replace('\\\n', ' ').split(':', 1)[1]))
    need(dependencies(adapted / 'runner.d') == {replacements.get(v, v) for v in dependencies(adapted / 'parent/runner.d')},
         'unchanged actual compiler header dependencies')
    receipts = records(campaign, [item[0] for item in validator.CASES], expected)
    need(summary['records'] == read(campaign / 'state.json')['records'] and
         set(summary['validations']) == set(receipts), 'complete sequence summary and case inventory')
    cases = {}
    for label, negative, calls, seconds in validator.CASES:
        receipt = receipts[label]
        need(receipt['negative'] is negative and receipt['command'][0] == str(original_adapter / 'reference-runner') and
             receipt['external_timeout_seconds'] == seconds + 30 and receipt['cpu_affinity'] == [3] and
             receipt['max_output_file_bytes'] == 128 * 1024 * 1024, 'actual sequence control, CPU and hard execution bounds')
        reference_command(receipt, pins, original_build, build, calls, seconds)
        reference_trap(campaign / label)
        checked = validator.validate(build, campaign / label, record, receipt, negative)
        same_case(campaign, label, checked, summary['validations'][label], receipt)
        cases[label] = checked['status']
    return dict(cases=cases, validator_snapshots={'reference': snapshot}, data_path_relocations=0,
        adapter_budget_only_source_derivation=True, same_qualified_consumer_object=True,
        positions_compared=256, independent_full_sequence_replay=False,
        stage_performance_qualified=False, full_forward_performance_qualified=False)


def recheck(root, manifest_path, expected, output, kind):
    need(not output.exists() and not any(output.is_relative_to(p) for p in (root, REPO)), 'fresh isolated audit output')
    need(sha(manifest_path) == expected, 'exact published manifest SHA256')
    manifest = read(manifest_path)
    need(manifest['format'] == 'sha256-object-zip-v1', 'original byte-preserving archive format')
    rows = manifest['files']
    names = {row['path'] for row in rows}
    need(len(rows) == len(names) == manifest['file_count'], 'unique complete restored inventory')

    def verify():
        need({p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()} == names,
             'exact full restored file membership')
        for row in rows:
            path = root / row['path']
            need(path.resolve().is_relative_to(root) and not path.is_symlink() and
                 path.stat().st_size == row['size'] and sha(path) == row['sha256'], 'every original restored byte')

    verify()
    output.mkdir(parents=True)
    started = time.monotonic()
    sys.dont_write_bytecode = True
    try:
        detail = (check_core(root, output) if kind == 'core' else check_sequence(root, output) if kind == 'sequence'
                  else check_target(root, output, kind == 'failed-target'))
        verify()
        result = dict(status='RESTORED_W2_RAW_RECHECK_PASS', kind=kind, manifest_sha256=expected,
            rechecker_sha256=sha(HERE / 'recheck.py'), restored_file_count=len(rows),
            elapsed_seconds=time.monotonic() - started, new_reference_runs=0, new_emu_runs=0,
            physical_runtime_identity_rechecked=False, **detail)
    except BaseException as error:
        result = dict(status='FAILED', kind=kind, error=repr(error), manifest_sha256=expected)
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        raise
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'manifest', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--expected-manifest-sha256', required=True)
    parser.add_argument('--kind', choices=('core', 'target', 'failed-target', 'sequence'), required=True)
    args = parser.parse_args()
    value = recheck(args.root.resolve(), args.manifest.resolve(), args.expected_manifest_sha256,
                    args.output.resolve(), args.kind)
    print(json.dumps({key: value[key] for key in ('status', 'kind', 'cases', 'stage_performance_qualified')}, indent=2))
