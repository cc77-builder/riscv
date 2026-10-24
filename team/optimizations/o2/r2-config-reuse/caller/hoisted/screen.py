"""Full-call-only, fixed-layout screening over the frozen caller engine.

Original caller/hoisted drafts and all qualified leaves remain immutable.
This adapter selects one of five byte-distinct RVV leaves from ELF data,
retains the actual path/counter/DiffTest checks, and narrows the manifest to
36 full windows. Run each action in a fresh Python process.
"""
import argparse
import gzip
from pathlib import Path
import re
import struct
import sys

import candidate as h

e, g = h.e, h.g
HERE = Path(__file__).resolve().parent
S0 = Path("team/optimizations/o2/r2-select/evidence/entry-v1/files/builds/build-probe-01/images/performance-s0-d0-s03")
FIRST = Path("team/optimizations/o2/r2-vector-accum")
INPUTS = {
    str(S0 / "data/gemv.S.gz"): "dce2a2e16e2051c140c82c661cfd392d9a1a32941e043b75821aaf3436d554c3",
    str(S0 / "gemv-reference.o.gz"): "2a034f57cce082566bccf0d7f07d0950370af8a59b1f186bcaeefb95908e16a5",
    str(FIRST / "firstdot/public/gemv.S"): "1e1aa8ca665559efa6acab2648f4614c6121422aaf400d78c192e6accad5da47",
    str(FIRST / "evidence/firstdot-v1/library/member-extract/stdout.log"): "b65d4ca4faf3550ad2e95d3fb7d1d452923b71ae50776420bfcd679d098238af",
}
RVV = (
    ("r4_gemv_8x32_basic_rvv", 1060, "6f7c75562128eecc42c54ef840d0a6d04bd9446a4703e595ee61ffa432b5ecbe"),
    ("r4_gemv_8x32_reuse_rvv", 740, "20ee57db9abe4bf501608dc6680ff9ccc39c7ccd5fcadb637026da20edc2afc4"),
    ("config_reuse_gemv_8x32_basic_rvv", 676, "c33e1fb01a939cf68d4a867a5daf6b5fe4dc7bf9536d644808949ef555052def"),
    ("firstdot_gemv_8x32_reuse_rvv", 452, "f304ee128fbac736755d1fe7d03b6d8e8f6ea30e625dc1937f379445e6c23137"),
    ("config_reuse_gemv_8x32_reuse_rvv", 448, "ea86a50cd67113246dae98ef7ce8db4e0d1383f453d889c6aad6cf2579857513"),
)
DRAFTS = {
    "candidate.py": "138984fbf70c7ed6d504c8199ee7dc75be418757b328c3b9097cd876cd1f39ec",
    "caller.c": "141d1789e5cf8e55ba5463e1ed246868bc94bdeee3daf9006f6f0e134fb6e75b",
    "CONTRACT.md": "1b4efd5b5430b25251afb892eeb727db70dda115199ef683a0e732a9e9ad3ab6",
}


def raw(repo, name):
    value = (repo / name).read_bytes()
    return gzip.decompress(value) if name.endswith(".gz") else value


def replace_once(text, before, after):
    g.require(text.count(before) == 1, "screen source substitution is not unique")
    return text.replace(before, after)


def function(text, symbol):
    found = re.findall(r"(?m)^\.global " + re.escape(symbol) +
                       r"\n.*?^\.size " + re.escape(symbol) + r",[^\n]*\n", text, re.S | re.M)
    g.require(len(found) == 1, "screen qualified assembly function missing/duplicate")
    return ".balign 16\n" + found[0]


def selected(elf, choice):
    index = elf.symbol_data("hoisted_rvv_choice")
    g.require(len(index) == 4 and int.from_bytes(index, "little") == choice, "screen selector identity")
    pointers = elf.symbol_data("hoisted_rvv_entries")
    wanted = tuple(elf.symbols[name][0] for name, _, _ in RVV)
    g.require(len(pointers) == 40 and struct.unpack("<5Q", pointers) == wanted, "screen complete RVV table")
    return RVV[choice][0]


def configure(caller, choice):
    g.require(caller in ("baseline", "hoisted") and choice in range(5), "screen selection")
    g.require(caller == "hoisted" or choice == 4, "screen baseline only uses qualified reuse pair")
    for name, pin in DRAFTS.items():
        g.require(g.sha(HERE / name) == pin, "frozen hoisted draft changed")
    for name, pin in INPUTS.items():
        g.require(e.digest(raw(e.ROOT, name)) == pin, "screen qualified input changed: " + name)
    h.CONTRACT = "r2-s3-caller-screen-v2-" + ("b" if caller == "baseline" else "h") + str(choice)
    h.OWN += ("screen.py", "SCREEN_CONTRACT.md")
    original_install = h.install

    def install():
        original_install()
        old_sources, old_generate = e.sources, e.generate
        old_verify, old_path, old_load = e.verification, e.pathcheck.path, g.load
        original_phases = e.PHASES
        e.PHASES = ("full",)
        e.GENERATED += ("strong.S",)

        def sources(repo):
            result = old_sources(repo)
            result.update({name: g.sha(repo / name) for name in INPUTS})
            return result

        def generate(repo, out):
            # Keep all four original timer definitions; only the full timer
            # executes. This avoids changing the frozen timer generator.
            e.PHASES = original_phases
            try:
                manifest = old_generate(repo, out)
            finally:
                e.PHASES = ("full",)
            if caller == "baseline":
                (out / "caller.c").write_bytes((e.HERE / "caller.c").read_bytes())
            s0 = raw(repo, str(S0 / "data/gemv.S.gz")).decode()
            first = raw(repo, str(FIRST / "firstdot/public/gemv.S")).decode()
            assembly = ".option norvc\n.option norelax\n.text\n"
            assembly += function(s0, RVV[0][0]) + function(s0, RVV[1][0]) + function(first, RVV[3][0])
            (out / "strong.S").write_text(assembly)
            makefile = (out / "Makefile").read_text()
            (out / "Makefile").write_text(replace_once(makefile, "timers.S gemv.S\n", "timers.S gemv.S strong.S\n"))
            header = replace_once((out / "data.h").read_text(), "#define CALLER_WINDOWS 144", "#define CALLER_WINDOWS 36")
            for name, _, _ in RVV:
                header += "extern void " + name + "(const int8_t *, void *);\n"
            header += "const volatile unsigned hoisted_rvv_choice __attribute__((used)) = " + str(choice) + ";\n"
            header += "caller_leaf const hoisted_rvv_entries[5] __attribute__((used,aligned(8))) = {\n"
            header += ",\n".join(name for name, _, _ in RVV) + "\n};\n"
            (out / "data.h").write_text(header)
            main = replace_once((out / "main.c").read_text(), "stage<4", "stage<1")
            main = replace_once(main, "method ? config_reuse_gemv_8x32_reuse_rvv :", "method ? hoisted_rvv_entries[hoisted_rvv_choice] :")
            (out / "main.c").write_text(main)
            manifest["rows"] = [row for row in manifest["rows"] if row["stage"] == 0]
            manifest["rows"][1]["leaf"] = RVV[choice][0]
            manifest["plan"] = [step for step in manifest["plan"] if step["stage"] == 0]
            manifest.update(expected_dots=672, caller_variant=caller, selected_rvv=choice,
                            rvv_candidates=[dict(symbol=n, bytes=size, sha256=pin) for n, size, pin in RVV],
                            candidate_caller_sha256=g.sha(out / "caller.c"),
                            screening_scope="full only, 3 datasets, 36 windows, 24 measured; no diagnostic sum",
                            context_disjoint_from_write_regions=True, pointer_capture_inside_full=True)
            g.save(out / "manifest.json", manifest)
            return manifest

        class BoundElf:
            def __init__(self, elf, symbol):
                self.original, self.target = elf, symbol
                self.symbols = dict(elf.symbols)
                self.symbols[RVV[4][0]] = self.symbols[symbol]

            def symbol_data(self, name):
                return self.original.symbol_data(self.target if name == RVV[4][0] else name)

        def path(elf, stage, method, packed):
            symbol = selected(elf, choice)
            bound = BoundElf(elf, symbol) if method == "rvv" else elf
            return old_path(bound, stage, method, packed)

        def verification(repo, build):
            result = old_verify(repo, build)
            elf = g.ELF((build / "vdot-perf.elf").read_bytes())
            selected(elf, choice)
            references = (
                g.ELF(raw(repo, str(S0 / "gemv-reference.o.gz"))),
                g.ELF(raw(repo, str(FIRST / "evidence/firstdot-v1/library/member-extract/stdout.log"))),
                g.ELF((build / "gemv-reference.o").read_bytes()),
            )
            for i, (name, size, pin) in enumerate(RVV):
                reference = references[0 if i < 2 else 1 if i == 3 else 2]
                code = elf.symbol_data(name)
                g.require(len(code) == size and e.digest(code) == pin and code == reference.symbol_data(name),
                          "screen qualified RVV leaf changed: " + name)
            result.update(screening_scope="full-only", caller_variant=caller, selected_rvv=choice,
                          selected_rvv_symbol=RVV[choice][0], qualified_rvv_leaves=5,
                          windows=36, formal_windows=24)
            return result

        def load(name, path):
            module = old_load(name, path)
            if Path(path).resolve() == (e.HERE / "evidence.py").resolve():
                original_audit = module.audit

                def audit(build, run):
                    result = original_audit(build, run)
                    validation = e.read(run / "runs/recovery/validation.json")
                    g.require(validation["windows"] == 36 and validation["formal_windows"] == 24 and
                              validation["committed_vdot"] == 672 and len(validation["summary"]) == 1,
                              "screen full-only audit coverage")
                    result.update(windows_per_normal_run=36, formal_windows_used=24, replay_windows=36,
                                  screening_scope="full-only", caller_variant=caller, selected_rvv=choice,
                                  selected_rvv_symbol=RVV[choice][0])
                    return result

                module.audit = audit
            return module

        e.sources, e.generate, e.verification = sources, generate, verification
        e.pathcheck.path, g.load = path, load

    h.install = install


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--caller", choices=("baseline", "hoisted"), required=True)
    parser.add_argument("--rvv", type=int, choices=range(5), required=True)
    selection, rest = parser.parse_known_args()
    configure(selection.caller, selection.rvv)
    sys.argv = [sys.argv[0]] + rest
    h.main()


if __name__ == "__main__":
    main()
