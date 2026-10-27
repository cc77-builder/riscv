"""Replay C3 test-only hold observations against unmodified parent cycle stream."""
import argparse,hashlib,json,re
from collections import Counter
from pathlib import Path
KEYS=set('schema cycle qualified reset te p fp_fire int_fire fp_out int_out cancel fp_hold int_hold expected_fp expected_int'.split())
def need(x,why):
    if not x:raise ValueError(why)
def parse(line,prefix,keys=None):
    need(line.startswith(prefix+' '),'wrong record')
    out={}
    for token in line.split()[1:]:
        k,v=token.split('=',1);need(k not in out,'duplicate key')
        out[k]=int(v) if re.fullmatch(r'[0-9]+',v) else v
    if keys is not None:need(set(out)==keys,'monitor schema keys')
    return out
def check(monitor,parent):
    rows=[parse(x,'C3_HOLD',KEYS) for x in monitor.splitlines() if x.strip()]
    pr=[parse(x,'O2_PARENT_CYCLE') for x in parent.splitlines() if x.startswith('O2_PARENT_CYCLE ')]
    need(rows and len(rows)==len(pr),'monitor/parent length mismatch')
    qualified=0;expected_fp=0;expected_int=0;counts=Counter()
    for i,(m,p) in enumerate(zip(rows,pr)):
        need(m['schema']==1 and m['cycle']==p['cycle']==i,'monitor sequence')
        need(all(isinstance(m[k],int) and m[k] in (0,1) for k in KEYS-{'schema','cycle'}),'nonboolean monitor')
        need(m['reset']==p['reset'] and m['te']==p['te'],'sampling reset/TE mismatch')
        need(m['qualified']==qualified,'bootstrap qualification disagreement')
        need(m['fp_fire']==bool(p['child_fire']&4) and m['int_fire']==bool(p['child_fire']&2),'actual fire observation disagreement')
        need(m['fp_out']==bool(p['child_out']&4 and p['out_ready']) and m['int_out']==bool(p['child_out']&2 and p['out_ready']),'actual response fire observation disagreement')
        if not p['reset']:need(m['cancel']==p['kill_div'],'actual cancel disagreement')
        if qualified:
            need(m['p']==m['fp_fire'],'P_F differs from actual fire')
            need(m['fp_hold']==expected_fp and m['int_hold']==expected_int,'hold differs from original-fire recurrence')
            need(m['expected_fp']==expected_fp and m['expected_int']==expected_int,'shadow state disagreement')
            counts['qualified_cycles']+=1
            counts['fp_accepts']+=m['fp_fire'];counts['int_accepts']+=m['int_fire']
            counts['fp_hold_cycles']+=m['fp_hold'];counts['int_hold_cycles']+=m['int_hold']
            counts['te0_reset_cycles']+=bool(m['reset'] and not m['te'])
            counts['cancel_cycles']+=bool(m['cancel'] and not m['reset'])
            counts['fp_cancel_cycles']+=bool(m['cancel'] and m['fp_hold'] and not m['reset'])
            counts['fp_release_cycles']+=bool(m['fp_out'] and not m['reset'])
            counts['fp_backpressure_cycles']+=bool(p['child_out']&4 and not p['out_ready'] and not m['reset'])
            if p['case'].startswith('C2-sqrt-') and m['fp_fire']:counts['sqrt_accepts']+=1
        else:need(m['reset'] and m['te'],'unqualified activity before real reset+TE bootstrap')
        expected_fp=0 if m['reset'] else int(m['fp_fire'] or (m['fp_hold'] and not(m['fp_out'] or m['cancel'])))
        expected_int=0 if m['reset'] else int(m['int_fire'] or (m['int_hold'] and not(m['int_out'] or m['cancel'])))
        if m['reset'] and m['te']:qualified=1;counts['bootstrap_edges']+=1
    need(qualified and expected_fp==expected_int==0 and rows[-1]['fp_hold']==rows[-1]['int_hold']==0,'final holds not drained')
    for k in ['qualified_cycles','fp_accepts','int_accepts','fp_hold_cycles','int_hold_cycles','te0_reset_cycles','cancel_cycles','fp_cancel_cycles','fp_release_cycles','fp_backpressure_cycles','sqrt_accepts']:
        need(counts[k]>0,'vacuous coverage '+k)
    return dict(status='C3_HF_HOLD_MONITOR_PASS',cycles=len(rows),counts=dict(counts),
                scope='Actual new RTL TEST TOP observations; original fire recurrence after qualified synchronous bootstrap. Not async reset physical signoff.')
def negatives(monitor,parent):
    lines=monitor.splitlines()
    def change(condition,key,value):
        out=lines.copy()
        for i,line in enumerate(out):
            m=parse(line,'C3_HOLD',KEYS)
            if condition(m):
                out[i]=re.sub(r'(?<!\S)'+key+r'=\S+',key+'='+str(value(m)),line);return '\n'.join(out)+'\n'
        raise ValueError('missing negative target '+key)
    tests={
      'P_F_wrong':change(lambda m:m['fp_fire']==1,'p',lambda m:0),
      'FP_hold_wrong':change(lambda m:m['qualified'] and m['fp_hold'],'fp_hold',lambda m:0),
      'INT_hold_wrong':change(lambda m:m['qualified'] and m['int_hold'],'int_hold',lambda m:0),
      'FP_shadow_wrong':change(lambda m:m['qualified'] and m['expected_fp'],'expected_fp',lambda m:0),
      'cancel_wrong':change(lambda m:m['qualified'] and m['cancel'] and not m['reset'],'cancel',lambda m:0),
      'bootstrap_erased':change(lambda m:m['qualified'],'qualified',lambda m:0),
      'reset_mislabeled':change(lambda m:m['qualified'] and m['reset'] and not m['te'],'reset',lambda m:0),
      'actual_fire_wrong':change(lambda m:m['fp_fire']==1,'fp_fire',lambda m:0),
      'truncated':'\n'.join(lines[:-1])+'\n'}
    result=[]
    for name,bad in tests.items():
        try:check(bad,parent)
        except ValueError as e:result.append(dict(name=name,detected=True,reason=str(e),sha256=hashlib.sha256(bad.encode()).hexdigest()))
        else:raise ValueError('negative escaped '+name)
    return result
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--monitor',type=Path,required=True);ap.add_argument('--parent-log',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    need(not a.output.exists(),'output exists')
    m=a.monitor.read_text();p=a.parent_log.read_text();r=check(m,p)
    r['negative_controls']=negatives(m,p);r['monitor_sha256']=hashlib.sha256(m.encode()).hexdigest();r['parent_sha256']=hashlib.sha256(p.encode()).hexdigest()
    r['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
