from __future__ import annotations
import copy
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[5]
SOURCE = REPO/'team/optimizations/o2/integration/firstdot-v2-0f'
sys.path.insert(0, str(SOURCE))
spec = importlib.util.spec_from_file_location('actual_current_combination', SOURCE/'combination.py')
combo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(combo)

def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2)+'\n')
    return path

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

class CombinationFixtures(unittest.TestCase):
    # Synthetic receipts exercise rejection logic only, not physical runtime qualification.
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='combination-unit-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.identity = put(self.root/'identity.json',dict(contract='SYNTHETIC_UNIT_FIXTURE_NOT_RUNTIME'))
        self.matrix, self.run = self.root/'matrix', self.root/'run'
        self.images = []
        self.normal = []
        for n,item in enumerate(combo.inventory([1,3,5,7],[0,1,2])):
            image = dict(item,name=combo.name(item),image_sha256=sha(combo.name(item).encode()),
                         path=str(self.matrix/'images'/combo.name(item)))
            self.images.append(image)
            samples = []
            for repeat in range(6):
                for software in ('basic','reuse'):
                    for method in ('vdot','rvv'):
                        samples.append(dict(seq=len(samples),repeat=repeat,
                            phase='first' if repeat==0 else ('warmup' if repeat==1 else 'measured'),
                            variant=item['variant'],shard=item['shard'],software=software,method=method,
                            cycles=100+(method=='rvv'),instructions=80,scope='endtoend-with-c-abi-call'))
            self.normal.append(dict(image,status='R2_DIFFTEST_WINDOWS_AND_O2_PROTOCOL_PASS',replay=0,
                negative=False,samples=samples,started='2026-10-26T06:00:00+00:00',
                finished='2026-10-26T06:01:00+00:00',pid=n+100,exit_code=0,process_started=True))
        self.repeats = [dict(copy.deepcopy(r),replay=1,pid=r['pid']+1000) for r in self.normal if r['dataset']==0]
        self.negative = dict(next(r for r in self.normal if r['shard']==3 and r['dataset']==0 and r['variant']=='firstdot'),
            status='EXPECTED_VDOT_HIGHBIT_REJECTION',negative=True,exit_code=1,pid=50,
            started='2026-10-26T05:58:00+00:00',finished='2026-10-26T05:59:00+00:00',
            negative_details=dict(vd=0,word='0x0388000b',bit=100))
        self.result = dict(status=combo.RUN_PASS,contract=combo.CONTRACT,
            historical_pass_reused=False,parent_identity_sha256=combo.g.sha(self.identity),
            runs=self.normal+self.repeats,negative=self.negative,
            qualification=combo.qualification(self.images,self.normal+self.repeats,True,True),
            **combo.summarize(self.normal+self.repeats))
        self.state = dict(status=combo.RUN_PASS,contract=combo.CONTRACT,new_emu_runs=33)
        self.write()

    def write(self):
        put(self.matrix/'images.json',dict(images=self.images))
        put(self.matrix/'combination-build.json',dict(contract=combo.CONTRACT,historical_pass_reused=False,
            images={i['name']:i['image_sha256'] for i in self.images},adapter_files=combo.adapter_files(),
            parent_identity_sha256=combo.g.sha(self.identity)))
        put(self.run/'state.json',self.state)
        put(self.run/'results.json',self.result)

    def check(self):
        self.write()
        return combo.matrix_qualification(self.identity,self.matrix,self.run)

    def rejected(self):
        with self.assertRaises((ValueError,KeyError,AssertionError)):
            self.check()

    def test_complete_fixture(self):
        proof=self.check()
        self.assertEqual(proof['parent_identity_sha256'],combo.g.sha(self.identity))

    def test_missing_full_matrix(self):
        self.result['qualification']['full_matrix']=False
        self.rejected()

    def test_missing_replay_qualification(self):
        self.result['qualification']['all_window_replay']=False
        self.rejected()

    def test_missing_negative_qualification(self):
        self.result['qualification']['negative_and_recovery']=False
        self.rejected()

    def test_missing_image(self):
        self.images.pop()
        self.rejected()

    def test_fewer_processes(self):
        self.state['new_emu_runs']=32
        self.rejected()

    def test_wrong_identity(self):
        self.result['parent_identity_sha256']='f'*64
        self.rejected()

    def test_failed_normal(self):
        self.result['runs'][0]['status']='FAILED'
        self.rejected()

    def test_wrong_payload(self):
        self.result['runs'][0]['image_sha256']='0'*64
        self.rejected()

    def test_incomplete_windows(self):
        self.result['measured_windows']=383
        self.rejected()

    def test_wrong_outer_contract(self):
        self.result['contract']='historical-contract'
        self.rejected()

    def test_claimed_replay_but_missing_record(self):
        self.result['runs'].pop()
        self.rejected()

    def test_claimed_replay_but_duplicate_record(self):
        self.result['runs'][-1]=copy.deepcopy(self.result['runs'][-2])
        self.rejected()

    def test_claimed_replay_but_failed_record(self):
        self.result['runs'][-1]['status']='FAILED'
        self.rejected()

    def test_claimed_replay_but_changed_cycles(self):
        self.result['runs'][-1]['samples'][0]['cycles']+=1
        self.rejected()

    def test_negative_wrong_destination(self):
        self.result['negative']['negative_details']['vd']=20
        self.rejected()

    def test_wrong_state_contract(self):
        self.state['contract']='historical-contract'
        self.rejected()

    def test_replay_wrong_payload_even_with_identical_counters(self):
        self.result['runs'][-1]['image_sha256']='f'*64
        self.rejected()

    def test_replay_wrong_dataset_even_with_identical_counters(self):
        self.result['runs'][-1]['dataset']=2
        self.rejected()

class BuildIdentity(unittest.TestCase):
    def test_build_identity_mismatch(self):
        with tempfile.TemporaryDirectory(prefix='combination-build-unit-') as d:
            root=Path(d)
            identity=put(root/'identity.json',dict(unit_fixture=True))
            image=dict(name='performance-firstdot-d0-s03',image_sha256='a'*64)
            receipt=dict(contract=combo.CONTRACT,historical_pass_reused=False,
                images={image['name']:image['image_sha256']},adapter_files=combo.adapter_files(),
                parent_identity_sha256='0'*64)
            put(root/'combination-build.json',receipt)
            with self.assertRaises((ValueError,AssertionError)):
                combo.verify_build_scope(REPO,root,[image],identity)

class ImportManifest(unittest.TestCase):
    def test_real_import_manifest(self):
        combo.verify_imports()

    def test_rehashed_manifest_does_not_accept_changed_source(self):
        with tempfile.TemporaryDirectory(prefix='combination-import-unit-') as d:
            root=Path(d)
            manifest=copy.deepcopy(json.loads((SOURCE/'import-manifest.json').read_text()))
            manifest['files']=[]
            for i in range(45):
                imported=root/f'team/test-{i}.py'
                imported.parent.mkdir(parents=True,exist_ok=True)
                imported.write_bytes(b'original\\n')
                manifest['files'].append(dict(path=f'team/test-{i}.py',bytes=len(imported.read_bytes()),
                                    sha256=sha(imported.read_bytes()),state='imported'))
            fake_here=root/'adapter'
            put(fake_here/'import-manifest.json',manifest)
            with patch.object(combo,'HERE',fake_here), patch.object(combo,'ROOT',root):
                combo.verify_imports()
                (root/'team/test-0.py').write_bytes(b'forged!!\\n')
                with self.assertRaises((ValueError,AssertionError)):
                    combo.verify_imports()

if __name__ == '__main__':
    unittest.main(verbosity=2)
