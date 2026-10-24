#!/usr/bin/env python3
"""Independently replay O2 G2 cycle evidence; does not re-execute any RTL."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


class TraceError(ValueError):
    pass


def require(condition, detail):
    if not condition:
        raise TraceError(detail)


CYCLE_KEYS = set("""schema cycle p r case rob_flag rob pdest block_reason
pseq rseq divseq occupancy offered kind ready out_ready accept accept_seq p_to_r
response response_seq stall kill_p kill_r kill_div reset reset_drop redirect
redirect_flag redirect_rob self child_fire child_out child_ready busy clocks te
next_occupancy accepted_total responses_total cancels_total resets_total inflight""".split())
BOOL_KEYS = set("""p r rob_flag offered ready out_ready accept p_to_r response
stall kill_p kill_r kill_div reset redirect redirect_flag self busy te""".split())
PASS_KEYS = set("""schema cycles groups accepted responses cancelled reset_dropped
overlaps stalls p_to_r full_cycles full_blocked p_accept_r_blocked
r_response_p_survivor kill_p_only kill_r_only kill_both reset_both redirects
reset_cases te0_resets empty_te0_resets idle_clock_samples cancel_idle_clock_on
parent_tested fullcore_tested performance_measured""".split())
TRANSITION_CASES = {f"switch-{old}-{new}-{delay}" for old in range(3)
                    for new in range(3) for delay in (0, 1, 7)}
# Directed DIV redirects use absolute ROB positions 0..95.
DIV_RELATIONS = ((10, 10, False, False), (8, 10, False, False),
                 (12, 10, False, True), (47, 48, False, False),
                 (48, 47, False, True), (95, 0, False, False),
                 (0, 95, False, True))
DIV_ROB_CASES = {f"DIV-ROB-k{kind}-r{rel}-p{phase}"
                 for kind in (1, 2) for rel in range(len(DIV_RELATIONS))
                 for phase in range(2)}
FU_KEYS = set("""kind accepted responded killed reset_dropped raw_killed_response
latency_min latency_max latency_samples clock_edges waits""".split())


def fields(line, prefix, expected, string_keys=()):
    parts = line[len(prefix):].strip().split()
    result = {}
    for token in parts:
        require(token.count("=") == 1, "malformed field")
        key, value = token.split("=")
        require(key not in result, "duplicate field: " + key)
        if key not in string_keys:
            require(re.fullmatch(r"0|[1-9][0-9]*", value), "not an unsigned integer: " + key)
            value = int(value)
        result[key] = value
    require(set(result) == expected, "field schema mismatch: " + prefix)
    return result


def need_flush(req, row):
    if not row["redirect"]:
        return False
    distance = (48 * req["flag"] + req["rob"] -
                48 * row["redirect_flag"] - row["redirect_rob"]) % 96
    require(distance != 48, "ambiguous ROB age")
    return bool(row["self"]) if distance == 0 else distance < 48


def check_trace(text, require_campaign=True):
    """Replay independent slots/sequence/ROB age, then compare logged aggregates.

    Full VPU/data comparisons remain the live RTL scoreboard's responsibility:
    the cycle stream contains identities/control events, not 128-bit payloads.
    Child DIV readiness is an observed protocol boundary, not a latency model.
    """
    rows, groups, summaries = [], [], {}
    final = None
    phase = "cycles"
    for line in text.splitlines():
        if not line.strip():
            continue
        require(final is None, "content after final PASS")
        if line.startswith("O2_PARENT_CYCLE "):
            require(phase == "cycles", "cycle after summaries")
            rows.append(fields(line, "O2_PARENT_CYCLE", CYCLE_KEYS, ("case", "block_reason")))
        elif line.startswith("O2_PARENT_GROUP_PASS "):
            require(phase == "cycles", "group after summaries")
            groups.append(line[len("O2_PARENT_GROUP_PASS "):])
        elif line.startswith("O2_PARENT_FU "):
            phase = "summaries"
            summary = fields(line, "O2_PARENT_FU", FU_KEYS)
            require(summary["kind"] in (0, 1, 2) and summary["kind"] not in summaries,
                    "duplicate/unknown FU summary")
            summaries[summary["kind"]] = summary
        elif line.startswith("O2_PARENT_PASS "):
            final = fields(line, "O2_PARENT_PASS", PASS_KEYS)
        else:
            raise TraceError("unrecognized/error record: " + line[:100])
    require(rows and final is not None and set(summaries) == {0, 1, 2}, "incomplete evidence")
    require(len(set(groups)) == len(groups), "duplicate completed group")
    require(final["schema"] == 1 and final["parent_tested"] == 1 and
            final["fullcore_tested"] == 0 and final["performance_measured"] == 0,
            "invalid scope or schema")
    counts = Counter(cycles=len(rows), groups=len(groups))
    per_fu = [Counter(latency_min=9999) for _ in range(3)]
    live, ended = {}, set()
    p = r = div = 0
    previous_reset = False
    frozen_accept_cycles, frozen_response_latencies = [], []
    transition_cases = set()
    div_rob_cases, div_reset_overlap = set(), set()
    cancel_idle_window = None
    cancel_idle_samples = Counter()
    cancel_idle_cases = Counter()
    idle_clock_samples = 0

    def end(seq, category):
        require(seq in live and seq not in ended, "duplicate/missing terminal sequence")
        req = live.pop(seq)
        ended.add(seq)
        counts[category] += 1
        per_name = {"responses": "responded", "cancelled": "killed",
                    "reset_dropped": "reset_dropped"}[category]
        per_fu[req["kind"]][per_name] += 1

    for cycle, row in enumerate(rows):
        try:
            require(row["schema"] == 1 and row["cycle"] == cycle, "non-contiguous cycle/schema")
            require(all(row[k] in (0, 1) for k in BOOL_KEYS), "non-boolean field")
            require(row["kind"] in (0, 1, 2) and row["rob"] < 48 and row["redirect_rob"] < 48,
                    "bad FU/ROB")
            require(all(row[k] < 8 for k in ("child_ready", "child_out", "child_fire", "clocks")),
                    "bad child bit mask")
            old_p, old_r, old_div = p, r, div
            if cancel_idle_window is not None:
                kind, remaining, case = cancel_idle_window
                require(row["case"] == case and not (p or r or div or row["accept"] or
                        row["offered"] or row["reset"] or row["te"] or row["redirect"]),
                        "missing immediate post-cancel idle sample")
                pulse = bool(row["clocks"] & (1 << kind))
                counts["cancel_idle_clock_on"] += pulse
                cancel_idle_samples[kind] += 1
                require(not pulse, "canceled DIV retained clock on immediate idle sample")
                cancel_idle_window = ((kind, remaining - 1, case) if remaining > 1 else None)
            old_occ = bool(p) + bool(r)
            require((row["pseq"], row["rseq"], row["divseq"]) == (p, r, div), "slot sequence changed")
            require((row["p"], row["r"], row["occupancy"]) == (bool(p), bool(r), old_occ),
                    "slot occupancy mismatch")
            require(not (div and old_occ), "DIV overlaps vdot")
            reset, redirect, ready_out = row["reset"], row["redirect"], row["out_ready"]
            kp = bool(p and not reset and need_flush(live[p], row))
            kr = bool(r and not reset and need_flush(live[r], row))
            kd = bool(div and not reset and need_flush(live[div], row))
            require((row["kill_p"], row["kill_r"], row["kill_div"]) == (kp, kr, kd),
                    "ROB kill/priority mismatch")
            if row["case"].startswith("DIV-ROB-") and redirect:
                require(row["case"] in DIV_ROB_CASES and div and not reset,
                        "unknown or inactive directed DIV ROB case")
                match = re.fullmatch(r"DIV-ROB-k([12])-r([0-6])-p([01])", row["case"])
                kind, relation, _ = map(int, match.groups())
                req_at, flush_at, flush_self, expected_kill = DIV_RELATIONS[relation]
                require(live[div]["kind"] == kind and
                        live[div]["rob"] + 48 * live[div]["flag"] == req_at and
                        row["redirect_rob"] + 48 * row["redirect_flag"] == flush_at and
                        bool(row["self"]) == flush_self and kd == expected_kill,
                        "directed DIV ROB relation differs from contract")
                require(row["case"] not in div_rob_cases, "duplicate directed DIV ROB redirect")
                div_rob_cases.add(row["case"])
            if row["case"] == "DIV-legacy-reset" and reset and redirect:
                require(div and not kd and not row["kill_p"] and not row["kill_r"] and
                        row["te"] and row["self"] and
                        row["redirect_rob"] == live[div]["rob"] and
                        row["redirect_flag"] == live[div]["flag"],
                        "DIV reset/cancel overlap must reset exactly once with TE")
                div_reset_overlap.add(live[div]["kind"])
            if kd and row["case"].startswith(("DIV-cancel-", "DIV-ROB-")):
                require(cancel_idle_window is None, "overlapping cancel-idle windows")
                kind = live[div]["kind"]
                cancel_idle_cases[kind] += 1
                cancel_idle_window = (kind, 3, row["case"])
            live_p, live_r = bool(p and not kp and not reset), bool(r and not kr and not reset)
            move = live_p and (not live_r or ready_out)
            p_ready = not live_p or not live_r or ready_out
            require(bool(row["child_ready"] & 1) == (p_ready and not redirect and not reset),
                    "vdot ready differs from elastic state")
            div_unavailable = bool(div or (row["child_out"] & 6) or (row["child_ready"] & 6) != 6)
            expected_ready = bool(not reset and not redirect and not div_unavailable and
                                  (p_ready if row["kind"] == 0 else
                                   (not old_occ and row["child_ready"] & (1 << row["kind"]))))
            require(row["ready"] == expected_ready, "parent ready mismatch")
            if not reset:
                require(row["busy"] == bool(old_occ or div_unavailable), "parent busy mismatch")
            block = ("reset" if reset else "redirect" if redirect else "DIV" if div_unavailable
                     else "vdot-drain" if row["kind"] != 0 and old_occ else
                     "vdot-full" if row["kind"] == 0 and not p_ready else "none")
            require(row["block_reason"] == block, "block reason mismatch")
            accept = bool(row["offered"] and expected_ready)
            require(row["accept"] == accept and row["child_fire"] == ((1 << row["kind"]) if accept else 0),
                    "parent/child acceptance mismatch")
            output_mask = row["child_out"]
            require(output_mask & (output_mask - 1) == 0, "double FU output")
            if not reset:
                if old_occ:
                    require(output_mask == int(live_r), "vdot output qualification mismatch")
                elif div:
                    require(output_mask in (0, 1 << live[div]["kind"]), "wrong DIV output owner")
                    if live[div]["seen"] and not kd:
                        # A prior visible DIV result that was not consumed still
                        # owns the output. Only its kill/reset may withdraw valid.
                        require(output_mask == 1 << live[div]["kind"],
                                "stalled DIV valid withdrawn without kill/reset")
                else:
                    require(output_mask == 0, "ghost output after termination")
            response = bool(output_mask and ready_out and not reset and not kr and not kd)
            owner = r or div
            require(row["response"] == response and row["response_seq"] == (owner if response else 0),
                    "response sequence/priority mismatch")
            stall = bool(output_mask and not ready_out and not reset and not kr and not kd)
            require(row["stall"] == stall and row["p_to_r"] == move, "stall/transfer mismatch")
            if output_mask and not reset:
                require(owner in live, "output has no owner")
                req = live[owner]
                if not req["seen"]:
                    latency = cycle - req["cycle"]
                    require(latency >= (2 if req["kind"] == 0 else 1), "response too early")
                    pf = per_fu[req["kind"]]
                    pf["latency_min"] = min(pf["latency_min"], latency)
                    pf["latency_max"] = max(pf["latency_max"], latency)
                    pf["latency_samples"] += 1
                    req["seen"] = True
                    if row["case"] == "frozen-vdot-II1":
                        frozen_response_latencies.append(latency)
                if ready_out and kd:
                    per_fu[req["kind"]]["raw_killed_response"] += 1
            required_clocks = int(bool(old_occ)) | ((1 << live[div]["kind"]) if div else 0)
            if accept:
                required_clocks |= 1 << row["kind"]
            if reset:
                required_clocks |= 1
            require(row["clocks"] & required_clocks == required_clocks, "active/reset FU lost clock")
            if not (old_occ or old_div or accept or reset or row["te"]):
                require(row["clocks"] == 0, "idle FU retained clock after cancellation/completion")
            # These are the original explicitly counted startup/recovery samples.
            if ((row["case"] == "initial" and 2 <= cycle <= 5) or
                    (row["case"] == "clock-recovery" and
                     not (old_occ or old_div or row["offered"] or accept or reset or row["te"]))):
                require(row["clocks"] == 0, "counted idle sample has a clock")
                idle_clock_samples += 1
            for kind in range(3):
                per_fu[kind]["clock_edges"] += bool(row["clocks"] & (1 << kind))
            if row["offered"] and not accept and not reset and not redirect:
                per_fu[row["kind"]]["waits"] += 1
            counts["full_cycles"] += old_occ == 2
            counts["full_blocked"] += old_occ == 2 and not ready_out and not redirect and not reset
            counts["p_accept_r_blocked"] += accept and row["kind"] == 0 and bool(r) and not p and not ready_out
            counts["r_response_p_survivor"] += response and bool(p and r) and not accept and not kp and not reset
            counts["kill_p_only"] += kp and not kr
            counts["kill_r_only"] += kr and not kp
            counts["kill_both"] += kp and kr
            counts["reset_both"] += reset and old_occ == 2
            counts["overlaps"] += response and accept
            counts["stalls"] += stall
            counts["p_to_r"] += move
            counts["te0_resets"] += reset and not row["te"]
            counts["empty_te0_resets"] += reset and not row["te"] and not live
            counts["redirects"] += (redirect and not reset and
                (row["case"].startswith(("partial-ROB-", "DIV-cancel-", "DIV-ROB-")) or row["case"] == "single-slot-cancel"))
            counts["reset_cases"] += (reset and not previous_reset and
                (row["case"].startswith("TE0-reset-") or row["case"] == "DIV-legacy-reset"))
            previous_reset = bool(reset)
            if row["case"].startswith("switch-"):
                require(row["case"] in TRANSITION_CASES, "unknown FU transition case")
                transition_cases.add(row["case"])
            require(row["reset_drop"] == (len(live) if reset else 0), "reset drop count mismatch")
            if reset:
                for seq in list(live):
                    end(seq, "reset_dropped")
                p = r = div = 0
            else:
                for seq, kill in ((p, kp), (r, kr), (div, kd)):
                    if kill:
                        end(seq, "cancelled")
                if kp:
                    p = 0
                if kr:
                    r = 0
                if kd:
                    div = 0
                if response:
                    require(owner == min(live), "survivor responses reordered")
                    end(owner, "responses")
                    if owner == r:
                        r = 0
                    else:
                        div = 0
                if move:
                    require(p and not r, "bad transfer destination")
                    r, p = p, 0
                if accept:
                    seq = counts["accepted"] + 1
                    require(row["accept_seq"] == seq and seq not in live and seq not in ended,
                            "accept sequence reused/non-contiguous")
                    live[seq] = dict(kind=row["kind"], flag=row["rob_flag"], rob=row["rob"],
                                     pdest=row["pdest"], cycle=cycle, seen=False)
                    if row["kind"] == 0:
                        require(not p and not div, "accept into occupied product slot")
                        p = seq
                    else:
                        require(not p and not r and not div, "DIV accepted before drain")
                        div = seq
                    counts["accepted"] += 1
                    per_fu[row["kind"]]["accepted"] += 1
                    if row["case"] == "frozen-vdot-II1":
                        frozen_accept_cycles.append(cycle)
            if not accept:
                require(row["accept_seq"] == 0, "non-accept has a sequence")
            require(not (response and accept and row["kind"] != 0), "cross-FU handoff")
            require(set(filter(None, (p, r, div))) == set(live) and len(live) == bool(p) + bool(r) + bool(div),
                    "slot identities/liveness disagree")
            require(len(live) <= 2 and not (div and (p or r)), "capacity/exclusion violated")
            require(counts["accepted"] == counts["responses"] + counts["cancelled"] +
                    counts["reset_dropped"] + len(live), "prefix conservation failed")
            require(row["next_occupancy"] == bool(p) + bool(r) and row["inflight"] == len(live),
                    "next occupancy mismatch")
            for logged, name in (("accepted_total", "accepted"), ("responses_total", "responses"),
                                 ("cancels_total", "cancelled"), ("resets_total", "reset_dropped")):
                require(row[logged] == counts[name], "running counter mismatch: " + logged)
        except (TraceError, KeyError, ValueError) as exc:
            raise TraceError(f"cycle {cycle}: {exc}") from exc
    require(not live and not p and not r and not div, "unfinished transactions")
    require(cancel_idle_window is None, "truncated post-cancel idle window")
    require(final["cancel_idle_clock_on"] == counts["cancel_idle_clock_on"] == 0,
            "cancel-idle clock summary must match recomputed zero")
    require(final["idle_clock_samples"] == idle_clock_samples,
            "idle-clock sample summary mismatch")
    for name, value in counts.items():
        require(final[name] == value, "PASS summary mismatch: " + name)
    # Counter returns zero for absent keys; compare those too.
    for name in PASS_KEYS - {"schema", "idle_clock_samples",
                             "parent_tested", "fullcore_tested", "performance_measured"}:
        require(final[name] == counts[name], "PASS summary mismatch: " + name)
    for kind, summary in summaries.items():
        for name in FU_KEYS - {"kind"}:
            require(summary[name] == per_fu[kind][name], f"FU {kind} summary mismatch: {name}")
    if require_campaign:
        require(len(groups) == 13 and transition_cases == TRANSITION_CASES,
                "incomplete directed groups/transitions")
        require(len(frozen_accept_cycles) == len(frozen_response_latencies) == 10022 and
                all(b - a == 1 for a, b in zip(frozen_accept_cycles, frozen_accept_cycles[1:])) and
                set(frozen_response_latencies) == {2}, "frozen II=1/latency=2 evidence missing")
        for key in ("kill_p_only", "kill_r_only", "kill_both", "reset_both",
                    "p_accept_r_blocked", "full_blocked", "r_response_p_survivor",
                    "te0_resets", "empty_te0_resets"):
            require(counts[key] > 0, "missing contract corner: " + key)
        for pf in per_fu:
            require(all(pf[k] for k in ("accepted", "responded", "killed", "reset_dropped", "clock_edges")),
                    "missing per-FU terminal coverage")
        require(per_fu[0]["raw_killed_response"] == 0 and per_fu[1]["raw_killed_response"] > 0 and
                per_fu[2]["raw_killed_response"] > 0, "legacy DIV cancel-cycle observation missing")
        require(final["idle_clock_samples"] == 12, "idle-gating coverage missing")
        require(div_rob_cases == DIV_ROB_CASES and div_reset_overlap == {1, 2},
                "directed DIV ROB/reset-overlap coverage missing")
        require(cancel_idle_cases == {1: 24, 2: 24} and
                cancel_idle_samples == {1: 72, 2: 72},
                "missing 48 immediate DIV cancellation windows / 144 samples")
    return dict(status="O2_PARENT_OFFLINE_TRACE_PASS", cycles=len(rows), groups=len(groups),
                recomputed=dict(counts), per_fu=[dict(x) for x in per_fu],
                full_campaign_required=require_campaign,
                cancel_idle_cases=dict(cancel_idle_cases),
                cancel_idle_samples=dict(cancel_idle_samples),
                div_rob_cases=len(div_rob_cases),
                div_reset_overlap_kinds=sorted(div_reset_overlap),
                side_counters_not_recomputed=[],
                scope_note="strict idle gating; cancel edge remains required; legacy DIV reset uses TE",
                scope="cycle/identity/ROB/control replay only; no RTL execution or payload recheck")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    raw = args.log.read_bytes()
    result = check_trace(raw.decode("utf-8"))
    result["log_sha256"] = hashlib.sha256(raw).hexdigest()
    result["checker_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        require(not args.output.exists(), "refuse to overwrite prior replay evidence")
        args.output.write_text(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
