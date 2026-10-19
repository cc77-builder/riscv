"""Build O1 from the same source inputs as the qualified G3 O2 emulator.

The original O2 binary remains untouched. This builder uses an absolute BUILD_DIR
override inherited by recursive make; no source or dependency changes.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import shutil
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
FLAGS = {"VDOT_O1_HANDOFF": "1", "VDOT_O2_ELASTIC": "0", "VDOT_T14_FUSED_INPUT": "1",
         "VDOT_O1_TRACE": "1", "VDOT_O2_TRACE": "0", "VDOT_T12_TRACE": "0", "VDOT_T13_TRACE": "1"}
HARDWARE = ["src", "scripts", "build.sc", "Makefile", "Makefile.test", "team/scripts/activate.sh"]


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def git(*args, repo=ROOT):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def require(ok, message):
    if not ok:
        raise ValueError(message)


def dependency_snapshot():
    modules, files = [], {}
    def visit(repo):
        for item in git("ls-tree", "-rz", "HEAD", repo=repo).split(b"\0"):
            if not item:
                continue
            meta, name = item.split(b"\t", 1)
            mode, _, pin = meta.decode().split()
            if mode != "160000":
                continue
            sub = repo / name.decode()
            head = git("rev-parse", "HEAD", repo=sub).decode().strip()
            status = git("status", "--porcelain=v1", "--untracked-files=normal", repo=sub).decode()
            require(head == pin and not status, "dependency is not clean/pinned: " + str(sub))
            modules.append({"path": sub.relative_to(ROOT).as_posix(), "head": head, "pin": pin})
            for raw in git("ls-files", "-z", repo=sub).split(b"\0"):
                if raw:
                    p = sub / raw.decode()
                    if p.is_file():
                        files[p.relative_to(ROOT).as_posix()] = sha(p)
            visit(sub)
    visit(ROOT)
    return modules, dict(sorted(files.items()))



def stage_auxiliary(products):
    """SimTop/FileControl write these files to root build, independently of BUILD_DIR."""
    products.mkdir(parents=True, exist_ok=True)
    sources = [ROOT / "build" / name for name in
               ("chisel_db.cpp", "chisel_db.h", "constantin.cpp", "constantin.hpp")]
    sources += sorted(p for p in (ROOT / "build/generated-src").rglob("*") if p.is_file())
    require(len(sources) >= 8, "missing fresh generated support files")
    result = []
    for source in sources:
        require(source.is_file(), "missing generated auxiliary " + str(source))
        relative = source.relative_to(ROOT / "build")
        target = products / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        require(not target.exists() or sha(target) == sha(source), "auxiliary destination conflict")
        shutil.copyfile(source, target)
        result.append({"source": str(source), "destination": str(target),
                       "sha256": sha(source), "generated_mtime": source.stat().st_mtime})
    return result



def generated_files(root):
    return [p for p in sorted(root.rglob("*")) if p.is_file() and
            "emu-compile" not in p.relative_to(root).parts and p != root/"emu"]

def preserve_generated(root, saved):
    saved.mkdir()
    result={}
    for p in generated_files(root):
        rel=p.relative_to(root)
        target=saved/rel;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,target)
        result[rel.as_posix()]=sha(p)
    return result

def restore_generated(root, saved, original, changed):
    """Preserve new fixed-path auxiliaries, then restore the old generation."""
    require(root.is_absolute() and saved.is_absolute() and changed.is_absolute(),"absolute roots required")
    changed.mkdir(exist_ok=False)
    now_files={p.relative_to(root).as_posix():p for p in generated_files(root)}
    alterations=[]
    for name,p in now_files.items():
        digest=sha(p)
        if digest!=original.get(name):
            target=changed/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,target)
            alterations.append(dict(path=name,generated_sha256=digest,was_existing=name in original))
            if name not in original:
                # Only fixed-path generation outputs may be newly introduced.
                require(len(Path(name).parts)==1 or Path(name).parts[0]=="generated-src",
                        "unexpected new original-build output: "+name)
                # Move rather than delete new evidence.
                p.rename(target.with_name(target.name+".removed-from-original"))
    for name,digest in original.items():
        target=root/name
        require(sha(saved/name)==digest,"preserved source changed: "+name)
        if not target.exists() or sha(target)!=digest:
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(saved/name,target)
    require({p.relative_to(root).as_posix():sha(p) for p in generated_files(root)}==original,
            "original generated build changed")
    return alterations

def main(out):
    out = out.resolve()
    require(not out.exists(), "output already exists")
    require(not out.is_relative_to(ROOT), "output must be outside checkout")
    products = out / "products"
    require(not products.exists(), "fresh products directory required")
    original_emu = ROOT / "build/emu"
    original_sha = sha(original_emu)
    require(original_sha == "ac0123280bf6c742d27a7650505bc1d91db350d1519806edfd0be9c7ea208a57", "original O2 binary identity drift")
    require(not git("diff", "HEAD", "--", *HARDWARE), "commit hardware changes before building")
    require(not git("ls-files", "--others", "--exclude-standard", "--", *HARDWARE),
            "untracked hardware inputs must be committed before building")
    out.mkdir(parents=True)
    state = {"status": "CAPTURING", "started_utc": now(), "source_root": str(ROOT),
             "source_commit": git("rev-parse", "HEAD").decode().strip(), "flags": FLAGS, "original_o2_emu_sha256": original_sha, "build_products": str(products)}
    save(out / "build-state.json", state)
    try:
        (out / "source-status.txt").write_bytes(git("status", "--short"))
        (out / "working-tree.patch").write_bytes(git("diff", "--binary", "HEAD"))
        files = {}
        for raw in git("ls-files", "-z", "--", *HARDWARE).split(b"\0"):
            if raw:
                path = ROOT / raw.decode()
                if path.is_file():
                    files[path.relative_to(ROOT).as_posix()] = sha(path)
        dependencies, dependency_files = dependency_snapshot()
        save(out / "dependencies.json", dependencies)
        pins = {"source_commit": state["source_commit"], "config": "MinimalConfig",
                "NUM_CORES": 1, "EMU_THREADS": 1, "JVM_XMX": "12G", "BUILD_JOBS": 2,
                **FLAGS, "files": dict(sorted(files.items())), "dependency_files": dependency_files,
                "build_script_sha256": sha(Path(__file__)), "source_root": str(ROOT)}
        save(out / "hardware-inputs-before.json", pins)
        baseline=json.loads(Path("/home/riscv/riscv-lab/o2-fullcore-20261019/build-03/hardware-inputs.json").read_text())
        for group in ("files","dependency_files"):
            require(pins[group]==baseline[group],"O1/O2 original input mismatch: "+group)
        preserved=out/"preserved-o2-generated-build"
        original_generated=preserve_generated(ROOT/"build",preserved)
        save(out/"original-generated-sha256.json",original_generated)

        activated = "source team/scripts/activate.sh\n"
        tools = {"java": "java -version", "mill": "mill --version", "verilator": "verilator --version",
                 "clang": "clang++ --version", "make": "make --version", "python": "python3 --version",
                 "firtool": '\"$HOME/.cache/llvm-firtool/1.62.1/bin/firtool\" --version'}
        for name, command in tools.items():
            with (out / (name + "-version.log")).open("wb") as log:
                rc = subprocess.run(["bash", "-c", activated + command], cwd=ROOT,
                                    stdout=log, stderr=subprocess.STDOUT).returncode
            require(rc == 0, "missing tool " + name)
        shell = activated + "export " + " ".join(k + "=" + v for k, v in FLAGS.items()) + "\n"
        shell += 'export CHISEL_FIRTOOL_PATH="$HOME/.cache/llvm-firtool/1.62.1/bin"\n'
        shell += "make emu CONFIG=MinimalConfig NUM_CORES=1 EMU_THREADS=1 JVM_XMX=12G OPT_FAST=-O3 OPT_SLOW=-O0 BUILD_DIR=" + str(products) + " -j2\n"
        (out / "build-command.sh").write_text(shell, encoding="utf-8")
        state.update(status="BUILDING", build_started_utc=now(), command=["bash", "-c", shell])
        save(out / "build-state.json", state)
        print("O1_MATCHED_BUILD_STARTED " + str(out), flush=True)
        generation = ["bash", "-c", shell.replace("make emu ", "make sim-verilog ", 1)]
        state["generation_command"] = generation
        save(out / "build-state.json", state)
        try:
            with (out / "emu-build.log").open("wb") as log:
                rc = subprocess.run(generation, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT).returncode
                if rc == 0:
                    save(out / "generated-auxiliary.json", stage_auxiliary(products))
                    rc = subprocess.run(state["command"], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT).returncode
        finally:
            alterations=restore_generated(ROOT/"build",preserved,original_generated,out/"new-fixed-path-auxiliary")
            save(out/"original-build-restoration.json",dict(status="ORIGINAL_O2_GENERATION_RESTORED",alterations=alterations,files_verified=len(original_generated),original_emu_sha256=sha(original_emu)))

        state.update(build_exit_code=rc, build_finished_utc=now())
        save(out / "build-state.json", state)
        require(rc == 0, "EMU build failed; keep emu-build.log and build/ unchanged")
        for group in ("files", "dependency_files"):
            for path, digest in pins[group].items():
                require(sha(ROOT / path) == digest, "source changed during build: " + path)
        dep_after, dep_files_after = dependency_snapshot()
        require(dep_after == dependencies and dep_files_after == dependency_files, "dependencies changed")
        binary = products / "emu"
        require(binary.is_file(), "successful build has no EMU")
        pins.update(emu_sha256=sha(binary), emu_bytes=binary.stat().st_size, emu_path=str(binary))
        generated = [p for p in sorted(products.rglob("*"))
                     if p.is_file() and (p.suffix in (".sv", ".v", ".h") or p == binary)
                     and "emu-compile" not in p.parts]
        save(out / "generated-artifacts.json", [{"path": p.relative_to(products).as_posix(),
             "bytes": p.stat().st_size, "sha256": sha(p)} for p in generated])
        save(out / "hardware-inputs.json", pins)
        require(sha(original_emu) == original_sha, "original O2 binary changed")
        state.update(status="O1_MATCHED_BUILD_PASS", finished_utc=now(), emu_sha256=pins["emu_sha256"],
                     source_files=len(files), dependency_files=len(dependency_files), dependencies=len(dependencies))
        save(out / "build-state.json", state)
        print(state["status"], flush=True)
        return 0
    except Exception as exc:
        state.update(status="FAILED", error=repr(exc), finished_utc=now())
        save(out / "build-state.json", state)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(main(parser.parse_args().output))
