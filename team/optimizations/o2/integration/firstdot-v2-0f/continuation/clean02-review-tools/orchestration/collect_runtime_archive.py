#!/usr/bin/env python3
"""Seal completed orchestration evidence only; does not create runtime qualification."""
import argparse,gzip,hashlib,importlib.util,json,os
from datetime import datetime,timezone
from pathlib import Path
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,v):
    with p.open("x",encoding="utf-8") as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write("\n")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--work",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);ap.add_argument("--windows-jobs",type=Path,required=True)
    a=ap.parse_args();w=a.work.resolve();c=w/"clean-02";review=w/"reviews/config-reuse";out=a.output.resolve()
    assert out.is_relative_to(w/"reviews") and not out.exists()
    executor=review/"execute_clean02_stage_v2.py"
    spec=importlib.util.spec_from_file_location("review_executor",executor);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    plan_path=review/"clean02-launch-plan-v3.json";plan=read(plan_path)
    m.validate_plan(plan);ready=m.gate_metadata(plan)
    outer=w/"clean-postprocess-03.command.json";assert read(outer)["exit_code"]==0
    assert read(c/"matrix-waiter-01.json")["status"]=="CLEAN_CORE_GATE_AND_MATRIX_PASS"
    files={}
    def add(p,role):
        p=Path(p).absolute();assert p.is_file() and not p.is_symlink(),str(p)
        assert p.stat().st_size<=64*1024*1024,("unexpected large orchestration input",str(p))
        files.setdefault(str(p),set()).add(role)
    def triple(p,role):
        p=Path(p);add(p,role)
        for suffix in (".stdout.log",".stderr.log"):add(p.with_suffix(suffix),role)
    for name in ("run_recorded.py","wait_core_then_matrix.py","finish_clean_validation.py","finish_clean_validation_v2.py","prepare_clean_programs.py","provision_clean.py","continue_provision_clean.py","run_c_independent.py"):
        add(w/name,"driver-source")
    for name in ("clean-02-postbuild-plan.json","clean-02-postbuild-plan-v2.json"):add(w/name,"orchestration-plan")
    for p in ready["completion_receipts"]:triple(p,"completed-command")
    triple(outer,"postprocess-outer-command")
    for p in ready["gate_files"]:add(p,"qualified-result")
    for p in ready["failed_attempts"]:add(p,"preserved-strict-failure")
    add(c/"fullcore-archive-02/archive-manifest.json","semantic-archive-reference")
    add(c/"fullcore-archive-audit-02/current-archive-physical.json","live-raw-proof")
    add(c/"postprocess-02/state.json","completed-control-state")
    add(c/"matrix-waiter-01.json","completed-control-state")
    for n in ("fullcore-run-01/results.json","matrix-run-01/results.json","c-run-01/results.json","c-run-01/combination-c-qualification.json","c-run-01/combination-c-orchestration-proof.json","program-byte-comparison-01.json"):add(c/n,"runtime-summary")
    for p in (c/"combination-audit-02").rglob("*manifest*.json"):
        if p.is_file():add(p,"semantic-archive-reference")
    closure=plan["fullcore_limited_audit"]["runtime_closure"]
    add(closure["path"],"external-audit-runtime")
    for p in closure["files"]:add(p,"external-audit-runtime")
    for name in ("clean-fullcore-audit-v2","clean-fullcore-root-support-01","clean-fullcore-root-support-02","clean-clock-observation-02"):
        for p in (w/"reviews"/name).rglob("*"):
            if p.is_file() and p.suffix in (".json",".md",".py",".log",".txt") and "__pycache__" not in p.parts:add(p,"review-and-clock-limit")
    add(executor,"release-gate-source");add(plan_path,"release-gate-plan")
    add(review/"executor-v2-root-review-01.json","root-source-review")
    add(Path(__file__),"supplement-collector")
    add(a.windows_jobs/"launch_wsl_job.py","windows-launcher")
    for stem in ("clean-matrix-waiter-02","clean-postprocess-02","clean-postprocess-03"):
        add(a.windows_jobs/(stem+".json"),"windows-launch-command")
        p=a.windows_jobs/(stem+".receipt.json");v=read(p)
        assert type(v.get("exit_code")) is int and v.get("finished") and v.get("status") != "RUNNING",("Windows holder not terminal",str(p))
        add(p,"windows-launch-completion")
    out.mkdir();payload=out/"objects";payload.mkdir()
    rows=[]
    for pstr,roles in sorted(files.items()):
        p=Path(pstr);raw=p.read_bytes();digest=sha(raw);packed=gzip.compress(raw,mtime=0);obj=payload/(digest+".gz")
        if not obj.exists():obj.write_bytes(packed)
        stored=obj.read_bytes();assert sha(gzip.decompress(stored))==digest and p.read_bytes()==raw
        rows.append(dict(path=pstr,roles=sorted(roles),raw_sha256=digest,raw_bytes=len(raw),object="objects/"+obj.name,stored_sha256=sha(stored),stored_bytes=len(stored)))
    manifest=dict(contract="clean-runtime-orchestration-supplement-v1",created_at=datetime.now(timezone.utc).isoformat(),status="BYTE_ARCHIVE_ONLY_NO_NEW_RUNTIME_QUALIFICATION",files=rows,release_gate_snapshot=ready,scope="Completed source, actual commands, failures, audit tools and orchestration receipts. Not a replacement for fullcore/matrix semantic archives.",new_emu_runs=0)
    save(out/"manifest.json",manifest)
    for row in rows:
        b=(out/row["object"]).read_bytes();assert sha(b)==row["stored_sha256"] and sha(gzip.decompress(b))==row["raw_sha256"]
        assert sha(Path(row["path"]).read_bytes())==row["raw_sha256"]
    assert m.gate_metadata(plan)==ready
    save(out/"verification.json",dict(status="CLEAN_RUNTIME_ORCHESTRATION_SUPPLEMENTARY_BYTES_PASS",manifest_sha256=sha((out/"manifest.json").read_bytes()),files=len(rows),raw_bytes=sum(r["raw_bytes"] for r in rows),stored_bytes=sum(p.stat().st_size for p in payload.iterdir()),readback_verified=True,new_emu_runs=0,finished=datetime.now(timezone.utc).isoformat()))
    print(json.dumps(read(out/"verification.json")))
if __name__=="__main__":main()
