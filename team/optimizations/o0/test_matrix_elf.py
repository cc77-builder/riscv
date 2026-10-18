"""Recheck real compiled matrix bytes and reject reduced work/corrupted state.

These ELF files were compiled with GNU tools; none is DUT execution evidence.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tarfile
import tempfile
import unittest

import compile_matrix as compiler


class CompiledMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        bundle = compiler.ROOT/'team/evidence/o0-progress-20261017/matrix-images.tar.gz'
        if hashlib.sha256(bundle.read_bytes()).hexdigest() != '9a15c18502ac745aec60a6c29ddcfe7e6bced58d6026156c2034294add5398de':
            raise ValueError('compiled test fixture changed')
        with tarfile.open(bundle) as archive:
            for entry in archive.getmembers():
                if entry.isfile() and entry.name.startswith('matrix-') and entry.name.endswith(('vdot-perf.elf', 'manifest.json')):
                    dest = cls.root/entry.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(archive.extractfile(entry).read())
        spec = importlib.util.spec_from_file_location('matrix_elf_checker', compiler.ROOT/'team/workloads/unified-vdot/check.py')
        cls.checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.checker)
        cls.build = cls.root/'matrix-d0-s00'
        cls.manifest = json.loads((cls.build/'data/manifest.json').read_text())
        cls.original = (cls.build/'vdot-perf.elf').read_bytes()

    def reject_mutation(self, original, replacement, message):
        data = bytearray(self.original)
        self.assertEqual(data.count(original), 1, 'mutation must target one exact ELF sequence')
        at = data.index(original)
        data[at:at+len(original)] = replacement
        path = self.root/'mutated.elf'
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, message):
            compiler.check_elf(self.checker, path, self.manifest)

    def test_all_18_real_images_have_full_state_and_256_dot_paths(self):
        builds = sorted(self.root.glob('matrix-d*-s*'))
        self.assertEqual(len(builds), 18)
        for build in builds:
            with self.subTest(image=build.name):
                manifest = json.loads((build/'data/manifest.json').read_text())
                self.assertEqual(len(compiler.check_elf(self.checker, build/'vdot-perf.elf', manifest)), 2)

    def test_wrong_destination_is_rejected_even_with_256_dots(self):
        word = 0x0200000b | 24 << 7 | 8 << 15 | 9 << 20
        self.reject_mutation(struct.pack('<I', word), struct.pack('<I', word ^ (1 << 7)), 'operand mismatch')

    def test_255_dot_loop_is_rejected(self):
        # li t6,256 followed by the custom instruction uniquely selects vdot.
        word = 0x0200000b | 24 << 7 | 8 << 15 | 9 << 20
        original = struct.pack('<II', 0x10000f93, word)
        self.reject_mutation(original, struct.pack('<II', 0x0ff00f93, word), 'vdot work mismatch')

    def test_high_result_byte_corruption_is_rejected(self):
        row = self.manifest['rows'][0]
        # Distinguish the two methods' adjacent constants before their identical vectors.
        constants = struct.pack('<6I', row['iterations'], row['dots'], 0, row['vtype'], 0, row['operands'][0])
        data = bytearray(self.original)
        candidates = [i for i in range(len(data)) if data.startswith(constants, i)
                      and data[i+48:i+560] == bytes.fromhex(''.join(row['before']))]
        self.assertEqual(len(candidates), 1)
        at = candidates[0] + 560 + 24*16 + 12
        data[at] ^= 1
        path = self.root/'corrupted-golden.elf'
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'compiled full-register golden bytes'):
            compiler.check_elf(self.checker, path, self.manifest)


if __name__ == '__main__':
    unittest.main()
