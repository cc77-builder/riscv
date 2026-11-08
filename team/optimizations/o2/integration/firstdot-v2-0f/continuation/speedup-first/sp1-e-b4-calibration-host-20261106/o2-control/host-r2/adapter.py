"""B4 o2-control pure-host adapter. Never execute EMU/NEMU or load a native library."""
from pathlib import Path
import copy, hashlib, importlib.util, json, re
HERE = Path(__file__).resolve().parent
CONTRACT = json.loads((HERE / "CONTRACT.json").read_text())
CASE_ID = "o2-control"

def need(ok, message):
    if not ok:
        raise ValueError(message)

def check_pin(item):
    path = Path(item["path"])
    need(path.is_file() and path.stat().st_size == item["bytes"] and
         hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"],
         "input bytes or hash changed: " + str(path))

for _pin in CONTRACT["input_files"]:
    check_pin(_pin)
_spec = importlib.util.spec_from_file_location("b4_o2_strict_r7_helper", CONTRACT["strict_group_helper"]["path"])
strict = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(strict)
legacy = strict.legacy
_prefix_spec = importlib.util.spec_from_file_location("b4_o2_prefix_group", str(HERE / "prefix_group.py"))
prefix = importlib.util.module_from_spec(_prefix_spec)
_prefix_spec.loader.exec_module(prefix)
validate_group = prefix.configure(strict)
need(tuple(strict.CASE_IDS) == ("legacy-control", "o2-all-pairs"), "original helper whitelist must remain unchanged")

def descriptor():
    """Frozen workload inputs; root owns shared runtime and new stop-limit proposal."""
    legacy.descriptor(CASE_ID)
    out = {key: copy.deepcopy(CONTRACT[key]) for key in
           ("case_id", "runtime", "input_files", "normal_pass_status", "negative_pass_status", "comparison_fields", "coverage")}
    out["input_files"] += [
        {"path": str(HERE / name), "bytes": (HERE / name).stat().st_size,
         "sha256": hashlib.sha256((HERE / name).read_bytes()).hexdigest()}
        for name in ("adapter.py", "CONTRACT.json", "prefix_group.py")]
    out["negative_environment"] = dict(CONTRACT["bit100"]["environment"])
    out["historical"] = copy.deepcopy(CONTRACT["historical"])
    out["calibration_proposal"] = copy.deepcopy(CONTRACT["calibration_proposal"])
    return out

def collect(text, case_id, mode, reference, exit_code, run_id, scope="TARGET_LOG_REQUIRES_RUNTIME_RECEIPT"):
    need(case_id == CASE_ID, "B4 adapter case must be o2-control")
    result = legacy.collect(text, case_id, mode, reference, exit_code, run_id, scope)
    result["adapter_contract_sha256"] = hashlib.sha256((HERE / "CONTRACT.json").read_bytes()).hexdigest()
    return result

def negative(text, case_id, mode, reference, exit_code, run_id, scope="TARGET_LOG_REQUIRES_RUNTIME_RECEIPT"):
    need(case_id == CASE_ID, "B4 adapter case must be o2-control")
    need(mode == "candidate", "negative role uses candidate hardware")
    need(scope in legacy.SCOPES and isinstance(run_id, str) and bool(run_id), "explicit scope/run id")
    case = legacy.descriptor(case_id)
    plain, obs, analysis, events, uart = legacy.decode_observer(text, mode, False)
    legacy.image_gate(plain, case, reference, True)
    _, elf_read = legacy.legacy_windows.elf_data(case["elf"]["path"])
    fault = validate_group(plain, exit_code, case["bit100"], elf_read, events)
    architecture = legacy.bind_architecture(events, case)
    need(architecture[0]["pc"] == case["bit100"]["pc"], "first actual custom fault")
    need(not re.search(r"T12_SUMMARY|O2_DIAG_SUMMARY|O2_CONTROL_SUMMARY", uart), "negative stops before successful completion")
    return {"status": "B3_BIT100_LOG_PASS", "case_id": case_id, "mode": mode,
            "run_id": run_id, "scope": scope, "fault": fault,
            "reference_sha256": case["negative_reference"]["sha256"],
            "raw_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "target_run_qualified": False, "requires_runtime_receipt": True,
            "adapter_contract_sha256": hashlib.sha256((HERE / "CONTRACT.json").read_bytes()).hexdigest(),
            "strict_group_helper_sha256": CONTRACT["strict_group_helper"]["sha256"],
            "qualification": "o2-control log qualification only; actual identity/resource/cleanup receipts required"}
