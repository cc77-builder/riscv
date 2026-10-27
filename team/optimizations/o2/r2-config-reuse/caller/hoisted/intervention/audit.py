"""New-contract raw validation; frozen protocol/counter/frontier helpers reused."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

CONTRACT = "r2-s3-predecessor-intervention-v1"
ORDER = (0, 1, 1, 0) + (0, 1, 1, 0, 1, 0, 0, 1) * 2


def digest_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def summarize(targets):
    formal = [row for row in targets if row["trial"] >= 4]
    if [row["trial"] for row in targets] != list(range(20)):
        raise ValueError("target trial coverage")
    if [row["arm"] for row in targets] != list(ORDER):
        raise ValueError("target arm order")
    blocks = []
    for block in range(4):
        rows = formal[4 * block:4 * block + 4]
        arms = {}
        for arm in (0, 1):
            group = [row for row in rows if row["arm"] == arm]
            if len(group) != 2:
                raise ValueError("unbalanced formal block")
            arms[str(arm)] = dict(trials=[row["trial"] for row in group],
                                 cycles=[row["cycles"] for row in group],
                                 cycles_sum=sum(row["cycles"] for row in group),
                                 gaps=[row["call_to_leaf_retirement_gap"] for row in group],
                                 gap_sum=sum(row["call_to_leaf_retirement_gap"] for row in group),
                                 unique_origins=sum(row["call_redirect"]["status"] ==
                                                    "UNIQUE_CONTINUOUS_ORIGIN" for row in group))
        blocks.append(dict(block=block, order="".join("AB"[row["arm"]] for row in rows), arms=arms,
                           more_origins_a=arms["0"]["unique_origins"] > arms["1"]["unique_origins"],
                           larger_gap_sum_a=arms["0"]["gap_sum"] > arms["1"]["gap_sum"]))
    ambiguous = any(row["call_redirect"]["status"] == "AMBIGUOUS_ORIGINS" for row in targets)
    if ambiguous:
        decision = "INCONCLUSIVE_AMBIGUOUS_ORIGIN"
    elif all(block["more_origins_a"] and block["larger_gap_sum_a"] for block in blocks):
        decision = "REPRODUCED_PREDECESSOR_ASSOCIATION"
    elif any(block["more_origins_a"] or block["larger_gap_sum_a"] for block in blocks):
        decision = "MIXED_PREDECESSOR_ASSOCIATION"
    else:
        decision = "NOT_REPRODUCED_IN_THIS_PLAN"
    return dict(decision=decision, formal_trials=16, formal_trials_per_arm=8, blocks=blocks,
                legacy_hold_changed=False, kernel_selection=False,
                caveat="Fixed-order single-image intervention, not predictor identification or independent random samples")


def normal(e, repo, build, run, receipt):
    g = e.g
    g.require(receipt.get("process_started") is True and receipt.get("exit_code") == 0
              and not receipt.get("timed_out"), "intervention incomplete execution")
    manifest = e.read(build / "source/manifest.json")
    expected_plan = [dict(index=(arm + 1 if role == 0 else 0), stage=0, dataset=0,
                          repeat=trial, phase="warmup" if trial < 4 else "measured", trial=trial,
                          arm=arm, role="predecessor" if role == 0 else "target")
                     for trial, arm in enumerate(ORDER) for role in (0, 1)]
    g.require(manifest["contract"] == CONTRACT and manifest["plan"] == expected_plan
              and manifest["expected_dots"] == 640 and len(manifest["rows"]) == 3,
              "intervention manifest scope/order")
    stdout, stderr = ((run / name).read_text() for name in ("stdout.log", "stderr.log"))
    gate = g.load("intervention_failure_markers", repo / "team/optimizations/o1/audit/runtime_gate.py")
    fatal = g.load("intervention_fatal", repo / "team/optimizations/o2/fullcore/recheck.py")
    observer = g.load("intervention_protocol", repo / "team/optimizations/o2/fullcore/analyze.py")
    counter = g.load("intervention_counters", repo / "team/workloads/unified-vdot/check.py")
    frontier = g.load("intervention_frontiers", Path(__file__).resolve().parents[1] / "context_prefix.py")
    for stream in (stdout, stderr):
        gate.validate_failure_markers(stream)
        fatal.reject_fatal_output(stream)
    events, uart = observer.extract_events_and_uart(stderr + stdout)
    gate.validate_failure_markers(uart)
    fatal.reject_fatal_output(uart)
    plain = gate.normalize_console(uart)
    g.require("Difftest enabled." in stdout and plain.count("HIT GOOD TRAP") == 1,
              "live DiffTest and unique GOOD TRAP required")
    elf = g.ELF((build / "vdot-perf.elf").read_bytes())
    paths = {}
    for row in manifest["rows"]:
        checked = [e.pathcheck.path(elf, 0, row["method"], bytes(raw))[0] for raw in manifest["inputs"]]
        g.require(checked[0] == checked[1] == checked[2], "input-dependent compiled full path")
        paths[row["id"]] = checked[0]
    parsed = counter.parse_events(stderr)
    counter.walk = lambda compiled: compiled
    samples = counter.trace_windows(parsed, manifest, paths)
    windows = frontier.window_records(parsed)
    g.require(len(samples) == len(windows) == 40, "intervention full window coverage")
    analysis = observer.analyze(stderr + stdout)
    g.require(analysis["status"] == "O2_TRACE_PASS" and analysis["schema"]["slots"] == 2
              and all(analysis.get(key) == 0 for key in ("pending_count", "pending_div_count", "unfinished_rob_count"))
              and analysis["counts"].get("COMMIT") == 640, "complete O2 protocol/commits")
    frontier.check_redirect_commit_exclusion(parsed["RETIRE"], events)
    transactions_index = frontier.transaction_index(events)
    targets, hashes, common_calls = [], [], set()
    expected_uart = [f"CI_BEGIN contract={CONTRACT} trials=20 windows=40"]
    for sample, step, records in zip(samples, manifest["plan"], windows):
        sample.update(dataset=0, scope="full", trial=step["trial"], arm=step["arm"], role=step["role"])
        expected_uart.append(f"CW {sample['seq']} {sample['cycles']} {sample['instructions']} 0")
        start, end = sample["sample_ticks"][1:3]
        expanded = frontier.expanded_frontier(records, paths[step["index"]], start)
        symbols = dict(elf.symbols)
        symbols[frontier.LEAF] = elf.symbols[manifest["rows"][step["index"]]["leaf"]]
        points, loops = frontier.milestones(expanded, symbols)
        common_calls.add((points["leaf_call"]["pc"], points["leaf_call"]["word"]))
        hashes.append(dict(seq=sample["seq"], positions=len(expanded), groups=len(records),
                           frontier_sha256=digest_json(expanded), raw_groups_sha256=digest_json(records)))
        if step["role"] != "target":
            continue
        tx = frontier.committed_transactions(records, transactions_index, start)
        latency = dict(Counter(str(row["response"] - row["accept"]) for row in tx))
        # The frozen protocol auditor validates registered latency and legal
        # backpressure. Preserve the observed histogram rather than requiring
        # every otherwise valid transaction to happen to respond in two ticks.
        g.require(all(0 <= row["accept"] < row["response"] < end - start for row in tx),
                  "target transaction window binding")
        first, last = min(row["accept"] for row in tx), max(row["response"] for row in tx)
        targets.append(dict(trial=step["trial"], arm=step["arm"], phase=step["phase"], seq=sample["seq"],
                            cycles=sample["cycles"], instructions=sample["instructions"],
                            before_first_accept=first, response_envelope=last - first,
                            after_last_response=end - start - last,
                            accept_minus_leaf_entry_retire=first - points["leaf_entry"]["tick"],
                            call_to_leaf_retirement_gap=points["leaf_entry"]["tick"] - points["leaf_call"]["tick"],
                            call_redirect=frontier.call_redirect_context(records, events, points["leaf_call"],
                                                                         points["leaf_entry"], start, observer),
                            latency_histogram=latency, milestones=points, loops=loops, transactions=tx,
                            frontier_sha256=hashes[-1]["frontier_sha256"]))
    g.require(len(common_calls) == 1, "predecessor/target do not share one fixed caller callsite")
    pc, word = next(iter(common_calls))
    g.require(word & 127 == 0x67 and (word >> 7) & 31 == 1, "common caller is not indirect rd=ra")
    expected_uart += ["CI_CONTROLS detected=6 expected=6 restored=0", "CI_END windows=40 failures=0"]
    actual = [line for line in plain.splitlines() if line.startswith(("CI_", "CW "))]
    g.require(actual == expected_uart, "intervention raw UART/counters/judges/order differ")
    return dict(status="INTERVENTION_DIFFTEST_COUNTER_PATH_PASS", contract=CONTRACT, windows=40,
                formal_windows=32, formal_target_windows=16, committed_vdot=640, judge_fault_controls=6,
                fixed_call_pc=pc, fixed_call_word=word, samples=samples, frontier_hashes=hashes,
                targets=targets, summary=summarize(targets), hardware_changed=False, stable_default_changed=False,
                scalar_origin_scope=frontier.REDIRECT_SCOPE)


def audit(e, repo, build, run):
    # Reuse the complete frozen receipt/configuration/input/fixture/chronology
    # closure. Its normal checker is the new-contract private binding installed
    # by intervention.py. Negative helpers run on temporary log copies there,
    # so neither original evidence nor cached derived observations are rewritten.
    legacy = e.g.load("intervention_complete_archive_audit", e.HERE / "evidence.py")
    e.g.require(legacy.e is e and repo == e.ROOT, "archive engine/source identity")
    result = legacy.audit(build, run)
    result.update(status="INTERVENTION_RAW_AUDIT_PASS", windows_per_normal_run=40,
                  formal_windows_used=32, formal_target_windows=16, replay_windows=40,
                  ordinary_stack_demo_calls_per_normal_run=0, complete_replay_equal=True,
                  validation_sha256=digest_json(e.read(run / "runs/recovery/validation.json")),
                  conclusion=result.pop("summary"))
    return result
