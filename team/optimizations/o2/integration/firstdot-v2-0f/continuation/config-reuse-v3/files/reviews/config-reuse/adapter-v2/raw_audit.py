"""Reparse existing local transcripts without starting EMU or changing receipts.

This audits local raw evidence. It is not a portable archive extractor and does
not claim to re-measure hardware or regain missing historical physical files.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import json
import shutil
import tempfile

from probe import CONTRACT, read, sha, require


def times(record):
    start, finish = (datetime.fromisoformat(record[k]) for k in ("started","finished"))
    require(start.utcoffset() is not None and finish.utcoffset() is not None and start <= finish,
            "invalid execution chronology")
    return start, finish


def complete_common(p, build, images, m, physical):
    """Reconstruct exactly the input map captured by Probe.run."""
    files = physical[1] | m.checker_files(p.repo)
    for filename in ("probe-build.json", "state.json", "images.json", "pairs.json", "baseline-current.json"):
        files[str(build / filename)] = sha(build / filename)
    for image in images:
        for filename in ("build.json", "data/manifest.json"):
            files[str(Path(image["path"]) / filename)] = sha(Path(image["path"]) / filename)
    return files


def verify_common(m, recorded, expected):
    require(recorded == expected, "complete runtime input closure differs")
    m.verify_files(expected)


def record_audit(repo, g, f, m, cfg, image, directory, common, outer_contract,
                 replay=0, negative=False, fixture=None, expected_cwd=None):
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
    times(record)
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
    expected_inputs = dict(common) | local_inputs
    require(record["files"] == expected_inputs, "runtime input inventory drift")
    # audit_probe verifies the complete shared map once before and after all five
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


def audit_probe(p, build, campaign):
    build, campaign = Path(build).resolve(), Path(campaign).resolve()
    images = p.selected(build)
    f,m = p.runtime()
    state, cached = read(campaign/"state.json"),read(campaign/"results.json")
    require(state["contract"] == cached["contract"] == CONTRACT
            and state["new_emu_runs"] == cached["new_emu_runs"] == 5
            and state["functional_status"] == cached["functional_status"] == "FUNCTIONAL_PASS",
            "probe completion contract")
    require(cached["parent_identity_sha256"] == sha(p.identity_path)
            and cached["current_precondition"] == p.precondition, "probe clean/baseline identity")
    require(read(campaign/"parent-identity.json") == p.identity, "copied clean identity differs")
    require(read(campaign/"hardware-profile.json") == p.identity["hardware_profile"], "profile receipt differs")
    cfg, common = read(campaign/"configuration.json"),read(campaign/"runtime-inputs.json")
    require(cfg == p.identity["configuration"], "campaign configuration differs")
    before = p.physical()
    require(before[0] == p.identity and before[2] == p.identity["hardware_profile"],
            "physical clean identity differs")
    expected_common = complete_common(p, build, images, m, before)
    verify_common(m, common, expected_common)
    names = ("negative-config-reuse","recovery-config-reuse","formal-firstdot",
             "replay-firstdot","replay-config-reuse")
    require({q.name for q in (campaign/"runs").iterdir()} == set(names), "missing/extra probe process")
    fixture = read(campaign/"negative-fixture/fixture.json")
    require(sha(fixture["binary"]) == fixture["negative_sha256"], "local fault fixture digest")
    chosen = {i["variant"]:i for i in images}
    modes = (("config-reuse",0,True),("config-reuse",0,False),("firstdot",0,False),
             ("firstdot",1,False),("config-reuse",1,False))
    checked = []
    for label,(variant,replay,negative) in zip(names,modes):
        checked.append(record_audit(p.repo,p.g,f,m,cfg,chosen[variant],campaign/"runs"/label,common,
            CONTRACT,replay,negative,fixture if negative else None))
    records = [v["record"] for v in checked]
    require(len({r["pid"] for r in records}) == 5, "five distinct process IDs required")
    require(state.get("active_pid") is None and times(state)[0] <= times(records[0])[0]
            and times(records[-1])[1] <= times(state)[1], "campaign/process time bounds")
    for before,after in zip(records,records[1:]):
        require(times(before)[1] <= times(after)[0], "nonserial/reversed probe chronology")
    rejected,normal = records[0],records[1:]
    detail = rejected["negative_details"]
    require(int(detail["pc"],16) == p.a.negative_target(chosen["config-reuse"])
            and detail["vd"] == 0 and detail["word"] == "0x0388000b" and detail["bit"] == 100,
            "raw negative first actual candidate dot")
    m.validate_recovery(rejected,normal[0])
    require(cached["negative"] == rejected and cached["runs"] == normal
            and read(campaign/"completed-runs.json") == normal, "cached process set differs from raw")
    summary,decision,replay_equal = p.evaluate(normal,images,m)
    require(all(cached[k] == v for k,v in summary.items()), "cached statistics differ from raw")
    require(cached["performance"] == decision and cached["status"] == state["status"] == decision["decision"]
            and state["all_window_replay"] is replay_equal, "cached decision differs from raw")
    require(cached["default_changed"] is False and cached["historical_pass_reused"] is False,
            "unsupported default/historical qualification")
    verify_common(m, common, expected_common)
    require(p.physical() == before, "physical clean identity changed during audit")
    return dict(status="PROBE_LOCAL_RAW_AUDIT_PASS",contract=CONTRACT,new_emu_runs=0,
        complete_runtime_input_closure=True, physical_common_inputs_verified=True,
        private_process_inputs_verified=True,
        source_hardware_remeasured=False,portable_archive_audited=False,
        campaign=str(campaign),build=str(build),records=[v["audit"] for v in checked],
        functional_status="FUNCTIONAL_PASS",performance=decision,
        measured_windows=summary["measured_windows"],normal_all_windows=96)
