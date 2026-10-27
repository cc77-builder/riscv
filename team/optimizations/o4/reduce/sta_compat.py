#!/usr/bin/env python3
"""Split scalar concatenation assignments for OpenSTA 2.0.17, preserving logic.

No remapping, simplification, constraints or official tools are changed. Both
texts are reread by the same Yosys and their complete structural JSONs compared
after dropping only source/debug attributes and the tool creator string.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil


def split_assignments(text):
    result, changes = [], []
    signal = r"\\[^\s,{}]+\s+\[\d+\]"
    for line in text.splitlines(keepends=True):
        if not re.match(r"\s*assign\s+\{", line):
            result.append(line)
            continue
        m = re.fullmatch(r"\s*assign\s+\{([^{}]+)\}\s*=\s*\{([^{}]+)\};\s*", line)
        if not m:
            raise ValueError("unsupported concatenated assignment")
        left, right = ([part.strip() for part in group.split(",")] for group in m.groups())
        if len(left) != len(right) or not left:
            raise ValueError("concatenation arity differs")
        if not all(re.fullmatch(signal, token) for token in left):
            raise ValueError("non-scalar left side")
        if not all(re.fullmatch(signal + r"|1'[bh][01]", token) for token in right):
            raise ValueError("non-scalar right side")
        replacement = ["  assign " + a + " = " + b + ";\n" for a, b in zip(left, right)]
        result.extend(replacement)
        changes.append(dict(original=line, replacement=replacement))
    return "".join(result), changes


def canonical(value):
    if isinstance(value, dict):
        return {k: canonical(v) for k, v in value.items() if k not in ("attributes", "creator")}
    if isinstance(value, list):
        return [canonical(v) for v in value]
    return value


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("driver", "mapping", "output"):
        p.add_argument("--" + key, type=Path, required=True)
    a = p.parse_args()
    spec = importlib.util.spec_from_file_location("r3driver", a.driver)
    d = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(d)
    source = a.mapping.resolve()
    summary = d.read(source / "summary.json")
    generation = Path(summary["generation"])
    out = d.fresh(a.output, [source, generation, Path(d.read(generation / "result.json")["source_root"])])
    d.require(summary["pass"] and d.sha(source / "mapped.v") == summary["mapped_sha256"]
              and d.sha(source / "mapped.json") == summary["mapped_json_sha256"], "original mapping identity")
    text, changes = split_assignments((source / "mapped.v").read_text())
    (out / "mapped.v").write_text(text)
    for name in ("mapped.json", "map.ys"):
        shutil.copyfile(source / name, out / name)
    for label, netlist in (("original", source / "mapped.v"), ("compatible", out / "mapped.v")):
        script = out / (label + ".ys")
        script.write_text(f"read_verilog {netlist}\nwrite_json {out / (label + '-readback.json')}\n")
        r = d.command(["/usr/bin/yosys", "-Q", "-T", "-s", script], out, os.environ.copy(), out, label, 90)
        d.require(r["exit_code"] == 0, "netlist readback failed")
    d.require(canonical(d.read(out / "original-readback.json")) == canonical(d.read(out / "compatible-readback.json")),
              "serialized netlist structure differs")
    d.save(out / "serialization.json", dict(status="PASS", original_mapping=str(source),
           original_summary_sha256=d.sha(source / "summary.json"), original_verilog_sha256=d.sha(source / "mapped.v"),
           original_json_sha256=summary["mapped_json_sha256"], changes=changes,
           readbacks={n: d.sha(out / (n + "-readback.json")) for n in ("original", "compatible")},
           adapter_sha256=d.sha(__file__), yosys_sha256=d.sha("/usr/bin/yosys")))
    summary.update(mapped_sha256=d.sha(out / "mapped.v"), serialization_sha256=d.sha(out / "serialization.json"),
                   serialization="scalar assignment split; full structural readback equality; no logic remap")
    d.save(out / "summary.json", summary)
    print(json.dumps(dict(status="PASS", mapping=str(out), split_assignments=len(changes),
                         area=summary["cell_area_sum"]), indent=2))


if __name__ == "__main__":
    main()
