#!/usr/bin/env python3
"""Bind new software experiments to the preserved 0f12df6 hardware build.

This is a new outer identity contract. Historical R4/T17 pins are never changed.
The anchor below is a reviewed fixed build, not a learn-current-files whitelist.
Physical checks are read-only and do not launch EMU or rebuild anything.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ANCHOR = {'schema': 1, 'contract': 'current-o2-h1-div-cancel-hardware-v1', 'source_commit': '0f12df675378556670afd0dd2153f47fcb330610', 'emu_sha256': '2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8', 'reference_sha256': 'efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4', 'flash_sha256': 'a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994', 'metadata_sha256': {'build-command.sh': '91e7e1e41a36d6edb3409e3f9c255384b982fe6bf88ae2647d22702eac164882', 'build-state.json': 'f63d911245545948a32273eb3c59b6046acbd0d0314e9fe87557949fcd12d90a', 'clang-version.log': '8c803e6e30d91b83ca5df33fb58fc74c2021c3845b36ad4c22fb7fd8d94ee919', 'dependencies.json': '564b9534ef059f544c564d6a491cca32cd34e8b3ba0f7868c3de401e2bd547d8', 'emu-build.log': 'b9bb8196629a0e6760d83e45aa92a06f70439ec394623d2517e37a2c96d31b92', 'firtool-version.log': '314271dc6f68632027c0711da7f96100db18723d94d80a16ad9d82cdd2e0377f', 'generated-artifacts.json': '62bacc87513dde5edecefb2774c26d42348fafb3929a687e713b1ff4394092e1', 'hardware-inputs-before.json': '57efc29b45d54a69aa85f8a07393478fe9e5b8489995dc8afd7adbcc63659581', 'hardware-inputs.json': '388e286327006c7a58494d434370aaaf7c36815f1abeaa517c40754c4e620bc5', 'java-version.log': '5157fc80c2b1904606b0668b959604ac1266f20c8089e3e235d26ab755c73ead', 'make-version.log': '8ee498ee2fc27e8dcdf99191b454077df95e3840d841ec94321748b6d7f36819', 'mill-version.log': 'a84e9ec81bead3f47baf706995126a25e246322804cb780006b22bb0b093653d', 'python-version.log': 'f6b75e07f1488db28a89724a522725e3e01af3dc78f6fd365f17eb4059e41056', 'source-status.txt': '4159d8a3f5b6064ae6ecb28951ec5643f5e1f69629fdec0a59e22a9806a9ab58', 'verilator-version.log': '110d748d8e6eca23b22ad7bf766d1d1fcf69c45731c3260fc80857cdd2d62576', 'working-tree.patch': '620147872cc57001260492f175b9fd7acb53e27bedd6b9765fa91d226b6556c9'}, 'auxiliary_sha256': {'constantin.txt': 'a1fd1d4de05919fec0257bacb550a3622c0f4ec2373e5cf230fc4233fb98c1bf', 'plusArgs': '160d9702d313cbe66be84ae88c2f45c3df9ed7b61b65e3ddeea25133ac6765ff'}, 'checker_sha256': {'team/scripts/artifact_guard.py': '95eabdc0dc6191df4b03062e432ecc38877cc0c9626a81cdd002a4627ab54a85', 'team/patches/nemu/manifest.json': '1fee8f48616d7d09f46fd5924fb677f4a042ab7a6e2098a4af93e5e4e6a495a1'}, 'build_driver_sha256': '8a66fb75324ee1834401ec71b5c578141de6268a074253d37eb5494046c932d0', 'counts': {'source_files': 429, 'dependency_files': 21236, 'generated_files': 1672, 'dependencies': 126}}


CONFIG_FIELDS = {
    "hardware_source", "build_record", "build_driver", "am_home",
    "cross_prefix", "reference", "flash",
}
HARDWARE_SCOPE = ("src", "scripts", "Makefile", "Makefile.test", "build.sc",
                  "team/scripts/activate.sh")
PIN_FIELDS = {
    "config": "MinimalConfig", "NUM_CORES": 1, "EMU_THREADS": 1,
    "JVM_XMX": "12G", "BUILD_JOBS": 2, "VDOT_O2_ELASTIC": "1",
    "VDOT_O1_HANDOFF": "0", "VDOT_O1_TRACE": "0", "VDOT_T14_FUSED_INPUT": "1",
    "VDOT_O2_TRACE": "1", "VDOT_T12_TRACE": "0", "VDOT_T13_TRACE": "1",
    "profile": "observe",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def verify_files(files):
    for path, digest in files.items():
        require(sha(path) == digest, "input drift: " + str(path))


def config_paths(repo, cfg):
    require(set(cfg) == CONFIG_FIELDS, "unexpected/missing hardware configuration fields")
    require(all(isinstance(v, str) and v.strip() for v in cfg.values()), "invalid configuration")
    result = dict(cfg)
    for name in CONFIG_FIELDS - {"cross_prefix"}:
        result[name] = str(Path(cfg[name].replace("$"+"{REPO}", str(repo))).expanduser().resolve())
    return result


def safe_relative(name):
    p = Path(name)
    require(not p.is_absolute() and ".." not in p.parts and str(p) != ".", "unsafe path: " + name)
    return p


def git(repo, *args, input=None):
    return subprocess.check_output(["git", "-C", str(repo), *args], input=input)


def hardware_tree(repo, ref):
    rows = git(repo, "ls-tree", "-rz", ref, "--", *HARDWARE_SCOPE).split(b"\0")
    result = {}
    for row in rows:
        if not row:
            continue
        info, name = row.split(b"\t", 1)
        mode, kind, oid = info.decode().split()
        require(kind in ("blob", "commit"), "unexpected hardware Git entry")
        if kind == "commit":
            continue
        result[name.decode()] = (mode, oid)
    return result


def verify_source(repo, pins):
    """Bind hardware to 0f Git blobs, even when HEAD gains software commits."""
    original = hardware_tree(repo, ANCHOR["source_commit"])
    require(set(original) == set(pins["files"]), "hardware scope differs from build inventory")
    require(hardware_tree(repo, "HEAD") == original, "current HEAD has hardware changes")
    require(not git(repo, "diff", ANCHOR["source_commit"], "HEAD", "--", *HARDWARE_SCOPE),
            "current HEAD hardware Git links changed")
    request = "".join(ANCHOR["source_commit"] + ":" + n + "\n" for n in original).encode()
    data = git(repo, "cat-file", "--batch", input=request)
    offset = 0
    for name, (mode, oid) in original.items():
        end = data.index(b"\n", offset)
        header = data[offset:end].split()
        require(len(header) == 3 and header[1] == b"blob", "missing source Git blob: " + name)
        size = int(header[2])
        body = data[end + 1:end + 1 + size]
        require(hashlib.sha256(body).hexdigest() == pins["files"][name], "Git blob differs: " + name)
        path = repo / safe_relative(name)
        require(not path.is_symlink() and path.is_file(), "hardware source must be a regular file: " + name)
        require(sha(path) == pins["files"][name], "hardware worktree differs: " + name)
        offset = end + size + 2
    require(offset == len(data), "unparsed Git source batch")
    # Include ignored files: newly added compiler input must not escape the gate.
    for base in ("src", "scripts"):
        actual = {p.relative_to(repo).as_posix() for p in (repo / base).rglob("*") if p.is_file()}
        allowed = {name for name in original if name.startswith(base + "/")}
        dep_roots = {"src/main/resources/aia"}
        actual = {n for n in actual if not any(n.startswith(d + "/") for d in dep_roots)}
        require(actual == allowed, "unknown or missing hardware input in " + base)
    return git(repo, "rev-parse", "HEAD").decode().strip()


def validate_metadata(record):
    files = {str(record / n): digest for n, digest in ANCHOR["metadata_sha256"].items()}
    verify_files(files)
    pins = read_json(record / "hardware-inputs.json")
    before = read_json(record / "hardware-inputs-before.json")
    require(before == {k: v for k, v in pins.items()
                       if k not in ("emu_sha256", "emu_bytes", "emu_path")},
            "before/after hardware build inputs changed")
    state = read_json(record / "build-state.json")
    for key, value in PIN_FIELDS.items():
        require(type(pins.get(key)) is type(value) and pins.get(key) == value,
                "wrong build pin: " + key)
    require(pins["source_commit"] == ANCHOR["source_commit"] and
            pins["emu_sha256"] == ANCHOR["emu_sha256"], "wrong hardware build identity")
    require(state["source_commit"] == pins["source_commit"] and
            state["emu_sha256"] == pins["emu_sha256"] and
            state["status"] == "O2_FULLCORE_BUILD_PASS" and state["build_exit_code"] == 0,
            "hardware build was not completed successfully")
    require(len(pins["files"]) == 429 and len(pins["dependency_files"]) == 21236,
            "incomplete hardware source inventory")
    command = (record / "build-command.sh").read_text()
    require(state["command"] == ["bash", "-c", command], "actual build command differs")
    require(pins["build_script_sha256"] == ANCHOR["build_driver_sha256"], "wrong builder")
    return files, pins, state


def hardware_profile(repo, cfg):
    """Return (all immutable input paths/digests, verified physical profile)."""
    repo = Path(repo).resolve()
    cfg = config_paths(repo, cfg)
    root, record = Path(cfg["hardware_source"]), Path(cfg["build_record"])
    files, pins, state = validate_metadata(record)
    require(str(root) == pins["source_root"] == state["source_root"],
            "hardware checkout is not the recorded build source")
    require(str(root / "build/emu") == pins["emu_path"], "hardware binary path differs")
    files.update({str(root / "build" / n): d for n, d in ANCHOR["auxiliary_sha256"].items()})
    files.update({
        str(root / "build/emu"): ANCHOR["emu_sha256"],
        cfg["reference"]: ANCHOR["reference_sha256"],
        cfg["flash"]: ANCHOR["flash_sha256"],
        cfg["build_driver"]: ANCHOR["build_driver_sha256"],
    })
    files.update({str(repo / n): d for n, d in ANCHOR["checker_sha256"].items()})
    verify_files(files)
    head = verify_source(root, pins)
    files.update({str(root / safe_relative(n)): d for n, d in pins["files"].items()})
    dependencies = read_json(record / "dependencies.json")
    require(len(dependencies) == 126 and len({d["path"] for d in dependencies}) == 126,
            "incomplete dependency repositories")
    for item in dependencies:
        path = root / safe_relative(item["path"])
        require(item["head"] == item["pin"] and
                git(path, "rev-parse", "HEAD").decode().strip() == item["pin"],
                "dependency revision differs: " + item["path"])
    for name, digest in pins["dependency_files"].items():
        files[str(root / safe_relative(name))] = digest
    generated = read_json(record / "generated-artifacts.json")
    require(len(generated) == 1672 and len({p["path"] for p in generated}) == 1672,
            "incomplete/duplicate generated inventory")
    for item in generated:
        rel = safe_relative(item["path"])
        require(rel.parts[0] == "build", "generated path outside build")
        path = root / rel
        require(path.stat().st_size == item["bytes"], "generated artifact size differs: " + str(rel))
        files[str(path)] = item["sha256"]
    verify_files(files)
    guard_path = repo / "team/scripts/artifact_guard.py"
    spec = importlib.util.spec_from_file_location("_current_identity_artifact_guard", guard_path)
    guard = importlib.util.module_from_spec(spec)
    exec(compile(guard_path.read_bytes(), str(guard_path), "exec"), guard.__dict__)
    guard.ROOT = repo
    reference = Path(cfg["reference"])
    provenance = guard.verify_nemu(reference.parents[1], reference, "reference")
    files[str(reference.parent / "vdot-provenance.json")] = sha(reference.parent / "vdot-provenance.json")
    files[str(reference.parents[1] / ".config")] = provenance["config_sha256"]
    files.update({str(reference.parents[1] / n): d for n, d in provenance["source_sha256"].items()})
    profile = dict(
        contract=ANCHOR["contract"], status="HARDWARE_IDENTITY_VERIFIED_RUNTIME_NOT_TESTED",
        source_commit=ANCHOR["source_commit"], emu_sha256=ANCHOR["emu_sha256"],
        pins_sha256=ANCHOR["metadata_sha256"]["hardware-inputs.json"],
        **ANCHOR["counts"], before_after_identical=True,
        build_driver_sha256=pins["build_script_sha256"],
        reference_provenance_sha256=files[str(reference.parent / "vdot-provenance.json")],
        reference_provenance=provenance,
        historical_b0_h1_acceptance=False, whole_suite_acceptance=False,
        clean_reproduction=False, new_emu_runs=0,
    )
    verify_files(files)
    require(verify_source(root, pins) == head, "source HEAD moved during audit")
    return files, profile


def seal(value):
    return hashlib.sha256(encoded({k: v for k, v in value.items() if k != "identity_sha256"})).hexdigest()


def create_identity(repo, cfg, output, lock_output=None):
    """Audit, then write a new identity and separate fixed lock; never overwrite."""
    repo, output = Path(repo).resolve(), Path(output).resolve()
    lock_output = Path(lock_output).resolve() if lock_output else output.with_name("hardware-artifact-lock.json")
    require(not output.exists() and not lock_output.exists(), "identity/lock output already exists")
    cfg = config_paths(repo, cfg)
    files, profile = hardware_profile(repo, cfg)
    value = dict(
        schema=1, contract=ANCHOR["contract"], created=datetime.now(timezone.utc).isoformat(),
        configuration=cfg, source_commit=ANCHOR["source_commit"],
        source_checkout_head=git(Path(cfg["hardware_source"]), "rev-parse", "HEAD").decode().strip(),
        metadata_sha256=ANCHOR["metadata_sha256"], hardware_profile=profile,
        reference_sha256=ANCHOR["reference_sha256"], flash_sha256=ANCHOR["flash_sha256"],
        hardware_lock=str(lock_output), hardware_lock_sha256=hashlib.sha256(encoded(ANCHOR)).hexdigest(),
        adapter_sha256=sha(__file__),
    )
    value["identity_sha256"] = seal(value)
    output.parent.mkdir(parents=True, exist_ok=True)
    lock_output.parent.mkdir(parents=True, exist_ok=True)
    with lock_output.open("xb") as stream:
        stream.write(encoded(ANCHOR))
    with output.open("xb") as stream:
        stream.write(encoded(value))
    return value


def validate_identity(repo, path, physical=False):
    """Return identity; physical=True also returns immutable files and profile."""
    repo, path = Path(repo).resolve(), Path(path).resolve()
    value = read_json(path)
    require(value.get("schema") == 1 and value.get("contract") == ANCHOR["contract"],
            "identity version/contract differs")
    require(value.get("identity_sha256") == seal(value), "identity integrity seal differs")
    require(value.get("adapter_sha256") == sha(__file__), "identity adapter source differs")
    require(value.get("source_commit") == ANCHOR["source_commit"], "identity hardware version differs")
    require(value.get("metadata_sha256") == ANCHOR["metadata_sha256"], "identity metadata differs")
    for key in ("reference_sha256", "flash_sha256"):
        require(value.get(key) == ANCHOR[key], "identity " + key + " differs")
    profile = value["hardware_profile"]
    require(profile["source_commit"] == ANCHOR["source_commit"] and
            profile["emu_sha256"] == ANCHOR["emu_sha256"] and
            profile["pins_sha256"] == ANCHOR["metadata_sha256"]["hardware-inputs.json"],
            "identity hardware profile differs")
    for key, count in ANCHOR["counts"].items():
        require(profile.get(key) == count, "identity inventory differs: " + key)
    lock = Path(value["hardware_lock"])
    digest = hashlib.sha256(encoded(ANCHOR)).hexdigest()
    require(value["hardware_lock_sha256"] == digest and sha(lock) == digest and
            read_json(lock) == ANCHOR, "fixed hardware artifact lock differs")
    cfg = config_paths(repo, value["configuration"])
    require(cfg == value["configuration"], "identity configuration is not canonical")
    if not physical:
        return value
    files, actual = hardware_profile(repo, cfg)
    # Profile identifies the immutable built hardware; software HEAD is audit-only.
    require(actual == profile, "physical hardware profile differs")
    files.update({str(path): sha(path), str(lock): digest, str(Path(__file__).resolve()): sha(__file__)})
    verify_files(files)
    return value, files, actual


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("create", "verify"))
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--identity", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    if args.action == "create":
        parser.error("--config required for create") if args.config is None else None
        result = create_identity(args.repo, read_json(args.config), args.identity)
        print(json.dumps({"status": result["hardware_profile"]["status"], "identity": str(args.identity)}))
    else:
        value, files, profile = validate_identity(args.repo, args.identity, physical=True)
        print(json.dumps({"status": profile["status"], "immutable_files": len(files),
                          "source_commit": profile["source_commit"], "new_emu_runs": 0}))
