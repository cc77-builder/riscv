"""Run the unchanged R4 software gates against a separately verified T17 build.

Only private module instances receive the new hardware identity. The R4
generator, ELF/model, CSR, call-retirement, O2 and negative/recovery checks keep
their original source bytes. T17 results always carry a separate outer contract;
historical fixed-hardware R4/B0/H1 qualification is not inherited.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

import clean_profile as p

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ENTRY = ROOT / "team/optimizations/o2/r2-select"
sys.path.insert(0, str(ENTRY))
import entry_experiment as a
import entry_c_api as c
import entry_evidence as evidence
import entry_c_evidence as c_evidence

g = a.g
CONTRACT = "t17-current-entry-reproduction-v1"
FROZEN = {
    "entry_experiment.py": "417b2d8d0b97b293d7db565bfddb39f111756cd23638ddc62c8117997e069b6e",
    "entry_gate.py": "d20e0bd7426ac7a3b56b62d2a9b495b51b9cd6da257e46723eddbbb984de8f11",
    "entry_c_api.py": "4e1ae340c5b122d09d634631d7fce322ad121838ba9a4affdf193d2a4d9105fd",
    "entry_evidence.py": "039f81a2c7e216514c94939b8807647787c4b046413a48fb4c7e33293c027db3",
    "entry_c_evidence.py": "166186d7e9114729bb042b2cee3e719f6fe56150077aca905b657fe0e703362f",
}
ADAPTERS = ("clean_entry.py", "clean_profile.py", "clean_build.py", "clean_prepare.py", "clean_support.py")


def bind_sources(repo):
    p.require(repo == ROOT and Path(a.__file__).resolve() == ENTRY / "entry_experiment.py", "adapter/checkout mismatch")
    for name, digest in FROZEN.items():
        p.require(p.sha(ENTRY / name) == digest, "frozen software gate changed: " + name)
    a.frozen_f.pinned_modules(repo)
    g.verify_sources(repo)
    return {str((HERE / name).relative_to(repo)): p.sha(HERE / name) for name in ADAPTERS}


def identity(repo, cfg, output):
    p.require(not output.exists(), "identity output already exists")
    sources = bind_sources(repo)
    files, profile = p.hardware_profile(repo, cfg)
    record = Path(cfg["build_record"])
    prepared = p.read(Path(cfg["hardware_source"]).parent / "prepare-state.json")
    p.require(prepared["status"] == "T17_CLEAN_SOURCE_PREPARED" and prepared["revision"] == p.SOURCE and
              prepared["hardware_submodules"] == 126 and prepared["repository_count"] == len(prepared["repositories"]) == 133 and
              prepared["build_executed"] is False and prepared["toolchain_reinstalled"] is False and
              all(r["generated_products_copied"] is False and r["cache_worktree_used"] is False for r in prepared["repositories"]),
              "clean source preparation incomplete")
    value = dict(contract=CONTRACT, hardware_contract=p.CONTRACT, source_commit=p.SOURCE,
                 hardware_profile=profile, configuration=cfg,
                 metadata_sha256={n: p.sha(record / n) for n in p.META_NAMES},
                 adapter_sources=sources, frozen_software_gates=FROZEN,
                 reference_sha256=files[cfg["reference"]], flash_sha256=p.FLASH,
                 prepare_state=prepared, historical_fixed_hardware_acceptance=False,
                 scope="same-host clean source/build; installed toolchain and download caches retained")
    g.save(output, value)
    return value


def validate_identity(repo, value):
    p.require(value["contract"] == CONTRACT and value["hardware_contract"] == p.CONTRACT and
              value["source_commit"] == p.SOURCE and value["historical_fixed_hardware_acceptance"] is False,
              "wrong T17 identity contract")
    p.require(value["adapter_sources"] == bind_sources(repo) and value["frozen_software_gates"] == FROZEN,
              "T17 adapter or frozen gate identity differs")
    p.require(set(value["metadata_sha256"]) == set(p.META_NAMES) and value["flash_sha256"] == p.FLASH,
              "T17 metadata inventory differs")
    profile = value["hardware_profile"]
    p.require(profile["contract"] == p.CONTRACT and profile["source_commit"] == p.SOURCE and
              profile["build_driver_sha256"] == p.BUILDER and profile["pins_sha256"] == value["metadata_sha256"]["hardware-inputs.json"] and
              profile["reference_provenance"]["binary_sha256"] == value["reference_sha256"], "T17 profile identity differs")


def install(repo, value, physical):
    """Bind a new identity in isolated team modules; never edit old source/locks."""
    validate_identity(repo, value)
    cfg = value["configuration"]
    if physical:
        files, checked = p.hardware_profile(repo, cfg)
        p.require(checked == value["hardware_profile"] and
                  {n: files[str(Path(cfg["build_record"]) / n)] for n in p.META_NAMES} == value["metadata_sha256"],
                  "physical build differs from selected T17 identity")
    private_f = g.load("t17_private_fullcore", repo / g.REL / "fullcore_screen.py")
    private_f.REFERENCE = value["reference_sha256"]
    private_f.FLASH = value["flash_sha256"]

    def configure(m, software_contract=False):
        m.f = private_f
        m.SOURCE = p.SOURCE
        m.EMU = value["hardware_profile"]["emu_sha256"]
        m.META = dict(value["metadata_sha256"])
        m.CONTRACT = a.candidate.CONTRACT if software_contract else p.CONTRACT
        m.hardware_profile = p.hardware_profile
        original = m.checker_files
        def checker_files(repo_):
            result = original(repo_)
            result.update({str(Path(repo_) / rel): digest for rel, digest in value["adapter_sources"].items()})
            return result
        m.checker_files = checker_files
        return m

    a.frozen_f = private_f
    a.frozen_m = configure(g.load("t17_private_merged", repo / g.REL / "merged_screen.py"))
    original_modules = evidence.modules
    def modules(repo_):
        portable, m, common = original_modules(repo_)
        configure(m, software_contract=True)
        common.m, common.f = m, private_f
        return portable, m, common
    evidence.modules = modules
    evidence.EXTRA |= set(value["adapter_sources"])


def archive_identity(repo, archive, identity_path, value):
    portable, _, _ = evidence.modules(repo)
    sealed = portable.Archive(archive)
    logical = "support/" + identity_path.name
    p.require(logical in sealed.records and sealed.raw(logical) == identity_path.read_bytes(),
              "T17 identity is not sealed in this archive")
    raw = lambda n: sealed.raw("hardware/" + n)
    for name, expected in value["metadata_sha256"].items():
        import hashlib
        p.require(hashlib.sha256(raw(name)).hexdigest() == expected, "sealed T17 build metadata differs: " + name)
    obj = lambda n: json.loads(raw(n))
    p.validate_metadata(obj("hardware-inputs.json"), obj("build-state.json"), obj("hardware-inputs-before.json"),
                        obj("baseline-hardware-inputs.json"), obj("generated-artifacts.json"),
                        value["metadata_sha256"]["executed-builder.py"], value["metadata_sha256"]["baseline-hardware-inputs.json"])
    suite = g.load("t17_archive_pin_fields", repo / "team/optimizations/o2/fullcore/run_suite.py")
    suite.validate_pin_fields(obj("hardware-inputs.json"))
    return sealed


def main(args):
    repo = args.repo.resolve()
    bind_sources(repo)
    p.require(1 <= args.jobs <= 4, "CPU budget")
    if os.name == "posix":
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    output = args.output.resolve()
    p.require(not output.exists(), "output must be new")
    cfg = a.config(args.config) if args.config else None
    if args.action == "identity":
        p.require(cfg is not None, "identity needs configuration")
        result = identity(repo, cfg, output)
    elif args.action in ("build-matrix", "build-c"):
        p.require(cfg is not None, "software build needs configuration")
        result = a.build(repo, cfg, output, args.shards, args.datasets, args.jobs) if args.action == "build-matrix" else c.build(repo, cfg, output)
    else:
        p.require(args.identity is not None, "new hardware identity is required")
        value = p.read(args.identity)
        p.require(cfg is None or cfg == value["configuration"], "config differs from T17 identity")
        cfg = value["configuration"]
        install(repo, value, args.action in ("run-matrix", "run-c", "audit-c", "pack-matrix", "pack-c"))
        if args.action == "run-matrix":
            p.require(args.build and args.operation_id, "run needs build and operation identity")
            result = a.run(repo, cfg, [x.resolve() for x in args.build], output, args.operation_id, args.negative, args.replay)
        elif args.action == "run-c":
            p.require(len(args.build or []) == 1 and args.operation_id, "C run needs one build and operation")
            result = c.run(repo, cfg, args.build[0].resolve(), output, args.operation_id)
        elif args.action == "audit-c":
            result = c.audit_run(repo, args.build[0].resolve(), args.run[0].resolve())
            g.save(output, dict(contract=CONTRACT, identity_sha256=p.sha(args.identity), proof=result))
        elif args.action == "pack-matrix":
            result = evidence.pack(repo, [r.resolve() for r in args.run], args.archive.resolve(), args.scope,
                                   support=[args.identity.resolve()])
            g.save(output, dict(contract=CONTRACT, identity_sha256=p.sha(args.identity), proof=result))
        elif args.action == "audit-matrix":
            archive_identity(repo, args.archive.resolve(), args.identity.resolve(), value)
            result = evidence.audit(repo, args.archive.resolve())
            g.save(output, dict(contract=CONTRACT, identity_sha256=p.sha(args.identity), proof=result))
        elif args.action == "index-matrix":
            archive_identity(repo, args.archive.resolve(), args.identity.resolve(), value)
            result = evidence.index_check(repo, args.archive.resolve())
            g.save(output, dict(contract=CONTRACT, identity_sha256=p.sha(args.identity), proof=result))
        elif args.action == "pack-c":
            archive_identity(repo, args.matrix.resolve(), args.identity.resolve(), value)
            result = c_evidence.pack(repo, args.build[0].resolve(), args.run[0].resolve(), args.archive.resolve(), args.matrix.resolve())
            g.save(output, dict(contract=CONTRACT, identity_sha256=p.sha(args.identity), proof=result))
        elif args.action == "audit-c-archive":
            archive_identity(repo, args.matrix.resolve(), args.identity.resolve(), value)
            result = c_evidence.audit_archive(repo, args.archive.resolve(), args.matrix.resolve())
            g.save(output, dict(contract=CONTRACT, identity_sha256=p.sha(args.identity), proof=result))
        else:
            archive_identity(repo, args.matrix.resolve(), args.identity.resolve(), value)
            result = c_evidence.index_check(repo, args.archive.resolve())
            g.save(output, dict(contract=CONTRACT, identity_sha256=p.sha(args.identity), proof=result))
        if args.action in ("run-matrix", "run-c"):
            g.save(output / "t17-result.json", dict(contract=CONTRACT, identity_sha256=p.sha(args.identity),
                   hardware_contract=p.CONTRACT, emu_sha256=value["hardware_profile"]["emu_sha256"],
                   historical_fixed_hardware_acceptance=False, software_gate_result=result))
    print(json.dumps({k: v for k, v in result.items() if k not in ("functions", "rows", "cases", "inputs", "prepare_state")}, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--action", required=True, choices=("identity", "build-matrix", "build-c", "run-matrix", "run-c", "audit-c",
                    "pack-matrix", "audit-matrix", "index-matrix", "pack-c", "audit-c-archive", "index-c"))
    ap.add_argument("--config", type=Path)
    ap.add_argument("--identity", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--build", type=Path, action="append")
    ap.add_argument("--run", type=Path, action="append")
    ap.add_argument("--archive", type=Path)
    ap.add_argument("--matrix", type=Path)
    ap.add_argument("--scope", choices=("probe", "matrix"), default="matrix")
    ap.add_argument("--shards", type=int, nargs="+", default=[1, 3, 5, 7])
    ap.add_argument("--datasets", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--negative", action="store_true")
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--operation-id")
    main(ap.parse_args())
