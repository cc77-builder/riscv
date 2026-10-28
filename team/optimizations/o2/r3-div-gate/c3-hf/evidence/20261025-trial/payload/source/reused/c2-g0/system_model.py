"""Exhaustive control-quotient check for fixed O2 DIV gating, not RTL equivalence.

I/R/O collapses the concrete IDLE / nonterminal / output FSM states.
R can remain or finish on every active edge: no latency/fairness assumption.
ROB colors preserve equality and all possible deterministic flush decisions.
"""
from __future__ import annotations
import argparse
import itertools
import json
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path

IDLE, RUN, OUT = range(3)

@dataclass(frozen=True)
class State:
    busy: int = 0
    hold_i: int = 0
    hold_f: int = 0
    parent_rob: int = 0
    int_rob: int = 0
    fp_rob: int = 0
    integer: int = IDLE
    d0: int = IDLE
    s0: int = IDLE
    d1: int = IDLE
    s1: int = IDLE

@dataclass(frozen=True)
class Event:
    request: str
    rob: int
    output_ready: int
    flush: int  # -1 absent; 0..3 maps ROB colors 0/1 to kill false/true
    vdot_occupied: int
    te: int
    reset: int = 0

def need_flush(color, table):
    return table >= 0 and bool(table & (1 << color))

def observation(s):
    ri = s.integer == IDLE
    rf = all(x == IDLE for x in (s.d0, s.s0, s.d1, s.s1))
    oi = s.integer == OUT
    lane0 = s.d0 == OUT or s.s0 == OUT
    lane1 = s.d1 == OUT or s.s1 == OUT
    return ri, rf, oi, lane0 and lane1

def errors(s):
    ri, rf, oi, of = observation(s)
    out = []
    if not s.busy and not (ri and rf):
        out.append("idle_implies_all_ready")
    if s.hold_i + s.hold_f != s.busy:
        out.append("hold_busy_correspondence")
    if not s.hold_i and not ri:
        out.append("integer_inactive_idle")
    if not s.hold_f and not rf:
        out.append("fp_inactive_idle")
    if s.hold_i and s.parent_rob != s.int_rob:
        out.append("integer_rob_binding")
    if s.hold_f and s.parent_rob != s.fp_rob:
        out.append("fp_rob_binding")
    if oi and of:
        out.append("output_onehot")
    if (s.d0 != IDLE and s.s0 != IDLE) or (s.d1 != IDLE and s.s1 != IDLE):
        out.append("lane_div_sqrt_exclusion")
    if (s.d0 != IDLE or s.d1 != IDLE) and (s.s0 != IDLE or s.s1 != IDLE):
        out.append("lanes_same_operation")
    return out

def unit_next(state, start, consume, cancel, clock_edge, reset, asynchronous):
    if reset and asynchronous:
        return (IDLE,)
    if not clock_edge:
        return (state,)
    if reset or cancel:
        return (IDLE,)
    if state == IDLE:
        return (RUN,) if start else (IDLE,)
    if state == RUN:
        return (RUN, OUT)
    return (IDLE,) if consume else (OUT,)

def successors(s, e, reset_policy="async", mutation=None):
    ri, rf, oi, of = observation(s)
    if mutation == "fp_join_or":
        of = any(x == OUT for x in (s.d0, s.s0, s.d1, s.s1))
    occupied = bool(s.busy or oi or of or not (ri and rf))
    div_request = e.request in ("integer", "fpdiv", "fpsqrt")
    allowed = not occupied and not e.vdot_occupied and e.flush < 0 and not e.reset
    ai = bool(e.request == "integer" and allowed and ri)
    af = bool(e.request in ("fpdiv", "fpsqrt") and allowed and rf)
    # The proposed restricted launch removes ready/occupied's ready term ONLY.
    prelaunch = bool(div_request and not s.busy and not oi and not of
                     and not e.vdot_occupied and e.flush < 0 and not e.reset)
    fire_i, fire_f = bool(oi and e.output_ready), bool(of and e.output_ready)
    kill = bool(s.busy and need_flush(s.parent_rob, e.flush))
    ci = bool(ai or s.hold_i or e.te)
    cf = bool(af or s.hold_f or e.te)
    if mutation == "cancel_edge_removed" and kill:
        ci = cf = bool(e.te)
    # A not-ready wrapper selects the saved accepted ROB; an idle wrapper
    # selects the current input. This is derived from the fixed wrapper code.
    ki = need_flush(e.rob if ri else s.int_rob, e.flush)
    kf = need_flush(e.rob if rf else s.fp_rob, e.flush)
    if mutation == "fp_cancel_not_delivered":
        kf = False
    asynchronous = reset_policy == "async"
    if reset_policy == "sync-qualified" and e.reset and not e.te:
        return []  # Explicit fixture environment, separately falsified below.
    next_busy = 0 if e.reset or kill or fire_i or fire_f else (1 if ai or af else s.busy)
    hi = 0 if e.reset else int(ai or (s.hold_i and not (fire_i or kill)))
    hf = 0 if e.reset else int(af or (s.hold_f and not (fire_f or kill)))
    pr = e.rob if ai or af else s.parent_rob
    ir = e.rob if ai else s.int_rob
    fr = e.rob if af else s.fp_rob
    if mutation == "fp_rob_wrong" and af:
        fr = 1 - e.rob
    options = [
        unit_next(s.integer, ai, fire_i, ki, ci, e.reset, asynchronous),
        unit_next(s.d0, af and e.request == "fpdiv", fire_f, kf, cf, e.reset, asynchronous),
        unit_next(s.s0, af and e.request == "fpsqrt", fire_f, kf, cf, e.reset, asynchronous),
        unit_next(s.d1, af and e.request == "fpdiv", fire_f, kf, cf,
                  e.reset and mutation != "lane1_reset_missing", asynchronous),
        unit_next(s.s1, af and e.request == "fpsqrt", fire_f, kf, cf,
                  e.reset and mutation != "lane1_reset_missing", asynchronous),
    ]
    detail = dict(accept_i=ai, accept_f=af, parent_cancel=kill,
                  child_cancel_i=ki, child_cancel_f=kf,
                  clock_i=ci, clock_f=cf, out_fire_i=fire_i, out_fire_f=fire_f,
                  prelaunch=prelaunch, prelaunch_equals_fire=(prelaunch == (ai or af)))
    return [(State(next_busy, hi, hf, pr, ir, fr, *states), detail)
            for states in itertools.product(*options)]

def events():
    for values in itertools.product(
        ("none", "vdot", "integer", "fpdiv", "fpsqrt"),
        range(2), range(2), (-1, 0, 1, 2, 3), range(2), range(2)
    ):
        yield Event(*values)
    # Requests are forbidden under reset; arbitrary redirect/outReady/VDot
    # do not change the reset transition. Keep redirect overlap coverage.
    for rob, ready, flush, vdot, te in itertools.product(
        range(2), range(2), (-1, 0, 1, 2, 3), range(2), range(2)
    ):
        yield Event("none", rob, ready, flush, vdot, te, 1)

def witness(previous, state):
    steps = []
    while previous[state] is not None:
        parent, prior_event = previous[state]
        steps.append(dict(state=asdict(parent),event=asdict(prior_event),next_state=asdict(state)))
        state = parent
    steps.reverse()
    return steps

def prove(reset_policy="async", mutation=None, monitor_only_target=False):
    # ROB data registers need not reset. All color histories are initial seeds;
    # no equality is assumed until the accepted transaction binds them.
    seeds = [State(parent_rob=p, int_rob=i, fp_rob=f)
             for p, i, f in itertools.product(range(2), repeat=3)]
    previous = {s: None for s in seeds}
    todo = deque(seeds)
    ev = tuple(events())
    transitions = 0
    coverage = set()
    targets = set()
    while todo:
        s = todo.popleft()
        for e in ev:
            for ns, d in successors(s, e, reset_policy, mutation):
                transitions += 1
                err = errors(ns)
                if monitor_only_target:
                    err = [x for x in err if x == "idle_implies_all_ready"]
                if not d["prelaunch_equals_fire"]:
                    err.append("restricted_launch_changed")
                if err:
                    chain = witness(previous, s)
                    chain.append(dict(state=asdict(s), event=asdict(e),
                                      next_state=asdict(ns), detail=d, violation=err))
                    return dict(passed=False,transitions=transitions,
                                reached=len(previous),counterexample=chain)
                if d["accept_i"]: coverage.add("accept_integer")
                if d["accept_f"]: coverage.add("accept_"+e.request)
                if d["parent_cancel"]:
                    coverage.add("matching_cancel")
                    if fire := (d["out_fire_i"] or d["out_fire_f"]):
                        coverage.add("cancel_and_complete")
                    if e.reset: coverage.add("cancel_and_reset")
                if e.flush >= 0 and s.busy and not d["parent_cancel"]:
                    coverage.add("unrelated_redirect")
                if (s.d0 == OUT) != (s.d1 == OUT): coverage.add("fpdiv_lane_skew")
                if (s.s0 == OUT) != (s.s1 == OUT): coverage.add("fpsqrt_lane_skew")
                if (observation(s)[2] or observation(s)[3]) and not e.output_ready:
                    coverage.add("output_backpressure")
                if e.reset and s.busy:
                    coverage.add("reset_while_busy")
                if e.reset and not e.te:
                    coverage.add("reset_te0")
                if s.busy and e.vdot_occupied:
                    coverage.add("overapproximated_vdot_overlap")
                if ns not in previous:
                    previous[ns]=(s,e)
                    todo.append(ns)
        targets.add((s.integer,s.d0,s.s0,s.d1,s.s1))
    return dict(passed=True,states=len(previous),transitions=transitions,
                coverage=sorted(coverage),control_patterns=sorted(targets),
                initial_rob_seeds=len(seeds),
                invariant_method="Reachability fixpoint; every successor checked, no depth bound or fairness.",
                quotient="I/R/O per DIV/SQRT engine; RUN has arbitrary finite/infinite duration.")

def reset_establishes():
    count = 0
    e = Event("none",0,0,-1,0,0,1)
    for b, hi, hf in itertools.product(range(2),repeat=3):
        for engines in itertools.product(range(3),repeat=5):
            s=State(b,hi,hf,0,1,0,*engines)
            ns,_=successors(s,e,"async")[0]
            assert not errors(ns), (s,ns)
            count += 1
    # No-bootstrap and synchronous TE=0 reset are explicitly outside PASS.
    no_boot = State(integer=RUN)
    bad_sync, _ = successors(no_boot,e,"sync-unqualified")[0]
    assert "idle_implies_all_ready" in errors(bad_sync)
    return dict(arbitrary_control_initializations=count,async_reset_establishes=True,
                uninitialized_example=asdict(no_boot),sync_te0_after_reset=asdict(bad_sync),
                sync_te0_status="COUNTEREXAMPLE_WITHOUT_VALID_BOOTSTRAP",
                note="Arbitrary one-hot legal controller states modeled; async resets also override illegal concrete encodings per source.")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    assert not a.output.exists()
    production=prove("async")
    fixture=prove("sync-qualified")
    warm_reset=prove("sync-valid-bootstrap")
    assert production["passed"] and fixture["passed"] and warm_reset["passed"]
    negatives={m:prove("async",m,monitor_only_target=True)
               for m in ("cancel_edge_removed","fp_cancel_not_delivered",
                         "fp_rob_wrong","fp_join_or","lane1_reset_missing")}
    assert all(not x["passed"] for x in negatives.values())
    result=dict(status="C2_G0_CONTROL_QUOTIENT_PASS",production_async=production,
                fixture_sync_te1_reset=fixture,sync_warm_reset_te_unrestricted=warm_reset,
                reset_establishment=reset_establishes(),
                negative_controls=negatives,
                scope="Control abstraction only; source binding and detailed FSM checks are separate. No RTL formal equivalence, arithmetic test, new PPA or fullcore qualification.")
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("negative_controls",)},indent=2))
    print("NEGATIVE_CONTROLS_REJECTED",list(negatives))
if __name__=="__main__":main()
