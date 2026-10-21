import copy
import unittest
from compare_cost import check_groups, data_storage, mapped_metadata, module_body, timing_changes, PROFILES, check_sealed_inventory


def design(width=32, boundary="fu"):
    prefix = "dut." if boundary == "fu" else "dut.Vdot."
    bits = list(range(100, 100 + width))
    result = bits[:32] + (["0"] * 96 if width == 32 else bits[32:])
    cells = {f"q{i}": {"type": "DFF_X1", "port_directions": {"Q": "output", "D": "input"},
                       "connections": {"Q": [b], "D": [1000 + i]}} for i, b in enumerate(bits)}
    return {"cells": cells, "netnames": {prefix + "rPacket_res_data": {"bits": bits},
            prefix + "io_out_bits_res_data": {"bits": result}},
            "ports": {"io_out_bits_res_data" if boundary == "fu" else "io_out_bits_data_0":
                      {"direction": "output", "bits": result if boundary == "fu" else list(range(5000, 5128))}}}


def timing(boundary="fu"):
    paths = {"r2r", "i2r", "r2o", "i2o", "ready"}
    if boundary == "parent":
        paths |= {"vdot_r2r", "vdot_i2r", "vdot_r2o", "gate_enable"}
    return {"profiles": [{"profile": n, "period_ns": period, "load_ff": load,
            "paths": {key: {"exists": True, "arrival_ns": 1.2, "slack_ns": -.3,
                           "startpoint": "a", "endpoint": "b"} for key in paths}}
            for n, (period, load) in PROFILES.items()]}


class CompareCostTests(unittest.TestCase):
    def test_sealed_baseline_identity_and_file_set_required(self):
        entries = [{"path": "map/a", "sha256": "abc", "bytes": 3}]
        inventory = {"map": {"a": {"sha256": "abc", "bytes": 3}}}
        check_sealed_inventory(inventory, entries)
        inventory["map"]["a"]["sha256"] = "bad"
        with self.assertRaisesRegex(ValueError, "sealed manifest"):
            check_sealed_inventory(inventory, entries)
        with self.assertRaisesRegex(ValueError, "file set"):
            check_sealed_inventory({"map": {}}, entries)

    def test_unique_32_bit_storage_and_full_output(self):
        summary = data_storage(design(), "fu", 32)
        self.assertEqual(summary["unique_dff_cells"], 32)
        self.assertTrue(summary["child_output_high96_zero"])

    def test_old_128_bit_storage_is_supported(self):
        self.assertEqual(data_storage(design(128), "fu", 128)["stored_bits"], 128)

    def test_parent_div_output_need_not_be_constant(self):
        summary = data_storage(design(boundary="parent"), "parent", 32)
        self.assertFalse(summary["public_data_ports"]["io_out_bits_data_0"]["high96_constant_zero"])

    def test_result_alias_rejected(self):
        d = design()
        d["netnames"]["dut.rPacket_res_data"]["bits"][1] = 100
        with self.assertRaisesRegex(ValueError, "unique"):
            data_storage(d, "fu", 32)

    def test_non_dff_result_rejected(self):
        d = design()
        d["cells"]["q0"]["type"] = "BUF_X1"
        with self.assertRaisesRegex(ValueError, "DFF"):
            data_storage(d, "fu", 32)

    def test_multiple_driver_rejected(self):
        d = design()
        d["cells"]["bad"] = copy.deepcopy(d["cells"]["q0"])
        with self.assertRaisesRegex(ValueError, "multiple"):
            data_storage(d, "fu", 32)

    def test_dynamic_child_high_bit_rejected_even_in_parent(self):
        d = design(boundary="parent")
        d["netnames"]["dut.Vdot.io_out_bits_res_data"]["bits"][100] = 991
        with self.assertRaisesRegex(ValueError, "high 96"):
            data_storage(d, "parent", 32)

    def test_public_fu_output_cannot_hide_high_bit_error(self):
        d = design()
        d["ports"]["io_out_bits_res_data"]["bits"] = d["ports"]["io_out_bits_res_data"]["bits"].copy()
        d["ports"]["io_out_bits_res_data"]["bits"][100] = 991
        with self.assertRaisesRegex(ValueError, "public output"):
            data_storage(d, "fu", 32)

    def test_low_bits_remain_identity_bound(self):
        d = design()
        d["netnames"]["dut.io_out_bits_res_data"]["bits"][0] = 991
        with self.assertRaisesRegex(ValueError, "low 32"):
            data_storage(d, "fu", 32)

    def test_comment_only_arithmetic_changes_accepted(self):
        a = "// banner\nmodule P(input x); /* source */ assign y=x; endmodule"
        b = "module P(input x); assign y=x; // source\nendmodule"
        self.assertEqual(module_body(a, "P"), module_body(b, "P"))

    def test_arithmetic_logic_change_detected(self):
        self.assertNotEqual(module_body("module P; assign y=x; endmodule", "P"),
                            module_body("module P; assign y=~x; endmodule", "P"))

    def test_string_literal_is_not_a_comment(self):
        self.assertIn('"a//b"', module_body('module P; initial $display("a//b"); endmodule', "P"))

    def test_missing_module_rejected(self):
        with self.assertRaises(ValueError):
            module_body("module Q; endmodule", "P")

    def test_group_changes_are_explicit_failure(self):
        groups = {"result": 128, "products": 128, "stage_state": 2,
                  "p_control": 20, "p_perf": 100, "r_control": 20, "r_perf": 100}
        a = {"groups": groups, "total_bits": sum(groups.values())}
        b = copy.deepcopy(a)
        b["groups"]["result"] = 32
        b["total_bits"] -= 96
        check_groups(a, b)
        b["groups"]["p_perf"] -= 1
        with self.assertRaisesRegex(ValueError, "control/perf"):
            check_groups(a, b)

    def test_mapped_groups_ignore_constants_and_aliases(self):
        d = design()
        d["netnames"]["dut.pPerf_a"] = {"bits": [100, 100, "0"]}
        self.assertEqual(mapped_metadata(d, "fu")["p_perf"], 1)

    def test_all_profiles_and_parent_gate_paths_required(self):
        a = timing("parent")
        b = copy.deepcopy(a)
        b["profiles"][0]["paths"].pop("gate_enable")
        with self.assertRaisesRegex(ValueError, "path category"):
            timing_changes(a, b, "parent")

    def test_missing_or_duplicate_profile_rejected(self):
        a = timing()
        b = copy.deepcopy(a)
        b["profiles"][-1] = copy.deepcopy(b["profiles"][0])
        with self.assertRaisesRegex(ValueError, "profile"):
            timing_changes(a, b, "fu")

    def test_actual_timing_delta_signs(self):
        a = timing()
        b = copy.deepcopy(a)
        b["profiles"][0]["paths"]["ready"].update(arrival_ns=1.0, slack_ns=-.1)
        delta = timing_changes(a, b, "fu")["nominal"]["paths"]["ready"]
        self.assertAlmostEqual(delta["arrival_delta_ns"], -.2)
        self.assertAlmostEqual(delta["slack_delta_ns"], .2)
        self.assertAlmostEqual(delta["arrival_reduction_percent"], 100 / 6)

    def test_sensitivity_constraint_change_rejected(self):
        a = timing()
        b = copy.deepcopy(a)
        b["profiles"][0]["load_ff"] = 1
        with self.assertRaisesRegex(ValueError, "constraint"):
            timing_changes(a, b, "fu")


if __name__ == "__main__":
    unittest.main()
