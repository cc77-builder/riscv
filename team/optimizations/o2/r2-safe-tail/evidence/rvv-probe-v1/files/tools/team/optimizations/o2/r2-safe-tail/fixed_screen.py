#!/usr/bin/env python3
"""Build/run the complete-layout S2 screen, preserving historical contracts."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import fixed_layout as layout
g, f, m = layout.g, layout.f, layout.m


def read_config(path, repo):
    cfg = m.read_json(path)
    expected = {"am_home", "cross_prefix", "hardware_source", "build_record",
                "build_driver", "canonical_build", "reference", "flash"}
    g.require(set(cfg) == expected, "fixed-screen configuration fields")
    for key, value in cfg.items():
        g.require(isinstance(value, str) and value.strip(), "invalid configuration value")
        if key != "cross_prefix":
            cfg[key] = str(Path(value.replace("$" + "{REPO}", str(repo))).expanduser().resolve())
    return cfg


def build_tools(repo, cfg):
    am = Path(cfg["am_home"])
    g.verify_sources(repo)
    f.pinned_modules(repo)
    g.require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=am, text=True).strip() == f.AM_COMMIT,
              "AM commit differs")
    g.require(not subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"],
                                          cwd=am, text=True).strip(), "tracked AM source modified")
    for rel in ("Makefile.app", "Makefile.compile", "Makefile.check", "am/arch/riscv64-xs.mk",
                "am/build/am-riscv64-xs.a", "libs/klib/build/klib-riscv64-xs.a"):
        g.require((am / rel).is_file(), "missing AM build input: " + rel)
    tools = {n: shutil.which(cfg["cross_prefix"] + n) for n in ("gcc", "ld", "ar", "objcopy", "objdump", "readelf")}
    tools["make"] = shutil.which("make")
    g.require(all(tools.values()), "GNU/AM build tool missing")
    return tools


def build(repo, cfg, out):
    out.mkdir(parents=True, exist_ok=False)
    state = dict(contract=layout.CONTRACT, status="BUILDING", started=f.now(), new_emu_runs=0)
    g.save(out / "state.json", state)
    try:
        tools = build_tools(repo, cfg)
        images = [layout.build_one(repo, cfg, out / "images" / f.image_name(item), item, tools)
                  for item in f.inventory()]
        pairs = layout.validate_controls(images, repo)
        g.save(out / "images.json", dict(images=images))
        g.save(out / "pair-layout.json", dict(contract=layout.LAYOUT_CONTRACT, pairs=pairs))
        state.update(status=layout.BUILD_PASS, canonical_elfs=len(images), pairs=len(pairs))
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc))
        raise
    finally:
        state["finished"] = f.now()
        g.save(out / "state.json", state)
    return state


def run(repo, cfg, out, action):
    repo, out = Path(repo).resolve(), Path(out).resolve()
    g.require(Path(__file__).resolve() == (repo / layout.ENTRY).resolve(), "entry outside declared repo")
    with layout.bindings(repo):
        if action == "build":
            return build(repo, cfg, out)
        return m.run(repo, cfg, out, action)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--action", choices=("build", "preflight", "run"), required=True)
    a = p.parse_args()
    try:
        print(json.dumps(run(a.repo, read_config(a.config, a.repo.resolve()), a.output, a.action)))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        p.exit(2, "R2_FIXED_SCREEN_STOPPED: " + str(exc) + "\n")
