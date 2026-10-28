#!/usr/bin/env python3
"""Portable offline check: validate sealed bytes, restore into temp, rerun strict audit."""
import argparse, gzip, hashlib, json, subprocess, sys, tempfile
from pathlib import Path
def main():
    p=argparse.ArgumentParser();p.add_argument("evidence",type=Path);a=p.parse_args()
    manifest=json.loads((a.evidence/"manifest.json").read_text());names=set()
    with tempfile.TemporaryDirectory(prefix="vdot-o4-audit-") as tmp:
        root=Path(tmp)
        for entry in manifest["entries"]:
            rel=Path(entry["path"]);stored=Path(entry["stored"])
            if rel.is_absolute() or stored.is_absolute() or ".." in rel.parts or ".." in stored.parts or str(rel) in names:raise ValueError("unsafe/duplicate evidence path")
            names.add(str(rel));payload=(a.evidence/"files"/stored).read_bytes()
            if len(payload)!=entry["stored_bytes"] or hashlib.sha256(payload).hexdigest()!=entry["stored_sha256"]:raise ValueError("stored evidence identity")
            raw=gzip.decompress(payload) if entry["gzip"] else payload
            if len(raw)!=entry["bytes"] or hashlib.sha256(raw).hexdigest()!=entry["sha256"]:raise ValueError("original evidence identity")
            dest=root/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        subprocess.run([sys.executable,"-B",str(Path(__file__).parent/"audit.py"),str(root)],check=True)
    print(f"O4_SEALED_RECHECK_PASS files={len(names)}")
if __name__=="__main__":main()
