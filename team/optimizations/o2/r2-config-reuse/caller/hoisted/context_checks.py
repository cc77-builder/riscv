"""Targeted regressions for context_prefix; never run hardware or alter evidence.

The sealed h0 trace is the positive fixture. Mutations below are confined to
memory or a new temporary directory. Local binding tests do not qualify their
synthetic event streams as physical O2 runs.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile


def run(analyzer, evidence, output):
    spec = importlib.util.spec_from_file_location("context_prefix_checked", analyzer)
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)
    evidence = c.unlinked(evidence).resolve()
    output = output.resolve()
    c.need(not output.exists() and output != evidence and evidence not in output.parents,
           "new check output outside evidence required")
    raw_index = c.regular(evidence, "index.json").read_bytes()
    c.need(c.digest(raw_index) == c.INDEX_SHA256, "qualified screen index changed")
    index = json.loads(raw_index)
    item = next(row for row in index["campaigns"] if row["label"] == "h0")
    data, modules, identity = c.load_case(evidence, item)
    checks = []

    def accepted(name, fn, scope="sealed real fixture"):
        detail = fn()
        checks.append(dict(name=name, expectation="accept", status="PASS", scope=scope, detail=detail))

    def rejected(name, why, fn, scope="in-memory mutation of real fixture"):
        try:
            fn()
        except ValueError as exc:
            reasons = (why,) if isinstance(why, str) else why
            c.need(any(reason in str(exc) for reason in reasons), name + ": wrong rejection: " + str(exc))
            checks.append(dict(name=name, expectation="reject", status="PASS", scope=scope, reason=str(exc)))
        else:
            raise ValueError(name + ": mutation was accepted")

    with tempfile.TemporaryDirectory(prefix="hoisted-context-checks-") as temporary:
        root = Path(temporary)
        elf = root / "fixture.elf"
        elf.write_bytes(data["build/vdot-perf.elf"])
        manifest, paths, symbols = c.compiled_paths(data, modules, elf, "h0")
        normal = c.one_run(data, modules, manifest, paths, symbols, "recovery")
        replay = c.one_run(data, modules, manifest, paths, symbols, "replay")
        accepted("real_recovery_replay", lambda: c.require_identical_replay(normal, replay, "h0"))
        c.need(len(normal) == 12, "fixture formal window count")
        left = deepcopy(normal[0])
        left["label"] = "h0"
        accepted("identical_coordinates_and_complete_partition", lambda: c.compare(left, left))
        drift = deepcopy(replay)
        drift[0]["frontier"][20]["tick"] += 1
        c.need(drift[0]["cycles"] == normal[0]["cycles"], "same-total drift fixture")
        rejected("same_total_replay_coordinate_drift", "per-position recovery/replay diagnostic differs",
                 lambda: c.require_identical_replay(normal, drift, "h0"))
        before = deepcopy(left)
        c.need(before["frontier"][0]["tick"] < 0, "pre-sample marker fixture")
        before["frontier"][0]["tick"] -= 1
        comparison = c.compare(left, before)
        c.need(comparison["first_different_retirement_coordinate"]["position"] == 0 and
               comparison["first_different_retirement_coordinate"]["left_within_sample"] is False and
               comparison["first_different_measured_retirement_coordinate"] is None,
               "pre-sample coordinate mislabeled as measured")
        accepted("pre_sample_difference_is_distinguished", lambda: comparison)
        changed = deepcopy(left["frontier"])
        changed[left["milestones"]["leaf_entry"]["position"] - 1]["word"] = 0x13
        rejected("leaf_entry_without_real_call", "leaf entry lacks individually retired caller call",
                 lambda: c.milestones(changed, symbols))

        stderr = data["run/runs/recovery/stderr.log"].decode()
        stdout = data["run/runs/recovery/stdout.log"].decode()
        counter, observer = modules["counter"], modules["observer"]
        parsed = counter.parse_events(stderr)
        records = c.window_records(parsed)[left["seq"]]
        row = manifest["rows"][manifest["plan"][left["seq"]]["index"]]
        path = paths[row["id"]]
        start = json.loads(data["run/runs/recovery/validation.json"])["samples"][left["seq"]]["sample_ticks"][1]
        altered = deepcopy(parsed)
        altered["RETIRE"].insert(1, deepcopy(altered["RETIRE"][0]))
        rejected("duplicate_retirement_coordinate", "retirement slot order/duplicate", lambda: c.window_records(altered))
        altered = deepcopy(parsed)
        a, b = next((a, b) for a, b in zip(altered["RETIRE"], altered["RETIRE"][1:]) if a["cycle"] == b["cycle"])
        b.update(flag=a["flag"], rob=a["rob"])
        rejected("same_cycle_retirement_ROB_alias", "duplicate same-cycle retirement ROB", lambda: c.window_records(altered))
        changed = deepcopy(records)
        changed[10]["pc"] += 4
        rejected("wrong_dynamic_path_pc", "retirement path/coverage", lambda: c.expanded_frontier(changed, path, start))
        changed = deepcopy(records)
        custom = next(i for i, record in enumerate(changed) if record["word"] & c.CUSTOM_MASK == c.CUSTOM_MATCH)
        changed[custom]["count"] = 2
        rejected("compressed_group_hides_custom", "control/custom hidden in retirement group",
                 lambda: c.expanded_frontier(changed, path, start))
        altered = deepcopy(parsed)
        altered["CSR_SAMPLE"][4 * left["seq"] + 1]["cycle"] += 1
        rejected("CSR_tick_drift_without_value_change", ("counter sampling bounds", "cycle CSR/global clock disagreement"),
                 lambda: counter.trace_windows(altered, manifest, paths))

        events, _ = observer.extract_events_and_uart(stderr + stdout)
        bindings = c.transaction_index(events)
        transactions = c.committed_transactions(records, bindings, start)
        target = transactions[0]
        changed = deepcopy(records)
        changed[custom]["flag"] ^= 1
        rejected("retired_ROB_flag_mismatch", "T13/O2 commit mismatch",
                 lambda: c.committed_transactions(changed, bindings, start))
        target_rob = ":".join(map(str, target["rob"]))

        def alter_event(kind, predicate, field, value):
            changed, hits = [], 0
            for tick, order, name, event in events:
                event = dict(event)
                if name == kind and predicate(event):
                    event[field] = value
                    hits += 1
                changed.append((tick, order, name, event))
            c.need(hits == 1, "unique real mutation target")
            return changed

        changed = alter_event("RESPONSE", lambda event: event["seq"] == target["seq"] and event["rob"] == target_rob,
                              "pdest", target["pdest"] ^ 1)
        rejected("response_physical_destination_mismatch", "committed response identity/order",
                 lambda: c.committed_transactions(records, c.transaction_index(changed), start), "local binding only")
        changed = alter_event("COMMIT", lambda event: event["cycle"] == start + target["commit"] and event["rob"] == target_rob,
                              "ftq", "0:0" if target["ftq"] != "0:0" else "0:1")
        rejected("commit_allocation_FTQ_mismatch", "commit allocation mismatch",
                 lambda: c.committed_transactions(records, c.transaction_index(changed), start), "local binding only")

        # A same-cycle new allocation must not capture the old COMMIT. If this
        # real transaction already has one, retain it; otherwise add a local
        # binding-only fixture. The full O2 auditor is not bypassed in run().
        commit_tick = start + target["commit"]
        changed = list(events)
        existing = commit_tick in bindings[1][tuple(target["rob"])]
        if not existing:
            changed.append((commit_tick, len(events), "ENQUEUE", dict(cycle=commit_tick, rob=target_rob,
                            pc=target["pc"] + 4, ftq=target["ftq"], word=c.CUSTOM_MATCH)))
            changed.sort(key=lambda event: (event[0], event[1]))
        rebound = c.committed_transactions(records, c.transaction_index(changed), start)
        c.need(rebound[0] == target, "same-cycle allocation stole preceding commit")
        accepted("same_cycle_ROB_reallocation_uses_old_generation", lambda: dict(real_reallocation=existing),
                 "real fixture" if existing else "local binding only")
        shifted = c.committed_transactions(records, bindings, start + target["accept"] + 1)
        c.need(shifted[0]["accept"] == -1 and len(shifted) == 32, "signed origin was filtered or clipped")
        accepted("signed_transaction_coordinates_preserved", lambda: dict(first_accept=-1, transactions=32),
                 "local shifted coordinate origin")

        # These target the new scalar-origin continuity conditions. They do not
        # claim that scalar ENQUEUE/generation has become directly observable.
        window = normal[1]
        c.need(window["call_redirect"]["status"] == "UNIQUE_CONTINUOUS_ORIGIN", "real redirect fixture")
        retired = c.window_records(parsed)[window["seq"]]
        sample = json.loads(data["run/runs/recovery/validation.json"])["samples"][window["seq"]]
        origin_start = sample["sample_ticks"][1]
        origin = window["call_redirect"]["origin"]
        origin_tick = origin_start + origin["redirect_tick"]
        call, leaf = window["milestones"]["leaf_call"], window["milestones"]["leaf_entry"]
        rob = ":".join(map(str, call["rob"]))

        def unique_origin(events_arg=events, records_arg=retired):
            result = c.call_redirect_context(records_arg, events_arg, call, leaf, origin_start, observer)
            c.need(result["status"] == "UNIQUE_CONTINUOUS_ORIGIN", "scalar origin continuity not established")
            return result

        accepted("real_scalar_redirect_continuity", unique_origin)
        c.need(normal[0]["call_redirect"]["status"] == "NO_CONTINUOUS_ORIGIN", "real no-origin fixture")
        accepted("no_redirect_is_reported_without_invented_origin", lambda: normal[0]["call_redirect"])
        changed = [event for event in events if not (event[2] == "VFEX4_REDIRECT" and event[0] == origin_tick + 1)]
        rejected("scalar_origin_missing_parent_pair", "scalar origin continuity not established",
                 lambda: unique_origin(changed), "local association only")
        changed = []
        for tick, order, kind, event in events:
            event = dict(event)
            if (kind == "REDIRECT" and tick == origin_tick or kind == "VFEX4_REDIRECT" and tick == origin_tick + 1):
                event["self"] = 1
            changed.append((tick, order, kind, event))
        rejected("self_flushed_origin_not_reused_as_call", "scalar origin continuity not established",
                 lambda: unique_origin(changed), "local association only")
        changed = deepcopy(retired)
        stale = dict(next(row for row in retired if row["cycle"] == origin_start + call["tick"]
                          and (row["flag"], row["rob"]) == tuple(call["rob"])))
        stale.update(cycle=origin_tick + 1, pc=stale["pc"] + 4)
        changed.append(stale)
        changed.sort(key=lambda row: (row["cycle"], row["slot"]))
        rejected("intervening_same_ROB_retirement_breaks_origin", "scalar origin continuity not established",
                 lambda: unique_origin(records_arg=changed), "local association only")
        changed = deepcopy(retired)
        duplicate = dict(stale, cycle=origin_start + call["tick"], slot=call["slot"] ^ 1)
        changed.append(duplicate)
        changed.sort(key=lambda row: (row["cycle"], row["slot"]))
        rejected("same_cycle_call_ROB_alias", "ambiguous scalar call retirement identity",
                 lambda: unique_origin(records_arg=changed), "local association only")
        flag, number = call["rob"]
        older = ":".join(map(str, (flag, number - 1) if number else (flag ^ 1, 47)))
        changed = events + [(origin_tick + 1, len(events), "REDIRECT",
                             dict(cycle=origin_tick + 1, rob=older, ftq="0:0", self=0))]
        rejected("older_flush_breaks_scalar_origin", "scalar origin continuity not established",
                 lambda: unique_origin(changed), "local association only")
        changed = alter_event("REDIRECT", lambda event: event["cycle"] == origin_tick,
                              "rob", ":".join(map(str, (flag ^ 1, number))))
        rejected("scalar_origin_full_ROB_flag_required", "scalar origin continuity not established",
                 lambda: unique_origin(changed), "local association only")
        changed = [dict(retired[0], cycle=origin_tick)]
        rejected("scalar_retirement_on_redirect_cycle", "retirement on ROB redirect cycle",
                 lambda: c.check_redirect_commit_exclusion(changed, events), "local association only")

        bad_root = root / "bad-index"
        bad_root.mkdir()
        (bad_root / "index.json").write_bytes(raw_index + b" ")
        rejected("changed_index_bytes", "qualified screen index changed",
                 lambda: c.run(bad_root, root / "rejected-index-output"), "new temporary fixture")
        linked_root = root / "linked-campaign"
        linked_root.mkdir()
        (linked_root / item["path"]).symlink_to(evidence / item["path"], target_is_directory=True)
        rejected("linked_campaign_directory", "linked evidence path", lambda: c.load_case(linked_root, item),
                 "new temporary fixture")
        ancestor = root / "linked-ancestor"
        ancestor.symlink_to(evidence, target_is_directory=True)
        rejected("linked_ancestor_directory", "linked evidence path",
                 lambda: c.regular(ancestor / item["path"], "archive-manifest.json"), "new temporary fixture")

    summary = dict(status="HOISTED_CONTEXT_CHECKS_PASS", analyzer_sha256=c.digest(analyzer.read_bytes()),
                   checks_sha256=c.digest(Path(__file__).read_bytes()), input_index_sha256=c.INDEX_SHA256,
                   fixture=identity, accepted=sum(row["expectation"] == "accept" for row in checks),
                   rejected=sum(row["expectation"] == "reject" for row in checks), checks=checks,
                   new_emu_runs=0, limits="negative semantic fixtures are synthetic, not additional physical EMU evidence")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(c.json_bytes(summary))
    print(json.dumps({key: summary[key] for key in ("status", "accepted", "rejected", "new_emu_runs")}))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analyzer", type=Path, default=Path(__file__).with_name("context_prefix.py"))
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.analyzer, args.evidence, args.output)
