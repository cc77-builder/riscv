"""An attacker-controlled build receipt must not authorize Python execution."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import check

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('unified_trust_test', ROOT/'team/workloads/unified-vdot/check.py')
unified = importlib.util.module_from_spec(spec)
spec.loader.exec_module(unified)


class GeneratorTrustTests(unittest.TestCase):
    def test_self_signed_payload_rejected_before_execution(self):
        for checker in (check, unified):
            for injected in (False, True):
                with self.subTest(checker=checker.__name__, appended=injected), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    (root/'source').mkdir()
                    sentinel = root/'executed'
                    payload = f"\nfrom pathlib import Path\nPath({str(sentinel)!r}).write_text('executed')\n".encode()
                    if injected:
                        family = 'vdot-perf' if checker is check else 'unified-vdot'
                        payload = (ROOT/f'team/workloads/{family}/generate.py').read_bytes() + payload
                    recorded = {}
                    for name in ('generate.py', 'main.c', 'Makefile', 'fixed-layout.ld'):
                        data = payload if name == 'generate.py' else b'fixture'
                        (root/'source'/name).write_bytes(data)
                        recorded[name] = hashlib.sha256(data).hexdigest()
                    (root/'build.json').write_text(json.dumps({'software': recorded}))
                    with self.assertRaisesRegex(ValueError, 'unreviewed generator'):
                        checker.verify_generation(root, {})
                    self.assertFalse(sentinel.exists())

    def test_reviewed_sources_and_cross_family_rejection(self):
        for family in check.TRUSTED_GENERATORS:
            data=(ROOT/f'team/workloads/{family}/generate.py').read_bytes().replace(b'\r\n',b'\n')
            with tempfile.TemporaryDirectory() as tmp:
                source=Path(tmp)/'generate.py'
                for encoded in (data, data.replace(b'\n',b'\r\n')):
                    source.write_bytes(encoded)
                    self.assertEqual(check.trusted_generator_source(source, family), data)
                    other = 'unified-vdot' if family == 'vdot-perf' else 'vdot-perf'
                    with self.assertRaisesRegex(ValueError, 'unreviewed generator'):
                        check.trusted_generator_source(source, other)

    def test_source_size_is_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'generate.py'
            source.write_bytes(b' '*(128*1024+1))
            with self.assertRaisesRegex(ValueError, 'size limit'):
                check.trusted_generator_source(source,'vdot-perf')

    def test_empty_window_cannot_claim_rvv_work(self):
        import test_check
        for checker in (check, unified):
            events, manifest, kernels = test_check.CounterTests().fixture()
            manifest.update(custom_match=0x0200000b, custom_mask=0xfe00707f)
            manifest['rows'][0].update(method='rvv', n=128, dots=128)
            with self.assertRaisesRegex(ValueError, 'RVV dot work count'):
                checker.trace_windows(events, manifest, kernels)

    def test_real_rvv_machine_path_missing_or_wrong_operation(self):
        build=ROOT/'team/evidence/t13-performance-20261015/images-v3/performance-d0-s06'
        manifest=json.loads((build/'data/manifest.json').read_text())
        kernels=check.elf_kernels(build/'vdot-perf.elf')
        for index, row in enumerate(manifest['rows']):
            if row['method'] != 'rvv':
                continue
            path=check.walk(kernels[index])
            check.verify_rvv_work(path,row)
            for opcode in (0xec002057, 0xc4000057):
                victim=next(i for i,(_,w) in enumerate(path) if w & 0xfc00707f == opcode)
                for replacement in ([], [(path[victim][0], 0x13)]):
                    changed=path[:victim]+replacement+path[victim+1:]
                    with self.assertRaisesRegex(ValueError, 'RVV dot work count'):
                        check.verify_rvv_work(changed,row)


if __name__ == '__main__':
    unittest.main()
