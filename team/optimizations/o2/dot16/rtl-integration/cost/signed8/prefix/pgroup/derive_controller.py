#!/usr/bin/env python3
"""Derive a bounded P-group experiment from the exact completed prefix driver."""
from pathlib import Path
import ast
import difflib
import hashlib
import json

ROOT = Path(__file__).resolve().parent
BASE_SHA = '8f33f550c9b7e74e8190cb5f5a2cfdcc693a783d86ae905ec3e60c7ad10d148c'
PREFIX_RESULT_SHA = 'a0c4dd60fddc001f368b71ec283327f2d7fe0874080ac35304e3debe783116d0'
PREFIX_SOURCE_SHA = '1d02d8a34772e7d9b9947f997f32465f3e946f4b24cacc66159eef7ee10ab3bb'
CHECKER_SHA = 'e6924e406792fe9e2b82f27be5a591b37466fb7b3ee23ec93935698934e397de'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def derive(original, source_sha, derivation_sha):
    text = original
    edits = []
    def replace(before, after):
        nonlocal text
        assert before and text.count(before) == 1, ('unique edit', before[:120])
        text = text.replace(before, after, 1)
        edits.append(dict(before=before, after=after))

    replace('"""Compile one post-P prefix candidate; prove the actual finish modules, then run full FU/cost."""',
            '"""Compile one P-group candidate; prove actual CSA arithmetic, then run full FU/cost."""')
    replace("CONTRACT = 'dot16-csa-prefix-local-v1'\nCONTROLLER_BASELINE_SHA = '07d93e73072304a64b7bc415820b2856a27b2d74a01e649a2e141f78e8adf0f7'",
            "CONTRACT = 'dot16-prefix-pgroup-local-v1'\nCONTROLLER_BASELINE_SHA = '"+BASE_SHA+"'\nPREFIX_BASELINE_SHA = '"+PREFIX_RESULT_SHA+"'\nPREFIX_BASELINE_BYTES = 205865\nPREFIX_DATAPATH_SHA = '"+PREFIX_SOURCE_SHA+"'")
    replace("SOURCE_DERIVATION_SHA = '2c1fd758ba8ebb22537ee1ab776c3e9418331b16d5aa2064ff84163674d61caa'",
            "SOURCE_DERIVATION_SHA = '"+derivation_sha+"'")
    replace("SOURCE_SHA = '"+PREFIX_SOURCE_SHA+"'\nORIGINAL_SOURCE_SHA",
            "SOURCE_SHA = '"+source_sha+"'\nORIGINAL_SOURCE_SHA")
    replace("    cbase=a.csa_local.resolve()\n    need(a.cpu==1", "    cbase=a.csa_local.resolve()\n    pbase=a.prefix_local.resolve()\n    need(a.cpu==1")
    replace("    for d in (repo,cost,fu,here,source,baseline,rbase,cbase):", "    for d in (repo,cost,fu,here,source,baseline,rbase,cbase,pbase):")
    replace("    need(a.cpu==1 and a.budget_seconds==1200 and not out.exists(), 'CPU1, exact 1200s work budget, fresh output')", "    need(a.cpu==2 and a.budget_seconds==1200 and not out.exists(), 'CPU2, exact 1200s work budget, fresh output')")
    replace("    pin(Path(__file__));pin(here/'PREFIX_CONTRACT.md')", "    pin(Path(__file__));pin(here/'PGROUP_CONTRACT.md');pin(here/'verify_csa.py',VERIFY_SHA)")
    replace("         'entire mature CSA controller recovered')", "         'entire completed prefix controller recovered')")
    start=text.index("    proof=json.loads((source/'source-derivation.json').read_bytes())")
    end=text.index("    old_gen=json.loads((gen/'result.json').read_bytes())",start)
    replace(text[start:end], '''    pin(pbase/'result.json',PREFIX_BASELINE_SHA)
    need((pbase/'result.json').stat().st_size==PREFIX_BASELINE_BYTES,'exact closed prefix result')
    pb=json.loads((pbase/'result.json').read_bytes())
    need(pb['status']=='PREFIX_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE' and
         all(pb[k] is True for k in ('arithmetic_equivalent','fu_qualified','inputs_unchanged',
             'generated_inputs_unchanged','original_classpath_unchanged','all_children_reaped')) and
         pb['candidate_source_sha256']==PREFIX_DATAPATH_SHA and pb['candidate_wrapper_sha256']==WRAPPER_SHA,
         'completed applicable exact prefix arithmetic, FU and local cost')
    pin(pbase/'source-snapshot/VDotDatapath.scala',PREFIX_DATAPATH_SHA)
    pin(pbase/'source-snapshot/VDotElastic.scala',WRAPPER_SHA)
    need(len(pb['generated'])==4 and {(x['feature'],x['kind']) for x in pb['generated']}==
         {(f,k) for f in (0,1) for k in ('cost','fu')},'complete prior prefix consumer set')
    for entry in pb['generated']:
        feature,kind=entry['feature'],entry['kind']
        rtl=pbase/f'{kind}-feature{feature}'/'rtl'
        top='CommonFuCostTop' if kind=='cost' else 'VDotElasticFuTestTop'
        expected={'VDotCarrySaveRows.sv','VDotElastic.sv',f'VDotPrefixFinish{20 if feature else 19}.sv',top+'.sv','extern_modules.sv'}
        need(len(entry['files'])==5 and {Path(x['path']).name for x in entry['files']}==expected,
             'closed five-file prior prefix generated set')
        for rec in entry['files']:
            path=pbase/rec['path'];need(path.parent==rtl,'exact prefix consumer-relative path')
            pin(path,rec['sha256']);need(path.stat().st_size==rec['bytes'],'exact prefix generated length')
        pin(rtl/'filelist.f',entry['filelist_sha256'])
        pin(rtl/'firrtl_black_box_resource_files.f',entry['resource_manifest_sha256'])
    need(len(pb['prefix_miters'])==2 and {m['width'] for m in pb['prefix_miters']}=={19,20},
         'exact two original prefix SAT records')
    for miter in pb['prefix_miters']:
        width=miter['width'];feature=1 if width==20 else 0
        need(miter['feature']==feature and miter['row_count']==(4 if feature else 2) and
             miter['status']=='PASS' and miter['solver_equivalence_proved'] is True and
             miter['unconstrained_inputs'] is True and miter['counterexample_found'] is False and
             miter['exit_code']==0 and miter['retried'] is False,'complete exact old prefix SAT qualification')
        pin(pbase/f'cost-feature{feature}/rtl/VDotPrefixFinish{width}.sv',miter['actual_rtl_sha256'])
        for name,key in (('gold.sv','gold_sha256'),('gate.sv','gate_sha256'),('prove.ys','script_sha256')):
            pin(pbase/f'prefix-proof-{width}'/name,miter[key])
        log=pin(pbase/f'actual-prefix-{width}-miter.log',miter['log_sha256']).read_text()
        need(log.count('SAT proof finished - no model found: SUCCESS!')==1 and
             'SAT proof finished - model found: FAIL!' not in log and 'ERROR:' not in log,
             'actual preserved original successful prefix solver log')
    proof=json.loads((source/'source-derivation.json').read_bytes())
    need(proof['contract']==CONTRACT and proof['baseline_datapath_sha256']==PREFIX_DATAPATH_SHA and
         proof['candidate_datapath_sha256']==SOURCE_SHA and proof['baseline_wrapper_sha256']==WRAPPER_SHA and
         proof['candidate_wrapper_sha256']==WRAPPER_SHA and proof['wrapper_byte_identical'] is True and
         proof['exact_inverse'] is True and len(proof['edits'])==1,'single exact P-object source derivation')
    prior_datapath=(pbase/'source-snapshot/VDotDatapath.scala').read_bytes()
    restored=candidate.read_bytes().decode('utf-8')
    for edit in reversed(proof['edits']):
        need(restored.count(edit['after'])==1,'unique P-object inverse')
        restored=restored.replace(edit['after'],edit['before'],1)
    need(restored.encode()==prior_datapath,'all original prefix source outside P object retained')
    need(wrapper.read_bytes()==(pbase/'source-snapshot/VDotElastic.scala').read_bytes(),
         'entire prefix wrapper unchanged including state, clock, reset, R finish and control')
''')
    replace("        'prefix.py':Path(__file__),'PREFIX_CONTRACT.md':here/'PREFIX_CONTRACT.md',",
            "        'pgroup.py':Path(__file__),'PGROUP_CONTRACT.md':here/'PGROUP_CONTRACT.md',\n        'verify_csa.py':here/'verify_csa.py',\n        'prefix-result.json':pbase/'result.json',\n        'prefix-VDotDatapath.scala':pbase/'source-snapshot/VDotDatapath.scala',\n        'prefix-VDotElastic.scala':pbase/'source-snapshot/VDotElastic.scala',")
    replace("    snapshots={}\n    for name,source in copies.items():", '''    for width in (19,20):
        for name in ('gold.sv','gate.sv','prove.ys'):
            copies[f'prefix-proof-{width}-{name}']=pbase/f'prefix-proof-{width}'/name
        copies[f'prefix-proof-{width}.log']=pbase/f'actual-prefix-{width}-miter.log'
        copies[f'prefix-finish-{width}.sv']=pbase/f'cost-feature{1 if width==20 else 0}/rtl/VDotPrefixFinish{width}.sv'
    snapshots={}
    for name,source in copies.items():''')
    replace("        csa_baseline_result_sha256=CSA_BASELINE_SHA,csa_baseline_result_bytes=CSA_BASELINE_BYTES,",
            "        csa_baseline_result_sha256=CSA_BASELINE_SHA,csa_baseline_result_bytes=CSA_BASELINE_BYTES,\n        prefix_baseline_result_sha256=PREFIX_BASELINE_SHA,prefix_baseline_result_bytes=PREFIX_BASELINE_BYTES,")
    replace("        representation_equivalence_basis='Byte-identical actual CSA and reused complete structural proof; two new unconstrained SAT proofs of actual prefix modules; source inverse, emitted wrapper binding and actual FU checks. No whole-FU sequential SAT claim.',",
            "        representation_equivalence_basis='New strict complete proof of actual P CSA bytes; exact-byte reuse of two unconstrained prefix SAT proofs; source inverse, emitted wrapper binding and actual new FU checks. No whole-FU sequential SAT claim.',")
    replace("                binding=wrapper_binding((rtl/'VDotElastic.sv').read_text(),", "                need((rtl/'VDotElastic.sv').read_bytes()==(pbase/f'{kind}-feature{feature}/rtl/VDotElastic.sv').read_bytes(),\n                     'entire emitted prefix wrapper remains byte-identical')\n                binding=wrapper_binding((rtl/'VDotElastic.sv').read_text(),")
    replace("            previous_rtl=cbase/f\"{row['kind']}-feature{row['feature']}\"/'rtl'\n            need((rtl/'VDotCarrySaveRows.sv').read_bytes()==(previous_rtl/'VDotCarrySaveRows.sv').read_bytes()==\n                 (first/'VDotCarrySaveRows.sv').read_bytes(),\n                 'all four actual multiplier CSA modules exactly match their completed baseline bytes')",
            "            need((rtl/'VDotCarrySaveRows.sv').read_bytes()==(first/'VDotCarrySaveRows.sv').read_bytes(),\n                 'all four actual new CSA modules have identical complete bytes')")
    replace("                 (out/f'fu-feature{feature}/rtl'/name).read_bytes(),\n                 'actual cost and FU use the same complete prefix bytes')",
            "                 (out/f'fu-feature{feature}/rtl'/name).read_bytes()==\n                 (pbase/f'cost-feature{feature}/rtl'/name).read_bytes(),\n                 'actual new cost/FU R prefix bytes exactly match the previously proved modules')")
    start=text.index('        # Reuse the exact completed multiplier proof.')
    end=text.index("        for feature in (0,1):\n            env['VDOT_DOT16']=str(feature)\n            rtl=out/f'fu-feature{feature}'",start)
    replace(text[start:end], '''        # A new heap grouping needs a new proof over its real generated bytes.
        # The existing team verifier accepts arbitrary earlier-layer FA/HA grouping.
        report=out/'arithmetic-structure.json'
        command('actual-csa-structure',[sys.executable,'-B',snap/'verify_csa.py',
            '--rtl',first/'VDotCarrySaveRows.sv','--output',report],60)
        structure=json.loads(report.read_bytes())
        need(structure['status']=='CSA_STRUCTURAL_EQUIVALENCE_PASS' and
             structure['all_inputs_equivalent'] is True and structure['parsed_entire_module'] is True and
             structure['verifier']['sha256']==VERIFY_SHA and
             structure['rtl_sha256']==sha(first/'VDotCarrySaveRows.sv') and
             structure['full_adders']==477 and structure['half_adders']==17,
             'new complete actual CSA proof with fixed FA/HA counts')
        need(structure['discarded_carries']==[] and structure['rows_msb_to_lsb']['row0'][0]=="1'b1" and
             structure['rows_msb_to_lsb']['row1'][0]=="1'b0",
             'new integer signed-row invariant: no discarded carries and exact MSB1/0')
        result['arithmetic_structure_proof']=structure
        result['arithmetic_structure_proof_reused']=False
        result['direct_signed_row_encoding_verified']=True
        generated_pins[str(report)]=sha(report)
        result['historical_multiplication_miter']=dict(cb['independent_miter'])
        result['historical_multiplication_miter_source']=str(cbase)
        result['independent_miter']=dict(status='NOT_RUN',solver_equivalence_proved=False,
            retried=False,qualification_scope='new P candidate',
            reason='New actual structural proof is used; no new monolithic multiplication solver run.')
        result['prefix_miters']=json.loads(json.dumps(pb['prefix_miters']))
        result['prefix_miters_reused_from']=str(pbase)
        result['prefix_miters_reuse_basis']='Exact actual finish SV bytes, complete prior gold/gate/script/log pins and unconstrained-input SAT scope.'
        for miter in result['prefix_miters']:
            actual=out/f"cost-feature{miter['feature']}/rtl/VDotPrefixFinish{miter['width']}.sv"
            need(sha(actual)==miter['actual_rtl_sha256'],'new emitted R module matches the exact reused SAT proof')
        result['arithmetic_proof_completed']=True
        save(out/'result.json',result)
''')
    replace("                area_delta_from_rwidth=area-rb['cost_results'][feature]['cell_area'],",
            "                delta_from_prefix=dict(cell_area=area-pb['cost_results'][feature]['cell_area'],\n                    dff_cells=actual_dff-pb['cost_results'][feature]['dff_cells'],\n                    timing={n:{k:timing[n][k]-pb['cost_results'][feature]['timing'][n][k]\n                               for k in ('arrival_ns','slack_ns')} for n in timing}),\n                area_delta_from_rwidth=area-rb['cost_results'][feature]['cell_area'],")
    replace("        result.update(status='PREFIX_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE',", "        result.update(status='PGROUP_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE',")
    replace("        save(out/'final-artifact-pins.json',{**snapshots,**class_pins,**generated_pins})\n        result.update(status='PGROUP_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE',", "        save(out/'final-artifact-pins.json',{**snapshots,**class_pins,**generated_pins})\n        check()\n        need(time.monotonic()<deadline,'total budget after final manifest and pending-signal check')\n        result.update(status='PGROUP_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE',")
    replace("    for name in ('repo','cost-root','fu-root','signed8-local','rwidth-local','csa-local','output'):", "    for name in ('repo','cost-root','fu-root','signed8-local','rwidth-local','csa-local','prefix-local','output'):")
    replace("    p.add_argument('--cpu',type=int,choices=[1],default=1)", "    p.add_argument('--cpu',type=int,choices=[2],default=2)")
    return text,edits

def function_text(text,name):
    tree=ast.parse(text)
    node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name)
    return ast.get_source_segment(text,node)

def main():
    raw=(ROOT/'base/controller/prefix.py').read_bytes()
    assert sha(raw)==BASE_SHA
    source=(ROOT/'source/VDotDatapath.scala').read_bytes()
    derivation=(ROOT/'source/source-derivation.json').read_bytes()
    changed,edits=derive(raw.decode(),sha(source),sha(derivation))
    ast.parse(changed)
    restored=changed
    for e in reversed(edits):
        assert e['after'] and restored.count(e['after'])==1,('unique inverse',e['after'][:100])
        restored=restored.replace(e['after'],e['before'],1)
    assert restored.encode()==raw
    original=raw.decode()
    unchanged={n:function_text(original,n)==function_text(changed,n) for n in ('wrapper_binding','command','interrupt','check')}
    assert all(unchanged.values())
    first="        for feature in (0,1):\n            env['VDOT_DOT16']=str(feature)\n            rtl=out/f'fu-feature{feature}'"
    last="        result['fu_tests_completed']=True"
    old_fu=original[original.index(first):original.index(last)+len(last)]
    new_fu=changed[changed.index(first):changed.index(last)+len(last)]
    assert old_fu==new_fu
    dest=ROOT/'controller';dest.mkdir(exist_ok=False)
    (dest/'pgroup.py').write_bytes(changed.encode())
    checker=(ROOT.parents[1]/'source-review/csa-continuation-v4/verify_csa.py').read_bytes()
    assert sha(checker)==CHECKER_SHA
    (dest/'verify_csa.py').write_bytes(checker)
    record=dict(status='TEXT_DERIVED_NOT_EXECUTED',baseline_sha256=BASE_SHA,baseline_bytes=len(raw),
                candidate_sha256=sha(changed.encode()),candidate_bytes=len(changed.encode()),exact_inverse=True,edits=edits)
    (dest/'controller-derivation.json').write_text(json.dumps(record,indent=2)+'\n')
    (dest/'controller.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),changed.splitlines(True),
        fromfile='prefix/controller/prefix.py',tofile='pgroup/controller/pgroup.py')))
    review=dict(status='STATIC_ONLY_NOT_EXECUTED',candidate_sha256=record['candidate_sha256'],
                syntax_ast_parse=True,complete_controller_inverse=True,mature_functions_byte_identical=unchanged,
                entire_fu_tail_byte_identical=True,fu_tail_sha256=sha(new_fu.encode()),
                checker_byte_identical=True,checker_sha256=CHECKER_SHA,runtime_commands_started=0)
    (dest/'static-review.json').write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k!='edits'},indent=2))

if __name__=='__main__':
    main()
