"""Compile a bounded S1 first-dot initialization probe; start no simulator.

The frozen candidate remains byte-identical. A private in-memory renderer
substitutes only the explicitly checked body transformation below. This probe
has its own manifest/receipt identity and does not pass itself off as a v2
canonical build or qualify any runtime performance result.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

import candidate as c
import gate as g
import experiment as a

CONTRACT = "r2-s1-first-dot-initialization-probe-v1"
PARENT_SHA = "0270736b5c09e160626eb7b32d8e760faa193bf05761fea824a979108c3717b9"
GATE_SHA = "ab07b578f5fe2dc7782ef9af64e722e051363d1dfddfcd0f1939efb209346b6d"
EXPERIMENT_SHA = "75a26c36531b547ecb09c5ff19ecef1b338622779aedb2099f7775efd74cb7dd"


def first_dot(body, m, k, method, software):
    """Delete two group configurations and two instructions per output row."""
    original = list(body)
    if method == "rvv":
        return original
    g.require(method == "vdot" and (m, k) in ((4, 8), (8, 32), (16, 64), (4, 13)),
              "probe supports only the four existing dot8 shapes")
    g.require(software in ("basic", "reuse"), "probe software")
    group = 1 if software == "basic" else 4
    groups, chunks = m // group, k // 8
    positions = [i for i, line in enumerate(original) if line.startswith(".word ")]
    g.require(len(positions) == m * chunks, "original dot count")
    removed, replacements = set(), {}
    for ordinal, first in enumerate(range(0, m, group)):
        clear = ["vsetivli zero, 4, e32, m1, tu, mu"]
        clear += [f"vmv.v.i v{first + lane}, 0" for lane in range(group)]
        locations = [i for i in range(len(original) - len(clear) + 1)
                     if original[i:i + len(clear)] == clear]
        g.require(len(locations) == 1, "unique original group initialization")
        start = locations[0]
        removed.update(range(start, start + len(clear)))
        dots = positions[ordinal * group * chunks:ordinal * group * chunks + group]
        g.require(dots == list(range(dots[0], dots[0] + group)) and start + len(clear) < dots[0],
                  "first block instruction grouping")
        for lane, index in enumerate(dots):
            word = int(original[index].split()[1], 0)
            expected = 0x0200000b | (20 + lane) << 7 | (16 + lane) << 15 | 24 << 20
            g.require(word == expected, "first dot register assignment changed")
            replacements[index] = f".word 0x{((word & ~(31 << 7)) | ((first + lane) << 7)):08x}"
        add = ["vsetivli zero, 4, e32, m1, tu, mu"]
        add += [f"vadd.vv v{first + lane}, v{first + lane}, v{20 + lane}" for lane in range(group)]
        after = dots[-1] + 1
        g.require(original[after:after + len(add)] == add, "first block accumulation changed")
        removed.update(range(after, after + len(add)))
    g.require(len(removed) == 2 * m + 2 * groups and not (set(replacements) & removed),
              "unexpected transformation size")
    value = [replacements.get(i, line) for i, line in enumerate(original) if i not in removed]
    g.require(sum(line.startswith(".word ") for line in value) == m * chunks,
              "transformation changed dot count")
    return value


def generate(repo, output, variant, shard):
    g.require(variant in ("s1", "firstdot"), "probe variant")
    original_kernel = c.kernel
    def replacement(base, m, k, method, software, scope, selected):
        g.require(selected == "s1", "probe renderer selection")
        body = original_kernel(base, m, k, method, software, scope, selected)
        return body if variant == "s1" else first_dot(body, m, k, method, software)
    c.kernel = replacement
    try:
        manifest = c.generate(repo, output, "s1", 0, shard, "performance")
    finally:
        c.kernel = original_kernel
    # Keep the binary's frozen harness banner/data identical to canonical S1.
    # The manifest and build receipt explicitly identify this separate probe.
    manifest.update(contract=CONTRACT, probe_variant=variant, runtime_qualified=False,
                    binary_harness_contract=c.CONTRACT, parent_candidate_sha256=PARENT_SHA,
                    candidate_source_sha256=g.sha(Path(__file__)))
    for row in manifest["rows"]:
        row["probe_variant"] = variant
    g.save(output / "manifest.json", manifest)
    return manifest


def run(repo, config, output, canonical):
    repo, output, canonical = repo.resolve(), output.resolve(), canonical.resolve()
    g.require(not output.exists(), "new probe output required")
    for name, expected in (("candidate.py", PARENT_SHA), ("gate.py", GATE_SHA),
                           ("experiment.py", EXPERIMENT_SHA)):
        g.require(g.sha(repo / c.REL / name) == expected, "frozen S1 tool identity: " + name)
    g.require(Path(c.__file__).resolve() == repo / c.REL / "candidate.py" and
              Path(g.__file__).resolve() == repo / c.REL / "gate.py" and
              Path(a.__file__).resolve() == repo / c.REL / "experiment.py" and
              Path(__file__).resolve() == repo / c.REL / "first_dot_probe.py", "probe module roots")
    cfg, f = a.config(config, repo), a.legacy_f
    g.verify_sources(repo)
    tools = {key: shutil.which(cfg["cross_prefix"] + key) for key in
             ("gcc", "ld", "ar", "objcopy", "objdump", "readelf")}
    tools["make"] = shutil.which("make")
    g.require(all(tools.values()), "GNU tools missing")
    toolchain = {key: dict(path=p, sha256=g.sha(p)) for key, p in tools.items()}
    am = Path(cfg["am_home"])
    libraries = {str(am / name): g.sha(am / name) for name in
                 ("am/build/am-riscv64-xs.a", "libs/klib/build/klib-riscv64-xs.a")}
    env = dict(os.environ)
    for key in ("CFLAGS", "CPPFLAGS", "CXXFLAGS", "ASFLAGS", "LDFLAGS", "CC_OPT", "MAKEFLAGS", "MFLAGS",
                "CC", "AS", "LD", "OBJCOPY", "OBJDUMP", "ARCH", "MARCH", "LIBS", "PREBUILD"):
        env.pop(key, None)
    env.update(AM_HOME=str(am), LINUX_GNU_TOOLCHAIN="1")
    output.mkdir(parents=True)
    shutil.copyfile(Path(__file__), output / "probe-source.py")
    state = dict(contract=CONTRACT, status="BUILDING", started=f.now(), source_sha256=g.sha(Path(__file__)),
                 new_emu_runs=0, new_nemu_runs=0, runtime_qualified=False, performance_measured=False,
                 scope="real AM ELF, fixed-layout comparison, compiled finite model; not a runtime candidate")
    g.save(output / "state.json", state)
    pairs = []
    try:
        for shard in range(8):
            paths, manifests = [], []
            for variant in ("s1", "firstdot"):
                dest = output / f"s{shard:02}-{variant}"
                dest.mkdir()
                snapshot = dest / "source/repo"
                sources = sorted(set(g.PINNED) | {str(c.REL / n) for n in
                                 ("candidate.py", "gate.py", "experiment.py", "first_dot_probe.py")})
                for rel in sources:
                    target = snapshot / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(repo / rel, target)
                for name in ("main.c", "Makefile", "fixed-layout.ld"):
                    shutil.copyfile(snapshot / g.O3 / name, dest / "source" / name)
                manifest = generate(repo, dest / "data", variant, shard)
                record = dict(contract=CONTRACT, variant=variant, shard=shard, started=f.now(), commands=[],
                              toolchain=toolchain, external_files=libraries,
                              source_sha256={rel: g.sha(snapshot / rel) for rel in sources})
                argv = [tools["make"], "-C", str(dest / "source"), "ARCH=riscv64-xs", "MARCH=rv64gcv",
                        "CROSS_COMPILE=" + tools["gcc"][:-3], "T13_DATA=" + str(dest / "data"),
                        "T13_OBJ_ROOT=" + str(dest / "objects"), "BINARY=" + str(dest / "vdot-perf"),
                        "-o", "am", "-o", "klib", "-j1", "image"]
                record["commands"].append(f.command(argv, repo, dest / "make-command", env))
                argv = [tools["gcc"], "-march=rv64gcv", "-mabi=lp64d", "-mno-relax", "-c",
                        str(dest / "data/kernels.S"), "-o", str(dest / "kernels-reference.o")]
                record["commands"].append(f.command(argv, repo, dest / "reference-command", env))
                checked = g.original.inspect(dest / "vdot-perf.elf", dest / "vdot-perf.bin",
                                             dest / "kernels-reference.o", manifest, g.auditor(repo))
                elf = g.ELF((dest / "vdot-perf.elf").read_bytes())
                ref = g.ELF((dest / "kernels-reference.o").read_bytes())
                g.require(ref.named[".text"][5] == 32768 and
                          not any(s[1] in (4, 9) and s[5] for s in ref.sections), "probe reference layout")
                checked["finite_model"] = g.semantic_check(elf, manifest, repo)
                record.update(status="FIRST_DOT_PROBE_ELF_MODEL_PASS_NOT_RUNTIME", finished=f.now(),
                              artifacts={n: g.sha(dest / n) for n in
                                         ("vdot-perf.elf", "vdot-perf.bin", "kernels-reference.o", "data/manifest.json")})
                g.save(dest / "elf-validation.json", checked)
                g.save(dest / "build.json", record)
                paths.append(dest); manifests.append(manifest)
            elfs = [g.ELF((p / "vdot-perf.elf").read_bytes()) for p in paths]
            binaries = [(p / "vdot-perf.bin").read_bytes() for p in paths]
            layout = g.paired_layout(*elfs, *binaries)
            g.require(all(binaries[0][8192 * (i + 1):8192 * (i + 2)] ==
                          binaries[1][8192 * (i + 1):8192 * (i + 2)] for i in (1, 3)),
                      "probe changed RVV slots")
            baseline = canonical / "images" / f"performance-s1-d0-s{shard:02}"
            g.require(binaries[0] == (baseline / "vdot-perf.bin").read_bytes() and
                      (paths[0] / "data/cases.h").read_bytes() == (paths[1] / "data/cases.h").read_bytes(),
                      "probe baseline or paired mathematical/ABI bytes changed")
            decoder = g.auditor(repo)
            counts = []
            for index, (before, after) in enumerate(zip(*(m["rows"] for m in manifests))):
                m, k = before["m"], before["k"]
                expected = 0 if before["method"] == "rvv" else 2 * m + 2 * (m if before["software"] == "basic" else m // 4)
                sizes = [len(g.body_bytes(e.symbol_data(f"t13_kernel_{index}"), decoder)) // 4 for e in elfs]
                g.require(sizes == [len(before["body"]), len(after["body"])] and sizes[0] - sizes[1] == expected,
                          "actual compiled instruction difference")
                counts.append(dict(method=before["method"], software=before["software"], instructions=sizes,
                                   removed=expected))
            pairs.append(dict(shard=shard, shape=[manifests[0]["m"], manifests[0]["k"]],
                              scope=manifests[0]["scope"], **layout, instructions=counts,
                              rvv_slots_identical=True, canonical_s1_bin_identical=True,
                              canonical_s1_bin_sha256=g.sha(baseline / "vdot-perf.bin")))
        for name, digest in libraries.items():
            g.require(g.sha(name) == digest, "protected AM library changed")
        g.verify_sources(repo)
        state.update(status="FIRST_DOT_16_AM_ELFS_MODEL_AND_PAIR_LAYOUT_PASS_NOT_RUNTIME", pairs=pairs,
                     canonical_pairs=8, compiled_kernel_bodies=64, finite_model_trials_per_body=9)
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc))
        raise
    finally:
        state["finished"] = f.now()
        g.save(output / "state.json", state)
    return state


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--canonical", type=Path, required=True)
    args = parser.parse_args()
    value = run(args.repo, args.config, args.output, args.canonical)
    print(json.dumps({k: v for k, v in value.items() if k != "pairs"}, indent=2))
