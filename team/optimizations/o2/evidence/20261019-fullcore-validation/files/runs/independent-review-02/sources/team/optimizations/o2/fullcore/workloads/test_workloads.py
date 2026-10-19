import copy
import tempfile
from pathlib import Path
import unittest
import generate
import generate_control
import check

class WorkloadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.root=Path(cls.temp.name)
        cls.diag=generate.generate(cls.root/"diag")
        cls.control=generate_control.emit(cls.root/"control")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def uart(self,kind="diag"):
        if kind=="diag":
            lines=["O2_DIAG_BEGIN cases=10 fixed_dots=128 contract=vdot-s8x8-r32-v0.1",
                   "O2_DIAG_CHECKER_CONTROL highbit_detected=1"]
            for i,c in enumerate(self.diag["cases"]):
                lines.append(f'O2_DIAG_CASE_PASS seq={i} id={c["id"]} dots={c["counts"]["vdot"]} register_bytes=512 csr_fields=7')
            lines+=["O2_DIAG_SUMMARY cases=10 dots=1158 failures=0","HIT GOOD TRAP"]
        else:
            lines=["O2_CONTROL_BEGIN groups=16 trials=256 contract=vdot-s8x8-r32-v0.1"]
            lines += [f"O2_CONTROL_GROUP_PASS id={i} trials=16 register_bytes=8192" for i in range(16)]
            lines += ["O2_CONTROL_SUMMARY groups=16 trials=256 register_bytes=131072 failures=0","HIT GOOD TRAP"]
        return "\n".join(lines)+"\n"

    def analysis(self,dots):
        return dict(status="O2_TRACE_PASS",counts={"COMMIT":dots},pending_count=0,unfinished_rob_count=0)

    def test_deterministic_and_fixed_total(self):
        other=generate.generate(self.root/"diag-again")
        self.assertEqual(self.diag,other)
        self.assertEqual(self.diag["expected_vdot_commits"],1158)
        self.assertEqual([c["counts"]["vdot"] for c in self.diag["cases"][:9]],[128]*9)

    def test_full_register_expected_and_recurrence(self):
        for c in self.diag["cases"][:9]:
            self.assertEqual(len(c["expected"]),32)
            self.assertEqual([r for i,r in enumerate(c["expected"]) if not 16<=i<16+c["lanes"]],
                             [r for i,r in enumerate(c["before"]) if not 16<=i<16+c["lanes"]])
            for i in range(c["lanes"]):
                self.assertEqual(c["expected"][16+i][4:],[0]*12)
        chain=self.diag["cases"][6]
        first=generate.dot(chain["before"][16],chain["before"][9])
        self.assertNotEqual(chain["expected"][16],first)

    def test_full_type_transition_set(self):
        kinds=[op["op"] for op in self.diag["cases"][-1]["ops"]]
        self.assertEqual(set(zip(kinds,kinds[1:])),{(a,b) for a in ["vdot","vidiv","vfdiv"] for b in ["vdot","vidiv","vfdiv"]})
        self.assertEqual(len(kinds),18)

    def test_control_fixed_counts(self):
        self.assertEqual(self.control["expected_vdot_commits"],1208)
        self.assertEqual(sum(g["trials"] for g in self.control["groups"]),256)
        self.assertEqual([g["burst"] for g in self.control["groups"]],list(range(1,17)))

    def test_positive_contract(self):
        self.assertEqual(check.check(self.uart(),self.diag,0,self.analysis(1158))["status"],"O2_DIAGNOSTIC_PASS")
        self.assertEqual(check.check_control(self.uart("control"),self.control,0,self.analysis(1208))["status"],"O2_CONTROL_DIAGNOSTIC_PASS")

    def test_missing_or_duplicate_rejected(self):
        for text in [self.uart().replace("seq=5","seq=6"),self.uart()+self.uart(),self.uart().replace("HIT GOOD TRAP",""),
                     self.uart()+"O2_DIAG_FAIL\n"]:
            with self.assertRaises(ValueError):
                check.check(text,self.diag,0,self.analysis(1158))

    def test_partial_retirement_pending_rejected(self):
        for changes in [dict(status="O2_PARTIAL_TRACE_AUDIT"),dict(counts={"COMMIT":1157}),
                        dict(pending_count=1),dict(unfinished_rob_count=1)]:
            analysis=self.analysis(1158)
            analysis.update(changes)
            with self.assertRaises(ValueError):
                check.check(self.uart(),self.diag,0,analysis)

    def test_control_failure_rejected(self):
        for text in [self.uart("control").replace("id=5","id=6"),self.uart("control")+"O2_CONTROL_FAIL\n"]:
            with self.assertRaises(ValueError):
                check.check_control(text,self.control,0,self.analysis(1208))
        with self.assertRaises(ValueError):
            check.check_control(self.uart("control"),self.control,1,self.analysis(1208))

    def test_crlf_and_marker_bounds(self):
        self.assertEqual(check.check(self.uart().replace("\n","\r\n"),self.diag,0,self.analysis(1158))["status"],"O2_DIAGNOSTIC_PASS")
        self.assertEqual(check.check_control(self.uart("control").replace("\n","\r\n"),self.control,0,self.analysis(1208))["status"],"O2_CONTROL_DIAGNOSTIC_PASS")
        for text in [self.uart().replace("csr_fields=7","csr_fields=7 junk"),
                     self.uart().replace("fixed_dots=128","fixed_dots=128 junk"),
                     self.uart().replace("failures=0","failures=0 suffix")]:
            with self.assertRaises(ValueError):
                check.check(text,self.diag,0,self.analysis(1158))
        with self.assertRaises(ValueError):
            check.check_control(self.uart("control").replace("register_bytes=8192","register_bytes=8192 junk"),
                                self.control,0,self.analysis(1208))

    def test_checker_control_order(self):
        marker="O2_DIAG_CHECKER_CONTROL highbit_detected=1\n"
        text=self.uart().replace(marker,"")
        for altered in [marker+text,text+marker]:
            with self.assertRaises(ValueError):
                check.check(altered,self.diag,0,self.analysis(1158))

if __name__=="__main__":
    unittest.main()
