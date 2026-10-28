"""Seal C2 local evidence, including failed attempts, without obj/cache/binaries."""
import argparse, datetime, gzip, hashlib, json, subprocess
from pathlib import Path

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--work",type=Path,required=True)
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise ValueError("new output required")
    selected={}
    def add(key,path):
        if key in selected:
            raise ValueError("duplicate "+key)
        selected[key]=(path.read_bytes(),str(path))
    for path in sorted(args.work.iterdir()):
        if path.is_file():
            add("work/"+path.name,path)
    for name in ["fu-01","fu-02","parent-01","supplement-01","test-design",
                 "rtl-review","version-ledger","final-audit"]:
        for path in sorted((args.work/name).rglob("*")):
            rel=path.relative_to(args.work/name)
            if path.is_file() and not {"obj","__pycache__"}.intersection(rel.parts):
                add("work/"+path.relative_to(args.work).as_posix(),path)
    candidate=args.work/"repo"
    src="src/main/scala/xiangshan/backend/exu/ExeUnit.scala"
    add("source/candidate/"+src,candidate/src)
    add("source/baseline/"+src,args.repo/src)
    patch=subprocess.check_output(["git","format-patch","-1","--stdout","HEAD"],cwd=candidate)
    selected["source/candidate.commit.patch"]=(patch,"git format-patch -1 --stdout HEAD at "+str(candidate))
    for rel in ["build.sc","team/optimizations/o2/run_rtl.py","team/optimizations/o2/check_negative_fu.py",
                "team/optimizations/o2/test_negative_fu.py","team/scripts/activate.sh",
                "team/rtl/vdot/prepare_vectors.py"]:
        add("source/fixture/"+rel,candidate/rel)
    for rel in ["team/optimizations/o2/fu","team/optimizations/o2/parent","team/models/vdot"]:
        for path in sorted((candidate/rel).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix in [".py",".cpp",".h",".scala",".json",".jsonl",".md"]:
                add("source/fixture/"+path.relative_to(candidate).as_posix(),path)
    module=args.repo/"team/optimizations/o2/r3-div-gate/c2"
    for path in sorted(module.iterdir()):
        if path.is_file() and path.name not in ["RESULT.md","README.md"]:
            add("source/c2/"+path.name,path)
    for path in sorted((module/"parent").iterdir()):
        if path.is_file():
            add("source/c2/parent/"+path.name,path)
    refs={}
    for rel in ["team/optimizations/o2/r3-div-gate/evidence/20261024-local/manifest.json",
                "team/optimizations/o2/r3-div-gate/evidence/20261025-performance-cost/manifest.json",
                "team/optimizations/o2/r3-div-gate/c1/evidence/20261025-screen/manifest.json",
                "team/optimizations/o2/r3-div-gate/c2-g0/evidence/manifest.json"]:
        path=args.repo/rel
        if path.is_file():
            refs[rel]=dict(sha256=digest(path.read_bytes()),bytes=path.stat().st_size)
    args.output.mkdir(parents=True)
    files=[]
    for key,(raw,origin) in sorted(selected.items()):
        compressed=len(raw)>=16384
        payload=gzip.compress(raw,compresslevel=6,mtime=0) if compressed else raw
        stored="payload/"+key+(".gz" if compressed else "")
        dest=args.output/stored;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(payload)
        files.append(dict(path=key,origin=origin,raw_sha256=digest(raw),raw_bytes=len(raw),
                          stored=stored,stored_sha256=digest(payload),stored_bytes=len(payload),
                          compression="gzip" if compressed else "none"))
    result=dict(status="C2_LOCAL_EVIDENCE_SEALED",time=datetime.datetime.now().astimezone().isoformat(),
                baseline_commit="0f12df675378556670afd0dd2153f47fcb330610",
                candidate_commit="6704ce3502a7235cdb81697638c01ed23f6914f6",
                reference_archives=refs,files=files,
                scope="Local FU/real-parent/control structure only; failures retained. No PPA/fullcore. No obj/cache/binaries; binary hashes retained. Reports/ledger outside seal reference this immutable manifest.")
    (args.output/"manifest.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(dict(files=len(files),raw_bytes=sum(x["raw_bytes"] for x in files),
                         stored_bytes=sum(x["stored_bytes"] for x in files),
                         manifest_sha256=digest((args.output/"manifest.json").read_bytes())),indent=2))

if __name__=="__main__":
    main()
