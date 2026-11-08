"""Fixed R2 actual evidence reuse; original execution boot, never current audit boot."""
from pathlib import Path
import copy, hashlib, json
HERE = Path(__file__).resolve().parent
CONTRACT = json.loads((HERE / "CONTRACT.json").read_text())

def need(ok, message):
    if not ok: raise ValueError(message)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def identity_semantics(bundle):
    r, launch, identity = (bundle[k] for k in ("record", "launch", "identity"))
    guard, claim, terminal = (bundle[k] for k in ("guard", "claim", "terminal"))
    d = bundle["freeze"]["contract"]; auth = bundle["authorization"]
    boot = r["boot_id"]
    need(isinstance(boot, str) and boot and launch["boot_id"] == guard["boot_id"] == claim["boot_id"] == terminal["execution_boot"] == boot, "historical execution boot binding")
    need(r["role"] == launch["role"] == "candidate-full" and r["exit_code"] == 0, "historical normal role/exit")
    need(r["execution_identity"] == identity, "historical recorded identity")
    proc = identity["process"]
    need(identity["pid"] == r["pid"] == proc["pid"] == proc["sid"] == proc["pgid"], "historical owned PID/PGID/SID")
    need(proc["start_ticks"] == r["known_pid_start_ticks"][str(r["pid"])], "historical PID birth")
    observed = {(x["process"]["pid"], x["process"]["start_ticks"]) for x in guard["events"] if x.get("event") == "owned_process_observed"}
    need((r["pid"], proc["start_ticks"]) in observed, "guardian historical target birth")
    need(identity["executable"] == d["runtime"]["candidate_emu"]["path"] and identity["executable_sha256"] == d["runtime"]["candidate_emu"]["sha256"], "historical EMU identity")
    command = [d["runtime"]["candidate_emu"]["path"], "-i", d["runtime"]["bin"]["path"], "--flash="+d["runtime"]["flash"]["path"], "--ram-size=128MB", "--diff="+d["runtime"]["normal_reference"]["path"], "--max-cycles=1499984", "--seed=1", "--no-snapshot"]
    need(identity["command"] == r["command"] == launch["command"] == command, "historical exact argv")
    need(identity["cwd"] == r["cwd"] == launch["cwd"] == d["runtime_cwd"]["candidate"], "historical cwd")
    need(identity["environment"] == launch["env"], "historical sanitized environment")
    need(identity["process"]["tids"] and all(x["cpu_affinity"] == "4" for x in identity["process"]["tids"]), "historical CPU4")
    need(r["process_started"] is True and r["resource_ok"] is True and r["cleanup_ok"] is True and r["exception"] is None and r["cleanup_error"] is None and r["limit"] is None and r["stop_reason"] is None, "historical successful resource/cleanup")
    need(not r["final_snapshot"]["processes"] and guard["cleanup_ok"] and not guard["remaining_live_processes"], "historical whole-group cleanup")
    need(r["raw_truncated"] is False and r["observed_bytes"] == r["retained_bytes"], "historical complete raw")
    need(r["limits"] == launch["limits"] and r["limits"]["wall_seconds"] == 2400 and r["limits"]["guest_cycles"] == 1500000 and r["limits"]["cpu_affinity"] == [4] and r["limits"]["thread_cap"] == 4 and r["limits"]["rss_cap_bytes"] == 12884901888, "historical resource contract")
    need(0 < r["guest_cycles"] <= 1500000 and 0 <= r["active_wall_seconds"] <= r["elapsed_seconds"] <= 2400 and r["peak_threads"] <= 4 and r["peak_rss_bytes"] <= 12884901888, "historical resource bounds")
    need(abs(r["elapsed_seconds"] - r["ended_monotonic"] + r["started_monotonic"]) < 1e-6, "historical same-boot duration")
    ref = d["runtime"]["normal_reference"]["path"]
    need(r["observed_mapped_files"].get(ref, {}).get("pid") == r["pid"], "historical normal reference mapping")
    roles = [x for x in terminal["roles"] if x["case_id"] == "o2-control" and x["role"] == "candidate-full"]
    need(len(roles) == 1 and roles[0]["status"] == "PASS_RUNTIME_RECEIPT_LOG_UNQUALIFIED" and roles[0]["pid"] == r["pid"] and roles[0]["start_ticks"] == proc["start_ticks"] and roles[0]["boot_id"] == boot, "original independent runtime receipt")
    need(terminal["status"] == "READ_ONLY_STOPPED_CALIBRATION_EVIDENCE" and not terminal["errors"] and terminal["native_batch_status"] == "STOPPED" and guard["status"] == "GUARD_FAIL" and guard["reason"] == "CHILD_EXIT_1", "old FAIL retained, not promoted")
    need(bundle["partial"]["missing_coverage"] == ["KILL_P", "PARTIAL_KILL"] and bundle["partial"]["coverage_override"] is False, "original coverage failure scope")
    need(claim["authorization_sha256"] == CONTRACT["historical_sources"]["authorization"]["sha256"] and auth["case_ids"] == claim["case_ids"] == ["o2-control", "original-c8-c48"], "historical consumed authorization")
    frozen = CONTRACT["historical_sources"]["freeze"]
    need(auth["cases"][0]["freeze"] == frozen, "historical execution freeze binding")
    return {"status": "HISTORICAL_ACTUAL_IDENTITY_BOUND", "boot_id": boot, "pid": r["pid"], "start_ticks": proc["start_ticks"], "original_run_id": "o2-control:candidate-full:"+str(r["pid"])+":"+boot, "guest_cycles": r["guest_cycles"], "active_wall_seconds": r["active_wall_seconds"], "current_boot_compared": False, "original_coverage_fail_preserved": True}

def load_fixed_history(check_pin):
    sources = CONTRACT["historical_sources"]
    for row in CONTRACT["input_files"]: check_pin(row)
    bundle = {key: json.loads(Path(row["path"]).read_text()) for key,row in sources.items() if Path(row["path"]).suffix == ".json"}
    identity = identity_semantics(bundle)
    for stream in ("stdout", "stderr"):
        row = sources[stream]
        need(row["sha256"] == bundle["record"]["raw_sha256"][stream] and row["bytes"] == bundle["record"]["retained_bytes"][stream], "historical raw receipt binding")
    text = Path(sources["stdout"]["path"]).read_text()+Path(sources["stderr"]["path"]).read_text()
    return bundle, identity, text

def make_summary(collector, identity):
    need(collector["status"] == "B4_CALIBRATION_NUMERIC_LOG_PASS" and collector["scope"] == "HISTORICAL_LOG" and collector["mode"] == "candidate" and collector["case_id"] == "o2-control", "historical numeric invocation")
    need(collector["run_id"] == identity["original_run_id"] and collector["coverage_missing"] == ["KILL_P", "PARTIAL_KILL"], "historical summary identity/coverage")
    need(all(collector[key] is False for key in ("full_case_qualified", "fullcore_coverage_qualified", "formal_acceptance_qualified", "performance_qualified", "target_run_qualified")), "numeric summary cannot grant formal qualification")
    return {"schema":"b4-r4-historical-numeric-summary-v1", "status":"B4_HISTORICAL_CANDIDATE_NUMERIC_READY", "case_id":"o2-control", "reused":True, "collector":copy.deepcopy(collector), "collector_digest":digest(collector), "source_runtime_receipt":copy.deepcopy(CONTRACT["historical_sources"]), "history_identity":copy.deepcopy(identity), "coverage_missing":list(collector["coverage_missing"]), "full_case_qualified":False, "formal_acceptance_qualified":False, "performance_qualified":False, "target_execution_authorized":False, "qualification":"Original actual runtime evidence plus new numeric-only log review; prior batch/coverage FAIL remains; no new target or replay."}
