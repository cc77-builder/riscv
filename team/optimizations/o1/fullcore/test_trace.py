"""Behavioral positive/negative observer fixtures; these do not simulate RTL."""
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import analyze as a
import check_control as control


class Fixture:
    def __init__(self, handoff=1):
        self.header = f'O1_SCHEMA version=1 clock=global latency=2 rob_size=48 ftq_size=8 vlen=128 handoff={handoff}'
        self.rows = []
        self.seq = 0
        self.entries = {}

    def add(self, kind, /, **f):
        self.rows.append('O1_' + kind + ' ' + ' '.join(k + '=' + (hex(v) if k in a.HEXES else str(v)) for k, v in f.items()))

    def enq(self, cycle, rob='0:5', pdest=7, ftq='0:1', pc=0x80000004, vd=10):
        self.add('ENQUEUE', cycle=cycle, rob=rob, pc=pc, ftq=ftq, word=(0x0294050b & ~(31<<7)) | (vd<<7))
        self.entries[rob] = (pdest, ftq, pc)

    def accept(self, cycle, rob='0:5', illegal=0, vl=8, vecwen=1):
        seq = self.seq
        self.seq += 1
        pdest = self.entries[rob][0]
        self.add('VFEX4_ACCEPT', cycle=cycle, seq=seq, rob=rob, fu=a.VDOT, pdest=pdest)
        self.add('ACCEPT', cycle=cycle, seq=seq, rob=rob, pdest=pdest, vl=vl,
                 illegal=illegal, vecwen=vecwen, v0wen=1-vecwen)
        return seq

    def div(self, cycle, rob='0:4'):
        self.add('VFEX4_ACCEPT', cycle=cycle, seq=self.seq, rob=rob, fu=1<<22, pdest=8)
        self.seq += 1

    def output(self, kind, cycle, seq, rob='0:5', illegal=0, data=0xfffffff8, vecwen=1):
        self.add(kind, cycle=cycle, seq=seq, rob=rob, pdest=self.entries[rob][0], illegal=illegal,
                 data=0 if illegal else data, vecwen=0 if illegal else vecwen,
                 v0wen=0 if illegal else 1-vecwen, exception=4 if illegal else 0)

    def commit(self, cycle, rob='0:5'):
        pdest, ftq, pc = self.entries[rob]
        self.add('COMMIT', cycle=cycle, rob=rob, pc=pc, ftq=ftq)

    def redirect(self, cycle, rob='0:4', self_flush=0):
        self.add('REDIRECT', cycle=cycle, rob=rob, ftq='0:1', self=self_flush)
        self.add('VFEX4_REDIRECT', cycle=cycle+1, rob=rob, self=self_flush)

    def kill(self, cycle, seq, rob='0:5', redirect='0:4', self_flush=0, state=2):
        self.add('KILL', cycle=cycle, seq=seq, rob=rob, pdest=self.entries[rob][0],
                 redirect=redirect, self=self_flush, state=state)

    def handoff(self, cycle, oldseq, newseq, oldrob='0:5', newrob='0:6'):
        self.add('HANDOFF', cycle=cycle, oldseq=oldseq, newseq=newseq,
                 oldrob=oldrob, newrob=newrob, oldpdest=self.entries[oldrob][0],
                 newpdest=self.entries[newrob][0], busy=1)

    def text(self):
        rows = sorted(self.rows, key=lambda s: int(s.split('cycle=')[1].split()[0]))
        return self.header + '\n' + '\n'.join(rows) + ('\n' if rows else '')


def handoff_fixture():
    f = Fixture()
    f.div(1)
    f.enq(2)
    f.enq(2, '0:6', 8, pc=0x80000008, vd=0)
    s0 = f.accept(10)
    f.output('RESPONSE', 12, s0)
    s1 = f.accept(12, '0:6', vecwen=0)
    f.handoff(12, s0, s1)
    f.commit(13)
    for cycle in (14, 15):
        f.output('STALL', cycle, s1, '0:6', data=123, vecwen=0)
    f.add('VFEX4_WAIT', cycle=14, rob='0:7', fu=a.VDOT, busy=1)
    f.output('RESPONSE', 16, s1, '0:6', data=123, vecwen=0)
    f.commit(17, '0:6')
    return f


def single_fixture(illegal=False):
    f = Fixture()
    f.enq(1)
    seq = f.accept(2, illegal=int(illegal), vl=7 if illegal else 8)
    f.output('RESPONSE', 4, seq, illegal=int(illegal))
    if illegal:
        f.redirect(6, '0:5', 1)
    else:
        f.commit(5)
    return f


def killed_fixture(age=1):
    f = Fixture()
    f.enq(1)
    seq = f.accept(2)
    for cycle in range(4, 2+age):
        f.output('STALL', cycle, seq)
    f.redirect(1+age)
    f.kill(2+age, seq, state=2 if age == 1 else 3)
    return f


def control_fixture(handoff=True, pressure=True):
    f = killed_fixture()
    f.div(6)
    commits = 0
    for i in range(9):
        base = 20 + i*20
        rob, ftq = f'{i%2}:10', f'{i%2}:2'
        f.enq(base, rob, 7, ftq, 0x80001000 + i*8)
        seq = f.accept(base+1, rob)
        end = base+3
        if pressure:
            f.output('STALL', end, seq, rob)
            f.add('VFEX4_WAIT', cycle=end, rob=f'{i%2}:11', fu=a.VDOT, busy=1)
            end += 1
        f.output('RESPONSE', end, seq, rob)
        f.commit(end+1, rob)
        commits += 1
        if i == 0 and handoff:
            f.enq(base, '0:11', 9, ftq, 0x80001004)
            newseq = f.accept(end, '0:11')
            f.handoff(end, seq, newseq, rob, '0:11')
            f.output('RESPONSE', end+2, newseq, '0:11')
            f.commit(end+3, '0:11')
            commits += 1
    text = ('The reference model is /synthetic/ref.so\n'
            'The first instruction of core 0 has commited. Difftest enabled.\n' + f.text() +
            'T12_BEGIN seed=0x20261014 contract=vdot-s8x8-r32-v0.1\n' +
            ''.join(f'T12_GROUP_PASS id={i} checkpoints=32 bytes=16384\n' for i in range(4)) +
            'T12_SUMMARY groups=4 checkpoints=128 speculative_attempts=256 failures=0\nHIT GOOD TRAP\n')
    return text, {'groups':[{'vdot_count':commits}], 'speculation':{'expected_architectural_vdot':0}}


def replace_line(text, prefix, transform):
    rows = text.splitlines(keepends=True)
    for i, line in enumerate(rows):
        if line.startswith(prefix):
            rows[i] = transform(line)
            return ''.join(rows)
    raise AssertionError('missing fixture prefix ' + prefix)


class TraceTests(unittest.TestCase):
    def test_real_handoff_identity_with_div_sequence_gap(self):
        result = a.analyze(handoff_fixture().text())
        self.assertEqual(result['status'], 'O1_TRACE_PASS')
        self.assertEqual(result['counts']['HANDOFF'], 1)
        self.assertEqual([t['seq'] for t in result['transactions']], [1, 2])
        self.assertEqual(result['response_latency_histogram'], {'2':1, '4':1})
        self.assertEqual(result['counts']['STALL'], 2)

    def test_same_cycle_print_order_is_irrelevant(self):
        text = handoff_fixture().text()
        rows = [line for line in text.splitlines() if 'cycle=12 ' in line]
        prefix = text[:text.index(rows[0])]
        suffix = text[text.index(rows[-1])+len(rows[-1])+1:]
        wanted = a.analyze(text)
        wanted.pop('input_sha256')
        for permutation in itertools.permutations(rows):
            result = a.analyze(prefix + '\n'.join(permutation) + '\n' + suffix)
            result.pop('input_sha256')
            self.assertEqual(result, wanted)

    def test_illegal_full_result_and_self_redirect(self):
        result = a.analyze(single_fixture(True).text())
        self.assertEqual(result['counts']['COMMIT'], 0)
        self.assertEqual(result['counts']['ACCEPTED_THEN_SQUASHED'], 1)
        self.assertEqual(result['counts']['ACCEPTED_YOUNGER_SQUASHED'], 0)

    def test_kills_at_each_fused_stage(self):
        for age in (1, 2, 3, 7):
            with self.subTest(age=age):
                result = a.analyze(killed_fixture(age).text())
                self.assertEqual(result['counts']['KILL'], 1)
                self.assertEqual(result['counts']['STALL'], max(0, age-2))

    def test_current_rob_redirect_allows_handoff_before_real_flush(self):
        f = handoff_fixture()
        f.rows = [line for line in f.rows if not ('rob=0:6' in line and line.startswith(('O1_STALL ', 'O1_RESPONSE ', 'O1_COMMIT ')))]
        f.rows = [line for line in f.rows if not line.startswith('O1_VFEX4_WAIT')]
        f.redirect(12, '0:5')
        f.kill(13, 2, '0:6', '0:5')
        result = a.analyze(f.text())
        self.assertEqual(result['counts']['HANDOFF'], 1)
        self.assertEqual(result['counts']['KILL'], 1)

    def test_empty_hello_still_requires_schema(self):
        self.assertEqual(a.analyze(Fixture().text())['counts']['ACCEPT'], 0)
        with self.assertRaises(ValueError):
            a.analyze('HIT GOOD TRAP\n')

    def test_no_handoff_baseline_schema_remains_supported(self):
        self.assertEqual(a.analyze(single_fixture().text().replace('handoff=1', 'handoff=0'))['schema']['handoff'], 0)
        with self.assertRaisesRegex(ValueError, 'handoff'):
            a.analyze(handoff_fixture().text().replace('handoff=1', 'handoff=0'))

    def test_partial_is_explicit_and_still_strict(self):
        f = Fixture()
        f.enq(1)
        f.accept(2)
        with self.assertRaisesRegex(ValueError, 'unfinished'):
            a.analyze(f.text())
        result = a.analyze(f.text(), require_complete=False)
        self.assertEqual(result['status'], 'O1_PARTIAL_TRACE_AUDIT')
        self.assertEqual(result['pending_count'], 1)
        with self.assertRaisesRegex(ValueError, 'parent/child'):
            a.analyze(f.text().replace('O1_ACCEPT cycle=2 seq=0 rob=0:5 pdest=7', 'O1_ACCEPT cycle=2 seq=0 rob=0:5 pdest=8'), require_complete=False)

    def test_partial_redirect_tail_does_not_require_unobserved_next_tick(self):
        f = Fixture()
        f.enq(1)
        f.add('REDIRECT', cycle=2, rob='0:4', ftq='0:1', self=0)
        self.assertEqual(a.analyze(f.text(), require_complete=False)['status'], 'O1_PARTIAL_TRACE_AUDIT')
        with self.assertRaisesRegex(ValueError, 'next-cycle'):
            a.analyze(f.text())

    def test_strip_interleaved_o1_and_t13_without_touching_uart(self):
        f = Fixture().text()
        trace = 'O1_VFEX4_WAIT cycle=10 rob=0:2 fu=0x400000 busy=0\n'
        t13 = 'T13_CSR_SAMPLE cycle= 11 addr=0xc00 data=0x22 wen=0\n'
        events, uart = a.extract_events_and_uart(f + 'T12_GROUP_' + trace + 'PASS id=0\n' + t13)
        self.assertEqual(uart, 'T12_GROUP_PASS id=0\n')
        self.assertEqual(events[-1][2], 'VFEX4_WAIT')

    def test_malformed_schema_and_event_fields(self):
        text = single_fixture().text()
        edits = [('version=1', 'version=2'), ('clock=global', 'clock=gated'),
                 ('rob_size=48', 'rob_size=64'), ('ftq_size=8', 'ftq_size=16'),
                 ('latency=2', 'latency=3'), ('vlen=128', 'vlen=256'),
                 ('handoff=1', 'handoff=2'), ('pdest=7 vl=8', 'pdest=7 pdest=8 vl=8'),
                 ('pdest=7 vl=8', 'vl=8'), ('rob=0:5', 'rob=0:48'),
                 ('ftq=0:1', 'ftq=0:8'), ('illegal=0', 'illegal=2'),
                 ('cycle=2', 'cycle=-2'), ('data=0xfffffff8', 'data=0x'+'1'*33)]
        for before, after in edits:
            with self.subTest(after=after), self.assertRaises(ValueError):
                a.analyze(text.replace(before, after, 1))

    def test_unknown_truncated_duplicate_and_legacy_records(self):
        text = single_fixture().text()
        for suffix in ('O1_UNKNOWN x=1\n', 'O1_RESPONSE', 'O1_',
                       'T13_CSR_SAMPLE cycle=10', 'T13_UNKNOWN x=1\n',
                       'T12_ACCEPT cycle=2 rob=0:5 pdest=7 vl=8 illegal=0\n',
                       text.splitlines()[0]+'\n', text.splitlines()[1]+'\n'):
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                a.analyze(text + suffix)

    def test_wrong_old_identity_wen_exception_and_data(self):
        text = handoff_fixture().text()
        for before, after in [('seq=1','seq=2'), ('rob=0:5','rob=0:6'), ('pdest=7','pdest=8'),
                              ('vecwen=1 v0wen=0','vecwen=0 v0wen=1'), ('exception=0x0','exception=0x4'),
                              ('illegal=0','illegal=1'), ('data=0xfffffff8','data=0x1fffffff8')]:
            bad = replace_line(text, 'O1_RESPONSE cycle=12 ', lambda x:x.replace(before,after))
            with self.subTest(after=after), self.assertRaises(ValueError):
                a.analyze(bad)

    def test_parent_child_missing_duplicate_and_sequence_errors(self):
        text = handoff_fixture().text()
        for prefix in ('O1_VFEX4_ACCEPT cycle=12', 'O1_ACCEPT cycle=12', 'O1_RESPONSE cycle=12', 'O1_HANDOFF cycle=12'):
            with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                a.analyze(replace_line(text, prefix, lambda x:''))
        for before, after in [('seq=2','seq=3'), ('pdest=8','pdest=9'), ('rob=0:6','rob=0:7'), ('fu=0x800000000','fu=0x400000')]:
            bad = replace_line(text, 'O1_VFEX4_ACCEPT cycle=12', lambda x:x.replace(before,after))
            with self.subTest(after=after), self.assertRaises(ValueError):
                a.analyze(bad)

    def test_handoff_fields_must_exactly_identify_both_transactions(self):
        text = handoff_fixture().text()
        for before, after in [('oldseq=1','oldseq=2'), ('newseq=2','newseq=1'),
                              ('oldrob=0:5','oldrob=0:6'), ('newrob=0:6','newrob=0:5'),
                              ('oldpdest=7','oldpdest=8'), ('newpdest=8','newpdest=7'), ('busy=1','busy=0')]:
            with self.subTest(after=after), self.assertRaisesRegex(ValueError, 'handoff'):
                a.analyze(replace_line(text, 'O1_HANDOFF', lambda x:x.replace(before,after)))

    def test_stalled_snapshot_and_exact_latency_history(self):
        text = handoff_fixture().text()
        for prefix, before, after in [('O1_STALL cycle=15', 'data=0x7b','data=0x7c'),
                                      ('O1_RESPONSE cycle=16', 'data=0x7b','data=0x7c'),
                                      ('O1_STALL cycle=14', 'pdest=8','pdest=9')]:
            with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                a.analyze(replace_line(text,prefix,lambda x:x.replace(before,after)))
        with self.assertRaisesRegex(ValueError, 'history'):
            a.analyze(replace_line(text,'O1_STALL cycle=14',lambda x:''))
        early = single_fixture().text().replace('O1_RESPONSE cycle=4','O1_RESPONSE cycle=3')
        with self.assertRaisesRegex(ValueError, 'precedes'):
            a.analyze(early)

    def test_wrong_kill_redirect_state_or_missing_flush_is_rejected(self):
        text = killed_fixture(3).text()
        for prefix, before, after in [('O1_KILL', 'redirect=0:4','redirect=0:6'),
                                      ('O1_KILL', 'state=3','state=2'),
                                      ('O1_KILL', 'self=0','self=1'),
                                      ('O1_VFEX4_REDIRECT', 'rob=0:4','rob=0:5')]:
            with self.subTest(after=after), self.assertRaises(ValueError):
                a.analyze(replace_line(text,prefix,lambda x:x.replace(before,after)))
        for prefix in ('O1_KILL', 'O1_REDIRECT', 'O1_VFEX4_REDIRECT', 'O1_STALL'):
            with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                a.analyze(replace_line(text,prefix,lambda x:''))

    def test_cancelled_illegal_or_unbound_commit_rejected(self):
        for f in (killed_fixture(), single_fixture(True)):
            f.commit(10)
            with self.assertRaises(ValueError):
                a.analyze(f.text())
        text = single_fixture().text()
        for prefix in ('O1_ENQUEUE', 'O1_RESPONSE'):
            with self.assertRaises(ValueError):
                a.analyze(replace_line(text,prefix,lambda x:''))
        with self.assertRaisesRegex(ValueError, 'identity'):
            a.analyze(replace_line(text,'O1_COMMIT',lambda x:x.replace('pc=0x80000004','pc=0x80000008')))

    def test_reused_rob_has_new_allocation_and_sequence(self):
        f = single_fixture()
        f.enq(6, pdest=9, pc=0x80000008)
        seq = f.accept(7)
        f.output('RESPONSE',9,seq)
        f.commit(10)
        self.assertEqual(a.analyze(f.text())['counts']['COMMIT'], 2)
        bad = replace_line(f.text(), 'O1_RESPONSE cycle=9', lambda x:x.replace('seq=1','seq=0'))
        with self.assertRaisesRegex(ValueError, 'identity'):
            a.analyze(bad)

    def test_global_cycles_cannot_be_sorted_to_hide_reversal(self):
        text = single_fixture().text()
        rows = text.splitlines()
        with self.assertRaisesRegex(ValueError, 'out of order'):
            a.analyze(rows[0] + '\n' + '\n'.join(reversed(rows[1:]))+'\n')

    def test_input_wen_must_match_encoded_architectural_destination(self):
        text = single_fixture().text()
        text = replace_line(text, 'O1_ACCEPT', lambda x:x.replace('vecwen=1 v0wen=0','vecwen=0 v0wen=1'))
        text = replace_line(text, 'O1_RESPONSE', lambda x:x.replace('vecwen=1 v0wen=0','vecwen=0 v0wen=1'))
        with self.assertRaisesRegex(ValueError, 'decoded destination'):
            a.analyze(text)

    def test_parent_flush_forbids_new_accept_even_when_old_request_is_older(self):
        f = Fixture()
        f.enq(1)
        f.redirect(2, '0:6')
        seq = f.accept(3)
        f.output('RESPONSE',5,seq)
        f.commit(6)
        with self.assertRaisesRegex(ValueError, 'parent flush'):
            a.analyze(f.text())

    def test_false_enqueue_during_rob_redirect_is_rejected(self):
        f = Fixture()
        f.redirect(1)
        f.enq(1)
        with self.assertRaisesRegex(ValueError, 'ROB redirect gate'):
            a.analyze(f.text())

    def test_partial_mode_cannot_hide_missing_stalls_before_eof(self):
        f = Fixture()
        f.enq(1)
        f.accept(2)
        f.add('VFEX4_WAIT', cycle=10, rob='0:6', fu=a.VDOT, busy=1)
        with self.assertRaisesRegex(ValueError, 'already-observed'):
            a.analyze(f.text(), require_complete=False)

    def test_div_cannot_replace_vdot_in_same_cycle_handoff(self):
        f = single_fixture()
        f.div(4)
        with self.assertRaisesRegex(ValueError, 'non-vdot handoff'):
            a.analyze(f.text())

    def test_cli_returns_nonzero_and_never_writes_pass_for_bad_trace(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            log, out = path/'run.log', path/'out.json'
            log.write_text(single_fixture().text())
            cmd = [sys.executable, '-B', str(Path(a.__file__)), str(log), '--output', str(out)]
            good = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertEqual(json.loads(out.read_text())['status'], 'O1_TRACE_PASS')
            bad = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)
            log.write_text('bad log\n')
            bad = subprocess.run(cmd[:-2], capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)
            self.assertNotIn('O1_TRACE_PASS', bad.stdout)


class ControlTests(unittest.TestCase):
    def test_all_obligations_pass(self):
        text, manifest = control_fixture()
        result = control.check(text, manifest, 0)
        self.assertEqual(result['status'], 'O1_CONTROL_REGRESSION_PASS')
        self.assertTrue(all(result['coverage'].values()))

    def test_missing_handoff_is_only_coverage_incomplete(self):
        text, manifest = control_fixture(handoff=False)
        result = control.check(text, manifest, 0)
        self.assertEqual(result['status'], 'O1_COVERAGE_INCOMPLETE')
        self.assertTrue(result['legacy_coverage_complete'])
        self.assertFalse(result['handoff_coverage_complete'])

    def test_missing_old_pressure_obligation_remains_incomplete(self):
        text, manifest = control_fixture(pressure=False)
        result = control.check(text, manifest, 0)
        self.assertEqual(result['status'], 'O1_COVERAGE_INCOMPLETE')
        self.assertFalse(result['legacy_coverage_complete'])

    def test_exit_summary_banner_counts_and_manifest_are_strict(self):
        text, manifest = control_fixture()
        for before, after in [('T12_SUMMARY','T12_SUMMARY_DUP'), ('failures=0','failures=01'),
                              ('T12_GROUP_PASS id=2','T12_GROUP_PASS id=3'),
                              ('Difftest enabled.','Difftest disabled.'), ('HIT GOOD TRAP','HIT BAD TRAP')]:
            with self.subTest(after=after), self.assertRaises(ValueError):
                control.check(text.replace(before,after),manifest,0)
        for rc in (1, 124, -9):
            with self.assertRaises(ValueError):
                control.check(text,manifest,rc)
        with self.assertRaises(ValueError):
            control.check(text, {'groups':[{'vdot_count':999}], 'speculation':{'expected_architectural_vdot':0}}, 0)

    def test_cached_trace_must_bind_to_original_text_and_complete_status(self):
        text, manifest = control_fixture()
        analysis = a.analyze(text)
        self.assertEqual(control.check(text,manifest,0,analysis)['status'], 'O1_CONTROL_REGRESSION_PASS')
        with self.assertRaisesRegex(ValueError, 'different raw'):
            control.check(text+'suffix\n',manifest,0,analysis)
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            control.check(text,manifest,0,a.analyze(text,require_complete=False))


if __name__ == '__main__':
    unittest.main()
