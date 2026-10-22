"""ANSI-independent failure gates for post-run O1 evidence audits.

These gates inspect logs; they do not run an emulator or validate ISA state.
The frozen first campaign driver is intentionally not edited while it runs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ANSI_CSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
COMMON_FAILURES = re.compile(
    r'Assertion[^\n]*failed|HIT BAD TRAP|DIFFTEST FAIL|NEGATIVE_FIXTURE_SETUP_FAIL|'
    r'T12_(?:MISMATCH|CSR_FAIL|SPEC_FAIL)|T13_FAIL|'
    r'EXCEEDING CYCLE/INSTR LIMIT|SOME SIGNAL STOPS THE PROGRAM|Unknown trap code|'
    r'Segmentation fault|terminate called', re.I)
INJECTION = re.compile(
    r'^DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd=(\d+) '
    r'pc=(0x[0-9a-fA-F]+) instruction=(0x[0-9a-fA-F]+)$', re.M)
MISMATCH = re.compile(
    r'^v(\d+)_high different at pc = (0x[0-9a-fA-F]+), '
    r'right=\s*(0x[0-9a-fA-F]+), wrong =\s*(0x[0-9a-fA-F]+)$', re.M)
ABORT = re.compile(r'^Core 0: ABORT at pc = (0x[0-9a-fA-F]+)$', re.M)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def normalize_console(text):
    """Remove complete ANSI CSI controls before interpreting failure markers.

    Unsupported/incomplete escape controls fail closed. Preserve the original
    bytes separately; this returns only a parsing view with normalized newlines.
    """
    require(isinstance(text, str), 'console input must be decoded text')
    plain = ANSI_CSI.sub('', text).replace('\r\n', '\n').replace('\r', '\n')
    require('\x1b' not in plain and '\x9b' not in plain,
            'unsupported or truncated terminal escape')
    require(all((ord(ch) >= 32 or ch in '\n\t') and not 0x7f <= ord(ch) <= 0x9f
                for ch in plain), 'unsupported console control character')
    return plain


def validate_failure_markers(text, negative=False):
    """Normal mode rejects every ABORT; negative mode requires the full chain."""
    if negative:
        validate_negative(text, 1)
        return
    plain = normalize_console(text)
    require(COMMON_FAILURES.search(plain) is None and
            re.search(r'ABORT|different at pc|DIFFTEST_HIGHBIT_NEGATIVE_INJECTED', plain, re.I) is None,
            'runtime failure marker')


def validate_negative(text, return_code):
    require(return_code == 1, 'negative run must exit 1')
    plain = normalize_console(text)
    require(COMMON_FAILURES.search(plain) is None, 'unrelated runtime failure marker')
    require('HIT GOOD TRAP' not in plain.upper(), 'negative run unexpectedly reached GOOD TRAP')
    injected = list(INJECTION.finditer(plain))
    require(len(injected) == 1 and
            len(re.findall('DIFFTEST_HIGHBIT_NEGATIVE_INJECTED', plain, re.I)) == 1,
            'expected exactly one complete bit100 injection')
    vd_text, pc_text, word_text = injected[0].groups()
    vd, pc, word = int(vd_text), int(pc_text, 16), int(word_text, 16)
    require(0 <= vd < 32 and pc < 1 << 64 and word < 1 << 32 and
            word & 0xfe00707f == 0x0200000b,
            'injection is not a valid vdot destination/instruction')
    require((word >> 7) & 31 == vd, 'injection destination disagrees with instruction')
    mismatches = list(MISMATCH.finditer(plain))
    require(len(mismatches) == 1 and len(re.findall('different at pc', plain, re.I)) == 1,
            'expected exactly one complete vector high-half mismatch')
    diff_vd, diff_pc, right_text, wrong_text = mismatches[0].groups()
    right, wrong = int(right_text, 16), int(wrong_text, 16)
    require(int(diff_vd) == vd and int(diff_pc, 16) == pc,
            'negative mismatch must bind injected PC and vector register')
    require(right < 1 << 64 and wrong < 1 << 64 and right ^ wrong == 1 << 36,
            'negative mismatch is not exactly vector bit100')
    aborted = list(ABORT.finditer(plain))
    require(len(aborted) == 1 and len(re.findall('ABORT', plain, re.I)) == 1,
            'expected exactly one canonical Core 0 ABORT')
    abort_pc = int(aborted[0][1], 16)
    require(abort_pc < 1 << 64, 'ABORT event PC overflow')
    require(mismatches[0].end() < aborted[0].start() and
            not plain[mismatches[0].end():aborted[0].start()].strip(),
            'terminal ABORT must immediately follow the bound mismatch')
    # display_trapinfo prints dut->trap.pc, which is the XSTrap event PC;
    # it is not the dut->commit[0].pc used for the mismatch diagnostic.
    return dict(vd=vd, pc=hex(pc), word=f'0x{word:08x}', bit=100,
                abort_event_pc=hex(abort_pc), abort_count=1,
                fault_pc_binding='injection PC equals mismatch PC',
                abort_pc_scope='recorded XSTrap event field; not required to equal mismatch PC')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', required=True, type=Path)
    parser.add_argument('--mode', required=True, choices=('normal', 'negative'))
    parser.add_argument('--exit-code', required=True, type=int)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        raw = args.log.read_bytes()
        text = raw.decode('utf-8')
        if args.mode == 'negative':
            details = validate_negative(text, args.exit_code)
            status = 'EXPECTED_BIT100_NEGATIVE_LOG_GATE_PASS'
        else:
            require(args.exit_code == 0, 'normal run must exit zero')
            validate_failure_markers(text)
            details = {}
            status = 'NORMAL_FAILURE_MARKERS_CLEAR'
        result = dict(status=status, mode=args.mode, exit_code=args.exit_code,
                      raw_log=str(args.log.resolve()), raw_bytes_sha256=hashlib.sha256(raw).hexdigest(),
                      normalized_console_sha256=hashlib.sha256(normalize_console(text).encode()).hexdigest(),
                      checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      details=details, new_emu_run=False,
                      scope='offline failure-marker/negative-control gate; not whole-suite acceptance')
        require(not args.output.exists(), 'output already exists')
        args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, UnicodeError) as exc:
        print('O1_RUNTIME_LOG_GATE_REJECTED: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
