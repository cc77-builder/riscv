import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
spec=importlib.util.spec_from_file_location("continuation",Path(__file__).with_name("continuation.py"))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
REPO=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
WORK=Path("/home/riscv/riscv-lab/software-import-20261026")
class ContinuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.combo,cls.audit=c.modules(REPO)
        cls.identity=cls.combo.parent_identity(REPO,WORK/"reviews/identity/current-identity-v3.json")
        cls.f,cls.m=cls.combo.runtime(REPO,cls.identity)
        cls.images=c.read(WORK/"combination-build-02/images.json")["images"]
        cls.sequence=c.ordered(cls.combo,cls.images)
        cls.prior=WORK/"combination-run-01"
        cls.common=c.read(cls.prior/"runtime-inputs.json")
        cls.directory=cls.prior/"runs/recovery-firstdot-8x32"
        cls.record=c.read(cls.directory/"result.json")
        cls.image=next(x for x in cls.images if x["name"]==cls.record["name"])
    def receipt(self,record):
        return self.audit.process_receipt(record,self.image,self.directory,self.common,
                                         self.identity["configuration"],self.m)
    def test_original_completed_receipt(self):
        self.receipt(self.record)
    def test_real_prefix_counts(self):
        state=c.read(self.prior/"state.json")
        completed=c.read(self.prior/"completed-runs.json")
        self.assertEqual(state["new_emu_runs"],13)
        self.assertEqual(len(completed),11)
        self.assertEqual(len(self.sequence)-(len(completed)+1),21)
        self.assertEqual(13+21,34)
    def test_pending_order_is_unfinished_then_other_shapes(self):
        completed=12
        self.assertEqual(self.sequence[completed][0],"formal-performance-s1-d2-s03")
        self.assertEqual(self.sequence[completed+1][0],"formal-performance-firstdot-d0-s05")
        self.assertEqual(sum(x[3] for x in self.sequence[completed:]),8)
    def test_partial_receipt_rejected(self):
        record=c.read(self.prior/"runs/formal-performance-s1-d2-s03/result.json")
        image=next(x for x in self.images if x["name"]==record["name"])
        with self.assertRaises(ValueError):
            self.audit.process_receipt(record,image,Path(record["cwd"]).parent,self.common,
                                        self.identity["configuration"],self.m)
    def test_forged_cwd_rejected(self):
        row=copy.deepcopy(self.record);row["cwd"]="/tmp/false"
        with self.assertRaises(ValueError):self.receipt(row)
    def test_nonzero_exit_rejected(self):
        row=copy.deepcopy(self.record);row["exit_code"]=1
        with self.assertRaises(ValueError):self.receipt(row)
    def test_missing_exit_rejected(self):
        row=copy.deepcopy(self.record);row["exit_code"]=None
        with self.assertRaises(ValueError):self.receipt(row)
    def test_negative_role_rejected(self):
        row=copy.deepcopy(self.record);row["negative"]=True
        with self.assertRaises(ValueError):self.receipt(row)
    def test_missing_input_rejected(self):
        row=copy.deepcopy(self.record);row["files"].pop(next(iter(row["files"])))
        with self.assertRaises(ValueError):self.receipt(row)
    def test_changed_raw_hash_rejected(self):
        row=copy.deepcopy(self.record);row["raw_sha256"]["stdout.log"]="0"*64
        with self.assertRaises(ValueError):self.receipt(row)
    def test_snapshot_changed_file_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/"evidence";p.write_text("actual")
            old=c.snapshot(root);p.write_text("changed")
            with self.assertRaises(ValueError):c.verify_snapshot(root,old)
    def test_snapshot_extra_file_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/"evidence";p.write_text("actual");old=c.snapshot(root)
            (root/"extra").write_text("extra")
            with self.assertRaises(ValueError):c.verify_snapshot(root,old)
    def test_symlink_snapshot_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/"evidence";p.write_text("actual");(root/"link").symlink_to(p)
            with self.assertRaises(ValueError):c.snapshot(root)
if __name__=="__main__":unittest.main()
