#!/usr/bin/env python3
"""Derive a whole-eight load candidate from the frozen whole2 assembly.

This prepares source only. GNU, reference and XiangShan qualification are
separate steps; generating this file never launches an assembler or guest.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

CONTRACT = 'r3-dot16-whole8-source-v1'
BASE_SHA256 = 'df2983a21ab85d982b51e7faa0710d536d2bd4afe5bc9c2b91577dd3450972c8'
BASE_FUNCTION_SOURCE_SHA256 = '7937fb177d0325622c16ddc4caa81a22c0c5134e64d8ba31cd70e92ec6bd1f18'
BASE_FUNCTION_MACHINE_SHA256 = 'b2b5b7fa44ecf9646a7c07fdaf971df8fad6430aec58161ffc3e2c3332d934a6'
OLD = 'q288_dot16_whole2'
NEW = 'q288_dot16_whole8'
PREFIX = '.option norvc\n.option norelax\n.text\n.balign 64\n'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def instructions(text):
    return [line.strip() for line in text.splitlines()
            if line.startswith('  ') and line.strip()]


def derive(raw):
    need(sha(raw) == BASE_SHA256, 'exact complete frozen whole2 assembly')
    text = raw.decode('utf-8')
    pattern = r'(?ms)^\.global ' + OLD + r'\n.*?^\.size ' + OLD + r', \.-' + OLD + r'\n'
    matches = re.findall(pattern, text)
    need(len(matches) == 1 and text.endswith(matches[0]), 'unique complete final whole2 function')
    original = matches[0]
    need(sha((PREFIX + original).encode()) == BASE_FUNCTION_SOURCE_SHA256,
         'same extracted whole2 function used by the current forward image')
    changed, edits = original, []
    for first in (0, 4):
        before = ''.join(
            f'  addi t6, a2, {(first + slot) * 32}\n'
            f'  vl2re8.v v{16 + 2 * slot}, (t6)\n'
            for slot in range(4))
        after = ('  vl8re8.v v16, (a2)\n' if first == 0 else
                 '  addi t6, a2, 128\n  vl8re8.v v16, (t6)\n')
        need(changed.count(before) == 1 and after not in changed,
             'unique unchanged four-row load block')
        changed = changed.replace(before, after, 1)
        edits.append((before, after))
    for before, after, count in ((OLD, NEW, 5),
                                  ('.Ltile_dot16_whole2', '.Ltile_dot16_whole8', 2),
                                  ('.Lgroup_dot16_whole2', '.Lgroup_dot16_whole8', 2)):
        need(changed.count(before) == count and after not in changed,
             'exact symbol/label rename: ' + before)
        changed = changed.replace(before, after)
        edits.append((before, after))
    inverse = changed
    for before, after in reversed(edits):
        inverse = inverse.replace(after, before)
    need(inverse == original, 'all edits reconstruct the original function byte for byte')
    old_words, new_words = instructions(original), instructions(changed)
    need(len(old_words) == 103 and len(new_words) == 90, 'source instruction budgets')
    start = new_words.index('vsetivli zero, 16, e8, m1, ta, mu')
    end = new_words.index('vmv.v.v v10, v0')
    core = new_words[start:end]
    need(start == 15 and len(core) == 30, 'unchanged prefix and thirty-instruction core')
    counts = Counter(line.split()[0] for line in core)
    need(counts == Counter(vsetivli=2, addi=1,
                          **{'vl2re8.v': 1, 'vl8re8.v': 2, '.word': 16, 'vadd.vv': 8}),
         'only the intended integer-core operations')
    # Whole-register mapping: VLEN=128, EEW=8, vstart=0. These are source
    # address/register proofs, not evidence that a target executed either load.
    mapping = []
    for first in (0, 4):
        old_map = {(16 + 2 * slot + half, lane): (first + slot) * 32 + half * 16 + lane
                   for slot in range(4) for half in range(2) for lane in range(16)}
        new_map = {(16 + reg, lane): first * 32 + reg * 16 + lane
                   for reg in range(8) for lane in range(16)}
        need(old_map == new_map, 'exact byte-to-register mapping per load batch')
        mapping.append(dict(first_row=first, byte_range=[first * 32, first * 32 + 128],
                            destination_register_range=[16, 24], bytes=128))
    combined = raw + ('\n' + PREFIX + changed).encode()
    need(combined[:len(raw)] == raw, 'entire retained source is an unchanged prefix')
    report = dict(schema=1, contract=CONTRACT, status='SOURCE_DERIVED_UNBUILT',
                  base_assembly_sha256=sha(raw),
                  base_function_source_sha256=BASE_FUNCTION_SOURCE_SHA256,
                  base_function_machine_sha256_reference=BASE_FUNCTION_MACHINE_SHA256,
                  candidate=NEW, candidate_source_sha256=sha((PREFIX + changed).encode()),
                  combined_source_sha256=sha(combined),
                  original_reconstructed_byte_exact=True, retained_source_byte_equal=True,
                  edits=[dict(before=a, after=b) for a, b in edits],
                  weight_mapping=mapping, x_byte_range=[0, 32],
                  expected=dict(core_instructions=30, function_instructions=90,
                                function_machine_bytes=360, groups_per_function=324,
                                dynamic_function_instructions=16878,
                                dynamic_instruction_reduction=4212,
                                dynamic_dot16=5184, dynamic_whole2_loads=324,
                                dynamic_whole8_loads=648),
                  gnu_built=False, numeric_model_qualified=False,
                  reference_qualified=False, target_runtime_qualified=False,
                  performance_qualified=False, new_emu_runs=0)
    return combined, (PREFIX + changed).encode(), report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--whole2-assembly', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    source, output = a.whole2_assembly.resolve(), a.output.resolve()
    need(a.output.is_absolute() and not output.exists(), 'new absolute output')
    need(not source.is_relative_to(output), 'output must not contain the input')
    raw = source.read_bytes()
    combined, candidate, report = derive(raw)
    need(source.read_bytes() == raw, 'input stable during derivation')
    output.mkdir(parents=True)
    (output / 'whole2-input.S').write_bytes(raw)
    (output / 'whole8.S').write_bytes(combined)
    (output / 'whole8-only.S').write_bytes(candidate)
    report.update(source=str(source), output=str(output),
                  generated_at=datetime.now(timezone.utc).isoformat(),
                  generator_sha256=sha(Path(__file__).read_bytes()))
    (output / 'derivation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('contract', 'status', 'candidate',
                                           'combined_source_sha256')}, indent=2))


if __name__ == '__main__':
    main()
