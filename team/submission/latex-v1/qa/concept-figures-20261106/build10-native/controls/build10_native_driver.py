"""Build four Build10 reports once on Windows from pinned, copied inputs.

Requires adjacent source-preservation.json and v2/overlay-manifest.json.
--overlay is an extracted directory containing exactly the four overlay files.
--assets is {"assets": [{"id": "S1-01", "path": "D:\\...\\S1-01.png",
                        "bytes": 123, "sha256": "<64 lowercase hex>"}, ...]}.
No generators, source expansion, image conversion, retries or publication.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time
import traceback
import zipfile


BASELINE_SHA = "e3a913fd7374e9948202d51844f0c7f127fe920c554bdbd0cc7aeb9d2e781ecc"
OVERLAY_SHA = "610d5da11884bfd04aeccdb634f0c6d812b4f62cb1a6a3997efa8f66c359ea50"
NAMES = {
    "main": "三阶段技术文档_合订本.pdf",
    "stage1": "第一阶段_执行日志与过程文档.pdf",
    "stage2": "第二阶段_设计与基础测试文档.pdf",
    "stage3": "第三阶段_协同仿真与性能分析.pdf",
}
OVERLAY_FILES = {
    "preamble.tex", "report-concepts.tex",
    "figures/ai-concepts/layout-map.json", "BUILD10_LAYOUT_README.md",
}
# Two native Windows caches observed by root after the first preflight failure.
# They are excluded, never copied/executed, and do not replace any formal input.
ADDITIONAL_WINDOWS_CACHES = {
    "__pycache__/figure_placeholders.cpython-313.pyc": {
        "bytes": 3747,
        "sha256": "ab4c8ffaf3b1f6af49a64c363cbb63a050a4923ac13833546d3a8fd874fd6e97",
    },
    "__pycache__/report_layout.cpython-313.pyc": {
        "bytes": 3068,
        "sha256": "bc881f7e8f456850cbaea13ec1f761d93e255f8a94898bc76ecac6a816b76bc8",
    },
}
THREAD_ENV = {
    name: "1" for name in (
        "OMP_NUM_THREADS", "OMP_THREAD_LIMIT", "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    )
}
THREAD_ENV.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"})


def utc():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def identity(path):
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def file_inventory(root):
    return {p.relative_to(root).as_posix(): identity(p)
            for p in sorted(root.rglob("*")) if p.is_file()}


def checked_copy(source, target, expected):
    data = source.read_bytes()
    actual = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    require(actual == expected, f"Input identity mismatch: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    require(identity(target) == expected, f"Copied identity mismatch: {target}")


def pin_one_cpu(requested):
    """Constrain this driver; its child processes inherit this affinity."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    pointer = ctypes.POINTER(ctypes.c_size_t)
    kernel.GetProcessAffinityMask.argtypes = [wintypes.HANDLE, pointer, pointer]
    kernel.GetProcessAffinityMask.restype = wintypes.BOOL
    kernel.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
    kernel.SetProcessAffinityMask.restype = wintypes.BOOL
    handle = kernel.GetCurrentProcess()
    process_mask, system_mask = ctypes.c_size_t(), ctypes.c_size_t()
    if not kernel.GetProcessAffinityMask(
            handle, ctypes.byref(process_mask), ctypes.byref(system_mask)):
        raise ctypes.WinError(ctypes.get_last_error())
    allowed = process_mask.value
    require(allowed != 0, "Cannot identify an allowed Windows CPU affinity mask")
    cpu = (allowed & -allowed).bit_length() - 1 if requested is None else requested
    require(0 <= cpu < ctypes.sizeof(ctypes.c_size_t) * 8
            and allowed & (1 << cpu), f"CPU {cpu} is outside the inherited mask")
    if not kernel.SetProcessAffinityMask(handle, 1 << cpu):
        raise ctypes.WinError(ctypes.get_last_error())
    if not kernel.GetProcessAffinityMask(
            handle, ctypes.byref(process_mask), ctypes.byref(system_mask)):
        raise ctypes.WinError(ctypes.get_last_error())
    require(process_mask.value == 1 << cpu, "Single-CPU affinity was not applied")
    return {"cpu": cpu, "inherited_mask": allowed, "applied_mask": process_mask.value}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "overlay", "assets", "output", "compiler"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--cpu", type=int,
                        help="Allowed Windows logical CPU; default: lowest allowed bit")
    args = parser.parse_args()
    require(os.name == "nt", "This is a Windows native driver; no cloud execution")
    paths = {name: getattr(args, name).resolve()
             for name in ("base", "overlay", "assets", "output", "compiler")}
    base, overlay, assets, out, compiler = (
        paths[name] for name in ("base", "overlay", "assets", "output", "compiler"))
    require(not out.exists(), f"Output already exists; preserve it: {out}")
    for input_root in (base, overlay):
        require(out != input_root and input_root not in out.parents,
                f"Output must be outside input tree: {input_root}")
    out.mkdir(parents=True, exist_ok=False)
    controls = out / "controls"
    controls.mkdir()
    source = out / "source"
    receipt = {
        "schema": "xiangshan-build10-native-build-v1", "started_utc": utc(),
        "status": "PREPARING", "arguments": {k: str(v) for k, v in paths.items()},
        "driver_pid": os.getpid(), "parallel_documents": 1,
        "passes_per_document": 3, "thread_environment": THREAD_ENV,
        "steps": [], "files": [], "visual_review_performed": False,
        "human_approval_claimed": False, "metadata_archive": "metadata.zip",
    }
    external_inputs = []
    base_expected = None
    source_expected = None
    base_verified = False
    source_frozen = False
    exit_code = 1

    def save_state():
        write_json(out / "state.json", receipt)

    def pin_external(path, expected=None):
        actual = identity(path)
        require(expected is None or actual == expected,
                f"External input identity mismatch: {path}")
        external_inputs.append({"path": str(path), **actual})
        return actual

    def load_control(path, expected_sha, archive_name):
        data = path.read_bytes()
        (controls / archive_name).write_bytes(data)
        require(hashlib.sha256(data).hexdigest() == expected_sha,
                f"Pinned control identity mismatch: {path}")
        pin_external(path, {"bytes": len(data), "sha256": expected_sha})
        return json.loads(data)

    def run_step(name, command):
        log = out / (name + "-driver.log")
        step = {"name": name, "command": command, "cwd": str(source),
                "started_utc": utc(), "log": log.name}
        receipt["status"] = name.upper()
        receipt["steps"].append(step)
        save_state()
        started = time.monotonic()
        process = None
        try:
            with log.open("xb") as stream:
                try:
                    process = subprocess.Popen(
                        command, cwd=source, stdout=stream, stderr=subprocess.STDOUT,
                        env=os.environ.copy(), creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                    step["pid"] = process.pid
                    save_state()
                    step["exit_code"] = process.wait()
                except BaseException:
                    if process is not None and process.poll() is None:
                        try:
                            killed = subprocess.run(
                                ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                                stdout=stream, stderr=subprocess.STDOUT, timeout=30)
                            step["termination_attempt_exit_code"] = killed.returncode
                            process.wait(timeout=30)
                        except Exception as cleanup_error:
                            step["termination_error"] = repr(cleanup_error)
                    raise
                finally:
                    step["finished_utc"] = utc()
                    step["seconds"] = round(time.monotonic() - started, 3)
                    step["direct_process_exited"] = (
                        process is not None and process.poll() is not None)
        finally:
            if log.is_file():
                step["log_identity"] = identity(log)
            save_state()
        print(json.dumps({"step": name, "exit_code": step["exit_code"]}), flush=True)
        require(step["exit_code"] == 0, f"{name} failed; see {log}")

    try:
        script = Path(__file__).resolve()
        shutil.copyfile(script, controls / script.name)
        receipt["driver_identity"] = pin_external(script)
        receipt["python"] = {
            "executable": sys.executable, "version": sys.version,
            "identity": pin_external(Path(sys.executable).resolve()),
        }
        receipt["cpu_affinity"] = pin_one_cpu(args.cpu)
        os.environ.update(THREAD_ENV)
        receipt["compiler_identity"] = pin_external(compiler)
        baseline = load_control(
            script.with_name("source-preservation.json"), BASELINE_SHA,
            "source-preservation.json")
        overlay_manifest = load_control(
            script.parent / "v2/overlay-manifest.json", OVERLAY_SHA,
            "overlay-manifest.json")
        ignored = set(baseline["excluded_existing_cache_paths"])
        base_expected = {name: pin for name, pin in baseline["baseline_files"].items()
                         if name not in ignored}
        omitted = set(baseline["omitted_old_output_files"])
        require(len(base_expected) == 448 and len(ignored) == 7 and len(omitted) == 4,
                "Baseline file counts differ from the reviewed source-preservation record")
        require(base.is_dir() and overlay.is_dir(), "Base/overlay must be directories")
        actual_names = {p.relative_to(base).as_posix()
                        for p in base.rglob("*") if p.is_file()}
        extra_caches = set(ADDITIONAL_WINDOWS_CACHES)
        require(not (extra_caches & (set(base_expected) | ignored)),
                "Additional cache paths overlap the frozen baseline")
        observed_caches = []
        for name in sorted(extra_caches & actual_names):
            actual = identity(base / name)
            observed_caches.append({
                "path": str(base / name), "relative_path": name, **actual,
                "copied": False, "executed": False, "rendering_input": False})
            receipt["additional_windows_caches_observed"] = observed_caches
            save_state()
            require(actual == ADDITIONAL_WINDOWS_CACHES[name],
                    f"Additional Windows cache identity differs from root observation: {name}")
        receipt["additional_windows_caches_observed"] = observed_caches
        receipt["additional_windows_cache_allowed_paths"] = sorted(extra_caches)
        require(not (actual_names - set(base_expected) - ignored - extra_caches),
                "Unexpected base files outside the 448 formal inputs, 7 original caches, "
                "and 2 exact Windows cache exclusions: "
                + repr(sorted(actual_names - set(base_expected) - ignored - extra_caches)))
        for name, expected in base_expected.items():
            require(identity(base / name) == expected, f"Base input mismatch: {name}")
        base_verified = True
        receipt["base_formal_files_verified"] = len(base_expected)
        receipt["declared_caches_ignored_if_present"] = sorted(ignored & actual_names)
        overlay_rows = overlay_manifest["files"]
        require(len(overlay_rows) == 4
                and {r["path"] for r in overlay_rows} == OVERLAY_FILES,
                "Overlay does not contain exactly the four reviewed paths")
        require({p.relative_to(overlay).as_posix()
                 for p in overlay.rglob("*") if p.is_file()} == OVERLAY_FILES,
                "Overlay directory has missing or extra files")
        for row in overlay_rows:
            pin_external(overlay / row["path"], row["after"])
        raw_assets = assets.read_bytes()
        (controls / "assets-manifest.json").write_bytes(raw_assets)
        receipt["asset_manifest_identity"] = pin_external(
            assets, {"bytes": len(raw_assets),
                     "sha256": hashlib.sha256(raw_assets).hexdigest()})
        asset_rows = json.loads(raw_assets)["assets"]
        layout_path = overlay / "figures/ai-concepts/layout-map.json"
        layout_bytes = layout_path.read_bytes()
        layout_pin = next(r["after"] for r in overlay_rows
                          if r["path"] == "figures/ai-concepts/layout-map.json")
        require({"bytes": len(layout_bytes),
                 "sha256": hashlib.sha256(layout_bytes).hexdigest()} == layout_pin,
                "Layout identity changed before asset mapping")
        layout = json.loads(layout_bytes)
        target_ids = [row["id"] for row in layout["illustrations"]]
        require(len(target_ids) == 22 and len(set(target_ids)) == 22,
                "Reviewed layout target set is not 22 unique IDs")
        require(isinstance(asset_rows, list) and len(asset_rows) == 22
                and {row["id"] for row in asset_rows} == set(target_ids),
                "Asset manifest must contain exactly the 22 unique layout IDs")
        source.mkdir()
        source_expected = {name: pin for name, pin in base_expected.items()
                           if name not in omitted}
        require(len(source_expected) == 444, "Expected 444 original source files")
        for name, expected in source_expected.items():
            checked_copy(base / name, source / name, expected)
        for row in overlay_rows:
            name = row["path"]
            require(row["before"] == base_expected.get(name),
                    f"Overlay baseline mismatch: {name}")
            checked_copy(overlay / name, source / name, row["after"])
            source_expected[name] = row["after"]
        asset_records = []
        for row in asset_rows:
            require(isinstance(row["bytes"], int) and not isinstance(row["bytes"], bool)
                    and row["bytes"] > 0
                    and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]),
                    f"Invalid PNG identity record: {row['id']}")
            path = Path(row["path"])
            require(path.is_absolute(), f"PNG path must be absolute: {path}")
            path = path.resolve()
            expected = {key: row[key] for key in ("bytes", "sha256")}
            pin_external(path, expected)
            name = f"figures/ai-concepts/{row['id']}.png"
            checked_copy(path, source / name, expected)
            header = (source / name).read_bytes()[:24]
            require(len(header) == 24 and header[:8] == b"\x89PNG\r\n\x1a\n"
                    and header[12:16] == b"IHDR", f"Not a PNG: {row['id']}")
            width, height = struct.unpack(">II", header[16:24])
            require(width > 0 and height > 0, f"Invalid PNG dimensions: {row['id']}")
            asset_records.append({
                "id": row["id"], "original_path": str(path), "copied_path": name,
                **expected, "width": width, "height": height,
            })
            source_expected[name] = expected
        require(len(source_expected) == 469 and file_inventory(source) == source_expected,
                "New report source does not match the 444 + 3 + 22 frozen files")
        write_json(out / "frozen-sources.json", {
            "schema": "xiangshan-build10-source-freeze-v1",
            "source_root": str(source), "files": source_expected})
        source_frozen = True
        write_json(out / "asset-receipt.json", {
            "status": "ORIGINAL_PNG_BYTES_COPIED_AND_VERIFIED_NOT_VISUALLY_REVIEWED",
            "manifest": receipt["asset_manifest_identity"], "assets": asset_records})
        write_json(out / "frozen-external-inputs.json", external_inputs)
        receipt["source_files_frozen"] = len(source_expected)
        receipt["concept_png_files"] = 22
        save_state()
        for document in NAMES:
            run_step(document, [
                sys.executable, "-B", "-X", "utf8", str(source / "build.py"),
                "--compiler", str(compiler), "--output-dir", str(out / document),
                "--documents", document])
        delivery = out / "delivery"
        delivery.mkdir()
        for document, name in NAMES.items():
            pdf = out / document / name
            checked_copy(pdf, delivery / name, identity(pdf))
            receipt["files"].append({
                "document": document, "build_origin": "build-10",
                "path": str(delivery / name), **identity(delivery / name)})
        run_step("inspect", [
            sys.executable, "-B", "-X", "utf8", str(source / "qa/inspect_reports.py"),
            "--compiled-dir", str(delivery), "--logs-dir", str(out),
            "--result-dir", str(out / "qa")])
        inspection = json.loads((out / "qa/pdf-inspection.json").read_bytes())
        require(set(inspection["reports"]) == set(NAMES), "Inspector missed a report")
        issues = {}
        for document, record in inspection["reports"].items():
            bad = {key: record[key] for key in (
                "outside_text", "footer_mismatches", "placeholder_pages") if record[key]}
            for key in ("a4_all_pages", "figure_captions_unique"):
                if not record[key]:
                    bad[key] = record[key]
            if bad:
                issues[document] = bad
        receipt["automated_structural_issues"] = issues
        receipt["log_diagnostics_for_review"] = {
            key: value["final_log_diagnostics"]
            for key, value in inspection["reports"].items()
            if value["final_log_diagnostics"]}
        require(not issues, "Original inspector found structural issues; see qa/")
        receipt["status"] = "AUTOMATED_INSPECTION_COMPLETE_VISUAL_REVIEW_PENDING"
        exit_code = 0
    except BaseException as error:
        receipt["status"] = "FAILED_EVIDENCE_PRESERVED_NO_RETRY"
        receipt["error"] = {"type": type(error).__name__, "message": str(error)}
        (out / "failure-traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
        exit_code = 130 if isinstance(error, KeyboardInterrupt) else 1
    finally:
        mismatches = []
        checks = [("external", Path(r["path"]), {"bytes": r["bytes"], "sha256": r["sha256"]})
                  for r in external_inputs]
        if base_verified:
            checks += [("base", base / n, p) for n, p in base_expected.items()]
        if source_frozen:
            checks += [("source", source / n, p) for n, p in source_expected.items()]
        for kind, path, expected in checks:
            try:
                actual = identity(path)
                if actual != expected:
                    mismatches.append({"kind": kind, "path": str(path),
                                       "expected": expected, "actual": actual})
            except Exception as error:
                mismatches.append({"kind": kind, "path": str(path), "error": str(error)})
        if source_frozen:
            source_extras = ({p.relative_to(source).as_posix()
                              for p in source.rglob("*") if p.is_file()}
                             - set(source_expected))
            if source_extras:
                mismatches.append({"kind": "source_extra_files",
                                   "paths": sorted(source_extras)})
        write_json(out / "post-input-check.json", {
            "checks": len(checks), "mismatches": mismatches,
            "base_verified_before_execution": base_verified,
            "source_freeze_complete": source_frozen,
            "scope": "Pinned report/control/PNG/compiler/interpreter bytes only; "
                     "not a complete system library or font byte freeze."})
        if mismatches:
            receipt["status"] = "FAILED_INPUT_IDENTITY_CHANGED_EVIDENCE_PRESERVED"
            exit_code = 1
        receipt["post_input_mismatch_count"] = len(mismatches)
        receipt["completed_utc"] = utc()
        receipt["exit_code"] = exit_code
        write_json(out / "build-receipt.json", receipt)
        save_state()
        try:
            # Preserve raw logs and controls, without duplicating PDFs or PNG inputs.
            members = [p for p in out.iterdir() if p.is_file()]
            members += [p for p in controls.rglob("*") if p.is_file()]
            for name in (*NAMES, "qa"):
                directory = out / name
                if directory.exists():
                    members += [p for p in directory.rglob("*")
                                if p.is_file() and p.suffix.lower() != ".pdf"]
            temporary = out / "metadata.zip.partial"
            with zipfile.ZipFile(temporary, "x", zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(set(members)):
                    archive.write(path, path.relative_to(out).as_posix())
            temporary.rename(out / "metadata.zip")
            write_json(out / "metadata-receipt.json", {
                "path": str(out / "metadata.zip"), **identity(out / "metadata.zip"),
                "member_count": len(set(members)),
                "scope": "Build receipt, frozen identities, raw logs and controls; "
                         "full copied source and final PDFs remain beside the archive."})
        except Exception as error:
            receipt["status"] = "FAILED_METADATA_ARCHIVE_EVIDENCE_PRESERVED"
            receipt["metadata_error"] = repr(error)
            receipt["exit_code"] = exit_code = 1
            write_json(out / "build-receipt.json", receipt)
            save_state()
        print(json.dumps({"status": receipt["status"], "exit_code": exit_code,
                          "output": str(out)}, ensure_ascii=False), flush=True)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
