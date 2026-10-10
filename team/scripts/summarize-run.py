#!/usr/bin/env python3
"""Validate and extract actual emulator output; do not synthesize a passing log."""
import sys
import re
from pathlib import Path

source = Path(sys.argv[1])
content = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", source.read_text(errors="replace"))
required = ["Difftest enabled", "vadd case=0 output:", "vadd case=1 output:",
            "vadd case=2 output:", "HELLO_VADD_PASS cases=3 lanes=24", "HIT GOOD TRAP"]
for marker in required:
    if marker not in content:
        raise SystemExit(f"Missing acceptance marker: {marker}")
if "FAIL:" in content or "BAD TRAP" in content:
    raise SystemExit("Failure marker found in emulator output")
for line in content.splitlines():
    if any(marker in line for marker in required + ["The image is", "The reference model is", "Loading flash image", "hello xiangshan", "identity_status=", "RVV VLEN=", "instrCnt =", "Host time spent:", "Exit status:"]):
        print(line)
print("HELLO_VADD_EMU_RUN_PASS")
