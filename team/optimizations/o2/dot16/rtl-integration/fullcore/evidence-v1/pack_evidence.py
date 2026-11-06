#!/usr/bin/env python3
"""Archive completed fullcore attempts and bound runtime files without rerunning them."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import zipfile


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--record-root", type=Path, required=True)
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--windows-output", type=Path, required=True)
    args = parser.parse_args()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    assert os.sched_getaffinity(0) == {1}, "one assigned CPU required"
    assert not args.output.exists() and args.windows_output.is_dir()
    receipt_data = json.loads(args.receipts.read_text(encoding="utf-8-sig"))
    selected, by_source, outcomes = {}, {}, {}

    def add(path, member):
        path = Path(path).absolute()
        assert path.is_file() and not path.is_symlink(), str(path)
        assert not Path(member).is_absolute() and ".." not in Path(member).parts
        if str(path) in by_source:
            return
        assert member not in selected
        selected[member], by_source[str(path)] = path, member

    def runtime_member(path):
        if path.is_relative_to(args.record_root):
            return "records/" + path.relative_to(args.record_root).as_posix()
        if path.is_relative_to(args.repo):
            return "runtime/source/" + path.relative_to(args.repo).as_posix()
        return "runtime/external/" + path.as_posix().lstrip("/")

    for name, receipt in receipt_data["runs"].items():
        assert name in ("image-01", "build-01", "native-01", "native-02", "smoke-01")
        directory = args.record_root / name
        state = json.loads((directory / "status.json").read_text())
        result = receipt["result"]
        assert receipt["status"] in ("succeeded", "failed") and result["cleanup_complete"]
        assert state.get("finished") and state["status"] not in ("CAPTURING", "BUILDING", "RUNNING")
        if state["status"].endswith("_PASS"):
            assert result["exit_code"] == 0 and not result["timed_out"] and not result["cancelled"]
        else:
            assert state["status"] == "FAILED" and not state.get("fullcore_difftest_qualified", False)
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                add(path, "records/" + name + "/" + path.relative_to(directory).as_posix())
        outcomes[name] = dict(status=state["status"], operation_id=receipt["operation_id"],
                              started_at=receipt["started_at"], updated_at=receipt["updated_at"],
                              exit_code=result["exit_code"], cleanup_complete=result["cleanup_complete"],
                              status_sha256=digest(directory / "status.json"))
        runtime = directory / "runtime-inputs.json"
        if runtime.is_file():
            for source, expected in json.loads(runtime.read_text()).items():
                path = Path(source)
                assert digest(path) == expected, "changed runtime input: " + source
                add(path, runtime_member(path))
        if state["status"] == "DOT16_FULLCORE_BUILD_PASS":
            inputs = json.loads((directory / "build-inputs.json").read_text())
            emu = Path(inputs["emu"]["path"])
            assert digest(emu) == inputs["emu"]["sha256"]
            add(emu, runtime_member(emu))

    for name in ("pre-native-freeze.json", "native-preflight-02.json", "native-preflight-02.stdout", "native-preflight-02.stderr"):
        path = args.record_root / name
        if path.exists():
            add(path, "records/" + name)
    leaf = args.repo / "team/optimizations/o2/dot16/rtl-integration"
    for name in ("candidate.patch", "source-manifest.json"):
        add(leaf / name, "delivery/" + name)
    for name in ("CONTRACT.md", "build.py", "smoke.py", "Makefile", "main.c", "kernels.S", "abi_probe.cpp",
                 "resume_native.py", "RESUME_NATIVE_CONTRACT.md"):
        add(leaf / "fullcore" / name, "delivery/fullcore/" + name)
    for name in ("time.log", "emu-compile/VSimTop.mk", "emu-compile/VSimTop_classes.mk",
                 "generated-src/diffstate.h", "generated-src/difftest-dpic.h"):
        path = args.repo / "build" / name
        if path.is_file():
            add(path, runtime_member(path))
    add(args.receipts, "operation-receipts.json")
    add(Path(__file__).resolve(), "pack_evidence.py")
    members = [dict(name=name, source=str(path), bytes=path.stat().st_size, sha256=digest(path))
               for name, path in sorted(selected.items())]
    args.output.mkdir(parents=True, exist_ok=False)
    archive = args.output / "raw.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=3) as bundle:
        for row in members:
            bundle.write(selected[row["name"]], row["name"])
    with zipfile.ZipFile(archive) as bundle:
        assert sorted(bundle.namelist()) == [row["name"] for row in members]
        for row in members:
            observed, count = hashlib.sha256(), 0
            with bundle.open(row["name"]) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    observed.update(block)
                    count += len(block)
            assert count == row["bytes"] and observed.hexdigest() == row["sha256"]
            assert digest(selected[row["name"]]) == row["sha256"], "source changed while archiving"
    manifest = dict(schema=1, kind="dot16-fullcore-existing-evidence-v1", started_utc=started,
                    finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    archive=dict(name=archive.name, bytes=archive.stat().st_size, sha256=digest(archive)),
                    runs=outcomes, member_count=len(members),
                    member_uncompressed_bytes=sum(row["bytes"] for row in members), members=members,
                    original_runs_modified=False, tests_rerun=False,
                    excluded=dict(generated_intermediates="Existing ROOT/build C++/RTL/objects/PCH/caches remain at original paths; full pre-native file identities retained in pre-native-freeze.json. Only EMU and selected headers/Make/time records included.",
                                  external_build_dependencies="Original dependency identities retained; tool/JAR/library payloads are not duplicated except bound test runtime files."),
                    verification="Each archived member streamed and SHA/size compared, then each source SHA rechecked.")
    write_json(args.output / "manifest.json", manifest)
    shutil.copyfile(args.receipts, args.output / "operation-receipts.json")
    shutil.copyfile(Path(__file__).resolve(), args.output / "pack_evidence.py")
    (args.output / ".gitattributes").write_text("raw.zip -text\n")
    copied = []
    for path in sorted(args.output.iterdir()):
        target = args.windows_output / path.name
        assert not target.exists(), "preserve preexisting Windows artifact"
        shutil.copyfile(path, target)
        assert digest(target) == digest(path)
        copied.append(dict(name=path.name, bytes=path.stat().st_size, sha256=digest(path)))
    print(json.dumps(dict(status="FULLCORE_ARCHIVE_BYTE_VERIFIED", output=str(args.output),
                         windows_output=str(args.windows_output), files=copied,
                         member_count=len(members), tests_rerun=False), ensure_ascii=False))


if __name__ == "__main__":
    main()
