"""Read-only per-window acceptance observations; not an A/B performance result."""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
root=Path('/mnt/c/Code/RVInno/riscv')
sys.path.insert(0,str(root/'team/optimizations/o1'))
from check_trace import record
cache=Path('/home/amesotten/.cache/codex-rvinno/o1-optimization-20261019')
folder=cache/'extended-01/batch128'
paths=[folder/'stderr.log',folder/'checked.json',folder/'trace.json',
       root/'team/optimizations/o1/check_trace.py',Path(__file__)]
pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
checked=json.loads((folder/'checked.json').read_text())
assert checked['status']=='O1_CALIBRATED_WINDOWS_PASS'
frames=[record(line.strip())[1] for line in (folder/'stderr.log').read_text().splitlines()
        if line.strip().startswith('O1_EXU ')]
windows=[]
for sample in checked['samples']:
    if sample['method']!='vdot' or sample['phase']!='measured':continue
    lo,hi=sample['sample_ticks'][1:3]
    selected=[f for f in frames if lo<=f['cycle']<=hi]
    accepts=[f['cycle'] for f in selected if f['iv'] and f['ir'] and f['kind']==0]
    assert len(accepts)==sample['dots']==128
    assert hi-lo==sample['cycles']
    gaps=Counter(b-a for a,b in zip(accepts,accepts[1:]))
    row=dict(seq=sample['seq'],cycles=sample['cycles'],instructions=sample['instructions'],
             accepted=len(accepts),first_accept_offset=accepts[0]-lo,
             acceptance_span=accepts[-1]-accepts[0],after_last_accept=hi-accepts[-1],
             acceptance_gap_histogram=dict(sorted(gaps.items())),
             input_valid_not_ready_frames=sum(bool(f['iv'] and not f['ir']) for f in selected),
             output_backpressure_frames=sum(bool(f['ov'] and not f['ready']) for f in selected))
    assert row['first_accept_offset']+row['acceptance_span']+row['after_last_accept']==row['cycles']
    windows.append(row)
assert len(windows)==4
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in pins.items())
result=dict(status='CURRENT_BATCH_WINDOW_OBSERVATIONS',performance_ab=False,inputs=pins,
            windows=windows,limits='One workload/seed/configuration; no causal attribution, regression or speedup claim.')
with (cache/'window-observations.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(windows,indent=2))
