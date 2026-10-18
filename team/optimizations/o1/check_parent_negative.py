"""Bind a parent fault injection to its specific, unique detection reason."""
import argparse
from pathlib import Path
import re

from check_trace import record, require

REASONS = {'identity': 'old identity', 'wen': 'write class',
           'high': 'full128 shared/vec/v0 result',
           'cancel': 'unsolicited or canceled vdot output'}


def check(fault, return_code, text):
    require(fault in REASONS, 'unknown parent injection')
    require(return_code == 1, 'parent detection requires exit 1')
    markers = []
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.startswith('O1_'):
            require(not markers, 'trace after injection/detection')
            tag, _ = record(line)
            require(tag in ('O1_EXU_BEGIN', 'O1_EXU'), 'unexpected parent trace record')
        else:
            markers.append(line)
    require(len(markers)==2 and markers[0]=='PARENT_INJECT '+fault,
            'missing/duplicate/out-of-order parent injection')
    require(re.fullmatch(r'VFEX4_PARENT_FAIL tick=[0-9]+ '+re.escape(REASONS[fault]), markers[1])
            is not None, 'parent failure does not match injected fault')
    return dict(status='PARENT_NEGATIVE_CHECK_PASS', fault=fault, return_code=return_code)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fault', required=True, choices=REASONS)
    parser.add_argument('--return-code', required=True, type=int)
    parser.add_argument('--log', required=True, type=Path)
    args=parser.parse_args()
    print(check(args.fault,args.return_code,args.log.read_text())['status'])
