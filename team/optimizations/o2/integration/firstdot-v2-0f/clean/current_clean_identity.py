"""Standalone clean software/hardware identity with the current_hardware API."""
from __future__ import annotations
import argparse
from datetime import datetime
import json
from pathlib import Path
import subprocess
import current_clean_common as c
import current_clean_profile as p

CONTRACT = "zjhwork-0f-firstdot-v2-clean-identity-v1"
HERE = Path(__file__).resolve().parent
PREPARE_SHA = "8e59850c3edcf1bb26d6914759632bab626e297fc95f071f23b58a313043e561"
SUPPORT_SHA = "13d03b2a54c26d192e1757975b7583ba5d41a764e8e732caf5c2bc48d7351566"
NEMU_RECIPE_SHA = "bef805d62c5b64aedae63c295c1bb0a8d065147c48187a2ca7406afb92348e8a"
REPRO = Path("team/optimizations/o2/repro")
hardware_profile = p.hardware_profile

def adapters():
    return {str(HERE / name): c.sha(HERE / name)
            for name in (*c.ADAPTER_NAMES, "current_clean_identity.py")}

def restore_record(row, physical):
    required = {"source", "destination", "revision", "origin", "command",
                "generated_products_copied", "cache_worktree_used"}
    c.require(set(row) == required and row["generated_products_copied"] is False
              and row["cache_worktree_used"] is False, "restore record incomplete")
    dest = Path(row["destination"])
    c.require(row["command"] == ["git", "clone", "--quiet", "--no-hardlinks", "--no-checkout",
                                row["source"], str(dest)], "restore command differs")
    c.require(dest.is_absolute() and len(row["revision"]) == 40, "restore path/revision")
    if physical:
        c.require(c.git(dest, "rev-parse", "HEAD").decode().strip() == row["revision"], "restored HEAD changed")
        gitdir = Path(c.git(dest, "rev-parse", "--absolute-git-dir").decode().strip())
        c.require((dest / ".git").is_dir() and not (dest / ".git").is_symlink()
                  and gitdir.resolve() == (dest / ".git").resolve()
                  and not (gitdir / "objects/info/alternates").exists(), "restore not independent")
        c.require(c.git(dest, "remote", "get-url", "origin").decode().strip() == row["origin"], "restore origin drift")

def support_profile(repo, cfg, physical=True):
    root = Path(cfg["hardware_source"])
    prepare_path = root.parent / "prepare-state.json"
    support = Path(cfg.get("support_record", Path(cfg["reference"]).parents[3]))
    prepared, state = c.read(prepare_path), c.read(support / "state.json")
    c.require(prepared["status"] == "T17_CLEAN_SOURCE_PREPARED"
              and prepared["revision"] == cfg["source_commit"] and prepared["hardware_submodules"] == 126
              and prepared["repository_count"] == len(prepared["repositories"]) == 133
              and prepared["build_executed"] is False and prepared["toolchain_reinstalled"] is False,
              "new source prepare incomplete")
    c.require(state["contract"] == "t17-clean-support-v1"
              and state["status"] == "T17_CLEAN_SUPPORT_BUILD_PASS" and state["runtime_qualified"] is False
              and state["generated_products_copied"] is False
              and state["official_authoritative_programs_modified"] is False
              and state["jobs_per_component"] == 2 and state["reference"] == cfg["reference"]
              and state["am_home"] == cfg["am_home"], "new support build incomplete")
    records = prepared["repositories"] + c.read(support / "repositories.json")
    c.require(len(records) == len({r["destination"] for r in records}) == 145, "restore inventory differs")
    c.require(prepared["repositories"][0]["destination"] == str(root), "prepared root differs")
    c.require(str(Path(cfg["reference"]).parents[1]) in {r["destination"] for r in records}
              and cfg["am_home"] in {r["destination"] for r in records}, "support/source roots disconnected")
    for row in records: restore_record(row, physical)
    inputs = {str(prepare_path): c.sha(prepare_path), str(prepare_path.parent / "prepare.log"):
              c.sha(prepare_path.parent / "prepare.log")}
    for name in ("state.json", "source-restore.log", "repositories.json", "am-source-before.json", "verified-nemu.json"):
        inputs[str(support / name)] = c.sha(support / name)
    driver = root / "team/scripts/prepare-nemu-vdot.sh"
    c.require(c.sha(driver) == state["team_patch_recipe_sha256"] == NEMU_RECIPE_SHA, "NEMU recipe changed")
    c.require(c.sha(root / REPRO / "clean_prepare.py") == PREPARE_SHA
              and c.sha(root / REPRO / "clean_support.py") == SUPPORT_SHA, "upstream clean restore/support changed")
    expected = {"nemu": ["bash", str(driver), "reference"],
                "am": ["make", "-C", str(Path(cfg["am_home"]) / "am"), "ARCH=riscv64-xs",
                       "CROSS_COMPILE=riscv64-linux-gnu-", "-j2"],
                "klib": ["make", "-C", str(Path(cfg["am_home"]) / "libs/klib"), "ARCH=riscv64-xs",
                         "CROSS_COMPILE=riscv64-linux-gnu-", "-j2"]}
    c.require(state["commands"] == expected, "support commands differ")
    for name, command in expected.items():
        receipt_path = support / (name + "-command.json")
        receipt = c.read(receipt_path)
        c.require(receipt["command"] == command and receipt["cwd"] == str(root.resolve())
                  and receipt["exit_code"] == 0 and receipt["process_executed"] is True, "support execution differs")
        times = [datetime.fromisoformat(receipt[k]) for k in ("started", "finished")]
        c.require(all(t.utcoffset() is not None for t in times) and times == sorted(times), "support chronology")
        inputs[str(receipt_path)] = c.sha(receipt_path)
        for suffix in ("stdout.log", "stderr.log"):
            log = support / (name + "." + suffix)
            c.require(c.sha(log) == receipt["raw_sha256"][suffix], "support raw log differs")
            inputs[str(log)] = c.sha(log)
    guard = p.module("current_clean_support_guard", Path(repo) / "team/scripts/artifact_guard.py")
    reference = Path(cfg["reference"])
    provenance = guard.verify_nemu(reference.parents[1], reference, "reference")
    c.require(provenance == c.read(support / "verified-nemu.json") and
              c.sha(reference) == state["reference_sha256"], "support reference provenance differs")
    manifest = root / "team/patches/nemu/manifest.json"
    c.require(c.sha(manifest) == state["team_patch_manifest_sha256"], "support patch manifest changed")
    inputs[str(manifest)] = c.sha(manifest)
    for path, digest in state["am_libraries"].items():
        c.require(c.sha(path) == digest, "new AM library changed")
        inputs[path] = digest
    c.require(set(state["am_libraries"]) == {
        str(Path(cfg["am_home"]) / "am/build/am-riscv64-xs.a"),
        str(Path(cfg["am_home"]) / "libs/klib/build/klib-riscv64-xs.a")}, "AM library inventory")
    after = guard.audit_repo(Path(cfg["am_home"]), "086a238062fdfb3281b745a537b361983d0154b5",
                            source_roots=("am/src", "am/include", "libs/klib/src", "libs/klib/include"))
    c.require(after == c.read(support / "am-source-before.json"), "new AM source changed")
    return inputs, dict(contract="zjh-current-clean-support-proof-v1", restored_repositories=145,
        reference_provenance=provenance, am_libraries=state["am_libraries"],
        prepare_state_sha256=c.sha(prepare_path), support_state_sha256=c.sha(support / "state.json"),
        new_sources=True, new_support_builds=True, toolchain_reinstalled=False, runtime_qualified=False)

def create_identity(repo, cfg, output):
    repo, output = Path(repo).resolve(), Path(output).resolve()
    c.require(not output.exists() and not output.is_relative_to(repo), "identity must be new and outside checkout")
    files, hardware = hardware_profile(repo, cfg)
    support_files, support = support_profile(repo, cfg, physical=True)
    record = Path(cfg["build_record"])
    identity = dict(contract=CONTRACT, hardware_contract=p.CONTRACT, source_commit=cfg["source_commit"],
        selected_hardware_commit=c.BASELINE_SOURCE, hardware_profile=hardware, configuration=cfg,
        metadata_sha256={name: c.sha(record / name) for name in p.META_NAMES}, adapter_files=adapters(),
        reference_sha256=hardware["reference_provenance"]["binary_sha256"], flash_sha256=c.FLASH,
        support_profile=support, support_files=support_files,
        historical_fixed_hardware_acceptance=False, historical_t17_acceptance=False,
        new_source_build=True, new_runtime_execution_completed=False,
        scope="same-host clean independent source/build; installed tools/download cache retained")
    c.save(output, identity)
    return identity

def validate_identity(repo, path, physical=False):
    return validate_identity_value(repo, c.read(Path(path).resolve()), physical=physical)


def validate_identity_value(repo, value, physical=False):
    repo = Path(repo).resolve()
    c.require(value["contract"] == CONTRACT and value["hardware_contract"] == p.CONTRACT
              and value["selected_hardware_commit"] == c.BASELINE_SOURCE
              and value["new_source_build"] is True and value["new_runtime_execution_completed"] is False
              and value["historical_fixed_hardware_acceptance"] is False
              and value["historical_t17_acceptance"] is False, "wrong clean identity contract")
    c.require(value["adapter_files"] == adapters() and value["flash_sha256"] == c.FLASH
              and value["source_commit"] == value["configuration"]["source_commit"]
              and value["source_commit"] == value["hardware_profile"]["source_commit"]
              and set(value["metadata_sha256"]) == set(p.META_NAMES)
              and value["hardware_profile"]["pins_sha256"] == value["metadata_sha256"]["hardware-inputs.json"]
              and value["reference_sha256"] == value["hardware_profile"]["reference_provenance"]["binary_sha256"],
              "clean identity metadata differs")
    if not physical:
        return value
    files, profile = hardware_profile(repo, value["configuration"])
    support_files, support = support_profile(repo, value["configuration"], physical=True)
    c.require(profile == value["hardware_profile"] and support_files == value["support_files"]
              and support == value["support_profile"], "clean physical identity changed")
    record = Path(value["configuration"]["build_record"])
    c.require({name: files[str(record / name)] for name in p.META_NAMES} == value["metadata_sha256"],
              "clean build metadata drift")
    return value, files | support_files | adapters(), profile

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(create_identity(args.repo, c.read(args.config), args.output), indent=2))
