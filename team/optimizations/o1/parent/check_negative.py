"""Fail-closed checker for real VFEX4 parent scoreboard fault injections."""
import argparse
from pathlib import Path
import sys

FAULTS = ("identity", "wen", "high", "cancel", "busy", "route", "clock")


def check_negative(fault: str, return_code: int, log: str) -> None:
    """Accept only the selected injection and matching detection with exit 1."""
    if fault not in FAULTS:
        raise ValueError("unknown injection")
    if return_code != 1:
        raise ValueError(f"expected detection exit 1, got {return_code}")
    lines = [line for line in log.splitlines() if line.strip()]
    expected = [f"O1_PARENT_INJECT {fault}", f"O1_PARENT_FAIL {fault}"]
    if lines != expected:
        raise ValueError("expected exactly the matching injection/failure pair, in order")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fault", required=True, choices=FAULTS)
    parser.add_argument("--return-code", required=True, type=int)
    parser.add_argument("--log", required=True, type=Path)
    args = parser.parse_args()
    try:
        check_negative(args.fault, args.return_code, args.log.read_text(encoding="utf-8"))
    except (ValueError, OSError, UnicodeError) as exc:
        print(f"O1_PARENT_NEGATIVE_CHECK_FAIL {args.fault}: {exc}", file=sys.stderr)
        return 1
    print(f"O1_PARENT_NEGATIVE_CHECK_PASS {args.fault}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
