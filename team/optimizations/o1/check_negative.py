"""Fail-closed checker for the four O1 scoreboard fault-injection runs."""
import argparse
from pathlib import Path
import sys

EXPECTED_FAILURES = {
    "identity": "old identity",
    "wen": "old write enables",
    "high": "full128 result",
    "cancel": "output valid/kill/latency",
}


def check_negative(fault: str, return_code: int, log: str) -> None:
    """Accept only the selected injection followed by its specific detection."""
    if fault not in EXPECTED_FAILURES:
        raise ValueError("unknown injection")
    if return_code != 1:
        raise ValueError(f"expected detection exit 1, got {return_code}")
    lines = [line for line in log.splitlines() if line.strip()]
    expected = [f"O1_INJECT {fault}", f"O1_FU_FAIL {EXPECTED_FAILURES[fault]}"]
    if lines != expected:
        raise ValueError("expected exactly one injection and its matching failure, in order")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fault", required=True, choices=EXPECTED_FAILURES)
    parser.add_argument("--return-code", required=True, type=int)
    parser.add_argument("--log", required=True, type=Path)
    args = parser.parse_args()
    try:
        check_negative(args.fault, args.return_code, args.log.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        print(f"O1_NEGATIVE_CHECK_FAIL {args.fault}: {exc}", file=sys.stderr)
        return 1
    print(f"O1_NEGATIVE_CHECK_PASS {args.fault}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
