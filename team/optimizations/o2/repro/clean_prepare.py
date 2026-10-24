"""Restore clean Git checkouts from explicit, read-only local object caches.

No generated build products or working-tree changes are copied. Every repository
has an independent object store and index. This is a same-host cached-source
reproduction, not evidence of a fresh machine or an offline toolchain install.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess


def now():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def links(repo):
    result = []
    for item in git(repo, "ls-tree", "-rz", "HEAD").split(b"\0"):
        if not item:
            continue
        meta, name = item.split(b"\t", 1)
        mode, _, revision = meta.decode().split()
        if mode == "160000":
            result.append((name.decode(), revision))
    return result


def restore(source, destination, revision, records, log):
    source, destination = source.resolve(), destination.resolve()
    require(re.fullmatch(r"[0-9a-f]{40}", revision), "full revision required")
    require(Path(git(source, "rev-parse", "--show-toplevel").decode().strip()).resolve() == source,
            "cache is not the requested repository: " + str(source))
    # Clone committed objects only. Cache working-tree changes are neither read
    # nor copied; in particular, do not scan an NTFS worktree with Linux Git.
    require(not destination.exists() or (destination.is_dir() and not any(destination.iterdir())),
            "destination is not empty: " + str(destination))
    git(source, "cat-file", "-e", revision + "^{commit}")
    command = ["git", "clone", "--quiet", "--no-hardlinks", "--no-checkout", str(source), str(destination)]
    subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    git(destination, "config", "core.autocrlf", "false")
    git(destination, "checkout", "--quiet", "--detach", revision)
    origin = git(source, "remote", "get-url", "origin").decode().strip()
    git(destination, "remote", "set-url", "origin", origin)
    require(git(destination, "rev-parse", "HEAD").decode().strip() == revision, "checkout revision mismatch")
    require(not git(destination, "status", "--porcelain=v1", "--untracked-files=no", "--ignore-submodules=all"),
            "new checkout is not clean")
    common = Path(git(destination, "rev-parse", "--absolute-git-dir").decode().strip())
    require(not (common / "objects/info/alternates").exists(), "external object alternates are not self-contained")
    records.append(dict(source=str(source), destination=str(destination), revision=revision,
                        origin=origin, command=command, generated_products_copied=False,
                        cache_worktree_used=False))


def recursive(cache, target, records, log):
    for name, revision in links(target):
        restore(cache / name, target / name, revision, records, log)
        recursive(cache / name, target / name, records, log)


def main(args):
    out = args.output.resolve()
    require(not out.exists(), "output already exists; preserve the prior attempt")
    require(not out.is_relative_to(args.source.resolve()) and not out.is_relative_to(args.hardware_cache.resolve()),
            "output must be outside source caches")
    out.mkdir(parents=True)
    records = []
    state = dict(contract="t17-clean-build-v1", status="PREPARING", started=now(),
                 executor=args.executor, revision=args.revision, repositories=records,
                 scope="new source trees and generated products; same host and installed tools")
    save(out / "prepare-state.json", state)
    try:
        with (out / "prepare.log").open("wb") as log:
            repo = out / "source"
            restore(args.source, repo, args.revision, records, log)
            recursive(args.hardware_cache.resolve(), repo, records, log)
            hardware_count = len(records) - 1
            env = out / "xs-env"
            env_revision = git(args.environment_cache, "rev-parse", "HEAD").decode().strip()
            restore(args.environment_cache, env, env_revision, records, log)
            expected = dict(links(env))
            for name in ("NEMU", "nexus-am", "DRAMsim3"):
                require(name in expected, "missing xs-env component " + name)
                restore(args.environment_cache / name, env / name, expected[name], records, log)
                recursive(args.environment_cache / name, env / name, records, log)
            for component in (repo, env / "NEMU", env / "nexus-am", env / "DRAMsim3"):
                for generated in ("build", "out"):
                    require(not (component / generated).exists(), "unexpected generated directory: " + str(component / generated))
        state.update(status="T17_CLEAN_SOURCE_PREPARED", hardware_submodules=hardware_count,
                     external_components=["NEMU", "nexus-am", "DRAMsim3"],
                     repository_count=len(records), toolchain_reinstalled=False,
                     build_executed=False, finished=now())
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc), finished=now())
        raise
    finally:
        save(out / "prepare-state.json", state)
    print(json.dumps({k: v for k, v in state.items() if k != "repositories"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--hardware-cache", type=Path, required=True)
    parser.add_argument("--environment-cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--executor", required=True)
    main(parser.parse_args())
