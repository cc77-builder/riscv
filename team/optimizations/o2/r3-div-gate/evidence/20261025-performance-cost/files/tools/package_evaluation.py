#!/usr/bin/env python3
"""Seal local R3 cycle/cost raw evidence; portable mode verifies bytes only."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[4]
LAB=ROOT.parents[1]
MODULE=Path(__file__).resolve().parent

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

def package(out):
    need(not out.exists(),"archive exists")
    perf=LAB/"o2-r3-div-gate-performance-20261025"
    cost=LAB/"o2-r3-div-gate-cost-20261025"
    old=LAB/"o2-h1-result32-20261021"
    need(json.loads((cost/"campaign-state.json").read_text())["status"]=="passed","cost campaign incomplete")
    need(json.loads((perf/"results-01/verification.json").read_text())["status"]=="OFFLINE_BEFORE_AFTER_PAIRED_RECHECK_PASS","performance recheck incomplete")
    need(json.loads((cost/"results-01/summary.json").read_text())["status"]=="R3_DIV_GATE_COST_AUDIT_PASS","cost audit incomplete")
    sources={}
    def add_tree(prefix,root):
        for p in sorted(root.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                key=prefix+"/"+p.relative_to(root).as_posix()
                need(key not in sources,"duplicate source");sources[key]=p
    add_tree("performance",perf)
    add_tree("cost",cost)
    for boundary in ("fu","parent"):
        for suffix in ("-cost-01","-map-01","-sta-01"):
            name=boundary+suffix;add_tree("baseline-h1/"+name,old/name)
    for name in ("candidate-inputs.json","campaign-state.json","final-validation.json"):
        sources["baseline-h1/"+name]=old/name
    images=LAB/"unified-vdot-benchmark-20261017/runs/ours-images-02"
    # Include the exact software artifacts declared by sealed image verification.
    input_paths=json.loads((perf/"campaign-01/artifact-pins.json").read_text())
    for name,digest in input_paths.items():
        p=Path(name)
        if p.is_relative_to(images):
            sources["images/"+p.relative_to(images).as_posix()]=p
    for folder in ("performance","cost"):
        for p in (MODULE/folder).iterdir():
            if p.is_file():sources["tools/"+folder+"/"+p.name]=p
    sources["tools/package_evaluation.py"]=Path(__file__)
    sources["tools/test_package_evaluation.py"]=MODULE/"test_package_evaluation.py"
    sources["tools/finalize_evaluation.py"]=MODULE/"finalize_evaluation.py"
    sources["PERFORMANCE_COST_RESULT.md"]=MODULE/"PERFORMANCE_COST_RESULT.md"
    tools=LAB/"o4-cost-20261020"
    for folder in ("team/optimizations/o4","team/workloads/unified-vdot"):
        for p in (ROOT/folder).iterdir():
            if p.is_file() and p.suffix in (".py",".scala",".json",".md"):
                sources["source/"+folder+"/"+p.name]=p
    for name in ("library/NangateOpenCellLibrary_typical.lib","library/LICENSE","library/provenance.json","library/config.mk","tools/executable-identities.json",
                 "tools/packages.json","tools/yosys-version.log","tools/abc-version.log","tools/sta-version.log"):
        sources["eda-reference/"+name]=tools/name
    for name in ("build.sc","src/main/scala/xiangshan/backend/exu/ExeUnit.scala",
                 "src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala"):
        sources["source/"+name]=ROOT/name
    out.mkdir(parents=True)
    rows=[]
    for key,p in sorted(sources.items()):
        raw=p.read_bytes()
        packed=gzip.compress(raw,compresslevel=6,mtime=0) if len(raw)>262144 else raw
        compressed=len(raw)>262144
        dest="files/"+key+(".gz" if compressed else "")
        target=out/dest;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(packed)
        rows.append(dict(path=key,stored=dest,gzip=compressed,raw_bytes=len(raw),raw_sha256=sha(raw),
                         stored_bytes=len(packed),stored_sha256=sha(packed)))
    manifest=dict(format=1,created_utc=datetime.now(timezone.utc).isoformat(),files=rows,
                  external_binary_scope="EMU/NEMU and EDA executables retained locally by fixed SHA; workload ELF/bin included.",
                  baseline_scope="Previous H1 mapping/STA reused after full sealed byte audit; only after candidate newly synthesized.")
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    return verify(out)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path)
    p.add_argument("--verify",type=Path)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    need(bool(a.output)!=bool(a.verify),"select package or verify")
    need(not a.receipt.exists(),"receipt exists")
    report=verify(a.verify.resolve()) if a.verify else package(a.output.resolve())
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))

if __name__=="__main__":main()
