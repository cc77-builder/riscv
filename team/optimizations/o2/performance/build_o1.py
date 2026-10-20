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

sys.path.append(str(Path(__file__).resolve().parents[2] / "o1"))
from build_inputs import HARDWARE, hardware_files, verify_dependencies, verify_hardware_files
import build_recipe
sys.path.append(str(Path(__file__).resolve().parents[1] / "fullcore"))
import live_inputs

ROOT = Path(__file__).resolve().parents[4]
FLAGS = {"VDOT_O1_HANDOFF": "1", "VDOT_O2_ELASTIC": "0", "VDOT_T14_FUSED_INPUT": "1",
         "VDOT_O1_TRACE": "1", "VDOT_O1_TRACE_PROFILE": "events", "VDOT_O2_TRACE": "0", "VDOT_T12_TRACE": "0", "VDOT_T13_TRACE": "1"}


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
    return live_inputs.dependency_snapshot(ROOT)


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

def validate_reference(pins, state, files, dependency_files, contract, original_sha):
    build_recipe.validate(contract)
    require(state.get("status") == "O2_FULLCORE_BUILD_PASS" and
            type(state.get("build_exit_code")) is int and state["build_exit_code"] == 0,
            "reference O2 build did not complete")
    require(state.get("source_commit") == pins.get("source_commit") and
            pins.get("source_commit") == git("rev-parse", "HEAD").decode().strip(),
            "reference O2 source identity differs")
    require(pins.get("emu_sha256") == state.get("emu_sha256") == original_sha,
            "reference O2 binary identity drift")
    require(pins.get("files") == files and pins.get("dependency_files") == dependency_files,
            "reference O2 compiler inputs differ")
    require(pins.get("native_build_contract") == contract, "reference native build contract differs")
    expected = dict(FLAGS, VDOT_O1_HANDOFF="0", VDOT_O2_ELASTIC="1",
                    VDOT_O1_TRACE="0", VDOT_O2_TRACE="1", config="MinimalConfig",
                    NUM_CORES=1, EMU_THREADS=1, JVM_XMX="12G", BUILD_JOBS=2)
    expected.pop("VDOT_O1_TRACE_PROFILE")
    require(all(type(pins.get(k)) is type(v) and pins[k] == v for k, v in expected.items()),
            "reference O2 build profile differs")
    require(pins.get("emu_path") == str(ROOT / "build/emu"), "reference O2 binary path differs")


def main(out, o2_build=None):
    out = out.resolve()
    require(not out.exists(), "output already exists")
    require(not out.is_relative_to(ROOT), "output must be outside checkout")
    products = out / "products"
    require(not products.exists(), "fresh products directory required")
    original_emu = ROOT / "build/emu"
    original_sha = sha(original_emu)
    require(o2_build is not None, "--o2-build is required for current source-bound builds; use frozen tools for historical builds")
    o2_build = o2_build.resolve()
    reference_files = {p: sha(p) for p in (o2_build / "hardware-inputs.json", o2_build / "build-state.json")}
    baseline = json.loads((o2_build / "hardware-inputs.json").read_text())
    baseline_state = json.loads((o2_build / "build-state.json").read_text())
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
        files = hardware_files(ROOT)
        contract = build_recipe.capture(ROOT)
        clean = build_recipe.environment()
        dependencies, dependency_files = dependency_snapshot()
        save(out / "dependencies.json", dependencies)
        pins = {"source_commit": state["source_commit"], "config": "MinimalConfig",
                "NUM_CORES": 1, "EMU_THREADS": 1, "JVM_XMX": "12G", "BUILD_JOBS": 2,
                **FLAGS, "native_build_contract": contract, "files": dict(sorted(files.items())), "dependency_files": dependency_files,
                "build_tools": {str(p.relative_to(ROOT)): sha(p) for p in
                    (Path(__file__), Path(live_inputs.__file__), Path(build_recipe.__file__))},
                "build_script_sha256": sha(Path(__file__)), "source_root": str(ROOT)}
        save(out / "hardware-inputs-before.json", pins)
        validate_reference(baseline, baseline_state, files, dependency_files, contract, original_sha)
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
                                    stdout=log, stderr=subprocess.STDOUT, env=clean).returncode
            require(rc == 0, "missing tool " + name)
        shell = activated + "export " + " ".join(k + "=" + v for k, v in FLAGS.items()) + "\n"
        shell += 'export CHISEL_FIRTOOL_PATH="$HOME/.cache/llvm-firtool/1.62.1/bin"\n'
        shell += build_recipe.make_command(contract, products)
        (out / "build-command.sh").write_text(shell, encoding="utf-8")
        state.update(status="BUILDING", build_started_utc=now(), command=["bash", "-c", shell])
        save(out / "build-state.json", state)
        print("O1_MATCHED_BUILD_STARTED " + str(out), flush=True)
        generation = ["bash", "-c", shell.replace("make emu ", "make sim-verilog ", 1)]
        state["generation_command"] = generation
        save(out / "build-state.json", state)
        try:
            with (out / "emu-build.log").open("wb") as log:
                rc = subprocess.run(generation, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, env=clean).returncode
                if rc == 0:
                    save(out / "generated-auxiliary.json", stage_auxiliary(products))
                    rc = subprocess.run(state["command"], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, env=clean).returncode
        finally:
            alterations=restore_generated(ROOT/"build",preserved,original_generated,out/"new-fixed-path-auxiliary")
            save(out/"original-build-restoration.json",dict(status="ORIGINAL_O2_GENERATION_RESTORED",alterations=alterations,files_verified=len(original_generated),original_emu_sha256=sha(original_emu)))

        state.update(build_exit_code=rc, build_finished_utc=now())
        save(out / "build-state.json", state)
        require(rc == 0, "EMU build failed; keep emu-build.log and build/ unchanged")
        for group in ("files", "dependency_files"):
            for path, digest in pins[group].items():
                require(sha(ROOT / path) == digest, "source changed during build: " + path)
        require(all(sha(ROOT / name) == digest for name, digest in pins["build_tools"].items()),
                "build tooling changed during compilation")
        verify_hardware_files(ROOT, pins["files"])
        build_recipe.verify(ROOT, contract)
        dep_after, dep_files_after = dependency_snapshot()
        require(dep_after == dependencies and dep_files_after == dependency_files, "dependencies changed")
        require(all(sha(p) == digest for p, digest in reference_files.items()), "reference build receipts changed")
        require(sha(original_emu) == original_sha, "original O2 binary changed")
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
    parser.add_argument("--o2-build", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(main(args.output, args.o2_build))
