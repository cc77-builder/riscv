"""Independent o2-control numeric calibration; no native execution or old module edits."""
from pathlib import Path
import copy, hashlib, importlib.util, json, re
HERE = Path(__file__).resolve().parent
CONTRACT = json.loads((HERE / "CONTRACT.json").read_text())
CASE_ID = "o2-control"
STATUS = "B4_CALIBRATION_NUMERIC_LOG_PASS"

def need(ok, message):
    if not ok: raise ValueError(message)

def pin(path):
    path = Path(path)
    return {"path": str(path), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

def check_pin(item):
    need(pin(item["path"]) == item, "input bytes/hash changed: " + item["path"])

for item in CONTRACT["input_files"]: check_pin(item)
spec = importlib.util.spec_from_file_location("b4_r4_numeric_legacy", CONTRACT["old_collector"]["path"])
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)

def descriptor():
    legacy.descriptor(CASE_ID)
    summary_path = HERE / "HISTORICAL_CANDIDATE_SUMMARY.json"
    need(summary_path.is_file(), "historical numeric summary not prepared")
    out = {key: copy.deepcopy(CONTRACT[key]) for key in
           ("case_id", "runtime", "input_files", "normal_pass_status", "negative_pass_status",
            "comparison_fields", "coverage", "negative_environment")}
    out["input_files"] += [pin(HERE / name) for name in
                           ("adapter.py", "history.py", "CONTRACT.json", "HISTORICAL_CANDIDATE_SUMMARY.json")]
    out["historical_candidate_summary"] = pin(summary_path)
    out["calibration_only"] = True
    out["full_case_qualified"] = False
    out["formal_acceptance_qualified"] = False
    return out

def coverage_snapshot(counts, fu_counts):
    required = CONTRACT["coverage"]["required_counts"]
    checks = {key: counts.get(key, 0) >= minimum for key, minimum in required.items()}
    checks["required_fu_classes"] = all(fu_counts.get(fu, 0) > 0 for fu in CONTRACT["coverage"]["required_fu"])
    need(checks["COMMIT"] and checks["required_fu_classes"], "numeric required retirement/FU coverage")
    missing = [key for key in ("KILL_P", "KILL_R", "PARTIAL_KILL") if not checks[key]]
    return checks, missing

def collect(text, case_id, mode, reference, exit_code, run_id, scope="TARGET_LOG_REQUIRES_RUNTIME_RECEIPT"):
    """Same original numeric checks; named internal coverage is recorded, never waived into formal PASS."""
    need(case_id == CASE_ID, "numeric adapter case must be o2-control")
    need(scope in legacy.SCOPES and isinstance(run_id, str) and bool(run_id), "explicit scope/run id")
    c = legacy.descriptor(case_id)
    plain, obs, a, events, uart = legacy.decode_observer(text, mode)
    legacy.image_gate(plain, c, reference, False)
    m = json.loads(Path(c["manifest"]["path"]).read_text())
    work = legacy.legacy_adapter.check(plain, m, exit_code, mode, c["kind"], reference)
    coverage, missing = coverage_snapshot(a["counts"], a["vfex4_fu_counts"])
    arch = legacy.bind_architecture(events, c)
    need(len(arch) == c["expected_commits"], "exact architectural commit count")
    need(work["workload"]["checked_register_bytes"] == c["checked_register_bytes"], "complete target register checks")
    guest = re.findall(r"Guest cycle spent:\s*([0-9]+)", uart)
    instr = re.findall(r"Core-0 instrCnt = ([0-9]+), cycleCnt = ([0-9]+)", uart)
    need(len(guest) == len(instr) == 1, "single completion counter receipt")
    markers = [line for line in uart.splitlines() if re.match(r"^(?:T12_|O2_DIAG_|O2_CONTROL_)", line)]
    need(markers, "nonempty ordered workload checks")
    dividends = [(kind, fields) for _, _, kind, fields in events if kind.startswith("DIV_")]
    need(dividends, "required DIV records")
    material = {
        "architectural_commit": [{"pc": x["pc"], "word": x["word"], "vd": x["vd"], "vl": x["vl"]} for x in arch],
        "source": [[x["vs1"], x["vs2"]] for x in arch],
        "result": [[x["result"], x["exception"]] for x in arch],
        "observer": events, "uart_checks": markers,
        "csr_contract": {"frozen_image": c["bin"]["sha256"], "target_checks": c["csr_contract"], "workload_markers": markers},
        "div_events": dividends,
        "completion": {"guest_cycles": int(guest[0]), "instr_count": int(instr[0][0]), "cycle_count": int(instr[0][1])}}
    return {
        "status": STATUS, "case_id": case_id, "mode": mode, "scope": scope, "run_id": run_id,
        "bin_sha256": c["bin"]["sha256"], "elf_sha256": c["elf"]["sha256"], "manifest_sha256": c["manifest"]["sha256"],
        "reference_sha256": legacy.CONTRACT["normal_reference"]["sha256"],
        "raw_sha256": hashlib.sha256(text.encode()).hexdigest(), "observer_status": a["status"],
        "counts": a["counts"], "coverage": coverage, "coverage_missing": missing, "fu_counts": a["vfex4_fu_counts"],
        "commits": len(arch), "checked_register_bytes": c["checked_register_bytes"], "csr_contract": c["csr_contract"],
        "accepted_source_arithmetic_full128_count": a["counts"]["ACCEPT"], "workload": work["workload"],
        "functional_replay": {key: legacy.digest(material[key]) for key in legacy.REPLAY_KEYS},
        "cross_hardware_architecture": legacy.digest(arch),
        "samples": {"status": "NOT_APPLICABLE_FUNCTIONAL_IMAGE", "event_count": 0},
        "counter_events": {"status": "NOT_APPLICABLE_FUNCTIONAL_IMAGE", "event_count": 0},
        "guest_cycles": int(guest[0]), "performance_measured": False, "performance_2_percent_qualified": False,
        "target_run_qualified": False, "requires_runtime_receipt": True,
        "full_case_qualified": False, "fullcore_coverage_qualified": False,
        "formal_acceptance_qualified": False, "performance_qualified": False,
        "calibration_numeric_only": True,
        "original_coverage_contract_unchanged": True,
        "adapter_contract_sha256": pin(HERE / "CONTRACT.json")["sha256"],
        "numeric_scope": "Observer recomputes accepted-source dot full128; complete registers/final CSR rely on frozen target self-check plus live DiffTest, not printed per-trial numeric dumps."}
