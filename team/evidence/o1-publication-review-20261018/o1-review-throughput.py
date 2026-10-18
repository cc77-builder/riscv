import collections,hashlib,json,pathlib,sys
root=pathlib.Path('/mnt/c/Code/RVInno/riscv')
out=root/'team/out/o1-publication-review-20261018'
cache=pathlib.Path('/home/amesotten/.cache/codex-rvinno/o1-complete-20261018/archive-replay/raw')
evidence=root/'team/evidence/o1-complete-20261018'
inventory=json.loads((evidence/'validation.tar.gz.json').read_text())['files']
path=cache/'runs-01/batch128/stderr.log'
raw=path.read_bytes()
if hashlib.sha256(raw).hexdigest()!=inventory['runs-01/batch128/stderr.log']:raise ValueError('raw transcript drift')
sys.path.insert(0,str(root/'team/optimizations/o1'))
from check_trace import ExuAudit,record,require
from check_extended import extended_audit
lines=raw.decode().splitlines();summary,events=extended_audit(lines)
audit=ExuAudit(2);frames={}
for line in lines:
    if line.startswith('O1_EXU_BEGIN '):audit.begin(record(line)[1])
    elif line.startswith('O1_EXU '):
        frame=record(line)[1];audit.frame(frame);frames[frame['cycle']]=frame
audit.finish()
archived=json.loads((cache/'recheck.json').read_text())
require(hashlib.sha256((cache/'recheck.json').read_bytes()).hexdigest()==inventory['recheck.json'],'summary drift')
samples=archived['results']['batch128']['result']['samples']
windows=[];all_gaps=[];tail_examples=[]
for sample in samples:
    lo,hi=sample['sample_ticks'][1:3]
    tx=[t for t in audit.transactions if lo<=t.cycle<hi]
    require(len(tx)==(sample['dots'] if sample['method']=='vdot' else 0),'window acceptance count differs')
    gaps=[b.cycle-a.cycle for a,b in zip(tx,tx[1:])]
    all_gaps.extend(gaps)
    for previous,following in zip(tx,tx[1:]):
        if following.cycle-previous.cycle>2:
            # Report only directly visible interface state, not inferred causes.
            tail_examples.append(dict(seq=sample['seq'],previous=previous.cycle,response=previous.end,
                                      following=following.cycle,gap=following.cycle-previous.cycle,
                                      recorded_frames=[frames[c] for c in sorted(frames) if previous.end<=c<=following.cycle]))
    windows.append(dict(seq=sample['seq'],phase=sample['phase'],repeat=sample['repeat'],method=sample['method'],
                        cycles=sample['cycles'],instructions=sample['instructions'],dots=sample['dots'],
                        accepted=len(tx),first_accept=tx[0].cycle if tx else None,last_response=tx[-1].end if tx else None,
                        accept_gap_histogram=dict(sorted(collections.Counter(gaps).items())),
                        response_to_next_accept_handoffs=sum(a.end==b.cycle for a,b in zip(tx,tx[1:]))))
result=dict(status='O1_BATCH_THROUGHPUT_REVIEW',raw_sha256=hashlib.sha256(raw).hexdigest(),new_cpu_runs=0,
            source_pack_sha256='7c4d9c4306703ce95a1aa20ac8d070327f7c7a852cb03f279f30c4799f45bb9d',
            complete_trace=summary,windows=windows,within_window_gap_histogram=dict(sorted(collections.Counter(all_gaps).items())),
            delayed_pairs=len(tail_examples),delayed_pair_frames=tail_examples,performance_ab=False,
            limits=['one fixed dataset/seed/image; no same-source baseline/T14 run',
                    'EXU interface cannot attribute idle gaps to wakeup/frontend/cache',
                    'window cycles/dot is not FU II or Fmax; no power/STA claim'])
result['delayed_pair_response_states']={
    'no_input_valid':sum(not x['recorded_frames'][0]['iv'] for x in tail_examples),
    'input_valid_blocked_with_redirect':sum(x['recorded_frames'][0]['iv'] and
        not x['recorded_frames'][0]['ir'] and x['recorded_frames'][0]['fv'] for x in tail_examples)}
measured=[w['cycles'] for w in windows if w['phase']=='measured' and w['method']=='vdot']
result['measured_vdot_cycles']=measured
result['measured_vdot_mean']=sum(measured)/len(measured)
result['measured_rvv_cycles']=[w['cycles'] for w in windows if w['phase']=='measured' and w['method']=='rvv']
(out/'throughput.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('delayed_pair_frames','complete_trace')},indent=2))
