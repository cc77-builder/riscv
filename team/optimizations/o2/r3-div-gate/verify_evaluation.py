"""Portable byte-only verifier for the sealed R3 cycle/cost archive."""
import argparse,gzip,hashlib,json
from pathlib import Path

def need(v,m):
    if not v: raise ValueError(m)
def sha(b): return hashlib.sha256(b).hexdigest()

def verify(root):
    manifest=json.loads((root/"manifest.json").read_text())
    seen=set();stored=set();raw_total=0
    for e in manifest["files"]:
        rel=Path(e["path"]); dest=(root/e["stored"]).resolve()
        need(not rel.is_absolute() and ".." not in rel.parts,"unsafe raw path")
        need(dest.is_relative_to((root/"files").resolve()),"unsafe stored path")
        need(e["path"] not in seen and e["stored"] not in stored,"duplicate payload")
        seen.add(e["path"]);stored.add(e["stored"])
        data=dest.read_bytes()
        need(len(data)==e["stored_bytes"] and sha(data)==e["stored_sha256"],"stored drift: "+e["path"])
        raw=gzip.decompress(data) if e["gzip"] else data
        need(len(raw)==e["raw_bytes"] and sha(raw)==e["raw_sha256"],"raw drift: "+e["path"])
        raw_total+=len(raw)
    need(stored=={p.relative_to(root).as_posix() for p in (root/"files").rglob("*") if p.is_file()},
         "extra/missing archive payload")
    return dict(status="R3_PERFORMANCE_COST_ARCHIVE_BYTES_PASS",
        manifest_sha256=sha((root/"manifest.json").read_bytes()),files=len(seen),raw_bytes=raw_total,
        stored_bytes=sum(e["stored_bytes"] for e in manifest["files"]),
        new_emu_or_eda_run=False,scope="Byte inventory only; not a new functional/STA execution.")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise ValueError("output exists")
    data=verify(a.archive.resolve())
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps(data))
if __name__=="__main__":main()
