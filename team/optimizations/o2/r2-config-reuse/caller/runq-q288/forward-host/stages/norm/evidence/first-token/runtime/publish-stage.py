from pathlib import Path
import datetime, hashlib, importlib.util, json, os, shutil
REPO=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/checkout/source')
OUT=REPO.parents[1]/'runs/first-token-close-20261028-1127'
PREV=REPO.parents[1]/'runs/norm-resume-20261027-2000'
STAGES=REPO/'team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def pin(p):return dict(bytes=p.stat().st_size,sha256=sha(p))
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
state=json.loads((OUT/'pipeline-state.json').read_text())
assert state['steps']['seal']['status']=='PASS' and state['steps']['restore']['status']=='PASS'
archive=OUT/'evidence-01/archive'
report=json.loads((archive/'verification.json').read_text())
assert report['archive_sha256']=='5dd9c61601ed204ba6d0475da2fb5319b36a164129257ea6eeea23f85bdfc28e'
pub=OUT/'publication-01';pub.mkdir()
metadata={}
for name,source in [('manifest.json',archive/'manifest.json'),('verification.json',archive/'verification.json'),('restore-verification.json',OUT/'restore-verification.json')]:
 shutil.copyfile(source,pub/name);metadata[name]=pin(pub/name)
parts=[];whole=hashlib.sha256();total=0
with (archive/'payload.zip').open('rb') as source:
 while True:
  block=source.read(20*1024*1024)
  if not block:break
  name=f'payload.zip.part-{len(parts)+1:04d}'
  with (pub/name).open('xb') as dest:dest.write(block)
  whole.update(block);total+=len(block)
  parts.append(dict(path=name,bytes=len(block),sha256=hashlib.sha256(block).hexdigest()))
assert total==report['archive_bytes'] and whole.hexdigest()==report['archive_sha256']
save(pub/'parts.json',dict(format='forward-evidence-parts-v1',artifact='payload.zip',bytes=total,sha256=whole.hexdigest(),parts=parts,metadata=metadata))
helper=STAGES/'restore.py'
assert sha(helper)=='8eddb62724dda7b96a658dda9c795e01575ceb9338b143832e7f5b41aa1a2811'
spec=importlib.util.spec_from_file_location('published_restore',helper)
restore=importlib.util.module_from_spec(spec);spec.loader.exec_module(restore)
joined=restore.restore(pub,OUT/'reassembled-01')
assert joined['archive_sha256']==report['archive_sha256']
shutil.copyfile(OUT/'reassembled-01/transport-receipt.json',pub/'transport-receipt.json')
p=PREV/'first-token-target-01/results.json'
assert sha(p)=='57643f2429a21df0c3035777af5277865700d27d03aef7db0db9985afe8b4f51'
r=json.loads(p.read_bytes());vs=r['validations']
assert r['target_correctness_qualified'] and not r['performance_qualified'] and not r['full_retirement_window_audited']
assert vs['ta']==vs['replay']
rows={}
for name,v in vs.items():
 c=v['counter_values']
 assert c==[z['sample']['data'] for z in v['counter_audit']['records']]
 assert c==[z['retire']['data'] for z in v['counter_audit']['records']]
 sample=v['samples'][0]
 assert (c[3]-c[0],c[2]-c[1])==(sample['cycles'],sample['instret'])
 by_function={}
 for pc,count in v['custom']['per_site'].items():
  f=v['custom']['sites'][pc]['function']
  by_function[f]=by_function.get(f,0)+count
 assert sum(by_function.values())==v['custom']['count']
 if name!='fr':
  assert by_function=={'q768_ta':6*36*24*32,'q288_tail_vdot':172*36*9*32}
  assert v['custom']['per_site']==v['custom']['enqueue_per_site']
 rows[name]=dict(status=v['status'],window=sample,guest_cycles=v['guest_cycles'],flags=v['flags'],counter_values_hex=[f'{n:016x}' for n in c],custom_commits=v['custom']['count'],custom_by_function=by_function,protocol_counts={k:v['protocol']['counts'][k] for k in ('ACCEPT','MOVE','RESPONSE','ENQUEUE','COMMIT','STALL','FULL_STALL','KILL','VFEX4_WAIT')},response_latency_histogram=v['protocol']['response_latency_histogram'],one_cycle_accept_gaps=v['protocol']['observed_accept_gap_histogram'].get('1',0),unfinished={k:v['protocol'][k] for k in ('pending_count','pending_div_count','unfinished_rob_count')},exact_dynamic_count_claimed_by_original_validator=v['custom']['exact_dynamic_count_claimed'])
negative_gap=rows['ta']['guest_cycles']-rows['negative']['guest_cycles']
window_gap=rows['ta']['window']['cycles']-rows['negative']['window']['cycles']
summary=dict(status='FIRST_TOKEN_DERIVED_ARITHMETIC_CHECK_PASS',created=datetime.datetime.now(datetime.timezone.utc).isoformat(),original_results=pin(p),ta_replay_complete_validation_equal=True,rows=rows,geometry_crosscheck=dict(k288_groups=172*36*9,k768_groups=6*36*24,custom_per_group=32,custom_total=(172*36*9+6*36*24)*32,original_validator_field_unchanged=True),negative_normal_difference=dict(guest_cycles=negative_gap,window_cycles=window_gap,outside_window_cycles=negative_gap-window_gap,exact_stage_attribution=False),fr_minus_ta_window_cycles=rows['fr']['window']['cycles']-rows['ta']['window']['cycles'],performance_qualified=False,full_retirement_window_audited=False,new_reference_runs=0,new_emu_runs=0)
save(pub/'analysis/target-summary.json',summary)
save(OUT/'publication-stage-result.json',dict(status='FIRST_TOKEN_FRAGMENT_STAGE_PASS',archive=report,transport=joined,manifest_sha256=sha(pub/'manifest.json'),parts_manifest_sha256=sha(pub/'parts.json'),derived_summary_sha256=sha(pub/'analysis/target-summary.json'),raw_recheck_qualification_pending=True))
print(json.dumps(dict(status='FIRST_TOKEN_FRAGMENT_STAGE_PASS',archive_bytes=total,parts=len(parts),last_part_bytes=parts[-1]['bytes'],manifest_sha256=sha(pub/'manifest.json'),parts_manifest_sha256=sha(pub/'parts.json'),native_results_sha256=sha(p),summary=summary),indent=2))
