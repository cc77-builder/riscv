#!/usr/bin/env python3
"""R0: verify the frozen O2 baseline and prepare explicit reproduction commands."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = "9b6cf074951dbd51e1670c5fbc7111a97c362b3f"
COMMON = {"VDOT_T14_FUSED_INPUT": "1", "VDOT_O1_HANDOFF": "0", "VDOT_O2_ELASTIC": "1"}
TRACES = ("VDOT_O2_TRACE", "VDOT_T13_TRACE", "VDOT_O1_TRACE", "VDOT_T12_TRACE")
PROFILES = {
    "observe": {**COMMON, **{k: "1" if k in TRACES[:2] else "0" for k in TRACES}},
    "cost": {**COMMON, **{k: "0" for k in TRACES}},
}
TOOL_ARGS = {
    "java": ["-version"], "mill": ["--version"], "verilator": ["--version"],
    "clang++": ["--version"], "make": ["--version"], "python3": ["--version"],
    "riscv64-linux-gnu-gcc": ["--version"], "firtool": ["--version"],
    "yosys": ["-V"], "berkeley-abc": ["-c", "version"], "sta": ["-version"],
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git(*args, root=ROOT):
    return subprocess.check_output(["git", "-C", str(root), *args])


def expand(value, base):
    require(isinstance(value, str) and bool(value), "empty/non-string configured path")
    missing = [name for name in re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", value)
               if not os.environ.get(name)]
    require(not missing, "unset path variables: " + ", ".join(missing))
    value = os.path.expandvars(value)
    require("$" not in value, "unexpanded variable in configured path: " + value)
    path = Path(value).expanduser()
    return (path if path.is_absolute() else base / path).resolve()


def member(roots, item):
    require(isinstance(item, dict) and set(item) >= {"root", "path"}, "invalid logical path")
    require(item["root"] in roots, "unknown logical root: " + str(item["root"]))
    rel = Path(item["path"])
    require(not rel.is_absolute() and ".." not in rel.parts, "unsafe logical path: " + str(rel))
    root = roots[item["root"]]
    path = (root / rel).resolve()
    require(path.is_relative_to(root), "logical path escapes root: " + str(rel))
    return path


def load_config(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    require(data.get("schema_version") == 1, "wrong config schema")
    require(set(data) == {"schema_version", "roots", "locations", "tools"}, "unknown/missing config fields")
    roots = {k: expand(v, path.parent) for k, v in data["roots"].items()}
    require(set(roots) == {"repo", "lab", "xs_env", "system", "java", "firtool"}, "wrong configured roots")
    require(roots["repo"] == ROOT, "config repo is not this checkout")
    locations = {k: member(roots, v) for k, v in data["locations"].items()}
    require(set(locations) == {"t12", "t14", "dense", "g4_images", "o3_images", "cost_work",
                               "o2_pins", "o1_pins", "o2_emu", "o1_emu"}, "wrong locations")
    require(set(data["tools"]) == set(TOOL_ARGS), "incomplete tool map")
    tools = {k: expand(v, path.parent) for k, v in data["tools"].items()}
    require((roots["firtool"] / "firtool").resolve() == tools["firtool"],
            "configured firtool directory differs from verified tool")
    return data, roots, locations, tools


def verify_file(path, expected):
    require(path.is_file(), "missing input: " + str(path))
    require(sha(path) == expected, "SHA-256 mismatch: " + str(path))


def verify_profiles(path):
    require(json.loads(path.read_text()) == PROFILES, "profile matrix changed or mixes O1/O2")


def verify_source(lock, roots, pins):
    source = lock["source"]
    require(source["baseline_commit"] == BASE, "unexpected baseline commit")
    require(git("merge-base", "--is-ancestor", BASE, "HEAD").strip() == b"", "baseline is not an ancestor")
    require(not git("diff", BASE, "--", "src", "scripts", "Makefile", "Makefile.test",
                    "team/scripts/activate.sh"), "unreviewed production/build input changes")
    require(not git("ls-files", "--others", "--exclude-standard", "--", "src", "scripts",
                    "build.sc", "Makefile", "Makefile.test", "team/scripts/activate.sh"),
            "untracked production/build inputs")
    drifts = []
    for group in ("files", "dependency_files"):
        for rel, digest in pins[group].items():
            require(not Path(rel).is_absolute() and ".." not in Path(rel).parts, "unsafe source pin")
            expected = source["current_build_sc_sha256"] if rel == "build.sc" and group == "files" else digest
            verify_file(roots["repo"] / rel, expected)
            if expected != digest:
                drifts.append(rel)
    require(drifts == ["build.sc"], "unexpected baseline source delta")
    require(git("rev-parse", "HEAD:src").decode().strip() == source["production_src_tree"],
            "production source tree differs from baseline")
    # bind the one accepted build-file delta to the reviewed immutable Git blob.
    blob = git("show", BASE + ":build.sc")
    require(hashlib.sha256(blob).hexdigest() == source["current_build_sc_sha256"],
            "unrecognized build.sc exception")
    patch = git("diff", source["emu_build_commit"], BASE, "--", "build.sc")
    require(hashlib.sha256(patch).hexdigest() == source["build_sc_delta_sha256"], "build delta changed")
    return {"hardware_files": len(pins["files"]), "dependency_files": len(pins["dependency_files"]),
            "accepted_delta": drifts, "legacy_hardware_guard_matches_current_build_sc": False}


def verify_dependencies(lock, roots):
    records = lock["dependencies"]
    for item in records:
        path = roots["repo"] / item["path"]
        require(git("rev-parse", "--show-toplevel", root=path).decode().strip() == str(path),
                "dependency is not an independent Git checkout: " + str(path))
        require(git("rev-parse", "HEAD", root=path).decode().strip() == item["pin"],
                "dependency revision drift: " + item["path"])
        require(not git("status", "--porcelain=v1", "--untracked-files=normal", root=path),
                "dirty dependency: " + item["path"])
    return len(records)


def verify_binding(lock, roots, locations):
    normal = locations["t12"] / "nemu/reference/build/riscv64-nemu-interpreter-so"
    negative = locations["t12"] / "build-evidence/negative-reference.so"
    probe = subprocess.run(["readelf", "-d", str(negative)], capture_output=True, text=True, timeout=30)
    require(probe.returncode == 0, "cannot read negative-reference ELF dependencies")
    binding = lock["negative_reference_binding"]
    require(binding in probe.stdout, "negative wrapper binding differs")
    require(normal.resolve() == Path(binding).resolve(),
            "frozen negative wrapper binds " + binding +
            "; restore its original reference location, or create a separately versioned wrapper/contract in R4")
    return {"linked_reference": binding, "portable_without_rebuild": False}


def environment(roots, tools, profile):
    env = os.environ.copy()
    # Drop inherited VDOT switches, then explicitly set every reviewed profile flag.
    for key in list(env):
        if key.startswith("VDOT_"):
            del env[key]
    env.update(PROFILES[profile])
    env.update(JAVA_HOME=str(roots["java"]), TEAM_XS_ENV_ROOT=str(roots["xs_env"]),
               CHISEL_FIRTOOL_PATH=str(roots["firtool"]), PYTHONDONTWRITEBYTECODE="1")
    env["PATH"] = os.pathsep.join(dict.fromkeys(str(p.parent) for p in tools.values())) + os.pathsep + env.get("PATH", "")
    return env


def verify_tools(lock, tools, output, env):
    rows = {}
    for name, args in TOOL_ARGS.items():
        path = tools[name]
        verify_file(path, lock["tools"][name]["sha256"])
        command = [str(path), *args]
        process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=45)
        (output / (name.replace("+", "p") + "-version.stdout.log")).write_bytes(process.stdout)
        (output / (name.replace("+", "p") + "-version.stderr.log")).write_bytes(process.stderr)
        require(process.returncode == 0, "tool version probe failed: " + name)
        version = (process.stdout + process.stderr).decode("utf-8", errors="strict")
        require(lock["tools"][name]["version_marker"] in version, "wrong version: " + name)
        rows[name] = {"path": str(path), "sha256": sha(path), "exit_code": process.returncode,
                      "version": version.strip()}
    return rows


def legacy_preflight(locations, output, env):
    command = [sys.executable, "-B", str(ROOT / "team/optimizations/o2/fullcore/run_suite.py"),
               "--output", str(output / "legacy-inputs"), "--preflight-only",
               "--t12-root", str(locations["t12"]), "--t14-root", str(locations["t14"]),
               "--dense-build", str(locations["dense"])]
    process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True)
    (output / "legacy.stdout.log").write_bytes(process.stdout)
    (output / "legacy.stderr.log").write_bytes(process.stderr)
    save(output / "legacy-command.json", {"command": command, "exit_code": process.returncode})
    require(process.returncode == 0, "frozen input/provenance preflight failed; inspect legacy.stderr.log")
    result = json.loads((output / "legacy-inputs/result.json").read_text())
    require(result.get("status") == "O2_PREFLIGHT_ONLY_PASS" and result.get("emulators_executed") == 0,
            "unexpected legacy preflight result")
    return result


def command_recipes(locations, roots, tools, config, lock_path, output, profile):
    common = [str(tools["python3"]), "-B", str(HERE / "repro.py"),
              "build", "--config", str(config), "--lock", str(lock_path),
              "--profile", profile, "--output", str(output / "NEW-BUILD-OUTPUT")]
    flags = PROFILES[profile]
    cost = ["bash", "-c", 'source team/scripts/activate.sh\nexec "$@"', "o2-r0",
            str(tools["mill"]), "-i", "-j", "2", "vdotCost.runMain", "team.vdot.GenerateVDotCost",
            "parent", str(output / "NEW-COST-RTL")]
    return {
        "commands_executed": False, "profile": profile, "flags": flags,
        "fullcore_build": {"argv": common, "requires": "fresh checkout with no build/; all baseline assets restored"},
        "cost_rtl": {"argv": cost, "profile_required": "cost", "cwd": str(ROOT),
                     "environment": {**PROFILES["cost"], "JAVA_HOME": str(roots["java"]),
                                     "TEAM_XS_ENV_ROOT": str(roots["xs_env"]),
                                     "CHISEL_FIRTOOL_PATH": str(roots["firtool"])},
                     "requires": "new output directory; use configured tools in PATH"},
        "core_run": {"argv": [str(tools["python3"]), "-B",
                    str(ROOT / "team/optimizations/o2/fullcore/run_suite.py"),
                    "--output", str(output / "NEW-CORE-OUTPUT"),
                    "--hardware-pins", "NEW-BUILD/hardware-inputs.json", "--emu", "NEW-CHECKOUT/build/emu",
                    "--t12-root", str(locations["t12"]), "--t14-root", str(locations["t14"]),
                    "--dense-build", str(locations["dense"]), "--jobs", "1"],
                     "requires": "new observe-profile build pins; B0 pins reject current build.sc"},
        "limits": ["Recipes are not build/run evidence.", "Do not use cost trace settings for G3.",
                   "The frozen negative wrapper still requires its linked absolute normal-reference path.",
                   "Current root build/ is preserved; this R0 command does not migrate or delete it."],
    }


def run(args):
    output = args.output.resolve()
    require(not output.is_relative_to(ROOT), "output must be outside checkout")
    output.mkdir(parents=True, exist_ok=False)
    result = {"status": "R0_RUNNING", "started_utc": datetime.now(timezone.utc).isoformat(),
              "action": args.action, "profile": args.profile, "emulators_executed": 0,
              "new_hardware_built": False, "independent_member_reproduction": False}
    save(output / "result.json", result)
    try:
        config = args.config.resolve()
        lock_path = args.lock.resolve()
        _, roots, locations, tools = load_config(config)
        lock = json.loads(lock_path.read_text())
        for name, item in lock["locations"].items():
            require(locations[name] == member(roots, item), "location differs from frozen layout: " + name)
        require(lock.get("schema_version") == 1, "wrong lock schema")
        verify_profiles(HERE / "profiles.json")
        env = environment(roots, tools, args.profile)
        result.update(source_commit=git("rev-parse", "HEAD").decode().strip(),
                      config_sha256=sha(config), lock_sha256=sha(lock_path),
                      entry_sha256=sha(Path(__file__)),
                      builder_sha256=sha(ROOT / "team/optimizations/o2/fullcore/build_fullcore.py"),
                      flags=PROFILES[args.profile])
        (output / "source-status.txt").write_bytes(git("status", "--short"))
        (output / "working-tree.patch").write_bytes(git("diff", "--binary", "HEAD"))
        for item in lock["artifacts"]:
            verify_file(member(roots, item), item["sha256"])
        pins = json.loads(locations["o2_pins"].read_text())
        for key, value in PROFILES["observe"].items():
            require(pins.get(key) == value, "B0 is not an O2 observe-profile build: " + key)
        require(pins["source_commit"] == lock["source"]["emu_build_commit"], "wrong B0 build commit")
        require(pins["emu_sha256"] == lock["o2_emu_sha256"], "wrong B0 EMU identity")
        verify_file(locations["o2_emu"], pins["emu_sha256"])
        result["source_check"] = verify_source(lock, roots, pins)
        result["dependency_checkouts"] = verify_dependencies(lock, roots)
        result["negative_binding"] = verify_binding(lock, roots, locations)
        result["tools"] = verify_tools(lock, tools, output, env)
        legacy_preflight(locations, output, env)
        result.update(artifacts_checked=len(lock["artifacts"]), legacy_input_preflight_pass=True,
                      existing_build_preserved=(ROOT / "build").exists())
        recipes = command_recipes(locations, roots, tools, config, lock_path, output, args.profile)
        save(output / "commands.json", recipes)
        if args.action == "build":
            require(not (ROOT / "build").exists(), "build/ exists: use a fresh checkout; nothing was deleted")
            command = [str(tools["python3"]), "-B",
                       str(ROOT / "team/optimizations/o2/fullcore/build_fullcore.py"),
                       "--output", str(output / "build"), "--profile", args.profile,
                       "--firtool-dir", str(roots["firtool"])]
            save(output / "build-command.json", {"argv": command, "profile": args.profile})
            with (output / "build.stdout.log").open("wb") as out, (output / "build.stderr.log").open("wb") as err:
                process = subprocess.run(command, cwd=ROOT, env=env, stdout=out, stderr=err)
            result["build_exit_code"] = process.returncode
            require(process.returncode == 0, "build failed; preserve complete logs and build/")
            result["new_hardware_built"] = True
            result["status"] = "O2_R0_BUILD_PASS"
        else:
            result["status"] = "O2_R0_PREFLIGHT_PASS"
        result["finished_utc"] = datetime.now(timezone.utc).isoformat()
        save(output / "result.json", result)
        print(result["status"] + " emulators_executed=0 independent_member_reproduction=false")
        return 0
    except Exception as exc:
        result.update(status="O2_R0_FAILED", error=str(exc),
                      finished_utc=datetime.now(timezone.utc).isoformat())
        save(output / "result.json", result)
        print("O2_R0_FAILED " + str(exc), file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["preflight", "commands", "build"])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--lock", type=Path, default=HERE / "baseline-lock.json")
    parser.add_argument("--profile", choices=PROFILES, default="observe")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
