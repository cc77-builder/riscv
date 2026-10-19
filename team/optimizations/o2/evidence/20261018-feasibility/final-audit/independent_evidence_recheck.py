from pathlib import Path
import json,hashlib,gzip,collections,subprocess,shutil
repo=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
base=repo/"team/optimizations/o2"
result_path=base/"evidence/20261018-feasibility/with-allocation-fate/trace-result.json"
d=json.loads(result_path.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
archive=repo/"team/optimizations/o1/evidence/20261018-performance-ab"
assert sha(archive/"archive-manifest.json")==d["archive_manifest_sha256"]
for name,pin in d["input_files"].items():
    p=archive/name
    blob=p.read_bytes()
    assert hashlib.sha256(blob).hexdigest()==pin["stored_sha256"]
    assert len(blob)==pin["stored_bytes"]
    raw=gzip.decompress(blob) if name.endswith(".gz") else blob
    assert hashlib.sha256(raw).hexdigest()==pin["original_sha256"]
    assert len(raw)==pin["original_bytes"]
assert d["analyzer_sha256"]==sha(base/"analyze_trace.py")
assert len(d["jobs"])==24 and len(d["windows"])==96
keys=set()
for w in d["windows"]:
    key=tuple(w[k] for k in ("mode","scenario","dataset","repeat"))
    assert key not in keys
    keys.add(key)
    assert w["cycles"]==w["global_stop_exclusive"]-w["global_start_inclusive"]
    assert w["counts"]["ACCEPT"]==w["counts"]["RESPONSE"]==w["counts"]["COMMIT"]==w["dots"]
    assert not any(w["boundary_audit"].values())
    assert sum(w["vdot_wait_by_allocation_fate"].values())==sum(w["vdot_wait_by_busy"].values())
    assert set(w["vdot_wait_by_allocation_fate"])<={"accepted_and_committed_in_window","cancelled_before_accept"}
for row in d["summary"]:
    ws=[w for w in d["windows"] if w["scenario"]==row["scenario"] and w["mode"]==row["mode"]]
    assert len(ws)==12
    assert row["mean_cycles"]==sum(w["cycles"] for w in ws)/12
    for name in ("counts","vdot_wait_by_allocation_fate","vdot_wait_by_busy","accept_gap_histogram","response_latency_histogram","boundary_audit"):
        keys=set().union(*(w[name] for w in ws))
        expected={k:sum(w[name].get(k,0) for w in ws) for k in keys}
        assert row[name]==expected
batch=next(r for r in d["summary"] if r["scenario"]=="batch" and r["mode"]=="o1")
assert batch["vdot_wait_by_allocation_fate"]=={"accepted_and_committed_in_window":1266,"cancelled_before_accept":9}
assert sum(batch["accept_gap_histogram"].values())==1524
work=Path("/home/riscv/riscv-lab/o2-feasibility-20261018")
pins=json.loads((work/"WORK_STATE.json").read_text())
for path,expected in pins["source_pins"].items(): assert sha(repo/path)==expected
subprocess.run(["git","diff","--exit-code",pins["base_commit"],"--","src","team/spec","team/models"],cwd=repo,check=True)
print(json.dumps({"status":"INDEPENDENT_EVIDENCE_RECHECK_PASS","verified_input_files":len(d["input_files"]),"formal_windows":96,"jobs":24,"useful_batch_wait_cycles":1266,"speculative_batch_wait_cycles":9,"production_source_unchanged":True,"new_emu_executed":False}))
