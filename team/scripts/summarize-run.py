#!/usr/bin/env python3
"""Check one hello/vadd execution and extract its actual output."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
EXPECTED = (
    (9, 9, 9, 9, 9, 9, 9, 9),
    (254, 252, 250, 248, 246, 244, 242, 240),
    (128, 127, 0, 0, 0, 0, 254, 254),
)


def validate(content, receipt, log_sha256, errors, stderr_sha256):
    """Validate values, event order, and the supplied execution receipt."""
    if receipt.get("schema") != "hello-vadd-run-v1":
        raise ValueError("Unknown execution receipt")
    if receipt.get("exit_code") != 0 or receipt.get("timed_out") is not False:
        raise ValueError("Execution did not finish normally with exit code zero")
    if receipt.get("log_sha256") != log_sha256:
        raise ValueError("Log is not the one bound by the execution receipt")
    if receipt.get("stderr_sha256") != stderr_sha256:
        raise ValueError("Stderr is not the one bound by the execution receipt")
    before, after = receipt.get("inputs", {}), receipt.get("inputs_after", {})
    if set(before) != {"emu", "reference", "image", "flash"} or before != after:
        raise ValueError("Missing or changed execution inputs")
    for item in before.values():
        if not item.get("path") or not re.fullmatch(r"[0-9a-f]{64}", item.get("sha256", "")):
            raise ValueError("Invalid input identity")
    aux = receipt.get("aux", {})
    if set(aux) != {"constantin.txt", "plusArgs"} or receipt.get("aux_after") != {
            name: item["sha256"] for name, item in aux.items()}:
        raise ValueError("Missing or changed runtime auxiliary inputs")
    identity = receipt["identity"]
    text = ANSI.sub("", content).replace("\r", "")
    if re.search(r"FAIL:|BAD TRAP|ABORT|Assertion.*failed|DIFFTEST.*FAIL|EXCEED.*LIMIT", text + ANSI.sub("", errors), re.I):
        raise ValueError("Failure marker in emulator output")
    required = [
        "Difftest enabled",
        f"hello xiangshan, I am {identity['team_id']}, IP address={identity['host_ip']}",
        f"identity_status={identity['status']}; IP address is build-host IPv4",
        "RVV VLEN=128 bits; SEW=8 LMUL=1 AVL=8",
        *[f"vadd case={i} output: " + " ".join(map(str, row)) + " PASS"
          for i, row in enumerate(EXPECTED)],
        "HELLO_VADD_PASS cases=3 lanes=24",
        "HIT GOOD TRAP",
    ]
    positions = []
    for marker in required:
        if text.count(marker) != 1:
            raise ValueError(f"Expected exactly one acceptance marker: {marker}")
        positions.append(text.index(marker))
    if positions != sorted(positions):
        raise ValueError("Acceptance markers are out of order")
    if len(re.findall(r"vadd case=\d+ output:", text)) != 3:
        raise ValueError("Unexpected or repeated case output")
    for key, marker in (("image", "The image is "), ("reference", "The reference model is "),
                        ("flash", "Loading flash image: ")):
        path = before[key]["path"]
        if marker + path not in text:
            raise ValueError(f"Runtime did not report expected {key}: {path}")
    return [line for line in text.splitlines() if any(
        word in line for word in required + ["The image is", "The reference model is",
        "Loading flash image", "instrCnt =", "Host time spent:"])]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--stderr", type=Path, required=True)
    args = parser.parse_args()
    raw = args.log.read_bytes()
    errors = args.stderr.read_bytes()
    receipt = json.loads(args.receipt.read_text())
    try:
        lines = validate(raw.decode("utf-8"), receipt, hashlib.sha256(raw).hexdigest(),
                         errors.decode("utf-8"), hashlib.sha256(errors).hexdigest())
    except (ValueError, KeyError) as error:
        raise SystemExit(f"HELLO_VADD_CHECK_FAIL: {error}") from error
    print("\n".join(lines))
    print("HELLO_VADD_EMU_RUN_PASS")


if __name__ == "__main__":
    main()
