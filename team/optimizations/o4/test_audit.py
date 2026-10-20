import copy, json, tempfile, unittest
from pathlib import Path
from audit import compare_interfaces, mapping_audit
from timing import parse_path, validate_log, constant_warnings
class EvidenceGates(unittest.TestCase):
    def test_arrival_uses_positive_path_not_slack_subtraction(self):
        path="Startpoint: a\nEndpoint: b\n 1.2 data arrival time\n 0.9 data required time\n -1.2 data arrival time\n -0.3 slack (VIOLATED)\n"
        self.assertEqual(parse_path(path)["arrival_ns"],1.2)
        self.assertEqual(parse_path(path)["slack_ns"],-.3)
    def test_zero_exit_with_tcl_error_is_rejected(self):
        with self.assertRaises(ValueError):validate_log("Error: invalid command\nO4_STA_COMPLETE\n")
    def test_partial_log_is_rejected(self):
        with self.assertRaises(ValueError):validate_log("OpenSTA loaded design\n")
    def test_missing_path_is_not_zero_delay(self):
        self.assertEqual(parse_path("No paths found.\n"),{"exists":False})
        with self.assertRaises(ValueError):parse_path("")
    def test_dynamic_unconstrained_endpoint_is_rejected(self):
        design={"ports":{"dynamic":{"direction":"output","bits":[12]}}}
        with self.assertRaises(ValueError):constant_warnings("Warning: There are 1 unconstrained endpoints.\n  dynamic\n",design)
    def test_only_exact_constant_warning_is_accepted(self):
        design={"ports":{"constant":{"direction":"output","bits":["0"]}}}
        self.assertEqual(constant_warnings("Warning: There are 1 unconstrained endpoints.\n  constant\n",design),["constant"])
        with self.assertRaises(ValueError):constant_warnings("Warning: There are 2 unconstrained endpoints.\n  constant\n",design)
        with self.assertRaises(ValueError):constant_warnings("Warning: no clock\n",design)
    def test_port_width_or_direction_mismatch_is_rejected(self):
        a={"x":{"width":1,"direction":"input"}}
        compare_interfaces(a,copy.deepcopy(a))
        with self.assertRaises(ValueError):compare_interfaces(a,{"x":{"width":2,"direction":"input"}})
        with self.assertRaises(ValueError):compare_interfaces(a,{"x":{"width":1,"direction":"output"}})
    def test_area_tamper_and_unknown_cell_are_rejected(self):
        # Minimal independently assembled mapped fixture, not a copy of synthesis output.
        from hashlib import sha256
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp); lib=d/"cell.lib";lib.write_text("cell (DFF_X1) { area : 2.0; }\n")
            net=d/"mapped.v";net.write_text("fixture")
            m={"modules":{"top":{"cells":{"r":{"type":"DFF_X1"}}}}}
            (d/"mapped.json").write_text(json.dumps(m));(d/"synthesis.log").write_text("Chip area for module top: 2.0\n")
            digest=lambda p:sha256(p.read_bytes()).hexdigest()
            s={"pass":True,"top":"top","library_sha256":digest(lib),"mapped_sha256":digest(net),"mapped_json_sha256":digest(d/"mapped.json"),"cell_histogram":{"DFF_X1":1},"cell_area_sum":2.0}
            (d/"summary.json").write_text(json.dumps(s));mapping_audit(d,lib)
            s["cell_area_sum"]=1.0;(d/"summary.json").write_text(json.dumps(s))
            with self.assertRaises(ValueError):mapping_audit(d,lib)
            s["cell_area_sum"]=2;m["modules"]["top"]["cells"]["r"]["type"]="UNKNOWN"
            (d/"mapped.json").write_text(json.dumps(m));s["mapped_json_sha256"]=digest(d/"mapped.json")
            (d/"summary.json").write_text(json.dumps(s))
            with self.assertRaises(ValueError):mapping_audit(d,lib)
if __name__=="__main__":unittest.main()
