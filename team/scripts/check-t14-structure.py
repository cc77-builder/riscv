"""Audit the one-factor T14 RTL structure; this is not synthesis or STA."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def require(ok, message):
    if not ok:
        raise ValueError(message)


def normalize(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"at VDot\.scala:\d+ ", "at VDot.scala:<line> ", text)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def module(text, name):
    found = re.findall(r"\bmodule " + name + r"\(.*?\bendmodule", text, re.S)
    require(len(found) == 1, "missing/duplicate module " + name)
    return found[0]


def registers(text):
    result = {}
    for high, low, name in re.findall(r"^\s*reg\s+(?:\[(\d+):(\d+)\]\s+)?(\w+)\s*;", text, re.M):
        require(name not in result, "duplicate register")
        result[name] = int(high) - int(low) + 1 if high else 1
    return result


def audit(old, baseline, candidate):
    texts = {name: normalize(path.read_text()) for name, path in
             (("old", old), ("baseline", baseline), ("candidate", candidate))}
    require(texts["old"] == texts["baseline"], "baseline changed beyond assertion line annotations")
    base_regs = registers(module(texts["baseline"], "VDot"))
    candidate_regs = registers(module(texts["candidate"], "VDot"))
    removed = {name: width for name, width in base_regs.items() if name not in candidate_regs}
    require(removed == {"src1Reg": 128, "src2Reg": 128}, "unexpected register removal")
    require(candidate_regs == {name: width for name, width in base_regs.items() if name not in removed},
            "other declared register widths changed")
    for name in ("VDotProducts", "VDotReduce"):
        require(module(texts["baseline"], name) == module(texts["candidate"], name),
                "arithmetic logic changed: " + name)
    multiply = module(texts["candidate"], "VDotProducts").count(" * ")
    addition = module(texts["candidate"], "VDotReduce").count(" + ")
    require((multiply, addition) == (8, 7), "operator counts changed")
    return dict(status="T14_STRUCTURE_AUDIT_PASS", source_files={
        name: dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        for name, path in (("old", old), ("baseline", baseline), ("candidate", candidate))},
        baseline_logic_text_identical=True, removed_declared_registers=removed,
        baseline_declared_register_bits=sum(base_regs.values()),
        candidate_declared_register_bits=sum(candidate_regs.values()),
        multiplication_operators=multiply, addition_operators=addition,
        arithmetic_modules_identical=True,
        limitations="Elaborated SV declarations, including simulation assertions/debug state; not synthesized flops, area, power, Fmax or formal equivalence. Upper unused source bits may be removed by synthesis.",
        timing_tradeoff="Multiplication moves onto the upstream input-to-product-register path; shorter cycle latency does not establish a shorter clock period.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("old", "baseline", "candidate", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.old, args.baseline, args.candidate)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
