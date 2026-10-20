#!/usr/bin/env python3
"""Validate sealed bytes, restore in isolation, then run the current strict audit."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile
from archive_gate import assessment, restore, require


def recheck(evidence):
    with tempfile.TemporaryDirectory(prefix="vdot-o4-audit-") as temporary:
        root = Path(temporary)
        count = restore(evidence, root)
        claimed = assessment(root)
        # Keep optimization enabled in the child when checking -OO behavior.
        option = "-" + "O" * sys.flags.optimize if sys.flags.optimize else "-B"
        subprocess.run([sys.executable, option, str(Path(__file__).with_name("audit.py")), str(root)], check=True)
        actual = assessment(root)
        require(all(actual.get(key) == claimed.get(key) for key in
                    ("results", "selection", "arithmetic_identity", "not_signoff")),
                "stored assessment differs from independent audit")
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    count = recheck(parser.parse_args().evidence)
    print(f"O4_SEALED_RECHECK_PASS files={count}")


if __name__ == "__main__":
    main()
