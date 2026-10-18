"""Independent math, register budget and frozen-emitter compatibility checks."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

import generate_matrix as matrix


def oracle(a, b):
    a, b = bytes.fromhex(a), bytes.fromhex(b)
    total = sum(int.from_bytes(a[i:i+1], 'little', signed=True) *
                int.from_bytes(b[i:i+1], 'little', signed=True) for i in range(8))
    return ((total % (1 << 32)).to_bytes(4, 'little') + bytes(12)).hex()


class MatrixTests(unittest.TestCase):
    def test_full_math_state_and_decoded_instruction_operands(self):
        for dataset in range(3):
            rows, _ = matrix.corpus(dataset)
            for row in rows:
                with self.subTest(dataset=dataset, case=row['id']):
                    expected = list(row['before'])
                    dests, inputs = set(), set()
                    for d, a, b in row['lane_operands']:
                        dests.add(d)
                        inputs.update((a, b))
                        expected[d] = oracle(row['before'][a], row['before'][b])
                    self.assertFalse(dests & inputs)
                    self.assertFalse(set(row['scratch']) & (dests | inputs))
                    self.assertEqual(row['expected'], expected)
                    self.assertEqual(row['iterations'] * len(dests), 256)
                    if row['method'] == 'vdot':
                        words = [int(s.split()[1], 16) for s in row['body'] if s.startswith('.word')]
                        decoded = [[(w >> 7) & 31, (w >> 15) & 31, (w >> 20) & 31] for w in words]
                        self.assertEqual(decoded, row['lane_operands'])
                        self.assertTrue(all(w & 0xfe00707f == 0x0200000b for w in words))

    def test_pairing_and_abba_all_phases(self):
        for dataset in range(3):
            rows, plan = matrix.corpus(dataset)
            self.assertEqual(len(rows), 12)
            self.assertEqual(len(plan), 72)
            self.assertEqual(Counter(p['phase'] for p in plan), {'first': 12, 'warmup': 12, 'measured': 48})
            for i in range(0, 12, 2):
                self.assertEqual(rows[i]['before'], rows[i+1]['before'])
                self.assertEqual(rows[i]['expected'], rows[i+1]['expected'])
                methods = [rows[p['index']]['method'] for p in plan if p['index'] in (i, i+1)]
                self.assertEqual(methods, ['vdot', 'rvv', 'rvv', 'vdot'] * 3)

    def test_distinct_input_values_and_one_lane_control(self):
        for dataset in range(3):
            rows, _ = matrix.corpus(dataset)
            for row in rows:
                pairs = {(row['before'][a][:16], row['before'][b][:16]) for _, a, b in row['lane_operands']}
                self.assertEqual(len(pairs), row['lanes'] if row['input_mode'] == 'different' else 1)
            self.assertEqual(rows[0]['before'], rows[2]['before'])
            self.assertEqual(rows[0]['body'], rows[2]['body'])

    def test_six_shards_preserve_work_and_repetitions(self):
        with tempfile.TemporaryDirectory() as temp:
            coordinates = set()
            for shard in range(6):
                result = matrix.generate(Path(temp)/str(shard), 2, shard, 6)
                self.assertEqual(len(result['rows']), 2)
                self.assertEqual(len(result['plan']), 12)
                self.assertEqual(result['diagnostic']['status'], 'GENERATED_NOT_HARDWARE_VALIDATED')
                coordinates.add(result['rows'][0]['scenario'])
                for name, digest in result['files'].items():
                    raw = (Path(temp)/str(shard)/name).read_bytes()
                    self.assertNotIn(b'\r', raw)
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            self.assertEqual(len(coordinates), 6)

    def test_invalid_coordinates_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            for dataset, shard, shards in [(True, 0, 1), (-1, 0, 1), (3, 0, 1), (0, 0, 3), (0, 6, 6)]:
                with self.subTest(dataset=dataset, shard=shard, shards=shards), self.assertRaises(ValueError):
                    matrix.generate(Path(temp)/'invalid', dataset, shard, shards)

    def test_emitter_refactor_preserves_all_64_frozen_images(self):
        bundle = matrix.ROOT/'team/evidence/unified-vdot-20261017/archive/测试镜像与构建快照.tar.gz'
        g = matrix.emitter()
        with tempfile.TemporaryDirectory() as temp, tarfile.open(bundle) as archive:
            count = 0
            for entry in archive.getmembers():
                if not entry.name.endswith('/data/manifest.json'):
                    continue
                saved = json.load(archive.extractfile(entry))
                fresh = g.generate(Path(temp)/str(count), saved['suite'], saved['dataset'], saved['shard'], saved['shards'], True, saved['variant'])
                self.assertEqual(fresh, saved)
                count += 1
            self.assertEqual(count, 64)


if __name__ == '__main__':
    unittest.main()
