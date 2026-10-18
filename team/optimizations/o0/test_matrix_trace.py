"""Mutation checks on a real newly executed matrix pilot, not synthetic logs."""
import hashlib
import json
from pathlib import Path
import re
import tarfile
import unittest

import matrix_check as check
import test_matrix_runtime as build_fixture


class RealTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reuse the authenticated build fixture setup, without inheriting tests.
        build_fixture.RuntimeGateTests.setUpClass.__func__(cls)
        bundle = check.ROOT/'team/evidence/o0-baseline-20261018/pilot-run.tar.gz'
        cls.originals = {}
        with tarfile.open(bundle) as archive:
            for entry in archive:
                if entry.isfile() and entry.name in ('result.json', 'check.json', 'stdout.log', 'stderr.log'):
                    if entry.name in cls.originals:
                        raise ValueError('duplicate pilot member')
                    cls.originals[entry.name] = archive.extractfile(entry).read()
        if hashlib.sha256(cls.originals['result.json']).hexdigest() != '2fceb8e247200ab70628dc3008b7064e7ab1d8cc5e1f48391ba50a10255cb8b1':
            raise ValueError('pilot receipt changed')

    def setUp(self):
        self.run = self.root/self.id().rsplit('.', 1)[-1]
        self.run.mkdir()
        for name, raw in self.originals.items():
            (self.run/name).write_bytes(raw)

    def change_stream(self, name, change):
        raw = change(self.originals[name])
        self.assertNotEqual(raw, self.originals[name], 'mutation did not alter the stream')
        (self.run/name).write_bytes(raw)
        receipt = json.loads(self.originals['result.json'])
        receipt['raw_sha256'][name] = hashlib.sha256(raw).hexdigest()
        (self.run/'result.json').write_text(json.dumps(receipt), encoding='utf-8')

    def test_actual_full_run_passes(self):
        self.assertEqual(check.verify(self.build, self.run, external=True), json.loads(self.originals['check.json']))

    def test_missing_retired_dot_rejected_after_rehashing_stream(self):
        self.change_stream('stderr.log', lambda raw: re.sub(rb'^T13_RETIRE[^\n]*word=0x02940c0b[^\n]*\n', b'', raw, count=1, flags=re.M))
        with self.assertRaisesRegex(ValueError, 'retirement PC/word mismatch'):
            check.verify(self.build, self.run, external=True)

    def test_high_96_bit_response_rejected_after_rehashing_stream(self):
        self.change_stream('stderr.log', lambda raw: re.sub(rb'(^T12_RESPONSE[^\n]*data=)0x[0-9a-f]+',
                                                           rb'\g<1>0x10000000000000000000000000', raw, count=1, flags=re.M))
        with self.assertRaisesRegex(ValueError, 'nonzero high 96 result bits'):
            check.verify(self.build, self.run, external=True)

    def test_uart_cycles_must_match_live_counter_trace(self):
        self.change_stream('stdout.log', lambda raw: raw.replace(b'T13_P seq=0 c=1563', b'T13_P seq=0 c=1562', 1))
        with self.assertRaisesRegex(ValueError, 'UART/trace delta disagreement'):
            check.verify(self.build, self.run, external=True)

    def test_runtime_negative_controls_are_required(self):
        self.change_stream('stdout.log', lambda raw: raw.replace(b'T13_CONTROLS detected=6', b'T13_CONTROLS detected=5', 1))
        with self.assertRaisesRegex(ValueError, 'negative controls'):
            check.verify(self.build, self.run, external=True)


if __name__ == '__main__':
    unittest.main()
