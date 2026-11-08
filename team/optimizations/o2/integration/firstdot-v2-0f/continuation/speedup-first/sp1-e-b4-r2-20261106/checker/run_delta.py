"""Single frozen fail-stop delta gate; no target or native library execution."""
from pathlib import Path
import hashlib, json, time, traceback
HERE = Path(__file__).resolve().parent

def pin(p):
    p = Path(p)
    return {"path": str(p), "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
def verify(items):
    for x in items:
        assert pin(x["path"]) == x, x["path"]
def save(p, value): p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

def main():
    out = HERE / "attempt-01"; out.mkdir(exist_ok=False)
    start = time.monotonic(); result = {"status": "RUNNING", "checks": [], "target_processes_started": 0, "native_library_loads": 0, "automatic_retry": False, "actual_prior_target_FAIL_changed": False}
    frozen = json.loads((HERE.parent / "o2-control/SOURCE_FREEZE.json").read_text())
    result["source_freeze"] = pin(HERE.parent / "o2-control/SOURCE_FREEZE.json")
    try:
        verify(frozen["files"])
        import test_raw_dst as tests
        rows = tests.controls()
        for name, reject, callback in rows:
            before = time.monotonic()
            try:
                value = callback()
            except ValueError as exc:
                if not reject: raise
                if name.startswith("current_custom_dst_") and name != "current_custom_dst_17_rejected":
                    assert str(exc) == "current group architectural destination", str(exc)
                value = {"rejection": str(exc)}
            else:
                if reject: raise AssertionError("negative accepted: " + name)
            result["checks"].append({"name": name, "status": "PASS", "expected_reject": reject, "elapsed_seconds": time.monotonic()-before, "evidence": value})
            save(out / "PARTIAL.json", result)
            print(json.dumps({"name": name, "status": "PASS"}), flush=True)
        verify(frozen["files"])
        result["status"] = "PASS_B4_R2_RAW_DST_HOST_DELTA"
    except BaseException as exc:
        result.update(status="FAIL_B4_R2_RAW_DST_HOST_DELTA", error=str(exc), traceback=traceback.format_exc())
    result["completed_controls"] = len(result["checks"])
    result["elapsed_seconds"] = time.monotonic()-start
    result["scope"] = "new-source pure-host reinterpretation and delta controls; original target remains STOPPED, no target qualification"
    save(out / "RESULT.json", result)
    print(json.dumps({"status": result["status"], "count": result["completed_controls"], "elapsed_seconds": result["elapsed_seconds"]}))
    return 0 if result["status"].startswith("PASS_") else 1

if __name__ == "__main__": raise SystemExit(main())
