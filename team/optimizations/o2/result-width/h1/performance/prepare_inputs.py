"""Copy exact immutable inputs for portable replay; no simulator execution."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from portable import require, safe_relative

ROOT=Path(__file__).resolve().parents[6]
REVISION="f732d92d13fb47fdf9eea46d32c5e77bd4343363"
FROZEN_INPUTS=Path("/home/riscv/riscv-lab/o2-performance-20261019/portable-inputs")
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,data):
    require(not path.exists() and not path.is_symlink(), "output already exists: " + str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def prepare(work):
    work=work.resolve()
    artifact=json.loads((work/"campaign-01/artifact-pins.json").read_text())
    old=FROZEN_INPUTS
    manifest=json.loads((old/"input-manifest.json").read_text())
    require(len(manifest["files"])==209, "incomplete frozen input inventory")
    dest=work/"portable-inputs"
    for output in (dest,work/"input-builds"):
        require(not output.exists() and not output.is_symlink(), "output already exists: " + str(output))
    selected=[]
    for rel,item in manifest["files"].items():
        relative=safe_relative(rel)
        source=old/"ours"/Path(*relative.parts)
        require(source.resolve().is_relative_to((old/"ours").resolve()), "frozen input path escapes root")
        for parent in (source,*(old/"ours"/Path(*relative.parts[:i]) for i in range(len(relative.parts)))):
            require(not parent.is_symlink(), "frozen input symlink")
        raw=source.read_bytes()
        require(sha(raw)==item["sha256"]==artifact[item["original"]], "frozen input hash mismatch")
        require(raw==Path(item["original"]).read_bytes(), "frozen input differs from original")
        selected.append((rel,raw))
    for rel,raw in selected:
        p=dest/"ours"/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    (dest/"input-manifest.json").write_bytes((old/"input-manifest.json").read_bytes())
    builds={
      "b0":Path("/home/riscv/riscv-lab/o2-fullcore-20261019/build-03"),
      "h1":Path("/home/riscv/riscv-lab/o2-h1-fullcore-20261021/build-01")}
    metadata={}
    for mode,folder in builds.items():
        for leaf in ("hardware-inputs.json","build-state.json","generated-artifacts.json",
                     "build-command.sh","dependencies.json","emu-build.log"):
            p=folder/leaf;raw=p.read_bytes()
            require(sha(raw)==artifact[str(p)], "build metadata hash mismatch")
            dst=work/"input-builds"/mode/leaf;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
            metadata[str(dst.relative_to(work))]=dict(original=str(p),sha256=sha(raw))
        for p in sorted(folder.glob("*-version.log")):
            if str(p) not in artifact:continue
            raw=p.read_bytes()
            require(sha(raw)==artifact[str(p)], "tool version hash mismatch")
            dst=work/"input-builds"/mode/p.name;dst.write_bytes(raw)
            metadata[str(dst.relative_to(work))]=dict(original=str(p),sha256=sha(raw))
        pins=json.loads((folder/"hardware-inputs.json").read_text())
        for rel in ("build.sc","src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala"):
            raw=subprocess.check_output(["git","show",pins["source_commit"]+":"+rel],cwd=ROOT)
            require(sha(raw)==pins["files"][rel], "Git source hash mismatch")
            dst=work/"input-builds"/mode/"source"/rel
            dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
            metadata[str(dst.relative_to(work))]=dict(source_commit=pins["source_commit"],path=rel,sha256=sha(raw))
    save(work/"input-builds/manifest.json",metadata)
    print("FROZEN_INPUT_SNAPSHOT_PASS")
def support(archive):
    archive=archive.resolve()
    for name in ("support", "support-manifest.json", "support-manifest.sha256"):
        require(not (archive/name).exists() and not (archive/name).is_symlink(), "support output already exists")
    files={}
    for rel in ("team/models/vdot/data/directed.jsonl","team/models/vdot/data/random.jsonl"):
        raw=subprocess.check_output(["git","show",REVISION+":"+rel],cwd=ROOT)
        oid=subprocess.check_output(["git","rev-parse",REVISION+":"+rel],cwd=ROOT,text=True).strip()
        require(hashlib.sha1(("blob "+str(len(raw))+"\0").encode()+raw).hexdigest()==oid,
                "Git corpus blob mismatch")
        p=archive/"support"/rel
        require(not p.exists(), "support file already exists")
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
    require(bool(args.work)!=bool(args.archive), "exactly one of --work and --archive is required")
    if args.work:prepare(args.work)
    else:support(args.archive)
