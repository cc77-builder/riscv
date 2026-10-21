"""Copy exact immutable inputs for portable replay; no simulator execution."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[6]
REVISION="f732d92d13fb47fdf9eea46d32c5e77bd4343363"
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def prepare(work):
    artifact=json.loads((work/"campaign-01/artifact-pins.json").read_text())
    old=Path("/home/riscv/riscv-lab/o2-performance-20261019/portable-inputs")
    manifest=json.loads((old/"input-manifest.json").read_text())
    assert len(manifest["files"])==209
    dest=work/"portable-inputs"
    assert not dest.exists()
    for rel,item in manifest["files"].items():
        raw=(old/"ours"/rel).read_bytes()
        assert sha(raw)==item["sha256"]==artifact[item["original"]]
        assert raw==Path(item["original"]).read_bytes()
        p=dest/"ours"/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    (dest/"input-manifest.json").write_bytes((old/"input-manifest.json").read_bytes())
    builds={
      "b0":Path("/home/riscv/riscv-lab/o2-fullcore-20261019/build-03"),
      "h1":Path("/home/riscv/riscv-lab/o2-h1-fullcore-20261021/build-01")}
    metadata={}
    for mode,folder in builds.items():
        for leaf in ("hardware-inputs.json","build-state.json","generated-artifacts.json",
                     "build-command.sh","dependencies.json","emu-build.log"):
            p=folder/leaf;raw=p.read_bytes();assert sha(raw)==artifact[str(p)]
            dst=work/"input-builds"/mode/leaf;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
            metadata[str(dst.relative_to(work))]=dict(original=str(p),sha256=sha(raw))
        for p in sorted(folder.glob("*-version.log")):
            if str(p) not in artifact:continue
            raw=p.read_bytes();assert sha(raw)==artifact[str(p)]
            dst=work/"input-builds"/mode/p.name;dst.write_bytes(raw)
            metadata[str(dst.relative_to(work))]=dict(original=str(p),sha256=sha(raw))
        pins=json.loads((folder/"hardware-inputs.json").read_text())
        for rel in ("build.sc","src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala"):
            raw=subprocess.check_output(["git","show",pins["source_commit"]+":"+rel],cwd=ROOT)
            assert sha(raw)==pins["files"][rel]
            dst=work/"input-builds"/mode/"source"/rel
            dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
            metadata[str(dst.relative_to(work))]=dict(source_commit=pins["source_commit"],path=rel,sha256=sha(raw))
    save(work/"input-builds/manifest.json",metadata)
    print("FROZEN_INPUT_SNAPSHOT_PASS")
def support(archive):
    files={}
    for rel in ("team/models/vdot/data/directed.jsonl","team/models/vdot/data/random.jsonl"):
        raw=subprocess.check_output(["git","show",REVISION+":"+rel],cwd=ROOT)
        oid=subprocess.check_output(["git","rev-parse",REVISION+":"+rel],cwd=ROOT,text=True).strip()
        assert hashlib.sha1(("blob "+str(len(raw))+"\0").encode()+raw).hexdigest()==oid
        p=archive/"support"/rel;assert not p.exists()
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        files[rel]=dict(bytes=len(raw),sha256=sha(raw),git_blob=oid)
    save(archive/"support-manifest.json",dict(version=1,source_revision=REVISION,files=files))
    (archive/"support-manifest.sha256").write_text(sha((archive/"support-manifest.json").read_bytes())+"  support-manifest.json\n",encoding="ascii")
    print("FROZEN_CORPUS_SUPPORT_PASS")
if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work",type=Path)
    parser.add_argument("--archive",type=Path)
    args=parser.parse_args()
    assert bool(args.work)!=bool(args.archive)
    if args.work:prepare(args.work)
    else:support(args.archive)
