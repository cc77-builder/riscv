"""Narrow clean-02 shallow metadata restoration; no fetch, source writes, or RTL edits."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

CONTRACT = "current-clean-shallow-metadata-restore-v1"
REVISION = "c823a8786e052c6e26f6915563c42b6d730dd8e3"
EXPECTED_BOUNDARY = "16ae9ddcda54fc9a2fddffad73174cf793ac7814"
EXPECTED_SHALLOW_SHA = "f785f2b3aead4449129beede03711c25f57349392c41ea41e25b4d1a7f0afcbc"
COMMANDS = []

def require(ok, message):
    if not ok:
        raise ValueError(message)

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    path = Path(path)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def read(path):
    return json.loads(Path(path).read_text())

def command(repo, *args, check=True):
    argv = ["git", "-C", str(repo), *args]
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    p = subprocess.run(argv, env=env, capture_output=True, text=True)
    row = dict(command=argv, exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr)
    COMMANDS.append(row)
    if check:
        require(p.returncode == 0, "read-only Git failed: " + repr(row))
    return row

def git(repo, *args):
    return command(repo, *args)["stdout"].strip()

def git_path(repo, name):
    p = Path(git(repo, "rev-parse", "--git-path", name))
    return p.resolve() if p.is_absolute() else (Path(repo) / p).resolve()

def boundaries(path):
    path = Path(path)
    if not path.exists():
        return []
    require(path.is_file() and not path.is_symlink(), "shallow metadata is not a regular file")
    values = path.read_text().splitlines()
    require(bool(values) and all(re.fullmatch("[0-9a-f]{40}", value) for value in values),
            "invalid shallow boundary metadata")
    return values

def identity(repo):
    return dict(head=git(repo, "rev-parse", "HEAD"), index_sha256=sha(git_path(repo, "index")),
                shallow_path=str(git_path(repo, "shallow")),
                shallow_sha256=sha(git_path(repo, "shallow")))

def inspect(row, number, root, stage):
    source, target = Path(row["source"]).resolve(), Path(row["destination"]).resolve()
    require(target.is_relative_to(root) and not source.is_relative_to(target),
            "destination must be isolated inside clean-02")
    require(Path(git(source, "rev-parse", "--show-toplevel")).resolve() == source,
            "source repository root differs")
    require(Path(git(target, "rev-parse", "--show-toplevel")).resolve() == target,
            "destination repository root differs")
    source_meta, target_meta = identity(source), identity(target)
    require(target_meta["head"] == row["revision"], "prepared target HEAD changed")
    require((target / ".git").is_dir() and not (target / ".git").is_symlink()
            and Path(git(target, "rev-parse", "--absolute-git-dir")).resolve() == target / ".git"
            and not (target / ".git/objects/info/alternates").exists(), "target must retain independent Git metadata")
    require(target_meta["shallow_path"] == str(target / ".git/shallow"), "unexpected target shallow path")
    require(git(target, "remote", "get-url", "origin") == row["origin"], "target origin changed")
    require(git(source, "cat-file", "-t", row["revision"]) == "commit", "cached selected commit missing")
    source_count = git(source, "rev-list", "--count", row["revision"])
    require(source_count.isdigit(), "source traversal did not return count")
    source_lines, target_lines = boundaries(source_meta["shallow_path"]), boundaries(target_meta["shallow_path"])
    source_set, target_set = set(source_lines), set(target_lines)
    require(target_set <= source_set, "existing target introduces a foreign shallow boundary")
    for commit in sorted(source_set):
        require(git(source, "cat-file", "-t", commit) == "commit", "source boundary object missing")
    for commit in sorted(target_set):
        require(git(target, "cat-file", "-t", commit) == "commit", "target boundary object missing")
    traversal = command(target, "rev-list", "--count", "HEAD", check=False)
    missing_main = (number == 0 and stage == "after-prepare"
                    and target_meta["shallow_sha256"] is None and bool(source_set))
    if missing_main:
        require(target == root / "checkout/source" and source_set == {EXPECTED_BOUNDARY}
                and source_meta["shallow_sha256"] == EXPECTED_SHALLOW_SHA,
                "only exact observed MAIN shallow metadata can be restored")
        require(traversal["exit_code"] == 128
                and "Could not read e524aeedab50586b2dbc86a2180380085c43a4cd" in traversal["stderr"]
                and "16ae9ddcda54fc9a2fddffad73174cf793ac7814" in traversal["stderr"],
                "missing metadata failure differs from recorded incident")
        require(git(target, "cat-file", "-t", EXPECTED_BOUNDARY) == "commit", "target boundary object absent")
    else:
        require(traversal["exit_code"] == 0 and traversal["stdout"].strip().isdigit(),
                "existing target does not traverse HEAD")
    return dict(source=str(source), destination=str(target), revision=row["revision"],
        source_before=source_meta, target_before=target_meta,
        source_boundary_lines=source_lines, target_boundary_lines=target_lines,
        source_boundary_set=sorted(source_set), target_boundary_set=sorted(target_set),
        existing_target_boundary_subset=True,
        omitted_source_boundaries=sorted(source_set - target_set),
        source_selected_revision_commit_count=int(source_count),
        original_clone_traversal=traversal,
        operation="RESTORE_MISSING_MAIN_SHALLOW" if missing_main else "VERIFY_ONLY",
        existing_shallow_modified=False,
        original_clone_record=row)

def main(args):
    prepare, receipt = args.prepare.resolve(), args.receipt.resolve()
    root = prepare.parent.parent
    require(root.name == "clean-02" and prepare == root / "checkout/prepare-state.json",
            "this narrow tool only accepts fresh clean-02")
    require(not receipt.exists() and not receipt.is_relative_to(root / "checkout/source"),
            "new external receipt required")
    require(args.action in ("plan", "apply") and args.stage in ("after-prepare", "after-support"), "invalid action/stage")
    require(args.stage != "after-support" or args.action == "plan", "after-support is read-only")
    require(args.stage != "after-support" or args.support is not None, "support record required")
    require(args.stage != "after-prepare" or args.support is None, "prepare stage excludes support record")
    result = dict(contract=CONTRACT, action=args.action, stage=args.stage, status="RUNNING", started=now(),
        tool_sha256=sha(__file__), source_revision=REVISION, new_builds=0, new_emu_runs=0,
        source_git_modified=False, rtl_modified=False, frozen_prepare_modified=False, repositories=[])
    metadata_files = {str(prepare): sha(prepare)}
    result["input_metadata"] = metadata_files
    try:
        prepared = read(prepare)
        require(prepared["status"] == "T17_CLEAN_SOURCE_PREPARED" and prepared["revision"] == REVISION
                and prepared["repository_count"] == len(prepared["repositories"]) == 133
                and prepared["hardware_submodules"] == 126 and prepared["build_executed"] is False,
                "fresh 133-repository prepare required")
        records = prepared["repositories"]
        source = root / "checkout/source"
        require(records[0]["destination"] == str(source), "unexpected prepared main source")
        if args.stage == "after-prepare":
            require(not (source / "build").exists() and not (source / "out").exists(),
                    "metadata restoration must precede all hardware generated outputs")
        if args.support:
            support = args.support.resolve()
            require(support == root / "support/repositories.json", "unexpected support inventory")
            support_state = read(support.parent / "state.json")
            require(support_state["status"] == "T17_CLEAN_SUPPORT_BUILD_PASS", "support must complete first")
            additions = read(support)
            require(len(additions) == 12, "exactly 12 support restore records required")
            records = records + additions
            metadata_files[str(support)] = sha(support)
            metadata_files[str(support.parent/"state.json")] = sha(support.parent/"state.json")
        require(len({row["destination"] for row in records}) == len(records), "duplicate restored repository")
        rows = [inspect(row, i, root, args.stage) for i, row in enumerate(records)]
        result["repositories"] = rows
        pending = [row for row in rows if row["operation"] == "RESTORE_MISSING_MAIN_SHALLOW"]
        require(len(pending) <= 1, "multiple unexpected metadata restorations")
        result["planned_writes"] = len(pending)
        # All checks finish before any target metadata write.
        for row in rows:
            require(identity(Path(row["source"])) == row["source_before"], "source Git metadata changed during review")
            require(identity(Path(row["destination"])) == row["target_before"], "destination metadata changed during review")
        if args.action == "apply":
            for row in pending:
                path = Path(row["target_before"]["shallow_path"])
                raw = Path(row["source_before"]["shallow_path"]).read_bytes()
                require(hashlib.sha256(raw).hexdigest() == EXPECTED_SHALLOW_SHA, "source shallow drift")
                with path.open("xb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                row["restored_shallow_sha256"] = sha(path)
                require(row["restored_shallow_sha256"] == row["source_before"]["shallow_sha256"], "copy was not byte-exact")
            for row in rows:
                target = Path(row["destination"])
                row["target_after"] = identity(target)
                expected = dict(row["target_before"])
                if row["operation"] == "RESTORE_MISSING_MAIN_SHALLOW":
                    expected["shallow_sha256"] = row["source_before"]["shallow_sha256"]
                require(row["target_after"] == expected, "unexpected target metadata/HEAD/index change")
                row["post_traversal"] = command(target, "rev-list", "--count", "HEAD")
                require(row["post_traversal"]["stdout"].strip().isdigit(), "post-repair traversal count")
                require(identity(Path(row["source"])) == row["source_before"], "source Git changed")
            result.update(status="CLEAN_SHALLOW_METADATA_RESTORED", actual_writes=len(pending))
        else:
            result.update(status=("CLEAN_SHALLOW_ALL_REPOSITORIES_VERIFIED" if args.stage == "after-support"
                                  else "CLEAN_SHALLOW_REPAIR_PLAN_READY"), actual_writes=0)
        require(all(sha(path) == digest for path, digest in metadata_files.items()), "frozen preparation/support evidence changed")
        result["repository_count"] = len(rows)
    except BaseException as exc:
        result.update(status="FAILED", error=repr(exc))
        raise
    finally:
        result.update(finished=now(), commands=COMMANDS)
        receipt.parent.mkdir(parents=True, exist_ok=True)
        with receipt.open("x") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
    print(result["status"], result.get("repository_count"), result.get("actual_writes"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", type=Path, required=True)
    parser.add_argument("--support", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--stage", choices=("after-prepare", "after-support"), required=True)
    parser.add_argument("--action", choices=("plan", "apply"), required=True)
    main(parser.parse_args())
