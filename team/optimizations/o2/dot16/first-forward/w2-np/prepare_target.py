"""Prepare the existing owned target runner for four-arm dot16 TRACE0.

Source preparation only: no compiler, reference, EMU or host probe is launched.
Budgets are mandatory inputs; their approval and the outer owner are separate.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import sys

HERE = Path(__file__).resolve().parent
CONTRACT = 'r3-dot16-first-forward-w2np-v1'
PROFILE = 'r3-dot16-first-forward-w2np-resources-v1'
ACTIVE = ('paired16', 'paired16_quantize', 'dot16', 'dot16_quantize')
TARGET_CASES = (('paired16', 0x50313631, False), ('paired16_quantize', 0x50535131, False),
                ('dot16', 0x44313631, False), ('dot16_quantize', 0x44313651, False))
PARENT_BINDING_SHA = 'abab046e22508c6287b1ea9a9e91ece6d994ca6dd3c5d596d8d99e6ae3032972'
PARENT_PINS = dict(
    run='b8ab0c2bafaa7f329fec72537541fa621e1b428436ce587eb893e57d636e69a8',
    audit='ffc32d13a5fc1d8483f3050d286fc80c26e970e585ec33255fd590a67a63694f')
CHANGED = {
    'team/optimizations/o1/audit/runtime_gate.py',
    'team/optimizations/o2/fullcore/recheck.py',
    'team/optimizations/o2/fullcore/run_suite.py',
    'team/optimizations/o2/r2-safe-tail/merged_screen.py',
    'team/optimizations/o2/r2-select/entry_c_api.py',
    'team/optimizations/o2/r2-select/entry_experiment.py',
    'team/optimizations/o2/result-width/h1/performance/build_profile.py',
}
EXCLUDED = {
    'team/optimizations/o2/fullcore/input_contract.py',
    'team/optimizations/o2/fullcore/live_inputs.py',
    'team/optimizations/o1/build_recipe.py',
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as source:
        for raw in iter(lambda: source.read(1 << 20), b''):
            h.update(raw)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def inventory(root):
    paths = list(root.rglob('*'))
    need(not root.is_symlink() and not any(path.is_symlink() for path in paths), 'plain source inputs')
    return {path.relative_to(root).as_posix(): digest(path) for path in paths if path.is_file()}


def transform(name, original, budget):
    text, changes = original.decode(), []
    def edit(before, after, count=1):
        nonlocal text
        starts = [match.start() for match in re.finditer(re.escape(before), text)]
        need(before and before != after and len(starts) == count, 'exact target source change: ' + name + ': ' + before[:100])
        previous = text
        for start in reversed(starts):
            text = text[:start] + after + text[start + len(before):]
        positions = [start + i * (len(after) - len(before)) for i, start in enumerate(starts)]
        changes.append(dict(before=before, after=after, count=count, output_positions=positions,
                            input_sha256=sha(previous.encode()), output_sha256=sha(text.encode())))
    def cut(begin, end, replacement):
        need(text.count(begin) == text.count(end) == 1, 'unique bounded target edit markers')
        first, last = text.index(begin), text.index(end)
        need(first < last, 'ordered bounded target edit markers')
        edit(text[first:last], replacement)
    if name == 'run.py':
        edit('MAX_CYCLES = 40_000_000', 'MAX_CYCLES = ' + str(budget['max_cycles']))
        edit('TIMEOUT = 28_800', 'TIMEOUT = ' + str(budget['external_timeout_seconds']))
        edit('RAW_LIMIT = 4 * 1024 * 1024 * 1024', 'RAW_LIMIT = ' + str(budget['max_output_file_bytes']))
        edit("\"\"\"Freeze and run the two isolated P/PQ prescribed-prepare first-forward observations.\"\"\"", "\"\"\"Freeze and run four isolated dot16 TRACE0 first-forward observations.\"\"\"")
        edit("FIRST_FORWARD_PSQ_TARGET_OBSERVATIONS_COMPLETE", "FIRST_FORWARD_W2NP_TARGET_OBSERVATIONS_COMPLETE")
        edit("(('negative', 0x50535131, True), *TARGET_CASES)", "(('negative', 0x44313651, True), *TARGET_CASES)")
        edit("exact final PQ-negative/P/PQ reference contract", "exact final DQ-negative/four-normal reference contract")
        edit("closed three-case P/PQ reference qualification", "closed five-case dot16 reference qualification")
        edit("exact three actual independent reference cases", "exact five actual independent reference cases")
        edit("    cfg = identity['configuration']\n    for rel in ('difftest/src/test/csrc/verilator/emu.cpp', 'difftest/verilator.mk',\n                'difftest/src/main/scala/Difftest.scala', 'src/main/scala/xiangshan/backend/exu/ExeUnit.scala',\n                'src/main/scala/xiangshan/backend/rob/Rob.scala', 'build/rtl/ExeUnit_17.sv'):\n        c.pin(files, Path(cfg['hardware_source']) / rel)\n", "    # physical_identity has checked the fixed dot16 report and all actual runtime inputs.\n")
        edit("two_fresh_normal_first_forwards", "four_fresh_normal_first_forwards")
        edit("log-end=0; original bare O2/T13 printf retained; original DiffTest/UART enabled", "log-end=0; fixed dot16 TRACE0; original DiffTest and complete UART enabled")
        edit("    output.mkdir(parents=True); cwd = output / 'cwd'; (cwd / 'build').mkdir(parents=True)\n    for name, value in checker.AUX.items():\n        path = cwd / 'build' / name; shutil.copyfile(Path(cfg['hardware_source']) / 'build' / name, path); c.pin(files, path, value)\n", "    output.mkdir(parents=True); cwd = output / 'cwd'; cwd.mkdir()\n    # The fixed TRACE0 EMU uses its explicit flash/reference; no old T17 trace auxiliaries.\n")
        edit("FIRST_FORWARD_PSQ_TARGET_DIFFTEST_PASS", "FIRST_FORWARD_W2NP_TARGET_DIFFTEST_PASS")
        edit("both exact normal P/PQ target cases", "all four exact normal target cases")
        edit("two independently launched, owned and audited original EMUs", "four independently launched, owned and audited fixed EMUs")
    elif name == 'audit.py':
        edit("\"\"\"Read complete first-token raw logs without copying or retaining the event stream.\"\"\"", "\"\"\"Audit complete dot16 TRACE0 raw logs without claiming retirement traces.\"\"\"")
        edit("from collections import Counter\n", "")
        edit("stream, projection = norm.stream, norm.projection", "stream = norm.stream")
        edit("r2-s3-first-forward-psq-resources-v1", "r3-dot16-first-forward-w2np-resources-v1")
        edit("TARGET_CASES = (('paired16', 0x50313631, False), ('paired16_quantize', 0x50535131, False))", "TARGET_CASES = (('paired16', 0x50313631, False), ('paired16_quantize', 0x50535131, False),\n                ('dot16', 0x44313631, False), ('dot16_quantize', 0x44313651, False))")
        edit("r2-s3-first-forward-psq-v1", "r3-dot16-first-forward-w2np-v1")
        edit("exact P/PQ workload and method words", "exact four-arm dot16 workload and method words")
        edit("Bind the profile to the two fixed cases, independently of its receipts.", "Bind the profile to the four fixed cases, independently of its receipts.")
        edit("exact two-case P/PQ target profile", "exact four-case dot16 TRACE0 target profile")
        edit("fixed P/PQ image names, methods and UART controls", "fixed four-arm image names, methods and UART controls")
        edit("    banner.validate_runtime(uart, cfg['reference']); fatal.reject_fatal_output(uart)\n", "    banner.validate_runtime(uart, cfg['reference']); fatal.reject_fatal_output(uart)\n    need(uart.count('The first instruction of core 0 has commited. Difftest enabled.') == 1,\n         'one actual DiffTest enabled banner')\n")
        edit("(output / 'counter-source.txt').write_text(counters)", "(output / 'uart-counter-row.txt').write_text(counters)")
        edit("FIRST_FORWARD_PSQ_TARGET_DIFFTEST_PASS", "FIRST_FORWARD_W2NP_TARGET_DIFFTEST_PASS")
        edit("guest_cycles=int(spent[0]), counter_values=values, samples=samples, trap_pc=hex(trap_pc), custom=custom,", "guest_cycles=int(spent[0]), counter_values=values, counter_hex=list(match.groups()[1:]),\n        counter_retirement_verified=False, samples=samples, trap_pc=hex(trap_pc), custom=custom,")
        edit("one prescribed-prepare first p0 token1 complete forward, original DiffTest, zero custom commits and four CSR chains", "one prescribed-prepare first p0 token1 complete forward, original DiffTest and UART CSR observations; TRACE0 retirement evidence not collected")
        cut('def custom_sites(', 'def validate(', '')
        cut('    sites = custom_sites(', '    banner.validate_runtime(', "    # Reuse only the original bounded raw-line reader, not its trace protocol.\n    # The old non-O2 residue limit remains the complete TRACE0 text limit.\n    with ExitStack() as stack:\n        reader = stream.Reader([stack.enter_context(path.open('r', encoding='utf-8')) for path in logs])\n        parts, size = [], 0\n        for line in reader.lines():\n            size += len(line.encode())\n            need(size <= stream.MAX_RESIDUAL, 'complete TRACE0 text within original residue bound')\n            parts.append(line)\n        uart = ''.join(parts)\n")
        cut('    # Reuse the exact numerical gate', '    output.mkdir(', "    # These are exact UART words and static CSR sites, not a retirement proof.\n    counters = lines[1] + '\\n'\n    protocol = dict(status='NOT_COLLECTED_TRACE0', event_protocol_verified=False)\n    timing = dict(status='UART_CSR_OBSERVATION_ONLY',\n        counter_hex=list(match.groups()[1:]), counter_values=values,\n        static_counter_sites=build['counter_sites'], retirement_association_verified=False,\n        samples=samples)\n    custom = dict(status='NOT_COLLECTED_TRACE0', retired_count=None,\n        exact_dynamic_count_claimed=False, pc_digest=None)\n")
    else:
        raise ValueError('unknown target source: ' + name)
    restored = text
    for row in reversed(changes):
        need(sha(restored.encode()) == row['output_sha256'], 'exact target inverse intermediate output')
        for start in reversed(row['output_positions']):
            need(restored[start:start + len(row['after'])] == row['after'], 'exact target inverse span')
            restored = restored[:start] + row['before'] + restored[start + len(row['after']):]
        need(sha(restored.encode()) == row['input_sha256'], 'exact target inverse intermediate input')
    need(restored.encode() == original, 'whole original P/PQ target source recovered')
    compile(text, name, 'exec')
    return text, changes


def prepare(args):
    need(sys.dont_write_bytecode, '-B required; frozen inputs stay read-only')
    reference, paired, output = (path.resolve() for path in
                                 (args.reference_controller, args.paired_target, args.output))
    need(all(path.is_absolute() for path in
             (args.reference_controller, args.paired_target, args.output)), 'explicit absolute controller paths')
    need(not output.exists() and not any(output.is_relative_to(root) or root.is_relative_to(output)
         for root in (HERE, reference, paired)), 'fresh separate target controller')
    need(all(value > 0 for value in (args.max_cycles, args.timeout, args.raw_limit)),
         'explicit positive resource budget; no implicit old campaign limits')
    budget = dict(max_cycles=args.max_cycles, external_timeout_seconds=args.timeout,
                  max_output_file_bytes=args.raw_limit)
    need(digest(paired / 'binding.json') == PARENT_BINDING_SHA, 'exact actual P/PQ target controller binding')
    parent = read(paired / 'binding.json')
    parent_files = inventory(paired)
    need(parent['contract'] == 'r2-s3-first-forward-psq-v1'
         and parent['target_entry_scripts_included'] is True
         and parent['target_cases'] == ['paired16', 'paired16_quantize']
         and set(parent_files) == set(parent['generated_files']) | {'binding.json'}
         and all(parent_files[name] == pin for name, pin in parent['generated_files'].items()),
         'complete unchanged fixed target source controller')
    for name, pin in PARENT_PINS.items():
        need(digest(paired / (name + '.py')) == pin, 'fixed actual P/PQ target source: ' + name)
    binding = read(reference / 'binding.json')
    before = inventory(reference)
    need(binding['contract'] == CONTRACT
         and binding['status'] == 'FIRST_FORWARD_W2NP_CONTROLLER_BOUND_NOT_RUNTIME'
         and binding['reference_cases'] == ['negative', *ACTIVE]
         and binding['target_cases'] == [] and binding['target_entry_scripts_included'] is False,
         'new four-arm reference-only controller')
    need(set(before) == set(binding['generated_files']) | {'binding.json'}
         and all(before[name] == pin for name, pin in binding['generated_files'].items()),
         'complete exact four-arm source closure')
    configured_roots = []
    for name, value in binding['config'].items():
        source = Path(value)
        need(source.is_absolute(), 'absolute configured source: ' + name)
        source = source.resolve()
        need(source.exists(), 'existing configured source: ' + name)
        configured_roots.append(source.parent if source.is_file() else source)
    need(not any(output.is_relative_to(root) or root.is_relative_to(output) for root in configured_roots),
         'target output outside every configured source and frozen input root')
    original_pins = dict(binding['input_files'])
    for path, pin in original_pins.items():
        need(digest(path) == pin, 'original reference provenance input: ' + path)
    prefix = 'target-support/'
    expected = {name[len(prefix):]: pin for name, pin in parent['generated_files'].items() if name.startswith(prefix)}
    prior = {name[len(prefix):]: pin for name, pin in before.items() if name.startswith(prefix)}
    changed = {name: dict(reference_sha256=prior[name], target_sha256=pin)
               for name, pin in expected.items() if name in prior and prior[name] != pin}
    excluded = {name: pin for name, pin in prior.items() if name not in expected}
    added = {name: pin for name, pin in expected.items() if name not in prior}
    need(len(prior) == 56 and len(expected) == 93 and set(changed) == CHANGED
         and set(excluded) == EXCLUDED and len(added) == 40
         and inventory(paired / 'target-support') == expected,
         'same actual 93-source target closure and original 7/3/40 adaptation')
    unchanged = {name: pin for name, pin in before.items()
                 if name not in ('binding.json', 'BUDGET.md') and not name.startswith(prefix)}
    reserved = {'reference-binding.json', 'reference-BUDGET.md', 'prepare_target.py',
                'psq-target-run.py', 'psq-target-audit.py', 'target-transformations.json', 'run.py', 'audit.py'}
    need(not reserved.intersection(before), 'fresh target-only controller member names')
    output.mkdir()
    for name in unchanged:
        dest = output / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(reference / name, dest)
    shutil.copyfile(reference / 'binding.json', output / 'reference-binding.json')
    shutil.copyfile(reference / 'BUDGET.md', output / 'reference-BUDGET.md')
    for name in expected:
        dest = output / prefix / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(paired / prefix / name, dest)
    transformations = {}
    for name in ('run.py', 'audit.py'):
        original = (paired / name).read_bytes()
        text, transformations[name] = transform(name, original, budget)
        (output / name).write_text(text)
        (output / ('psq-target-' + name)).write_bytes(original)
    shutil.copyfile(HERE / 'prepare_target.py', output / 'prepare_target.py')
    proof = dict(status='DOT16_FORWARD_TARGET_SOURCE_PREPARED_NOT_RUNTIME',
        source_target_binding_sha256=PARENT_BINDING_SHA,
        reference_binding_sha256=before['binding.json'], source_pins=PARENT_PINS,
        edits=transformations, original_target_sources_recovered=True,
        original_process_owner_and_scheduler_control_flow_unchanged=True,
        unchanged_reference_files=unchanged, changed_helpers=changed, excluded_helpers=excluded, added_helpers=added,
        target_support_members=93, target_cases=[list(case) for case in TARGET_CASES], resource_values=budget,
        trace_protocol_collected=False, dynamic_custom_retirement_collected=False,
        csr_retirement_association_collected=False, new_builds=0, new_reference_runs=0, new_target_emu_runs=0,
        resource_profile_frozen=False, outer_launch_contract_frozen=False,
        reference_reaudit_required=True, physical_reaudit_required=True, performance_qualified=False,
        full_retirement_window_audited=False)
    save(output / 'target-transformations.json', proof)
    (output / 'BUDGET.md').write_text(
        '# Four-arm TRACE0 target source\n\n'
        + json.dumps(budget, indent=2) + '\n\n'
        'Exactly four fresh normal EMU processes; each instance uses one declared CPU. '
        'The shared total remains at most four CPUs. No automatic restart or budget extension. '
        'The existing 64 KiB physical-line and 16 MiB complete text limits remain in the raw reader. '
        'The resource profile must separately bind real CPU slots, operation ID, all input identities, '
        'the completed new reference campaign and the four method-only images before launch. '
        'The outer operation owner and its wall-clock/cleanup budget are not created here. '
        'This preparer launches no build, host probe, reference or EMU.\n')
    for name, pin in before.items():
        binding['input_files'][str(reference / name)] = pin
    for name, pin in expected.items():
        binding['input_files'][str(paired / prefix / name)] = pin
    for path in (paired / 'binding.json', paired / 'run.py', paired / 'audit.py', HERE / 'prepare_target.py'):
        binding['input_files'][str(path)] = digest(path)
    binding.update(target_cases=list(ACTIVE), target_entry_scripts_included=True,
        target_support_files=93, target_support_source_identity='fixed original P/PQ target source closure; source reuse only',
        target_host_adaptation=dict(proof='target-transformations.json',
            reference_binding_sha256=before['binding.json'], original_target_binding_sha256=PARENT_BINDING_SHA),
        target_resource_values=budget, target_evidence_scope='TRACE0; UART observations without retirement claims')
    binding['generated_files'] = inventory(output)
    save(output / 'binding.json', binding)
    need(inventory(reference) == before and inventory(paired) == parent_files, 'both original source parents unchanged')
    need(all(digest(output / name) == pin for name, pin in unchanged.items()), 'all copied reference logic unchanged')
    need(inventory(output / 'target-support') == expected
         and set(inventory(output)) == set(binding['generated_files']) | {'binding.json'}, 'complete prepared target closure')
    for path, pin in binding['input_files'].items():
        need(digest(path) == pin, 'source input unchanged after target preparation: ' + path)
    need(all(binding['input_files'][path] == pin for path, pin in original_pins.items()), 'all original provenance pins retained')
    return dict(status=proof['status'], output=str(output), binding_sha256=digest(output / 'binding.json'),
        target_cases=[list(case) for case in TARGET_CASES], resource_values=budget,
        new_builds=0, new_reference_runs=0, new_target_emu_runs=0, resource_profile_frozen=False,
        outer_launch_contract_frozen=False, performance_qualified=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('reference-controller', 'paired-target', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('max-cycles', 'timeout', 'raw-limit'):
        parser.add_argument('--' + name, type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args)), flush=True)
