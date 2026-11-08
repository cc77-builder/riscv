#!/usr/bin/env python3
"""A distinct, bounded Gold-association experiment; the Booth3 DUT is unchanged."""
from pathlib import Path
import ast
import difflib
import hashlib
import json

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'prefix-booth3-candidate-01'
BASE_SHA='bcde44c580003a0a99e18cc30a2795a9c7a9af08ed56ef38a8f740987ec8241f'


def main():
    raw=(BASE/'controller/booth3.py').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==BASE_SHA
    text=raw.decode();edits=[]
    def edit(before,after):
        nonlocal text
        assert before!=after and text.count(before)==1,(before[:100],text.count(before))
        assert text.count(after)==0,after[:100]
        text=text.replace(before,after,1);edits.append(dict(before=before,after=after))
    def lines_replace(before,after):
        for line in list(dict.fromkeys(x for x in text.splitlines(True) if before in x)):
            edit(line,line.replace(before,after))
    edit('"""Compile one three-row Booth candidate; prove new P and R arithmetic, then FU/cost."""',
         '"""Recheck unchanged Booth3 with a balanced independent Gold, then bounded FU/cost."""')
    edit("CONTRACT = 'dot16-prefix-booth3-local-v1'", "CONTRACT = 'dot16-prefix-booth3-balanced-gold-v1'")
    edit("CONTROLLER_BASELINE_SHA = '6681fce5cc739206c5922e025d76ae0a75334d57502b089902b5a7a72f05ea60'",
         "CONTROLLER_BASELINE_SHA = '"+BASE_SHA+"'")
    edit("    pbase=a.prefix_local.resolve()", "    pbase=a.prefix_local.resolve()\n    previous_failed=a.previous_failed.resolve()")
    edit("    need(a.cpu==2 and a.budget_seconds==1200 and not out.exists(), 'CPU2, exact 1200s work budget, fresh output')",
         "    need(a.cpu==2 and a.budget_seconds==300 and not out.exists(), 'CPU2, exact 300s work budget, fresh output')")
    edit('    for d in (repo,cost,fu,here,source,baseline,rbase,cbase,pbase):',
         '    for d in (repo,cost,fu,here,source,baseline,rbase,cbase,pbase,previous_failed):')
    edit("         'entire completed Booth2 controller recovered')", "         'entire original failed Booth3 controller recovered')")
    marker="    pin(cbase/'result.json',CSA_BASELINE_SHA)"
    edit(marker,"""    prior_path=pin(previous_failed/'result.json','7eb958143cc41f98cad195e0e7089b8924f827af340c51abca18ba573174d050')
    prior=json.loads(prior_path.read_bytes())
    need(prior['status']=='FAILED' and prior['contract']=='dot16-prefix-booth3-local-v1' and
         prior['candidate_source_sha256']==SOURCE_SHA and prior['candidate_wrapper_sha256']==WRAPPER_SHA and
         len(prior['commands'])==8 and all(c['reaped'] and c['group_absent'] for c in prior['commands']) and
         not prior['fu_results'] and not prior['cost_results'] and
         prior['prefix_miters'][0]['status']=='PASS' and prior['prefix_miters'][1]['status']=='FAILED',
         'exact closed predecessor retained; no FU/cost qualified')
    failure_log=pin(previous_failed/'actual-prefix-20-miter.log','957987acdcf4a9a90f8762444b0bad0c65b4618b19cf7e563201fb99094486a8')
    need('ERROR: Called with -verify and proof did time out!' in failure_log.read_text() and
         not prior['prefix_miters'][1]['counterexample_found'], 'prior solver timeout, not a counterexample')
    for old in prior['generated']:
        for f in old['files']:pin(previous_failed/f['path'],f['sha256'])
"""+marker)
    edit("    need(proof['contract']==CONTRACT and proof['baseline_datapath_sha256']==PREFIX_DATAPATH_SHA and",
         "    need(proof['contract']=='dot16-prefix-booth3-local-v1' and proof['baseline_datapath_sha256']==PREFIX_DATAPATH_SHA and")
    edit("        'prefix-result.json':pbase/'result.json',", "        'prefix-result.json':pbase/'result.json',\n        'prior-failed-result.json':prior_path,'prior-r20-timeout.log':failure_log,")
    edit("    result=dict(contract=CONTRACT,status='RUNNING',started=util.stamp(),commands=[],",
         "    result=dict(contract=CONTRACT,status='RUNNING',started=util.stamp(),commands=[],\n        prior_failed_result_sha256=sha(prior_path),prior_run_remains_failed=True,\n        reference_change='R20 Gold: (a0+a1+a2)+(a3+a4+a5); all120 input bits remain unconstrained.',\n        dut_source_unchanged_from_prior=True,proof_formulation_attempt=2,")
    edit("        first=out/'cost-feature0/rtl'", """        for old in prior['generated']:
            for f in old['files']:
                if Path(f['path']).name=='extern_modules.sv':continue
                need(sha(out/f['path'])==f['sha256'],
                     'complete regenerated DUT/top SV bytes unchanged from failed attempt '+f['path'])
        result['all_actual_DUT_SV_bytes_match_previous_failed_attempt']=True
        first=out/'cost-feature0/rtl'""")
    edit("            gold.write_text('module Gold('+ports+');\\nassign result='+\n                '+'.join(f'a{i}' for i in range(row_count))+';\\nendmodule\\n')",
         "            gold_expression='a0+a1+a2' if row_count==3 else '(a0+a1+a2)+(a3+a4+a5)'\n            gold.write_text('module Gold('+ports+');\\nassign result='+gold_expression+';\\nendmodule\\n')")
    edit("                qualification_scope='actual prefix combinational modular sum only',retried=False)",
         "                qualification_scope='actual prefix combinational modular sum only',retried=True,\n                retry_kind='new frozen contract; R20 Gold association changed, no original operation replay',\n                prior_attempt_contract='dot16-prefix-booth3-local-v1',gold_expression=gold_expression)")
    lines_replace('BOOTH3_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE','BOOTH3_BALANCED_GOLD_ARITHMETIC_FU_AND_COST_COMPLETE')
    edit("    for name in ('repo','cost-root','fu-root','signed8-local','rwidth-local','csa-local','prefix-local','output'):p.add_argument('--'+name,type=Path,required=True)",
         "    for name in ('repo','cost-root','fu-root','signed8-local','rwidth-local','csa-local','prefix-local','previous-failed','output'):p.add_argument('--'+name,type=Path,required=True)")
    edit("    p.add_argument('--budget-seconds',type=int,default=1200)", "    p.add_argument('--budget-seconds',type=int,default=300)")
    ast.parse(text)
    inverse=text
    for e in reversed(edits):
        assert inverse.count(e['after'])==1
        inverse=inverse.replace(e['after'],e['before'],1)
    assert inverse.encode()==raw
    out=ROOT/'controller';out.mkdir(parents=True,exist_ok=False)
    target=out/'booth3.py';target.write_text(text)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    (out/'controller-derivation.json').write_text(json.dumps(dict(baseline_sha256=BASE_SHA,
        candidate_sha256=sha(target),exact_inverse=True,edits=edits,
        DUT_source_changes=0,all_actual_DUT_SV_bytes_must_match_prior=True,
        original_failed_result_retained=True,new_solver_timeout_seconds=30,new_total_budget_seconds=300),indent=2)+'\n')
    (out/'controller.diff').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),
        text.splitlines(True),fromfile='failed01/booth3.py',tofile='balanced02/booth3.py')))
    for rel in ('source/VDotDatapath.scala','source/VDotElastic.scala','source/source-derivation.json','source/source.diff',
                'controller/verify_booth.py','controller/verifier-derivation.json'):
        b=(BASE/rel).read_bytes();p=ROOT/rel;p.parent.mkdir(exist_ok=True);assert not p.exists();p.write_bytes(b)
        assert p.read_bytes()==b
    print(json.dumps(dict(bytes=target.stat().st_size,sha256=sha(target),edits=len(edits),
        derivation_sha256=sha(out/'controller-derivation.json')),indent=2))


if __name__=='__main__':main()
