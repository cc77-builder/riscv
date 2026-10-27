"""Read-only raw audit of the 4-shape/3-dataset configuration-reuse matrix.

No EMU is started. All reports are reconstructed from existing source-pinned
GNU artifacts, raw UART/CSR/O2 traces and actual process receipts.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import tempfile


def require(ok, why):
    if not ok:
        raise ValueError(why)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc_fields(record):
    """UTC is diagnostic metadata; actual ordering uses recorded monotonic time."""
    stamps = []
    for key in ("started", "finished"):
        require(isinstance(record.get(key), str), "missing UTC diagnostic field")
        stamp = datetime.fromisoformat(record[key])
        require(stamp.utcoffset() is not None, "UTC field lacks timezone")
        stamps.append(stamp)
    return tuple(stamps)


def verify_common(m, recorded, expected):
    require(recorded == expected, "complete runtime input closure differs")
    m.verify_files(expected)


def verify_summary(cached, summary):
    require(cached.get("summary") == summary, "cached nested statistics differ from raw samples")


def audit_timing(records, specs, state):
    """Independently recompute the measured spawn/wait envelope and phase gates."""
    require(type(state.get("workers")) is int and 1 <= state["workers"] <= 4,
            "invalid worker budget")
    boot = state.get("boot_id")
    require(isinstance(boot, str) and re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", boot),
            "invalid campaign boot identity")
    low, high = state.get("monotonic_start_ns"), state.get("monotonic_end_ns")
    require(type(low) is int and type(high) is int and 0 < low < high, "invalid campaign monotonic bounds")
    require(len(records) == len(specs) == 33, "expected 33 actual process records")
    require(len({s["label"] for s in specs}) == 33, "duplicate process labels")
    require(type(state.get("new_emu_runs")) is int and state["new_emu_runs"] == 33,
            "actual target count mismatch")
    require(state.get("active_pids") == {}, "unfinished active process")
    utc_fields(state)
    events, by_label, pids = [], {}, set()
    for record, spec in zip(records, specs):
        require(record.get("label") == spec["label"] and record.get("phase") == spec["phase"],
                "actual process label/phase differs")
        require(type(record.get("pid")) is int and record["pid"] > 0
                and record["pid"] not in pids, "missing or reused actual PID")
        pids.add(record["pid"])
        timing = record.get("monotonic")
        require(isinstance(timing, dict) and timing.get("boot_id") == boot
                and type(timing.get("pid")) is int and timing["pid"] == record["pid"]
                and timing.get("scope") == "popen_wait_bracket", "process timing identity mismatch")
        start, end = timing.get("start_ns"), timing.get("end_ns")
        require(type(start) is int and type(end) is int and low <= start < end <= high,
                "invalid process monotonic bounds")
        require(record.get("process_started") is True and type(record.get("exit_code")) is int
                and not record.get("timed_out"), "target incomplete")
        utc_fields(record)
        by_label[spec["label"]] = (start, end)
        events.extend(((start, 1), (end, -1)))
    negative = [s for s in specs if s["negative"] is True]
    recovery = [s for s in specs if s["phase"] == "recovery"]
    formal = [s for s in specs if s["phase"] == "formal"]
    replays = [s for s in specs if s["phase"] == "replay"]
    require(len(negative) == len(recovery) == 1 and len(formal) == 23 and len(replays) == 8,
            "phase inventory differs")
    neg_end = by_label[negative[0]["label"]][1]
    rec_start, rec_end = by_label[recovery[0]["label"]]
    require(neg_end <= rec_start, "negative/recovery processes overlap or reverse")
    require(all(rec_end <= by_label[s["label"]][0] for s in formal + replays),
            "parallel targets began before recovery completed")
    formal_end = max(by_label[s["label"]][1] for s in formal)
    require(all(formal_end <= by_label[s["label"]][0] for s in replays), "replay phase lacks formal barrier")
    active = peak = 0
    for stamp, delta in sorted(events):
        active += delta
        require(active >= 0, "invalid sweep ordering")
        peak = max(peak, active)
    require(active == 0 and peak <= state["workers"], "measured concurrency exceeds worker budget")
    return dict(status="MONOTONIC_PROCESS_CAPACITY_PASS", boot_id=boot, process_count=33,
                peak_process_envelopes=peak, worker_budget=state["workers"], phase_barriers=True,
                evidence_scope="conservative Popen/wait brackets; not instantaneous CPU utilisation",
                utc_used_for_ordering=False)


def record_audit(repo, g, f, m, cfg, image, directory, common, outer_contract,
                 replay=0, negative=False, fixture=None, expected_cwd=None, process_common=None):
    """Actual GNU + UART/CSR/counters/O2 revalidation; cached facts must match."""
    directory = Path(directory)
    record = read(directory / "result.json")
    require(type(record["replay"]) is int and record["replay"] == replay
            and type(record["negative"]) is bool and record["negative"] is negative,
            "run mode identity")
    require(record["contract"] == outer_contract and record["mode"] == "merged"
            and record["process_started"] is True and type(record["pid"]) is int and record["pid"] > 0,
            "run contract/process identity")
    require(type(record["exit_code"]) is int and not record.get("timed_out"), "incomplete target process")
    utc_fields(record)
    require(all(record[k] == image[k] for k in
                ("suite","shard","dataset","variant","name","path","image_sha256")), "raw image selection")
    build = Path(image["path"])
    g.verify_build(build, repo)
    require(sha(build / "vdot-perf.bin") == image["image_sha256"], "raw build image digest")
    m.validate_selection(image, read(build / "data/manifest.json"), read(build / "build.json"))
    if negative:
        require(fixture is not None and fixture["source_sha256"] == m.NEGATIVE_SHA
                and fixture["normal_reference_sha256"] == f.REFERENCE
                and fixture["historical_negative_hash_claim"] is False, "negative fixture identity")
        reference = fixture["binary"]
    else:
        require(fixture is None, "normal run received a fault fixture")
        reference = cfg["reference"]
    argv = [str(Path(cfg["hardware_source"]) / "build/emu"), "-i", str(build / "vdot-perf.bin"),
            "--flash=" + cfg["flash"], "--ram-size=128MB", "--diff=" + reference,
            "--max-cycles=2000000", "--seed=1"]
    require(record["command"] == argv and record["reference"] == reference, "raw command/reference drift")
    cwd = Path(expected_cwd) if expected_cwd is not None else directory / "cwd"
    require(record["cwd"] == str(cwd), "raw destination/cwd drift")
    local_inputs = {str(cwd / "build" / name): digest for name,digest in m.AUX.items()}
    local_inputs[str(build / "vdot-perf.bin")] = image["image_sha256"]
    if negative:
        local_inputs[reference] = fixture["negative_sha256"]
    require(process_common is not None and process_common ==
            {key: value for key, value in common.items() if not key.endswith("/vdot-perf.bin")},
            "per-process common map must remove only shared comparison BIN roles")
    expected_inputs = dict(process_common) | local_inputs
    require(record["files"] == expected_inputs, "runtime input inventory drift")
    # audit_probe verifies the complete shared map once before and after all thirty-three
    # records. Recheck each process's real private AUX/BIN/reference here.
    private_inputs = dict(local_inputs)
    private_inputs[reference] = fixture["negative_sha256"] if negative else f.REFERENCE
    m.verify_files(private_inputs)
    require(record["environment_overrides"] == {"XS_NEGATIVE_VECTOR_TARGET": "vdot" if negative else None},
            "fault environment drift")
    require(record["raw_sha256"] == {n:sha(directory/n) for n in ("stdout.log","stderr.log")},
            "raw transcript digest differs")
    suite = g.load("probe_raw_runtime_banner", repo / "team/optimizations/o2/fullcore/run_suite.py")
    suite.validate_runtime((directory/"stdout.log").read_text()+(directory/"stderr.log").read_text(), reference)
    # The original negative checker writes diagnostic JSON. Isolate those writes;
    # do not mutate the campaign we are auditing.
    with tempfile.TemporaryDirectory(prefix="config-raw-audit-") as tmp:
        scratch = Path(tmp)
        for name in ("result.json","stdout.log","stderr.log"):
            shutil.copyfile(directory/name, scratch/name)
        if negative:
            require(record["status"] == m.NEGATIVE_PASS and record["exit_code"] != 0, "negative exit/status")
            detail = m.negative_check(repo, build, scratch, record)
            require(detail == record["negative_details"] == read(directory/"negative.json"), "cached negative detail differs")
            require(read(scratch/"observation.json") == read(directory/"observation.json"), "cached negative O2 differs")
            fresh_samples = None
        else:
            require(record["status"] == m.NORMAL_PASS and record["exit_code"] == 0, "normal exit/status")
            windows, observation = f.verify_runtime(repo, build, scratch)
            require(windows == read(directory/"windows.json"), "cached windows differ from raw reparse")
            require(observation == read(directory/"observation.json"), "cached O2 differs from raw reparse")
            manifest = read(build/"data/manifest.json")
            require(len(windows["samples"]) == len(manifest["plan"]) == 24, "all 24 raw windows required")
            fresh_samples = []
            for sample, entry in zip(windows["samples"],manifest["plan"]):
                row = manifest["rows"][entry["index"]]
                fresh_samples.append(dict(sample,mode="merged",variant=image["variant"],shard=image["shard"],
                    software=row["software"],m=row["m"],k=row["k"],scope=row["scope"],
                    image_sha256=image["image_sha256"]))
            require(fresh_samples == record["samples"], "cached samples differ from raw reparse")
    m.verify_files(private_inputs)
    return dict(record=record, audit=dict(status="RAW_REPARSE_PASS", negative=negative,
        windows=0 if fresh_samples is None else len(fresh_samples), new_emu_runs=0,
        raw_sha256=record["raw_sha256"], source_hardware_remeasured=False))



def tree_seal(root):
    root = Path(root)
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "symlink in campaign evidence")
        if path.is_file():
            result[str(path.relative_to(root))] = sha(path)
    return result


def audit_matrix(p, build, campaign):
    """Read every actual process and reconstruct the complete published result."""
    import matrix as contract
    build, campaign = Path(build).resolve(), Path(campaign).resolve()
    images = p.selected(build)
    f, m = p.runtime()
    state, cached = read(campaign/"state.json"), read(campaign/"results.json")
    require(state["contract"] == cached["contract"] == contract.CONTRACT
            and state["status"] == cached["status"] == contract.RUN_PASS
            and state["functional_status"] == cached["functional_status"] == "FUNCTIONAL_PASS",
            "expanded matrix completion contract")
    require(type(cached.get("new_emu_runs")) is int and cached["new_emu_runs"] == 33,
            "cached process count")
    require(cached["parent_identity_sha256"] == sha(p.identity_path)
            and cached["current_precondition"] == p.precondition, "clean/baseline identity")
    require(read(campaign/"parent-identity.json") == p.identity, "copied identity differs")
    require(read(campaign/"hardware-profile.json") == p.identity["hardware_profile"], "copied profile differs")
    cfg, common = read(campaign/"configuration.json"), read(campaign/"runtime-inputs.json")
    require(cfg == p.identity["configuration"], "configuration differs")
    physical_before = p.physical()
    require(physical_before[0] == p.identity and physical_before[2] == p.identity["hardware_profile"],
            "physical identity differs")
    expected_common = p.common_inputs(build, images, m, physical_before)
    verify_common(m, common, expected_common)
    process_common = contract.process_inputs(common, p.comparison_bins())
    evidence_before = tree_seal(campaign)
    specs = contract.run_specs(images)
    require(read(campaign/"run-plan.json") == specs, "persisted run plan differs")
    require(len(specs) == 33 and len({s["label"] for s in specs}) == 33, "canonical process inventory")
    require({q.name for q in (campaign/"runs").iterdir()} == {s["label"] for s in specs}
            and all(q.is_dir() for q in (campaign/"runs").iterdir()), "missing/extra process outputs")
    fixture = read(campaign/"negative-fixture/fixture.json")
    require(sha(fixture["binary"]) == fixture["negative_sha256"], "fault fixture bytes")
    checked = []
    for spec in specs:
        checked.append(record_audit(p.repo, p.g, f, m, cfg, spec["image"],
            campaign/"runs"/spec["label"], common, contract.CONTRACT,
            replay=spec["replay"], negative=spec["negative"],
            fixture=fixture if spec["negative"] else None, process_common=process_common))
    records = [item["record"] for item in checked]
    timing = audit_timing(records, specs, state)
    require(cached.get("workers") == state["workers"] and cached.get("boot_id") == state["boot_id"],
            "cached capacity/clock identity differs")
    affinity = state.get("cpu_affinity")
    require(isinstance(affinity, list) and all(type(cpu) is int and cpu >= 0 for cpu in affinity)
            and len(set(affinity)) == len(affinity) and state["workers"] <= len(affinity) <= 4,
            "invalid recorded CPU affinity")
    require(state.get("hardware_changed") is False and state.get("default_changed") is False,
            "unsupported campaign hardware/default mutation")
    cached_proof = contract.validate_timing(records, state["workers"], state["boot_id"],
        bounds=(state["monotonic_start_ns"], state["monotonic_end_ns"]))
    cached_proof["barriers_verified"] = True
    require(cached.get("monotonic_proof") == state.get("monotonic_proof") == cached_proof,
            "cached monotonic proof differs from actual records")
    negative = [r for r, s in zip(records, specs) if s["negative"]]
    recovery = [r for r, s in zip(records, specs) if s["phase"] == "recovery"]
    require(len(negative) == len(recovery) == 1, "negative/recovery inventory")
    rejected, restored = negative[0], recovery[0]
    contract.validate_recovery(rejected, restored)
    neg_spec = next(s for s in specs if s["negative"])
    detail = rejected["negative_details"]
    require(int(detail["pc"], 16) == p.a.negative_target(neg_spec["image"])
            and detail["vd"] == 0 and detail["word"] == "0x0388000b" and detail["bit"] == 100,
            "negative actual candidate dot differs")
    require(rejected["status"] == m.NEGATIVE_PASS and restored["status"] == m.NORMAL_PASS
            and rejected["image_sha256"] == restored["image_sha256"]
            and rejected["path"] == restored["path"] and rejected["pid"] != restored["pid"],
            "same-image recovery identity differs")
    normals = [r for r, s in zip(records, specs) if not s["negative"]]
    require(len(normals) == 32 and sum(len(r["samples"]) for r in normals) == 768,
            "normal record/window inventory")
    require(cached["negative"] == rejected and cached["runs"] == normals
            and read(campaign/"completed-runs.json") == normals, "cached records differ from actual receipts")
    summary, decisions, replay_equal = p.evaluate(normals, images, m)
    require(summary["measured_windows"] == 384 and len(summary["rows"]) == 4, "formal statistics inventory")
    verify_summary(cached, summary)
    require(cached["decisions"] == decisions and state["all_window_replay"] is replay_equal
            and cached["all_window_replay"] is replay_equal,
            "cached shape decisions/replay differ")
    require(cached["default_changed"] is False and cached["historical_pass_reused"] is False,
            "unsupported default or historical runtime qualification")
    # Recompute exact whole sample dictionaries for all 8 replay images.
    originals = {(r["variant"], r["shard"], r["dataset"]): r for r in normals if r["replay"] == 0}
    replays = [r for r in normals if r["replay"] == 1]
    require(len(originals) == 24 and len(replays) == 8
            and {(r["variant"], r["shard"], r["dataset"]) for r in replays} ==
                {(v, s, 0) for v in ("firstdot", "config-reuse") for s in (1, 3, 5, 7)},
            "replay inventory differs")
    replay_pairs = [dict(name=r["name"], equal=r["samples"] ==
        originals[(r["variant"], r["shard"], r["dataset"])]["samples"], windows=24) for r in replays]
    require(replay_equal is all(row["equal"] for row in replay_pairs), "replay result differs")
    # Firstdot is freshly executed: compare its 12 exact BIN controls against
    # qualified clean baseline; differences remain explicit decisions, not hidden.
    baseline = {(r["shard"], r["dataset"]): r for r in p.baseline_records
                if r["variant"] == "firstdot" and r["replay"] == 0}
    firstdot = [r for r in normals if r["variant"] == "firstdot" and r["replay"] == 0]
    require(len(firstdot) == len(baseline) == 12, "firstdot baseline control inventory")
    controls = []
    for record in firstdot:
        prior = baseline[(record["shard"], record["dataset"])]
        require(record["image_sha256"] == prior["image_sha256"], "firstdot baseline BIN differs")
        controls.append(dict(name=record["name"], windows=24, equal=record["samples"] == prior["samples"]))
    verify_common(m, common, expected_common)
    require(p.physical() == physical_before, "physical identity changed during audit")
    evidence_after = tree_seal(campaign)
    require(evidence_after == evidence_before, "campaign evidence changed during read-only audit")
    return dict(status="EXPANDED_MATRIX_LOCAL_RAW_AUDIT_PASS", contract=contract.CONTRACT,
        campaign=str(campaign), build=str(build), new_emu_runs=0, new_nemu_runs=0,
        actual_target_processes=33, normal_processes=32, formal_windows=384, normal_all_windows=768,
        replay_window_pairs=192, baseline_firstdot_windows=288, firstdot_controls=controls,
        replay_controls=replay_pairs, all_window_replay=replay_equal, decisions=decisions,
        timing=timing, functional_status="FUNCTIONAL_PASS",
        complete_runtime_input_closure=True, private_process_inputs_verified=True,
        campaign_evidence_unchanged=True, campaign_evidence_sha256=evidence_before,
        source_hardware_remeasured=False, portable_archive_audited=False,
        default_changed=False, records=[dict(label=s["label"], **r["audit"]) for s, r in zip(specs, checked)])


def main():
    parser = argparse.ArgumentParser()
    for name in ("repo", "identity", "matrix", "matrix-run", "build", "campaign", "output"):
        parser.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args()
    import matrix
    require(not args.output.exists(), "new audit output required")
    destination = args.output.resolve()
    require(not any(destination.is_relative_to(root.resolve()) for root in (args.build, args.campaign)),
            "audit output must be outside immutable build/campaign evidence")
    p = matrix.Matrix(args.repo, args.identity, args.matrix, args.matrix_run)
    result = audit_matrix(p, args.build, args.campaign)
    with args.output.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({k: result[k] for k in ("status", "actual_target_processes", "normal_all_windows")}))


if __name__ == "__main__":
    main()
