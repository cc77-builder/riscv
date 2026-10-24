"""T17 provenance and portable R4 software evidence under a new hardware contract.

The frozen runtime adapters are never edited. The recorded executed builder has
two logical roles but one original path, so archives store it once as the build
driver and still validate all nineteen original metadata identities.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess

import clean_entry as ce

p, g, e = ce.p, ce.g, ce.evidence
CONTRACT = "t17-clean-evidence-v1"
SUPPORT_CONTRACT = "t17-clean-support-proof-v1"
SUPPORT_FILES = ("state.json", "repositories.json", "source-restore.log", "am-source-before.json", "verified-nemu.json") + tuple(
    component + suffix for component in ("nemu", "am", "klib")
    for suffix in ("-command.json", ".stdout.log", ".stderr.log"))


def unpack_files(bundle):
    expected = {"prepare/prepare-state.json", "prepare/prepare.log"} | {"support/" + n for n in SUPPORT_FILES}
    p.require(bundle["contract"] == SUPPORT_CONTRACT and set(bundle["files"]) == expected, "support proof inventory")
    result = {}
    originals = set()
    for name, row in bundle["files"].items():
        raw = base64.b64decode(row["base64"], validate=True)
        p.require(len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"] and
                  row["original"] not in originals, "support raw identity: " + name)
        result[name] = raw
        originals.add(row["original"])
    return result


def validate_support(bundle, identity):
    raw = unpack_files(bundle)
    obj = lambda name: json.loads(raw[name])
    cfg = identity["configuration"]
    prepared, state = obj("prepare/prepare-state.json"), obj("support/state.json")
    p.require(bundle["identity_sha256"] == hashlib.sha256(bundle["identity_raw"].encode()).hexdigest() and
              json.loads(bundle["identity_raw"]) == identity, "support proof identity")
    p.require(prepared == identity["prepare_state"] and prepared["status"] == "T17_CLEAN_SOURCE_PREPARED" and
              prepared["revision"] == p.SOURCE and prepared["hardware_submodules"] == 126 and
              len(prepared["repositories"]) == prepared["repository_count"] == 133 and
              prepared["build_executed"] is False and prepared["toolchain_reinstalled"] is False, "clean source preparation proof")
    p.require(state["contract"] == "t17-clean-support-v1" and state["status"] == "T17_CLEAN_SUPPORT_BUILD_PASS" and
              state["generated_products_copied"] is False and state["runtime_qualified"] is False and
              state["reference"] == cfg["reference"] and state["reference_sha256"] == identity["reference_sha256"] and
              state["am_home"] == cfg["am_home"] and state["jobs_per_component"] == 2 and
              1 <= len(state["cpu_affinity"]) <= 4, "support build state/reference differs")
    prepare_root = str(PurePosixPath(cfg["hardware_source"]).parent)
    support_root = str(PurePosixPath(cfg["reference"]).parents[3])
    for name, record in bundle["files"].items():
        prefix, relative = name.split("/", 1)
        root = prepare_root if prefix == "prepare" else support_root
        p.require(record["original"] == str(PurePosixPath(root) / relative), "support source path differs")
    repos = prepared["repositories"] + obj("support/repositories.json")
    p.require(len(repos) == 145 and len({r["destination"] for r in repos}) == 145, "repository restore inventory")
    live = bundle["live_repository_facts"]
    p.require(set(live) == {r["destination"] for r in repos}, "live repository inventory differs")
    for r in repos:
        p.require(r["generated_products_copied"] is False and r["cache_worktree_used"] is False and
                  r["command"] == ["git", "clone", "--quiet", "--no-hardlinks", "--no-checkout", r["source"], r["destination"]] and
                  live[r["destination"]] == dict(revision=r["revision"], origin=r["origin"], has_alternates=False),
                  "restored repository differs: " + r["destination"])
    provenance = obj("support/verified-nemu.json")
    p.require(provenance == identity["hardware_profile"]["reference_provenance"] and
              bundle["live_am_source"] == obj("support/am-source-before.json"), "support source/provenance differs")
    expected_libs = {str(PurePosixPath(cfg["am_home"]) / name) for name in
                     ("am/build/am-riscv64-xs.a", "libs/klib/build/klib-riscv64-xs.a")}
    p.require(set(state["am_libraries"]) == expected_libs and state["am_libraries"] == bundle["live_am_libraries"],
              "support AM library identity differs")
    p.require(state["team_patch_recipe_sha256"] == "bef805d62c5b64aedae63c295c1bb0a8d065147c48187a2ca7406afb92348e8a" and
              state["team_patch_manifest_sha256"] == bundle["team_patch_manifest_sha256"], "team support recipe differs")
    start, finish = (datetime.fromisoformat(state[k]) for k in ("started", "finished"))
    p.require(start.utcoffset() is not None and finish.utcoffset() is not None and start <= finish, "support timeline")
    expected_commands = {
        "nemu": ["bash", str(PurePosixPath(cfg["hardware_source"]) / "team/scripts/prepare-nemu-vdot.sh"), "reference"],
        "am": ["make", "-C", str(PurePosixPath(cfg["am_home"]) / "am"), "ARCH=riscv64-xs", "CROSS_COMPILE=riscv64-linux-gnu-", "-j2"],
        "klib": ["make", "-C", str(PurePosixPath(cfg["am_home"]) / "libs/klib"), "ARCH=riscv64-xs", "CROSS_COMPILE=riscv64-linux-gnu-", "-j2"],
    }
    p.require(state["commands"] == expected_commands, "support command specification differs")
    for component in ("nemu", "am", "klib"):
        receipt = obj("support/" + component + "-command.json")
        a, b = (datetime.fromisoformat(receipt[k]) for k in ("started", "finished"))
        p.require(receipt["process_executed"] is True and type(receipt["exit_code"]) is int and receipt["exit_code"] == 0 and
                  receipt["command"] == state["commands"][component] and receipt["cwd"] == cfg["hardware_source"] and
                  start <= a <= b <= finish and receipt["raw_sha256"] == {
                      suffix: hashlib.sha256(raw["support/" + component + "." + suffix]).hexdigest()
                      for suffix in ("stdout.log", "stderr.log")}, "support command/raw receipt: " + component)
    return dict(status="T17_SUPPORT_PROVENANCE_CHAIN_PASS", restored_repositories=145, hardware_submodules=126,
                reference_sha256=state["reference_sha256"], am_libraries=state["am_libraries"],
                same_host=True, toolchain_reinstalled=False, historical_runtime_pass_inherited=False)


def support_proof(repo, identity_path):
    identity = p.read(identity_path)
    ce.validate_identity(repo, identity)
    cfg = identity["configuration"]
    prepared = Path(cfg["hardware_source"]).parent
    support = Path(cfg["reference"]).parents[3]
    files = {"prepare/" + name: prepared / name for name in ("prepare-state.json", "prepare.log")}
    files.update({"support/" + name: support / name for name in SUPPORT_FILES})
    encoded = {}
    for name, path in files.items():
        p.require(path.is_file() and not path.is_symlink(), "support file missing/symlink")
        raw = path.read_bytes()
        encoded[name] = dict(original=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                             base64=base64.b64encode(raw).decode())
    repositories = identity["prepare_state"]["repositories"] + p.read(support / "repositories.json")
    live = {}
    for row in repositories:
        root = Path(row["destination"])
        git = lambda *args: subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()
        live[str(root)] = dict(revision=git("rev-parse", "HEAD"), origin=git("remote", "get-url", "origin"),
                              has_alternates=(Path(git("rev-parse", "--absolute-git-dir")) / "objects/info/alternates").exists())
    guard = g.load("t17_support_chain_guard", repo / "team/scripts/artifact_guard.py")
    am_source = guard.audit_repo(Path(cfg["am_home"]), "086a238062fdfb3281b745a537b361983d0154b5",
                                source_roots=("am/src", "am/include", "libs/klib/src", "libs/klib/include"))
    libs = {str(Path(cfg["am_home"]) / n): p.sha(Path(cfg["am_home"]) / n) for n in
            ("am/build/am-riscv64-xs.a", "libs/klib/build/klib-riscv64-xs.a")}
    bundle = dict(contract=SUPPORT_CONTRACT, identity_sha256=p.sha(identity_path), identity_raw=identity_path.read_text(),
                  files=encoded, live_repository_facts=live, live_am_source=am_source, live_am_libraries=libs,
                  team_patch_manifest_sha256=p.sha(repo / "team/patches/nemu/manifest.json"),
                  audit_source_sha256=p.sha(__file__))
    return bundle, validate_support(bundle, identity)


def install(repo, identity, physical=False):
    ce.install(repo, identity, physical=physical)
    original = e.modules
    def modules(repo_):
        portable, m, common = original(repo_)
        p.require(m.META.get("executed-builder.py") == p.BUILDER, "missing builder metadata")
        m.META = {n: sha for n, sha in m.META.items() if n != "executed-builder.py"}
        return portable, m, common
    e.modules = modules
    e.EXTRA.add(Path(__file__).resolve().relative_to(repo).as_posix())


def archive_identity(repo, archive, identity_path, value):
    portable, _, _ = e.modules(repo)
    sealed = portable.Archive(archive)
    p.require(sealed.raw("support/" + identity_path.name) == identity_path.read_bytes(), "identity bytes not sealed")
    raw = lambda name: sealed.raw("hardware/" + ("build-driver.py" if name == "executed-builder.py" else name))
    for name, digest in value["metadata_sha256"].items():
        p.require(hashlib.sha256(raw(name)).hexdigest() == digest, "sealed metadata identity: " + name)
    obj = lambda name: json.loads(raw(name))
    p.validate_metadata(obj("hardware-inputs.json"), obj("build-state.json"), obj("hardware-inputs-before.json"),
                        obj("baseline-hardware-inputs.json"), obj("generated-artifacts.json"),
                        value["metadata_sha256"]["executed-builder.py"], value["metadata_sha256"]["baseline-hardware-inputs.json"])
    suite = g.load("t17_archive_new_pins", repo / "team/optimizations/o2/fullcore/run_suite.py")
    suite.validate_pin_fields(obj("hardware-inputs.json"))
    support = sealed.json("support/support-proof.json")
    proof = validate_support(support, value)
    manifest_path = str(PurePosixPath(value["configuration"]["hardware_source"]) / "team/patches/nemu/manifest.json")
    p.require(support["team_patch_manifest_sha256"] == sealed.json("sealed-inputs.json")[manifest_path]["sha256"],
              "support patch manifest differs from actual runtime input")
    for path, digest in proof["am_libraries"].items():
        p.require(sealed.json("sealed-inputs.json")[path]["sha256"] == digest, "matrix did not use rebuilt AM library")
    return sealed


def main(args):
    repo, out = args.repo.resolve(), args.output.resolve()
    p.require(not out.exists(), "output must be new")
    value = p.read(args.identity)
    if args.action == "support":
        bundle, result = support_proof(repo, args.identity.resolve())
        g.save(out, bundle)
        return result
    install(repo, value, physical=args.action in ("pack-matrix", "pack-c"))
    if args.action == "pack-matrix":
        p.require(args.support.name == "support-proof.json", "support proof needs stable archive name")
        validate_support(p.read(args.support), value)
        result = e.pack(repo, [r.resolve() for r in args.run], args.archive.resolve(), "matrix",
                        support=[args.identity.resolve(), args.support.resolve()])
        archive_identity(repo, args.archive.resolve(), args.identity.resolve(), value)
    elif args.action in ("audit-matrix", "index-matrix"):
        archive_identity(repo, args.archive.resolve(), args.identity.resolve(), value)
        result = (e.audit if args.action == "audit-matrix" else e.index_check)(repo, args.archive.resolve())
    else:
        archive_identity(repo, args.matrix.resolve(), args.identity.resolve(), value)
        if args.action == "pack-c":
            result = ce.c_evidence.pack(repo, args.build.resolve(), args.run[0].resolve(), args.archive.resolve(), args.matrix.resolve())
        elif args.action == "audit-c":
            result = ce.c_evidence.audit_archive(repo, args.archive.resolve(), args.matrix.resolve())
        else:
            result = ce.c_evidence.index_check(repo, args.archive.resolve())
    outer = dict(contract=CONTRACT, identity_sha256=p.sha(args.identity), hardware_contract=p.CONTRACT,
                 emu_sha256=value["hardware_profile"]["emu_sha256"], audit_source_sha256=p.sha(__file__),
                 historical_fixed_hardware_acceptance=False, historical_b0_h1_acceptance=False,
                 whole_suite_acceptance=False, software_gate_result=result)
    g.save(out, outer)
    return outer


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--identity", type=Path, required=True)
    ap.add_argument("--action", required=True, choices=("support", "pack-matrix", "audit-matrix", "index-matrix", "pack-c", "audit-c", "index-c"))
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--archive", type=Path)
    ap.add_argument("--run", type=Path, action="append")
    ap.add_argument("--build", type=Path)
    ap.add_argument("--matrix", type=Path)
    ap.add_argument("--support", type=Path)
    print(json.dumps(main(ap.parse_args()), indent=2))
