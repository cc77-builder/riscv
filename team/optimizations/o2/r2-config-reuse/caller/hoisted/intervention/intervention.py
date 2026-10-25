"""One fixed-image, fixed-target predecessor intervention over team-owned tools.

Run one action per Python process. The adapter changes private module bindings,
never the frozen source files, official programs or historical decision rules.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import struct
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import screen

e, g = screen.e, screen.g
REL = e.REL / "hoisted/intervention"
CONTRACT = "r2-s3-predecessor-intervention-v1"
ORDER = (0, 1, 1, 0) + (0, 1, 1, 0, 1, 0, 0, 1) * 2
LEAF = "config_reuse_gemv_8x32_reuse_vdot"
PREDECESSORS = screen.RVV[:2]
OWN = ("intervention.py", "audit.py", "main.c", "CONTRACT.md", "checks.py")
EXTRA_INPUTS = tuple(name for name in screen.INPUTS if str(screen.S0) in name)
ORIGINAL_PATH = e.pathcheck.path
ORIGINAL_GENERATE, ORIGINAL_SOURCES, ORIGINAL_VERIFY = e.generate, e.sources, e.verification


def plan():
    return [dict(index=(arm + 1 if role == 0 else 0), stage=0, dataset=0,
                 repeat=trial, phase="warmup" if trial < 4 else "measured",
                 trial=trial, arm=arm, role="predecessor" if role == 0 else "target")
            for trial, arm in enumerate(ORDER) for role in (0, 1)]


class BoundElf:
    def __init__(self, elf, symbol):
        self.original, self.target = elf, symbol
        self.symbols = dict(elf.symbols)
        self.symbols[screen.RVV[4][0]] = self.symbols[symbol]

    def symbol_data(self, name):
        return self.original.symbol_data(self.target if name == screen.RVV[4][0] else name)


def path(elf, stage, method, packed):
    g.require(stage == 0 and method in ("vdot", "rvv0", "rvv1"), "intervention path scope")
    if method == "vdot":
        return ORIGINAL_PATH(elf, 0, method, packed)
    return ORIGINAL_PATH(BoundElf(elf, PREDECESSORS[int(method[-1])][0]), 0, "rvv", packed)


def sources(repo):
    found = ORIGINAL_SOURCES(repo)
    for name, pin in screen.h.BASE_PINS.items():
        g.require(g.sha(e.HERE / name) == pin, "frozen caller source: " + name)
    for name, pin in screen.DRAFTS.items():
        g.require(g.sha(HERE.parent / name) == pin, "frozen hoisted source: " + name)
    g.require(g.sha(e.HERE / "evidence.py") == screen.h.AUX_PINS["evidence.py"],
              "frozen complete evidence auditor")
    for name in EXTRA_INPUTS:
        g.require(e.digest(screen.raw(repo, name)) == screen.INPUTS[name], "qualified S0 input: " + name)
    additional = [str(REL / name) for name in OWN]
    additional += [str(e.REL / "hoisted" / name) for name in
                   ("screen.py", "candidate.py", "caller.c", "CONTRACT.md", "context_prefix.py")]
    additional += list(EXTRA_INPUTS)
    additional += [str(e.REL / "evidence.py")]
    found.update({name: g.sha(repo / name) for name in additional})
    return found


def generate(repo, out):
    manifest = ORIGINAL_GENERATE(repo, out)
    shutil.copyfile(HERE.parent / "caller.c", out / "caller.c")
    shutil.copyfile(HERE / "main.c", out / "main.c")
    assembly = ".option norvc\n.option norelax\n.text\n"
    s0 = screen.raw(repo, str(screen.S0 / "data/gemv.S.gz")).decode()
    assembly += "".join(screen.function(s0, name) for name, _, _ in PREDECESSORS)
    (out / "strong.S").write_text(assembly)
    makefile = (out / "Makefile").read_text()
    (out / "Makefile").write_text(screen.replace_once(
        makefile, "timers.S gemv.S\n", "timers.S gemv.S strong.S\n"))
    header = screen.replace_once((out / "data.h").read_text(),
                                 "#define CALLER_WINDOWS 144", "#define CALLER_WINDOWS 40")
    header += "#define CONTEXT_TRIALS 20\n"
    for name, _, _ in PREDECESSORS:
        header += "extern void " + name + "(const int8_t *, void *);\n"
    header += "const volatile unsigned context_order[20] __attribute__((used,aligned(8))) = {"
    header += ",".join(map(str, ORDER)) + "};\n"
    header += "caller_leaf const context_predecessors[2] __attribute__((used,aligned(8))) = {"
    header += ",".join(name for name, _, _ in PREDECESSORS) + "};\n"
    header += "caller_leaf const volatile context_target[1] __attribute__((used,aligned(8))) = {" + LEAF + "};\n"
    (out / "data.h").write_text(header)
    rows = [dict(id=0, stage=0, scope="full", scenario="fixed-target", method="vdot", n=1, dots=32, leaf=LEAF)]
    rows += [dict(id=i + 1, stage=0, scope="full", scenario="predecessor-" + str(i),
                  method="rvv" + str(i), n=1, dots=0, leaf=name)
             for i, (name, _, _) in enumerate(PREDECESSORS)]
    manifest.update(rows=rows, plan=plan(), expected_dots=640, ordinary_stack_demo_calls=0,
                    contract=CONTRACT, datasets=[0], stored_datasets=[0, 1, 2],
                    trial_order=list(ORDER), formal_trials=16, warmup_trials=4,
                    caller_variant="frozen-hoisted", caller_sha256=g.sha(HERE.parent / "caller.c"),
                    scope="one fixed target, two predecessor implementations; no kernel selection",
                    uart_format="CW seq cycles instructions verdict; all output deferred",
                    diagnostic_sum_is_endtoend=False, stable_default_changed=False, hardware_changed=False)
    g.save(out / "manifest.json", manifest)
    return manifest


def verification(repo, build):
    result = ORIGINAL_VERIFY(repo, build)
    elf = g.ELF((build / "vdot-perf.elf").read_bytes())
    g.require(elf.symbol_data("context_order") == struct.pack("<20I", *ORDER), "compiled intervention order")
    wanted = tuple(elf.symbols[name][0] for name, _, _ in PREDECESSORS)
    g.require(elf.symbol_data("context_predecessors") == struct.pack("<2Q", *wanted), "compiled predecessor table")
    g.require(elf.symbol_data("context_target") == struct.pack("<Q", elf.symbols[LEAF][0]), "compiled fixed target")
    reference = g.ELF(screen.raw(repo, str(screen.S0 / "gemv-reference.o.gz")))
    for name, size, sha in PREDECESSORS:
        raw = elf.symbol_data(name)
        g.require(len(raw) == size and e.digest(raw) == sha and raw == reference.symbol_data(name),
                  "changed qualified predecessor: " + name)
    symbols = ("caller_full", "caller_measure_0", LEAF) + tuple(name for name, _, _ in PREDECESSORS)
    result.update(contract=CONTRACT, windows=40, formal_target_windows=16,
                  formal_predecessor_windows=16, predecessor_leaves=2,
                  symbols={name: dict(address=elf.symbols[name][0], bytes=len(elf.symbol_data(name)),
                                     sha256=e.digest(elf.symbol_data(name))) for name in symbols},
                  target_fixed=True, selection_performed=False)
    return result


def install():
    g.require(e.CONTRACT == "r2-s3-caller-8x32-v2" and HERE == e.ROOT / REL,
              "intervention/base source binding")
    old_load = g.load
    auditor = old_load("predecessor_intervention_audit", HERE / "audit.py")

    def load(name, filename):
        module = old_load(name, filename)
        if Path(filename).resolve() == e.HERE / "check.py":
            # Preserve the base module identity expected by the run engine;
            # the new-contract normal validator is explicitly source-bound.
            module.normal = lambda repo, build, run, receipt: auditor.normal(e, repo, build, run, receipt)
        return module

    e.CONTRACT, e.sources, e.generate, e.verification = CONTRACT, sources, generate, verification
    e.pathcheck.path, g.load = path, load
    e.GENERATED += ("strong.S",)
    return auditor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--identity", type=Path)
    parser.add_argument("--action", choices=("build", "run", "verify-build", "audit", "checks", "pack", "audit-archive"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--build", type=Path)
    parser.add_argument("--run", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--operation-id")
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.output.resolve()
    g.require(repo == e.ROOT and not out.exists(), "selected source and fresh output required")
    identity = (args.identity or repo / e.parent.REPRO /
                "evidence/clean-reproduction-v1/reports/identity-02.json").resolve()
    cfg = e.parent.parent_identity(repo, identity)["configuration"]
    protected = [repo, identity.parent] + [cfg[k] for k in ("am_home", "hardware_source", "build_record")]
    protected += [p.resolve() for p in (args.build, args.run, args.archive) if p]
    e.parent.outside_inputs(out, protected)
    if os.name == "posix":
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    auditor = install()
    if args.action == "build":
        result = e.build(repo, identity, out)
    elif args.action == "run":
        g.require(args.build and args.operation_id, "run needs build and operation ID")
        result = e.run(repo, identity, args.build.resolve(), out, args.operation_id)
    elif args.action == "verify-build":
        g.require(args.build, "verify needs build")
        result = verification(repo, args.build.resolve())
        g.save(out, result)
    elif args.action == "checks":
        checker = g.load("predecessor_intervention_checks", HERE / "checks.py")
        result = checker.run(e, auditor, args.build.resolve() if args.build else None,
                             args.run.resolve() if args.run else None)
        g.save(out, result)
    elif args.action == "audit":
        g.require(args.build and args.run, "audit needs build and run")
        result = auditor.audit(e, repo, args.build.resolve(), args.run.resolve())
        g.save(out, result)
    else:
        archive = g.load("intervention_archive_actions", e.HERE / "evidence.py")
        archive.audit = lambda build, run: auditor.audit(e, repo, build, run)
        if args.action == "pack":
            g.require(args.build and args.run, "pack needs build and run")
            result = archive.pack(args.build.resolve(), args.run.resolve(), out)
        else:
            g.require(args.archive, "audit-archive needs archive")
            result = archive.audit_archive(args.archive.resolve())
            result["status"] = "INTERVENTION_ARCHIVE_RAW_AUDIT_PASS"
            g.save(out, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
