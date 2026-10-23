from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,sys
base=Path('/home/amesotten/.cache/codex-rvinno/merge-reg-20261023');old=base.parent/'o5-fullcore-20261021';root=base/'repo'
sys.path.insert(0,str(root/'team/optimizations/o2/fullcore'));import analyze
log=old/'runs/supplements-01/o2-control-diagnostic/run.log';raw=log.read_bytes();text=raw.decode()
proof=analyze.analyze(text);events,_=analyze.extract_events_and_uart(text)
build=json.loads((old/'inputs/supplement-control/build.json').read_text());ranges=[(r['group'],int(r['begin'],16),int(r['end'],16)) for r in build['compiled_cases']]
by=defaultdict(list)
for cycle,_,kind,f in events:by[cycle].append((kind,f))
rob_pc={};seq_pc={};kill_rows=[];classes=Counter()
def pc_info(seq):
 pc=seq_pc.get(seq)
 return dict(seq=seq,pc=hex(pc) if pc is not None else None,group=next((g for g,a,b in ranges if pc is not None and a<=pc<b),None))
for cycle,items in sorted(by.items()):
 for k,f in items:
  if k=='ENQUEUE':rob_pc[f['rob']]=f['pc']
 for k,f in items:
  if k=='ACCEPT':seq_pc[f['seq']]=rob_pc[f['rob']]
 st=next((f for k,f in items if k=='STATE'),None)
 if st and (st['killp'] or st['killr']):
  label='both_slots_cancelled' if st['killp'] and st['killr'] else 'one_slot_occupied' if st['occupancy']==1 else 'partial_kill'
  classes[label]+=1
  kill_rows.append(dict(cycle=cycle,classification=label,occupancy=st['occupancy'],p=pc_info(st['pseq']) if st['pvalid'] else None,r=pc_info(st['rseq']) if st['rvalid'] else None,killp=st['killp'],killr=st['killr']))
if classes['partial_kill']!=proof['counts'].get('PARTIAL_KILL',0):raise ValueError('diagnostic counts disagree with strict observer')
result=dict(status='HISTORICAL_COVERAGE_DIAGNOSIS',log=str(log),log_sha256=hashlib.sha256(raw).hexdigest(),analyzer_sha256=hashlib.sha256(Path(analyze.__file__).read_bytes()).hexdigest(),strict_trace_status=proof['status'],counts=proof['counts'],kill_classification=dict(classes),kill_windows=kill_rows,new_emu_runs=0,performance_measured=False,scope='Old 0484 control trace only; does not certify the new H1 campaign')
(base/'historical-partial-kill-diagnosis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(strict_trace=proof['status'],classes=classes,kills=len(kill_rows))))
