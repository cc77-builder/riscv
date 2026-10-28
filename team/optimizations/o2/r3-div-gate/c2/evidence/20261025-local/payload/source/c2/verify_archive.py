"""Verify sealed bytes and replay the frozen parent control/coverage checkers."""
import argparse, gzip, hashlib, json, subprocess, sys, tempfile
from pathlib import Path

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():
        raise ValueError("new output receipt required")
    archive=a.archive.resolve()
    manifest=json.loads((archive/"manifest.json").read_text(encoding="utf-8"))
    files=manifest["files"];raws={};stored=set()
    for item in files:
        key=item["path"]
        if key in raws or item["stored"] in stored:
            raise ValueError("duplicate manifest key")
        path=(archive/item["stored"]).resolve()
        if not path.is_relative_to(archive):
            raise ValueError("external payload path")
        payload=path.read_bytes()
        assert len(payload)==item["stored_bytes"] and sha(payload)==item["stored_sha256"],key
        raw=gzip.decompress(payload) if item["compression"]=="gzip" else payload
        assert item["compression"] in ["gzip","none"]
        assert len(raw)==item["raw_bytes"] and sha(raw)==item["raw_sha256"],key
        raws[key]=raw;stored.add(item["stored"])
    actual={x.relative_to(archive).as_posix() for x in (archive/"payload").rglob("*") if x.is_file()}
    assert actual==stored,"unlisted or missing payload"
    commands=[]
    with tempfile.TemporaryDirectory(prefix="c2-archive-replay-") as name:
        root=Path(name)
        for key,raw in raws.items():
            dest=(root/key).resolve()
            assert dest.is_relative_to(root),"external extracted path"
            dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        parent=root/"source/fixture/team/optimizations/o2/parent"
        supplement=root/"source/c2/parent"
        tests=[
          [parent/"check_trace.py","--log",root/"work/parent-01/result.log"],
          [supplement/"check_c2_parent.py","--log",root/"work/supplement-01/result.log","--parent-dir",parent],
          [supplement/"negative_c2_parent.py","--log",root/"work/supplement-01/result.log","--parent-dir",parent,"--output",root/"negative-replay.json"]]
        for args in tests:
            proc=subprocess.run([sys.executable,"-B",*map(str,args)],capture_output=True,text=True,encoding="utf-8")
            assert proc.returncode==0,proc.stderr+"\n"+proc.stdout[-2000:]
            commands.append(dict(command=[str(x).replace(str(root),"<extracted>") for x in args],
                                 exit_code=proc.returncode,stdout_sha256=sha(proc.stdout.encode()),
                                 result=json.loads(proc.stdout)))
    result=dict(status="C2_ARCHIVE_REPLAY_PASS",platform=sys.platform,
                python=sys.version,files=len(files),raw_bytes=sum(x["raw_bytes"] for x in files),
                stored_bytes=sum(x["stored_bytes"] for x in files),
                manifest_sha256=sha((archive/"manifest.json").read_bytes()),replays=commands,
                scope="Sealed bytes plus frozen control/coverage/negative replay. No new RTL, payload arithmetic execution, fullcore or PPA.")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ["status","platform","files","raw_bytes","stored_bytes","manifest_sha256"]},indent=2))

if __name__=="__main__":
    main()
