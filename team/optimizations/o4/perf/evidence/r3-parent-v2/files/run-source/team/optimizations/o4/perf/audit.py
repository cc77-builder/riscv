#!/usr/bin/env python3
"""Replay complete R3 perf payloads against the independently checked G2 control trace.
No RTL/EMU execution, no arithmetic revalidation, no PPA or whole-core qualification.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re

BITS = 577
MASK = (1 << BITS) - 1
FIELDS_LSB = ("tlbRespTime", "tlbFirstReqTime", "runahead_checkpoint_id",
              "writebackTime", "issueTime", "selectTime", "enqRsTime",
              "dispatchTime", "renameTime", "eliminatedMove")
ROOT = Path(__file__).resolve().parents[4]

def require(ok, why):
    if not ok:
        raise ValueError(why)

def fields(line, keys):
    tokens = line.split()
    pairs = [x.split("=", 1) for x in tokens[1:]]
    require(all(len(x) == 2 and x[0] and x[1] for x in pairs), "malformed metadata field")
    result = dict(pairs)
    require(len(result) == len(pairs) and set(result) == set(keys.split()),
            "duplicate/unknown/missing metadata field")
    return result

def payload(text):
    require(re.fullmatch(r"[0-9a-f]{152}", text) is not None, "noncanonical perf hex")
    value = int(text, 16)
    require(value <= MASK, "nonzero padding above bit 576")
    return value

def replay(control, metadata):
    spec = importlib.util.spec_from_file_location("r3_control",
        ROOT/"team/optimizations/o2/parent/check_trace.py")
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    control_result = gate.check_trace(control)
    cycles = [gate.fields(x, "O2_PARENT_CYCLE", gate.CYCLE_KEYS, ("case", "block_reason"))
              for x in control.splitlines() if x.startswith("O2_PARENT_CYCLE ")]
    summary = gate.fields(next(x for x in control.splitlines() if x.startswith("O2_PARENT_PASS ")),
                          "O2_PARENT_PASS", gate.PASS_KEYS | gate.PERF_PASS_KEYS)
    require(summary.get("perf_contract") == 2, "R3 requires explicit perf v2 source identity")
    lines = metadata.splitlines()
    require(len(lines) > 2 and lines[0] == "R3_PERF schema=1 bits=577", "missing metadata header")
    require(lines[-1].startswith("END "), "missing metadata terminal")
    end = fields(lines[-1], "cycles accepts observations one zero")
    events = {}
    schemas = {"A": "cycle seq kind walk zero expected child",
               "O": "cycle seq child parent", "E": "cycle seq reason"}
    for line in lines[1:-1]:
        event = line.split(" ", 1)[0]
        require(event in schemas, "unknown metadata event")
        f = fields(line, schemas[event])
        key = (int(f["cycle"]), event, int(f["seq"]))
        require(0 <= key[0] < len(cycles) and key[2] > 0, "invalid cycle/seq")
        require(key not in events, "duplicate metadata event")
        events[key] = f
    used, live = set(), {}
    counts, per_fu = Counter(), Counter()
    walking = {"one": set(), "zero": set()}
    walking_done = {"one": set(), "zero": set()}
    ones = zeroes = 0
    distinct_fields = 0
    def event(cycle, kind, seq):
        key = (cycle, kind, seq)
        require(key in events and key not in used, f"missing/duplicate {key}")
        used.add(key)
        return events[key]
    for index, c in enumerate(cycles):
        n = lambda key: int(c[key])
        p, r, div = n("pseq"), n("rseq"), n("divseq")
        require(set(live) == {x for x in (p, r, div) if x}, "metadata/control live sets disagree")
        if n("child_out") and not n("reset") and not n("kill_r"):
            seq = r or div
            require(seq in live, "unknown observed response")
            o = event(index, "O", seq)
            expected = live[seq]["payload"]
            require(payload(o["child"]) == expected, "child response metadata mismatch")
            require(payload(o["parent"]) == expected, "actual parent output metadata mismatch")
            counts["observations"] += 1
        ended = []
        if n("reset"):
            ended = [(x, 2) for x in (p, r, div) if x]
        else:
            ended += [(p, 1)] if n("kill_p") else []
            ended += [(r, 1)] if n("kill_r") else []
            ended += [(div, 1)] if n("kill_div") else []
            ended += [(n("response_seq"), 0)] if n("response") else []
        for seq, reason in ended:
            e = event(index, "E", seq)
            require(seq in live and int(e["reason"]) == reason, "terminal metadata/control mismatch")
            item = live.pop(seq)
            counts[("responded", "cancelled", "reset")[reason]] += 1
            if item["walk"] >= 0:
                require(reason == 0, "walking transaction did not respond")
                walking_done[item["pattern"]].add(item["walk"])
        if n("accept"):
            seq = n("accept_seq")
            a = event(index, "A", seq)
            value = payload(a["expected"])
            require(payload(a["child"]) == value, "external input/child input mismatch")
            require(int(a["kind"]) == n("kind"), "accepted FU identity mismatch")
            bit, zero = int(a["walk"]), int(a["zero"])
            require(-1 <= bit < BITS and zero in (0, 1), "invalid walking tag")
            pattern = "zero" if zero else "one"
            if bit >= 0:
                require(n("kind") == 0 and c["case"] == "perf-walking", "misplaced walking transaction")
                require(value == (MASK ^ (1 << bit) if zero else 1 << bit), "wrong walking payload")
                require(bit not in walking[pattern], "duplicate walking bit")
                walking[pattern].add(bit)
            else:
                require(not zero, "nonwalking zero tag")
                values = [(value >> (64 * j)) & ((1 << 64) - 1) for j in range(9)]
                require(len(set(values)) == 9, "ordinary stimulus has aliased 64-bit fields")
                distinct_fields += 1
            live[seq] = {"payload": value, "walk": bit, "pattern": pattern}
            counts["accepts"] += 1
            per_fu[n("kind")] += 1
            ones |= value
            zeroes |= MASK ^ value
    require(not live and used == set(events), "pending or unmatched metadata events")
    for name in ("one", "zero"):
        require(walking[name] == set(range(BITS)) == walking_done[name], "incomplete delivered bit sweep")
    require(ones == MASK and zeroes == MASK, "not all metadata bits exercised at 0 and 1")
    require(set(per_fu) == {0, 1, 2} and distinct_fields > 0, "missing FU/independent field coverage")
    for key, value in (("cycles", len(cycles)), ("accepts", counts["accepts"]),
                       ("observations", counts["observations"]), ("one", BITS), ("zero", BITS)):
        require(int(end[key]) == value, "metadata end count mismatch")
    for key, value in (("perf_inputs", counts["accepts"]),
                       ("perf_observations", counts["observations"]),
                       ("perf_walk_one", BITS), ("perf_walk_zero", BITS)):
        require(int(summary[key]) == value, "metadata/control summary mismatch")
    require(counts["accepts"] == counts["responded"] + counts["cancelled"] + counts["reset"],
            "payload transaction conservation")
    return {"status": "R3_PERF_PAYLOAD_REPLAY_PASS", "contract": "r3-perf-parent-v2",
            "bits": BITS, "fields_lsb_first": list(FIELDS_LSB), "cycles": len(cycles),
            "payload_events": len(events), "counts": dict(counts),
            "per_fu_accepts": dict(per_fu), "independent_field_requests": distinct_fields,
            "walking_one_bits": BITS, "walking_zero_bits": BITS,
            "input_bits_at_both_values": BITS, "actual_parent_output_checked": True,
            "control_replay": control_result, "new_fullcore": False, "new_ppa": False}

def negative_checks(control, metadata):
    """Corrupt real retained evidence; the unchanged verifier must reject each case."""
    rows = metadata.splitlines()
    first_a = next(i for i, x in enumerate(rows) if x.startswith("A "))
    first_o = next(i for i, x in enumerate(rows) if x.startswith("O "))
    first_walk = next(i for i, x in enumerate(rows) if x.startswith("A ") and " walk=0 " in x)
    cases = {}
    def altered(index, old, new):
        copy = rows.copy()
        require(old in copy[index], "negative fixture not found")
        copy[index] = copy[index].replace(old, new, 1)
        return "\n".join(copy) + "\n"
    o = fields(rows[first_o], "cycle seq child parent")
    cases["parent_bit_576"] = altered(first_o, "parent="+o["parent"],
        "parent="+f'{payload(o["parent"]) ^ (1 << 576):0152x}')
    v = payload(o["child"])
    word = (1 << 64) - 1
    swapped = (v & ~((1 << 128) - 1)) | ((v & word) << 64) | ((v >> 64) & word)
    cases["child_field_swap"] = altered(first_o, "child="+o["child"], "child="+f"{swapped:0152x}")
    a = fields(rows[first_a], "cycle seq kind walk zero expected child")
    cases["input_route_bit_448"] = altered(first_a, "child="+a["child"],
        "child="+f'{payload(a["child"]) ^ (1 << 448):0152x}')
    cases["missing_parent_observation"] = "\n".join(rows[:first_o]+rows[first_o+1:])+"\n"
    cases["duplicate_parent_observation"] = "\n".join(rows[:first_o]+[rows[first_o]]+rows[first_o:])+"\n"
    cases["wrong_response_seq"] = altered(first_o, "seq="+o["seq"]+" ", "seq=99999999 ")
    cases["wrong_walking_tag"] = altered(first_walk, "walk=0 ", "walk=1 ")
    cases["missing_terminal"] = "\n".join(rows[:-1])+"\n"
    results = {}
    for name, corrupt in cases.items():
        try:
            replay(control, corrupt)
        except (ValueError, KeyError, TypeError, StopIteration) as error:
            results[name] = {"detected": True, "error": str(error)}
        else:
            raise ValueError("evidence mutation escaped: "+name)
    return results

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--negative-checks", action="store_true")
    args = parser.parse_args()
    require(not args.output.exists(), "output must not exist")
    control, metadata = args.control.read_text(), args.metadata.read_text()
    result = replay(control, metadata)
    result["inputs"] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in (args.control, args.metadata)}
    if args.negative_checks:
        result["evidence_mutations"] = negative_checks(control, metadata)
    with args.output.open("x") as out:
        json.dump(result, out, indent=2, sort_keys=True)
        out.write("\n")
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
