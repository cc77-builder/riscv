"""Execute an explicit split native recipe, retaining every phase result.

Scala compilation/elaboration finish before serial FIR lowering begins. This
entry point only accepts a fresh build/ and never resumes interrupted output.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess

import build_recipe as recipe

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def environment(pins):
    # The parent activated the project in a restricted environment. Preserve
    # only that explicit project configuration and the pins' VDOT switches.
    env = recipe.environment()
    for name in ("LINUX_GNU_TOOLCHAIN", "XS_PROJECT_ROOT", "NOOP_HOME", "NEMU_HOME", "AM_HOME",
                 "DRAMSIM3_HOME", "CHISEL_FIRTOOL_PATH"):
        if name in os.environ:
            env[name] = os.environ[name]
    for name, value in pins.items():
        if name.startswith("VDOT_"):
            require(os.environ.get(name) == value, "parent VDOT configuration differs: " + name)
            env[name] = value
    return env


def verify_tools(contract, root):
    recipe.validate(contract)
    require(contract.get("profile") in recipe.SPLIT_PROFILES, "split executor requires split contract")
    require(sha(__file__) == contract["split_script_sha256"], "split executor changed")
    require(sha(recipe.__file__) == contract["recipe_sha256"], "native recipe changed")
    require(sha(root / ".mill-version") == contract["launch_metadata"][".mill-version"]["sha256"],
            "Mill launcher metadata changed")
    for tool in contract["compilers"].values():
        require(sha(tool["path"]) == tool["sha256"], "native tool payload changed: " + tool["path"])
        if "payload_path" in tool:
            require(str(Path(tool["path"]).resolve()) == tool["payload_path"],
                    "native driver payload target changed: " + tool["path"])
    if "verilator_support" in contract:
        require(recipe.verilator_support(contract["verilator_support"]["root"]) == contract["verilator_support"],
                "Verilator runtime/template inventory changed")
        require(recipe.compiler_runtime(contract["compilers"]) == contract["compiler_runtime"],
                "native compiler library inventory changed")
    for name, role in (("mill", "mill"), ("java", "java"), ("verilator", "verilator"), ("python3", "python")):
        selected = shutil.which(name)
        require(selected is not None and str(Path(selected).resolve()) == contract["compilers"][role]["path"],
                "activated native tool differs: " + name)


def commands(contract):
    recipe.validate(contract)
    require(contract.get("profile") in recipe.SPLIT_PROFILES, "split commands require split contract")
    phases = contract["phases"]
    tools = contract["compilers"]
    return {
        "scala-compile": [*contract["mill_launch"], *phases[0]["mill_args"]],
        "fir-elaborate": [tools["make"]["path"], *phases[1]["make_args"], *recipe.make_overrides(contract)],
        "fir-lower": [tools["firtool"]["path"], *phases[2]["firtool_args"]],
        "memory-generate": [tools["bash"]["path"], phases[3]["script"], *phases[3]["arguments"]],
        "native-compile": shlex.split(recipe.make_command(contract)),
    }


def rtl_inventory(root):
    return {path.relative_to(root).as_posix(): sha(path) for path in sorted((root / "build/rtl").glob("*"))
            if path.is_file() and path.suffix in (".sv", ".v", ".conf")}


def postprocess(root):
    """The root Makefile's default simulation postprocessing, after mem-gen."""
    top = root / "build/rtl/SimTop.sv"
    require(top.is_file(), "serial lowering produced no SimTop.sv")
    history = subprocess.check_output(["git", "log", "-n", "1"], cwd=root)
    history += subprocess.check_output(["git", "diff"], cwd=root)
    header = b"".join(b"//" + line + b"\n" for line in history.splitlines())
    top.write_bytes(header + top.read_bytes())
    for path in (root / "build/rtl").glob("*.sv"):
        body = path.read_bytes().replace(b"$fatal", b"xs_assert_v2(`__FILE__, `__LINE__)")
        path.write_bytes(body.replace(b"$error(", b"$fwrite(32'h80000002, "))


def run(pins_path, output, root=ROOT):
    root = Path(root).resolve()
    output = Path(output).resolve()
    require(not output.exists() and not output.is_relative_to(root), "split output must be fresh and outside checkout")
    require(not (root / "build").exists(), "split recipe must not reuse existing build/")
    pins = json.loads(Path(pins_path).read_text(encoding="utf-8"))
    contract = pins["native_build_contract"]
    verify_tools(contract, root)
    require(pins.get("source_root") == str(root), "split pins refer to another checkout")
    pins_sha = sha(pins_path)
    output.mkdir(parents=True)
    state = dict(status="RUNNING", profile=contract["profile"], started=now(), phases=[], pins_sha256=pins_sha)
    save(output / "state.json", state)
    env = environment(pins)
    argv = commands(contract)
    prepared = None
    fir_sha = None
    try:
        for phase in contract["phases"]:
            name = phase["name"]
            require(sha(pins_path) == pins_sha, "hardware pins changed during split recipe")
            verify_tools(contract, root)
            row = dict(name=name, status="RUNNING", started=now(), environment=phase.get("environment", {}))
            state["phases"].append(row)
            save(output / "state.json", state)
            print("SPLIT_PHASE_STARTED " + name, flush=True)
            if name == "rtl-postprocess":
                row["implementation"] = phase["implementation"]
                postprocess(root)
                prepared = rtl_inventory(root)
                require(prepared and "build/rtl/SimTop.sv" in prepared, "prepared RTL inventory incomplete")
                save(output / "prepared-rtl.json", prepared)
            else:
                if name == "fir-lower":
                    require(not (root / "build/rtl/SimTop.sv").exists(), "unexpected pre-lowered RTL")
                    fir_sha = sha(root / "build/rtl/SimTop.fir")
                    save(output / "fir-input.json", dict(path="build/rtl/SimTop.fir", sha256=fir_sha))
                if name == "native-compile":
                    require(prepared == rtl_inventory(root), "prepared RTL changed before compilation")
                command = [contract["compilers"]["time"]["path"], "-v", "-o", str(output / (name + ".time.log")), *argv[name]]
                row["command"] = command
                save(output / "state.json", state)
                save(output / (name + ".command.json"), command)
                with (output / (name + ".log")).open("wb") as log:
                    rc = subprocess.run(command, cwd=root, env=env | phase.get("environment", {}),
                                        stdout=log, stderr=subprocess.STDOUT).returncode
                row["exit_code"] = rc
                save(output / "state.json", state)
                require(rc == 0, "split phase failed: " + name)
                if name == "fir-elaborate":
                    require((root / "build/rtl/SimTop.fir").is_file(), "elaboration produced no FIR")
                if name == "fir-lower":
                    require(sha(root / "build/rtl/SimTop.fir") == fir_sha, "FIR changed during lowering")
                    require((root / "build/rtl/SimTop.sv").is_file() and (root / "build/rtl/SimTop.sv.conf").is_file(),
                            "lowering produced incomplete RTL")
                    save(output / "lowered-rtl.json", rtl_inventory(root))
                if name == "native-compile":
                    require(prepared == rtl_inventory(root), "Make regenerated or changed prepared RTL")
                    require((root / "build/emu").is_file(), "native phase produced no EMU")
            verify_tools(contract, root)
            row.update(status="PASS", finished=now())
            save(output / "state.json", state)
            print("SPLIT_PHASE_PASS " + name, flush=True)
        state.update(status="SPLIT_NATIVE_BUILD_PASS", finished=now(), emu_sha256=sha(root / "build/emu"))
        save(output / "state.json", state)
        return 0
    except Exception as error:
        if state["phases"] and state["phases"][-1]["status"] == "RUNNING":
            state["phases"][-1].update(status="FAILED", finished=now(), error=repr(error))
        state.update(status="FAILED", error=repr(error), finished=now())
        save(output / "state.json", state)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pins", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.pins, args.output))
