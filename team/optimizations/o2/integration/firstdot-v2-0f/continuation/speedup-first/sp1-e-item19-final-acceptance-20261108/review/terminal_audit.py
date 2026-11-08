"""Read-only terminal synthesis of the pre-frozen final campaign. Never launches targets."""
from pathlib import Path
import datetime,hashlib,json,math
F=Path(__file__).resolve().parent.parent
P=F.parent
R=next(x for x in P.parents if (x/'AGENTS.md').is_file() and (x/'team/docs/version-data-ledger.json').is_file())
def read(p):return json.loads(Path(p).read_text())
def need(x,m):
 if not x:raise ValueError(m)
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def check_pin(x):
 actual=pin(x['path']);need(all(actual[k]==x[k]for k in ['path','bytes','sha256']), 'pin mismatch '+x['path']);return actual
def field(o,p):
 for k in p.split('.'):o=o[k]
 return o
C=read(F/'CONTRACT.json');B=read(F/'target-01/batch.json');G=read(F/'external-batch/RESULT.json');Z=read(F/'EXECUTION_FREEZE.json')
need(B['status']=='ITEM19_REQUIRED_REPLAYS_PASS','five-role campaign not complete')
need(G['status']=='GUARD_PASS' and G['cleanup_ok'] and not G['remaining_live_processes'],'outer guardian/cleanup')
need(B['launch_attempts']==B['target_processes_started']==len(B['roles'])==5,'exact five roles')
need([x['role']for x in B['roles']]==[x['name']for x in C['roles']],'role ordering')
need(B['target_active_seconds']<=7500 and B['host_seconds']<=900 and B['elapsed_seconds']<=8400 and G['elapsed_seconds']<=8400,'original batch budget')
for x in Z['files']:check_pin(x)
roles=[];vals=[];previous_end=None
for number,(spec,entry)in enumerate(zip(C['roles'],B['roles']),1):
 check_pin(entry['validation']);rd=F/'target-01'/('%02d-%s'%(number,spec['name']));V=read(rd/'validation.json');M=read(rd/'record.json');A=read(rd/'launch.json');I=read(rd/'execution-identity.json');O=V['collector']
 need(V['actual_target'] and V['runtime']['status']=='ACTUAL_RUNTIME_RECEIPT_PASS' and O['acceptance_comparison']=='PASS','actual validation')
 need(M['exit_code']==0 and M['resource_ok'] and M['cleanup_ok'] and M['stop_reason']is None and not M['final_snapshot']['processes'],'normal exit/resources/cleanup')
 need(M['elapsed_seconds']<=spec['wall_seconds'] and 0<M['guest_cycles']<=spec['guest_cycles'],'role budget')
 need(M['guest_cycles']==O['guest_cycles']==entry['guest_cycles'],'guest consistency')
 need(M['peak_threads']<=4 and M['peak_rss_bytes']<=12*1024**3,'resource samples')
 need(M['execution_identity']==I and M['command']==I['command']==A['command'] and M['cwd']==I['cwd']==A['cwd'],'actual runtime binding')
 need(I['executable_sha256']==C['runtime'][spec['emu']]['sha256'],'actual hardware identity')
 need(C['runtime']['normal_reference']['path']in M['observed_mapped_files'],'live NEMU reference mapping')
 need(not M['raw_truncated'],'raw logs complete')
 for x in V['runtime']['files'].values():check_pin(x)
 for stream in ['stdout','stderr']:
  q=pin(rd/(stream+'.log'));need(q['sha256']==M['raw_sha256'][stream] and q['bytes']==M['observed_bytes'][stream]==M['retained_bytes'][stream],'raw identity')
 if previous_end is not None:need(M['started_monotonic']>=previous_end,'serial execution')
 previous_end=M['ended_monotonic']
 comparisons=[]
 for comp in spec.get('comparisons',[]):
  old=read(comp['path']);old=field(old,comp['prefix']) if comp.get('prefix')else old
  for key in comp['fields']:need(field(O,key)==field(old,key),'replay/pair mismatch '+key)
  comparisons.append(dict(reference=pin(comp['path']),fields=comp['fields'],pass_all=True))
 if spec['kind']=='supplement':need(O['calls']==41 and O['commits']==77 and O['full128'],'full supplement scope')
 else:need(O['commits']==1208 and O['checked_register_bytes']==131072 and O['csr_contract']['trials']==256,'full original scope')
 roles.append(dict(role=spec['name'],active_seconds=M['active_wall_seconds'],supervised_seconds=M['elapsed_seconds'],guest_cycles=M['guest_cycles'],peak_threads=M['peak_threads'],peak_rss_bytes=M['peak_rss_bytes'],raw_bytes=sum(M['retained_bytes'].values()),comparison= comparisons,validation=pin(rd/'validation.json'),receipt=pin(rd/'record.json')));vals.append(V)
need(math.isclose(sum(x['active_seconds']for x in roles),B['target_active_seconds'],abs_tol=1e-6),'sum target budget')
# S0/S1 must both be demonstrated by the plain functional SP1 binary and repeated.
for V in vals[:2]:
 detail=V['collector']['detail'];need(detail['status']=='SUPPLEMENT_TRACE_HIT'and detail['witnesses']['S0']and detail['witnesses']['S1'],'actual plain-SP1 S0/S1')
 for k in ['STALL','ENQUEUE_P','FULL_STALL','KILL_P','PARTIAL_KILL','P_KILL_R_SURVIVES']:need(detail['counts'][k]>0,'missing supplement '+k)
need(vals[0]['collector']['detail']['witnesses']==vals[1]['collector']['detail']['witnesses'],'witness replay')
original=vals[3]['collector'];need(original['counts']['KILL_R']>0 and original['counts']['DIV_ACCEPT']==original['counts']['DIV_RESPONSE']==256,'original KILL_R/DIV')
# Baseline never lends its slot coverage to the candidate. Pair ISA-visible summaries only.
for key in ['cross_hardware_architecture','functional_replay.uart_checks','functional_replay.csr_contract']:
 need(field(vals[3]['collector'],key)==field(vals[4]['collector'],key),'original cross-hardware architecture')
N=read(F/'target-01/01-supplement-candidate-normal/neutrality.json');need(N['status']=='PASS_EXACT_EFFECTIVE_SP1_T13','observer neutrality')
# Actual negative guards preserved as separate historical evidence, not rerun.
ledger=read(R/'team/docs/version-data-ledger.json')['records'];old=ledger[82]
for k in ['negative','negative_validation']:check_pin(old['evidence'][k])
need(old['negative_qualified'],'original-image bit100')
m4=P/'sp1-e-item19-m4-fp-pressure-20261108';m4batch=read(m4/'target-01/batch.json');need(m4batch['roles'][0]['status']=='NEW_GUARD_BIT100_LOG_PASS','M4 bit100')
check_pin(m4batch['roles'][0]['validation'])
# Rechecked immutable summaries for the other 19 cases.
reuse=read(F/'review/OTHER19_EVIDENCE_RECHECK.json');need(reuse['status']=='PASS_SELECTED_REUSE_PINS','other19 evidence')
for row in reuse['records']:
 for x in row['pins']:check_pin(x)
need(read(F/'review/COST_REUSE.json')['status']=='REUSED_NEW_SP0_COST_47_OF_47','SP0 cost')
need(read(F/'review/PATCH_SOURCE_AUDIT.json')['status']=='PASS_FROZEN_FUNCTIONAL_SOURCE','functional candidate source audit')
result=dict(schema='item19-terminal-synthesis-v1',status='PASS_ITEM19_FULL_COVERAGE_AND_REPLAYS',recorded_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),item19_qualified=True,coverage_qualified=20,coverage_required=20,default_changed=False,github_upload=False,roles=roles,freeze_files_rechecked=len(Z['files']),target_seconds=B['target_active_seconds'],host_seconds=B['host_seconds'],outer_seconds=G['elapsed_seconds'],raw_bytes=B['log_bytes'],witnesses=vals[0]['collector']['detail']['witnesses'],supplement_counts=vals[0]['collector']['detail']['counts'],original_counts=original['counts'],neutrality=N,original_negative=old['evidence']['negative_validation'],supplement_negative=m4batch['roles'][0]['validation'],matrix_method='original image full numeric/CSR/register coverage and all previous covers preserved, plus same-candidate M4 S0/S1; original 1500-second contract HOLD preserved; new pre-frozen 2400-second replay contract passed',CSR_scope='actual target self-check plus live DiffTest; not independent per-trial numeric CSR dumps',resource_scope='50ms process-group samples, not instantaneous kernel peak guarantee',replay_scope='all eight frozen same-hardware semantic/raw-event digests; banners and host elapsed text are provenance only',new_three_metrics={k:'NOT_TESTED'for k in ['speedup','area','timing']},new_EMU_runs=5,new_standalone_NEMU_runs=0,new_DiffTest_reference_sessions=5,evidence={str(x.relative_to(F)):pin(x)for x in [F/'CONTRACT.json',F/'EXECUTION_FREEZE.json',F/'RUN_AUTHORIZATION.json',F/'host/RESULT.json',F/'target-01/batch.json',F/'external-batch/RESULT.json']})
(F/'review/TERMINAL_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['status'])
