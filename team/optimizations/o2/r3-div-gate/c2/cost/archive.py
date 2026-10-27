"""Seal C2 cost raw outputs and execution inputs; keep prior archives unchanged."""
import argparse,datetime,gzip,hashlib,json,subprocess
from pathlib import Path
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--work",type=Path,required=True)
    p.add_argument("--source-repo",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise ValueError("new output required")
    selected={}
    def add(key,path):
        if key in selected:raise ValueError("duplicate "+key)
        selected[key]=(path.read_bytes(),str(path))
    for path in sorted(a.work.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            add("work/"+path.relative_to(a.work).as_posix(),path)
    module=a.source_repo/"team/optimizations/o2/r3-div-gate/c2/cost"
    for path in sorted(module.iterdir()):
        if path.is_file() and path.name not in ["RESULT.md","README.md"]:
            add("source/cost/"+path.name,path)
    candidate=Path("/home/riscv/riscv-lab/o2-c2-readyless-20261025/repo")
    rel="src/main/scala/xiangshan/backend/exu/ExeUnit.scala"
    add("source/candidate/"+rel,candidate/rel)
    add("source/baseline/"+rel,a.source_repo/rel)
    for path in sorted((candidate/"team/optimizations/o4").rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix in [".py",".scala"]:
            add("source/fixture/"+path.relative_to(candidate).as_posix(),path)
    add("source/fixture/timing-review.py",a.source_repo/"team/optimizations/o2/r3-div-gate/timing-review/review.py")
    tool=Path("/home/riscv/riscv-lab/o4-cost-20261020")
    for rel in ["library/NangateOpenCellLibrary_typical.lib","tools/executable-identities.json"]:
        add("tools/"+rel,tool/rel)
    refs={}
    for rel in ["team/optimizations/o2/r3-div-gate/evidence/20261025-performance-cost/manifest.json",
                "team/optimizations/o2/r3-div-gate/c1/evidence/20261025-screen/manifest.json",
                "team/optimizations/o2/r3-div-gate/c2/evidence/20261025-local/manifest.json"]:
        f=a.source_repo/rel;refs[rel]=dict(sha256=sha(f.read_bytes()),bytes=f.stat().st_size)
        add("references/"+rel,f)
    baseline_manifest=a.source_repo/"team/optimizations/o2/r3-div-gate/evidence/20261025-performance-cost/manifest.json"
    baseline_root=Path("/home/riscv/riscv-lab/o2-r3-div-gate-cost-20261025")
    baseline_count=0
    for row in json.loads(baseline_manifest.read_text())["files"]:
        if any(row["path"].startswith("cost/"+part+"/") for part in ("parent-cost-01","parent-map-01","parent-sta-01")):
            relative=row["path"][len("cost/"):]
            f=baseline_root/relative
            if sha(f.read_bytes())!=row["raw_sha256"] or f.stat().st_size!=row["raw_bytes"]:
                raise ValueError("baseline payload mismatch "+relative)
            add("baseline/"+relative,f);baseline_count+=1
    if baseline_count!=143:raise ValueError("baseline file set differs")
    a.output.mkdir(parents=True)
    files=[]
    for key,(raw,origin) in selected.items():
        compressed=len(raw)>=16384
        payload=gzip.compress(raw,compresslevel=6,mtime=0) if compressed else raw
        stored="payload/"+key+(".gz" if compressed else "")
        path=a.output/stored;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(payload)
        files.append(dict(path=key,origin=origin,raw_sha256=sha(raw),raw_bytes=len(raw),
                          stored=stored,stored_sha256=sha(payload),stored_bytes=len(payload),
                          compression="gzip" if compressed else "none"))
    result=dict(status="C2_COST_EVIDENCE_SEALED",time=datetime.datetime.now().astimezone().isoformat(),
                candidate_commit="6704ce3502a7235cdb81697638c01ed23f6914f6",
                baseline_commit="0f12df675378556670afd0dd2153f47fcb330610",
                reference_archives=refs,files=files,
                scope="Frozen same-constraint parent synthesis/five-profile/targeted STA, screening and audits. Prior local qualification and baseline mappings remain in unchanged linked seals; no obj/cache/tool binaries.")
    raw=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    (a.output/"manifest.json").write_text(raw)
    print(json.dumps(dict(files=len(files),raw_bytes=sum(x["raw_bytes"] for x in files),
                         stored_bytes=sum(x["stored_bytes"] for x in files),manifest_sha256=sha(raw.encode())),indent=2))
if __name__=="__main__":main()
