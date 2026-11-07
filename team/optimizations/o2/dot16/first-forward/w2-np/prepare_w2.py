#!/usr/bin/env python3
"""Prepare one isolated whole-consumer view from qualified narrow and W2 inputs."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
CONTRACT = 'r3-dot16-first-forward-w2np-v1'
PARENT_SHA = 'f67ed9e3831ecd58748ec9bcb23565ff38ce95b566a88cc1d746836306a66364'
REFERENCE_SHA = '7d46f70b4cb105bd468577815e21c97fe9fa249fb447eeec3c977d9236e3b8c1'
W2_SOURCE_SHA = 'fbe3a93f642ec3468da92ae776e1b547c29c527d4dffc30456191b437d1272c5'
W2_ELF_SHA = '82497a4b17533ede1484ef88c9ccd27ea00dd0259586e7fb23925155acfe8591'
W2_REFERENCE_ELF_SHA = '8d7c7b95b45d4e555912f914ee5d72482123ff4e10cd534112681824939dc86c'
W2_KERNELS = {
    'q768_dot16_whole8_narrow': dict(bytes=312, sha256='b4a0e512feafd3ae8ea7e4531e13e1a23b12f97d80b3b007be6c52c3bdea56be'),
    'q768_paired16_rvv': dict(bytes=1096, sha256='26f972751fb9882f92118ac30b98f2d0b4d1df9225be5d9cd136e7ed5c4629d3'),
}


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def edit(text, before, after, log):
    need(text.count(before) == 1 and after not in text, 'one exact build edit: ' + before[:75])
    log.append(dict(before=before, after=after))
    return text.replace(before, after, 1)


def prepare(parent, gnu, reference, output):
    need(not output.exists(), 'fresh output only')
    for source in (parent, gnu, reference, HERE):
        need(not output.is_relative_to(source) and not source.is_relative_to(output), 'separate input/output')
    pins = {}
    def pin(path, expected=None):
        p = str(Path(path).resolve()); value = sha(p)
        need(expected is None or value == expected, 'exact input: ' + p)
        need(p not in pins or pins[p] == value, 'unambiguous input')
        pins[p] = value
    pin(parent / 'binding.json', PARENT_SHA)
    binding = read(parent / 'binding.json')
    need(binding['contract'] == 'r3-dot16-first-forward-v1' and
         binding['status'] == 'FIRST_FORWARD_DOT16_CONTROLLER_BOUND_NOT_RUNTIME', 'source-only narrow parent')
    need(binding['selected_dot16_kernel']['symbol'] == 'q288_dot16_whole8_narrow', 'selected complete N')
    for p, h in binding['input_files'].items(): pin(p, h)
    for p, h in binding['generated_files'].items(): pin(parent / p, h)
    pin(reference / 'result.json', REFERENCE_SHA)
    ref = read(reference / 'result.json')
    need(ref['status'] == 'K768_N_P_REAL_FIXTURE_AND_EDGE_REFERENCE_PASS' and
         ref['reference_qualified'] is True and ref['target_emu_runs'] == 0 and
         ref['all_inputs_unchanged'] is True and ref['all_children_reaped'] is True,
         'real K768 reference evidence, without application inheritance')
    for group in ('original_inputs', 'snapshots'):
        for p, h in ref[group].items(): pin(p, h)
    pin(gnu / 'w2_np.S', W2_SOURCE_SHA); pin(gnu / 'w2_np.elf', W2_ELF_SHA)
    ref_elf = reference / 'w2-np.elf'
    pin(ref_elf, W2_REFERENCE_ELF_SHA)
    for name, expected in W2_KERNELS.items():
        need({k: ref['static_inspection']['kernels'][name][k] for k in expected} == expected,
             'actual reference whole kernel: ' + name)
    own = ('prepare_w2.py', 'w2_extension.py', 'w2_selector.py', 'selector_proof.py', 'W2_CONTRACT.md')
    for name in own: pin(HERE / name)
    output.mkdir(parents=True)
    for name, value in binding['generated_files'].items():
        target = output / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(parent / name, target); need(sha(target) == value, 'exact helper copy')
    for name in own:
        shutil.copyfile(HERE / name, output / name)
    original_derive = (parent / 'derive.py').read_text()
    extension = (HERE / 'w2_extension.py').read_text()
    (output / 'derive.py').write_text(original_derive + '\n\n' + extension)
    original = (parent / 'build.py').read_text(); build = original; edits = []
    pairs = [
        ("PREFIX = 'first-forward-dot16'", "PREFIX = 'first-forward-w2np'"),
        ("CORE = 'consumer-first-forward-dot16.o'", "CORE = 'consumer-first-forward-w2np.o'"),
        ("STATIC = 'FIRST_FORWARD_DOT16_STATIC_PASS_NOT_RUNTIME'", "STATIC = 'FIRST_FORWARD_W2NP_STATIC_PASS_NOT_RUNTIME'"),
        ("REFERENCE_PASS = 'FIRST_FORWARD_DOT16_REFERENCE_CAMPAIGN_PASS'", "REFERENCE_PASS = 'FIRST_FORWARD_W2NP_REFERENCE_CAMPAIGN_PASS'"),
        ("BINDING['status'] == 'FIRST_FORWARD_DOT16_CONTROLLER_BOUND_NOT_RUNTIME'", "BINDING['status'] == 'FIRST_FORWARD_W2NP_CONTROLLER_BOUND_NOT_RUNTIME'"),
        ("             Path(CFG['dot16_hardware_result']).parent)), 'isolated output outside every input')",
         "             Path(CFG['dot16_hardware_result']).parent, Path(CFG['w2_source']).parent,\n"
         "             Path(CFG['w2_elf']).parent, Path(CFG['w2_reference_elf']).parent)), 'isolated output outside every input')"),
        ("        expected = [kernel] * 6 + ['q288_fused_rvv4', kernel]\n",
         "        expected = ([kernel] * 8 if name in ('consumer_paired16_cache', 'consumer_paired16_quantize_cache',\n"
         "            'consumer_dot16_cache', 'consumer_dot16_quantize_cache') else [kernel] * 6 + ['q288_fused_rvv4', kernel])\n"),
        ("        w2_fr_selector=selectors[0], measured_call=", "        w2_np_selector=selectors, measured_call="),
        ("        old_argv = read(parent / 'derivation.json')['derived_compile_argv']\n",
         "        shutil.copyfile(Path(CFG['w2_source']), source / 'w2_np.S')\n"
         "        need(digest(source / 'w2_np.S') == BINDING['w2_kernels']['source_sha256'], 'complete qualified K768 source')\n"
         "        old_argv = read(parent / 'derivation.json')['derived_compile_argv']\n"),
        ("        shutil.copyfile(Path(CFG['quantize_build']) / 'source/candidate.o', output / 'quantize.o')\n",
         "        command([tools['gcc']['path'], '-march=rv64gv', '-mabi=lp64d', '-mno-relax', '-c', source / 'w2_np.S',\n"
         "                 '-o', output / 'w2_np.o'], output, 'w2-np-compile', timeout=60)\n"
         "        shutil.copyfile(Path(CFG['quantize_build']) / 'source/candidate.o', output / 'quantize.o')\n"),
        ("output / 'quantize.o', output / 'dot16.o'],", "output / 'quantize.o', output / 'dot16.o', output / 'w2_np.o'],"),
        ("        image = (output / (PREFIX + '.bin')).read_bytes()\n",
         "        for path in (CFG['w2_elf'], CFG['w2_reference_elf']):\n"
         "            prior_w2 = c.base.f.g.ELF(Path(path).read_bytes())\n"
         "            for name in BINDING['w2_kernels']['functions']:\n"
         "                need(body(elf, name) == body(prior_w2, name), 'entire K768 matches actual GNU and reference ELF: ' + name)\n"
         "        image = (output / (PREFIX + '.bin')).read_bytes()\n"),
        ("'quantize.o', 'dot16.o', 'dump-plan.txt',", "'quantize.o', 'dot16.o', 'w2_np.o', 'dump-plan.txt',"),
        ("            methods=METHODS, active_methods=list(ACTIVE_METHODS), selected_dot16_kernel=BINDING['selected_dot16_kernel'],\n",
         "            methods=METHODS, active_methods=list(ACTIVE_METHODS), selected_dot16_kernel=BINDING['selected_dot16_kernel'],\n"
         "            selected_w2_kernels=BINDING['w2_kernels'],\n"),
    ]
    for before, after in pairs: build = edit(build, before, after, edits)
    insertion = "\n\ndef read(path):\n"
    build = edit(build, insertion, '\nKERNELS.update(' + repr(W2_KERNELS) + ')\n' + insertion, edits)
    begin, end = build.index('    selectors = []\n'), build.index('    begin, end = ')
    old_selector = build[begin:end]
    new_selector = "    selector_check = load('w2_final_selector', HERE / 'w2_selector.py')\n    selectors = selector_check.inspect(elf)\n"
    build = edit(build, old_selector, new_selector, edits)
    inverse = build
    for row in reversed(edits):
        need(inverse.count(row['after']) == 1, 'unique complete build inverse')
        inverse = inverse.replace(row['after'], row['before'], 1)
    need(inverse == original, 'entire previous build recovered')
    (output / 'build.py').write_text(build)
    compile(build, str(output / 'build.py'), 'exec')
    compile((output / 'derive.py').read_text(), str(output / 'derive.py'), 'exec')
    cfg = dict(binding['config'])
    cfg.update(identity=cfg['dot16_hardware_result'],
               w2_source=str(gnu / 'w2_np.S'), w2_elf=str(gnu / 'w2_np.elf'),
               w2_reference_elf=str(ref_elf), w2_reference_result=str(reference / 'result.json'))
    proof = dict(parent_binding_sha256=PARENT_SHA, extension_sha256=sha(HERE / 'w2_extension.py'),
                 build_edits=edits, complete_original_build_recovered=True,
                 original_derive_prefix_preserved=True, original_reference_sha256=sha(parent / 'reference.py'))
    save(output / 'w2-transformations.json', proof)
    updated = dict(binding)
    updated.update(contract=CONTRACT, status='FIRST_FORWARD_W2NP_CONTROLLER_BOUND_NOT_RUNTIME', config=cfg,
        input_files=pins, parent_narrow_binding_sha256=PARENT_SHA, w2_transformations=proof,
        w2_kernels=dict(functions=W2_KERNELS, source_sha256=W2_SOURCE_SHA,
            gnu_elf_sha256=W2_ELF_SHA, reference_elf_sha256=W2_REFERENCE_ELF_SHA,
            reference_result_sha256=REFERENCE_SHA, inherited_scope='complete kernel bytes and local qualification only'),
        reference_runs=0, target_emu_runs=0, performance_qualified=False,
        report_magic_preserved=True, target_entry_scripts_included=False)
    updated['generated_files'] = {str(p.relative_to(output)): sha(p)
        for p in sorted(output.rglob('*')) if p.is_file()}
    save(output / 'binding.json', updated)
    for p, h in pins.items(): need(sha(p) == h, 'input unchanged after source preparation: ' + p)
    return dict(contract=CONTRACT, status=updated['status'], binding_sha256=sha(output / 'binding.json'),
                generated_files=len(updated['generated_files']), input_files=len(pins),
                reference_runs=0, target_emu_runs=0, performance_qualified=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('parent', 'gnu', 'reference', 'output'): parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(*(getattr(args, k).resolve() for k in ('parent', 'gnu', 'reference', 'output'))), indent=2))
