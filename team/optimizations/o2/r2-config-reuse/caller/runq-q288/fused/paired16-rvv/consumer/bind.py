"""Derive a separate paired16 consumer controller from pinned GS32 tooling.

This is a bounded source binding, not a new validator. The historical norm/W2
parent, scalar restoration receipts, support snapshot and numerical/process
validators retain their original identities. Generated controllers are new
inputs and must pass their own GNU build, ELF routing review and reference run.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil

HERE = Path(__file__).resolve().parent
TEMPLATES = {
    'derive.py': '8b920d6742cd40a21f07c5d548901bdc8f9020ce9847cf623e508f4f42ee2ab2',
    'build.py': '70233def12c5e4c5eb5ea07ac9e36709006cd10de5ff8e2100ffaa944dd3f3c2',
    'run.py': '0af5ade6ff73dcf99fea0b3fd305b8e7222ee3179534cd66374df35f68621216',
}
HOST = {
    'paired16.elf': 'fb3c030efa7aa347029a69f6aabe82c912cbbb85294b27cf407a01ea58a314f3',
    'generated/paired16.S': '7b1bf0ba021a69aeab466c8e6bce6a1a88072d40d3f18adfe47555df5dcd3c56',
    'screen/result.json': '6a9e418223ad9b44235f5b4216419288e0d9f6302dfdfed0295e1d26130b5fa0',
    'run.json': 'c3309e8db47cc734a71a231d5b0e7437c765db489f3a0c847d588be8d406a14f',
}
BODY_SHA = 'a06e377e88a230929cc971acf91b0adf3ac27e52fd17ec72956ae7890ed7e73c'
ENTRY_TAG = 0x50313631  # P161, an independent entry tag, never an old method.
CONTRACT = 'r2-s3-forward-consumer-paired16-v1'


def need(condition, detail):
    if not condition:
        raise ValueError(detail)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def edit(text, before, after, count, records):
    """Record exact source positions so reversal never relies on a global guess."""
    starts = [m.start() for m in re.finditer(re.escape(before), text)]
    need(before and len(starts) == count, 'exact edit count: ' + before[:80])
    old = text
    for start in reversed(starts):
        text = text[:start] + after + text[start + len(before):]
    positions = [start + i * (len(after) - len(before)) for i, start in enumerate(starts)]
    restored = text
    for start in reversed(positions):
        need(restored[start:start + len(after)] == after, 'exact inserted source span')
        restored = restored[:start] + before + restored[start + len(after):]
    need(restored == old, 'one edit reverses byte-for-byte')
    records.append(dict(before=before, after=after, count=count,
                        output_positions=positions, input_sha256=sha(old.encode()),
                        output_sha256=sha(text.encode())))
    return text


def transform(name, original):
    text = original.decode('utf-8')
    changes = []
    def change(before, after, count=1):
        nonlocal text
        text = edit(text, before, after, count, changes)

    # Lower-case identifiers belong to this new candidate. Upper-case historical
    # support/scalar status strings below are deliberately NOT renamed.
    change('gs32', 'paired16', {'derive.py': 26, 'build.py': 31, 'run.py': 3}[name])
    change('GS32 ', 'paired16 ', {'derive.py': 1, 'build.py': 4, 'run.py': 2}[name])
    if name == 'derive.py':
        change('0x47533332', '0x50313631', 3)
    elif name == 'build.py':
        change('GS32_CONSUMER_STATIC_PASS_NOT_RUNTIME', 'PAIRED16_CONSUMER_STATIC_PASS_NOT_RUNTIME')
        change('GS32_ACTUAL_ELF_NUMERIC_PASS', 'PAIRED16_ACTUAL_ELF_NUMERIC_PASS')
        change('8316e32939385653c1c4f7e257443529c19dc71df8b5991552a2ab1453069daa', HOST['paired16.elf'])
        change('4320150dc48884201f836bd516c11d7b44dfd9fc287999978828d4bd68d193e2', HOST['generated/paired16.S'])
        change("screen / 'source/paired16.S'", "screen / 'generated/paired16.S'", 3)
        change("screen / 'numeric-01/result.json'", "screen / 'screen/result.json'", 2)
        change('qualified v2', 'frozen paired16 host ELF')
        change('fixed screened v2 ELF and actual assembly', 'fixed paired16 host ELF and actual assembly')
        change('def build(parent, campaign, screen, output, scalar_view=None):',
               'def build(parent, campaign, screen, output, scalar_view=None, support_snapshot=None):')
        change('r, inputs = support(campaign)', 'r, inputs = support(campaign, support_snapshot)')
        change("    parser.add_argument('--scalar-view', type=Path)",
               "    parser.add_argument('--scalar-view', type=Path)\n    parser.add_argument('--support-snapshot', type=Path, required=True)")
        change('args.scalar_view.resolve() if args.scalar_view else None)',
               'args.scalar_view.resolve() if args.scalar_view else None, args.support_snapshot.resolve())')
        change("'consumer_paired16.h', 'CONTRACT.md')", "'consumer_paired16.h', 'CONTRACT.md', 'bind.py', 'binding.json')", 2)
        change('    output.mkdir(parents=True)\n',
               "    binding = read(HERE / 'binding.json')\n"
               "    need(binding['status'] == 'PAIRED16_CONSUMER_CONTROLLER_BOUND_NOT_RUNTIME', 'new controller binding')\n"
               "    for path, value in binding['template_files'].items():\n"
               "        pin(inputs, path, value)\n"
               "    for path, value in binding['host_files'].items():\n"
               "        pin(inputs, path, value)\n"
               "    for name, value in binding['generated_files'].items():\n"
               "        pin(inputs, HERE / name, value)\n"
               '    output.mkdir(parents=True)\n')
        change("    paired16 = body(elf, 'q288_paired16_rvv')\n",
               "    paired16 = body(elf, 'q288_paired16_rvv')\n"
               "    need(len(paired16) == 1096 and derive.sha(paired16) == '" + BODY_SHA + "',\n"
               "         'complete fixed paired16 body including guard and embedded FR fallback')\n")
        change("        assembly = '.option norvc\\n.option norelax\\n.text\\n' + raw[raw.index(begin):]\n",
               "        end = '.size q288_paired16_rvv, .-q288_paired16_rvv\\n'\n"
               "        need(raw.count(end) == 1 and raw.index(end) > raw.index(begin), 'one complete paired16 function end')\n"
               "        fragment = raw[raw.index(begin):raw.index(end) + len(end)]\n"
               "        need(fragment.count('q288_paired16_rvv_fallback_begin:') == 1 and\n"
               "             fragment.count('q288_paired16_rvv_fallback_end:') == 1, 'embedded fallback is included')\n"
               "        assembly = '.option norvc\\n.option norelax\\n.text\\n' + fragment\n")
    else:
        for before in ('GS32_CONSUMER_REFERENCE_CAMPAIGN_PASS',
                       'EXPECTED_GS32_CONSUMER_STATE_REJECTION',
                       'GS32_CONSUMER_COMPLETE_REFERENCE_PASS',
                       'GS32_CONSUMER_ROUTING_REVIEW_PASS'):
            change(before, before.replace('GS32', 'PAIRED16'))
        change("'consumer_paired16.h', 'CONTRACT.md')", "'consumer_paired16.h', 'CONTRACT.md', 'bind.py', 'binding.json')")

    # Every stage is reversed using its own recorded positions and SHA; this is
    # a proof about derived source bytes, not a numerical qualification claim.
    reversed_text = text
    for row in reversed(changes):
        need(sha(reversed_text.encode()) == row['output_sha256'], 'reverse intermediate identity')
        for start in reversed(row['output_positions']):
            need(reversed_text[start:start + len(row['after'])] == row['after'], 'reverse exact span')
            reversed_text = reversed_text[:start] + row['before'] + reversed_text[start + len(row['after']):]
        need(sha(reversed_text.encode()) == row['input_sha256'], 'reverse previous identity')
    need(reversed_text.encode() == original, 'entire controller exactly reverses to pinned template')
    compile(text, name, 'exec')
    if name == 'build.py':
        for receipt in ('GS32_REFERENCE_SUPPORT_SNAPSHOT_COMPLETE', 'GS32_ORIGINAL_SCALAR_SUBSET_RESTORED'):
            need(text.count(receipt) == original.decode().count(receipt) == 1, 'historical receipt identity preserved')
    return text, changes


def bind(template, host, output):
    need(not output.exists(), 'fresh controller output')
    need(not any(output.is_relative_to(p) for p in (template, host, HERE)), 'controller outside fixed inputs')
    templates, host_files, generated, transformations = {}, {}, {}, {}
    for name, expected in TEMPLATES.items():
        path = template / name
        raw = path.read_bytes()
        need(sha(raw) == expected, 'pinned GS32 tooling: ' + name)
        templates[str(path)] = expected
        generated[name], transformations[name] = transform(name, raw)
    for name, expected in HOST.items():
        path = host / name
        need(sha(path.read_bytes()) == expected, 'actual frozen paired16 host artifact: ' + name)
        host_files[str(path)] = expected
    screen = json.loads((host / 'screen/result.json').read_text())
    need(screen['status'] == 'PAIRED16_ACTUAL_ELF_NUMERIC_PASS' and screen['elf_sha256'] == HOST['paired16.elf'],
         'original paired16 host screen, not a renamed GS32 report')
    need(len(screen['numeric']['cases']) == 19 and len(screen['controls']) == 6, 'full paired16 screen inventory')
    output.mkdir(parents=True)
    for name, text in generated.items():
        (output / name).write_text(text)
    for name in ('bind.py', 'consumer_paired16.h', 'CONTRACT.md'):
        shutil.copyfile(HERE / name, output / name)
    files = {p.name: sha(p.read_bytes()) for p in output.iterdir() if p.is_file()}
    proof = dict(contract=CONTRACT, status='PAIRED16_CONSUMER_CONTROLLER_BOUND_NOT_RUNTIME',
        entry='r2_w2_paired16_forward', entry_tag=ENTRY_TAG,
        template_files=templates, host_files=host_files, generated_files=files,
        source_transformations=transformations, all_source_edits_exactly_reversed=True,
        kernel=dict(symbol='q288_paired16_rvv', bytes=1096, sha256=BODY_SHA),
        reference_runs=0, target_emu_runs=0, performance_qualified=False,
        stable_default_changed=False, old_paired16_performance_hold_preserved=True)
    (output / 'binding.json').write_text(json.dumps(proof, indent=2) + '\n')
    return proof


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('template', 'host', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = bind(*(getattr(args, name).resolve() for name in ('template', 'host', 'output')))
    print(json.dumps(dict(status=result['status'], output=str(args.output), files=len(result['generated_files']),
                          performance_qualified=False)), flush=True)
