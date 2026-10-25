"""Offline retirement-frontier diagnostics for the sealed hoisted screen.

The original HOLD decision is immutable. This observes retirement coordinates,
not scalar execution latency, and never launches a compiler, simulator or Git.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import struct
import tempfile
import types
import zipfile

INDEX_SHA256 = "38c2b5b1613a849272cbe1d5e1e9dd9db2596eef4660a7881a92a56137505173"
LABELS = ("b4", "h0", "h1", "h2", "h3", "h4")
HELPERS = {
    "counter": ("team/workloads/unified-vdot/check.py", "084bebc22e2f4665e5c7a7797e5cd2a6c73220719b4cf228ce3075ae2446bc66"),
    "path": ("team/optimizations/o2/r2-config-reuse/caller/pathcheck.py", "87e11075f1d84946277cf4d24914944ec9793cfffcc2bfab5a2cc8592c44f1b8"),
    "observer": ("team/optimizations/o2/fullcore/analyze.py", "27d9fe451c035157848625e84c2a229ac1d83073eb56ba3ebc25131e5569d496"),
}
START, STOP = 0x51300013, 0x51400013
CUSTOM_MASK, CUSTOM_MATCH = 0xfe00707f, 0x0200000b
LEAF = "config_reuse_gemv_8x32_reuse_vdot"
RVV_ALIAS = "config_reuse_gemv_8x32_reuse_rvv"
REDIRECT_SCOPE = ("same complete ROB pointer within a fully observed retirement window, paired parent redirect, "
                  "and no intervening retirement or flushing redirect; origin liveness relies on the pinned RTL "
                  "redirect/ROB semantics, not a directly logged scalar allocation generation")


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def safe_name(name):
    path = PurePosixPath(name)
    need(str(path) == name and name not in ("", ".") and not path.is_absolute()
         and ".." not in path.parts and "\\" not in name and ":" not in name, "unsafe evidence member")
    return path


def unlinked(path):
    path = path.absolute()
    need(".." not in path.parts, "parent traversal in evidence path")
    for candidate in (path, *path.parents):
        need(not candidate.is_symlink(), "linked evidence path")
    return path


def regular(root, name):
    path = unlinked(root)
    for part in safe_name(name).parts:
        path = path / part
        need(not path.is_symlink(), "linked evidence member")
    need(path.is_file(), "missing regular evidence file: " + name)
    return path


def verified(raw, size, sha, name):
    need(len(raw) == size and digest(raw) == sha, "evidence bytes changed: " + name)
    return raw


def load_case(evidence, item):
    """Verify every archive member; retain only the bounded diagnostic inputs."""
    directory = unlinked(evidence / safe_name(item["path"]))
    need(directory.is_dir(), "missing campaign directory")
    raw = {}
    for name, pin in item["files"].items():
        raw[name] = verified(regular(directory, name).read_bytes(), pin["bytes"], pin["sha256"], name)
    manifest = json.loads(raw["archive-manifest.json"])
    need(manifest["format"] == "caller-evidence-zip-v1", "archive format")
    need(manifest["payload_sha256"] == digest(raw["payload.zip"]), "archive payload binding")
    audit = json.loads(raw["original-audit.json"])
    need(audit["status"] == "CALLER_RAW_EVIDENCE_AUDIT_PASS" and audit["windows_per_normal_run"] == 36
         and audit["replay_windows"] == 36 and audit["original_emu_runs"] == 3, "prior qualification scope")
    entries = {row["path"]: row for row in manifest["files"]}
    need(len(entries) == len(manifest["files"]), "duplicate archive manifest member")
    selected = {"build/build.json", "build/vdot-perf.elf", "build/vdot-perf.bin", "build/source/manifest.json",
                "build/source/caller.c", "build/source/main.c", "build/elf-validation.json"}
    selected |= {"build/source/repo/" + path for path, _ in HELPERS.values()}
    selected |= {"run/runs/" + phase + "/" + name for phase in ("recovery", "replay")
                 for name in ("stderr.log", "stdout.log", "validation.json", "result.json")}
    data, total = {}, 0
    # ZipFile accepts an in-memory stream; no archive-supplied path is executed.
    import io
    with zipfile.ZipFile(io.BytesIO(raw["payload.zip"])) as archive:
        names = archive.namelist()
        need(len(names) == len(set(names)) and set(names) == set(entries), "archive member inventory")
        for name in names:
            safe_name(name)
            info, pin = archive.getinfo(name), entries[name]
            need(not info.is_dir() and (info.external_attr >> 16) == 0o100644, "archive file kind")
            blob = verified(archive.read(name), pin["raw_bytes"], pin["raw_sha256"], name)
            total += len(blob)
            if name in selected:
                data[name] = blob
    need(set(data) == selected and total == manifest["raw_bytes"], "archive selected inputs/size")
    build = json.loads(data["build/build.json"])
    need(build["accepted"] is True and build["exit_code"] == 0, "build not accepted")
    for name in ("vdot-perf.elf", "vdot-perf.bin"):
        need(digest(data["build/" + name]) == build["artifacts"][name], "build artifact binding")
    need(build["artifacts"]["vdot-perf.bin"] == audit["image_sha256"], "prior audit image binding")
    modules = {}
    for key, (path, pin) in HELPERS.items():
        code = data["build/source/repo/" + path]
        need(digest(code) == pin == build["software_files"][path], "frozen helper identity: " + key)
        module = types.ModuleType("context_" + key)
        module.__file__ = "<qualified-archive>/" + path
        exec(compile(code, module.__file__, "exec"), module.__dict__)
        modules[key] = module
    identity = dict(label=item["label"], archive_sha256=digest(raw["payload.zip"]),
                    archive_manifest_sha256=digest(raw["archive-manifest.json"]),
                    prior_audit_sha256=digest(raw["original-audit.json"]), verified_members=len(entries),
                    verified_raw_bytes=total, image_sha256=audit["image_sha256"],
                    input_sha256={name: digest(value) for name, value in sorted(data.items())})
    return data, modules, identity


class ElfView:
    """The frozen counter helper supplies ELF parsing; only its view is adapted."""
    def __init__(self, symbols, read, rvv=None):
        self.original_symbols, self.read, self.rvv = symbols, read, rvv
        self.symbols = dict(symbols)
        if rvv is not None:
            self.symbols[RVV_ALIAS] = symbols[rvv]

    def symbol_data(self, name):
        target = self.rvv if name == RVV_ALIAS and self.rvv is not None else name
        return self.read(*self.original_symbols[target][:2])


def compiled_paths(data, modules, elf_path, label):
    manifest = json.loads(data["build/source/manifest.json"])
    need(manifest["contract"] == "r2-s3-caller-screen-v2-" + label, "manifest contract")
    need(manifest["custom_mask"] == CUSTOM_MASK and manifest["custom_match"] == CUSTOM_MATCH,
         "custom instruction identity")
    wanted = [dict(index=order ^ (repeat & 1), stage=0, dataset=dataset, repeat=repeat,
                   phase="first" if repeat == 0 else "warmup" if repeat == 1 else "measured")
              for dataset in range(3) for repeat in range(6) for order in range(2)]
    need(manifest["plan"] == wanted and len(manifest["rows"]) == 2, "full screen plan")
    symbols, read = modules["counter"].elf_data(elf_path)
    paths = {}
    for row in manifest["rows"]:
        view = ElfView(symbols, read, row.get("leaf") if row["method"] == "rvv" else None)
        checked = [modules["path"].path(view, 0, row["method"], bytes(value)) for value in manifest["inputs"]]
        need(checked[0] == checked[1] == checked[2], "data-dependent compiled path")
        paths[row["id"]] = checked[0][0]
    report = json.loads(data["build/elf-validation.json"])
    for key, path in paths.items():
        pin = digest(b"".join(struct.pack("<QI", pc, word) for pc, word in path))
        need(pin == report["paths"][str(key)]["path_sha256"], "original compiled path identity")
    return manifest, paths, symbols


def window_records(events):
    previous, windows, active, cycle_robs = None, [], None, set()
    for row in events["RETIRE"]:
        coordinate = (row["cycle"], row["slot"])
        need(0 <= row["slot"] < 8 and (previous is None or coordinate > previous),
             "retirement slot order/duplicate")
        if previous is None or row["cycle"] != previous[0]:
            cycle_robs.clear()
        identity = (row["flag"], row["rob"])
        need(identity not in cycle_robs, "duplicate same-cycle retirement ROB")
        cycle_robs.add(identity)
        previous = coordinate
        if row["word"] == START:
            need(active is None, "nested retirement marker")
            active = []
        if active is not None:
            active.append(row)
        if row["word"] == STOP:
            need(active is not None, "unbound retirement stop")
            windows.append(active)
            active = None
    need(active is None, "incomplete retirement window")
    return windows


def expanded_frontier(records, path, start):
    """Expand architectural positions, retaining each original observation group."""
    rows, position, occurrences = [], 0, Counter()
    for group, event in enumerate(records):
        count = event["count"]
        covered = path[position:position + count]
        need(1 <= count <= 8 and len(covered) == count and
             (event["pc"], event["word"]) == covered[0], "retirement path/coverage")
        if count > 1:
            need(all(pc == covered[0][0] + 4 * offset for offset, (pc, _) in enumerate(covered)),
                 "noncontiguous retirement group")
            need(all(word not in (START, STOP) and word & 127 not in (0x63, 0x6f, 0x67, 0x73)
                     and word & CUSTOM_MASK != CUSTOM_MATCH for _, word in covered),
                 "control/custom hidden in retirement group")
        for offset, (pc, word) in enumerate(covered):
            occurrence = occurrences[pc]
            occurrences[pc] += 1
            rows.append(dict(position=position + offset, pc=pc, word=word, occurrence=occurrence,
                             tick=event["cycle"] - start, group=group, group_offset=offset,
                             group_count=count, slot=event["slot"], rob=[event["flag"], event["rob"]]))
        position += count
    need(position == len(path), "retirement path incomplete")
    return rows


def transaction_index(events):
    allocations, accepts, responses, commits = defaultdict(list), {}, {}, {}
    pointer = lambda event: tuple(map(int, event["rob"].split(":")))
    identity = lambda event: (event["seq"], pointer(event), event["pdest"])
    for _, _, kind, event in events:
        if kind == "ENQUEUE":
            allocations[pointer(event)].append(event)
        elif kind == "RESPONSE":
            key = identity(event)
            need(key not in responses, "duplicate response identity")
            responses[key] = event
        elif kind == "COMMIT":
            key = (event["cycle"], pointer(event), event["pc"])
            need(key not in commits, "duplicate commit identity")
            commits[key] = event
    times = {rob: [event["cycle"] for event in rows] for rob, rows in allocations.items()}
    need(all(values == sorted(set(values)) for values in times.values()), "ambiguous allocation generation")
    for _, _, kind, event in events:
        if kind != "ACCEPT":
            continue
        rob = pointer(event)
        generation = bisect_right(times.get(rob, []), event["cycle"]) - 1
        key = (rob, generation)
        need(generation >= 0 and key not in accepts, "accept allocation identity")
        accepts[key] = event
    return allocations, times, accepts, responses, commits


def committed_transactions(records, index, start):
    allocations, times, accepts, responses, commits = index
    result = []
    for event in records:
        if event["word"] & CUSTOM_MASK != CUSTOM_MATCH:
            continue
        need(event["count"] == 1, "custom must retire individually")
        rob = (event["flag"], event["rob"])
        commit = commits.get((event["cycle"], rob, event["pc"]))
        need(commit is not None, "T13/O2 commit mismatch")
        # Commit is processed before same-cycle allocation in the frozen auditor.
        generation = bisect_left(times.get(rob, []), commit["cycle"]) - 1
        need(generation >= 0, "commit without preceding allocation")
        allocation = allocations[rob][generation]
        need(all(allocation[key] == commit[key] for key in ("rob", "pc", "ftq")), "commit allocation mismatch")
        accept = accepts.get((rob, generation))
        need(accept is not None, "committed instruction missing acceptance")
        identity = (accept["seq"], rob, accept["pdest"])
        response = responses.get(identity)
        need(response is not None and allocation["cycle"] <= accept["cycle"] < response["cycle"] <= commit["cycle"],
             "committed response identity/order")
        result.append(dict(pc=event["pc"], rob=list(rob), generation=generation, seq=accept["seq"],
                           pdest=accept["pdest"], ftq=allocation["ftq"],
                           enqueue=allocation["cycle"] - start, accept=accept["cycle"] - start,
                           response=response["cycle"] - start, commit=commit["cycle"] - start))
    need(len(result) == 32 and len({(row["seq"], tuple(row["rob"]), row["pdest"]) for row in result}) == 32,
         "committed transaction inventory")
    return result


def branch_offset(word):
    immediate = ((word >> 31) << 12) | (((word >> 7) & 1) << 11) | (((word >> 25) & 63) << 5) | (((word >> 8) & 15) << 1)
    return immediate - 8192 if immediate & 4096 else immediate


def milestones(frontier, symbols):
    def one_entry(name):
        positions = [row["position"] for row in frontier if row["pc"] == symbols[name][0]]
        need(len(positions) == 1, "missing/duplicate function entry: " + name)
        return positions[0]
    wrapper, leaf = one_entry("caller_full"), one_entry(LEAF)
    wrapper_start, wrapper_size = symbols["caller_full"][:2]
    leaf_start, leaf_size = symbols[LEAF][:2]
    call = frontier[leaf - 1]
    need(wrapper < leaf and wrapper_start <= call["pc"] < wrapper_start + wrapper_size
         and call["word"] & 127 in (0x6f, 0x67) and (call["word"] >> 7) & 31 == 1
         and call["group_count"] == 1, "leaf entry lacks individually retired caller call")
    loop_rows = defaultdict(list)
    for row in frontier:
        if wrapper_start <= row["pc"] < wrapper_start + wrapper_size and row["word"] & 127 == 0x63 and branch_offset(row["word"]) < 0:
            loop_rows[row["pc"]].append(row["position"])
    loops = sorted(loop_rows.items(), key=lambda item: item[1][0])
    # Labels describe statically verified dynamic branch visits, not execution times.
    bounds = [("wrapper_entry", wrapper)]
    bounds += [("loop_%d_last_branch" % (i + 1), positions[-1]) for i, (_, positions) in enumerate(loops)]
    bounds += [("leaf_call", leaf - 1), ("leaf_entry", leaf)]
    for name, begin, size in (("wrapper_return", wrapper_start, wrapper_size), ("leaf_return", leaf_start, leaf_size)):
        positions = [row["position"] for row in frontier if begin <= row["pc"] < begin + size and row["word"] == 0x00008067]
        need(len(positions) == 1, "missing/duplicate function return: " + name)
        bounds.append((name, positions[0]))
    bounds.sort(key=lambda item: item[1])
    need(len({position for _, position in bounds}) == len(bounds), "ambiguous frontier milestone")
    points = {name: dict(frontier[position]) for name, position in bounds}
    return points, [dict(pc=pc, visits=len(positions), first_position=positions[0], last_position=positions[-1],
                         backedge_target=pc + branch_offset(frontier[positions[0]]["word"])) for pc, positions in loops]


def call_redirect_context(records, events, call, leaf, start, observer):
    """Conservative scalar-origin association, conditional on fixed RTL liveness.

    Events must first pass the frozen O2 audit. A full ROB pointer alone is
    insufficient: the old occupant may have retired
    or been flushed. Check both exit kinds between origin and call retirement.
    Unlike vdot transactions, scalar dispatch generations are not logged.
    """
    rob = ":".join(map(str, call["rob"]))
    tick = start + call["tick"]
    matching = [row for row in records if row["cycle"] == tick
                and (row["flag"], row["rob"]) == tuple(call["rob"])]
    need(len(matching) == 1 and matching[0]["count"] == 1 and
         all(matching[0][key] == call[key] for key in ("pc", "word", "slot")),
         "ambiguous scalar call retirement identity")
    redirects = [row for _, _, kind, row in events if kind == "REDIRECT"]
    parents = {row["cycle"]: row for _, _, kind, row in events if kind == "VFEX4_REDIRECT"}
    candidates = []
    for event in redirects:
        if event["rob"] != rob or not records[0]["cycle"] <= event["cycle"] < tick:
            continue
        exits = [row for row in records if event["cycle"] <= row["cycle"]
                 and (row["cycle"], row["slot"]) < (tick, call["slot"])
                 and (row["flag"], row["rob"]) == tuple(call["rob"])]
        kills = [row for row in redirects if event["cycle"] < row["cycle"] <= tick
                 and observer.flushed(rob, row["rob"], row["self"])]
        parent = parents.get(event["cycle"] + 1)
        paired = parent is not None and (parent["rob"], parent["self"]) == (rob, event["self"])
        candidates.append(dict(redirect_tick=event["cycle"] - start, rob=list(call["rob"]),
                               redirect_ftq=event["ftq"], self=event["self"], parent_paired=paired,
                               intervening_retirements=[dict(row) for row in exits],
                               intervening_flushing_redirects=[dict(row) for row in kills],
                               observed_continuity=event["self"] == 0 and paired and not exits and not kills,
                               redirect_to_call_retire=tick - event["cycle"],
                               redirect_to_leaf_retire=start + leaf["tick"] - event["cycle"]))
    survivors = [row for row in candidates if row["observed_continuity"]]
    return dict(scope=REDIRECT_SCOPE, candidates=candidates,
                status="UNIQUE_CONTINUOUS_ORIGIN" if len(survivors) == 1 else
                       "NO_CONTINUOUS_ORIGIN" if not survivors else "AMBIGUOUS_ORIGINS",
                origin=survivors[0] if len(survivors) == 1 else None)


def check_redirect_commit_exclusion(retirements, events):
    # Fixed Rob.scala blockCommit includes io.redirect.valid. A contradictory
    # scalar event must not become an association merely by convenient ordering.
    ticks = {row["cycle"] for _, _, kind, row in events if kind == "REDIRECT"}
    need(not any(row["cycle"] in ticks for row in retirements), "retirement on ROB redirect cycle")


def one_run(data, modules, manifest, paths, symbols, phase):
    prefix = "run/runs/" + phase + "/"
    stderr, stdout = (data[prefix + name].decode("utf-8") for name in ("stderr.log", "stdout.log"))
    saved = json.loads(data[prefix + "validation.json"])
    receipt = json.loads(data[prefix + "result.json"])
    need(receipt.get("process_started") is True and receipt.get("exit_code") == 0 and not receipt.get("timed_out"), "normal process receipt")
    counter, observer = modules["counter"], modules["observer"]
    parsed = counter.parse_events(stderr)
    records = window_records(parsed)
    counter.walk = lambda compiled: compiled
    samples = counter.trace_windows(parsed, manifest, paths)
    for sample, entry in zip(samples, manifest["plan"]):
        sample.update(dataset=entry["dataset"], scope=manifest["rows"][entry["index"]]["scope"])
    need(samples == saved["samples"] and len(samples) == len(records) == 36, "raw samples differ from qualified audit")
    audit = observer.analyze(stderr + stdout)
    need(audit["status"] == "O2_TRACE_PASS" and audit["counts"]["COMMIT"] == 672
         and all(audit[key] == 0 for key in ("pending_count", "pending_div_count", "unfinished_rob_count")), "full O2 protocol audit")
    events, uart = observer.extract_events_and_uart(stderr + stdout)
    check_redirect_commit_exclusion(parsed["RETIRE"], events)
    need("Difftest enabled." in stdout and uart.count("HIT GOOD TRAP") == 1, "normal live DiffTest/trap")
    index, result = transaction_index(events), []
    for sample, retired in zip(samples, records):
        # Validate grouping for every window, including RVV and warmup.
        start, end = sample["sample_ticks"][1:3]
        frontier = expanded_frontier(retired, paths[sample["id"]], start)
        if sample["method"] != "vdot" or sample["phase"] != "measured":
            continue
        transactions = committed_transactions(retired, index, start)
        points, loops = milestones(frontier, symbols)
        first = min(row["accept"] for row in transactions)
        last = max(row["response"] for row in transactions)
        entry = manifest["plan"][sample["seq"]]
        previous = manifest["plan"][sample["seq"] - 1] if sample["seq"] else None
        result.append(dict(seq=sample["seq"], dataset=sample["dataset"], repeat=sample["repeat"],
                           order="vdot_then_rvv" if entry["repeat"] % 2 == 0 else "rvv_then_vdot",
                           previous_method=manifest["rows"][previous["index"]]["method"] if previous else None,
                           previous_dataset=previous["dataset"] if previous else None,
                           previous_repeat=previous["repeat"] if previous else None,
                           cycles=end - start, instructions=sample["instructions"],
                           before_first_accept=first, response_envelope=last - first,
                           after_last_response=end - start - last,
                           accept_minus_leaf_entry_retire=first - points["leaf_entry"]["tick"],
                           call_to_leaf_retirement_gap=points["leaf_entry"]["tick"] - points["leaf_call"]["tick"],
                           call_redirect=call_redirect_context(retired, events, points["leaf_call"],
                                                              points["leaf_entry"], start, observer),
                           outside_counter_bounds=sum(not (0 <= row["accept"] <= row["response"] < end - start) for row in transactions),
                           latency_histogram=dict(Counter(str(row["response"] - row["accept"]) for row in transactions)),
                           milestones=points, loops=loops, frontier=frontier, transactions=transactions))
    need(len(result) == 12, "formal diagnostic window inventory")
    return result


def compare(left, right):
    """All deltas are right minus left; never reinterpret a gap as execution cost."""
    a, b = left["frontier"], right["frontier"]
    need([(r["pc"], r["word"], r["occurrence"]) for r in a] ==
         [(r["pc"], r["word"], r["occurrence"]) for r in b], "compared dynamic paths differ")
    changed = [i for i in range(len(a)) if a[i]["tick"] != b[i]["tick"]]
    gap_changes = []
    for i in range(1, len(a)):
        ga, gb = a[i]["tick"] - a[i - 1]["tick"], b[i]["tick"] - b[i - 1]["tick"]
        if ga != gb:
            gap_changes.append(dict(position=i, pc=a[i]["pc"], occurrence=a[i]["occurrence"],
                                    left_gap=ga, right_gap=gb, delta=gb - ga,
                                    left_group=a[i]["group"], right_group=b[i]["group"]))
    def within(row, window):
        return 0 <= row["tick"] < window["cycles"]
    def coordinate(position):
        if position is None:
            return None
        x, y = a[position], b[position]
        return dict(position=position, pc=x["pc"], word=x["word"], occurrence=x["occurrence"],
                    left_tick=x["tick"], right_tick=y["tick"], left_group_count=x["group_count"],
                    right_group_count=y["group_count"], left_within_sample=within(x, left),
                    right_within_sample=within(y, right))
    measured = [i for i in changed if within(a[i], left) and within(b[i], right)]
    points = sorted(left["milestones"], key=lambda name: left["milestones"][name]["position"])
    need(points == sorted(right["milestones"], key=lambda name: right["milestones"][name]["position"]), "milestone path differs")
    # The two CSR samples are execution-stage coordinates. All inner points are
    # retirement coordinates; this is an exact telescoping partition, not a set
    # of non-overlapping execution costs. Signed gaps are retained.
    coordinates = [("csr_sample_start", 0, 0)]
    coordinates += [(name, left["milestones"][name]["tick"], right["milestones"][name]["tick"]) for name in points]
    coordinates += [("csr_sample_end", left["cycles"], right["cycles"])]
    segments = []
    for previous, current in zip(coordinates, coordinates[1:]):
        la, rb = current[1] - previous[1], current[2] - previous[2]
        segments.append(dict(start=previous[0], end=current[0], left_coordinate_gap=la,
                             right_coordinate_gap=rb, delta=rb - la))
    need(sum(row["left_coordinate_gap"] for row in segments) == left["cycles"] and
         sum(row["right_coordinate_gap"] for row in segments) == right["cycles"], "coordinate partition total")
    return dict(left={k: left[k] for k in ("label", "seq", "dataset", "repeat", "cycles", "order")},
                right={k: right[k] for k in ("label", "seq", "dataset", "repeat", "cycles", "order")},
                cycle_delta=right["cycles"] - left["cycles"], instruction_delta=right["instructions"] - left["instructions"],
                before_first_accept_delta=right["before_first_accept"] - left["before_first_accept"],
                first_different_retirement_coordinate=coordinate(changed[0] if changed else None),
                first_different_measured_retirement_coordinate=coordinate(measured[0] if measured else None),
                differing_positions=len(changed), differing_measured_positions=len(measured),
                changed_retirement_gaps=len(gap_changes), first_changed_gap=gap_changes[0] if gap_changes else None,
                largest_gap_changes=sorted(gap_changes, key=lambda row: (-abs(row["delta"]), row["position"]))[:8],
                coordinate_segments=segments,
                all_retirement_milestones_within_samples=all(within(row, window) for window in (left, right)
                                                             for row in window["milestones"].values()))


def aggregate(cases):
    """Keep four-window totals separate from the extrema of individual windows."""
    result = []
    fields = ("cycles", "before_first_accept", "response_envelope", "after_last_response")
    for dataset in range(3):
        totals = {}
        for label, windows in cases.items():
            if not label.startswith("h"):
                continue
            rows = [row for row in windows if row["dataset"] == dataset]
            need([row["repeat"] for row in rows] == [2, 3, 4, 5], "formal total repeat inventory")
            totals[label] = {field: sum(row[field] for row in rows) for field in fields}
        low = min(totals, key=lambda label: (totals[label]["cycles"], label))
        high = max(totals, key=lambda label: (totals[label]["cycles"], label))
        differences = {field: totals[high][field] - totals[low][field] for field in fields}
        left = [row for row in cases[low] if row["dataset"] == dataset]
        right = [row for row in cases[high] if row["dataset"] == dataset]
        comparisons = [compare(a, b) for a, b in zip(left, right)]
        segments = [dict(start=segment["start"], end=segment["end"],
                         delta=sum(row["coordinate_segments"][i]["delta"] for row in comparisons))
                    for i, segment in enumerate(comparisons[0]["coordinate_segments"])]
        need(sum(row["delta"] for row in segments) == differences["cycles"], "aggregate coordinate total")
        result.append(dict(dataset=dataset, scope="four formal windows per image (repeats 2,3,4,5)",
                           totals=totals, minimum_label=low, maximum_label=high,
                           maximum_minus_minimum=differences, coordinate_segment_deltas=segments))
    return result


def require_identical_replay(normal, replay, label):
    need(normal == replay, "per-position recovery/replay diagnostic differs: " + label)


def run(evidence, output):
    evidence, output = unlinked(evidence).resolve(), output.resolve()
    need(not output.exists() and output != evidence and evidence not in output.parents, "new output outside evidence required")
    raw_index = regular(evidence, "index.json").read_bytes()
    need(digest(raw_index) == INDEX_SHA256, "qualified screen index changed")
    index = json.loads(raw_index)
    need(index["decision"] == "HOLD_CONTEXT_VARIATION" and {row["label"] for row in index["campaigns"]} == set(LABELS), "screen scope")
    output.mkdir(parents=True)
    cases, identities = {}, []
    for label in LABELS:
        item = next(row for row in index["campaigns"] if row["label"] == label)
        data, modules, identity = load_case(evidence, item)
        with tempfile.TemporaryDirectory(prefix="context-elf-", dir=output) as temporary:
            elf = Path(temporary) / "qualified.elf"
            elf.write_bytes(data["build/vdot-perf.elf"])
            manifest, paths, symbols = compiled_paths(data, modules, elf, label)
            normal = one_run(data, modules, manifest, paths, symbols, "recovery")
            replay = one_run(data, modules, manifest, paths, symbols, "replay")
        require_identical_replay(normal, replay, label)
        for row in normal:
            row["label"] = label
        cases[label] = normal
        identity["recovery_replay_observations_identical"] = True
        identities.append(identity)
        print(json.dumps(dict(case=label, status="CONTEXT_CASE_PASS", formal_windows=12)), flush=True)
    matched = [compare(base, cases[label][i]) for label in LABELS if label.startswith("h") and label != "h0"
               for i, base in enumerate(cases["h0"])]
    extrema = []
    for dataset in range(3):
        rows = [row for label, group in cases.items() if label.startswith("h") for row in group if row["dataset"] == dataset]
        low = min(rows, key=lambda row: (row["cycles"], row["label"], row["seq"]))
        high = max(rows, key=lambda row: (row["cycles"], row["label"], row["seq"]))
        extrema.append(compare(low, high))
    detail = dict(format="hoisted-retirement-frontier-detail-v1", cases=cases)
    raw_detail = json_bytes(detail)
    compressed = gzip.compress(raw_detail, compresslevel=9, mtime=0)
    (output / "frontiers.json.gz").write_bytes(compressed)
    concise = {label: [{k: value for k, value in row.items() if k not in ("frontier", "transactions")} for row in rows]
               for label, rows in cases.items()}
    redirect_summary = {}
    for label, rows in cases.items():
        origins = [row["call_redirect"]["origin"] for row in rows if row["call_redirect"]["origin"]]
        redirect_summary[label] = dict(statuses=dict(Counter(row["call_redirect"]["status"] for row in rows)),
            call_to_leaf_gap_by_status={status: dict(Counter(str(row["call_to_leaf_retirement_gap"]) for row in rows
                                       if row["call_redirect"]["status"] == status))
                                       for status in sorted({row["call_redirect"]["status"] for row in rows})},
            redirect_to_leaf_retire_histogram=dict(Counter(str(row["redirect_to_leaf_retire"]) for row in origins)))
    result = dict(status="HOISTED_CONTEXT_PREFIX_PASS", scope="six sealed campaigns; 72 formal vdot windows in each of recovery/replay",
                  input_index_sha256=INDEX_SHA256, analyzer_sha256=digest(Path(__file__).read_bytes()),
                  original_decision=index["decision"], decision_changed=False, new_emu_runs=0,
                  prior_full_qualification="reused by pinned complete archive identities; no external hardware/reference revalidation",
                  recomputed="all 432 normal windows: exact ELF scalar paths, counter identities/fences, complete O2 protocol; 144 formal vdot frontiers/transaction chains",
                  interpretation="retirement coordinates and gaps are not scalar execution latency or causal attribution; shared retirement groups retain provenance; ACCEPT coordinates can precede leaf-entry retirement",
                  limits="T13 retirement is marker-gated and does not observe complete preceding UART/initialization/other window-external execution; no cache/predictor cause inferred; scalar redirect origin liveness is a fixed-RTL semantic premise",
                  inputs=identities, windows=concise, matched_h0_comparisons=matched,
                  call_redirect_summary=redirect_summary, call_redirect_scope=REDIRECT_SCOPE,
                  within_dataset_single_window_extrema=extrema, within_dataset_four_window_totals=aggregate(cases),
                  detail=dict(path="frontiers.json.gz", raw_sha256=digest(raw_detail), raw_bytes=len(raw_detail),
                              sha256=digest(compressed), bytes=len(compressed)))
    (output / "result.json").write_bytes(json_bytes(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if hasattr(os, "sched_setaffinity"):
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    result = run(args.evidence, args.output)
    print(json.dumps({key: result[key] for key in ("status", "new_emu_runs", "original_decision", "detail")}, indent=2))


if __name__ == "__main__":
    main()
