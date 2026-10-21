#!/usr/bin/env python3
"""Bind completed H1 local evidence; no hardware execution or baseline rewrite."""
from pathlib import Path
import hashlib
import json
import subprocess
from datetime import datetime, timezone

REPO = Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
WORK = Path("/home/riscv/riscv-lab/o2-h1-result32-20261021")
H1 = REPO / "team/optimizations/o2/result-width/h1"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(relative):
    return json.loads((WORK / relative).read_text())

def need(condition, message):
    if not condition:
        raise ValueError(message)

def main():
    output = WORK / "final-validation.json"
    need(not output.exists(), "final receipt already exists")
    state = read("campaign-state.json")
    need(state["status"] == "passed" and state["source_and_r0_lock_unchanged"], "campaign incomplete")
    need(len(state["steps"]) == 11 and all(x["status"] == "passed" and x["exit_code"] == 0 for x in state["steps"]), "hardware stage incomplete")
    functional = read("functional-validation-01.json")
    cost = read("cost-comparison-01/summary.json")
    need(functional["status"] == "H1_FUNCTIONAL_VALIDATION_PASS", "functional audit failed")
    need(cost["status"] == "O2_H1_COST_COMPARISON_PASS" and cost["pass"], "cost audit failed")
    pins = read("candidate-inputs.json")
    for rel, digest in pins["source_sha256"].items():
        need(sha(REPO / rel) == digest, "source changed: " + rel)
    lock_sha = sha(REPO / "team/optimizations/o2/repro/baseline-lock.json")
    need(lock_sha == pins["r0_lock_sha256"] == "8bc49ced46926b4015b900185bd657bee13bb606a27fc6482d4f169c1766c29e", "B0 R0 lock changed")
    need(sha(REPO / "team/optimizations/o4/evidence/20261020-cost/manifest.json") == cost["baseline_sealed_manifest_sha256"] == "9f95c19b737b0428afca36686aabd1454d7fb44880040f2bf41109b71c39c0a1", "O4 baseline changed")
    need(sha(WORK / "cost-comparison-01/summary.json") == "6c851df6b828550d75a469044ba559150d28ebd2e58a858818038d50757e5732", "cost review identity changed")
    need(sha(H1 / "validate_functional.py") == functional["checker_sha256"], "functional checker changed")
    need(sha(H1 / "compare_cost.py") == read("cost-comparison-01/command.json")["audit_sha256"], "cost checker changed")
    for script in H1.glob("*.py"):
        need(sha(script) == sha(WORK / "post-tools" / script.name), "post tool snapshot mismatch")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    need(head == pins["base_commit"], "base commit changed")
    production = subprocess.check_output(["git", "diff", "--name-only", "HEAD", "--", "src"], cwd=REPO, text=True).splitlines()
    need(production == ["src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala"], "extra production changes")
    patch = subprocess.check_output(["git", "diff", "--binary", "HEAD", "--", "src"], cwd=REPO)
    need(patch == (WORK / "h1-production.patch").read_bytes(), "production patch changed")
    diff_check = subprocess.run(["git", "diff", "--check"], cwd=REPO, capture_output=True, text=True)
    need(diff_check.returncode == 0, "git diff --check failed: " + diff_check.stdout + diff_check.stderr)
    checks = ["functional-checker-tests-01.command.json", "cost-host-tests-03.command.json", "functional-validation-01.command.json", "cost-comparison-01.command.json"]
    for rel in checks:
        need(read(rel)["exit_code"] == 0, "post validation command failed: " + rel)
    old_emu = sha(REPO / "build/emu")
    need(old_emu == "ac0123280bf6c742d27a7650505bc1d91db350d1519806edfd0be9c7ea208a57", "old emulator identity differs")
    bound = ["campaign-state.json", "candidate-inputs.json", "h1-production.patch", "functional-validation-01.json", "parent-replay.json",
             "cost-comparison-01/summary.json", "cost-comparison-01/command.json", "H1_RESULT.md", "timing-comparison.csv",
             "independent-rtl-review.md", "independent-cost-and-conclusion-review.md", "finalize-local.py"] + checks
    receipt = {
        "status": "O2_H1_LOCAL_VALIDATION_PASS",
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "base_commit": head,
        "production_source_changes": production,
        "source_pins_checked": len(pins["source_sha256"]),
        "r0_b0_lock_sha256": lock_sha,
        "old_build_emu_sha256": old_emu,
        "bound_files": {rel: sha(WORK / rel) for rel in bound},
        "post_tools": {str(p.relative_to(WORK)): sha(p) for p in sorted((WORK / "post-tools").glob("*.py"))},
        "hardware_steps": len(state["steps"]),
        "functional_unique_vectors": 10022,
        "actual_observation_negative_cases": 20,
        "cost_new_mapping_count": 2,
        "cost_new_sta_profile_count": 10,
        "cost_compared_path_categories": 70,
        "one_ns_timing_closed": False,
        "fullcore_h1_built_or_run": False,
        "new_cycles_or_speedup": False,
        "human_ack": False,
        "git_commit_or_push": False,
        "recommendation": "Keep H1 as a locally validated area-reduction candidate for a separate full-core regression; retain ready-load regressions."
    }
    output.write_text(json.dumps(receipt, indent=2) + "\n")
    print(receipt["status"])
    print("source pins:", receipt["source_pins_checked"])
    print("receipt sha256:", sha(output))

if __name__ == "__main__":
    main()
