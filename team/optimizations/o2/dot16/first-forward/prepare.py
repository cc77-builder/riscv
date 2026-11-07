"""Prepare a distinct four-arm dot16 forward controller. No compiler or guest.

The fixed P/PQ preparer remains unchanged. This file adds bounded, reversible
edits and explicit selected-kernel/hardware identities to its new output.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import sys

HERE = Path(__file__).resolve().parent
CONTRACT = 'r3-dot16-first-forward-v1'
PARENT_PINS = {
    'prepare.py': '4e8ed98eb776092e35bbef0cd6b47df667ffd8322434bb52b3db2e96485d3605',
    'derive_extension.py': '65bbf59f8784295daa384a646b0b68a0c320e524463fba4ae38c72288649e49e',
    'inspect_quantize.py': '76c248339ad4a2f2fac4b2256b2139c3147c771f53e41b378ea92297e58feef5',
    'CONTRACT.md': '1b56065bcb4c41156ac3d4e16fe549f5ec5f60b7a81f9fd6b2ac2b087bd43cea',
}
KERNELS = {
    'plain': dict(symbol='q288_dot16_vdot', bytes=484,
        function_sha256='ee92c07b7803b04c5340ba4412cb36326b8f5ed42fbf0677fc2f210bcd6711bb',
        source_sha256='f0aa30d96e4519a238b88c5fa3911080ec99d267af24579ded3ae754faf3a730',
        elf_sha256='216ed0418829bed5be00732670aed8d09532ca6f9615a68f9ea720fd05649fe5'),
    'whole2': dict(symbol='q288_dot16_whole2', bytes=412,
        function_sha256='b2b5b7fa44ecf9646a7c07fdaf971df8fad6430aec58161ffc3e2c3332d934a6',
        source_sha256='df2983a21ab85d982b51e7faa0710d536d2bd4afe5bc9c2b91577dd3450972c8',
        elf_sha256='0ea09990c578faccab105afd1942d66a3f6f9905876b2e5462ae7e0f7a0e2adc'),
}
HARDWARE_RESULT_SHA = 'e825fff45feb5afa9952140d9832ec8afe9393c02ebd1ab1558ddcfb4a63ae8f'
ACTIVE = ('paired16', 'paired16_quantize', 'dot16', 'dot16_quantize')


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


HARDWARE_CODE = r'''HARDWARE_RESULT_SHA = 'e825fff45feb5afa9952140d9832ec8afe9393c02ebd1ab1558ddcfb4a63ae8f'
DOT16_EMU_SHA = 'f14918658fcd2f19c9fb6c1d493025d98f727ac985ea73129edc58270fa6977d'
DOT16_FLASH_SHA = 'a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994'
DOT16_FLAGS = dict(VDOT_DOT16='1', VDOT_O2_ELASTIC='1', VDOT_T14_FUSED_INPUT='1',
    VDOT_O1_HANDOFF='0', VDOT_O1_TRACE='0', VDOT_O2_TRACE='0', VDOT_T12_TRACE='0', VDOT_T13_TRACE='0')
DOT16_ABI = dict(bytes=1400, regs_int=0, regs_fp=256, csr=512, pc=656,
    hcsr=664, regs_vec=800, vcsr=1312, fcsr=1368, triggercsr=1376)


def physical_identity(identity_path, physical=False):
    path = Path(identity_path).resolve()
    need(path == Path(CFG['dot16_hardware_result']).resolve()
         and digest(path) == HARDWARE_RESULT_SHA, 'fixed explicit dot16 hardware record')
    report = read(path)
    need(report['status'] == 'DOT16_FULLCORE_SMOKE_PASS'
         and report['qualification']['fixed_six_legal_case_fullcore_difftest'] is True
         and report['abi']['actual_dynamic_difftest_passed'] is True
         and report['abi']['layout'] == DOT16_ABI
         and report['source_identity']['flags'] == DOT16_FLAGS,
         'existing dot16 hardware qualification and exact ABI/flags')
    files = dict(report['runtime_inputs'])
    files[str(path)] = HARDWARE_RESULT_SHA
    verify(files)
    def unique(pin):
        paths = [p for p, value in report['runtime_inputs'].items() if value == pin]
        need(len(paths) == 1, 'unique actual fixed dot16 runtime input')
        return paths[0]
    emu, reference, flash = (unique(pin) for pin in (DOT16_EMU_SHA, REFERENCE_SHA, DOT16_FLASH_SHA))
    need(report['emu']['path'] == emu and report['emu']['sha256'] == DOT16_EMU_SHA,
         'actual previously qualified EMU')
    configuration = dict(hardware_source=str(Path(emu).parent.parent), reference=reference, flash=flash)
    need(Path(configuration['hardware_source']) / 'build/emu' == Path(emu), 'exact executable location')
    value = dict(schema=1, kind='DOT16_FIXED_RUNTIME_IDENTITY',
        configuration=configuration, reference_sha256=REFERENCE_SHA,
        hardware_result=str(path), hardware_result_sha256=HARDWARE_RESULT_SHA,
        flags=DOT16_FLAGS, abi=DOT16_ABI, runtime_inputs=files,
        prior_qualification='fixed six legal cases only; no inherited new-forward result')
    return (value, files, dict(flags=DOT16_FLAGS, abi=DOT16_ABI,
            emu_sha256=DOT16_EMU_SHA)) if physical else value


def runtime_identity(identity):
    need(identity == physical_identity(CFG['dot16_hardware_result']),
         'unchanged explicit dot16 runtime identity')
    return dict(identity['runtime_inputs']), types.SimpleNamespace(verify_files=verify)


'''


def transform(name, original, selected):
    text, changes = original.decode(), []
    def edit(before, after, count=1):
        nonlocal text
        starts = [m.start() for m in re.finditer(re.escape(before), text)]
        need(before and before != after and len(starts) == count,
             'exact dot16 source edit count: ' + name + ': ' + before[:90])
        previous = text
        for start in reversed(starts):
            text = text[:start] + after + text[start + len(before):]
        positions = [start + i * (len(after) - len(before)) for i, start in enumerate(starts)]
        changes.append(dict(before=before, after=after, count=count, output_positions=positions,
                            input_sha256=sha(previous.encode()), output_sha256=sha(text.encode())))
    if name == 'build.py':
        edit("PREFIX = 'first-forward-psq'", "PREFIX = 'first-forward-dot16'")
        edit("CORE = 'consumer-first-forward-psq.o'", "CORE = 'consumer-first-forward-dot16.o'")
        edit('FIRST_FORWARD_PSQ', 'FIRST_FORWARD_DOT16', 4)
        edit('METHODS = derive.METHODS\n', 'METHODS = derive.METHODS\nACTIVE_METHODS = derive.ACTIVE_METHODS\n')
        edit("REFERENCE_SHA = '8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9'",
             "REFERENCE_SHA = 'cc768488944941d59442727a96e0a19206e24872dcefed0052cf6cb3694a3fae'")
        edit("\n\ndef read(path):", "\nKERNELS[derive.DOT16_SYMBOL] = " +
             repr(dict(bytes=selected['bytes'], sha256=selected['function_sha256'])) + "\n\n\ndef read(path):")
        begin = text.index('def physical_identity(')
        end = text.index('def body(', begin)
        edit(text[begin:end], HARDWARE_CODE)
        edit("                         ('consumer_paired16_quantize_cache', 'q288_paired16_rvv')):",
             "                         ('consumer_paired16_quantize_cache', 'q288_paired16_rvv'),\n"
             "                         ('consumer_dot16_cache', derive.DOT16_SYMBOL),\n"
             "                         ('consumer_dot16_quantize_cache', derive.DOT16_SYMBOL)):")
        old_entries = "'r2_w2_forward', 'r2_w2_gs32_forward', 'r2_w2_paired16_forward', 'r2_w2_paired16_quantize_forward'"
        new_entries = old_entries + ", 'r2_w2_dot16_forward', 'r2_w2_dot16_quantize_forward'"
        edit(old_entries, new_entries, 3)
        edit("== [" + new_entries + "],", "== sorted([" + new_entries + "]),")
        edit('four actual public entries, including the new PQ branch',
             'six compiled public entries; the execution inventory is explicitly four arms')
        edit("for name in ('gs32', 'paired16', 'paired16_quantize'):",
             "for name in ('gs32', 'paired16', 'paired16_quantize', 'dot16', 'dot16_quantize'):")
        edit("'consumer_gs32_cache', 'consumer_paired16_cache', 'consumer_paired16_quantize_cache')",
             "'consumer_gs32_cache', 'consumer_paired16_cache', 'consumer_paired16_quantize_cache',\n"
             "                 'consumer_dot16_cache', 'consumer_dot16_quantize_cache')", 2)
        edit("need(len(norm_calls) == 21, 'exact seven consumer norm route scope')",
             "need(len(norm_calls) == 27, 'exact nine retained-plus-new consumer norm route scope')")
        edit("Path(CFG['gs32_screen']), Path(CFG['paired16_screen'])))",
             "Path(CFG['gs32_screen']), Path(CFG['paired16_screen']),\n"
             "             Path(CFG['dot16_source']).parent, Path(CFG['dot16_elf']).parent,\n"
             "             Path(CFG['dot16_hardware_result']).parent))")
        marker = "        old_argv = read(parent / 'derivation.json')['derived_compile_argv']"
        extract = r'''        dot16_text = Path(CFG['dot16_source']).read_text()
        name = derive.DOT16_SYMBOL
        matches = re.findall(r'(?ms)^\.global ' + re.escape(name) +
            r'\n.*?^\.size ' + re.escape(name) + r', \.-' + re.escape(name) + r'\n', dot16_text)
        need(len(matches) == 1 and dot16_text.endswith(matches[0]), 'unique complete selected dot16 function')
        (source / 'dot16.S').write_text('.option norvc\n.option norelax\n.text\n.balign 64\n' + matches[0])
'''
        edit(marker, extract + marker)
        marker = "        shutil.copyfile(Path(CFG['quantize_build']) / 'source/candidate.o', output / 'quantize.o')"
        compile_dot16 = """        command([tools['gcc']['path'], '-march=rv64gv', '-mabi=lp64d', '-mno-relax', '-c', source / 'dot16.S',
                 '-o', output / 'dot16.o'], output, 'dot16-compile', timeout=60)
"""
        edit(marker, compile_dot16 + marker)
        edit("output / 'paired16.o', output / 'quantize.o'],",
             "output / 'paired16.o', output / 'quantize.o', output / 'dot16.o'],")
        marker = "        image = (output / (PREFIX + '.bin')).read_bytes()"
        check_dot16 = """        selected_elf = c.base.f.g.ELF(Path(CFG['dot16_elf']).read_bytes())
        need(body(elf, derive.DOT16_SYMBOL) == body(selected_elf, derive.DOT16_SYMBOL),
             'whole selected dot16 function matches the pinned source ELF')
"""
        edit(marker, check_dot16 + marker)
        edit("CORE, 'consumer-core.o', 'gs32.o', 'paired16.o', 'quantize.o', 'dump-plan.txt'",
             "CORE, 'consumer-core.o', 'gs32.o', 'paired16.o', 'quantize.o', 'dot16.o', 'dump-plan.txt'")
        edit("methods=METHODS, reference_runs=0, target_emu_runs=0, performance_qualified=False,",
             "methods=METHODS, active_methods=list(ACTIVE_METHODS), selected_dot16_kernel=BINDING['selected_dot16_kernel'],\n"
             "            reference_runs=0, target_emu_runs=0, performance_qualified=False,")
    elif name == 'reference.py':
        edit("CASES = [('negative', b.METHODS['paired16_quantize'], True),\n"
             "         ('paired16', b.METHODS['paired16'], False), ('paired16_quantize', b.METHODS['paired16_quantize'], False)]",
             "CASES = [('negative', b.METHODS['dot16_quantize'], True)] + [\n"
             "    (name, b.METHODS[name], False) for name in b.ACTIVE_METHODS]")
        edit("method in (b.METHODS['paired16'], b.METHODS['paired16_quantize'])",
             "method in tuple(b.METHODS[name] for name in b.ACTIVE_METHODS)")
        edit("not negative or method == b.METHODS['paired16_quantize']",
             "not negative or method == b.METHODS['dot16_quantize']")
        edit("for name in ('paired16', 'paired16_quantize'):",
             "for name in b.ACTIVE_METHODS:")
        edit("need(set(validations) == {'negative', 'paired16', 'paired16_quantize'}, 'exact new three-case campaign')",
             "need(set(validations) == {'negative', *b.ACTIVE_METHODS}, 'exact four normal arms plus one DQ negative')")
        edit("state['reference_runs'] == 3", "state['reference_runs'] == len(CASES)")
        edit("len({row['pid'] for row in state['records']}) == 3",
             "len({row['pid'] for row in state['records']}) == len(CASES)")
        edit('three closed independent reference processes', 'five closed independent reference processes')
        edit('reference_runs=3,', 'reference_runs=len(CASES),')
        edit('FIRST_FORWARD_PSQ', 'FIRST_FORWARD_DOT16', 2)
    elif name == 'inspect_quantize.py':
        edit("('consumer_paired16_quantize_cache',qname)):",
             "('consumer_paired16_quantize_cache',qname),\n"
             "                          ('consumer_dot16_cache','quantize'),('consumer_dot16_quantize_cache',qname)):")
        edit('PSQ_QUANTIZE_ACTUAL_ELF_IDENTITY_PASS', 'DOT16_FORWARD_QUANTIZE_ACTUAL_ELF_IDENTITY_PASS')
    else:
        raise ValueError('unknown dot16 controller source: ' + name)
    restored = text
    for row in reversed(changes):
        need(sha(restored.encode()) == row['output_sha256'], 'inverse intermediate dot16 output')
        for start in reversed(row['output_positions']):
            need(restored[start:start + len(row['after'])] == row['after'], 'exact inverse dot16 span')
            restored = restored[:start] + row['before'] + restored[start + len(row['after']):]
        need(sha(restored.encode()) == row['input_sha256'], 'inverse intermediate dot16 input')
    need(restored.encode() == original, 'whole original P/PQ controller recovered')
    compile(text, name, 'exec')
    return text, changes


def prepare(args):
    need(sys.dont_write_bytecode, '-B required; all old inputs stay read-only')
    parent, output = args.paired_consumer.resolve(), args.output.resolve()
    roots = (HERE, parent, args.base.resolve(), args.config.resolve().parent, args.quantize.resolve(),
             args.kernel_source.resolve().parent, args.kernel_elf.resolve().parent,
             args.hardware_result.resolve().parent)
    need(args.output.is_absolute() and not output.exists()
         and not any(output.is_relative_to(root) for root in roots), 'fresh separate new controller')
    for name, pin in PARENT_PINS.items():
        need(digest(parent / name) == pin, 'fixed original P/PQ preparation input: ' + name)
    selected = KERNELS[args.kernel]
    need(digest(args.kernel_source) == selected['source_sha256']
         and digest(args.kernel_elf) == selected['elf_sha256'], 'explicit fixed complete selected kernel sources')
    need(digest(args.hardware_result) == HARDWARE_RESULT_SHA, 'existing dot16 hardware report identity')
    hardware = json.loads(args.hardware_result.read_text())
    need(hardware['status'] == 'DOT16_FULLCORE_SMOKE_PASS', 'existing fixed hardware result')
    spec = importlib.util.spec_from_file_location('dot16_parent_psq_prepare', parent / 'prepare.py')
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    binding = old.prepare(args.base.resolve(), args.config.resolve(), args.quantize.resolve(), output)
    prior_binding = (output / 'binding.json').read_bytes()
    (output / 'psq-binding.json').write_bytes(prior_binding)
    for name in ('build.py', 'reference.py', 'derive.py', 'inspect_quantize.py',
                 'prepare.py', 'derive_extension.py', 'CONTRACT.md', 'BUDGET.md'):
        (output / ('psq-' + name)).write_bytes((output / name).read_bytes())
    proofs = {}
    for name in ('build.py', 'reference.py', 'inspect_quantize.py'):
        original = (output / name).read_bytes()
        changed, proofs[name] = transform(name, original, selected)
        (output / name).write_text(changed)
    original = (output / 'derive.py').read_bytes()
    extension = (HERE / 'derive_extension.py').read_text()
    need(extension.count('__SELECTED_DOT16_SYMBOL__') == 1, 'one explicit kernel placeholder')
    actual_extension = extension.replace('__SELECTED_DOT16_SYMBOL__', selected['symbol'])
    combined = original + b'\n\n' + actual_extension.encode()
    compile(combined, 'derive.py', 'exec')
    (output / 'derive.py').write_bytes(combined)
    proofs['derive.py'] = dict(parent_sha256=sha(original),
        template_extension_sha256=sha(extension.encode()), actual_extension_sha256=sha(actual_extension.encode()),
        original_prefix_unchanged=True, selected_symbol=selected['symbol'])
    for name in ('prepare.py', 'derive_extension.py', 'CONTRACT.md'):
        raw = (HERE / name).read_bytes()
        (output / name).write_bytes(raw)
        binding['input_files'][str(HERE / name)] = sha(raw)
    (output / 'BUDGET.md').write_text(
        '# Four-arm reference preparation\n\nGNU build and reference queue each use one coordinated CPU. '
        'Exactly four normal reference cases plus one DQ last-logit negative; each original reference owner '
        'retains 100M API calls / 600s internal / 630s external bounds. '
        'Whole-operation CPU, elapsed and output budgets must be frozen separately before execution. '
        'No target EMU entry script is included; no automatic launch or budget extension.\n')
    binding['config'].update(dot16_source=str(args.kernel_source.resolve()),
        dot16_elf=str(args.kernel_elf.resolve()), dot16_hardware_result=str(args.hardware_result.resolve()))
    for path, pin in ((args.kernel_source, selected['source_sha256']),
                      (args.kernel_elf, selected['elf_sha256']), (args.hardware_result, HARDWARE_RESULT_SHA)):
        binding['input_files'][str(path.resolve())] = pin
    for path, pin in hardware['runtime_inputs'].items():
        need(digest(path) == pin, 'unchanged fixed dot16 physical input: ' + path)
        binding['input_files'][path] = pin
    for name, pin in PARENT_PINS.items():
        binding['input_files'][str(parent / name)] = pin
    binding.update(contract=CONTRACT, status='FIRST_FORWARD_DOT16_CONTROLLER_BOUND_NOT_RUNTIME',
        psq_binding_sha256=sha(prior_binding), dot16_transformations=proofs,
        selected_dot16_kernel=dict(choice=args.kernel, **selected),
        reference_cases=['negative', *ACTIVE], target_cases=[], target_entry_scripts_included=False,
        target_evidence_scope='planned TRACE0; no trace or dynamic-retirement qualification inherited',
        reference_runs=0, target_emu_runs=0, performance_qualified=False)
    binding['generated_files'] = {
        str(path.relative_to(output)): digest(path)
        for path in output.rglob('*') if path.is_file() and path != output / 'binding.json'}
    (output / 'binding.json').write_text(json.dumps(binding, indent=2) + '\n')
    for path, pin in binding['input_files'].items():
        need(digest(path) == pin, 'input unchanged after dot16 preparation: ' + path)
    return binding


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('paired-consumer', 'base', 'config', 'quantize', 'kernel-source', 'kernel-elf',
                 'hardware-result', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--kernel', choices=tuple(KERNELS), required=True)
    args = parser.parse_args()
    result = prepare(args)
    print(json.dumps(dict(contract=CONTRACT, status=result['status'], output=str(args.output),
                          kernel=args.kernel, reference_runs=0, target_emu_runs=0)), flush=True)
