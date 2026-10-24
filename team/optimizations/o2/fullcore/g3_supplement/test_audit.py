"""Composition refusal tests using the sealed real verdicts, without an EMU."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import audit

ROOT = Path(__file__).resolve().parents[5]
EVIDENCE = ROOT / 'team/evidence'


class SupplementTests(unittest.TestCase):
    def setUp(self):
        self.core = json.loads((EVIDENCE / 'merge-reg-20261023/campaign/recheck-result.json').read_bytes())
        self.partial = json.loads((EVIDENCE / 'partial-dependency-admission-20261024/result.json').read_bytes())

    def test_real_policy_and_no_negative_coverage(self):
        result = audit.combine(self.core, self.partial)
        self.assertTrue(result['g3_complete'])
        self.assertEqual(result['new_emu_runs'], 0)
        self.assertEqual([sum(x['count'] for x in result['coverage_sources'][k]) for k in audit.TARGETS],
                         [2786, 2104, 13, 41, 30, 5])
        bad = next(x for x in self.core['runs'] if x['name'] == 'negative-vdot')
        bad['observation_counts']['PARTIAL_KILL'] = 999
        self.assertEqual(audit.combine(self.core, self.partial), result)

    def test_core_missing_recovery_and_identity(self):
        for key, value in [('normal_reference_recovery', False), ('core_regression_pass', False),
                           ('supplements_pass', False), ('completed_only', True), ('emu_sha256', 'wrong'),
                           ('hardware_pins_sha256', 'wrong'), ('build_source_commit', 'wrong'),
                           ('original_evidence_unchanged', False), ('missing_jobs', ['control'])]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                candidate = copy.deepcopy(self.core)
                candidate[key] = value
                audit.combine(candidate, self.partial)

    def test_missing_duplicate_failed_and_partial_jobs(self):
        for action in ('remove', 'duplicate', 'failed', 'partial'):
            with self.subTest(action=action), self.assertRaises(ValueError):
                candidate = copy.deepcopy(self.core)
                if action == 'remove': candidate['runs'].pop()
                if action == 'duplicate': candidate['runs'][-1] = candidate['runs'][0]
                if action == 'failed': candidate['runs'][0]['status'] = 'FAILED'
                if action == 'partial': candidate['runs'][0]['observation_status'] = 'O2_PARTIAL_TRACE_AUDIT'
                audit.combine(candidate, self.partial)

    def test_original_supplements_required(self):
        for key, value in [('status', 'PASS'), ('emu_sha256', 'wrong'), ('hardware_pins_sha256', 'wrong'),
                           ('records', []), ('records', self.core['supplement_audit']['records'] * 2)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                candidate = copy.deepcopy(self.core)
                candidate['supplement_audit'][key] = value
                audit.combine(candidate, self.partial)

    def test_partial_target_architecture_and_full_width_required(self):
        for key, value in [('status', 'PARTIAL_V5_FUNCTIONAL_PASS_COVERAGE_MISSING'),
                           ('architectural_pass', False), ('target_covered', False), ('target_windows', 0),
                           ('target_windows', True), ('checked_register_bytes', 512), ('campaign_acceptance', True)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                candidate = copy.deepcopy(self.partial)
                candidate[key] = value
                audit.combine(self.core, candidate)

    def test_counter_forgery_and_inconsistent_coverage(self):
        for value in (-1, True, '13', 0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                candidate = copy.deepcopy(self.core)
                next(r for r in candidate['runs'] if r['name'] == 'control')['observation_counts']['FULL_STALL'] = value
                audit.combine(candidate, self.partial)
        for key, value in [('PARTIAL_KILL', 99), ('PARTIAL_KILL', True), ('COMMIT', 111)]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                candidate = copy.deepcopy(self.partial)
                candidate['counts'][key] = value
                audit.combine(self.core, candidate)

    def test_output_protects_existing_ancestor_and_descendant(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            protected = base / 'input'
            protected.mkdir()
            for output in (base, protected, protected / 'new', Path('relative')):
                with self.subTest(output=output), self.assertRaises(ValueError):
                    audit.output_guard(output, [protected])
            audit.output_guard(base / 'new', [protected])

    def test_output_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            protected = base / 'input'
            protected.mkdir()
            link = base / 'alias'
            try:
                link.symlink_to(protected, target_is_directory=True)
            except OSError:
                self.skipTest('host cannot create symlinks')
            with self.assertRaises(ValueError):
                audit.output_guard(link / 'new', [protected])

    def test_capsule_refuses_unrecognized_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / audit.CAPSULES['partial'][0]
            folder.mkdir(parents=True)
            (folder / 'manifest.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'unrecognized'):
                audit.Capsule(directory, 'partial')

    def test_recognized_manifest_rejects_corrupt_payload_before_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            relative = audit.CAPSULES['partial'][0]
            folder = Path(directory) / relative
            folder.mkdir(parents=True)
            manifest = (EVIDENCE / relative / 'manifest.json').read_bytes()
            (folder / 'manifest.json').write_bytes(manifest)
            first = json.loads(manifest)['payloads'][0]['path']
            (folder / first).write_bytes(b'changed evidence')
            with self.assertRaisesRegex(ValueError, 'payload drift'):
                audit.Capsule(directory, 'partial')

    def test_native_source_must_equal_archived_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'run.log'
            source.write_bytes(b'original')
            capsule = object.__new__(audit.Capsule)
            capsule.rows = {'run/run.log': dict(source=str(source), sha256=audit.digest(b'original'))}
            self.assertEqual(capsule.native(('run/',)), 1)
            source.write_bytes(b'altered')
            with self.assertRaisesRegex(ValueError, 'native/archive mismatch'):
                capsule.native(('run/',))


if __name__ == '__main__':
    unittest.main()
