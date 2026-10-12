#!/usr/bin/env python3
"""Validate the existing T05 artifacts and export inputs/expectations verbatim.

No arithmetic oracle or random generator belongs in this RTL adapter: expected
results come from the checked-in JSONL files, authenticated by their manifest.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re


CONTRACT = "vdot-s8x8-r32-v0.1"
EXPECTED_COUNTS = {"directed": 22, "random": 10000}
HEX128 = re.compile(r"0x[0-9a-f]{32}\Z")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(data_dir, output):
    manifest = json.loads((data_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest["contract"] != CONTRACT or manifest["schema_version"] != 1:
        raise ValueError("unsupported vector contract/schema")
    for name in ("model.py", "generate.py"):
        if sha256(data_dir.parent / name) != manifest["source_sha256"][name]:
            raise ValueError(f"model source hash mismatch: {name}")

    rows = []
    ids = set()
    for suite, count in EXPECTED_COUNTS.items():
        name = f"{suite}.jsonl"
        path = data_dir / name
        metadata = manifest["files"][name]
        if metadata["count"] != count or sha256(path) != metadata["sha256"]:
            raise ValueError(f"vector count/hash mismatch: {name}")
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) != count:
            raise ValueError(f"wrong actual vector count: {name}")
        for line in lines:
            case = json.loads(line)
            case_id = case["id"]
            if not isinstance(case_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", case_id):
                raise ValueError(f"invalid case id: {case_id!r}")
            if case_id in ids:
                raise ValueError(f"duplicate case id: {case_id}")
            ids.add(case_id)
            values = [case[key] for key in ("vs1", "vs2", "expected_vd")]
            if any(not isinstance(value, str) or not HEX128.fullmatch(value) for value in values):
                raise ValueError(f"invalid 128-bit field: {case_id}")
            rows.append("\t".join([suite, case_id, *(value[2:] for value in values)]))
        print(f"VECTOR_CHECK_PASS suite={suite} count={count} sha256={metadata['sha256']}")

    # Write only after all input artifacts have passed validation.
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    print(f"VECTOR_EXPORT_PASS contract={CONTRACT} total={len(rows)} sha256={sha256(output)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        prepare(args.data_dir, args.output)
    except (KeyError, OSError, TypeError, ValueError) as exc:
        parser.exit(1, f"VECTOR_CHECK_FAIL: {exc}\n")


if __name__ == "__main__":
    main()
