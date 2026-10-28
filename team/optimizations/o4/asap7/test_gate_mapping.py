import tempfile
import unittest
from pathlib import Path
from gate_mapping import mapping

RTL = 'always @(*) if (!CK) EN = TE | E; assign Q = CK & EN;'
LIB = '''cell (ICGx1_ASAP7_75t_R) {
statetable ("CLK ENA SE", "IQ") {table : "L L L : - : L, L L H : - : H, L H L : - : H, L H H : - : H, H - - : - : N";}
pin (GCLK) {state_function : "CLK & IQ";}
}'''

class MappingChecks(unittest.TestCase):
    def check_map(self, lib=LIB, rtl=RTL):
        with tempfile.TemporaryDirectory() as d:
            return mapping('asap7',lib,rtl,Path(d)/'gate.v')

    def test_all_binary_transitions(self):
        self.assertEqual(len(self.check_map()['transitions']),16)

    def test_test_enable_ignored_rejected(self):
        with self.assertRaises(ValueError):self.check_map(LIB.replace('L L H : - : H','L L H : - : L'))

    def test_high_clock_not_holding_rejected(self):
        with self.assertRaises(ValueError):self.check_map(LIB.replace('H - - : - : N','H - - : - : H'))

    def test_wrong_output_rejected(self):
        with self.assertRaises(ValueError):self.check_map(LIB.replace('CLK & IQ','CLK'))

    def test_missing_test_pin_rejected(self):
        with self.assertRaises(ValueError):self.check_map(LIB.replace('CLK ENA SE','CLK ENA'))

    def test_clock_bypass_rejected(self):
        with self.assertRaises(ValueError):self.check_map(rtl='assign Q = CK;')

    def test_duplicate_transition_rejected(self):
        with self.assertRaises(ValueError):self.check_map(LIB.replace('H - - : - : N','H - - : - : N, H - - : - : N'))

if __name__=='__main__':unittest.main()
