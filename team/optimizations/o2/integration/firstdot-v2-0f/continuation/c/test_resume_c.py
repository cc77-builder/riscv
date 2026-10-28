"""Temporary non-execution fixtures; these tests never start an EMU."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location("resume_c",Path(__file__).with_name("resume_c.py"))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ROOT=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
WORK=Path("/home/riscv/riscv-lab/software-import-20261026")
IDENTITY=WORK/"reviews/identity/current-identity-v3.json"
MATRIX=WORK/"combination-build-02";BUILD=WORK/"c-build-01";PRIOR=WORK/"c-run-01"
class StopBeforeEmu(Exception):pass

class ResumeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle=m.inspect_prior(ROOT,IDENTITY,MATRIX,BUILD,PRIOR,physical=False)
    def test_actual_prior_negative_raw_pass(self):
        self.assertEqual(self.bundle[-1]["retained_completed_processes"],1)
        self.assertEqual(self.bundle[-1]["interrupted_processes"],1)
    def test_transform_reject_missing_anchor(self):
        with self.assertRaises(ValueError):m.replace_one("abc","absent","new")
    def test_transform_reject_duplicate_anchor(self):
        with self.assertRaises(ValueError):m.replace_one("twice twice","twice","new")
    def test_transform_preserves_base_globals(self):
        combo,base,value,negative,fixture,common,proof=self.bundle
        before=base.CONTRACT;run,sha=m.private_run(base,negative,fixture,common,proof,{})
        self.assertEqual(base.CONTRACT,before)
        self.assertEqual(run.__globals__["_resume_negative"],negative)
        self.assertEqual(run.__globals__["_resume_contract"],m.CONTRACT)
        self.assertEqual(len(sha),64)
    def test_resumed_execution_reaches_normal_recovery_without_launch(self):
        combo,base,value,negative,fixture,common,proof=self.bundle
        before=m.tree(PRIOR)
        calls=[]
        def forbidden(argv,cwd,stdout,stderr,record,progress,**kwargs):
            calls.append((argv,str(cwd),dict(record),kwargs))
            raise StopBeforeEmu("host integration test stops before process spawn")
        with tempfile.TemporaryDirectory(prefix="resume-c-host-noemu-") as td:
            out=Path(td)/"run"
            run,_=m.private_run(base,negative,fixture,common,proof,{})
            with patch.object(base.a.frozen_f,"spawn",side_effect=forbidden):
                with self.assertRaises(StopBeforeEmu):
                    run(ROOT,value["configuration"],BUILD,out,"host-no-emu")
            self.assertEqual(len(calls),1)
            argv,cwd,record,kwargs=calls[0]
            self.assertIn("--diff="+value["configuration"]["reference"],argv)
            self.assertFalse(record["negative"]);self.assertFalse(record["process_started"])
            self.assertEqual(cwd,str(out/"runs/recovery/cwd"))
            self.assertEqual(m.read(out/"state.json")["new_emu_runs"],0)
            self.assertEqual(m.read(out/"state.json")["status"],"FAILED")
            self.assertEqual({p.name for p in (out/"runs").iterdir()},{"recovery"})
            self.assertFalse((out/"negative-fixture").exists())
        self.assertEqual(m.tree(PRIOR),before)
if __name__=="__main__":unittest.main()
