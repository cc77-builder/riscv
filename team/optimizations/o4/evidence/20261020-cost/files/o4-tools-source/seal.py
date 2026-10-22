#!/usr/bin/env python3
"""Archive completed evidence with deterministic gzip; never include installed binaries/cache."""
import argparse, gzip, hashlib, json, shutil
from pathlib import Path
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument("work",type=Path);p.add_argument("output",type=Path);a=p.parse_args()
    assert json.loads((a.work/"assessment.json").read_text())["audit_pass"]
    a.output.mkdir(parents=True,exist_ok=False)
    files=a.output/"files";files.mkdir();index=[];external=[]
    assessment=json.loads((a.work/"assessment.json").read_text())
    accepted={name for pair in assessment["selection"].values() for name in pair}
    accepted|={"o1-fu-02","o2-fu-01","o1-parent-01","o2-parent-01"}
    for src in sorted(a.work.rglob("*")):
        if not src.is_file():continue
        rel=src.relative_to(a.work)
        if rel.parts[:2] in [("tools","root"),("tools","debs")]:continue
        if "__pycache__" in rel.parts:continue
        raw=src.read_bytes()
        # Failed attempts are fully retained locally. Archive logs/receipts and hashes, not repeated regenerable large netlists.
        if rel.parts[0].startswith(("o1-","o2-")) and rel.parts[0] not in accepted and len(raw)>262144:
            external.append({"path":str(rel),"bytes":len(raw),"sha256":sha(raw),"retained_at":str(src),"reason":"reconstructible large intermediate from excluded/failed attempt; commands/logs and input identities included"})
            continue
        compress=len(raw)>262144
        destrel=Path(str(rel)+".gz") if compress else rel
        dest=files/destrel;dest.parent.mkdir(parents=True,exist_ok=True)
        payload=gzip.compress(raw,compresslevel=9,mtime=0) if compress else raw
        dest.write_bytes(payload)
        index.append({"path":str(rel),"stored":str(destrel),"gzip":compress,"bytes":len(raw),"sha256":sha(raw),"stored_bytes":len(payload),"stored_sha256":sha(payload)})
    (a.output/"external-artifacts.json").write_text(json.dumps({"scope":"retained in WSL, not required for final accepted-set offline audit","entries":external},indent=2)+"\n")
    (a.output/"manifest.json").write_text(json.dumps({"format":1,"entries":index},indent=2)+"\n")
    print(json.dumps({"files":len(index),"stored_bytes":sum(x["stored_bytes"] for x in index),"largest_blob":max(x["stored_bytes"] for x in index)}))
if __name__=="__main__":main()
