#!/usr/bin/env python3
"""Build only the isolated dot16 ISS candidate; never write an existing reference."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time

REV = "a48a11f208ff81ad765591d83271d1b339fb3861"
REPO_REV = "c981529dc6e493fb7deee8429b9ce05fd197497b"
DIFFSTATE = "6a2ce3ab51893908f74452522ab03c553cf7fa7e8aa25f74ea84d79aa45f044d"
LEGACY_PATCH = "6c165bf5f94ef0bfb4f894a5f06eb6d620d4a7e0e12f3b1400fa72811f5d24db"
CANDIDATE_PATCH = "d803d7bd6c6c89ae759e76477b63e50e680dc6ce56e9e3898259f4e428b91966"
DEPENDENCIES = {
    "resource/nanopb": ("26e4b21317f88a66fb351f5aa3d8cc0083622b25", "https://github.com/nanopb/nanopb.git"),
    "resource/LibCheckpoint": ("1d8905cc2803c242ef257569128c2e68bf4272aa", "https://github.com/OpenXiangShan/LibCheckpoint.git"),
    "resource/LibCheckpoint/resource/nanopb": ("671672b4d7994a9b07a307ae654885c7202ae886", "https://github.com/nanopb/nanopb"),
    "resource/gcpt_restore": ("5169da768d18f4682a489eaabe7c071df6d6ef88", "https://github.com/OpenXiangShan/LibCheckpointAlpha.git"),
    "resource/softfloat/repo": ("a0c6494cdc11865811dec815d5c0049fba9d82a8", "https://github.com/ucb-bar/berkeley-softfloat-3"),
}
CONTROL = ("API_CONTRACT.md", "build_reference.py", "run_reference_api.py",
           "reference_api.cpp", "manifest.json", "dot16-s8x16-r32-v0.1.patch")


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def reap_group(process):
    """Only the process group created by this invocation may be stopped."""
    def exists():
        try:
            os.killpg(process.pid, 0)
            return True
        except ProcessLookupError:
            return False
    if not exists():
        process.wait()
        return True
    for sig, seconds in [(signal.SIGTERM, 5), (signal.SIGKILL, 5)]:
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            process.poll()
            if not exists():
                process.wait()
                return True
            time.sleep(0.05)
    return False


def write_json(path, data):
    Path(path).write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def load_guard(path):
    spec = importlib.util.spec_from_file_location("dot16_fixed_guard", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.DEPENDENCIES == {k: v[0] for k, v in DEPENDENCIES.items()}, "dependency pin drift")
    return module


class Job:
    def __init__(self, output, phase):
        self.output = output
        self.state = {"phase": phase, "started": utc(), "status": "RUNNING", "commands": [],
                      "cpu_affinity": sorted(os.sched_getaffinity(0)), "workers": 1}
        self.flush()

    def flush(self):
        write_json(self.output / "state.json", self.state)

    def command(self, name, argv, cwd, env=None, timeout=900):
        record = {"name": name, "argv": [str(x) for x in argv], "cwd": str(cwd),
                  "started": utc(), "process_started": False}
        self.state["commands"].append(record)
        self.flush()
        start = time.monotonic()
        with (self.output / (name + ".stdout.log")).open("wb") as out, \
                (self.output / (name + ".stderr.log")).open("wb") as err:
            process = None
            try:
                process = subprocess.Popen(record["argv"], cwd=cwd, env=env, stdout=out, stderr=err,
                                           start_new_session=True)
                record.update(process_started=True, pid=process.pid)
                self.flush()
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    record["timed_out"] = True
            finally:
                record["process_group_absent"] = process is None or reap_group(process)
                self.flush()
            require(record["process_group_absent"], "command process group still present: " + name)
            rc = process.returncode
        record.update(returncode=rc, finished=utc(), seconds=time.monotonic() - start,
                      stdout_sha256=sha(self.output / (name + ".stdout.log")),
                      stderr_sha256=sha(self.output / (name + ".stderr.log")))
        self.flush()
        print(json.dumps(record), flush=True)
        require(rc == 0 and not record.get("timed_out"), "command did not complete: " + name)

    def finish(self, status, **fields):
        self.state.update(status=status, finished=utc(), **fields)
        self.flush()
        print(json.dumps({k: v for k, v in self.state.items() if k != "commands"}), flush=True)


def verify_controls(work):
    identity = json.loads((work / "inputs/control.json").read_text())
    for rel, digest in identity["sha256"].items():
        require(sha(work / "inputs" / rel) == digest, "frozen control changed: " + rel)
    return identity


def snapshot(source, guard, manifest, build=None):
    result = guard.audit_repo(source, REV, manifest["patched_source_sha256"],
                              generated=("include/config", "include/generated/autoconf.h"))
    for rel, (revision, _) in DEPENDENCIES.items():
        child = source / rel
        subset = guard.audit_repo(child, revision)
        result.update({rel + "/" + k: v for k, v in subset.items()})
        if (child / "CONFIG.mk").exists():
            result[rel + "/CONFIG.mk"] = sha(child / "CONFIG.mk")
    # The completed default build directory is preserved here before the next configuration.
    if build:
        import shlex
        for dependency in build.rglob("*.d"):
            logical = dependency.read_text().replace("\\\n", "")
            if ":=" in logical:
                continue
            for line in logical.splitlines():
                if ":" not in line:
                    continue
                for name in shlex.split(line.split(":", 1)[1]):
                    path = (source / name).resolve()
                    if path.is_relative_to(source):
                        rel = path.relative_to(source).as_posix()
                        require(rel in result and sha(path) == result[rel], "unbound compiled input: " + rel)
                    else:
                        require(path.is_relative_to(Path("/usr")), "unexpected external input: " + str(path))
                        result["@system/" + str(path)] = sha(path)
    return result


def prepare(args, work):
    root, base, diffstate = args.repository.resolve(), args.base.resolve(), args.diffstate.resolve()
    leaf = root / "team/optimizations/o2/dot16/nemu"
    require(not work.exists(), "workspace already exists; inspect its original receipt")
    require(not work.is_relative_to(base) and not base.is_relative_to(work), "overlapping donor/output")
    require(not work.is_relative_to(root) and not root.is_relative_to(work), "output overlaps source tree")
    require(git(root, "rev-parse", "HEAD") == REPO_REV, "superproject revision mismatch")
    require(sha(Path(__file__)) == sha(leaf / "build_reference.py"), "running builder differs from frozen candidate")
    require(git(base, "rev-parse", "HEAD") == REV, "base revision mismatch")
    require(not git(base, "status", "--porcelain", "--untracked-files=no"), "base tracked changes")
    for rel, (revision, _) in DEPENDENCIES.items():
        require(git(base / rel, "rev-parse", "HEAD") == revision, "donor dependency pin: " + rel)
        require(not git(base / rel, "status", "--porcelain", "--untracked-files=all"),
                "donor dependency edits: " + rel)
    require(sha(diffstate) == DIFFSTATE, "DUT generated state header mismatch")
    require(sha(leaf / "dot16-s8x16-r32-v0.1.patch") == CANDIDATE_PATCH, "candidate patch mismatch")
    require(sha(root / "team/patches/nemu/vdot-s8x8-r32-v0.1.patch") == LEGACY_PATCH, "legacy patch mismatch")
    for rel in CONTROL:
        require((leaf / rel).is_file(), "missing controller: " + rel)
    work.mkdir(parents=True)
    output = work / "prepare-01"; output.mkdir()
    job = Job(output, "prepare")
    try:
        inputs = work / "inputs"; inputs.mkdir()
        for rel in CONTROL:
            shutil.copyfile(leaf / rel, inputs / rel)
        shutil.copyfile(root / "team/scripts/artifact_guard.py", inputs / "artifact_guard.py")
        shutil.copyfile(root / "team/patches/nemu/manifest.json", inputs / "legacy-manifest.json")
        shutil.copyfile(root / "team/patches/nemu/vdot-s8x8-r32-v0.1.patch", inputs / "legacy.patch")
        shutil.copyfile(diffstate, inputs / "diffstate.h")
        identity = {"repository_head": git(root, "rev-parse", "HEAD"), "base": str(base),
                    "base_rev": REV, "diffstate_origin": str(diffstate),
                    "sha256": {p.name: sha(p) for p in sorted(inputs.iterdir()) if p.is_file()}}
        write_json(inputs / "control.json", identity)
        manifest = json.loads((inputs / "manifest.json").read_text())
        legacy = json.loads((inputs / "legacy-manifest.json").read_text())
        require(manifest["base_rev"] == REV and manifest["patch_sha256"] == CANDIDATE_PATCH,
                "candidate manifest mismatch")
        require(legacy["base_rev"] == REV and legacy["patch_sha256"] == LEGACY_PATCH,
                "legacy manifest mismatch")
        source = work / "source"
        job.command("clone-source", ["git", "-c", "pack.threads=1", "clone", "--no-local",
                    "--no-checkout", "--no-recurse-submodules", base, source], work)
        job.command("checkout-source", ["git", "-C", source, "checkout", "--detach", REV], work)
        job.command("origin-source", ["git", "-C", source, "remote", "set-url", "origin",
                    "https://github.com/OpenXiangShan/NEMU.git"], work)
        for number, (rel, (revision, url)) in enumerate(DEPENDENCIES.items()):
            destination = source / rel
            require(not destination.exists() or not any(destination.iterdir()), "nonempty dependency: " + rel)
            destination.parent.mkdir(parents=True, exist_ok=True)
            job.command(f"clone-dep-{number}", ["git", "-c", "pack.threads=1", "clone", "--no-local",
                        "--no-checkout", "--no-recurse-submodules", base / rel, destination], work)
            job.command(f"checkout-dep-{number}", ["git", "-C", destination, "checkout", "--detach", revision], work)
            job.command(f"origin-dep-{number}", ["git", "-C", destination, "remote", "set-url", "origin", url], work)
        for name, patch, expected in [
            ("legacy", inputs / "legacy.patch", manifest["legacy_patched_source_sha256"]),
            ("dot16", inputs / "dot16-s8x16-r32-v0.1.patch", manifest["patched_source_sha256"])]:
            job.command(name + "-check", ["git", "-C", source, "apply", "--check", patch], work)
            job.command(name + "-apply", ["git", "-C", source, "apply", patch], work)
            for rel, digest in expected.items():
                require(sha(source / rel) == digest, name + " source mismatch: " + rel)
        for path in [source] + [source / rel for rel in DEPENDENCIES]:
            object_dir = Path(git(path, "rev-parse", "--absolute-git-dir")) / "objects"
            require(not (object_dir / "info/alternates").exists(), "unexpected object borrowing")
            require(all(p.stat().st_nlink == 1 for p in object_dir.rglob("*") if p.is_file()),
                    "shared hardlinked Git objects")
        guard = load_guard(inputs / "artifact_guard.py")
        write_json(output / "source-snapshot.json", snapshot(source, guard, manifest))
        job.command("compile-api", ["g++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
                    "-I", inputs, inputs / "reference_api.cpp", "-ldl", "-o", work / "reference-api"], work)
        job.finish("PREPARE_PASS", controls_sha256=sha(inputs / "control.json"),
                   probe_sha256=sha(work / "reference-api"), source=str(source),
                   source_snapshot_sha256=sha(output / "source-snapshot.json"))
    except BaseException as error:
        job.finish("PREPARE_INCOMPLETE", error=repr(error))
        raise


def build(args, work):
    identity = verify_controls(work)
    require(sha(Path(__file__)) == identity["sha256"]["build_reference.py"], "running builder identity drift")
    require(json.loads((work / "prepare-01/state.json").read_text())["status"] == "PREPARE_PASS",
            "prepare not complete")
    feature = args.feature
    output = work / ("feature" + str(feature) + "-01")
    require(not output.exists(), "build output already exists; inspect its original receipt")
    output.mkdir()
    job = Job(output, "feature" + str(feature))
    try:
        source, inputs = work / "source", work / "inputs"
        manifest = json.loads((inputs / "manifest.json").read_text())
        guard = load_guard(inputs / "artifact_guard.py")
        snapshot(source, guard, manifest)
        env = dict(os.environ, NEMU_HOME=str(source), CCACHE_DISABLE="1")
        env.pop("MAKEFLAGS", None); env.pop("MFLAGS", None)
        build_dir = output / "build"
        require(not (source / "build").exists(), "default build directory is not empty")
        make = ["make", "-j1", "__NOT_DEFINED=", "CPT_CROSS_COMPILE=riscv64-linux-gnu-"]
        job.command("configure", make + ["riscv64-xs-ref_defconfig"], source, env)
        config = source / ".config"
        desired = {"CUSTOM_VDOT": True, "CUSTOM_VDOT_XS_TVAL": True, "CUSTOM_VDOT16": bool(feature),
                   "CUSTOM_VDOT16_XS_TVAL": False, "TVAL_EX_II": True,
                   "NMIE_INIT": True, "MDT_INIT": False, "LIGHTQS": False}
        text = config.read_text()
        for key, enabled in desired.items():
            pattern = rf"^(?:CONFIG_{key}=.*|# CONFIG_{key} is not set)$"
            matches = re.findall(pattern, text, flags=re.M)
            require(len(matches) <= 1, "duplicate configuration key: " + key)
            value = f"CONFIG_{key}=y" if enabled else f"# CONFIG_{key} is not set"
            text = re.sub(pattern, value, text, flags=re.M) if matches else text + "\n" + value + "\n"
        config.write_text(text)
        job.command("syncconfig", [source / "tools/kconfig/build/conf", "--syncconfig", "Kconfig"], source, env)
        effective = dict(re.findall(r"^CONFIG_([A-Z0-9_]+)=(.*)$", config.read_text(), re.M))
        for key, enabled in {**desired, "RVV": True, "DIFFTEST_CHECK_VCSR": True,
                             "DIFFTEST_CHECK_FCSR": True, "DIFFTEST_CHECK_SDTRIG": True}.items():
            require((effective.get(key) == "y") == enabled, "effective configuration mismatch: " + key)
        generated = (source / "include/generated/autoconf.h").read_text()
        require(("#define CONFIG_CUSTOM_VDOT16 1" in generated) == bool(feature),
                "generated feature gate mismatch")
        require("#define CONFIG_CUSTOM_VDOT16_XS_TVAL " not in generated and
                "#define CONFIG_LIGHTQS " not in generated, "forbidden generated profile")
        shutil.copyfile(config, output / "nemu.config")
        shutil.copytree(source / "include/config", output / "generated/include/config")
        target = output / "generated/include/generated"; target.mkdir(parents=True)
        shutil.copyfile(source / "include/generated/autoconf.h", target / "autoconf.h")
        job.command("make", make, source, env, timeout=args.timeout)
        require((source / "build/riscv64-nemu-interpreter-so").is_file(), "default build produced no library")
        # Move only this completed candidate's own output, before freezing its build identity.
        # Every object/preprocessed source remains available; old references are never touched.
        (source / "build").rename(build_dir)
        binary = build_dir / "riscv64-nemu-interpreter-so"
        require(binary.is_file() and binary.stat().st_size > 0, "missing actual library")
        job.command("exports", ["nm", "-D", binary], source, env)
        job.command("links", ["ldd", "-r", binary], source, env)
        require("undefined symbol" not in (output / "links.stdout.log").read_text() +
                (output / "links.stderr.log").read_text(), "unresolved dynamic symbol")
        exports = (output / "exports.stdout.log").read_text()
        for name in ("difftest_init_v2", "DIFFTEST_REG_SIZE", "difftest_regcpy",
                     "difftest_memcpy", "difftest_csrcpy", "difftest_exec", "difftest_set_ramsize"):
            require(any(line.split()[-1] == name for line in exports.splitlines() if line.split()),
                    "missing export: " + name)
        write_json(output / "source-snapshot.json", snapshot(source, guard, manifest, build_dir))
        job.finish("BUILD_PASS", feature=feature, base_rev=REV, library=str(binary),
                   library_sha256=sha(binary), library_bytes=binary.stat().st_size,
                   config_sha256=sha(output / "nemu.config"),
                   source_snapshot_sha256=sha(output / "source-snapshot.json"),
                   controls_sha256=sha(work / "inputs/control.json"),
                   candidate_patch_sha256=CANDIDATE_PATCH, legacy_patch_sha256=LEGACY_PATCH,
                   reference_api_qualified=False, fullcore_qualified=False,
                   dot16_platform_tval_qualified=False)
    except BaseException as error:
        job.finish("BUILD_INCOMPLETE", error=repr(error))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "build"))
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--base", type=Path)
    parser.add_argument("--diffstate", type=Path)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--feature", type=int, choices=(0, 1), default=0)
    parser.add_argument("--cpu", type=int, required=True)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    require(60 <= args.timeout <= 3600, "invalid bounded build timeout")
    os.sched_setaffinity(0, {args.cpu})
    work = args.workspace.resolve()
    if args.phase == "prepare":
        require(args.repository and args.base and args.diffstate, "prepare inputs required")
        prepare(args, work)
    else:
        build(args, work)


if __name__ == "__main__":
    main()
