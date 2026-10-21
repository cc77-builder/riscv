"""Behavioral console-format and injected-failure counterexamples."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

import runtime_gate as gate


def fixture(color=False, crlf=False):
    text = ('DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd=10 pc=0x80001bdc instruction=0x0294050b\n'
            'register dump omitted in this synthetic fixture\n'
            'v10_high different at pc = 0x0080001bdc, right= 0x0000001000000000, wrong = 0x0000000000000000\n'
            'Core 0: ABORT at pc = 0x800016b0\n'
            'Core-0 instrCnt = 238849, cycleCnt = 311097, IPC = 0.767764\n')
    if color:
        text = text.replace('ABORT', '\x1b[31mABORT').replace('Core-0', '\x1b[0m\x1b[35mCore-0') + '\x1b[0m'
    return text.replace('\n','\r\n') if crlf else text


def group_fixture(wrap=False, color=False, crlf=False):
    """Actual six-instruction batch shape, including its noncontiguous jump."""
    instructions = ((0x80001c40, 0x0c543423, 0, 8), (0x80001c44, 0x00100293, 1, 5),
                    (0x80001c48, 0x00543c23, 0, 24), (0x80001c4c, 0x0294050b, 1, 10),
                    (0x80001c50, 0xb3dff06f, 0, 0), (0x8000178c, 0x02043283, 1, 5))
    rows = []
    for index, (pc, word, wen, dst) in enumerate(instructions):
        slot = ((30 if wrap else 9) + index) % 32
        row = f'[{slot:02d}] commit pc {pc:016x} inst {word:08x} wen {wen} dst {dst:02d} data 0000000000000000 idx {index + 2:03x}'
        rows.append(row + (' <--' if index == len(instructions) - 1 else ''))
    group = ('the first commit instr pc of DUT is 0x0000000080001c40\n'
             'the first commit instr pc of REF is 0x0000000080001c40\n'
             'commit group [02]: pc 0080001c40 cmtcnt 6 <--\n' + '\n'.join(rows))
    text = fixture().replace('pc=0x80001bdc', 'pc=0x80001c4c').replace('pc = 0x0080001bdc', 'pc = 0x0080001c40')
    text = text.replace('register dump omitted in this synthetic fixture', group)
    if color:
        text = '\x1b[35m' + text.replace('ABORT', '\x1b[31mABORT') + '\x1b[0m'
    return text.replace('\n', '\r\n') if crlf else text


class RuntimeGateTests(unittest.TestCase):
    def test_distinct_pc_requires_exact_latest_commit_group(self):
        for wrap in (False, True):
            for color in (False, True):
                for crlf in (False, True):
                    with self.subTest(wrap=wrap, color=color, crlf=crlf):
                        result = gate.validate_negative(group_fixture(wrap, color, crlf), 1)
                        self.assertEqual(result['pc'], '0x80001c4c')
                        self.assertEqual(result['mismatch_pc'], '0x80001c40')
                        self.assertEqual(result['group_instructions'], 6)

    def test_group_binding_rejects_corrupt_or_unrelated_evidence(self):
        text = group_fixture()
        mutations = (('cmtcnt 6', 'cmtcnt 5'), ('cmtcnt 6', 'cmtcnt 0'), ('cmtcnt 6', 'cmtcnt 33'),
                     ('group [02]', 'group [16]'), ('pc 0080001c40 cmtcnt', 'pc 0080001c44 cmtcnt'),
                     ('REF is 0x0000000080001c40', 'REF is 0x0000000080001c44'),
                     ('DUT is 0x0000000080001c40', 'DUT is 0x0000000080001c44'),
                     ('[12] commit', '[08] commit'), ('inst 0294050b', 'inst 0294058b'),
                     ('wen 1 dst 10', 'wen 0 dst 10'), ('wen 1 dst 10', 'wen 1 dst 11'),
                     ('pc 0000000080001c4c inst', 'pc 0000000080001c4e inst'),
                     ('pc 0000000080001c4c inst', 'pc 10000000080001c4c inst'),
                     ('inst 0294050b', 'inst 10294050b'), ('idx 007 <--', 'idx 007'),
                     ('idx 003\n', 'idx 003 <--\n'), ('idx 007 <--', 'idx 007 <-- <--'))
        for old, new in mutations:
            with self.subTest(old=old, new=new), self.assertRaises(ValueError):
                gate.validate_negative(text.replace(old, new), 1)
        for line in text.splitlines():
            if line.startswith(('the first commit', 'commit group', '[12]')):
                for changed in (text.replace(line + '\n', ''), text.replace(line, line + '\n' + line)):
                    with self.subTest(line=line), self.assertRaises(ValueError):
                        gate.validate_negative(changed, 1)

    def test_group_must_follow_injection_and_precede_mismatch(self):
        text = group_fixture()
        injection = text.splitlines()[0] + '\n'
        with self.assertRaises(ValueError):
            gate.validate_negative(text.replace(injection, '') + injection, 1)
        marker = 'commit group [02]: pc 0080001c40 cmtcnt 6 <--\n'
        for changed in (marker + text.replace(marker, ''), text.replace(marker, '') + marker):
            with self.assertRaises(ValueError):
                gate.validate_negative(changed, 1)

    def test_equal_pc_cannot_bypass_present_group_evidence(self):
        text = group_fixture().replace('pc=0x80001c4c', 'pc=0x80001c40')
        text = text.replace('inst 0c543423 wen 0 dst 08', 'inst 0294050b wen 1 dst 10')
        result = gate.validate_negative(text, 1)
        self.assertEqual(result['pc'], result['group_pc'])
        for bad in (text.replace('cmtcnt 6', 'cmtcnt 5'), text.replace('idx 007 <--', 'idx 007'),
                    text.replace('REF is 0x0000000080001c40', 'REF is 0x0000000080001c44')):
            with self.assertRaises(ValueError):
                gate.validate_negative(bad, 1)

    def test_injected_tuple_must_be_unique_inside_latest_group(self):
        text = group_fixture()
        # A matching row in history cannot authorize a different latest batch.
        outside = text.replace('[12] commit', '[08] commit')
        filler = '[12] commit pc 0000000080001c4c inst 00100513 wen 1 dst 10 data 0000000000000000 idx 005\n'
        outside = outside.replace('[13] commit', filler + '[13] commit')
        # Two identical PC/word/write destinations are ambiguous, even in one batch.
        duplicate = text.replace('pc 0000000080001c48 inst 00543c23 wen 0 dst 24',
                                 'pc 0000000080001c4c inst 0294050b wen 1 dst 10')
        for bad in (outside, duplicate):
            with self.assertRaisesRegex(ValueError, 'not uniquely present'):
                gate.validate_negative(bad, 1)

    def test_real_format_is_independent_of_ansi_and_crlf(self):
        expected = gate.validate_negative(fixture(), 1)
        for color in (False, True):
            for crlf in (False, True):
                with self.subTest(color=color, crlf=crlf):
                    self.assertEqual(gate.validate_negative(fixture(color,crlf),1), expected)
        self.assertNotEqual(expected['pc'], expected['abort_event_pc'])

    def test_normal_mode_rejects_colored_or_split_abort(self):
        for text in ('Core 0: ABORT at pc = 0x80000000\n',
                     'Core 0: \x1b[31mABORT at pc = 0x80000000\n',
                     'Core 0: AB\x1b[31mORT at pc = 0x80000000\n',
                     'prefixABORTsuffix'):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError,'failure marker'):
                gate.validate_failure_markers(text)

    def test_second_colored_or_plain_abort_cannot_escape(self):
        for extra in ('Core 0: ABORT at pc = 0x800016b0\n',
                      'Core 0: \x1b[31mABORT at pc = 0x800016b0\n',
                      '\x1b[31mABORT unrelated extra failure\n', 'unexpected abort\n'):
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError,'exactly one'):
                gate.validate_negative(fixture(True)+extra,1)

    def test_missing_malformed_or_wrong_core_terminal_rejected(self):
        terminal = 'Core 0: ABORT at pc = 0x800016b0\n'
        for replacement in ('', 'ABORT\n', 'Core 1: ABORT at pc = 0x800016b0\n',
                            'Core 0: ABORT at pc = UNKNOWN\n', terminal.rstrip()+' extra\n',
                            'Core 0: ABORT at pc = 0x10000000000000000\n'):
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                gate.validate_negative(fixture().replace(terminal,replacement),1)

    def test_abort_must_directly_follow_bound_mismatch(self):
        text=fixture()
        terminal='Core 0: ABORT at pc = 0x800016b0\n'
        for bad in (terminal+text.replace(terminal,''), text.replace(terminal,'other failure\n'+terminal)):
            with self.assertRaisesRegex(ValueError,'immediately follow'):
                gate.validate_negative(bad,1)

    def test_wrong_exit_codes_never_pass(self):
        for code in (0,2,3,124,-6,-9):
            with self.subTest(code=code), self.assertRaisesRegex(ValueError,'exit 1'):
                gate.validate_negative(fixture(),code)

    def test_unrelated_failure_markers_reject_in_both_modes(self):
        for marker in ('Assertion failed: extra', 'Assertion source.scala:1 failed',
                       '\x1b[31mAssertion failed: extra', 'DIFFTEST FAIL', 'HIT BAD TRAP',
                       'NEGATIVE_FIXTURE_SETUP_FAIL', 'T12_MISMATCH', 'T12_CSR_FAIL',
                       'T12_SPEC_FAIL', 'T13_FAIL', 'EXCEEDING CYCLE/INSTR LIMIT',
                       'SOME SIGNAL STOPS THE PROGRAM', 'Unknown trap code',
                       'Segmentation fault', 'terminate called after throwing'):
            for negative in (False,True):
                with self.subTest(marker=marker,negative=negative), self.assertRaises(ValueError):
                    gate.validate_failure_markers((fixture(True) if negative else 'normal log')+'\n'+marker,negative=negative)

    def test_good_trap_is_forbidden_in_negative(self):
        for marker in ('HIT GOOD TRAP', '\x1b[32mHIT GOOD TRAP', 'hit good trap'):
            with self.subTest(marker=marker), self.assertRaisesRegex(ValueError,'GOOD TRAP'):
                gate.validate_negative(fixture()+'\n'+marker,1)

    def test_injection_cardinality_and_fields_are_strict(self):
        text=fixture()
        line=text.splitlines()[0]+'\n'
        variants=(text.replace(line,''),text+line,text+line.replace('bit=100','bit=99'),
                  text.replace('bit=100','bit=99'),text.replace('instruction=0x0294050b','instruction=0x02940513'),
                  text.replace('vd=10','vd=11'),text.replace('instruction=0x0294050b','instruction=0x10294050b'),
                  text.replace('pc=0x80001bdc','pc=0x180001bdc0deadbeef0'),
                  text.replace('DIFFTEST_HIGHBIT_NEGATIVE_INJECTED','prefixDIFFTEST_HIGHBIT_NEGATIVE_INJECTED'))
        for bad in variants:
            with self.subTest(bad=bad[:160]), self.assertRaises(ValueError):
                gate.validate_negative(bad,1)

    def test_mismatch_must_bind_pc_vd_and_exactly_bit100(self):
        for before,after in [('pc = 0x0080001bdc','pc = 0x0080001be0'),
                             ('v10_high','v11_high'),('v10_high','v10_low'),
                             ('right= 0x0000001000000000','right= 0x0000002000000000'),
                             ('right= 0x0000001000000000','right= 0x0000001000000001'),
                             ('wrong = 0x0000000000000000','wrong = 0x0000001000000000'),
                             ('right= 0x0000001000000000','right= 0x10000001000000000')]:
            with self.subTest(after=after), self.assertRaises(ValueError):
                gate.validate_negative(fixture().replace(before,after),1)

    def test_duplicate_and_unrelated_mismatches_rejected(self):
        line=fixture().splitlines()[2]+'\n'
        for extra in (line,line.replace('v10_high','v9_high'),'x1 different at pc = 0x80000000\n'):
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError,'exactly one'):
                gate.validate_negative(fixture()+extra,1)

    def test_unsupported_or_truncated_escapes_fail_closed(self):
        for extra in ('\x1b[31','\x1b]0;hidden title\x07','\x9b31m'):
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError,'terminal escape'):
                gate.validate_negative(fixture()+extra,1)

    def test_other_c0_c1_controls_cannot_edit_failure_markers(self):
        for char in ('\b','\x00','\x07','\x7f','\x80','\x9f'):
            for negative in (False,True):
                text=(fixture() if negative else 'normal log\n')+'ABO'+char+'ORT unrelated'
                with self.subTest(control=ord(char),negative=negative), self.assertRaises(ValueError):
                    gate.validate_failure_markers(text,negative=negative)

    def test_normal_success_is_only_marker_clearance(self):
        self.assertIsNone(gate.validate_failure_markers('hello\nHIT GOOD TRAP\n'))
        with self.assertRaises(ValueError):
            gate.validate_failure_markers(fixture())
        with self.assertRaises(ValueError):
            gate.validate_failure_markers('DIFFTEST FAIL',negative=True)

    def test_negative_interface_requires_terminal_abort_even_with_two_valid_markers(self):
        text=fixture().replace('Core 0: ABORT at pc = 0x800016b0\n','')
        with self.assertRaisesRegex(ValueError,'ABORT'):
            gate.validate_failure_markers(text,negative=True)

    def test_cli_negative_actual_exit_and_output_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);log=base/'raw.log';out=base/'receipt.json'
            raw=fixture(True,True).encode();log.write_bytes(raw)
            cmd=[sys.executable,'-B',gate.__file__,'--log',str(log),'--mode','negative',
                 '--exit-code','1','--output',str(out)]
            result=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(out.read_text())['status'],'EXPECTED_BIT100_NEGATIVE_LOG_GATE_PASS')
            self.assertEqual(log.read_bytes(),raw)
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2)
            log.write_text(fixture(True)+'\n\x1b[31mABORT unrelated\n')
            cmd[-1]=str(base/'bad.json')
            result=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            self.assertFalse((base/'bad.json').exists())


if __name__=='__main__':
    unittest.main()
