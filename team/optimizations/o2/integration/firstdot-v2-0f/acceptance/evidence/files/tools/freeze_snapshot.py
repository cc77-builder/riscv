"""Save and read back the frozen nonignored workspace; dependencies have separate pins."""
import argparse, hashlib, json, tarfile
from pathlib import Path

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run(repo, freeze, output):
    value=json.loads(freeze.read_text())
    assert not output.exists()
    for rel,digest in value["files"].items():
        assert sha(repo/rel)==digest, rel
    with tarfile.open(output,"w:gz",compresslevel=1) as tar:
        for rel in value["files"]:
            tar.add(repo/rel,arcname=rel,recursive=False)
    count=0
    with tarfile.open(output,"r:gz") as tar:
        members=tar.getmembers()
        assert len(members)==len(value["files"])
        assert {m.name for m in members}==set(value["files"])
        for member in members:
            assert member.isfile()
            assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==value["files"][member.name],member.name
            count+=1
    result=dict(status="FROZEN_WORKSPACE_ARCHIVE_READBACK_PASS",files=count,path=str(output),
                sha256=sha(output),bytes=output.stat().st_size,freeze_sha256=sha(freeze),
                contains_git_history=False,contains_external_dependencies=False)
    output.with_suffix(output.suffix+".json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for key in ("repo","freeze","output"):p.add_argument("--"+key,type=Path,required=True)
    a=p.parse_args();run(a.repo,a.freeze,a.output)
