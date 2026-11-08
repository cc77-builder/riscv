#!/usr/bin/env python3
"""Derive one P3 screen from the completed Booth2 controller, with fresh R SAT."""
from pathlib import Path
import ast
import difflib
import hashlib
import json

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'prefix-booth-candidate-01/controller/booth9.py'
BASE_SHA='6681fce5cc739206c5922e025d76ae0a75334d57502b089902b5a7a72f05ea60'


def main():
    raw=BASE.read_bytes();assert hashlib.sha256(raw).hexdigest()==BASE_SHA
    text=raw.decode();edits=[]
    def edit(before,after):
        nonlocal text
        assert before!=after and text.count(before)==1,(before[:100],text.count(before))
        assert text.count(after)==0,after[:100]
        text=text.replace(before,after,1);edits.append(dict(before=before,after=after))
    def lines_replace(before,after):
        for line in list(dict.fromkeys(x for x in text.splitlines(True) if before in x)):
            edit(line,line.replace(before,after))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    proof=json.loads((ROOT/'source/source-derivation.json').read_bytes())
    edit('"""Compile one Booth9 candidate; prove actual biased CSA arithmetic, then run FU/cost."""',
         '"""Compile one three-row Booth candidate; prove new P and R arithmetic, then FU/cost."""')
    edit("CONTRACT = 'dot16-prefix-booth9-local-v1'", "CONTRACT = 'dot16-prefix-booth3-local-v1'")
    edit("CONTROLLER_BASELINE_SHA = '794544ddfb3455b05deaffe8588d3c9715d02446ac04c50fe2710c6caaaafc0e'",
         "CONTROLLER_BASELINE_SHA = '"+BASE_SHA+"'")
    for constant,old,new in (
        ('SOURCE_DERIVATION_SHA','72b19ecbc899c0175c86a31e1032607b65897999c17117e2de21f21fac7c7eae',sha(ROOT/'source/source-derivation.json')),
        ('VERIFY_SHA','b3044e637a5f312b71497de1eaa44503e27894cb7fd313ee389208a8fc351dc5',sha(ROOT/'controller/verify_booth.py')),
        ('SOURCE_SHA','f0a8bbe58440c6113aa56f848387c6b4e4a487d71ec2832a1e43fca55d3a8245',proof['candidate_datapath_sha256']),
        ('WRAPPER_SHA','0fcc5df10355ee1e6382678ba40bc9d7ddf830b560dcc469c46e6a6888441556',proof['candidate_wrapper_sha256'])):
        edit(f"{constant} = '{old}'",f"{constant} = '{new}'")
    edit("len(pairs)==4 and len(dict(pairs))==4,\n             'closed four CSA instance ports'",
         "len(pairs)==5 and len(dict(pairs))==5,\n             'closed five CSA instance ports'")
    edit("                     'row0':f'_{name}_row0','row1':f'_{name}_row1'},'exact input halves and output wires')",
         "                     'row0':f'_{name}_row0','row1':f'_{name}_row1','row2':f'_{name}_row2'},'exact input halves and all three output wires')")
    edit("    pnames=[f'pRows_{half}_{row}' for half in range(2 if feature else 1) for row in range(2)]",
         "    pnames=[f'pRows_{half}_{row}' for half in range(2 if feature else 1) for row in range(3)]")
    edit('        for row in range(2):','        for row in range(3):')
    edit("         'entire completed Pgroup controller recovered')", "         'entire completed Booth2 controller recovered')")
    edit("         proof['exact_inverse'] is True and len(proof['edits'])==5,\n         'one heap replacement and four explicit wrapper data-representation edits')\n    need(Counter(e['file'] for e in proof['edits'])=={'VDotDatapath.scala':1,'VDotElastic.scala':4},",
         "         proof['exact_inverse'] is True and len(proof['edits'])==16,\n         'complete prefix-to-Booth2-to-Booth3 inverse, sixteen exact hunks')\n    need(Counter(e['file'] for e in proof['edits'])=={'VDotDatapath.scala':7,'VDotElastic.scala':9},")
    edit("    need(proof['external_interface_unchanged'] and proof['clock_reset_slot_protocol_unchanged'] and\n         proof['old_prefix_finish_source_retained'],\n         'P representation changes only; clock/reset/control and R prefix source retained')",
         "    need(proof['external_interface_unchanged'] and proof['clock_reset_slot_protocol_unchanged'] and\n         proof['old_prefix_finish_source_retained'] is False and proof['old_prefix_network_suffix_retained'] and\n         proof['fresh_three_six_row_unconstrained_proofs_required'] and proof['p_rows_per_half']==3,\n         'one P/R boundary change, preserved slot control, fresh R arithmetic proof required')")
    edit('        result_widths={0:19,1:20},p_row_bits={0:19,1:20},p_rows_per_half=2,',
         '        result_widths={0:19,1:20},p_row_bits={0:19,1:20},p_rows_per_half=3,')
    edit("        representation_equivalence_basis='New complete proof of actual Booth recoder/biased CSA bytes; exact-byte reuse of unconstrained prefix SAT proofs; full source inverse, new emitted wrapper binding and new FU tests. No whole-FU sequential or RTL-to-mapped SAT claim.',",
         "        representation_equivalence_basis='New complete proof of actual three-row Booth heap; fresh actual unconstrained three/six-row R SAT; full source inverse, emitted wrapper binding and new FU tests. No whole-FU sequential or RTL-to-mapped SAT claim.',")
    edit("            need((out/f'cost-feature{feature}/rtl'/name).read_bytes()==\n                 (out/f'fu-feature{feature}/rtl'/name).read_bytes()==\n                 (pbase/f'cost-feature{feature}/rtl'/name).read_bytes(),\n                 'actual new cost/FU R prefix bytes exactly match the previously proved modules')",
         "            need((out/f'cost-feature{feature}/rtl'/name).read_bytes()==\n                 (out/f'fu-feature{feature}/rtl'/name).read_bytes(),\n                 'actual new cost/FU R bytes are identical and require fresh SAT proofs')")
    edit("structure['status']=='BOOTH_CSA_STRUCTURAL_EQUIVALENCE_PASS'",
         "structure['status']=='BOOTH3_CSA_STRUCTURAL_EQUIVALENCE_PASS'")
    edit("structure['full_adders']==288 and structure['half_adders']==20", "structure['full_adders']==272 and structure['half_adders']==19")
    edit("structure['layers']==list(range(8))", "structure['layers']==list(range(7))")
    start=text.index("        result['prefix_miters']=json.loads(json.dumps(pb['prefix_miters']))")
    end=text.index("        result['arithmetic_proof_completed']=True",start)
    sat_source=(ROOT.parent/'prefix-pgroup-candidate-01/base/controller/prefix.py').read_text()
    start_sat=sat_source.index('        for feature,width,row_count in ((0,19,2),(1,20,4)):')
    end_sat=sat_source.index("        result['arithmetic_proof_completed']=True",start_sat)
    fresh=sat_source[start_sat:end_sat].replace('((0,19,2),(1,20,4))','((0,19,3),(1,20,6))')
    edit(text[start:end],"        result['prefix_miters_reused']=False\n"+fresh)
    lines_replace('BOOTH_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE','BOOTH3_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE')
    lines_replace("'booth9.py'","'booth3.py'")
    ast.parse(text)
    restored=text
    for e in reversed(edits):
        assert restored.count(e['after'])==1
        restored=restored.replace(e['after'],e['before'],1)
    assert restored.encode()==raw
    out=ROOT/'controller';target=out/'booth3.py'
    assert not target.exists()
    target.write_text(text)
    (out/'controller-derivation.json').write_text(json.dumps(dict(baseline_sha256=BASE_SHA,
        candidate_sha256=sha(target),exact_inverse=True,edits=edits,
        new_unconstrained_actual_prefix_SAT_required=True,old_prefix_proofs_not_reused=True,
        absolute_total_success_deadline_preserved=True),indent=2)+'\n')
    (out/'controller.diff').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),
        text.splitlines(True),fromfile='booth2/booth9.py',tofile='booth3/booth3.py')))
    print(json.dumps(dict(bytes=target.stat().st_size,sha256=sha(target),edits=len(edits),
        derivation_sha256=sha(out/'controller-derivation.json')),indent=2))


if __name__=='__main__':main()
