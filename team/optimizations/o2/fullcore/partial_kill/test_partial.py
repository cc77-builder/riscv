import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import check
import generate
import run


class DirectedTest(unittest.TestCase):
    def transcript(self):
        return ('The reference model is /reference.so\n'
                'The first instruction of core 0 has commited. Difftest enabled.\n'
                'PARTIAL_V2_BEGIN groups=8 trials=128\n'+
                ''.join(f'PARTIAL_V2_GROUP_PASS id={i} trials=16 register_bytes=8192 csr_fields=5\n' for i in range(8))+
                'PARTIAL_V2_SUMMARY groups=8 trials=128 register_bytes=65536 failures=0\n'
                'HIT GOOD TRAP\nSeed=1 Guest cycle spent: 123\n')

    def evaluate(self,text=None,manifest=None,windows=None):
        manifest=generate.corpus()[1] if manifest is None else manifest
        # Isolate the UART gate; real strict traces have their own regression and
        # are mandatory in the real runner. This fixture cannot qualify hardware.
        diagnosis={'counts':{'COMMIT':generate.corpus()[1]['expected_vdot_commits']},'windows':windows or []}
        raw=(self.transcript() if text is None else text).encode()
        with patch.object(check.diagnose_kills,'diagnose',return_value=diagnosis), \
             patch.object(check.diagnose_kills.analyze,'extract_events_and_uart',return_value=([],raw.decode())):
            return check.check(raw,0,manifest,'/reference.so')

    def test_functional_pass_does_not_close_missing_coverage(self):
        result=self.evaluate()
        self.assertTrue(result['architectural_pass']);self.assertFalse(result['target_covered'])
        self.assertFalse(result['campaign_acceptance'])

    def test_missing_duplicate_and_reordered_markers_rejected(self):
        text=self.transcript();row='PARTIAL_V2_GROUP_PASS id=2 trials=16 register_bytes=8192 csr_fields=5\n'
        for bad in (text.replace(row,''),text.replace(row,row+row),text.replace('id=2','id=3')):
            with self.assertRaises(ValueError):self.evaluate(bad)

    def test_wrong_manifest_and_reference_or_seed_rejected(self):
        manifest=copy.deepcopy(generate.corpus()[1]);manifest['expected_vdot_commits']-=1
        with self.assertRaises(ValueError):self.evaluate(manifest=manifest)
        for old,new in (('/reference.so','/wrong.so'),('Seed=1','Seed=2'),('HIT GOOD TRAP','HIT BAD TRAP')):
            with self.assertRaises(ValueError):self.evaluate(self.transcript().replace(old,new))

    def test_partial_requires_real_survivor_and_cancelled_victim(self):
        row=dict(classification='partial_kill',survivor_committed=True,victim_committed=False)
        self.assertTrue(self.evaluate(windows=[row])['target_covered'])
        for key,value in (('survivor_committed',False),('victim_committed',True)):
            with self.assertRaises(ValueError):self.evaluate(windows=[dict(row,**{key:value})])

    def test_fresh_outputs_only_and_canonical_lf_generation(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'new';generate.emit(out)
            files,manifest=generate.corpus()
            for name,text in files.items():self.assertEqual((out/name).read_bytes(),text.encode())
            with self.assertRaises(FileExistsError):generate.emit(out)
            with self.assertRaises(ValueError):run.check_output(out,[Path(temp)/'input'])
            with self.assertRaises(ValueError):run.check_output(Path(temp)/'inside',[Path(temp)])


if __name__=='__main__':unittest.main()
