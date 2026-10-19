"""Resume the generated T14 RTL after the recorded missing-support-file failure."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("matched_builder", HERE / "build_t14.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
ROOT = builder.ROOT


def main(attempt, output):
    require, sha, save, now = builder.require, builder.sha, builder.save, builder.now
    require(not output.exists(), "resume evidence must use a new directory")
    old = json.loads((attempt / "build-state.json").read_text())
    pins = json.loads((attempt / "hardware-inputs-before.json").read_text())
    require(old["status"] == "FAILED" and old["build_exit_code"] == 2, "unexpected prior failure")
    require("chisel_db.cpp" in (attempt / "emu-build.log").read_text(), "not the known auxiliary path failure")
    products = Path(old["build_products"])
    require((products / "rtl/SimTop.sv").exists() and not (products / "emu").exists(), "unexpected product state")
    for group in ("files", "dependency_files"):
        for name, digest in pins[group].items():
            require(sha(ROOT / name) == digest, "hardware drift: " + name)
    require(sha(ROOT / "build/emu") == old["original_o1_emu_sha256"], "original O1 EMU changed")
    output.mkdir()
    state = dict(status="STAGING_AUXILIARY", started_utc=now(), source_commit=builder.git("rev-parse", "HEAD").decode().strip(),
                 generation_source_commit=pins["source_commit"], generation_attempt=str(attempt),
                 original_attempt_status=old["status"], build_products=str(products), flags=old["flags"],
                 scope="same freshly generated T14 RTL, resume compilation after generated support path fix")
    save(output / "build-state.json", state)
    generated_before = {str(p): sha(p) for p in products.rglob("*") if p.is_file()}
    save(output / "generated-before-resume.json", generated_before)
    auxiliary = builder.stage_auxiliary(products)
    save(output / "generated-auxiliary.json", auxiliary)
    shell = old["command"][2]
    require("VDOT_O1_HANDOFF=0" in shell and "BUILD_DIR=" + str(products) in shell, "mode/path binding")
    state.update(status="COMPILING", command=["bash", "-c", shell], build_started_utc=now())
    save(output / "build-state.json", state)
    (output / "build-command.sh").write_text(shell)
    print("T14_MATCHED_RESUME_STARTED", flush=True)
    with (output / "emu-build.log").open("wb") as log:
        rc = subprocess.run(state["command"], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT).returncode
    state.update(build_exit_code=rc, build_finished_utc=now())
    save(output / "build-state.json", state)
    require(rc == 0, "resumed compilation failed; preserve all files")
    require("[mill] Generating Verilog" not in (output / "emu-build.log").read_text(), "unexpected RTL regeneration")
    for path, digest in generated_before.items():
        require(sha(Path(path)) == digest, "original generated input changed: " + path)
    for group in ("files", "dependency_files"):
        for name, digest in pins[group].items():
            require(sha(ROOT / name) == digest, "hardware changed during resumed compilation: " + name)
    deps, dep_files = builder.dependency_snapshot()
    require(dep_files == pins["dependency_files"], "dependency inventory drift")
    save(output / "dependencies.json", deps)
    require(sha(ROOT / "build/emu") == old["original_o1_emu_sha256"], "original O1 EMU changed")
    binary = products / "emu"
    require(binary.is_file(), "missing fresh T14 EMU")
    pins.update(emu_path=str(binary), emu_sha256=sha(binary), emu_bytes=binary.stat().st_size,
                resumed_compile_source_commit=state["source_commit"], generation_attempt=str(attempt),
                generation_build_script_sha256=pins["build_script_sha256"],
                build_script_sha256=sha(Path(__file__)), helper_script_sha256=sha(HERE / "build_t14.py"))
    save(output / "hardware-inputs.json", pins)
    state.update(status="T14_MATCHED_BUILD_PASS", finished_utc=now(), emu_sha256=pins["emu_sha256"],
                 hardware_inputs_unchanged=True, generated_rtl_unchanged=True, original_o1_emu_unchanged=True)
    save(output / "build-state.json", state)
    print(state["status"], flush=True)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raise SystemExit(main(args.attempt, args.output))
