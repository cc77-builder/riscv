"""Checks for audit mistakes that would change the H1 go/no-go decision."""
from pathlib import Path
import tempfile
import unittest

import audit


def dff(q, d):
    return {"type": "DFF_X1", "port_directions": {"D": "input", "Q": "output", "CK": "input"},
            "connections": {"D": [d], "Q": [q], "CK": [2]}}


def gate(kind, inputs, output):
    names = ["A"] if len(inputs) == 1 else ["A1", "A2"]
    return {"type": kind, "port_directions": {**dict.fromkeys(names, "input"), "ZN": "output"},
            "connections": {**{n: [b] for n, b in zip(names, inputs)}, "ZN": [output]}}


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.module = {"cells": {"ff": dff(10, 20)},
                       "netnames": {"result": {"bits": [10, 10, "0"]}}}

    def test_aliases_and_constants_are_not_extra_registers(self):
        rows = audit.result_registers(self.module, "result", audit.drivers(self.module))
        self.assertEqual(audit.counts(rows), {"positions": 3, "unique_q_bits": 1,
                         "constant_positions": 1, "dff_positions": 2, "unique_dff_cells": 1})

    def test_independent_same_type_cells_remain_distinct(self):
        self.module["cells"]["ff2"] = dff(11, 20)
        self.module["netnames"]["result"]["bits"] = [10, 11]
        rows = audit.result_registers(self.module, "result", audit.drivers(self.module))
        self.assertEqual(audit.counts(rows)["unique_dff_cells"], 2)

    def test_non_dff_driver_is_not_counted(self):
        self.module["cells"]["ff"]["type"] = "BUF_X1"
        rows = audit.result_registers(self.module, "result", audit.drivers(self.module))
        self.assertEqual(audit.counts(rows)["unique_dff_cells"], 0)

    def test_multiple_drivers_fail(self):
        self.module["cells"]["ff2"] = dff(10, 21)
        with self.assertRaisesRegex(ValueError, "multiple drivers"):
            audit.drivers(self.module)

    def test_own_q_and_hold(self):
        self.module["cells"]["hold"] = gate("AND2_X1", [10, 30], 20)
        result = audit.hold_feedback({"q": 10, "d": 20}, self.module, audit.drivers(self.module))
        self.assertEqual(result["expression"], "D = Q & hold")
        self.assertEqual(result["local_cells"], ["hold"])

    def test_other_q_feedback_fails(self):
        self.module["cells"]["hold"] = gate("AND2_X1", [11, 30], 20)
        with self.assertRaisesRegex(ValueError, "own Q"):
            audit.hold_feedback({"q": 10, "d": 20}, self.module, audit.drivers(self.module))

    def test_inverted_own_q_nor_clear(self):
        self.module["cells"].update(inv=gate("INV_X1", [10], 40),
                                    hold=gate("NOR2_X1", [40, 30], 20))
        result = audit.hold_feedback({"q": 10, "d": 20}, self.module, audit.drivers(self.module))
        self.assertEqual(result["expression"], "D = ~(~Q | clear)")
        self.assertEqual(set(result["local_cells"]), {"hold", "inv"})

    def test_buffer_chain_is_normalized(self):
        self.module["cells"].update(b1=gate("BUF_X1", [31], 30), b2=gate("BUF_X1", [32], 31))
        self.assertEqual(audit.strip_buffers(30, self.module, audit.drivers(self.module)), 32)

    def test_buffer_cycle_fails(self):
        self.module["cells"].update(b1=gate("BUF_X1", [31], 30), b2=gate("BUF_X1", [30], 31))
        with self.assertRaisesRegex(ValueError, "buffer cycle"):
            audit.strip_buffers(30, self.module, audit.drivers(self.module))

    def test_unpinned_manifest_fails(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "manifest.json").write_text('{"entries": []}')
            with self.assertRaisesRegex(ValueError, "manifest identity"):
                audit.Evidence(root)

    def test_shared_feedback_gate_is_excluded(self):
        self.module["ports"] = {}
        self.module["cells"].update(inv=gate("INV_X1", [10], 40),
                                    hold=gate("NOR2_X1", [40, 30], 20),
                                    consumer=gate("AND2_X1", [40, 31], 50))
        exclusive, shared = audit.partition_feedback(self.module, {"inv", "hold"}, {"ff"})
        self.assertEqual(exclusive, {"hold"})
        self.assertEqual(shared, {"inv"})

    def test_transitive_shared_feedback_is_excluded(self):
        self.module["ports"] = {"out": {"direction": "output", "bits": [20]}}
        self.module["cells"].update(inv=gate("INV_X1", [10], 40),
                                    hold=gate("NOR2_X1", [40, 30], 20))
        exclusive, shared = audit.partition_feedback(self.module, {"inv", "hold"}, {"ff"})
        self.assertEqual(exclusive, set())
        self.assertEqual(shared, {"inv", "hold"})


if __name__ == "__main__":
    unittest.main()
