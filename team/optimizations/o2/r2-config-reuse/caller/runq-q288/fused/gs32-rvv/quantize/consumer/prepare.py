"""Prepare a new G/GQ reference controller from exact closed team inputs.

This derivation executes no guest. The numerical comparator and process owner
are retained from the existing first-forward controller. All edits are exactly
reversible; original inputs remain read-only.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import sys

HERE = Path(__file__).resolve().parent
CONTRACT = 'r2-s3-first-forward-gsq-v1'
BASE_PINS = {
    'bind.py': '7794317256c641688ed60eeccb268ecb9c65f69c04aa4c166cbbc79919585381',
    'build.py': 'a508d5b0d22f73aa198a66f9da7f62e24c8d3a4cf3a00ac11e9a6a57e8624a5c',
    'derive.py': 'eabb68810a9f0fbfbddb58774b85f1fe37e6cf18a6e0f00452df5ea651d5cfb7',
    'CONTRACT.md': 'fa78799c2d89131d646f160667fd3990bebc0b56926a2779219ec9648a604332',
    'BUDGET.md': 'b1a02f82536c7235476ab0cdf3f760bb808ccc4974b054a7ebce3934ae06af6a',
}
QUANTIZE_PINS = {
    'result.json': 'b902b0ac415c1f250dea5f44acc17f542793ed7e6315e1a81911ef998c469a65',
    'build.json': '6e8aa4971d0bb8b0d11bfbf0aa9565e5f653df879129f63669e52f91dd176c13',
    'state.json': '19ab64f8e0bf903542813fa0f04eed5f4ade6980f2d5a11cc355acfccecb5ad9',
    'quantize-gs32-check.elf': 'a428f20d3c6d67ab074320f33932289a35243d485e909148f5e9bbdccdc722ec',
    'source/candidate.o': 'bfceecb3771168c20d5496a38fc581db0fb9b9ae1959038a7e4a3807e31d1215',
    'source/quantize.S': 'ad377a29fce0226cb30ccc5c2526cb672ea413c5ff3a7ec4103c9cdb22129197',
    'source/verify.py': 'cf60648f3e76477c8cc3ba9b4c1500728fbc1597bc7dfde4b32dc13fbeabb5e4',
    'source/oracle.json': 'e6c784d2cc143b6a39bf864f1d709f81a8a6f0059c6595ad478483d4fea513a3',
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def transform(name, original):
    text, changes = original.decode(), []

    def edit(before, after, count=1):
        nonlocal text
        starts = [m.start() for m in re.finditer(re.escape(before), text)]
        need(before and before != after and len(starts) == count,
             'exact edit count: ' + name + ': ' + before[:90])
        previous = text
        for start in reversed(starts):
            text = text[:start] + after + text[start + len(before):]
        positions = [start + i * (len(after) - len(before)) for i, start in enumerate(starts)]
        changes.append(dict(before=before, after=after, count=count, output_positions=positions,
                            input_sha256=sha(previous.encode()), output_sha256=sha(text.encode())))

    if name == 'build.py':
        edit("PREFIX = 'first-forward-rvv'", "PREFIX = 'first-forward-gsq'")
        edit("CORE = 'consumer-first-forward-rvv.o'", "CORE = 'consumer-first-forward-gsq.o'")
        edit('FIRST_FORWARD_RVV', 'FIRST_FORWARD_GSQ', 4)
        edit("                         ('consumer_paired16_cache', 'q288_paired16_rvv')):",
             "                         ('consumer_paired16_cache', 'q288_paired16_rvv'),\n"
             "                         ('consumer_gs32_quantize_cache', 'q288_gs32_rvv')):")
        edit("'r2_w2_forward', 'r2_w2_gs32_forward', 'r2_w2_paired16_forward'",
             "'r2_w2_forward', 'r2_w2_gs32_forward', 'r2_w2_gs32_quantize_forward', 'r2_w2_paired16_forward'", 3)
        edit('three real existing public entries in the dispatcher',
             'four actual public entries, including the new GQ branch')
        edit("for name in ('gs32', 'paired16'):", "for name in ('gs32', 'paired16', 'gs32_quantize'):")
        edit("'consumer_gs32_cache', 'consumer_paired16_cache')",
             "'consumer_gs32_cache', 'consumer_paired16_cache', 'consumer_gs32_quantize_cache')", 2)
        edit("need(len(norm_calls) == 18, 'exact six consumer norm route scope')",
             "need(len(norm_calls) == 21, 'exact seven consumer norm route scope')")
        edit("    result['routing_identity'] = routing(elf, dis)\n",
             "    result['routing_identity'] = routing(elf, dis)\n"
             "    quantize_inspector = load('gsq_quantize_identity', HERE / 'inspect_quantize.py')\n"
             "    result['quantize_identity'] = quantize_inspector.inspect(\n"
             "        sys.modules[__name__] if __name__ in sys.modules else\n"
             "        types.SimpleNamespace(need=need, c=c, g=g, signed=signed, load=load, digest=digest),\n"
             "        elf, dis, Path(CFG['quantize_build']))\n")
        edit("        command([tools['ld']['path'], '-r', '--no-relax', '-o', output / CORE, output / 'consumer-core.o',\n"
             "                 source / 'candidate.o', source / 'norm.o', output / 'gs32.o', output / 'paired16.o'],",
             "        shutil.copyfile(Path(CFG['quantize_build']) / 'source/candidate.o', output / 'quantize.o')\n"
             "        shutil.copyfile(Path(CFG['quantize_build']) / 'source/quantize.S', source / 'quantize.S')\n"
             "        need(digest(output / 'quantize.o') == 'bfceecb3771168c20d5496a38fc581db0fb9b9ae1959038a7e4a3807e31d1215',\n"
             "             'exact independently qualified quantize object')\n"
             "        command([tools['ld']['path'], '-r', '--no-relax', '-o', output / CORE, output / 'consumer-core.o',\n"
             "                 source / 'candidate.o', source / 'norm.o', output / 'gs32.o', output / 'paired16.o', output / 'quantize.o'],")
        edit("CORE, 'consumer-core.o', 'gs32.o', 'paired16.o', 'dump-plan.txt'",
             "CORE, 'consumer-core.o', 'gs32.o', 'paired16.o', 'quantize.o', 'dump-plan.txt'")
    elif name == 'reference.py':
        edit("CASES = [('negative', b.METHODS['paired16'], True), ('fr', b.METHODS['fr'], False),\n"
             "         ('gs32', b.METHODS['gs32'], False), ('paired16', b.METHODS['paired16'], False),\n"
             "         ('replay', b.METHODS['paired16'], False)]",
             "CASES = [('negative', b.METHODS['gs32_quantize'], True),\n"
             "         ('gs32', b.METHODS['gs32'], False), ('gs32_quantize', b.METHODS['gs32_quantize'], False)]")
        edit('method in b.METHODS.values()', "method in (b.METHODS['gs32'], b.METHODS['gs32_quantize'])")
        edit("not negative or method == b.METHODS['paired16']",
             "not negative or method == b.METHODS['gs32_quantize']")
        edit("for name, method in b.METHODS.items():",
             "for name in ('gs32', 'gs32_quantize'):\n        method = b.METHODS[name]")
        edit("        need(validations['paired16'] == validations['replay'], 'complete independent reference replay')",
             "        need(set(validations) == {'negative', 'gs32', 'gs32_quantize'}, 'exact new three-case campaign')")
        edit("state['reference_runs'] == 5", "state['reference_runs'] == 3")
        edit("len({row['pid'] for row in state['records']}) == 5",
             "len({row['pid'] for row in state['records']}) == 3")
        edit('five closed independent reference processes', 'three closed independent reference processes')
        edit('reference_runs=5,', 'reference_runs=3,')
        edit('FIRST_FORWARD_RVV', 'FIRST_FORWARD_GSQ', 2)
    else:
        raise ValueError('unknown controller transformation: ' + name)
    restored = text
    for row in reversed(changes):
        need(sha(restored.encode()) == row['output_sha256'], 'inverse intermediate output identity')
        for start in reversed(row['output_positions']):
            need(restored[start:start + len(row['after'])] == row['after'], 'inverse exact span')
            restored = restored[:start] + row['before'] + restored[start + len(row['after']):]
        need(sha(restored.encode()) == row['input_sha256'], 'inverse intermediate input identity')
    need(restored.encode() == original, 'entire original controller recovered')
    compile(text, name, 'exec')
    return text, changes


def prepare(base, config, quantize, output):
    need(sys.dont_write_bytecode, '-B required; original source stays untouched')
    need(not output.exists(), 'fresh separate G/GQ controller')
    for root, pins in ((base, BASE_PINS), (quantize, QUANTIZE_PINS)):
        for name, value in pins.items():
            need(sha((root / name).read_bytes()) == value, 'exact closed input: ' + str(root / name))
    qualification = json.loads((quantize / 'result.json').read_text())
    need(qualification['status'] == 'GS32_QUANTIZE_BOUNDED_REFERENCE_PASS'
         and qualification['reference_runs'] == 4 and qualification['performance_qualified'] is False,
         'actual bounded prototype qualification; not performance')
    spec = importlib.util.spec_from_file_location('gsq_parent_controller_binding', base / 'bind.py')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    binding = parent.bind(config, output)
    parent_binding_raw = (output / 'binding.json').read_bytes()
    (output / 'parent-binding.json').write_bytes(parent_binding_raw)
    proofs = {}
    for name in ('build.py', 'reference.py'):
        original = (output / name).read_bytes()
        (output / ('parent-' + name)).write_bytes(original)
        changed, proofs[name] = transform(name, original)
        (output / name).write_text(changed)
    original = (output / 'derive.py').read_bytes()
    extension = (HERE / 'derive_extension.py').read_bytes()
    combined = original + b'\n\n' + extension
    compile(combined, 'derive.py', 'exec')
    (output / 'parent-derive.py').write_bytes(original)
    (output / 'derive.py').write_bytes(combined)
    proofs['derive.py'] = dict(parent_sha256=sha(original), extension_sha256=sha(extension),
                               original_prefix_unchanged=True, added_bytes=2 + len(extension))
    for name in ('CONTRACT.md', 'BUDGET.md'):
        (output / ('parent-' + name)).write_bytes((output / name).read_bytes())
    for name in ('prepare.py', 'derive_extension.py', 'inspect_quantize.py', 'CONTRACT.md'):
        raw = (HERE / name).read_bytes()
        (output / name).write_bytes(raw)
        binding['input_files'][str(HERE / name)] = sha(raw)
    (output / 'BUDGET.md').write_text(
        '# G/GQ reference batch\n\nCPU1; GNU -j1; exactly three serial original NEMU processes at most; '
        '100M API calls / 600s internal / 630s owner per process; 2100s whole batch including preparation '
        'and cleanup. No automatic extension; no target EMU; no performance qualification.\n')
    # These newly generated, never executed target entry scripts are outside
    # this reference-only contract. Their original derivation is retained.
    for name in ('run.py', 'audit.py'):
        (output / name).unlink()
    binding.update(contract=CONTRACT, status='FIRST_FORWARD_GSQ_CONTROLLER_BOUND_NOT_RUNTIME',
                   parent_binding_sha256=sha(parent_binding_raw), gsq_transformations=proofs,
                   reference_cases=['negative', 'gs32', 'gs32_quantize'], target_cases=[],
                   target_entry_scripts_included=False)
    binding['config']['quantize_build'] = str(quantize)
    for name, value in QUANTIZE_PINS.items():
        binding['input_files'][str(quantize / name)] = value
    binding['generated_files'] = {
        str(p.relative_to(output)): sha(p.read_bytes())
        for p in output.rglob('*') if p.is_file() and p != output / 'binding.json'}
    (output / 'binding.json').write_text(json.dumps(binding, indent=2) + '\n')
    for path, value in binding['input_files'].items():
        need(sha(Path(path).read_bytes()) == value, 'input unchanged after preparation: ' + path)
    return binding


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'config', 'quantize', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = prepare(*(getattr(args, name).resolve() for name in ('base', 'config', 'quantize', 'output')))
    print(json.dumps(dict(contract=CONTRACT, status=result['status'],
                         output=str(args.output), reference_runs=0, target_emu_runs=0)), flush=True)
