"""Freeze selected C1 evidence, excluding build caches and executables."""
import argparse, gzip, hashlib, json, subprocess, datetime
from pathlib import Path

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a=p.parse_args()
    if a.output.exists(): raise ValueError("new output required")
    a.output.mkdir(parents=True)
    selected={}
    def add_file(key, path):
        if key in selected: raise ValueError("duplicate "+key)
        selected[key]=(path.read_bytes(), str(path))
    for f in sorted(a.work.iterdir()):
        if f.is_file(): add_file("work/"+f.name, f)
    for name in ["fu-01","fu-02","parent-01","parent-cost-01","parent-map-01","parent-sta-01","screen-01"]:
        for f in sorted((a.work/name).rglob("*")):
            if f.is_file() and "obj" not in f.relative_to(a.work/name).parts:
                add_file("work/"+f.relative_to(a.work).as_posix(), f)
    for name in ["parent-map-01/summary.json","parent-sta-01/summary.json"]:
        add_file("baseline/"+name, a.baseline/name)
    for profile in ["nominal","period050","period200","load001","load020"]:
        for f in sorted((a.baseline/"parent-sta-01"/profile).iterdir()):
            if f.is_file(): add_file("baseline/parent-sta-01/"+profile+"/"+f.name, f)
    candidate=a.work/"repo"
    src="src/main/scala/xiangshan/backend/exu/ExeUnit.scala"
    add_file("source/candidate/"+src, candidate/src)
    add_file("source/baseline/"+src, a.repo/src)
    patch=subprocess.check_output(["git","format-patch","-1","--stdout","HEAD"],cwd=candidate)
    selected["source/candidate.commit.patch"]=(patch,"git format-patch -1 --stdout HEAD at "+str(candidate))
    for rel in ["build.sc","team/optimizations/o2/run_rtl.py","team/optimizations/o2/check_negative_fu.py",
                "team/rtl/vdot/prepare_vectors.py","team/optimizations/o4/elaborate.py",
                "team/optimizations/o4/synthesize.py","team/optimizations/o4/timing.py"]:
        if (candidate/rel).is_file(): add_file("source/fixture/"+rel, candidate/rel)
    for rel in ["team/optimizations/o2/fu","team/optimizations/o2/parent","team/optimizations/o4/scala",
                "team/models/vdot"]:
        for f in sorted((candidate/rel).rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts and f.suffix in [".py",".cpp",".h",".scala",".json",".jsonl",".md"]:
                add_file("source/fixture/"+f.relative_to(candidate).as_posix(), f)
    module=a.repo/"team/optimizations/o2/r3-div-gate/c1"
    for f in sorted(module.iterdir()):
        if f.is_file() and f.suffix in [".py",".md",".json"]:
            add_file("source/c1/"+f.name,f)
    add_file("source/prior-review.py",a.repo/"team/optimizations/o2/r3-div-gate/timing-review/review.py")
    tool=Path("/home/riscv/riscv-lab/o4-cost-20261020")
    for rel in ["library/NangateOpenCellLibrary_typical.lib","tools/executable-identities.json"]:
        add_file("tools/"+rel,tool/rel)
    refs={}
    for name in ["20261024-local","20261025-performance-cost"]:
        f=a.repo/"team/optimizations/o2/r3-div-gate/evidence"/name/"manifest.json"
        refs[name]=dict(path=str(f),sha256=sha(f.read_bytes()))
    files=[]
    for key,(raw,origin) in sorted(selected.items()):
        compressed=len(raw)>=16384
        payload=gzip.compress(raw,compresslevel=6,mtime=0) if compressed else raw
        stored="payload/"+key+(".gz" if compressed else "")
        dest=a.output/stored
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(payload)
        files.append(dict(path=key,origin=origin,raw_sha256=sha(raw),raw_bytes=len(raw),
                          stored=stored,stored_sha256=sha(payload),stored_bytes=len(payload),
                          compression="gzip" if compressed else "none"))
    result=dict(status="C1_EVIDENCE_SEALED",time=datetime.datetime.now().astimezone().isoformat(),
                baseline_commit="0f12df675378556670afd0dd2153f47fcb330610",
                candidate_commit="3be0e3d9e500bd1aa772bcc8d4f8b023a2877c66",
                reference_archives=refs, files=files,
                scope="Raw failures, local verification, generated RTL, mapped netlists, constraints and timing. No obj/cache/binaries; binary hashes remain in artifact receipts. Baseline maps already sealed in reference archive.")
    (a.output/"manifest.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(dict(files=len(files),raw_bytes=sum(x["raw_bytes"] for x in files),
                         stored_bytes=sum(x["stored_bytes"] for x in files),
                         manifest_sha256=sha((a.output/"manifest.json").read_bytes())),indent=2))

if __name__=="__main__":main()
