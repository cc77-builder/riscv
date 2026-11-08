#!/usr/bin/env python3
"""Derive the single Booth9 local run from the completed Pgroup controller."""
from pathlib import Path
import ast
import difflib
import hashlib
import json

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'prefix-pgroup-candidate-01/controller/pgroup.py'
BASE_SHA='794544ddfb3455b05deaffe8588d3c9715d02446ac04c50fe2710c6caaaafc0e'

SOURCE_PROOF = '''    proof=json.loads((source/'source-derivation.json').read_bytes())
    need(proof['contract']==CONTRACT and proof['baseline_datapath_sha256']==PREFIX_DATAPATH_SHA and
         proof['candidate_datapath_sha256']==SOURCE_SHA and proof['baseline_wrapper_sha256']==PREFIX_WRAPPER_SHA and
         proof['candidate_wrapper_sha256']==WRAPPER_SHA and proof['wrapper_byte_identical'] is False and
         proof['exact_inverse'] is True and len(proof['edits'])==5,
         'one heap replacement and four explicit wrapper data-representation edits')
    need(Counter(e['file'] for e in proof['edits'])=={'VDotDatapath.scala':1,'VDotElastic.scala':4},
         'closed per-source edit counts')
    for name,path in (('VDotDatapath.scala',candidate),('VDotElastic.scala',wrapper)):
        restored=path.read_bytes().decode('utf-8')
        for edit in reversed([e for e in proof['edits'] if e['file']==name]):
            need(restored.count(edit['after'])==1,'unique source inverse '+name)
            restored=restored.replace(edit['after'],edit['before'],1)
        need(restored.encode()==(pbase/'source-snapshot'/name).read_bytes(),
             'full frozen prefix source recovered '+name)
    need(proof['external_interface_unchanged'] and proof['clock_reset_slot_protocol_unchanged'] and
         proof['old_prefix_finish_source_retained'],
         'P representation changes only; clock/reset/control and R prefix source retained')
'''

STRUCTURE_PROOF = '''        # Prove the actual emitted recoder, biased heap, compressor graph and rows.
        # This verifier accepts no unparsed SV statements or hidden arithmetic.
        report=out/'arithmetic-structure.json'
        command('actual-booth-structure',[sys.executable,'-B',snap/'verify_booth.py',
            '--rtl',first/'VDotCarrySaveRows.sv','--output',report],60)
        structure=json.loads(report.read_bytes())
        need(structure['status']=='BOOTH_CSA_STRUCTURAL_EQUIVALENCE_PASS' and
             structure['all_inputs_equivalent'] is True and structure['parsed_entire_module'] is True and
             structure['verifier']['sha256']==VERIFY_SHA and
             structure['rtl_sha256']==sha(first/'VDotCarrySaveRows.sv') and
             structure['full_adders']==288 and structure['half_adders']==20 and
             structure['actual_recode_cases']==7168 and structure['signed_byte_decomposition_cases']==256 and
             structure['layers']==list(range(8)) and structure['total_correction']==350208 and
             structure['disabled_high_half_sum']==1<<19,
             'new complete actual Booth proof with exact recode, bias and FA/HA counts')
        result['arithmetic_structure_proof']=structure
        result['arithmetic_structure_proof_reused']=False
        result['biased_unsigned_row_encoding_verified']=True
        result['direct_signed_row_encoding_verified']=False
        generated_pins[str(report)]=sha(report)
'''


def main():
    raw=BASE.read_bytes();assert hashlib.sha256(raw).hexdigest()==BASE_SHA
    original=raw.decode();text=original;edits=[]
    def replace(before,after):
        nonlocal text
        assert before!=after and text.count(before)==1,(before[:160],text.count(before))
        assert text.count(after)==0,(after[:80],'already present')
        text=text.replace(before,after,1);edits.append(dict(before=before,after=after))
    def all_text(before,after):
        nonlocal text
        assert before!=after and before in text
        # One whole-buffer edit is not used: retain independently reviewable hunks.
        lines=text.splitlines(True)
        for line in list(dict.fromkeys(x for x in lines if before in x)):
            assert text.count(line)==1,line
            replace(line,line.replace(before,after))

    deriv=json.loads((ROOT/'source/source-derivation.json').read_bytes())
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    replace('"""Compile one P-group candidate; prove actual CSA arithmetic, then run full FU/cost."""',
            '"""Compile one Booth9 candidate; prove actual biased CSA arithmetic, then run FU/cost."""')
    replace("CONTRACT = 'dot16-prefix-pgroup-local-v1'", "CONTRACT = 'dot16-prefix-booth9-local-v1'")
    replace("CONTROLLER_BASELINE_SHA = '8f33f550c9b7e74e8190cb5f5a2cfdcc693a783d86ae905ec3e60c7ad10d148c'",
            "CONTROLLER_BASELINE_SHA = '"+BASE_SHA+"'")
    replace("SOURCE_DERIVATION_SHA = 'b757bddd341c5dae1188b6a45a1a88ba32ed7b856864e4fbc6e503283b13a630'",
            "SOURCE_DERIVATION_SHA = '"+sha(ROOT/'source/source-derivation.json')+"'")
    replace("VERIFY_SHA = 'e6924e406792fe9e2b82f27be5a591b37466fb7b3ee23ec93935698934e397de'",
            "VERIFY_SHA = '"+sha(ROOT/'controller/verify_booth.py')+"'")
    replace("WRAPPER_SHA = '912c1a038ef8e9a1ac56cfa349161ae1c582d763acfce5352b08ebde2a227f92'",
            "WRAPPER_SHA = '"+deriv['candidate_wrapper_sha256']+"'\nPREFIX_WRAPPER_SHA = '912c1a038ef8e9a1ac56cfa349161ae1c582d763acfce5352b08ebde2a227f92'")
    replace("SOURCE_SHA = '1f9a4c807b30b8aa769e65595ce6b54619b190a5f2b5af1d531413de9970b90c'",
            "SOURCE_SHA = '"+deriv['candidate_datapath_sha256']+"'")

    replace("    need(declarations==[('18',name) for name in pnames],'actual complete 19-bit P rows')",
            "    need(declarations==[(str(19 if feature else 18),name) for name in pnames],\n         'actual complete P rows: feature0 low19, feature1 full20')")
    replace("            expected=f'isDot16?_highProducts_row{row}:19\\'h0' if half else f'_products_row{row}'\n            need(expressions==[expected],'exact P capture and dot8 zero encoding')",
            "            if half:\n                constant=\"20'h80000\" if row==0 else \"20'h0\"\n                expected=f'isDot16?_highProducts_row{row}:{constant}'\n            else:\n                expected=f'_products_row{row}'+('' if feature else '[18:0]')\n            need(expressions==[expected],'exact P capture and dot8 biased-zero encoding')")
    replace("        expected_ports[f'rows_{i}']='{'+name+'[18],'+name+'}' if feature else name\n    need(ports==expected_ports,'exact saved low0/low1/high0/high1 rows with required sign extension')",
            "        expected_ports[f'rows_{i}']=name\n    need(ports==expected_ports,'exact saved unsigned rows, no signed extension or post-P correction')")
    replace("        p_capture_and_dot8_zero_verified=True,non_data_sequential_assignments_unchanged=True,",
            "        p_capture_and_dot8_biased_zero_verified=True,p_row_bits=20 if feature else 19,\n        non_data_sequential_assignments_unchanged=True,")

    replace("         'entire completed prefix controller recovered')","         'entire completed Pgroup controller recovered')")
    replace("         pb['candidate_source_sha256']==PREFIX_DATAPATH_SHA and pb['candidate_wrapper_sha256']==WRAPPER_SHA,",
            "         pb['candidate_source_sha256']==PREFIX_DATAPATH_SHA and pb['candidate_wrapper_sha256']==PREFIX_WRAPPER_SHA,")
    replace("    pin(pbase/'source-snapshot/VDotElastic.scala',WRAPPER_SHA)",
            "    pin(pbase/'source-snapshot/VDotElastic.scala',PREFIX_WRAPPER_SHA)")
    begin=text.index("    proof=json.loads((source/'source-derivation.json').read_bytes())")
    end=text.index("    old_gen=json.loads((gen/'result.json').read_bytes())",begin)
    replace(text[begin:end],SOURCE_PROOF)
    replace("        result_widths={0:19,1:20},p_row_bits=19,p_rows_per_half=2,",
            "        result_widths={0:19,1:20},p_row_bits={0:19,1:20},p_rows_per_half=2,")
    replace("        representation_equivalence_basis='New strict complete proof of actual P CSA bytes; exact-byte reuse of two unconstrained prefix SAT proofs; source inverse, emitted wrapper binding and actual new FU checks. No whole-FU sequential SAT claim.',",
            "        representation_equivalence_basis='New complete proof of actual Booth recoder/biased CSA bytes; exact-byte reuse of unconstrained prefix SAT proofs; full source inverse, new emitted wrapper binding and new FU tests. No whole-FU sequential or RTL-to-mapped SAT claim.',")
    replace("        no_state_clock_latency_change=True)",
            "        no_clock_reset_latency_or_slot_protocol_change=True,internal_P_row_width_changed=True)")
    replace("    def check():\n        if pending[0] is not None:raise InterruptedError('received signal '+str(pending[0]))",
            "    def check():\n        if pending[0] is not None:raise InterruptedError('received signal '+str(pending[0]))\n        if time.monotonic()>=deadline:raise TimeoutError('total success budget exhausted')")
    replace("        check();remaining=deadline-time.monotonic();need(remaining>0,'total deadline before '+label)\n        rec=dict(label=label,argv=list(map(str,argv)),started=util.stamp(),budget_seconds=min(limit,remaining),",
            "        check();now=time.monotonic();until=min(deadline,now+limit)\n        need(until>now,'total deadline before '+label)\n        rec=dict(label=label,argv=list(map(str,argv)),started=util.stamp(),budget_seconds=until-now,")
    replace("                rec['pid']=proc.pid;save(out/'result.json',result)\n                until=time.monotonic()+rec['budget_seconds']",
            "                rec['pid']=proc.pid;save(out/'result.json',result)\n                # Absolute command deadline was fixed before Popen, including launch/log overhead.")
    replace("    finally:\n        result['finished']=util.stamp();save(out/'result.json',result)\n    print(json.dumps({k:v for k,v in result.items() if k not in ('commands','generated','cost_results')},indent=2))",
            "    finally:\n        result['finished']=util.stamp();save(out/'result.json',result)\n        if result.get('status')=='PGROUP_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE':\n            try:check()\n            except BaseException as exc:\n                result.update(status='FAILED',error=repr(exc),finished=util.stamp())\n                save(out/'result.json',result)\n                raise\n    print(json.dumps({k:v for k,v in result.items() if k not in ('commands','generated','cost_results')},indent=2))")
    replace("                need((rtl/'VDotElastic.sv').read_bytes()==(pbase/f'{kind}-feature{feature}/rtl/VDotElastic.sv').read_bytes(),\n                     'entire emitted prefix wrapper remains byte-identical')\n",
            '                # The changed P representation is bound below; whole-wrapper byte reuse is not claimed.\n')
    begin=text.index('        # A new heap grouping needs a new proof over its real generated bytes.')
    end=text.index("        result['historical_multiplication_miter']=dict(cb['independent_miter'])",begin)
    replace(text[begin:end],STRUCTURE_PROOF)
    all_text('PGROUP_CONTRACT.md','BOOTH_CONTRACT.md')
    all_text("'pgroup.py'","'booth9.py'")
    all_text('verify_csa.py','verify_booth.py')
    all_text('PGROUP_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE','BOOTH_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE')
    ast.parse(text)
    restored=text
    for e in reversed(edits):
        assert restored.count(e['after'])==1,('inverse',e['after'][:100])
        restored=restored.replace(e['after'],e['before'],1)
    assert restored==original
    out=ROOT/'controller'
    (out/'booth9.py').write_bytes(text.encode())
    proof=dict(contract=deriv['contract'],baseline_sha256=BASE_SHA,candidate_sha256=sha(out/'booth9.py'),
        exact_inverse=True,edits=edits,official_code_changed=False,
        budget_seconds=1200,cpu=2,source_candidate=deriv['candidate_datapath_sha256'],
        new_fu_and_cost_run=True,new_parent_or_core_run=False)
    (out/'controller-derivation.json').write_text(json.dumps(proof,indent=2)+'\n')
    (out/'controller.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),text.splitlines(True),
        fromfile='completed-pgroup/pgroup.py',tofile='booth9/booth9.py')))
    print(json.dumps({k:v for k,v in proof.items() if k!='edits'},indent=2))


if __name__=='__main__':main()
