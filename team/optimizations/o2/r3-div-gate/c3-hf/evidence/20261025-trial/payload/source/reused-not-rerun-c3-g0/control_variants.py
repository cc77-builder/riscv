"""C3-G0 source-bound control quotient: hypothetical FP hold launch variants.
No RTL edit, RTL equivalence, numerical simulation, synthesis, STA, or EMU.
Reference semantics imported only from immutable reviewed C2-G0 control model.
"""
import argparse
import hashlib
import importlib.util
import itertools
import json
import sys
from collections import deque
from dataclasses import asdict
from pathlib import Path

MAIN=Path('/home/riscv/riscv-lab/zjhwork2-review-20261018/repo')
G0=MAIN/'team/optimizations/o2/r3-div-gate/c2-g0/system_model.py'
EXPECTED_G0='8ae8349a08ff5e234215ebc68607f58784492d17b53dea9dfb01657db9968018'
EXPECTED_EXE='fd98aaced17c39dabd4776a53948f05650c8956178f6540bf5695d15753d60fa'
assert hashlib.sha256(G0.read_bytes()).hexdigest()==EXPECTED_G0
assert hashlib.sha256((MAIN/'src/main/scala/xiangshan/backend/exu/ExeUnit.scala').read_bytes()).hexdigest()==EXPECTED_EXE
spec=importlib.util.spec_from_file_location('g0',G0)
g0=importlib.util.module_from_spec(spec)
sys.modules['g0']=g0
spec.loader.exec_module(g0)

def events():
    # Include asserted valid with reset; RTL masks it rather than assuming it absent.
    for values in itertools.product(('none','vdot','integer','fpdiv','fpsqrt'),
                                    range(2),range(2),(-1,0,1,2,3),range(2),range(2),range(2)):
        yield g0.Event(*values)

def candidate(s,e,mode,mutation=None,reset_policy='async'):
    ri,rf,oi,of=g0.observation(s)
    occupied=bool(s.busy or oi or of or not (ri and rf))
    allowed=not occupied and not e.vdot_occupied and e.flush<0 and not e.reset
    ai=bool(e.request=='integer' and allowed and ri)
    af=bool(e.request in ('fpdiv','fpsqrt') and allowed and rf)
    p=bool(e.request in ('fpdiv','fpsqrt') and not s.busy and not oi and not of
           and not e.vdot_occupied and e.flush<0 and not e.reset)
    if mutation=='omit_flush':
        p=bool(e.request in ('fpdiv','fpsqrt') and not s.busy and not oi and not of
               and not e.vdot_occupied and not e.reset)
    if mutation=='omit_vdot':
        p=bool(e.request in ('fpdiv','fpsqrt') and not s.busy and not oi and not of
               and e.flush<0 and not e.reset)
    if mutation=='omit_busy':
        p=bool(e.request in ('fpdiv','fpsqrt') and not oi and not of
               and not e.vdot_occupied and e.flush<0 and not e.reset)
    if mutation=='omit_reset':
        p=bool(e.request in ('fpdiv','fpsqrt') and not s.busy and not oi and not of
               and not e.vdot_occupied and e.flush<0)
    if mutation=='omit_sqrt' and e.request=='fpsqrt':
        p=False
    fi,ff=bool(oi and e.output_ready),bool(of and e.output_ready)
    kill=bool(s.busy and g0.need_flush(s.parent_rob,e.flush))
    ci=bool(ai or s.hold_i or e.te)
    cf=bool((p if mode=='gate-plus-hold' else af) or s.hold_f or e.te)
    if mutation=='kill_masks_clock' and kill:
        cf=bool(e.te)
    ki=g0.need_flush(e.rob if ri else s.int_rob,e.flush)
    kf=g0.need_flush(e.rob if rf else s.fp_rob,e.flush)
    busy=0 if e.reset or kill or fi or ff else (1 if ai or af else s.busy)
    hi=0 if e.reset else int(ai or (s.hold_i and not(fi or kill)))
    hf=0 if e.reset else int(p or (s.hold_f and not(ff or kill)))
    async_reset=reset_policy=='async'
    ns0=[busy,hi,hf,e.rob if ai or af else s.parent_rob,e.rob if ai else s.int_rob,e.rob if af else s.fp_rob]
    options=[
        g0.unit_next(s.integer,ai,fi,ki,ci,e.reset,async_reset),
        g0.unit_next(s.d0,af and e.request=='fpdiv',ff,kf,cf,e.reset,async_reset),
        g0.unit_next(s.s0,af and e.request=='fpsqrt',ff,kf,cf,e.reset,async_reset),
        g0.unit_next(s.d1,af and e.request=='fpdiv',ff,kf,cf,e.reset,async_reset),
        g0.unit_next(s.s1,af and e.request=='fpsqrt',ff,kf,cf,e.reset,async_reset)]
    detail=dict(P_F=p,fire_F=af,clock_i=ci,clock_f=cf,hold_F_next=hf)
    return {g0.State(*ns0,*ns) for ns in itertools.product(*options)},detail

def check(mode,reset_policy,mutation=None):
    seeds=[g0.State(parent_rob=p,int_rob=i,fp_rob=f) for p,i,f in itertools.product(range(2),repeat=3)]
    seen={s:None for s in seeds}; queue=deque(seeds)
    event_count=transitions=0
    coverage=set()
    for s in seeds: assert not g0.errors(s)
    while queue:
        s=queue.popleft()
        for e in events():
            refs=g0.successors(s,e,reset_policy)
            expected={ns for ns,_ in refs}
            actual,detail=candidate(s,e,mode,mutation,reset_policy)
            event_count+=1;transitions+=len(expected)
            gates=refs[0][1]
            violation=[]
            if detail['P_F']!=detail['fire_F']: violation.append('P_F_equals_actual_fire_F')
            if detail['clock_i']!=gates['clock_i'] or detail['clock_f']!=gates['clock_f']:
                violation.append('exact_clock_edge_equivalence')
            if actual!=expected: violation.append('all_next_states_equal')
            if violation:
                return dict(status='REJECT',mode=mode,reset_policy=reset_policy,mutation=mutation,
                            reached=len(seen),events=event_count,transitions=transitions,
                            violation=violation,witness=g0.witness(seen,s)+[dict(state=asdict(s),event=asdict(e),detail=detail,
                            reference_next=[asdict(x) for x in expected],candidate_next=[asdict(x) for x in actual])])
            if e.reset and e.request!='none': coverage.add('valid_during_reset')
            if e.reset and not e.te and s.busy: coverage.add('TE0_active_reset')
            if gates['parent_cancel']: coverage.add('matching_cancel')
            if gates['parent_cancel'] and (gates['out_fire_i'] or gates['out_fire_f']):coverage.add('cancel_completion_overlap')
            if gates['parent_cancel'] and e.reset:coverage.add('cancel_reset_overlap')
            if e.flush>=0 and s.busy and not gates['parent_cancel']:coverage.add('unrelated_redirect')
            if e.request=='fpsqrt' and detail['fire_F']:coverage.add('SQRT_accept')
            if e.request=='fpdiv' and detail['fire_F']:coverage.add('FP_DIV_accept')
            if gates['accept_i']:coverage.add('INT_accept')
            if s.d0!=s.d1:coverage.add('DIV_lane_skew')
            if s.s0!=s.s1:coverage.add('SQRT_lane_skew')
            if (g0.observation(s)[2] or g0.observation(s)[3]) and not e.output_ready:coverage.add('response_backpressure')
            if e.vdot_occupied and e.request in ('fpdiv','fpsqrt'):coverage.add('VDot_blocks_FP')
            for ns in expected:
                assert not g0.errors(ns)
                if ns not in seen:
                    seen[ns]=(s,e);queue.append(ns)
    return dict(status='PASS',mode=mode,reset_policy=reset_policy,states=len(seen),
                events=event_count,transitions=transitions,initial_rob_seeds=len(seeds),coverage=sorted(coverage))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists()
    positives=[check(mode,policy) for mode in ('hold-only','gate-plus-hold') for policy in ('async','sync-valid-bootstrap')]
    assert all(x['status']=='PASS' for x in positives)
    negatives=[check('hold-only','async',m) for m in ('omit_flush','omit_vdot','omit_busy','omit_reset','omit_sqrt','kill_masks_clock')]
    assert all(x['status']=='REJECT' for x in negatives)
    # No valid reset: B=0 with a not-ready integer blocks actual FP acceptance.
    invalid=g0.State(integer=g0.RUN)
    event=g0.Event('fpdiv',0,0,-1,0,0)
    ns,d=candidate(invalid,event,'hold-only')
    assert d['P_F'] and not d['fire_F']
    result=dict(status='C3_G0_CONTROL_VARIANTS_PASS',source_binding=dict(G0=str(G0),G0_sha256=EXPECTED_G0,ExeUnit_sha256=EXPECTED_EXE),
        scope='Read-only abstract control review; hypothetical variants only. No RTL edit/formal-equivalence/simulation/PPA/fullcore qualification.',
        positives=positives,negative_controls=negatives,
        outside_contract_counterexample=dict(state=asdict(invalid),event=asdict(event),detail=d,
            reason='Uninitialized synchronous child with TE=0 is outside qualified bootstrap; P_F != actual fire.'))
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],positives=positives,
        negative_controls=[dict(mutation=x['mutation'],violation=x['violation'],witness_length=len(x['witness'])) for x in negatives]),indent=2))
if __name__=='__main__':main()
