"""Bind imported successful jobs and new recovery attempts without hiding interruption."""
from datetime import datetime
import hashlib
import json
from pathlib import Path,PurePosixPath

def require(ok,msg):
    if not ok:raise ValueError(msg)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def partition(proof,records):
    old={tuple(k) for k in proof["imported_keys"]};new={tuple(k) for k in proof["pending_keys"]}
    require(len(old)==len(proof["imported_keys"])==proof["imported_accepted_jobs"]==46,"reused job inventory")
    require(len(new)==len(proof["pending_keys"])==proof["pending_jobs"]==10,"new job inventory")
    require(not old&new,"old/new job overlap")
    indexed={(r["mode"],r["image"],r["replay"]):r for r in records}
    require(len(indexed)==len(records)==56 and indexed.keys()==old|new,"recovery aggregate inventory")
    require(len(proof["incomplete_attempts"])==2,"interrupted attempt count")
    for key in new:
        require(datetime.fromisoformat(indexed[key]["started_utc"])>=datetime.fromisoformat(proof["started_utc"]),"new job incorrectly reused")
    return old,new,indexed

def validate(work,campaign,records,original_work_root):
    work,campaign=Path(work),Path(campaign)
    if not (campaign/"recovery.json").exists():return {"recovered":False}
    proof=json.loads((campaign/"recovery.json").read_text(encoding="utf-8"))
    old,new,indexed=partition(proof,records)
    prefix=original_work_root.rstrip("/")+"/"
    require(proof["previous"].startswith(prefix),"foreign recovery parent")
    rel=PurePosixPath(proof["previous"][len(prefix):])
    require(not rel.is_absolute() and ".." not in rel.parts,"unsafe recovery parent")
    previous=work/Path(*rel.parts)
    for name,digest in proof["previous_file_sha256"].items():
        rel=PurePosixPath(name)
        require(not rel.is_absolute() and ".." not in rel.parts,"unsafe old file path")
        require(sha(previous/Path(*rel.parts))==digest,"original interrupted campaign drift")
    for key in old:
        mode,image,replay=key
        source=previous/mode/(image+f"-r{replay}");target=campaign/mode/source.name
        require(json.loads((source/"result.json").read_text(encoding="utf-8"))==indexed[key],"imported result identity")
        source_files={p.name:sha(p) for p in source.iterdir() if p.is_file()}
        target_files={p.name:sha(p) for p in target.iterdir() if p.is_file()}
        require(source_files==target_files,"reused raw evidence not byte-identical")
    identity=json.loads((campaign/"execution-source.json").read_text(encoding="utf-8"))
    require(identity["original_source_commit"]==proof["source_commit"],"executor commit")
    require(sha(campaign/"source/team/workloads/o3-gemv/campaign.py")==identity["original_source_sha256"],"original executor source")
    require(sha(campaign/"recovery-source/resume.py")==identity["recovery_script_sha256"],"recovery script identity")
    return dict(recovered=True,reused_completed_jobs=46,new_recovery_emu_jobs=10,interrupted_emu_attempts=2,total_started_emu_attempts=58)
