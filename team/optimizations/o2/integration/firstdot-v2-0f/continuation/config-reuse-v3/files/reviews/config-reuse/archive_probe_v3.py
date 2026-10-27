"""Seal both attempts' local bytes after V3 raw audit; no new target runs."""
from pathlib import Path
import json,gzip,hashlib
from datetime import datetime,timezone
W=Path("/home/riscv/riscv-lab/software-import-20261026")
D=W/"reviews/config-reuse";O=W/"config-reuse-clean02-02";A=W/"reviews/config-reuse-final-archive-01"
def read(p):return json.loads(Path(p).read_text())
def digest(b):return hashlib.sha256(b).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
def main():
    assert read(O/"completion-02.json")["status"]=="PROBE_V3_RUNTIME_AND_FIXED_READONLY_AUDIT_PASS"
    assert read(O/"audit-02.json")["status"]=="PROBE_LOCAL_RAW_AUDIT_PASS"
    assert read(W/"config-reuse-audit-fix-01.command.json")["exit_code"]==0
    assert read(W/"config-reuse-clean02-01/run-01/state.json")["new_emu_runs"]==2
    assert not A.exists()
    paths=set()
    for root in [W/"config-reuse-clean02-01",O,D/"adapter-v2",D/"adapter-v3",D/"audit-scope-fix-v1"]:
        for p in root.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts:
                assert not p.is_symlink();paths.add(p)
    for name in ["run_image_scope_retry_v3.py","ROOT_REVIEW.image-scope-v3-01.json","pipeline-state-01.json",
        "run_reviewed_pipeline_v2.py","ROOT_REVIEW.clean02-20261027-01.json","clean02-launch-plan-v4.json",
        "execute_clean02_stage_v3.py","actual-clean-readiness-01.json","archive_probe_v3.py","IMAGE_SCOPE_FIX.md"]:
        paths.add(D/name)
    for glob in ["adapter-v3-tests-01.command.*","adapter-v3-tests-02.command.*","audit-scope-tests-01.command.*"]:
        paths.update(D.glob(glob))
    for glob in ["config-reuse-clean02-pipeline-01.command.*","config-reuse-clean02-import-01.command.*","config-reuse-v3-pipeline-01.command.*","config-reuse-audit-fix-01.command.*"]:
        paths.update(W.glob(glob))
    paths.add(W/"run_recorded.py")
    manifest=read(D/"adapter-v3/import-manifest.json")
    for row in manifest["files"]+manifest["already_present_dependencies"]:
        paths.add(W/"clean-02/checkout/source"/row["path"])
    A.mkdir();(A/"objects").mkdir()
    rows=[]
    for i,p in enumerate(sorted(paths)):
        raw=p.read_bytes();encoded=gzip.compress(raw,compresslevel=6,mtime=0)
        stored="objects/"+str(i).zfill(5)+".gz";(A/stored).write_bytes(encoded)
        rows.append(dict(original=str(p),stored=stored,encoding="gzip",raw_bytes=len(raw),
          raw_sha256=digest(raw),stored_bytes=len(encoded),stored_sha256=digest(encoded)))
    meta=dict(contract="config-probe-local-byte-archive-v1",status="BYTES_SEALED",
      files=rows,scope="V2 failed attempt and V3 actual build/run/audit, fixed sources and command receipts",
      portable_raw_recomputation=False,requires_external_physical_inputs=True,
      semantic_audit=str(O/"audit-02.json"),semantic_audit_sha256=digest((O/"audit-02.json").read_bytes()))
    save(A/"manifest.json",meta)
    for row in rows:
        encoded=(A/row["stored"]).read_bytes();raw=gzip.decompress(encoded)
        assert len(encoded)==row["stored_bytes"] and digest(encoded)==row["stored_sha256"]
        assert len(raw)==row["raw_bytes"] and digest(raw)==row["raw_sha256"]
        assert Path(row["original"]).read_bytes()==raw
    result=dict(status="CONFIG_PROBE_BOTH_ATTEMPTS_BYTES_VERIFIED",members=len(rows),
      raw_bytes=sum(x["raw_bytes"] for x in rows),stored_bytes=sum(x["stored_bytes"] for x in rows),
      manifest_sha256=digest((A/"manifest.json").read_bytes()),raw_and_stored_readback=True,
      portable_raw_recomputation=False,new_emu_runs=0,finished=datetime.now(timezone.utc).isoformat())
    save(A/"verification.json",result);print(json.dumps(result))
if __name__=="__main__":main()
