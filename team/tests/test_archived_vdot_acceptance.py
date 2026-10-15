"""Real evidence replay plus isolated corruption tests; no fake DUT pass claims."""
import gzip,importlib.util,json,re,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'team/evidence/t10-t11-fullcore-20261013'
spec=importlib.util.spec_from_file_location('strict_archive_verifier',ROOT/'team/scripts/check-vdot-shards.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class ArchivedAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.pins=json.loads((EVIDENCE/'acceptance-pins.json').read_text())
    def validate(self,runs,pins=None):
        return mod.validate(EVIDENCE/'parent',runs,ROOT,expected=pins or self.pins)
    def changed_copy(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        r=Path(t.name)/'matrix';shutil.copytree(EVIDENCE/'matrix',r);return r
    def log(self,path):return mod.raw_log(path).decode()
    def write_log(self,path,text):
        if path.exists():path.write_text(text)
        else:path.with_suffix(path.suffix+'.gz').write_bytes(gzip.compress(text.encode(),mtime=0))
    def test_positive_archive_replays_complete_actual_results(self):
        result=self.validate(EVIDENCE/'matrix')
        self.assertEqual((result['unique_cases'],result['unique_legal'],result['unique_exceptions']),(117,80,37))
        self.assertEqual(result['same_image_normal_restore'],'PASS shard-0')
    def test_all_sources_changed_together_still_rejected(self):
        r=self.changed_copy()
        for i in range(8):(r/f'run-{i}/evidence/team.sha').write_text('0'*40+'\n')
        with self.assertRaisesRegex(ValueError,'receipt source'):self.validate(r)
    def test_agreeing_wrong_runtime_still_rejected(self):
        r=self.changed_copy()
        for i in range(8):
            p=r/f'run-{i}/evidence/runtime.sha256';p.write_text(p.read_text().replace(self.pins['emu'],'0'*64))
        with self.assertRaisesRegex(ValueError,'runtime differs'):self.validate(r)
    def test_selftest_marker_without_seven_real_records_rejected(self):
        r=self.changed_copy();p=r/'run-0/evidence/run.log'
        s='\n'.join(x for x in self.log(p).splitlines() if not x.startswith('VDOT_PACKED id=H'))
        self.write_log(p,s)
        with self.assertRaisesRegex(ValueError,'declared order'):self.validate(r)
    def test_exception_cannot_precede_D00(self):
        r=self.changed_copy();p=r/'run-0/evidence/run.log';lines=self.log(p).splitlines()
        d=next(i for i,x in enumerate(lines) if x.startswith('VDOT_PACKED id=D00 '))
        x=next(i for i,x in enumerate(lines) if x.startswith('VDOT_PACKED id=X'))
        lines[d],lines[x]=lines[x],lines[d];self.write_log(p,'\n'.join(lines))
        with self.assertRaisesRegex(ValueError,'declared order'):self.validate(r)
    def test_unrelated_negative_mismatch_PC_rejected(self):
        r=self.changed_copy();p=r/'negative-0/run.log'
        s,count=re.subn(r'(v\d+_high different at pc = )0x[0-9a-f]+',r'\g<1>0x0080000000',self.log(p),count=1)
        self.assertEqual(count,1);self.write_log(p,s)
        with self.assertRaisesRegex(ValueError,'mismatch PC differs'):self.validate(r)
    def test_truncated_run_is_not_rescued_by_zero_driver_status(self):
        r=self.changed_copy();p=r/'run-0/evidence/run.log'
        self.write_log(p,'\n'.join(x for x in self.log(p).splitlines() if not x.startswith('VDOT_SUMMARY')))
        with self.assertRaisesRegex(ValueError,'summary'):self.validate(r)
    def test_negative_summary_must_match_raw_event(self):
        r=self.changed_copy();p=r/'negative-0/result.json';j=json.loads(p.read_text());j['pc']='0x80000000';p.write_text(json.dumps(j))
        with self.assertRaisesRegex(ValueError,'summary disagrees'):self.validate(r)
    def test_expected_corpus_is_required_not_just_an_internally_consistent_subset(self):
        with self.assertRaisesRegex(ValueError,'parent plan differs'):
            self.validate(EVIDENCE/'matrix',dict(self.pins,plan='0'*64))
    def test_good_trap_before_extension_cannot_stand_for_final_trap(self):
        r=self.changed_copy();p=r/'run-0/evidence/run.log';lines=self.log(p).splitlines()
        good=[x for x in lines if 'HIT GOOD TRAP' in x];self.assertEqual(len(good),1)
        lines=[x for x in lines if 'HIT GOOD TRAP' not in x]
        pos=next(i for i,x in enumerate(lines) if x=='VDOT_EXTENSION_BEGIN');lines.insert(pos,good[0])
        self.write_log(p,'\n'.join(lines))
        with self.assertRaisesRegex(ValueError,'ordered DiffTest'):self.validate(r)
    def test_contradictory_status_rejected(self):
        r=self.changed_copy();p=r/'run-0/status';p.write_text(p.read_text()+'exit_code=124\n')
        with self.assertRaisesRegex(ValueError,'contradictory'):self.validate(r)
    def test_missing_actual_build_provenance_rejected(self):
        r=self.changed_copy();p=r/'run-0/evidence/build-verification.json.gz';p.unlink()
        with self.assertRaises(FileNotFoundError):self.validate(r)
    def test_run_image_different_from_captured_build_rejected(self):
        r=self.changed_copy();p=r/'run-0/evidence/runtime-parameters.txt'
        p.write_text(p.read_text().replace('image=','image=wrong-'))
        with self.assertRaisesRegex(ValueError,'runtime image'):self.validate(r)
    def test_wrong_reference_role_rejected(self):
        r=self.changed_copy();p=r/'run-0/evidence/nemu-verification.json'
        j=json.loads(self.log(p));j['build_mode']='standalone';self.write_log(p,json.dumps(j))
        with self.assertRaisesRegex(ValueError,'NEMU role'):self.validate(r)
    def test_dirty_tested_team_tree_rejected(self):
        r=self.changed_copy();(r/'run-0/evidence/working-tree.txt').write_text(' M team/workloads/vdot-exceptions/main.c\n')
        with self.assertRaisesRegex(ValueError,'dirty'):self.validate(r)
    def test_common_wrong_model_hash_rejected(self):
        r=self.changed_copy()
        for i in range(8):
            p=r/f'data-{i}/manifest.json';j=json.loads(p.read_text());j['source_sha256']['vdot_model.py']='0'*64;p.write_text(json.dumps(j))
        with self.assertRaisesRegex(ValueError,'generator/model'):self.validate(r)
    def test_negative_reference_metadata_must_match_normal(self):
        r=self.changed_copy();p=r/'negative-0/reference-verification.json'
        j=json.loads(self.log(p));j['config_sha256']='0'*64;self.write_log(p,json.dumps(j))
        with self.assertRaisesRegex(ValueError,'base-reference provenance'):self.validate(r)
    def test_negative_actual_image_provenance_must_match_normal(self):
        r=self.changed_copy();p=r/'negative-0/image-verification.json'
        j=json.loads(self.log(p));j['mode']='selftest';self.write_log(p,json.dumps(j))
        with self.assertRaisesRegex(ValueError,'actual workload provenance'):self.validate(r)
if __name__=='__main__':unittest.main()
