"""Verify exact archive inventory and both compressed/raw bytes. Python standard library."""
import argparse, gzip, hashlib, json, datetime
from pathlib import Path, PurePosixPath

def sha(data):
    return hashlib.sha256(data).hexdigest()

def verify(root):
    manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    need=lambda ok, message: None if ok else (_ for _ in ()).throw(ValueError(message))
    files=manifest["files"]; paths=set(); stored=set(); raw_bytes=0; stored_bytes=0
    for row in files:
        need(row["path"] not in paths,"duplicate logical path")
        need(row["stored"] not in stored,"duplicate stored path")
        for key in ["path","stored"]:
            p=PurePosixPath(row[key])
            need(not p.is_absolute() and ".." not in p.parts,"unsafe manifest path")
        paths.add(row["path"]);stored.add(row["stored"])
        blob=(root/row["stored"]).read_bytes()
        need(len(blob)==row["stored_bytes"] and sha(blob)==row["stored_sha256"],"stored mismatch "+row["path"])
        need(row["compression"] in ("gzip","none"),"compression")
        raw=gzip.decompress(blob) if row["compression"]=="gzip" else blob
        need(len(raw)==row["raw_bytes"] and sha(raw)==row["raw_sha256"],"raw mismatch "+row["path"])
        raw_bytes+=len(raw);stored_bytes+=len(blob)
    actual={p.relative_to(root).as_posix() for p in (root/"payload").rglob("*") if p.is_file()}
    need(actual==stored,"unlisted/missing payload")
    return dict(status="C1_ARCHIVE_BYTES_PASS", time=datetime.datetime.now().astimezone().isoformat(),
                files=len(files),raw_bytes=raw_bytes,stored_bytes=stored_bytes,
                manifest_sha256=sha((root/"manifest.json").read_bytes()),
                scope="Exact payload inventory and raw/stored bytes; not a new hardware run or independent functional proof.")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise ValueError("new output required")
    result=verify(a.archive)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
