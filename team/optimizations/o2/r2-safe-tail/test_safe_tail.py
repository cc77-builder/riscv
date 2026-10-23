"""Host/compiler tests only. No timing model or RTL is exercised."""
from pathlib import Path
import random
import shutil
import struct
import tempfile
import unittest
from unittest.mock import patch
import candidate
from machine_model import Machine
import screen

ROOT = Path(__file__).resolve().parents[4]

class SafeTailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = candidate.load_base(ROOT)
        cls.audit = screen.audit_module(ROOT)
        cls.clang = shutil.which("clang")
        if not cls.clang:
            raise RuntimeError("compiler required; do not silently skip machine-code checks")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.serial = 0

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def compile(self, body):
        type(self).serial += 1
        return screen.assemble(body, Path(self.tmp.name)/str(self.serial), self.clang, self.audit)

    def body(self, software="reuse", scope="endtoend", variant="s2"):
        return candidate.kernel(self.base, 4, 13, "vdot", software, scope, variant)

    def reject_body(self, body):
        a, x = [[127] * 13 for _ in range(4)], [-128] * 13
        code = self.compile(body)  # Assembly failure must not count as a semantic rejection.
        with self.assertRaises(ValueError):
            Machine(a, x, 91).execute(code).check(a, x)

    def test_only_4x13_vdot_changes(self):
        for m,k in self.base.SHAPES:
            for method in ("vdot","rvv"):
                for software in ("basic","reuse"):
                    for scope in self.base.SCOPES:
                        old=self.base.kernel(m,k,method,software,scope)
                        new=candidate.kernel(self.base,m,k,method,software,scope)
                        self.assertEqual(old==new, (m,k)!=(4,13) or method!="vdot")

    def test_s0_is_original(self):
        self.assertEqual(self.body(variant="s0"),self.base.kernel(4,13,"vdot","reuse","endtoend"))

    def test_counts_and_dot_metadata(self):
        row=candidate.make_case(self.base,4,13,0,"vdot","reuse","endtoend","s2")
        self.assertEqual((len(row["body"]),row["dots"]),(83,8))
        self.assertFalse(any(x.startswith(("lb ","mulw ")) for x in row["body"]))

    def test_expected_layout_and_input_unchanged(self):
        for ds in range(3):
            old=self.base.case(4,13,ds,"vdot","reuse","endtoend")
            new=candidate.make_case(self.base,4,13,ds,"vdot","reuse","endtoend","s2")
            for field in ("before","expected","outputs","stream","scratch","iterations","vtype"):
                self.assertEqual(old[field],new[field])

    def test_positive_core_and_endtoend(self):
        for software in ("basic","reuse"):
            for scope in self.base.SCOPES:
                code=self.compile(self.body(software,scope))
                for ds in range(3):
                    a,x=self.base.inputs(4,13,ds)
                    self.assertTrue(Machine(a,x,ds).execute(code).check(a,x,scope=="endtoend"))

    def test_exact_tail_read_spans(self):
        a,x=self.base.inputs(4,13,2)
        vm=Machine(a,x).execute(self.compile(self.body()))
        self.assertEqual([r for r in vm.reads if r[1]==5],[(60,5),(8,5),(21,5),(34,5),(47,5)])
        self.assertEqual(sum(n for _,n in vm.reads),65)

    def test_negative_missing_zero_initialization(self):
        body=self.body();start=body.index("vmv.v.i v24, 0")
        del body[start:start+5]
        self.reject_body(body)

    def test_negative_tail_agnostic(self):
        self.reject_body([s.replace("5, e8, m1, tu", "5, e8, m1, ta") for s in self.body()])

    def test_negative_overread_vl8(self):
        self.reject_body([s.replace("5, e8, m1", "8, e8, m1") for s in self.body()])

    def test_negative_missing_vl8_restore(self):
        body=self.body();pos=body.index("vsetivli zero, 5, e8, m1, tu, mu")
        nxt=body.index("vsetivli zero, 8, e8, m1, tu, mu",pos)
        del body[nxt];self.reject_body(body)

    def test_negative_row_boundary(self):
        self.reject_body(["addi t6, a2, 48" if s=="addi t6, a2, 47" else s for s in self.body()])

    def test_negative_drop_tail_accumulation(self):
        body=self.body();pos=max(i for i,s in enumerate(body) if s=="addw t0, t0, t6")
        del body[pos];self.reject_body(body)

    def test_negative_high96_not_cleared(self):
        body=self.body();pos=body.index("vmv.v.i v0, 0")
        body[pos:pos]=["vsetivli zero, 1, e32, m1, tu, mu"]
        self.reject_body(body)

    def test_negative_protected_register_clobber(self):
        body=self.body();body[0:0]=["vsetivli zero, 4, e32, m1, tu, mu","vmv.v.i v4, 0"]
        self.reject_body(body)

    def test_unknown_and_truncated_rejected(self):
        a,x=self.base.inputs(4,13,0)
        for code in (b"\0",struct.pack("<I",0xffffffff),struct.pack("<I",0x00000063)):
            with self.assertRaises(ValueError):Machine(a,x).execute(code)

    def test_direct_memory_bounds(self):
        a,x=self.base.inputs(4,13,0);vm=Machine(a,x)
        for addr,n in ((0x1000+8,8),(0x1000+60,8),(0xfff,1)):
            with self.assertRaises(ValueError):vm.read(addr,n)

    def test_generation_rejects_existing_directory(self):
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaises(ValueError):candidate.generate(ROOT,out,"s2",0,7)

    def test_drift_and_unsupported_variants_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/next(iter(candidate.PINS));p.parent.mkdir(parents=True);p.write_text("pass\n")
            with self.assertRaises(ValueError):candidate.load_base(d)
        with self.assertRaises(ValueError):candidate.kernel(self.base,4,13,"vdot","reuse","core","s1")
        with self.assertRaises(ValueError):candidate.kernel(self.base,4,14,"vdot","reuse","core")

    def test_splice_fails_closed(self):
        with patch.object(self.base,"kernel",return_value=["li t0, 0"]):
            with self.assertRaises(ValueError):candidate.kernel(self.base,4,13,"vdot","reuse","core")

    def test_s1_register_budget_and_group_disjointness(self):
        for method in ("vdot","rvv"):
            for first in (0,4,8,12):
                for k in (8,32,64):
                    regs=candidate.s1_register_plan(method,first,k)
                    allregs=[r for v in regs.values() for r in v]
                    self.assertEqual(len(allregs),len(set(allregs)))
                    self.assertEqual(regs["output_accumulators"],list(range(first,first+4)))
                    self.assertTrue(set(regs["partials"])<=set(range(20,28)))
        self.assertEqual(len(set.union(*(set(v) for n,v in candidate.s1_register_plan("vdot").items() if n!="output_accumulators"))),16)

    def test_s1_int32_seed_equivalence_model_only(self):
        rng=random.Random(1947)
        for k in (8,32,64):
            for _ in range(100):
                a=[rng.randrange(-128,128) for _ in range(k)]
                x=[rng.randrange(-128,128) for _ in range(k)]
                wanted=sum(u*v for u,v in zip(a,x))
                for width in (8,16):
                    seed=0
                    for pos in range(0,k,width):seed+=sum(u*v for u,v in zip(a[pos:pos+width],x[pos:pos+width]))
                    self.assertEqual(seed,wanted)
                    self.assertTrue(-(1<<31)<=seed<(1<<31))

if __name__=="__main__":unittest.main()
