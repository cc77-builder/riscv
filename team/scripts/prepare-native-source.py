#!/usr/bin/env python3
"""Prepare a pinned, self-contained Git store and isolated source checkouts.

Only committed superproject objects are transferred. Submodule repositories,
untracked inputs, tools and hardware results remain separate contracts. Existing
outputs are never resumed, rewritten or removed by this tool.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


FORMAT = "native-source-store-v1"
PIN = "refs/heads/pinned-source"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def environment(threads):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_SYSTEM=os.devnull, GIT_NO_REPLACE_OBJECTS="1",
               GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0",
               GIT_CONFIG_COUNT="3", GIT_CONFIG_KEY_0="pack.threads",
               GIT_CONFIG_VALUE_0=str(threads), GIT_CONFIG_KEY_1="gc.auto",
               GIT_CONFIG_VALUE_1="0", GIT_CONFIG_KEY_2="maintenance.auto",
               GIT_CONFIG_VALUE_2="false", LC_ALL="C")
    return env


class Git:
    def __init__(self, output, threads):
        self.output, self.env, self.records = output, environment(threads), []

    def __call__(self, *args, repo=None, ok=(0,)):
        command = ["git"] + (["-C", str(repo)] if repo else []) + [str(a) for a in args]
        started = now()
        result = subprocess.run(command, capture_output=True, env=self.env)
        self.records.append(dict(command=command, started=started, finished=now(),
                                 exit_code=result.returncode,
                                 stdout=result.stdout.decode("utf-8", errors="replace"),
                                 stderr=result.stderr.decode("utf-8", errors="replace")))
        if self.output is not None:
            save(self.output / "commands.json", self.records)
        require(result.returncode in ok,
                "Git failed (see commands.json): " + " ".join(command))
        return result.stdout.decode("utf-8").strip()


def git_directory(git, repo):
    return Path(git("rev-parse", "--absolute-git-dir", repo=repo)).resolve()


def complete_repository(git, repo, *, allow_alternates=False):
    directory = git_directory(git, repo)
    common = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir", repo=repo)).resolve()
    require(directory == common, "linked worktrees are not supported as source stores")
    require(git("rev-parse", "--is-shallow-repository", repo=repo) == "false", "shallow input")
    require(not (common / "shallow").exists(), "shallow metadata")
    require(not (common / "info/grafts").exists(), "grafted history")
    require(not git("for-each-ref", "--format=%(refname)", "refs/replace/", repo=repo), "replacement refs")
    config = git("config", "--local", "--get-regexp", r"^(extensions\.partialclone|remote\..*\.promisor)$",
                 repo=repo, ok=(0, 1))
    require(not config, "partial/promisor input")
    objects = common / "objects"
    require(not objects.is_symlink(), "symlinked object directory")
    require(not list((objects / "pack").glob("*.promisor")), "promisor pack")
    require(not (objects / "info/http-alternates").exists(), "HTTP object dependency")
    if not allow_alternates:
        for name in ("alternates", "http-alternates"):
            require(not (objects / "info" / name).exists(), "external object dependency: " + name)
    return common


def object_manifest(directory):
    result = {}
    for path in sorted((directory / "objects").rglob("*")):
        require(not path.is_symlink(), "object store contains a symlink")
        if path.is_file():
            require(path.stat().st_nlink == 1, "object store contains a hardlinked file")
            result[path.relative_to(directory).as_posix()] = dict(bytes=path.stat().st_size, sha256=digest(path))
    require(result, "empty object store")
    return result


def prepare_store(args, git, state):
    source, output = args.source.resolve(), args.output.resolve()
    require(re.fullmatch(r"[0-9a-f]{40}", args.revision), "full lowercase SHA-1 revision required")
    repo = output / "repository.git"
    bundle_sha = digest(source) if source.is_file() else None
    if source.is_dir():
        complete_repository(git, source, allow_alternates=True)
        require(git("rev-parse", "--verify", args.revision + "^{commit}", repo=source) == args.revision,
                "source revision is not the requested commit")
    else:
        require(source.is_file(), "source must be an existing local repository or bundle")
    git("init", "--bare", "--template=", "--object-format=sha1", str(repo))
    if source.is_file():
        # Verification in this empty repository rejects incremental bundles.
        git("bundle", "verify", str(source), repo=repo)
        heads = git("bundle", "list-heads", str(source), repo=repo).splitlines()
        require(any(line.split()[0] == args.revision for line in heads), "bundle does not advertise revision")
    git("fetch", "--no-tags", "--no-auto-gc", "--no-write-fetch-head", str(source),
        args.revision + ":" + PIN, repo=repo)
    git("symbolic-ref", "HEAD", PIN, repo=repo)
    git("config", "gc.auto", "0", repo=repo)
    git("config", "maintenance.auto", "false", repo=repo)
    common = complete_repository(git, repo)
    require(git("rev-parse", "HEAD", repo=repo) == args.revision, "store revision mismatch")
    git("fsck", "--full", "--no-reflogs", repo=repo)
    require(not source.is_file() or digest(source) == bundle_sha, "source bundle changed during import")
    manifest = dict(format=FORMAT, revision=args.revision, pin=PIN,
                    tree=git("rev-parse", "HEAD^{tree}", repo=repo),
                    git_version=git("--version"), source=str(source), created=now(),
                    source_bundle_sha256=bundle_sha,
                    objects=object_manifest(common),
                    scope="complete reachable superproject history; no submodule repositories or untracked inputs")
    save(output / "manifest.json", manifest)
    state.update(status="NATIVE_STORE_PASS", revision=args.revision, tree=manifest["tree"],
                 object_files=len(manifest["objects"]), self_contained=True,
                 manifest_sha256=digest(output / "manifest.json"))


def validate_store(root, git):
    state = json.loads((root / "state.json").read_text(encoding="utf-8"))
    require(state.get("status") == "NATIVE_STORE_PASS", "store creation did not finish")
    require(state.get("manifest_sha256") == digest(root / "manifest.json"), "sealed manifest changed")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    require(manifest.get("format") == FORMAT and manifest.get("pin") == PIN, "unrecognized source store")
    require(re.fullmatch(r"[0-9a-f]{40}", manifest["revision"]), "invalid pinned revision")
    repo = root / "repository.git"
    require(not repo.is_symlink(), "store repository is a symlink")
    common = complete_repository(git, repo)
    require(git("rev-parse", "--is-bare-repository", repo=repo) == "true", "store is not bare")
    require(git("rev-parse", "--verify", PIN + "^{commit}", repo=repo) == manifest["revision"], "pin moved")
    require(git("rev-parse", "HEAD", repo=repo) == manifest["revision"], "store HEAD moved")
    require(git("rev-parse", PIN + "^{tree}", repo=repo) == manifest["tree"], "tree changed")
    require(object_manifest(common) == manifest["objects"], "store object bytes changed")
    require(state.get("revision") == manifest["revision"] and state.get("tree") == manifest["tree"],
            "store state identity differs")
    return repo, manifest


def prepare_checkout(args, git, state):
    store, output = args.store.resolve(), args.output.resolve()
    source, manifest = validate_store(store, git)
    repo = output / "source"
    mode = "--shared" if args.mode == "shared" else "--no-local"
    git("clone", "--quiet", "--template=", "--no-checkout", "--no-tags", mode, str(source), str(repo))
    # A store is a fixed object donor, never the default publishing destination.
    git("remote", "remove", "origin", repo=repo)
    git("config", "core.autocrlf", "false", repo=repo)
    git("config", "core.eol", "lf", repo=repo)
    git("config", "gc.auto", "0", repo=repo)
    git("config", "maintenance.auto", "false", repo=repo)
    git("checkout", "--quiet", "--detach", manifest["revision"], repo=repo)
    common = complete_repository(git, repo, allow_alternates=args.mode == "shared")
    require(common == repo / ".git", "checkout must have its own gitdir and index")
    require(git("rev-parse", "HEAD", repo=repo) == manifest["revision"], "checkout revision mismatch")
    require(git("rev-parse", "HEAD^{tree}", repo=repo) == manifest["tree"], "checkout tree mismatch")
    require(not git("status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=all", repo=repo),
            "new checkout is not clean")
    if args.mode == "shared":
        actual = (common / "objects/info/alternates").read_text(encoding="utf-8").splitlines()
        require(len(actual) == 1 and Path(actual[0]).resolve() == (source / "objects").resolve(),
                "checkout must depend directly on exactly this store")
        require(not (common / "objects/info/http-alternates").exists(), "HTTP alternate")
    else:
        object_manifest(common)
    git("fsck", "--full", "--no-reflogs", repo=repo)
    state.update(status="NATIVE_CHECKOUT_PASS", revision=manifest["revision"], tree=manifest["tree"],
                 mode=args.mode, self_contained=args.mode == "independent", store=str(store),
                 store_manifest_sha256=digest(store / "manifest.json"),
                 gitdir=str(common), index=str(common / "index"), source=str(repo),
                 submodules_initialized=False, tools_or_hardware_validated=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    store = sub.add_parser("store", help="seal a new self-contained bare store from local committed objects")
    store.add_argument("--source", type=Path, required=True)
    store.add_argument("--revision", required=True)
    checkout = sub.add_parser("checkout", help="create a new repository with an independent index")
    checkout.add_argument("--store", type=Path, required=True)
    checkout.add_argument("--mode", choices=("shared", "independent"), required=True)
    for command in (store, checkout):
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--threads", type=int, choices=range(1, 5), default=2)
    args = parser.parse_args()
    out = args.output.resolve()
    source = (args.source if args.action == "store" else args.store).resolve()
    require(not args.output.is_symlink() and not out.exists(), "output already exists; preserve the prior attempt")
    require(source.exists() and not out.is_relative_to(source), "output must be outside an existing input")
    git = Git(None, args.threads)
    if args.action == "store" and source.is_dir():
        common = complete_repository(git, source, allow_alternates=True)
        if git("rev-parse", "--is-bare-repository", repo=source) == "true":
            require(source == common, "bare source must be its repository root")
        else:
            require(Path(git("rev-parse", "--show-toplevel", repo=source)).resolve() == source,
                    "source must be the working tree root, not a subdirectory or .git")
        roots = [common]
        for line in git("count-objects", "-v", repo=source).splitlines():
            if line.startswith("alternate: "):
                name = line[len("alternate: "):]
                require(not name.startswith('"'), "quoted alternate paths are unsupported")
                parent = Path(name).resolve().parent
                roots.append(parent.parent if parent.name == ".git" else parent)
        require(all(not out.is_relative_to(root) for root in roots), "output is inside an input object donor")
    if hasattr(os, "sched_getaffinity"):
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:args.threads])
    out.mkdir(parents=True)
    state = dict(format=FORMAT, action=args.action, started=now(), status="PREPARING", threads=args.threads)
    save(out / "state.json", state)
    git.output = out
    save(out / "commands.json", git.records)
    try:
        (prepare_store if args.action == "store" else prepare_checkout)(args, git, state)
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc))
        raise
    finally:
        state["finished"] = now()
        save(out / "state.json", state)
    print(json.dumps(state, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
