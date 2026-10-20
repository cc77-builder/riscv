import unittest
from check_negative_fu import check, FAULTS

class NegativeGateTests(unittest.TestCase):
    def test_exact_detection(self):
        for f in FAULTS:
            check(f,1,f"O2_FU_INJECT {f}\nO2_FU_FAIL {f}\n")
    def test_reject_false_positives(self):
        good="O2_FU_INJECT identity\nO2_FU_FAIL identity\n"
        for rc,text in [(0,good),(3,good),(1,""),(1,good+good),(1,good+"O2_FU_PASS\n"),
                        (1,good.replace("FAIL identity","FAIL high")),(1,good.replace("INJECT identity","FAULT_ESCAPED identity"))]:
            with self.subTest(rc=rc,text=text), self.assertRaises(ValueError):
                check("identity",rc,text)
if __name__=="__main__": unittest.main()
