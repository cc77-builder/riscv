"""Verify every sealed payload, then optionally unpack to a fresh directory."""
import argparse,gzip,hashlib,json
from pathlib import Path

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def relative(value):
    p=Path(value)
    if p.is_absolute() or ".." in p.parts or not p.parts:
        raise ValueError("invalid archive path: "+value)
    return p

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--output",type=Path)
    a=parser.parse_args()
    manifest=a.archive/"manifest.json"
    rows=json.loads(manifest.read_text(encoding="utf-8"))["files"]
    if a.output and a.output.exists():
        raise ValueError("new output directory required")
    verified=[]
    raw_seen,stored_seen=set(),set()
    for row in rows:
        key=relative(row["path"]);stored=relative(row["stored"])
        if str(key) in raw_seen or str(stored) in stored_seen:
            raise ValueError("duplicate path")
        raw_seen.add(str(key));stored_seen.add(str(stored))
        payload=(a.archive/stored).read_bytes()
        if len(payload)!=row["stored_bytes"] or digest(payload)!=row["stored_sha256"]:
            raise ValueError("stored checksum mismatch: "+str(stored))
        compression=row.get("compression","gzip" if row.get("gzip") else "none")
        if compression not in ("gzip","none"):
            raise ValueError("unknown compression")
        raw=gzip.decompress(payload) if compression=="gzip" else payload
        if len(raw)!=row["raw_bytes"] or digest(raw)!=row["raw_sha256"]:
            raise ValueError("raw checksum mismatch: "+str(key))
        verified.append((key,raw))
    if not verified:raise ValueError("empty manifest")
    if a.output:
        a.output.mkdir(parents=True,exist_ok=False)
        for key,raw in verified:
            p=a.output/key;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    print(json.dumps(dict(status="C2_COST_PAYLOAD_VERIFY_PASS",
                         files=len(verified),raw_bytes=sum(len(raw) for _,raw in verified),
                         manifest_sha256=digest(manifest.read_bytes()),
                         extracted_to=str(a.output) if a.output else None),indent=2))
if __name__=="__main__":main()
