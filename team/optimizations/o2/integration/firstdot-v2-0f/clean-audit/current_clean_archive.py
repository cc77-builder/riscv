"""Strict current-clean archive bytes plus read-only raw recheck using physical originals.

No new EMU process is spawned. Semantic audit intentionally still needs original
physical source/build/run inputs; bytes-only verification is separately labelled.
Historical T17 contracts, source files and locks are never rewritten.
"""
from __future__ import annotations
import argparse
from datetime import datetime
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import types

CONTRACT = "zjh-current-clean-fullcore-archive-v1"
HERE = Path(__file__).resolve().parent
PORTABLE = "team/optimizations/o2/fullcore/portable.py"
PORTABLE_SHA = "7a2fc8e9638b898cc8f2f24fcb7794cf7108ef4e625bf38bcd8cc423ef3ae17b"
RECEIPT_TOOL = "team/optimizations/o2/repro/clean_fullcore_evidence.py"
RECEIPT_SHA = "20bebd4f5526a3522a09c2324e683d34b55997930c5078e89c3e5d04a6733412"
CLEAN_REL = "team/optimizations/o2/integration/firstdot-v2-0f/clean"
CORE = {"hello-vadd", "negative-vdot", "control", "dense-batch128"} | {f"functional-{i}" for i in range(8)}
SUPPLEMENTS = {"o2-diagnostic", "o2-control-diagnostic"}
PASS = "CURRENT_CLEAN_FULLCORE_PASS"

def require(ok, message):
    if not ok: raise ValueError(message)

def sha(path):
    d = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for raw in iter(lambda: stream.read(1048576), b""): d.update(raw)
    return d.hexdigest()

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value

def outside(output, roots):
    output = Path(output).resolve()
    require(not output.exists(), "new output required; preserve prior attempt")
    for root in roots:
        root = Path(root).resolve()
        require(not output.is_relative_to(root) and not root.is_relative_to(output), "output overlaps protected input")

def files_under(root):
    root = Path(root)
    values = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "symlink in evidence/source collection")
        if path.is_file():
            values[path.relative_to(root).as_posix()] = path
    return values

def portable(repo):
    path = Path(repo) / PORTABLE
    require(sha(path) == PORTABLE_SHA, "frozen portable reader changed")
    return load("current_archive_portable", path)

def selected_tools(repo, clean):
    repo, clean = Path(repo).resolve(), Path(clean).resolve()
    lock = read(HERE / "runtime-source-lock.json")
    require(lock["contract"] == "zjh-current-clean-archive-source-lock-v1"
            and set(lock["sources"]) == {"current_clean_common.py", "current_clean_build.py",
                "current_clean_profile.py", "current_clean_identity.py", "current_clean_fullcore.py"},
            "runtime source lock inventory")
    for name, expected in lock["sources"].items():
        require(sha(clean / name) == expected, "runtime adapter changed: " + name)
    sys.path.insert(0, str(clean))
    # These are trusted local, explicitly hash-pinned runtime modules.
    for name in ("current_clean_common", "current_clean_profile", "current_clean_identity"):
        old = sys.modules.get(name)
        require(old is None or Path(old.__file__).resolve() == clean / (name + ".py"), "runtime module from another tree")
    wrapper = load("current_archive_fullcore_wrapper", clean / "current_clean_fullcore.py")
    return wrapper

def receipt_tools(repo, fc):
    path = Path(repo) / RECEIPT_TOOL
    require(sha(path) == RECEIPT_SHA, "frozen spawn receipt checker changed")
    sys.path.insert(0, str(Path(repo) / "team/optimizations/o2/repro"))
    e = load("current_archive_private_receipts", path)
    # Only this private module instance receives this explicit new contract.
    e.fc, e.p, e.g, e.ce = fc, fc.p, fc.g, fc.ce
    e.CONTRACT = CONTRACT
    e.CONTROLLER = sha(fc.__file__)
    return e

def process_receipts(run, e):
    run = Path(run)
    files_under(run)
    state = read(run / "state.json")
    require(type(state["jobs"]) is int and 1 <= state["jobs"] <= 4
            and type(state["new_emu_runs"]) is int and type(state["new_emu_launch_attempts"]) is int
            and state["new_emu_runs"] == state["new_emu_launch_attempts"] == 14
            and type(state["cpu_affinity"]) is list and 1 <= len(state["cpu_affinity"]) <= 4
            and len(set(state["cpu_affinity"])) == len(state["cpu_affinity"])
            and all(type(cpu) is int and cpu >= 0 for cpu in state["cpu_affinity"]), "campaign resource/count types")
    proof = e.process_proof(run)
    rows = {}
    start, end = (datetime.fromisoformat(state[k]) for k in ("started", "finished"))
    require(start.utcoffset() is not None and end.utcoffset() is not None and start <= end, "campaign timeline")
    for name in sorted(CORE | SUPPLEMENTS):
        directory = run / "runs" / name
        row = read(directory / "result.json")
        raw = {n: (directory / n).read_bytes() for n in ("stdout.log", "stderr.log", "run.log")}
        require(row["raw_logs_sha256"] == {n: digest(v) for n, v in raw.items()}, "raw log digest changed")
        require(raw["run.log"] == raw["stderr.log"] + raw["stdout.log"], "run.log is not exact stderr+stdout")
        exit_raw = (directory / "exit-code.txt").read_bytes()
        require(re.fullmatch(rb"-?[0-9]+\n", exit_raw), "invalid exit receipt")
        require(type(row["exit_code"]) is int and row["exit_code"] == int(exit_raw), "actual exit receipt differs")
        require(row["exit_code"] == (1 if name == "negative-vdot" else 0), "unexpected real exit code")
        require(start <= datetime.fromisoformat(row["started"]) <= datetime.fromisoformat(row["finished"]) <= end,
                "job outside campaign lifetime")
        negative = name == "negative-vdot"
        require(row["negative_target"] == ("vdot" if negative else None)
                and row["environment_overrides"] == {"XS_NEGATIVE_VECTOR_TARGET": "vdot" if negative else None},
                "injection environment differs")
        rows[name] = row
    negative, recovery = rows["negative-vdot"], rows["functional-0"]
    require(negative["pid"] != recovery["pid"]
            and datetime.fromisoformat(negative["finished"]) <= datetime.fromisoformat(recovery["started"]),
            "negative and recovery not ordered distinct processes")
    require(negative["command"][6:8] == recovery["command"][6:8]
            and negative["command"][6] == "-i", "negative recovery images differ")
    require(read(run / "completed-runs.json") == sorted(rows.values(), key=lambda row: row["name"]),
            "completed-run index is not exact")
    return dict(status="CURRENT_CLEAN_PROCESS_RECEIPTS_PASS", delegated_frozen_proof=proof,
                source_new_emu_runs=14, new_emu_runs=0, negative_recovery_same_image=True)

def protected(repo, run, value):
    cfg = value["configuration"]
    return [repo, run, cfg["hardware_source"], cfg["build_record"], cfg["am_home"],
            Path(cfg["reference"]).parents[3]]

def physical(repo, clean, run, output):
    repo, clean, run, output = map(lambda p: Path(p).resolve(), (repo, clean, run, output))
    value = read(run / "identity.json")
    outside(output, protected(repo, run, value))
    wrapper = selected_tools(repo, clean)
    fc = wrapper.configure(repo, value)
    e = receipt_tools(repo, fc)
    before = process_receipts(run, e)
    result = fc.audit(repo, run, output)
    after = process_receipts(run, e)
    require(before == after, "receipt drift during raw audit")
    save(output / "process-bindings.json", after)
    receipt = dict(contract=CONTRACT, status="CURRENT_CLEAN_PHYSICAL_RAW_AUDIT_PASS",
        source_run=str(run), source_result_sha256=sha(run / "results.json"),
        identity_sha256=sha(run / "identity.json"), raw_result_sha256=sha(output / "results.json"),
        process_bindings_sha256=sha(output / "process-bindings.json"),
        auditor_sha256=sha(__file__), source_lock_sha256=sha(HERE / "runtime-source-lock.json"),
        controller_sha256=sha(clean / "current_clean_fullcore.py"), clean_adapter=str(clean),
        source_new_emu_runs=14, new_emu_runs=0, physical_originals_required=True,
        historical_t17_acceptance=False, scope="fresh raw recheck with physical source/build/input validation")
    require(result["source_new_emu_runs"] == 14 and result["new_emu_runs"] == 0
            and result["normal_reference_recovery"] is True, "raw recheck scope")
    save(output / "current-archive-physical.json", receipt)
    return receipt



def pinned_source_link(path, root, expected):
    path, root = Path(path), Path(root).resolve()
    if not path.is_symlink():
        return None
    require(path.resolve().is_relative_to(root), "pinned source symlink escapes hardware root")
    require(sha(path) == expected, "pinned source symlink content drift")
    return dict(target=os.readlink(path), resolved_target=str(path.resolve()), content_sha256=expected)


class Writer:
    def __init__(self, output, reader):
        self.output, self.reader = Path(output), reader
        self.output.mkdir(parents=True, exist_ok=False)
        self.records, self.originals, self.roles = [], {}, {}

    def add(self, path, logical, role, source_link=None):
        path = Path(path)
        self.reader.safe_relative(logical)
        require(path.is_file() and (not path.is_symlink() or (source_link is not None and role == "hardware-source")),
                "missing/unapproved symlink archive input")
        original, raw = str(path.absolute()), path.read_bytes()
        raw_sha = digest(raw)
        self.roles.setdefault(role, {})[original] = raw_sha
        if original in self.originals:
            require(self.originals[original]["sha256"] == raw_sha, "input drift during sealing")
            return
        stored, body, encoding = Path("files") / logical, raw, "identity"
        if len(raw) >= 4096:
            packed = gzip.compress(raw, compresslevel=6, mtime=0)
            if len(packed) + 64 < len(raw):
                stored, body, encoding = stored.with_name(stored.name + ".gz"), packed, "gzip"
        destination = self.output / stored
        require(not destination.exists(), "duplicate stored archive path")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(body)
        self.records.append(dict(original=original, stored=stored.as_posix(), encoding=encoding,
            raw_bytes=len(raw), raw_sha256=raw_sha, stored_bytes=len(body), stored_sha256=digest(body)))
        if source_link is not None:
            self.records[-1]["source_link"] = source_link
        self.originals[original] = dict(logical=logical, sha256=raw_sha)

    def finish(self, info):
        # This generated map is a marker, not a claim of a vanished source file.
        temp = self.output / "evidence-map.json"
        info = dict(info, roles=self.roles)
        save(temp, info)
        self.add(temp, "evidence-map.json", "generated-map")
        self.records[-1]["original"] = "generated:evidence-map"
        temp.unlink()
        manifest = dict(version=1, contract=CONTRACT, files=self.records)
        save(self.output / "archive-manifest.json", manifest)
        (self.output / "archive-manifest.sha256").write_text(
            sha(self.output / "archive-manifest.json") + "  archive-manifest.json\n", encoding="ascii")
        return self.reader.Archive(self.output)

def validate_physical_receipt(repo, clean, run, audit):
    receipt = read(audit / "current-archive-physical.json")
    expected = dict(contract=CONTRACT, status="CURRENT_CLEAN_PHYSICAL_RAW_AUDIT_PASS",
        source_run=str(run), source_result_sha256=sha(run / "results.json"),
        identity_sha256=sha(run / "identity.json"), raw_result_sha256=sha(audit / "results.json"),
        process_bindings_sha256=sha(audit / "process-bindings.json"),
        auditor_sha256=sha(__file__), source_lock_sha256=sha(HERE / "runtime-source-lock.json"),
        controller_sha256=sha(clean / "current_clean_fullcore.py"), clean_adapter=str(clean),
        source_new_emu_runs=14, new_emu_runs=0, physical_originals_required=True,
        historical_t17_acceptance=False, scope="fresh raw recheck with physical source/build/input validation")
    require(receipt == expected, "physical receipt/tool/source binding differs")
    return receipt

def pack(repo, clean, run, audit, output, source_scope="hardware"):
    repo, clean, run, audit, output = map(lambda p: Path(p).resolve(), (repo, clean, run, audit, output))
    value = read(run / "identity.json")
    outside(output, protected(repo, run, value) + [audit, clean, HERE])
    wrapper = selected_tools(repo, clean)
    fc = wrapper.configure(repo, value)
    e = receipt_tools(repo, fc)
    proof = process_receipts(run, e)
    require(proof == read(audit / "process-bindings.json"), "physical receipt replay differs")
    validate_physical_receipt(repo, clean, run, audit)
    inputs = read(run / "runtime-inputs.json")
    require(source_scope in ("direct", "hardware"), "unknown source collection scope")
    cfg = value["configuration"]
    emu = str(Path(cfg["hardware_source"]) / "build/emu")
    external = {emu: value["hardware_profile"]["emu_sha256"]}
    require(inputs.get(emu) == external[emu] and sha(emu) == external[emu], "EMU binding changed")
    reader = portable(repo)
    writer = Writer(output, reader)
    for role, root in (("campaign", run), ("physical-audit", audit)):
        for relative, path in files_under(root).items():
            writer.add(path, role + "/" + relative, role)
    for number, (name, expected) in enumerate(sorted(inputs.items())):
        require(sha(name) == expected, "runtime input drift at sealing")
        if name not in external:
            writer.add(Path(name), f"inputs/{number:05d}/" + Path(name).name, "runtime-input")
    for number, (name, expected) in enumerate(sorted(value["support_files"].items())):
        require(sha(name) == expected, "support provenance input drift")
        writer.add(Path(name), f"support/{number:05d}/" + Path(name).name, "support-input")
    for number, path in enumerate([Path(__file__).resolve(), HERE / "runtime-source-lock.json",
                                  repo / PORTABLE, repo / RECEIPT_TOOL] +
                                 [clean / n for n in read(HERE / "runtime-source-lock.json")["sources"]]):
        writer.add(path, f"auditors/{number:02d}/" + path.name, "auditor-source")
    source_links = {}
    if source_scope == "hardware":
        pins = read(Path(cfg["build_record"]) / "hardware-inputs.json")
        all_sources = pins["files"] | pins["dependency_files"]
        require(len(all_sources) == 429 + 21236, "hardware/dependency source inventory overlaps")
        for relative, expected in sorted(all_sources.items()):
            reader.safe_relative(relative)
            path = Path(cfg["hardware_source"]) / relative
            require(sha(path) == expected, "hardware/dependency source drift while packing")
            link = pinned_source_link(path, cfg["hardware_source"], expected)
            if link is not None:
                source_links[str(path.absolute())] = link
            writer.add(path, "hardware-source/" + relative, "hardware-source", source_link=link)
    info = dict(contract=CONTRACT, source_root=str(repo), clean_adapter=str(clean), campaign=str(run),
        physical_audit=str(audit), external_inputs=external, source_scope=source_scope, source_links=source_links,
        audit_source_sha256=sha(__file__), source_lock_sha256=sha(HERE / "runtime-source-lock.json"),
        auditor_path=str(Path(__file__).resolve()), source_lock_path=str(HERE / "runtime-source-lock.json"),
        controller_sha256=sha(clean / "current_clean_fullcore.py"), source_result_sha256=sha(run / "results.json"),
        identity_sha256=sha(run / "identity.json"), semantic_audit_requires_physical_originals=True,
        full_machine_environment_included=False, new_emu_runs=0,
        scope="Exact raw campaign, checker/controller sources, direct inputs and support proofs; EMU external. " +
              ("All 429 hardware and 21236 dependency source files included. " if source_scope == "hardware" else
               "Full hardware/dependency source trees external. ") +
              "Git object stores, installed tools and generated build tree remain external.")
    writer.finish(info)
    sealed, sealed_info, combined = open_archive(repo, output)
    live_match(sealed_info, combined)
    # Hash-only seal; semantic PASS is produced only by a later physical raw audit.
    return dict(status="CURRENT_CLEAN_ARCHIVE_BYTES_SEALED", contract=CONTRACT, new_emu_runs=0,
                semantic_recheck_executed=False, **sealed.bytes_result)

def open_archive(repo, archive):
    archive = Path(archive).resolve()
    sealed = portable(repo).Archive(archive)
    require(set(p.name for p in archive.iterdir()) == {"files", "archive-manifest.json", "archive-manifest.sha256"},
            "archive root inventory differs")
    require(sealed.manifest["contract"] == CONTRACT, "wrong archive contract")
    info = sealed.json("evidence-map.json")
    require(info["contract"] == CONTRACT and info["semantic_audit_requires_physical_originals"] is True
            and info["audit_source_sha256"] == sha(__file__)
            and info["source_lock_sha256"] == sha(HERE / "runtime-source-lock.json"), "archive audit identity differs")
    originals = {}
    for logical, row in sealed.records.items():
        original = row["original"]
        require(original not in originals, "duplicate original input mapping")
        originals[original] = logical
        require(original == "generated:evidence-map" or Path(original).is_absolute(), "nonabsolute original mapping")
    roles = info["roles"]
    require("generated-map" not in roles and set(roles) == {
        "campaign", "physical-audit", "runtime-input", "support-input", "auditor-source"} |
        ({"hardware-source"} if info["source_scope"] == "hardware" else set()), "archive role inventory differs")
    combined = {}
    for role, rows in roles.items():
        for original, expected in rows.items():
            require(original in originals and sealed.records[originals[original]]["raw_sha256"] == expected,
                    "archive role digest mapping differs")
            require(original not in combined or combined[original] == expected, "role identity conflict")
            combined[original] = expected
    require(set(originals) == set(combined) | {"generated:evidence-map"}, "unassigned archive payload")
    source_links = info.get("source_links", {})
    recorded_links = {row["original"]: row["source_link"] for row in sealed.records.values() if "source_link" in row}
    require(source_links == recorded_links and set(source_links) <= set(roles.get("hardware-source", {})),
            "source symlink metadata closure differs")
    for original, link in source_links.items():
        require(set(link) == {"target", "resolved_target", "content_sha256"}
                and isinstance(link["target"], str) and link["target"]
                and link["content_sha256"] == combined[original], "source symlink identity differs")
    for role in ("campaign", "physical-audit"):
        root = Path(info["campaign" if role == "campaign" else "physical_audit"])
        require(all(Path(name).is_relative_to(root) for name in roles[role]), "campaign original escapes root")
    expected_auditors = {
        info["auditor_path"]: info["audit_source_sha256"],
        info["source_lock_path"]: info["source_lock_sha256"],
        str(Path(info["source_root"]) / PORTABLE): PORTABLE_SHA,
        str(Path(info["source_root"]) / RECEIPT_TOOL): RECEIPT_SHA,
    }
    for name, expected in read(HERE / "runtime-source-lock.json")["sources"].items():
        expected_auditors[str(Path(info["clean_adapter"]) / name)] = expected
    require(roles["auditor-source"] == expected_auditors, "auditor/controller source closure differs")
    require(info["controller_sha256"] ==
            read(HERE / "runtime-source-lock.json")["sources"]["current_clean_fullcore.py"], "controller identity differs")
    def original_json(path):
        require(str(path) in originals, "missing original payload")
        return sealed.json(originals[str(path)])
    run = Path(info["campaign"])
    value = original_json(run / "identity.json")
    require(str(run / "results.json") in originals and
            digest(sealed.raw(originals[str(run / "results.json")])) == info["source_result_sha256"], "source result raw differs")
    require(digest(sealed.raw(originals[str(run / "identity.json")])) == info["identity_sha256"], "identity raw differs")
    runtime = original_json(run / "runtime-inputs.json")
    external = {str(Path(value["configuration"]["hardware_source"]) / "build/emu"):
                value["hardware_profile"]["emu_sha256"]}
    require(external == info["external_inputs"], "unexpected external omission")
    for link in source_links.values():
        require(Path(link["resolved_target"]).is_absolute() and
                Path(link["resolved_target"]).is_relative_to(Path(value["configuration"]["hardware_source"])),
                "recorded source symlink target escapes root")
    require(runtime == roles["runtime-input"] | external, "exact runtime input set not sealed")
    require(value["support_files"] == roles["support-input"], "support input set not sealed")
    require(info["source_scope"] in ("direct", "hardware"), "source scope differs")
    if info["source_scope"] == "hardware":
        pins = original_json(Path(value["configuration"]["build_record"]) / "hardware-inputs.json")
        expected = {str(Path(value["configuration"]["hardware_source"]) / rel): expected
                    for rel, expected in (pins["files"] | pins["dependency_files"]).items()}
        require(expected == roles["hardware-source"], "full source exact set differs")
    return sealed, info, combined

def bytes_only(repo, archive):
    sealed, info, _ = open_archive(repo, archive)
    return dict(status="CURRENT_CLEAN_ARCHIVE_BYTES_ONLY_PASS", contract=CONTRACT, new_emu_runs=0,
                raw_semantic_audit_executed=False, physical_originals_revalidated=False,
                source_scope=info["source_scope"], **sealed.bytes_result)

def live_match(info, combined):
    for original, expected in combined.items():
        path = Path(original)
        link = info.get("source_links", {}).get(original)
        if link is not None:
            require(path.is_symlink() and os.readlink(path) == link["target"]
                    and str(path.resolve()) == link["resolved_target"]
                    and sha(path) == link["content_sha256"] == expected, "physical source link differs")
        else:
            require(path.is_file() and not path.is_symlink() and sha(path) == expected,
                    "physical original differs from sealed payload: " + original)
    for path, expected in info["external_inputs"].items():
        require(Path(path).is_file() and sha(path) == expected, "physical external input missing/changed")
    for role in ("campaign", "physical-audit"):
        root = Path(info["campaign" if role == "campaign" else "physical_audit"])
        require({str(path.resolve()): sha(path) for path in files_under(root).values()} == info["roles"][role],
                "live campaign/audit exact file inventory differs")

def audit(repo, archive, output):
    repo, archive, output = Path(repo).resolve(), Path(archive).resolve(), Path(output).resolve()
    sealed, info, combined = open_archive(repo, archive)
    run, clean = Path(info["campaign"]), Path(info["clean_adapter"])
    value = read(run / "identity.json")
    outside(output, protected(repo, run, value) + [archive, Path(info["physical_audit"]), HERE])
    live_match(info, combined)
    raw = physical(repo, clean, run, output)
    live_match(info, combined)
    result = dict(status="CURRENT_CLEAN_ARCHIVE_LIVE_RAW_AUDIT_PASS", contract=CONTRACT,
        source_new_emu_runs=14, new_emu_runs=0, negative_reference_recovery=True,
        raw_audit_receipt_sha256=sha(output / "current-archive-physical.json"),
        original_physical_inputs_required=True, source_scope=info["source_scope"],
        detached_archive_semantic_recheck=False, historical_t17_acceptance=False, **sealed.bytes_result)
    save(output / "archive-live-recheck.json", result)
    return result

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--clean-adapter", type=Path)
    ap.add_argument("--action", choices=("physical", "pack", "bytes", "audit"), required=True)
    ap.add_argument("--run", type=Path)
    ap.add_argument("--audit", type=Path)
    ap.add_argument("--archive", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--source-scope", choices=("direct", "hardware"), default="hardware")
    args = ap.parse_args()
    clean = args.clean_adapter or args.repo / CLEAN_REL
    if args.action == "physical":
        require(args.run, "physical action needs completed run")
        result = physical(args.repo, clean, args.run, args.output)
    elif args.action == "pack":
        require(args.run and args.audit and args.archive, "pack needs run/audit/archive")
        outside(args.output, [args.repo, args.run, args.audit, args.archive, HERE])
        result = pack(args.repo, clean, args.run, args.audit, args.archive, args.source_scope)
        save(args.output, result)
    elif args.action == "bytes":
        require(args.archive, "bytes needs archive")
        outside(args.output, [args.repo, args.archive, HERE])
        result = bytes_only(args.repo, args.archive)
        save(args.output, result)
    else:
        require(args.archive, "audit needs archive")
        result = audit(args.repo, args.archive, args.output)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
