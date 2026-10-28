import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("resume_audit",HERE/"resume_audit.py")
x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)
REPO=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
WORK=Path("/home/riscv/riscv-lab/software-import-20261026")
IDENTITY=WORK/"reviews/identity/current-identity-v3.json"

class ActualCReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=x.helpers(REPO);cls.combo=cls.a.load_combination(REPO)
        cls.identity=cls.combo.parent_identity(REPO,IDENTITY)
        cls.base,cls.common,cls.profile=x.c_common(cls.a,cls.combo,REPO,cls.identity,WORK/"c-build-01")
        cls.cfg=cls.identity["configuration"];cls.directory=WORK/"c-run-01/runs/negative"
        cls.fixture=cls.a.negative_fixture(WORK/"c-run-01",cls.cfg,cls.base.a.frozen_m)
        cls.validation=cls.base.verify_build(REPO,WORK/"c-build-01")
        cls.original=cls.a.read(cls.directory/"result.json")
        cls.before={p:cls.a.sha(p) for p in cls.directory.rglob("*") if p.is_file()}
    @classmethod
    def tearDownClass(cls):
        assert cls.before=={p:cls.a.sha(p) for p in cls.directory.rglob("*") if p.is_file()}
    def setUp(self):self.record=copy.deepcopy(self.original)
    def check(self):
        return x.c_receipt(self.a,self.record,self.directory,self.common,self.cfg,self.fixture,self.base,
                           WORK/"c-build-01","negative",self.validation)
    def reject(self):
        with self.assertRaises(ValueError):self.check()
    def test_actual_old_negative(self):
        self.assertEqual(self.check(),self.original["files"])
    def test_null_exit_rejected(self):
        self.record["exit_code"]=None;self.reject()
    def test_interrupted_status_rejected(self):
        self.record["status"]="RUNNING";self.reject()
    def test_false_positive_exit_rejected(self):
        self.record["exit_code"]=0;self.reject()
    def test_bad_pid_rejected(self):
        self.record["pid"]=False;self.reject()
    def test_not_launched_rejected(self):
        self.record["process_started"]=False;self.reject()
    def test_timeout_rejected(self):
        self.record["timed_out"]=True;self.reject()
    def test_changed_input_inventory_rejected(self):
        self.record["files"].pop(next(iter(self.record["files"])));self.reject()
    def test_changed_actual_cwd_rejected(self):
        self.record["cwd"]="/tmp/fake-cwd";self.reject()
    def test_changed_command_rejected(self):
        self.record["command"][-1]="--seed=2";self.reject()
    def test_changed_reference_rejected(self):
        self.record["reference"]=self.cfg["reference"];self.reject()
    def test_raw_hash_rejected(self):
        self.record["raw_sha256"]["stdout.log"]="0"*64;self.reject()
    def test_performance_scope_rejected(self):
        self.record["performance_measured"]=True;self.reject()
    def test_contract_rejected(self):
        self.record["contract"]="old-contract";self.reject()
    def test_bad_replay_rejected(self):
        self.record["replay"]=1;self.reject()
    def test_bad_negative_environment_rejected(self):
        self.record["environment_overrides"]={"XS_NEGATIVE_VECTOR_TARGET":None};self.reject()
    def test_bad_time_rejected(self):
        self.record["finished"]="2000-01-01T00:00:00+00:00";self.reject()

class ArchiveEnvelope(unittest.TestCase):
    def test_new_contract_archive_and_bytes(self):
        a=x.helpers(REPO)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/"raw.txt";p.write_text("unfinished log stays preserved")
            result=a.pack_archive({"interrupted/raw.txt":p},root/"archive")
            self.assertEqual(a.read(root/"archive/manifest.json")["contract"],x.CONTRACT)
            self.assertEqual(result["new_emu_runs"],0)
            self.assertEqual(x.verify_archive(REPO,root/"archive"),result)
    def test_archive_tamper_rejected(self):
        a=x.helpers(REPO)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/"raw.txt";p.write_text("immutable")
            a.pack_archive({"interrupted/raw.txt":p},root/"archive")
            next((root/"archive/payload").iterdir()).write_bytes(b"bad")
            with self.assertRaises(ValueError):x.verify_archive(REPO,root/"archive")
    def test_output_overlap_rejected(self):
        a=x.helpers(REPO)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with self.assertRaises(ValueError):a.fresh_output(root/"child",[root])


class ReadonlyQualificationFix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=x.helpers(REPO)
        cls.path=REPO/x.LEAF/"continuation/matrix/continuation.py"
        cls.controller=x.load("_test_frozen_continuation",cls.path)
        cls.campaign=WORK/"combination-resume-01"
        cls.target=REPO/x.MERGED_SCREEN
    def call(self):
        return x.private_matrix_qualify(self.a,self.controller,REPO,IDENTITY,WORK/"combination-build-02",self.campaign)
    def test_actual_complete_campaign_and_no_source_mutation(self):
        before=self.a.sha(self.path);function=self.controller.qualify
        proof,adaptation=self.call()
        self.assertEqual(proof["qualified_processes"],33)
        self.assertEqual(proof["total_processes_started"],34)
        self.assertEqual(adaptation["substitutions"],2)
        self.assertFalse(adaptation["controller_source_modified"])
        self.assertIs(self.controller.qualify,function)
        self.assertEqual(self.a.sha(self.path),before)
    def test_wrong_controller_hash_rejected(self):
        sha=self.a.sha
        with mock.patch.object(self.a,"sha",side_effect=lambda p:"0"*64 if Path(p)==self.path else sha(p)):
            with self.assertRaisesRegex(ValueError,"unrecognized frozen"):self.call()
    def test_wrong_checker_hash_rejected(self):
        sha=self.a.sha
        with mock.patch.object(self.a,"sha",side_effect=lambda p:"0"*64 if Path(p)==self.target else sha(p)):
            with self.assertRaisesRegex(ValueError,"actual frozen runtime"):self.call()
    def test_checker_not_in_frozen_runtime_rejected(self):
        read=self.a.read
        def altered(path):
            value=read(path)
            if Path(path)==self.campaign/"runtime-inputs.json":
                value=dict(value);value.pop(str(self.target))
            return value
        with mock.patch.object(self.a,"read",side_effect=altered):
            with self.assertRaisesRegex(ValueError,"actual frozen runtime"):self.call()
    def test_original_actual_count_guard_retained(self):
        read=self.controller.read
        def altered(path):
            value=read(path)
            if Path(path)==self.campaign/"state.json":
                value=dict(value);value["total_processes_started"]=33
            return value
        with mock.patch.object(self.controller,"read",side_effect=altered):
            with self.assertRaisesRegex(ValueError,"accounting drift"):self.call()
    def test_original_raw_hash_guard_retained(self):
        read=self.controller.read
        def altered(path):
            value=read(path)
            if Path(path).name=="result.json" and "runs" in Path(path).parts:
                value=copy.deepcopy(value);value["raw_sha256"]["stdout.log"]="0"*64
            return value
        with mock.patch.object(self.controller,"read",side_effect=altered):
            with self.assertRaisesRegex(ValueError,"raw transcript drift"):self.call()

if __name__=="__main__":unittest.main()

