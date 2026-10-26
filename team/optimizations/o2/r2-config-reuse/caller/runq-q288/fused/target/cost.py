"""Offline Q288 cost diagnostics. No new EMU or qualification."""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
import copy
import hashlib
import gzip
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import struct
import sys
import time
import zipfile

sys.dont_write_bytecode = True
CONTRACT = "r2-s3-runq-q288-fused-cost-v1"
TARGET = "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/target"
CONTEXT = "team/optimizations/o2/r2-config-reuse/caller/hoisted/context_prefix.py"
CONTEXT_SHA = "e65e4a6056c9059af4a407445e3485256fbd976ad3778a7c24655cb08753015b"
ARCHIVE_PINS = {
    "payload.zip": "de3afffda86d1db7981d793d17f180b6af879582530d0979fe313bea00170b6c",
    "archive-manifest.json": "446a6cfb3e4f8ebc55ed2deb555bd46556a73c8c5912a5b5a8e3cfbee156c1c9",
    "original-audit.json": "92483cb201c667a80da2e806fbc658ae8994eaa81f78efb8bdd086efaed1a60c",
}
CUSTOM_MASK, CUSTOM_MATCH = 0xfe00707f, 0x0200000b
FIXED_ORDER = [2, 0, 1, 3, 4, 2, 2, 4, 3, 1, 0, 2]


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def file_digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def group_diagnostics(frontier, transactions, row, elf):
    """Positions in a proved path; retirement spans are not execution cost."""
    fused = row["variant"] == "fused"
    if fused:
        begin = elf.symbols[row["wrapper"]][0] + 60
        words = 140 if row["method"] == "vdot" else 87
    else:
        begin = elf.symbols[row["leaf"]][0]
        words = elf.symbols[row["leaf"]][1] // 4
    starts = [i for i, item in enumerate(frontier) if item["pc"] == begin]
    need(len(starts) == 324, "dynamic core/leaf group inventory")
    rows, deltas, cursor = [], defaultdict(list), 0
    for number, pos in enumerate(starts):
        block = frontier[pos:pos + words]
        need(len(block) == words and all(v["pc"] == begin + 4 * i for i, v in enumerate(block)),
             "contiguous actual integer core/leaf")
        dots = [v for v in block if v["word"] & CUSTOM_MASK == CUSTOM_MATCH]
        count = 32 if row["method"] == "vdot" else 0
        need(len(dots) == count, "group custom inventory")
        tx = transactions[cursor:cursor + count]
        cursor += count
        need([v["pc"] for v in dots] == [v["pc"] for v in tx], "group transaction PC order")
        item = dict(group=number, tile=number // 9, quant_group=number % 9,
                    entry_position=pos, last_position=pos + words - 1,
                    first_retire_tick=block[0]["tick"], last_retire_tick=block[-1]["tick"],
                    retirement_envelope=block[-1]["tick"] - block[0]["tick"])
        if fused:
            next_start = starts[number + 1] if number + 1 < len(starts) else len(frontier)
            tail = frontier[pos + words:next_start]
            convert = [v for v in tail if v["word"] & 127 == 0x57 and
                       (v["word"] >> 26, (v["word"] >> 12) & 7) == (0x12, 1)]
            add = [v for v in tail if v["word"] & 127 == 0x57 and
                   (v["word"] >> 26, (v["word"] >> 12) & 7) == (0, 1)]
            need(len(convert) == len(add) == 1, "one FP convert/accumulate per group")
            item.update(convert_retire_tick=convert[0]["tick"], fp_add_retire_tick=add[0]["tick"],
                        convert_position=convert[0]["position"], fp_add_position=add[0]["position"])
        if tx:
            item.update(first_enqueue=min(v["enqueue"] for v in tx), first_accept=min(v["accept"] for v in tx),
                        last_response=max(v["response"] for v in tx), last_commit=max(v["commit"] for v in tx),
                        accepted_in_program_order=all(a["accept"] < b["accept"] for a, b in zip(tx, tx[1:])))
            for i, (a, b) in enumerate(zip(tx, tx[1:]), 1):
                deltas[i].append(b["accept"] - a["accept"])
        rows.append(item)
    need(cursor == len(transactions), "all target transactions belong to dynamic groups")
    return dict(groups=rows, program_neighbor_accept_delta={str(k): stats(v) for k, v in deltas.items()},
                group_retirement_envelope=stats(v["retirement_envelope"] for v in rows),
                scope="dynamic position and retirement coordinates; no exclusive instruction-class cycle attribution")


def stats(values):
    values = sorted(values)
    if not values:
        return {"count": 0, "histogram": {}}
    percentile = lambda p: values[max(0, math.ceil(p * len(values)) - 1)]
    return dict(count=len(values), minimum=values[0], maximum=values[-1],
                mean=sum(values) / len(values), p50=percentile(.5), p90=percentile(.9),
                p99=percentile(.99), histogram={str(k): v for k, v in sorted(Counter(values).items())})


def merged_waits(transactions, start, stop):
    """Integer cycles strictly after enqueue and before accept; union, not sum."""
    changes = Counter()
    for row in transactions:
        a, b = max(start, row["enqueue"] + 1), min(stop, row["accept"])
        if a < b:
            changes[a] += 1
            changes[b] -= 1
    depth, result = 0, set()
    for cycle in range(start, stop):
        depth += changes[cycle]
        if depth:
            result.add(cycle)
    return result


def bind_transactions(records, index, expected):
    allocations, times, accepts, responses, commits = index
    result = []
    for row in records:
        if row["word"] & CUSTOM_MASK != CUSTOM_MATCH:
            continue
        need(row["count"] == 1, "custom must retire individually")
        rob = (row["flag"], row["rob"])
        commit = commits.get((row["cycle"], rob, row["pc"]))
        need(commit is not None, "T13/O2 commit mismatch")
        generation = bisect_left(times.get(rob, []), commit["cycle"]) - 1
        need(generation >= 0, "commit without preceding allocation")
        allocation = allocations[rob][generation]
        need(all(allocation[k] == commit[k] for k in ("rob", "pc", "ftq"))
             and allocation["word"] == row["word"], "commit allocation mismatch")
        accept = accepts.get((rob, generation))
        need(accept is not None, "committed instruction missing acceptance")
        identity = (accept["seq"], rob, accept["pdest"])
        response = responses.get(identity)
        need(response is not None and allocation["cycle"] <= accept["cycle"] < response["cycle"] < commit["cycle"],
             "committed response identity/order")
        result.append(dict(pc=row["pc"], word=row["word"], rob=list(rob), generation=generation,
                           seq=accept["seq"], pdest=accept["pdest"], ftq=allocation["ftq"],
                           enqueue=allocation["cycle"], accept=accept["cycle"],
                           response=response["cycle"], commit=commit["cycle"]))
    keys = {(row["seq"], tuple(row["rob"]), row["pdest"]) for row in result}
    need(len(result) == len(keys) == expected, "committed transaction inventory")
    return result


def trace_inputs(archive, entries, samples, observer):
    """Use frozen field grammar, gated by an exact previously qualified archive.

    Selection does not constitute a fresh whole-stream O2 state/UART audit.
    """
    starts = [row["sample_ticks"][1] for row in samples]
    stops = [row["sample_ticks"][2] for row in samples]
    inside = lambda t: (i := bisect_right(starts, t) - 1) >= 0 and t < stops[i]
    names = "|".join(sorted(observer.FIELDS, key=len, reverse=True))
    pattern = re.compile(r"O2_(" + names + r")[ \t]+([^\n]*)\n")
    global_kinds = {"ENQUEUE", "ACCEPT", "RESPONSE", "COMMIT"}
    local_kinds = {"STATE", "MOVE", "STALL", "VFEX4_WAIT", "VFEX4_REDIRECT", "KILL",
                   "DIV_ACCEPT", "DIV_KILL", "DIV_OUTPUT"}
    events, local, t13 = [], [[] for _ in samples], []
    counts, schema, raw_sha, raw_size = Counter(), None, hashlib.sha256(), 0
    name = "run/runs/recovery/stderr.log"
    with archive.open(name) as stream:
        for raw in stream:
            raw_sha.update(raw)
            raw_size += len(raw)
            line = raw.decode("utf-8")
            if line.startswith(("T13_COUNTER_ENQUEUE", "T13_CSR_SAMPLE", "T13_RETIRE")):
                t13.append(line)
            match = pattern.search(line)
            if match is None:
                continue
            kind, body = match.groups()
            counts[kind] += 1
            if kind == "SCHEMA":
                need(schema is None, "duplicate schema")
                schema = observer.parse_fields(kind, body, observer.FIELDS[kind])
                continue
            need(schema is not None and kind != "RESET", "missing schema or runtime reset")
            tick_match = re.match(r"cycle=\s*([0-9]+)", body)
            need(tick_match is not None, "missing event cycle")
            tick = int(tick_match.group(1))
            if not (kind in global_kinds or kind in local_kinds and inside(tick)):
                continue
            row = observer.parse_fields(kind, body, observer.FIELDS[kind], schema)
            event = (tick, len(events), kind, row)
            if kind in global_kinds:
                events.append(event)
            if inside(tick):
                local[bisect_right(starts, tick) - 1].append(event)
    pin = entries[name]
    need(raw_size == pin["raw_bytes"] and raw_sha.hexdigest() == pin["raw_sha256"], "recovery raw identity")
    fixed = dict(version=1, clock="global", latency=2, slots=2, rob_size=48, ftq_size=8, vlen=128,
                 vpu_width=195, perf_width=577)
    need(schema == fixed and counts["COMMIT"] == 103681, "fixed schema and complete custom inventory")
    need(all(a[0] <= b[0] for a, b in zip(events, events[1:])), "event clock order")
    replay = "run/runs/replay/stderr.log"
    replay_hash, replay_size = hashlib.sha256(), 0
    with archive.open(replay) as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            replay_hash.update(chunk)
            replay_size += len(chunk)
    need(replay_size == entries[replay]["raw_bytes"] == raw_size and
         replay_hash.hexdigest() == entries[replay]["raw_sha256"] == raw_sha.hexdigest(),
         "replay exact trace identity")
    return events, local, "".join(t13), dict(schema=schema, full_event_counts=dict(counts),
        stderr_bytes=raw_size, stderr_sha256=raw_sha.hexdigest(), replay_input_identical=True,
        replay_interpretation="same deterministic input bytes; no new target run or independent sample")


def active_state_coverage(transactions, states):
    for row in transactions:
        for cycle in range(row["accept"] + 1, row["response"] + 1):
            need(cycle in states, "missing active transaction state")
            state = states[cycle]
            wanted = (row["seq"], ":".join(map(str, row["rob"])), row["pdest"])
            occupied = [(state[p + "seq"], state[p + "rob"], state[p + "pdest"])
                        for p in ("p", "r") if state[p + "valid"]]
            need(wanted in occupied, "active transaction absent from P/R state")


def fu_statistics(transactions, events, start, stop, silent_proven=False):
    by = defaultdict(list)
    for _, _, kind, row in events:
        by[kind].append(row)
    states = {row["cycle"]: row for row in by["STATE"]}
    need(len(states) == len(by["STATE"]), "duplicate STATE cycle")
    need(all(start <= row["accept"] < row["response"] < row["commit"] < stop for row in transactions),
         "target transaction crosses cycle interval")
    active_state_coverage(transactions, states)
    identities = {(row["seq"], ":".join(map(str, row["rob"])), row["pdest"]) for row in transactions}
    key = lambda row: (row["seq"], row["rob"], row["pdest"])
    target_stalls = [row for row in by["STALL"] if key(row) in identities]
    target_moves = [row for row in by["MOVE"] if key(row) in identities]
    target_accepts = [row for row in by["ACCEPT"] if key(row) in identities]
    target_responses = [row for row in by["RESPONSE"] if key(row) in identities]
    need(len(target_moves) == len(target_accepts) == len(target_responses) == len(transactions),
         "target event inventory inside interval")
    moves = {key(row): row["cycle"] for row in target_moves}
    need(len(moves) == len(transactions), "unique target MOVE")
    for row in transactions:
        ident = (row["seq"], ":".join(map(str, row["rob"])), row["pdest"])
        need(row["accept"] < moves[ident] < row["response"], "registered P/R movement order")
    stalled_cycles = {row["cycle"] for row in by["STALL"]}
    need(stalled_cycles == {c for c, row in states.items() if row["outvalid"] and not row["outready"]},
         "STALL/state mismatch")
    pending = merged_waits(transactions, start, stop)
    flushes = {row["cycle"] for row in by["VFEX4_REDIRECT"]}
    observed_wait = {c for c in pending if c in states and states[c]["vready"] == 1
                     and states[c]["invalid"] == 0 and states[c]["divoccupied"] == 0 and c not in flushes}
    silent_wait = pending - states.keys()
    ordered = sorted(row["accept"] for row in transactions)
    need(len(ordered) == len(set(ordered)), "multiple target acceptance in one cycle")
    runs, length = [], 0
    for i, tick in enumerate(ordered):
        if i and tick != ordered[i - 1] + 1:
            runs.append(length)
            length = 0
        length += 1
    if length:
        runs.append(length)
    a, m, r = ({row["cycle"] for row in by[k]} for k in ("ACCEPT", "MOVE", "RESPONSE"))
    occupancy = Counter(row["occupancy"] for row in states.values())
    result = dict(
        measured_cycles=stop - start, target_transactions=len(transactions),
        enqueue_before_start=sum(row["enqueue"] < start for row in transactions), boundary_crossings=0,
        target_accepts_per_cycle=len(transactions) / (stop - start),
        enqueue_to_accept=stats(row["accept"] - row["enqueue"] for row in transactions),
        accept_to_response=stats(row["response"] - row["accept"] for row in transactions),
        response_to_commit=stats(row["commit"] - row["response"] for row in transactions),
        accepted_time_order_gap=stats(b - a for a, b in zip(ordered, ordered[1:])),
        consecutive_accept_run_lengths=stats(runs), target_output_stall_events=len(target_stalls),
        all_output_stall_cycles=len(stalled_cycles), parent_wait_events=len(by["VFEX4_WAIT"]),
        div_accepts=len(by["DIV_ACCEPT"]), other_accepts=len(by["ACCEPT"]) - len(transactions),
        all_kill_events=len(by["KILL"]), triple_overlap_cycles=len(a & m & r),
        observed_state_cycles=len(states), observed_occupancy={str(k): occupancy[k] for k in range(3)},
        unobserved_cycles=stop - start - len(states), silent_domain_proven=silent_proven,
        pending_target_union_cycles=len(pending), pending_and_ready_without_request_observed=len(observed_wait),
        pending_during_silence=len(silent_wait),
        pending_and_ready_without_request_proven=len(observed_wait),
        pending_in_source_bound_empty_domain=len(silent_wait) if silent_proven else 0,
        scope="VFEX4 VDot/DIV boundary only; response-to-commit is retirement delay, not writeback stall")
    if silent_proven:
        result["total_occupancy"] = {str(k): occupancy[k] + (result["unobserved_cycles"] if k == 0 else 0)
                                     for k in range(3)}
    if transactions:
        first, last = min(ordered), max(row["response"] for row in transactions)
        result["time_envelope"] = dict(before_first_accept=first - start,
            first_accept_to_last_response=last - first, after_last_response=stop - last,
            scope="additive wall-clock envelope; middle includes overlapping non-vdot work")
    return result


def negative_controls(context, counter):
    """Tiny explicit counterexamples; never mutate the original evidence."""
    events = []
    def add(kind, **row):
        events.append((row["cycle"], len(events), kind, row))
    add("ENQUEUE", cycle=1, rob="0:3", pc=0x1000, ftq="0:0", word=CUSTOM_MATCH)
    add("ACCEPT", cycle=2, rob="0:3", seq=7, pdest=9)
    add("RESPONSE", cycle=4, rob="0:3", seq=7, pdest=9)
    add("COMMIT", cycle=5, rob="0:3", pc=0x1000, ftq="0:0")
    add("ENQUEUE", cycle=5, rob="0:3", pc=0x1004, ftq="0:1", word=CUSTOM_MATCH)
    add("ACCEPT", cycle=5, rob="0:3", seq=12, pdest=10)
    add("RESPONSE", cycle=7, rob="0:3", seq=12, pdest=10)
    add("COMMIT", cycle=8, rob="0:3", pc=0x1004, ftq="0:1")
    retires = [dict(cycle=5, flag=0, rob=3, pc=0x1000, word=CUSTOM_MATCH, count=1),
               dict(cycle=8, flag=0, rob=3, pc=0x1004, word=CUSTOM_MATCH, count=1)]
    bound = bind_transactions(retires, context.transaction_index(events), 2)
    need([v["generation"] for v in bound] == [0, 1] and [v["seq"] for v in bound] == [7, 12],
         "same-cycle old/new positive control")
    results = [dict(name="same-cycle-old-commit-new-enqueue", outcome="PASS", generations=[0, 1])]
    def rejected(name, run, message):
        try:
            run()
        except ValueError as error:
            need(str(error) == message, "unexpected control rejection: " + str(error))
            results.append(dict(name=name, outcome="REJECTED_AS_EXPECTED", reason=str(error)))
        else:
            raise ValueError("negative control accepted: " + name)
    wrong = copy.deepcopy(events)
    wrong[2][3]["pdest"] = 10
    rejected("response-pdest", lambda: bind_transactions(retires, context.transaction_index(wrong), 2),
             "committed response identity/order")
    wrong_rob = copy.deepcopy(events)
    wrong_rob[2][3]["rob"] = "0:4"
    rejected("response-rob", lambda: bind_transactions(retires, context.transaction_index(wrong_rob), 2),
             "committed response identity/order")
    compressed = copy.deepcopy(retires)
    compressed[0]["count"] = 2
    rejected("compressed-custom", lambda: bind_transactions(compressed, context.transaction_index(events), 2),
             "custom must retire individually")
    rejected("missing-custom", lambda: bind_transactions(retires[:-1], context.transaction_index(events), 2),
             "committed transaction inventory")
    rejected("duplicate-response", lambda: context.transaction_index(events + [events[2]]),
             "duplicate response identity")
    wait = merged_waits([dict(enqueue=0, accept=5), dict(enqueue=2, accept=7)], 0, 8)
    need(wait == set(range(1, 7)) and len(wait) == 6, "overlap union not sum")
    results.append(dict(name="overlapping-wait-union", outcome="PASS", union=6, interval_sum=8))
    rejected("missing-active-state", lambda: active_state_coverage(bound[:1], {}),
             "missing active transaction state")
    # A complete miniature fence/counter path, with independently chosen ticks.
    fence = 0x0330000f
    words = [counter.START, fence, counter.COUNTERS[0], fence, counter.COUNTERS[1], fence,
             0x00108093, fence, counter.COUNTERS[2], fence, counter.COUNTERS[3], fence, counter.STOP]
    path = [(0x2000 + 4 * i, word) for i, word in enumerate(words)]
    values, ticks, positions = [1000, 2000, 2040, 1008], [25, 45, 85, 105], [2, 4, 8, 10]
    retired = [dict(cycle=10 * i + 10, slot=0, flag=0, rob=i, pc=pc, word=word, count=1, data=0)
               for i, (pc, word) in enumerate(path)]
    enq, csr = [], []
    for j, pos in enumerate(positions):
        retired[pos]["data"] = values[j]
        enq.append({k: retired[pos][k] for k in ("flag", "rob", "pc", "word")} | {"cycle": ticks[j] - 3})
        csr.append(dict(cycle=ticks[j], addr=counter.COUNTERS[j] >> 20, data=values[j], wen=0))
    fixture = dict(RETIRE=retired, COUNTER_ENQUEUE=enq, CSR_SAMPLE=csr)
    plan = dict(plan=[dict(index=0, phase="measured", repeat=0)], dataset=0,
                rows=[dict(id=0, scenario="control", method="rvv", n=1, dots=0)],
                custom_mask=CUSTOM_MASK, custom_match=CUSTOM_MATCH)
    counter.walk = lambda value: value
    measured = counter.trace_windows(fixture, plan, {0: path})
    need(measured[0]["cycles"] == 40 and measured[0]["instructions"] == 8, "miniature counter positive")
    results.append(dict(name="fenced-counter-positive", outcome="PASS", cycles=40, instructions=8))
    shifted = copy.deepcopy(fixture)
    shifted["CSR_SAMPLE"][2]["cycle"] += 1
    rejected("counter-tick-shift", lambda: counter.trace_windows(shifted, plan, {0: path}),
             "cycle CSR/global clock disagreement")
    shifted_value = copy.deepcopy(fixture)
    shifted_value["CSR_SAMPLE"][2]["data"] += 1
    shifted_value["RETIRE"][8]["data"] += 1
    rejected("counter-value-shift", lambda: counter.trace_windows(shifted_value, plan, {0: path}),
             "cycle CSR/global clock disagreement")
    return dict(status="Q288_COST_IDENTITY_CONTROLS_PASS", controls=results,
                synthetic_target_runs=0, original_evidence_modified=False)


def bind_hardware(repo, read, entries):
    """Read the sealed build pins; do not substitute current HEAD for build identity."""
    profile = json.loads(read("run/hardware-profile.json"))
    parent = json.loads(read("run/parent-identity.json"))
    runtime = json.loads(read("run/runtime-inputs.json"))
    pin_path = repo / ("team/optimizations/o2/repro/evidence/clean-reproduction-v1/"
                       "matrix-archive/files/hardware/hardware-inputs.json.gz")
    compressed = pin_path.read_bytes()
    need(digest(compressed) == "614c959f8bc71e11858a35c65b3f0e07eda358cdee5f8643463892e6c312773a",
         "archived hardware pins compressed identity")
    raw = gzip.decompress(compressed)
    raw_sha = digest(raw)
    need(raw_sha == "7c42a8130e71b39e8f5ca08d7d662a85ac58f677040c6293d38007b007ac0dcc"
         == profile["pins_sha256"], "hardware pins raw identity")
    pins = json.loads(raw)
    need(profile == parent["hardware_profile"] and
         pins["source_commit"] == profile["source_commit"] == "34bae6d4acceac939f958199dae53c14bc1f6183" and
         pins["emu_sha256"] == profile["emu_sha256"] ==
         "ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f", "profile/build/EMU identity")
    exu_path = "src/main/scala/xiangshan/backend/exu/ExeUnit.scala"
    exu_sha = "166f70c704cc2ec477d316bc5d3ffb40498118e6f8c1c498209fc4b706070f1e"
    need(pins["files"][exu_path] == exu_sha == file_digest(repo / exu_path), "actual build observer source pin")
    hpath = "/home/lizufan/riscv-lab/t17-clean-20261024-0854/build-01/hardware-inputs.json"
    emu = "/home/lizufan/riscv-lab/t17-clean-20261024-0854/clean-02/source/build/emu"
    need(runtime[hpath] == raw_sha and runtime[emu] == pins["emu_sha256"], "runtime build/EMU pins")
    for phase in ("recovery", "replay"):
        name = "run/runs/" + phase + "/"
        receipt = json.loads(read(name + "result.json"))
        need(receipt["process_started"] is True and receipt["exit_code"] == 0 and
             all(receipt["files"].get(k) == v for k, v in runtime.items()) and
             receipt["command"][0] == emu and
             receipt["raw_sha256"]["stderr.log"] == entries[name + "stderr.log"]["raw_sha256"],
             "run receipt hardware/trace binding")
    return dict(silence_semantics_bound=True, source_commit=pins["source_commit"],
        emu_sha256=pins["emu_sha256"], pins_raw_sha256=raw_sha, pins_stored_sha256=digest(compressed),
        observer_source_path=exu_path, observer_source_sha256=exu_sha,
        observation_flags={k: pins[k] for k in ("VDOT_O2_TRACE", "VDOT_T13_TRACE", "NUM_CORES")},
        scope="absence of STATE implies empty P/R, no DIV occupancy, no parent valid or flush; not outready or whole-core idle",
        original_build_and_run_provenance_reused=True, physical_external_inputs_revalidated=False)


def analyze(repo, output):
    started = time.time()
    archive_path = repo / TARGET / "evidence/target-v1/archive"
    for name, pin in ARCHIVE_PINS.items():
        need(file_digest(archive_path / name) == pin, "sealed archive identity: " + name)
    manifest = json.loads((archive_path / "archive-manifest.json").read_text())
    audit = json.loads((archive_path / "original-audit.json").read_text())
    need(audit["status"] == "FUSED_TARGET_RAW_EVIDENCE_AUDIT_PASS" and
         audit["original_emu_runs"] == 3 and audit["windows_per_normal_run"] == 12, "original qualification")
    entries = {row["path"]: row for row in manifest["files"]}
    need(len(entries) == len(manifest["files"]) == 163, "archive inventory")
    input_hashes = {}
    with zipfile.ZipFile(archive_path / "payload.zip") as archive:
        names = archive.namelist()
        need(len(names) == len(set(names)) and set(names) == set(entries), "ZIP inventory")
        for name in names:
            p = PurePosixPath(name)
            need(not p.is_absolute() and ".." not in p.parts and "\\" not in name and ":" not in name,
                 "unsafe ZIP name")
            info = archive.getinfo(name)
            need(not info.is_dir() and info.file_size == entries[name]["raw_bytes"] and
                 info.external_attr >> 16 == 0o100644, "ZIP member type/size")
        def read(name):
            raw = archive.read(name)
            need(len(raw) == entries[name]["raw_bytes"] and digest(raw) == entries[name]["raw_sha256"],
                 "selected archive member identity: " + name)
            input_hashes[name] = digest(raw)
            return raw
        build = json.loads(read("build/build.json"))
        plan = json.loads(read("build/source/manifest.json"))
        certificate = json.loads(read("build/elf-validation.json"))
        validation_bytes = read("run/runs/recovery/validation.json")
        validation = json.loads(validation_bytes)
        need(validation_bytes == read("run/runs/replay/validation.json"), "replay validation identity")
        need(validation["status"] == "FUSED_TARGET_DIFFTEST_AND_PLAN_PASS" and
             [row["index"] for row in plan["plan"]] == FIXED_ORDER and
             len(plan["rows"]) == 5 and len(validation["samples"]) == 12, "fixed plan")
        pins = build["software_files"]
        need(len(pins) == 98, "frozen source inventory")
        def check_sources():
            for name, sha in pins.items():
                need(file_digest(repo / name) == sha, "frozen source changed: " + name)
            need(file_digest(repo / CONTEXT) == CONTEXT_SHA, "context helper identity")
        check_sources()
        target = module("q288_cost_target", repo / TARGET / "run.py")
        context = module("q288_cost_context", repo / CONTEXT)
        counter = module("q288_cost_counter", repo / "team/workloads/unified-vdot/check.py")
        observer = module("q288_cost_observer", repo / "team/optimizations/o2/fullcore/analyze.py")
        controls = negative_controls(context, counter)
        save(output / "controls.json", controls)
        elf = target.g.ELF(read("build/vdot-perf.elf"))
        paths, details = target.paths_for_plan(elf, plan)
        need(details == certificate["paths"], "all actual ELF path certificates")
        hardware_identity = bind_hardware(repo, read, entries)
        events, local, t13, trace_identity = trace_inputs(archive, entries, validation["samples"], observer)
    counters = counter.parse_events(t13)
    counter.walk = lambda path: path
    samples = counter.trace_windows(counters, plan, paths)
    for actual, prior in zip(samples, validation["samples"]):
        need(all(prior.get(key) == value for key, value in actual.items()), "original CSR/sample equality")
    windows = context.window_records(counters)
    need(len(windows) == 12, "all retirement windows")
    index = context.transaction_index(events)
    commits = [row for _, _, kind, row in events if kind == "COMMIT"]
    expected = [elf.symbols["q_fault_probe"][0] + 5 * 4]
    phases = []
    for i, call in enumerate(plan["call_plan"]):
        pcs = [pc for pc, word in paths[call["arm"]] if word & CUSTOM_MASK == CUSTOM_MATCH]
        phases.append(dict(seq=i, **call, vdot_count=len(pcs), first_commit_index=len(expected)))
        expected.extend(pcs)
    need(phases == validation["custom_phases"] and [row["pc"] for row in commits] == expected and
         digest(b"".join(struct.pack("<Q", pc) for pc in expected)) == validation["all_stage_custom_pc_sha256"],
         "all-stage custom phases and PC identity")
    timed = [row for row in phases if row["stage"] == 2]
    results, group_results = [], []
    for i, (records, sample, step, phase) in enumerate(zip(windows, samples, plan["plan"], timed)):
        row = plan["rows"][step["index"]]
        start, stop = sample["sample_ticks"][1:3]
        tx = bind_transactions(records, index, row["dots"])
        original_slice = commits[phase["first_commit_index"]:phase["first_commit_index"] + phase["vdot_count"]]
        need([(v["commit"], v["pc"], v["rob"]) for v in tx] ==
             [(v["cycle"], v["pc"], list(map(int, v["rob"].split(":")))) for v in original_slice],
             "timed phase isolation")
        frontier = context.expanded_frontier(records, paths[row["id"]], start)
        fu = fu_statistics(tx, local[i], start, stop, hardware_identity["silence_semantics_bound"])
        groups = group_diagnostics(frontier, tx, row, elf)
        group_results.append(dict(seq=i, label=row["label"], sample_start=start, **groups))
        coordinates = json.dumps(tx, sort_keys=True, separators=(",", ":")).encode()
        results.append(dict(seq=i, label=row["label"], block=step["block"], role=step["role"],
            cycles=sample["cycles"], instructions=sample["instructions"], sample_ticks=sample["sample_ticks"],
            transactions_sha256=digest(coordinates), fu=fu,
            group_retirement_envelope=groups["group_retirement_envelope"]))
    check_sources()
    need(file_digest(repo / hardware_identity["observer_source_path"]) ==
         hardware_identity["observer_source_sha256"], "observer source unchanged after diagnostics")
    result = dict(status="Q288_COST_DIAGNOSTIC_PASS", contract=CONTRACT, windows=results,
        archive_pins=ARCHIVE_PINS, selected_input_sha256=input_hashes, trace_identity=trace_identity,
        source_files_checked=len(pins), context_helper_sha256=CONTEXT_SHA, frozen_sources_unchanged=True,
        hardware_observation_binding=hardware_identity,
        new_emu_runs=0, hardware_changed=False, stable_default_changed=False, new_performance_qualification=False,
        scope="fixed synthetic prepacked Q only; FU boundary observations and retirement coordinates",
        unavailable_causality=["load/cache source readiness", "vset dependency stall", "FP issue/completion",
                               "exclusive instruction-class cycles", "token/full-model/quality/ASIC"],
        diagnostics_seconds=time.time() - started)
    save(output / "groups.json", group_results)
    save(output / "result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo, output = args.repo.resolve(), args.output.resolve()
    need(not output.exists() and repo != output and repo not in output.parents, "fresh output outside checkout")
    output.mkdir(parents=True, exist_ok=False)
    if hasattr(os, "sched_setaffinity"):
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:1])
    save(output / "invocation.json", dict(argv=sys.argv, started_epoch=time.time(),
        analyzer_sha256=file_digest(Path(__file__)), cpu_affinity=sorted(os.sched_getaffinity(0))
        if hasattr(os, "sched_getaffinity") else None))
    try:
        result = analyze(repo, output)
    except Exception as error:
        save(output / "failure.json", dict(status="Q288_COST_REJECTED", exception=type(error).__name__,
                                           error=str(error), new_emu_runs=0))
        raise
    print(json.dumps(dict(status=result["status"], output=str(output),
        windows=[dict(seq=v["seq"], label=v["label"], cycles=v["cycles"],
                      stalls=v["fu"]["target_output_stall_events"],
                      latency=v["fu"]["accept_to_response"],
                      observed_upstream_wait=v["fu"]["pending_and_ready_without_request_observed"],
                      silent_wait=v["fu"]["pending_during_silence"]) for v in result["windows"]]), indent=2))


if __name__ == "__main__":
    main()
