"""Strict observation-negative checks and offline O2 real-parent event replay.

Fault injections change C++ observed values only; they are not RTL mutations.
Positive replay does not rerun hardware or establish full-core/PPA results.
"""
import argparse
from pathlib import Path
import sys

FAULT_CATEGORIES = {
    "identity": "identity", "rob": "identity", "high": "high",
    "metadata": "identity", "wen": "wen", "stall": "stability",
    "route": "route", "double": "route", "clock": "clock",
    "occupancy": "occupancy", "kill_p": "cancel", "kill_r": "cancel",
    "survivor": "cancel", "duplicate": "ghost", "missing": "response",
    "reset": "reset",
    "perf_input": "perf_input", "perf_swap": "identity",
    "perf_parent": "perf_parent", "perf_cross": "perf_parent",
}
FAULTS = tuple(FAULT_CATEGORIES)


def check_negative(fault: str, return_code: int, log: str) -> None:
    if fault not in FAULT_CATEGORIES:
        raise ValueError("unknown injection")
    if return_code != 1:
        raise ValueError(f"expected detection exit 1, got {return_code}")
    expected = [f"O2_PARENT_INJECT {fault}", f"O2_PARENT_FAIL {FAULT_CATEGORIES[fault]}"]
    lines = [line for line in log.splitlines() if line.strip()]
    if lines != expected:
        raise ValueError("require exactly matching injection and expected rejection category")


def _fields(line: str) -> dict[str, str]:
    pairs = [word.split("=", 1) for word in line.split()[1:]]
    if any(len(pair) != 2 or not all(pair) for pair in pairs):
        raise ValueError("malformed event field")
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("duplicate event field")
    return result


def check_positive(log: str) -> dict:
    """Recompute exact two-slot transitions and per-seq conservation from events."""
    # Keep one strict clock/ROB replay contract for both positive entry points.
    # The legacy transaction replay below remains an independent cross-check.
    from check_trace import check_trace
    strict = check_trace(log)
    live = {}
    ended = set()
    p = r = div = 0
    accepted = response = cancel = reset_drop = 0
    cycle = groups = 0
    summary = None
    per_fu = {}
    frozen_accept = []
    frozen_responses = 0
    last_case = None
    for line in log.splitlines():
        if not line.strip():
            continue
        if summary is not None:
            raise ValueError("data after terminal PASS")
        if line.startswith("O2_PARENT_GROUP_PASS "):
            groups += 1
            continue
        if line.startswith("O2_PARENT_FU "):
            values = _fields(line)
            kind = int(values["kind"])
            if kind in per_fu or kind not in (0, 1, 2):
                raise ValueError("duplicate or unknown FU summary")
            per_fu[kind] = values
            continue
        if line.startswith("O2_PARENT_PASS "):
            summary = _fields(line)
            continue
        if not line.startswith("O2_PARENT_CYCLE "):
            raise ValueError("unexpected line, failure or truncated diagnostics")
        f = _fields(line)
        def n(key):
            return int(f[key])
        def require(ok, reason):
            if not ok:
                raise ValueError(f"cycle={cycle}: {reason}")
        for key in ("p", "r", "offered", "ready", "out_ready", "accept", "p_to_r",
                    "response", "stall", "kill_p", "kill_r", "kill_div", "reset",
                    "redirect", "redirect_flag", "self", "te", "rob_flag"):
            require(n(key) in (0, 1), f"non-boolean {key}")
        require(n("schema") == 1 and n("cycle") == cycle, "schema/cycle discontinuity")
        require((n("pseq"), n("rseq"), n("divseq")) == (p, r, div), "pre-edge slots changed")
        require((n("p"), n("r")) == (bool(p), bool(r)), "slot validity/seq mismatch")
        require(n("occupancy") == bool(p) + bool(r), "pre-edge occupancy mismatch")
        require(0 <= n("kind") <= 2 and 0 <= n("rob") < 48, "invalid request identity")
        require(not div or not (p or r), "DIV and vdot in flight together")
        old_occ = bool(p) + bool(r)
        old_live = set(live)
        def killed(seq):
            if not seq or not n("redirect") or n("reset"):
                return False
            req = live[seq]
            distance = (req["rob"] - (48*n("redirect_flag") + n("redirect_rob"))) % 96
            require(distance != 48, "ambiguous ROB window")
            return bool(n("self")) if distance == 0 else distance < 48
        kp, kr, kd = killed(p), killed(r), killed(div)
        require((n("kill_p"), n("kill_r"), n("kill_div")) == (kp, kr, kd), "ROB kill set mismatch")
        inf = bool(n("offered") and n("ready") and not n("reset"))
        require(n("accept") == inf and (not n("redirect") or not inf), "accept/redirect/reset mismatch")
        require(n("child_fire") == ((1 << n("kind")) if inf else 0), "parent/child handshake mismatch")
        child_out = n("child_out")
        require(child_out in (0, 1, 2, 4), "multi-FU output")
        if not n("reset"):
            if child_out:
                require(bool(r or div) and child_out == (1 << (0 if r else live[div]["kind"])), "ghost/wrong output owner")
            if p or r:
                require(bool(child_out) == bool(r and not kr), "vdot response visibility")
        out = bool(child_out and n("out_ready") and not n("reset") and not kr and not kd)
        require(n("response") == out, "response termination mismatch")
        require(n("response_seq") == ((r or div) if out else 0), "response seq mismatch")
        require(n("stall") == bool(child_out and not n("out_ready") and not n("reset") and not kr and not kd), "stall qualification")
        move = bool(p and not kp and not n("reset") and (not r or kr or n("out_ready")))
        require(n("p_to_r") == move, "P-to-R transfer mismatch")
        def terminate(seq):
            require(seq in live and seq not in ended, "duplicate/unknown terminal")
            ended.add(seq)
            del live[seq]
        if n("reset"):
            require(not out and not inf and not move, "reset priority")
            require(n("reset_drop") == len(old_live), "reset drop count")
            for seq in old_live:
                terminate(seq)
            reset_drop += len(old_live)
            p = r = div = 0
        else:
            require(n("reset_drop") == 0, "non-reset drop")
            if kp:
                terminate(p); p = 0; cancel += 1
            if kr:
                terminate(r); r = 0; cancel += 1
            if kd:
                terminate(div); div = 0; cancel += 1
            if out:
                seq = r or div
                require(seq == min(live), "surviving response reordered")
                if live[seq]["case"] == "frozen-vdot-II1":
                    require(cycle-live[seq]["cycle"] == 2, "frozen response latency !=2")
                    frozen_responses += 1
                terminate(seq); response += 1
                if r: r = 0
                else: div = 0
            if move:
                require(p and not r, "transfer into occupied result")
                r, p = p, 0
            if inf:
                seq = n("accept_seq")
                require(seq == accepted+1 and seq not in live and seq not in ended, "accept seq uniqueness")
                live[seq] = {"rob": n("rob")+48*n("rob_flag"), "kind": n("kind"),
                             "cycle": cycle, "case": f["case"]}
                if n("kind") == 0:
                    require(not p and not div, "accept into occupied product or DIV")
                    p = seq
                else:
                    require(not p and not r and not div, "DIV before pipeline drained")
                    div = seq
                accepted += 1
                if f["case"] == "frozen-vdot-II1":
                    frozen_accept.append(cycle)
            else:
                require(n("accept_seq") == 0, "non-accept seq")
        require(n("next_occupancy") == bool(p)+bool(r), "post-edge occupancy mismatch")
        require(set(live) == {seq for seq in (p, r, div) if seq}, "slot/live-set mismatch")
        require((n("accepted_total"), n("responses_total"), n("cancels_total"), n("resets_total")) ==
                (accepted, response, cancel, reset_drop), "cumulative totals disagree")
        require(n("inflight") == len(live) and accepted == response+cancel+reset_drop+len(live),
                "prefix conservation mismatch")
        require((n("clocks") & 1) or not (old_occ or (inf and n("kind") == 0) or n("reset")),
                "O2 clock absent with work/reset")
        last_case = f["case"]
        cycle += 1
    if summary is None or live:
        raise ValueError("missing complete PASS or requests remain live")
    for key, expected in (("schema", 1), ("cycles", cycle), ("groups", groups),
                          ("accepted", accepted), ("responses", response),
                          ("cancelled", cancel), ("reset_dropped", reset_drop),
                          ("parent_tested", 1), ("fullcore_tested", 0), ("performance_measured", 0)):
        if int(summary[key]) != expected:
            raise ValueError(f"final summary mismatch: {key}")
    perf_v2 = summary.get("perf_contract") == "2"
    if "perf_contract" in summary and not perf_v2:
        raise ValueError("unknown perf contract")
    if perf_v2:
        for key, value in (("perf_bits", 577), ("perf_inputs", accepted),
                           ("perf_walk_one", 577), ("perf_walk_zero", 577)):
            if int(summary[key]) != value:
                raise ValueError(f"incomplete perf v2 summary: {key}")
        if int(summary["perf_observations"]) < response:
            raise ValueError("missing parent perf observations")
    if set(per_fu) != {0, 1, 2} or groups != (14 if perf_v2 else 13) or last_case != "clock-recovery":
        raise ValueError("incomplete directed campaign")
    if len(frozen_accept) != 10022 or frozen_responses != 10022:
        raise ValueError("frozen arithmetic sample count mismatch")
    if any(b-a != 1 for a, b in zip(frozen_accept, frozen_accept[1:])):
        raise ValueError("frozen acceptance interval !=1")
    return {"status": "O2_PARENT_OFFLINE_REPLAY_PASS", "cycles": cycle, "accepted": accepted,
            "responses": response, "cancelled": cancel, "reset_dropped": reset_drop,
            "frozen_vectors": 10022, "ii1_intervals": 10021, "fullcore_tested": False,
            "strict_clock_replay": strict["status"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fault", choices=FAULTS)
    parser.add_argument("--return-code", type=int)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--positive", action="store_true")
    args = parser.parse_args()
    try:
        log = args.log.read_text(encoding="utf-8")
        if args.positive:
            if args.fault is not None or args.return_code != 0:
                raise ValueError("positive replay requires return-code 0 and no fault")
            import json
            print(json.dumps(check_positive(log), sort_keys=True))
        else:
            check_negative(args.fault, args.return_code, log)
            print(f"O2_PARENT_NEGATIVE_CHECK_PASS {args.fault}")
    except (ValueError, KeyError, TypeError, OSError, UnicodeError) as exc:
        print(f"O2_PARENT_CHECK_FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
