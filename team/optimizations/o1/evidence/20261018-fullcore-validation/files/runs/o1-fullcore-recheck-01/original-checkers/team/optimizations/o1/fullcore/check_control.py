"""Strict T12 workload obligations on the independent O1 observer schema."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

import analyze as trace


def check(text, manifest, exit_code, analysis=None):
    trace.require(exit_code == 0, 'emulator exit code is not zero')
    trace.require('The first instruction of core 0 has commited. Difftest enabled.' in text
                  and 'The reference model is ' in text, 'missing DiffTest runtime banner')
    trace.require(not re.search(r'T12_(?:MISMATCH|CSR_FAIL|SPEC_FAIL)|HIT BAD TRAP|Assertion.*failed|different at pc|DIFFTEST FAIL|ABORT', text),
                  'failure in raw log')
    _, uart = trace.extract_events_and_uart(text)
    uart = uart.replace('\r\n', '\n')
    summaries = list(re.finditer(r'^T12_SUMMARY groups=4 checkpoints=128 speculative_attempts=256 failures=0$', uart, re.M))
    trace.require(len(summaries) == 1 and uart.count('T12_SUMMARY') == 1,
                  'missing or duplicate successful workload summary')
    trace.require(uart.count('HIT GOOD TRAP') == 1 and 'HIT GOOD TRAP' in uart[summaries[0].end():],
                  'no unique GOOD TRAP after complete summary')
    groups = list(re.finditer(r'^T12_GROUP_PASS id=(\d+) checkpoints=32 bytes=16384$', uart, re.M))
    trace.require([m[1] for m in groups] == ['0', '1', '2', '3'] and uart.count('T12_GROUP_PASS') == 4,
                  'missing, duplicate or reordered group result')
    begins = list(re.finditer(r'^T12_BEGIN seed=0x20261014 contract=vdot-s8x8-r32-v0.1$', uart, re.M))
    trace.require(len(begins) == 1 and uart.count('T12_BEGIN') == 1
                  and begins[0].start() < groups[0].start()
                  and groups[-1].end() < summaries[0].start(), 'invalid begin/group/summary order')
    if analysis is None:
        analysis = trace.analyze(text)
    trace.require(analysis['status'] == 'O1_TRACE_PASS' and analysis['pending_count'] == 0
                  and analysis['unfinished_rob_count'] == 0, 'incomplete trace cannot pass control')
    trace.require(analysis['input_sha256'] == hashlib.sha256(text.encode('utf-8')).hexdigest(),
                  'cached analysis belongs to different raw trace')
    trace.require(analysis['schema']['handoff'] == 1, 'O1 control gate requires handoff candidate')
    trace.require(all(t['illegal'] == 0 and t['vl'] == 8 for t in analysis['transactions']),
                  'unexpected illegal stress request')
    counts = analysis['counts']
    expected = sum(g['vdot_count'] for g in manifest['groups']) + manifest['speculation']['expected_architectural_vdot']
    trace.require(counts['COMMIT'] == expected, 'vdot retirement count differs from manifest')
    coverage = {
        'accepted_younger_squashed': counts.get('ACCEPTED_YOUNGER_SQUASHED', 0) > 0,
        'inflight_fu_killed': counts['KILL'] > 0,
        'shared_vfex4_fu_kinds': len(analysis['vfex4_fu_counts']) >= 2,
        'shared_vfex4_backpressure': counts['VFEX4_WAIT'] > 0,
        'vdot_writeback_backpressure': counts['STALL'] > 0,
        'rob_wrap_repeated': counts.get('ROB_WRAP', 0) >= 8,
        'ftq_wrap_repeated': counts.get('FTQ_WRAP', 0) >= 8,
    }
    handoff_covered = counts['HANDOFF'] > 0
    complete = all(coverage.values()) and handoff_covered
    return dict(status='O1_CONTROL_REGRESSION_PASS' if complete else 'O1_COVERAGE_INCOMPLETE',
                architectural_checks='PASS', legacy_coverage=coverage,
                coverage=dict(coverage, same_cycle_handoff=handoff_covered),
                legacy_coverage_complete=all(coverage.values()),
                handoff_coverage_complete=handoff_covered, counts=counts,
                expected_vdot_commits=expected, vfex4_fu_counts=analysis['vfex4_fu_counts'],
                clock_mapping=analysis['clock_mapping'],
                scope='pinned MinimalConfig control regression; not performance or virtualization acceptance',
                performance_measured=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--exit-code', type=int, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = check(args.log.read_text(encoding='utf-8'), json.loads(args.manifest.read_text()), args.exit_code)
        encoded = json.dumps(result, indent=2) + '\n'
        if args.output:
            trace.require(not args.output.exists(), 'output already exists')
            args.output.write_text(encoded, encoding='utf-8')
        print(encoded, end='')
        return 0 if result['status'] == 'O1_CONTROL_REGRESSION_PASS' else 2
    except (ValueError, OSError, KeyError) as exc:
        print('O1_CONTROL_REJECTED: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
