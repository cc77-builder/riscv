"""Validate completed matched T14 compilation without rerunning or changing it.

The original resume wrapper mistakenly hashed mutable host time.log as an input.
This validator excludes only that recorded path and checks all hardware inputs,
generated RTL, staged support files, compiler provenance and both EMU identities.
"""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("matched_builder", HERE / "build_t14.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
ROOT = builder.ROOT


def main(attempt, resumed, output):
    require, sha, save, now = builder.require, builder.sha, builder.save, builder.now
    require(not output.exists(), "validation output already exists")
    state = json.loads((resumed / "build-state.json").read_text())
    require(state.get("build_exit_code") == 0, "actual resumed make did not succeed")
    require(not (resumed / "hardware-inputs.json").exists(), "original wrapper already has a final receipt")
    require((resumed / "wrapper-exit-code.txt").read_text().strip() == "1",
            "record original wrapper audit failure before finalization")
    pins = json.loads((attempt / "hardware-inputs-before.json").read_text())
    products = Path(state["build_products"])
    before = json.loads((resumed / "generated-before-resume.json").read_text())
    mutable = products / "time.log"
    changed = [path for path, digest in before.items() if sha(Path(path)) != digest]
    require(changed == [str(mutable)], "unexpected generated-input drift: " + repr(changed))
    correction = json.loads((resumed / "validation-scope-supplement.json").read_text())
    require(correction["excluded_mutable_file"] == str(mutable), "scope correction path mismatch")
    require(correction["created_utc"] < state["build_finished_utc"], "scope correction was not recorded before completion")
    aux = json.loads((resumed / "generated-auxiliary.json").read_text())
    for row in aux:
        require(sha(Path(row["source"])) == row["sha256"] == sha(Path(row["destination"])),
                "generated support drift: " + row["source"])
    for group in ("files", "dependency_files"):
        for name, digest in pins[group].items():
            require(sha(ROOT / name) == digest, "original hardware drift: " + name)
    require(not builder.git("diff", "HEAD", "--", *builder.HARDWARE), "uncommitted hardware changes")
    deps, dep_files = builder.dependency_snapshot()
    require(dep_files == pins["dependency_files"], "dependency inventory changed")
    require(deps == json.loads((attempt / "dependencies.json").read_text()), "dependency pin list changed")
    o1_emu = ROOT / "build/emu"
    require(sha(o1_emu) == "b13b05a3b03d2dd178d5e07b55bda1e8d99d7a094d44cf30405241f9793170cb",
            "original O1 EMU changed")
    compiler = json.loads((resumed / "actual-compiler.json").read_text())
    require(compiler["invocations"] and all(x["exe"] == "/usr/lib/llvm-19/bin/clang"
            and "Ubuntu clang version 19.1.7" in x["version"] for x in compiler["invocations"]),
            "actual compiler does not match fixed O1 build")
    binary = products / "emu"
    require(binary.is_file() and sha(binary) != sha(o1_emu), "no distinct completed T14 binary")
    require("VDOT_O1_HANDOFF=0" in state["command"][2], "wrong compile mode")
    log = (resumed / "emu-build.log").read_text()
    require("[mill] Generating Verilog" not in log and "Error " not in log,
            "unexpected regeneration or build error")
    output.mkdir()
    pins.update(emu_path=str(binary), emu_sha256=sha(binary), emu_bytes=binary.stat().st_size,
                generation_attempt=str(attempt), resumed_compile=str(resumed),
                compile_source_commit=state["source_commit"],
                validation_source_commit=builder.git("rev-parse", "HEAD").decode().strip(),
                validation_script_sha256=sha(Path(__file__)))
    save(output / "hardware-inputs.json", pins)
    save(output / "dependencies.json", deps)
    generated = [p for p in products.rglob("*") if p.is_file()
                 and (p.suffix in (".sv", ".v", ".h", ".hpp") or p == binary) and "emu-compile" not in p.parts]
    save(output / "generated-artifacts.json", [
        {"path": str(p), "sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(generated)])
    result = dict(status="T14_MATCHED_BUILD_PASS", finished_utc=now(),
                  generation_source_commit=pins["source_commit"], compile_source_commit=state["source_commit"],
                  actual_make_exit_code=0, original_resume_wrapper_exit_code=1,
                  excluded_host_timing_file=str(mutable), excluded_host_timing_before_sha256=before[str(mutable)],
                  excluded_host_timing_after_sha256=sha(mutable), immutable_generated_inputs_verified=len(before)-1,
                  generated_auxiliary_files_verified=len(aux), hardware_files_verified=len(pins["files"]),
                  dependency_files_verified=len(dep_files), dependencies_verified=len(deps),
                  actual_compiler_receipt=str(resumed / "actual-compiler.json"),
                  emu_sha256=pins["emu_sha256"], original_o1_emu_unchanged=True,
                  original_failed_attempts_preserved=True, hardware_inputs_unchanged=True,
                  new_compile_executed=False,
                  scope="independent input/provenance validation of the existing successful resumed compile")
    save(output / "build-state.json", result)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=Path)
    parser.add_argument("--resumed", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raise SystemExit(main(args.attempt, args.resumed, args.output))
