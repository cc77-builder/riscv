#!/usr/bin/env python3
"""Prepare pinned isolated tools without sudo or system-package mutation."""
import argparse, hashlib, json, subprocess, urllib.request
from pathlib import Path
import live_contract
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument("work",type=Path);a=p.parse_args()
    lock=json.loads((Path(__file__).parent/"toolchain-lock.json").read_text())
    # Never overwrite a previous preparation or its failed downloads.
    tools=a.work/"tools";tools.mkdir(parents=True,exist_ok=False)
    debs=tools/"debs";debs.mkdir();root=tools/"root";root.mkdir()
    with (tools/"apt-download.log").open("w") as f:
        subprocess.run(["apt-get","download",*lock["apt_specs"]],cwd=debs,stdout=f,stderr=subprocess.STDOUT,check=True)
    for pkg in lock["packages"]:
        path=debs/pkg["name"]
        if sha(path)!=pkg["sha256"]:raise ValueError(f"package SHA mismatch: {path}")
        subprocess.run(["dpkg-deb","-x",str(path),str(root)],check=True)
    for exe in ["yosys","berkeley-abc","sta"]:
        out=subprocess.check_output(["ldd",str(root/"usr/bin"/exe)],text=True)
        (tools/(exe+"-ldd.log")).write_text(out)
        if "not found" in out:raise ValueError("unresolved shared library")
    lib=a.work/"library";lib.mkdir(exist_ok=False)
    for item in lock["library"]["files"]:
        if "url" not in item:continue
        path=lib/item["file"]
        with urllib.request.urlopen(item["url"],timeout=60) as resp:path.write_bytes(resp.read())
        if sha(path)!=item["sha256"]:raise ValueError("library/source SHA mismatch")
    (lib/"provenance.json").write_text(json.dumps(lock["library"],indent=2)+"\n")
    (tools/"contract.json").write_text(json.dumps(live_contract.capture(a.work),indent=2)+"\n", encoding="utf-8")
    print("O4_ISOLATED_TOOLS_READY")
if __name__=="__main__":main()
