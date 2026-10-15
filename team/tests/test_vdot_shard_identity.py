"""Agreement among copies of wrong receipts must not replace fixed identity."""
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('shard_checker',ROOT/'team/scripts/check-vdot-shards.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class ExplicitIdentityTests(unittest.TestCase):
    def setUp(self):
        self.e=dict(source='a'*40,parent_source='a'*40,emu='b'*64,reference='c'*64,flash='d'*64,plan='e'*64,unique_cases=117)
        self.runtime=(self.e['emu'],self.e['reference'],self.e['flash'])
    def test_exact_explicit_identity(self):
        mod.require_runtime_identity(self.e['source'],self.runtime,self.e)
    def test_consistently_wrong_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'receipt source'):
            mod.require_runtime_identity('f'*40,self.runtime,self.e)
    def test_each_wrong_runtime_is_rejected(self):
        for index in range(3):
            runtime=list(self.runtime);runtime[index]='f'*64
            with self.subTest(index=index),self.assertRaisesRegex(ValueError,'runtime differs'):
                mod.require_runtime_identity(self.e['source'],runtime,self.e)
    def test_missing_identity_is_rejected(self):
        for e in (None,{},dict(self.e,source=None),dict(self.e,reference=None)):
            with self.subTest(expected=e),self.assertRaises(ValueError):mod.require_expected_identity(e)
    def test_invalid_digests_and_count_are_rejected(self):
        for key in ('source','parent_source','emu','reference','flash','plan'):
            with self.subTest(key=key),self.assertRaises(ValueError):
                mod.require_expected_identity(dict(self.e,**{key:'main'}))
        for count in (0,-1,True,'117'):
            with self.subTest(count=count),self.assertRaises(ValueError):
                mod.require_expected_identity(dict(self.e,unique_cases=count))
    def test_execution_without_pins_fails_before_read(self):
        with self.assertRaisesRegex(ValueError,'explicit expected'):
            mod.validate(Path('absent-parent'),Path('absent-runs'),ROOT)
    def test_partition_does_not_shadow_explicit_expected_identity(self):
        import hashlib,json,tempfile
        from generate_vdot_cases import generate
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);parent=root/'parent';runs=root/'runs';runs.mkdir()
            generate(parent,0,0x20261011,0,'legacy')
            for i in range(2):generate(runs/f'data-{i}',0,0x20261011,0,'legacy',shard_index=i,shard_count=2)
            _,legal,bad=mod.load_data(parent)
            plan=hashlib.sha256(json.dumps(dict(legal=legal,exceptions=bad),sort_keys=True,separators=(',',':')).encode()).hexdigest()
            expected=dict(self.e,source='1bd6f1d9c9485695876ff37a77fbb175a5125983',parent_source='1bd6f1d9c9485695876ff37a77fbb175a5125983',plan=plan,unique_cases=len(legal)+len(bad))
            with self.assertRaises(FileNotFoundError):
                mod.validate(parent,runs,ROOT,expected=expected)
            with self.assertRaisesRegex(ValueError,'parent plan differs'):
                mod.validate(parent,runs,ROOT,expected=dict(expected,plan='f'*64))
if __name__=='__main__':unittest.main()
