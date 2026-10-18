#!/usr/bin/env python3
"""Mutate an actual successful parent trace and require independent rejection."""
import argparse
import hashlib
import json
from pathlib import Path

from check_trace import HEX, TraceError, audit, record, require


def encode(tag, fields):
    return tag + " " + " ".join(f"{k}=" + (hex(v) if k in HEX else str(v)) for k, v in fields.items())


def check(path):
    raw = path.read_bytes()
    original = raw.decode("utf-8").splitlines()
    baseline = audit(original, 2, "parent")
    require(baseline["overlap"] > 10000 and baseline["canceled"] >= 36, "missing real parent stress coverage")
    frames = [(i, record(s)[1]) for i, s in enumerate(original) if s.startswith("O1_EXU ")]
    handoff = next((i, f) for i, f in frames if f["ca"] and f["ov"] and f["od"] != f["id"])
    cancel = next((i, f) for i, f in frames if f["kill"])
    records = []
    def reject(name, lines):
        try:
            audit(lines, 2, "parent")
        except TraceError as error:
            records.append(dict(name=name, status="EXPECTED_REJECTION", reason=str(error),
                                mutated_sha256=hashlib.sha256(("\n".join(lines)+"\n").encode()).hexdigest()))
            return
        raise TraceError("mutation escaped: " + name)
    for name, location, key, value in (
        ("new-destination-as-old", handoff, "od", handoff[1]["id"]),
        ("vector-high-bit", handoff, "vec", handoff[1]["vec"] ^ (1 << 100)),
        ("lost-child-acceptance", handoff, "ca", 0),
        ("lost-cancellation", cancel, "kill", 0),
    ):
        i, f = location
        changed = original.copy()
        modified = dict(f, **{key: value})
        changed[i] = encode("O1_EXU", modified)
        reject(name, changed)
    i, _ = handoff
    reject("missing-handoff-frame", original[:i] + original[i+1:])
    reject("duplicate-handoff-frame", original[:i] + [original[i]] + original[i:])
    reject("truncated-busy-tail", original[:i])
    reject("missing-independent-ledger", [s for s in original if not s.startswith("VFEX4_PARENT_PASS")])
    return dict(status="O1_REAL_TRACE_NEGATIVES_PASS", source_sha256=hashlib.sha256(raw).hexdigest(),
                positive=baseline, mutations=records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = check(args.log)
    args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(result["status"], "mutations=" + str(len(result["mutations"])))
