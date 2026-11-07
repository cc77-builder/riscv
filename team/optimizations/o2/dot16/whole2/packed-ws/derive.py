#!/usr/bin/env python3
"""Derive one explicit packed-Ws layout for the four frozen N/P kernels.

Only source preparation and inverse identity checks; no build or target run.
"""
import argparse
import hashlib
import json
from pathlib import Path

CONTRACT = 'r3-dot16-np-packed-ws-v1'
PINS = {
    'dot16.S': '40d263b68ead735b84cb626086674463fbb81154ed9898eb8a340f95f102d671',
    'paired16.S': '452ecab3ae3122dd8ea3d5ae05140197a10bb14a9a5ab76437f7591b00b29caf',
    'w2_np.S': 'fbe3a93f642ec3468da92ae776e1b547c29c527d4dffc30456191b437d1272c5',
}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def need(ok, message):
    if not ok:
        raise ValueError(message)

def derive(raw, names, tails):
    text = raw.decode('utf-8')
    edits = []
    def edit(before, after, count):
        nonlocal text
        need(text.count(before) == count, 'exact source anchor: '+before)
        text = text.replace(before, after)
        edits.append(dict(before=before, after=after, count=count))
    for name in names:
        # Prefix replacement also renames P guard/fast/fallback labels.
        edit(name, name+'_packed_ws', text.count(name))
    count = sum(n for _, n in tails)
    edit('  vlse32.v v12, (a4), t3\n', '  vle32.v v12, (a4)\n', count)
    edit('  addi a4, a4, 4\n', '  addi a4, a4, 32\n', count)
    for stride, occurrences in tails:
        edit(f'  addi a4, a4, {stride}\n', '  addi a4, a4, 0\n', occurrences)
    inverse = text
    for e in reversed(edits):
        need(inverse.count(e['after']) == e['count'], 'unique inverse anchor')
        inverse = inverse.replace(e['after'], e['before'])
    need(inverse.encode() == raw, 'byte-exact reconstruction of full parent source')
    return text.encode(), dict(parent_sha256=sha(raw), derived_sha256=sha(text.encode()),
                               edits=edits, reconstructed_parent_byte_exact=True)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parent', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    need(not a.output.exists(), 'fresh candidate output')
    raws = {n: (a.parent/n).read_bytes() for n in PINS}
    need(all(sha(raws[n]) == h for n,h in PINS.items()), 'frozen actual source identities')
    plans = [
        ('dot16.S', ['q288_dot16_whole8_narrow'], [(252,1)]),
        ('paired16.S', ['q288_paired16_rvv'], [(252,2)]),
        ('w2_np.S', ['q768_dot16_whole8_narrow','q768_paired16_rvv'], [(672,3)]),
    ]
    records = {}; blocks = []
    for filename,names,tails in plans:
        out, records[filename] = derive(raws[filename], names, tails)
        blocks.append(out)
    assembled_source = b'\n'.join(blocks)
    a.output.mkdir(parents=True)
    (a.output/'packed.S').write_bytes(assembled_source)
    result = dict(contract=CONTRACT, status='SOURCE_DERIVED_NOT_COMPILED', parents=PINS,
                  sources=records, packed_source_sha256=sha(assembled_source),
                  expected_changed_words={'q288_dot16_whole8_narrow_packed_ws':3,
                    'q288_paired16_rvv_packed_ws':6,
                    'q768_dot16_whole8_narrow_packed_ws':3,
                    'q768_paired16_rvv_packed_ws':6},
                  target_runs=0, performance_qualified=False,
                  source_preparer_sha256=sha(Path(__file__).read_bytes()))
    (a.output/'source-derivation.json').write_text(json.dumps(result,indent=2)+'\n')
    need(all(sha((a.parent/n).read_bytes()) == h for n,h in PINS.items()), 'parents unchanged')
    print(json.dumps(dict(status=result['status'], packed_source_sha256=sha(assembled_source))))

if __name__ == '__main__':
    main()
