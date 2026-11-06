"""Freeze a new controller by narrow reversible edits of the norm target tools.

The original numerical checks and owned process runner are reused. Reference
qualification has five cases; the target queue has exactly three normal cases.
No old PASS is renamed into a new result and this command executes no guest.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import sys
import types

HERE = Path(__file__).resolve().parent
CONTRACT = 'r2-s3-first-forward-rvv-v1'
TEMPLATES = {
    'reference.py': '573f266c00efd8ff1fb3f11fad428d3405107f215a22815ae0eb30493b63daeb',
    'audit.py': '9e2ede03a7cdb30bd0441b39ce0bdafbc8da888422c6f985e99e682eb9890951',
    'run.py': '0cf3fc20451236de2cc70baa6ac0ec39e953afdf6d6c74bcddca94982422b101',
}
GS32 = {
    'derive.py': '8b920d6742cd40a21f07c5d548901bdc8f9020ce9847cf623e508f4f42ee2ab2',
    'build.py': '70233def12c5e4c5eb5ea07ac9e36709006cd10de5ff8e2100ffaa944dd3f3c2',
}
HELPERS = {
    'consumer/aux_build.py': '0d2be1df9f4c972a6645840ad137d946ab63a964728ec0f221f59a4083ac2da0',
    'norm/run.py': '77fe20c798bcd5025810f5e7f97efa171935fc37fc43fff39e44d6dd6293bb53',
    'norm/target/build.py': 'b25e655da592dd686b904a884087661b8c651ae6d222fb07873d2dd186720656',
}
STAGES = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def transform(name, original):
    text, changes = original.decode(), []
    def change(before, after, count=1):
        nonlocal text
        starts = [m.start() for m in re.finditer(re.escape(before), text)]
        need(before and before != after and len(starts) == count, 'exact edit count: ' + name + ': ' + before[:80])
        old = text
        for start in reversed(starts):
            text = text[:start] + after + text[start + len(before):]
        positions = [start + i * (len(after) - len(before)) for i, start in enumerate(starts)]
        changes.append(dict(before=before, after=after, count=count, output_positions=positions,
                            input_sha256=sha(old.encode()), output_sha256=sha(text.encode())))
    if name == 'reference.py':
        begin = text.index('def inputs(')
        end = text.index('\ndef image(', begin)
        change(text[begin:end], 'def inputs(build, adapter, identity_path):\n    return b.inputs(build, adapter, identity_path)\n\n')
        change("CASES = [('negative', 4, True), ('fr', 3, False), ('ta', 4, False), ('replay', 4, False)]",
               "CASES = [('negative', b.METHODS['paired16'], True), ('fr', b.METHODS['fr'], False),\n"
               "         ('gs32', b.METHODS['gs32'], False), ('paired16', b.METHODS['paired16'], False),\n"
               "         ('replay', b.METHODS['paired16'], False)]")
        change("need(method in (3, 4) and type(negative) is bool and uart in (0, 1), 'bounded explicit controls')",
               "need(method in b.METHODS.values() and type(negative) is bool and uart in (0, 1) and\n"
               "         (not negative or method == b.METHODS['paired16']), 'bounded new experiment controls')")
        change("validations['ta'] == validations['replay']", "validations['paired16'] == validations['replay']")
        change('reference_runs=4,', 'reference_runs=5,')
        change("state['records'].append(rec); state['reference_runs'] += 1",
               "before = state['reference_runs']; state['records'].append(rec)")
        change('            def progress():\n',
               "            def progress():\n                state['reference_runs'] = before + int(rec.get('process_started') is True)\n")
        change("        checker.verify_files(files); state['status'] = b.REFERENCE_PASS",
               "        need(state['reference_runs'] == 5 and len({row['pid'] for row in state['records']}) == 5 and\n"
               "             all(row.get('direct_child_reaped') is True and row.get('process_group_absent_after_exit') is True\n"
               "                 and not row.get('residual_process_group') for row in state['records']), 'five closed independent reference processes')\n"
               "        checker.verify_files(files); state['status'] = b.REFERENCE_PASS")
        change('EXPECTED_FIRST_TOKEN_REFERENCE_REJECTION', 'EXPECTED_FIRST_FORWARD_RVV_REFERENCE_REJECTION')
        change('FIRST_TOKEN_COMPLETE_REFERENCE_PASS', 'FIRST_FORWARD_RVV_COMPLETE_REFERENCE_PASS')
        helper = '''def normal_identities(build, record):
    """Actual byte equality outside the single selector word, for UART=1."""
    base = (build / (b.PREFIX + '.bin')).read_bytes()
    offset = record['control_offset']
    need(base[offset:offset + 12] == struct.pack('<3I', b.METHODS['fr'], 0, 1), 'common target defaults')
    rows = {}
    for name, method in b.METHODS.items():
        raw, control = image(build, record, method, False, 1)
        need(raw[:offset] == base[:offset] and raw[offset + 4:] == base[offset + 4:] and
             raw[offset:offset + 4] == struct.pack('<I', method), 'only one selector word differs')
        rows[name] = dict(method=method, bytes=len(raw), sha256=control['sha256'], controls=control['controls'])
    return dict(base_sha256=record['artifacts'][b.PREFIX + '.bin'], control_offset=offset,
                permitted_byte_range=[offset, offset + 4], all_other_bytes_equal=True, images=rows)


'''
        change('def validate(build, dest, record, receipt, method, negative):', helper + 'def validate(build, dest, record, receipt, method, negative):')
    elif name == 'audit.py':
        change("HERE.parent / 'run.py'", "b.TOOL_REPO / b.STAGES / 'norm/run.py'")
        change("b.REPO / path", "b.TOOL_REPO / path")
        change("need(sites and {v['function'] for v in sites.values()} == {'q288_tail_vdot', 'q768_ta'}, 'both complete TA custom site maps')",
               "need({v['function'] for v in sites.values()} <= {'q288_tail_vdot', 'q768_ta'}, 'only preserved dormant TA custom sites')")
        change("need(method in (3, 4) and type(negative) is bool and (not negative or method == 4), 'exact method and negative controls')",
               "need(method in b.METHODS.values() and negative is False, 'only the three normal pure-RVV target cases')")
        change("need(method == 4 and pc in sites, 'only selected TA path may retire qualified custom sites')",
               "need(False, 'pure-RVV first forward cannot retire a custom instruction')")
        change("(count > 0 if method == 4 else count == 0)", 'count == 0')
        change("begin = f'CONSUMER_BEGIN method={method} token=1 position=0 negative={int(negative)}'",
               "begin = 'CONSUMER_BEGIN token=1 position=0'")
        change('CONSUMER_COUNTERS ([34]) ', 'CONSUMER_COUNTERS ([0-9]+) ')
        change('FIRST_TOKEN_TARGET_DIFFTEST_PASS', 'FIRST_FORWARD_RVV_TARGET_DIFFTEST_PASS')
        change('one cold p0 token1 complete state comparison, original DiffTest, full custom protocol and four CSR chains',
               'one prescribed-prepare first p0 token1 complete forward, original DiffTest, zero custom commits and four CSR chains')
    else:
        change('Freeze and run four isolated complete first-token correctness cases.',
               'Freeze and run three isolated prescribed-prepare first-forward observations.')
        change("PROFILE = 'r2-s3-w2-norm-first-token-resources-v1'", "PROFILE = 'r2-s3-first-forward-rvv-resources-v1'")
        change("PASS = 'NORM_W2_FIRST_TOKEN_TARGET_CAMPAIGN_PASS'",
               "PASS = 'FIRST_FORWARD_RVV_TARGET_OBSERVATIONS_COMPLETE'\n"
               "TARGET_CASES = [(name, method, False) for name, method in b.METHODS.items()]")
        change("state['reference_runs'] == 4", "state['reference_runs'] == 5")
        change('closed exact first-token reference qualification', 'closed five-case new first-forward reference qualification')
        change('exact four qualified cases', 'exact five qualified reference cases')
        change("actual['ta'] == actual['replay']", "actual['paired16'] == actual['replay']")
        change('old.r.parent.parent_identity(b.REPO, identity_path, physical=True)', 'b.physical_identity(identity_path, physical=True)', 3)
        change('old.r.parent.runtime(b.REPO, identity)', 'b.runtime_identity(identity)')
        change("cpu_slots=cpus, cases=[list(case) for case in ref.CASES], schedule='four_independent_after_exact_negative_reference_pass',",
               "cpu_slots=cpus, cases=[list(case) for case in TARGET_CASES], schedule='three_fresh_normal_first_forwards',\n"
               "        target_images=ref.normal_identities(build, record),")
        change("profile['cases'] == [list(case) for case in ref.CASES]", "profile['cases'] == [list(case) for case in TARGET_CASES]")
        change("{name: (method, negative) for name, method, negative in ref.CASES}[case]",
               "{name: (method, negative) for name, method, negative in TARGET_CASES}[case]")
        change("    raw, control = ref.image(build, record, method, negative, 1)\n",
               "    raw, control = ref.image(build, record, method, negative, 1)\n"
               "    need(control['sha256'] == profile['target_images']['images'][case]['sha256'], 'same pre-frozen one-word target image')\n")
        change('queue = [x[0] for x in ref.CASES]', 'queue = [x[0] for x in TARGET_CASES]')
        change('new_emu_runs=0, schedule=profile[\'schedule\'], target_correctness_qualified=False, performance_qualified=False)',
               'new_emu_runs=0, schedule=profile[\'schedule\'], target_correctness_qualified=False, performance_qualified=False,\n'
               '        running_count_scope="completed audited launches; live starts are in per-case receipts until final reconciliation")')
        change("validations = {name: read(output / name / 'validation.json') for name, _, _ in ref.CASES}",
               "validations = {name: read(output / name / 'validation.json') for name, _, _ in TARGET_CASES}")
        change("        need(validations['negative']['status'] == 'EXPECTED_FIRST_TOKEN_TARGET_REJECTION' and\n"
               "             all(validations[name]['status'] == 'FIRST_TOKEN_TARGET_DIFFTEST_PASS' for name in ('fr', 'ta', 'replay')),\n"
               "             'actual negative plus all complete positive cases')\n"
               "        need(validations['ta'] == validations['replay'], 'independent exact architecture/counter/protocol replay')",
               "        need(all(validations[name]['status'] == 'FIRST_FORWARD_RVV_TARGET_DIFFTEST_PASS'\n"
               "                 for name, _, _ in TARGET_CASES), 'three new complete normal target cases')")
        change("state['new_emu_runs'] == 4, 'four independent original EMUs'", "state['new_emu_runs'] == 3, 'three independent original EMUs'")
        change('new_emu_runs=4, target_correctness_qualified=True,', 'new_emu_runs=3, target_correctness_qualified=True,')
        change('validations=validations, new_emu_runs=3,', 'validations=validations, target_images=profile[\'target_images\'], new_emu_runs=3,')
        change("parser.add_argument('--cpus', default='0,1,2,3')", "parser.add_argument('--cpus', default='0,2,3')")
        change("choices=[x[0] for x in ref.CASES]", "choices=[x[0] for x in TARGET_CASES]")
    reversed_text = text
    for row in reversed(changes):
        need(sha(reversed_text.encode()) == row['output_sha256'], 'reverse intermediate controller identity')
        for start in reversed(row['output_positions']):
            need(reversed_text[start:start + len(row['after'])] == row['after'], 'exact reverse controller span')
            reversed_text = reversed_text[:start] + row['before'] + reversed_text[start + len(row['after']):]
        need(sha(reversed_text.encode()) == row['input_sha256'], 'reverse parent controller identity')
    need(reversed_text.encode() == original, 'whole controller exactly reverses to original bytes')
    compile(text, name, 'exec')
    return text, changes


def bind(config_path, output):
    config = json.loads(config_path.read_text())
    required = {'repository', 'parent_build', 'parent_campaign', 'support_snapshot', 'scalar_view',
                'gs32_controller', 'gs32_screen', 'paired16_screen', 'norm_target_build', 'adapter', 'identity'}
    need(set(config) == required and all(Path(p).is_absolute() and Path(p).exists() for p in config.values()),
         'all explicit existing input roots; no implicit checkout or search')
    need(not output.exists() and not output.is_relative_to(HERE) and
         not any(output.is_relative_to(Path(p)) for p in config.values()), 'fresh external controller output')
    files = {str(config_path): sha(config_path.read_bytes())}
    generated, proofs = {}, {}
    for name, expected in HELPERS.items():
        path = Path(config['repository']) / STAGES / name
        need(sha(path.read_bytes()) == expected, 'fixed original target support: ' + name)
        files[str(path)] = expected
    for name, expected in GS32.items():
        path = Path(config['gs32_controller']) / name
        need(sha(path.read_bytes()) == expected, 'actual fixed GS32 helper')
        files[str(path)] = expected
    for name, expected in TEMPLATES.items():
        path = Path(config['repository']) / STAGES / 'norm/target' / name
        raw = path.read_bytes()
        need(sha(raw) == expected, 'actual fixed norm target template: ' + name)
        files[str(path)] = expected
        generated[name], proofs[name] = transform(name, raw)
    # Import the unchanged target helpers once to discover their actual Python
    # closure, then preserve that small closure in this controller. No checkout
    # is made and future Git HEAD movement cannot change these helper bytes.
    need(sys.dont_write_bytecode, '-B protects original source while discovering helpers')
    repository = Path(config['repository'])
    template_audit = repository / STAGES / 'norm/target/audit.py'
    spec = importlib.util.spec_from_file_location('first_forward_original_target_closure', template_audit)
    audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
    # These unchanged physical-profile helpers are loaded dynamically by the
    # old checker, so its ordinary import graph alone cannot discover them.
    physical_helpers = []
    for index, relative in enumerate(('team/optimizations/o2/fullcore/run_suite.py',
            'team/optimizations/o2/result-width/h1/performance/build_profile.py', 'team/scripts/artifact_guard.py')):
        spec = importlib.util.spec_from_file_location('first_forward_physical_helper_' + str(index), repository / relative)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        physical_helpers.append(module)
    pending, seen, closure = [audit, *audit.gates(), *physical_helpers], set(), {}
    while pending:
        module = pending.pop()
        if not isinstance(module, types.ModuleType) or id(module) in seen:
            continue
        seen.add(id(module))
        pending.extend(v for v in vars(module).values() if isinstance(v, types.ModuleType))
        name = getattr(module, '__file__', None)
        if name:
            path = Path(name).resolve()
            if path.is_file() and path.is_relative_to(repository):
                raw = path.read_bytes()
                closure[str(path.relative_to(repository))] = raw
                files[str(path)] = sha(raw)
    need(closure and str(STAGES / 'consumer/aux_build.py') in closure and
         str(STAGES / 'norm/run.py') in closure, 'actual target helper closure includes UART and norm audit')
    output.mkdir(parents=True)
    for name, text in generated.items():
        (output / name).write_text(text)
    for name in ('bind.py', 'build.py', 'derive.py', 'CONTRACT.md', 'BUDGET.md'):
        raw = (HERE / name).read_bytes()
        files[str(HERE / name)] = sha(raw)
        (output / name).write_bytes(raw)
    for name, raw in closure.items():
        dest = output / 'target-support' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
    binding = dict(contract=CONTRACT, status='FIRST_FORWARD_RVV_CONTROLLER_BOUND_NOT_RUNTIME', config=config,
        input_files=files, generated_files={str(p.relative_to(output)): sha(p.read_bytes()) for p in output.rglob('*') if p.is_file()},
        target_support_files=len(closure), target_support_source_identity='actual imported unchanged target helper closure',
        source_transformations=proofs, exact_original_controllers_recovered=True,
        reference_cases=['negative', 'fr', 'gs32', 'paired16', 'replay'], target_cases=['fr', 'gs32', 'paired16'],
        reference_runs=0, target_emu_runs=0, performance_qualified=False)
    (output / 'binding.json').write_text(json.dumps(binding, indent=2) + '\n')
    return binding


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = bind(args.config.resolve(), args.output.resolve())
    print(json.dumps(dict(contract=CONTRACT, status=result['status'], output=str(args.output))), flush=True)
