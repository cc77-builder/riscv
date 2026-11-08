#!/usr/bin/env python3
"""Check third-output accounting using in-memory mutations of an old test fixture.

This does not implement or emit candidate RTL. The existing synthetic Booth2
fixture retains its eight compressor layers; it is only parser/checker input.
No candidate generator, compiler, HDL simulator, SAT or EDA tool is run.
"""
from pathlib import Path
import hashlib
import json
import re
import runpy
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CHECKER = ROOT / 'controller/verify_booth.py'
CHECKER_SHA = 'c0181c3c099a4a4e3ce4fcfcd1af3c34d337031675b6533ad303327ad632d587'
PARENT = ROOT.parent / 'prefix-booth-candidate-01/review/checker-fixtures/synthetic-correct.sv'
PARENT_SHA = '715b257a8bb84af07568436f2320737ba9cac40f2b24051c13419033049c37f6'
ZERO = "1'b0"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def row_assign(index, terms):
    return f'assign row{index} = ' + '{' + ', '.join(terms) + '};'


def main():
    parent, checker = PARENT.read_bytes(), CHECKER.read_bytes()
    assert sha(parent) == PARENT_SHA and sha(checker) == CHECKER_SHA
    api = runpy.run_path(str(CHECKER), run_name='row2_checker_test_only')
    text = parent.decode('ascii')
    header_before = 'output wire [19:0] row0, output wire [19:0] row1\n'
    header_after = 'output wire [19:0] row0, output wire [19:0] row1, output wire [19:0] row2\n'
    assert text.count(header_before) == 1
    base = text.replace(header_before, header_after)
    match = re.search(r'assign row0 = \{([^}]+)\};', base)
    old_row0 = [x.strip() for x in match[1].split(',')]
    assert len(old_row0) == 20
    moved_term = old_row0[-1]
    assert moved_term == 's_7_0_0'
    zero_row = [ZERO]*20

    def variant(row0, row2=None):
        current = base.replace(match[0], row_assign(0, row0))
        assert current.count('endmodule') == 1
        if row2 is not None:
            current = current.replace('endmodule', row_assign(2,row2)+'\nendmodule')
        return current.encode('ascii')

    low_row = old_row0[:-1] + [ZERO]
    third = zero_row[:-1] + [moved_term]
    shifted = list(zero_row);shifted[-2] = moved_term
    tests = [
        ('old-two-row-interface', parent, False),
        ('three-rows-zero-third', variant(old_row0,zero_row), True),
        ('three-rows-nonzero-third', variant(low_row,third), True),
        ('missing-row2-driver', variant(low_row), False),
        ('drop-row2-token', variant(low_row,zero_row), False),
        ('duplicate-row2-token', variant(old_row0,third), False),
        ('wrong-row2-weight', variant(low_row,shifted), False),
        ('short-row2-concat', variant(low_row,third[1:]), False),
    ]
    results = []
    for label, raw, expected in tests:
        try:
            proof = api['prove'](raw)
            accepted, error = True, None
        except api['Invalid'] as exc:
            proof, accepted, error = None, False, str(exc)
        assert accepted == expected, (label,expected,accepted,error)
        if proof:
            assert set(proof['rows_msb_to_lsb']) == {'row0','row1','row2'}
            assert proof['status'] == 'BOOTH3_CSA_STRUCTURAL_EQUIVALENCE_PASS'
            assert not proof['wrapper_binding_verified'] and not proof['sequential_fu_qualified']
        results.append(dict(case=label,bytes=len(raw),sha256=sha(raw),
            expected_accepted=expected,accepted=accepted,error=error,proof=proof))
    assert PARENT.read_bytes() == parent and CHECKER.read_bytes() == checker
    result = dict(status='ROW2_CHECKER_REGRESSION_PASS',
        scope='In-memory old synthetic fixture mutations; not candidate three-row P RTL or new R SAT.',
        parent_fixture=dict(path=str(PARENT),bytes=len(parent),sha256=PARENT_SHA),
        checker=dict(path=str(CHECKER),bytes=len(checker),sha256=CHECKER_SHA),
        moved_token=dict(name=moved_term,weight=0,source='row0',destination='row2'),
        tests=results,actual_candidate_sv_generated=False,new_r_sat_run=False,
        actual_fu_run=False,new_builds=0,new_eda_runs=0)
    output = HERE / 'row2-result.json'
    with output.open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(dict(status=result['status'],accepted=sum(x['accepted'] for x in results),
        rejected=sum(not x['accepted'] for x in results),bytes=output.stat().st_size,
        sha256=sha(output.read_bytes()))))


if __name__ == '__main__':
    main()
