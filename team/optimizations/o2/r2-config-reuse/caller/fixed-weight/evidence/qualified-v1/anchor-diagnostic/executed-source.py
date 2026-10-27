"""Post-hoc timing decomposition of qualified formal anchors; no new selection.

The middle interval includes software issue gaps and all inter-call work. It is
not standalone FU latency. No interval is subtracted across different N values.
"""
from pathlib import Path
import bisect,collections,hashlib,importlib.util,json,os,sys,time

ROOT=Path('/home/lizufan/riscv-lab/r2s3-fixed-weight-20261025-0920')
OPERATION='20261025-LiZufan001-r2s3-fixed-weight-0920'
IMAGE='ec41c369d718a30b8b82edad5adea06c52366b44dadcf19f137bf78deb6fa22c'
PARSER='team/optimizations/o2/fullcore/analyze.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def need(ok,why):
 if not ok:raise ValueError(why)
def main():
 os.sched_setaffinity(0,{0});started=time.time()
 source,build,run,post=ROOT/'source',ROOT/'build-02',ROOT/'run-01',ROOT/'post-01'
 out=ROOT/'anchor-diagnostic-01.json'
 need(not out.exists(),'fresh diagnostic output')
 state=read(run/'state.json');pr=read(post/'postprocess.json');br=read(build/'build.json')
 need(state['status']=='SPLIT_CAMPAIGN_PASS' and state['operation_id']==OPERATION and
      state['active_pid'] is None and state['active_result'] is None and state['new_emu_runs']==3,'closed original campaign')
 need(pr['status']=='FIXED_WEIGHT_POSTPROCESSING_PASS' and pr['original_run_state_sha256']==sha(run/'state.json') and
      pr['original_build_sha256']==sha(build/'build.json') and pr['image_sha256']==sha(build/'vdot-perf.bin')==IMAGE,'accepted postprocessing')
 for name,pin in pr['reports'].items():need(sha(post/name)==pin,'post report drift')
 need(sha(source/PARSER)==br['software_files'][PARSER],'frozen observer parser')
 validation=read(run/'runs/recovery/validation.json');rec=read(run/'runs/recovery/result.json')
 need(sha(run/'runs/recovery/validation.json')==rec['validation_sha256'],'accepted recovery validation')
 for name,pin in rec['raw_sha256'].items():need(sha(run/'runs/recovery'/name)==pin,'accepted raw log')
 spec=importlib.util.spec_from_file_location('fixed_anchor_original_observer',source/PARSER)
 observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
 text=(run/'runs/recovery/stderr.log').read_text()+(run/'runs/recovery/stdout.log').read_text()
 audit=observer.analyze(text);need(audit['status']=='O2_TRACE_PASS','original complete observer audit')
 # Public transactions omit the ROB entry. A FU response alone does not prove
 # architectural commitment: a later redirect can still squash that response.
 # Use the original observer's stronger, conservative whole-run zero-squash
 # condition; if it fails, this optional diagnostic stops without changing the
 # already qualified campaign or its HOLD decision.
 need(audit['counts']['ACCEPTED_THEN_SQUASHED']==0,'diagnostic requires no accepted-then-squashed transactions')
 transactions=audit['transactions'];ticks=[t['accept_cycle'] for t in transactions]
 need(ticks==sorted(ticks),'ordered actual transactions')
 prior_end=[-1]
 for t in transactions:prior_end.append(max(prior_end[-1],t['end_cycle']))
 manifest=read(build/'source/manifest.json');rows=[]
 for sample,plan in zip(validation['samples'],manifest['plan']):
  row=manifest['rows'][plan['index']]
  if not row['anchor'] or plan['repeat']<2:continue
  begin,end=sample['sample_ticks'][1:3]
  need(end-begin==sample['cycles'],'qualified counter interval')
  left,right=bisect.bisect_left(ticks,begin),bisect.bisect_left(ticks,end)
  need(prior_end[left]<begin,'diagnostic excludes carry-in transaction at timer start')
  selected=transactions[left:right]
  need(len(selected)==row['dots']==32*sample['n'] and all(t['outcome']=='response' for t in selected),'complete anchor requests')
  first=selected[0]['accept_cycle'];last=max(t['end_cycle'] for t in selected)
  need(begin<=first<=last<end,'response drained inside timed interval')
  values=[first-begin,last-first,end-last]
  need(sum(values)==sample['cycles'],'exact within-window decomposition')
  rows.append(dict(seq=sample['seq'],n=sample['n'],dataset=plan['dataset'],order=plan['order_group'],
      position=plan['anchor_position'],cycles=sample['cycles'],instructions=sample['instructions'],
      before_first_accept=values[0],first_accept_to_last_response=values[1],after_last_response=values[2],
      latency_histogram=dict(sorted(collections.Counter(str(t['elapsed_cycles']) for t in selected).items())),
      writeback_stall_events=sum(t['writeback_stall_events'] for t in selected),vdot_requests=len(selected)))
 need(len(rows)==48,'all formal anchors')
 groups=[]
 for n in (1,4):
  for d in range(3):
   for order in range(2):
    for position in ('start','end'):
     selected=[r for r in rows if (r['n'],r['dataset'],r['order'],r['position'])==(n,d,order,position)]
     need(len(selected)==2,'each original anchor cell has two samples')
     totals={k:sum(s[k] for s in selected) for k in ('cycles','before_first_accept','first_accept_to_last_response','after_last_response')}
     groups.append(dict(n=n,dataset=d,order=order,position=position,seqs=[r['seq'] for r in selected],totals=totals))
 report=dict(status='POSTHOC_QUALIFIED_ANCHOR_TIMING_DECOMPOSITION',operation_id=OPERATION,
      image_sha256=IMAGE,build_sha256=sha(build/'build.json'),state_sha256=sha(run/'state.json'),
      source_sha256={PARSER:sha(source/PARSER)},diagnostic_source_sha256=sha(Path(__file__)),
      validation_sha256=rec['validation_sha256'],raw_sha256=rec['raw_sha256'],
      samples=rows,groups=groups,started=started,finished=time.time(),new_emu_runs=0,
      accepted_then_squashed_entire_recovery=audit['counts']['ACCEPTED_THEN_SQUASHED'],
      carry_in_excluded=True,
      qualification_unchanged=True,decision=validation['selection']['decision'],
      scope='Post-hoc within-window decomposition only. Middle span includes software gaps and inter-call work. No causal attribution, cross-N subtraction, threshold correction or new algorithm selection.')
 out.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ('status','image_sha256','decision','new_emu_runs','groups')},indent=2))

if __name__=='__main__':main()
