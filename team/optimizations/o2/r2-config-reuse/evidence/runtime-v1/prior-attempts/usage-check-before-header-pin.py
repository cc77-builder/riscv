"""Compile the published C example and rebuild the exact public GNU object."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import c_api as c
import library

g, a = c.g, c.a


def check(repo, identity, build, lib, output):
    packaged = library.byte_check(lib)
    g.require(packaged["object_sha256"] == g.sha(build / "gemv-reference.o"),
              "usage input differs from C build object")
    source = repo / c.PUBLIC
    readme = repo / g.S3 / "RUNTIME_README.md"
    fence = chr(96) * 3
    blocks = re.findall(fence + "c\n(.*?)\n" + fence, readme.read_text(), re.S)
    examples = [text for text in blocks if "void gemv8(" in text]
    g.require(len(examples) == 1, "one complete documented C example required")
    tools = a.read(build / "build.json")["toolchain"]
    for tool in tools.values():
        g.require(g.sha(tool["path"]) == tool["sha256"], "usage toolchain changed")
    output.mkdir(parents=True, exist_ok=False)
    (output / "app.c").write_text(examples[0] + "\n")
    compiler, linker = tools["gcc"]["path"], tools["ld"]["path"]
    flags = ["-march=rv64gcv", "-mabi=lp64d", "-mno-relax"]
    command = c.adapter(repo, identity).a.frozen_f.command
    commands = [
        command([compiler, *flags, "-c", str(source / "gemv.S"), "-o", str(output / "rebuilt-gemv.o")],
                repo, output / "source-rebuild"),
        command([compiler, "-std=c11", *flags, "-ffreestanding", "-O2", "-I" + str(source),
                 "-c", str(output / "app.c"), "-o", str(output / "app.o")], repo, output / "example-compile"),
        command([linker, "-r", "--no-relax", str(output / "app.o"), str(lib / "libconfig_reuse_gemv.a"),
                 "-o", str(output / "app-config-reuse.o")], repo, output / "example-link"),
    ]
    g.require((output / "rebuilt-gemv.o").read_bytes() == (lib / "gemv.o").read_bytes(),
              "public source does not rebuild the qualified whole object")
    linked = g.ELF((output / "app-config-reuse.o").read_bytes())
    original = g.ELF((lib / "gemv.o").read_bytes())
    names = a.read(lib / "library.json")["public_symbols"]
    undefined = [name for name, value in linked.symbols.items() if name and value[2] == 0]
    g.require(not undefined and linked.symbols["gemv8"][1] > 0, "documented consumer did not link completely")
    g.require(all(linked.symbol_data(name) == original.symbol_data(name) for name in names),
              "documented consumer changed library leaves")
    result = dict(status="S3_README_EXAMPLE_COMPILE_LINK_AND_SOURCE_REBUILD_PASS", contract=c.CONTRACT,
        source_sha256=g.sha(Path(__file__)), readme_sha256=g.sha(readme),
        example_source_sha256=g.sha(output / "app.c"), qualified_object_sha256=g.sha(output / "rebuilt-gemv.o"),
        public_functions=len(names), linked_leaves_identical=True, undefined_symbols=undefined,
        commands=commands, new_emu_runs=0, example_executed=False, performance_measured=False,
        stable_default_changed=False,
        artifacts={p.relative_to(output).as_posix(): g.sha(p) for p in sorted(output.rglob("*")) if p.is_file()})
    g.save(output / "report.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "identity", "build", "library", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    repo, identity_path, build, lib, output = [getattr(args, name).resolve()
        for name in ("repo", "identity", "build", "library", "output")]
    g.require(repo == a.ROOT and not output.exists(), "selected source and new usage output required")
    identity = a.parent_identity(repo, identity_path)
    cfg = identity["configuration"]
    a.outside_inputs(output, [repo, identity_path.parent, build, lib,
                             cfg["hardware_source"], cfg["build_record"], cfg["am_home"]])
    result = check(repo, identity, build, lib, output)
    print(json.dumps({k: v for k, v in result.items() if k not in ("commands", "artifacts")}, indent=2))


if __name__ == "__main__":
    main()
