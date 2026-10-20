import copy, gzip, hashlib, json, subprocess, sys, tempfile, unittest
from unittest.mock import patch
from types import SimpleNamespace
import elaborate
from pathlib import Path
from audit import compare_interfaces, mapping_audit, timing_audit, validate_profiles, validate_tcl, verify_rtl
from timing import parse_path, validate_log, constant_warnings
class EvidenceGates(unittest.TestCase):
    def test_arrival_uses_positive_path_not_slack_subtraction(self):
        path="Startpoint: a\nEndpoint: b\n 1.2 data arrival time\n 0.9 data required time\n -1.2 data arrival time\n -0.3 slack (VIOLATED)\n"
        self.assertEqual(parse_path(path)["arrival_ns"],1.2)
        self.assertEqual(parse_path(path)["slack_ns"],-.3)
    def test_zero_exit_with_tcl_error_is_rejected(self):
        with self.assertRaises(ValueError):validate_log("Error: invalid command\nO4_STA_COMPLETE\n")
    def test_unbound_pin_even_without_tcl_error_is_rejected(self):
        with self.assertRaises(ValueError):validate_log("Warning: pin x not found.\nO4_STA_COMPLETE\n")
    def test_multiple_paths_cannot_mix_arrival_and_slack(self):
        text="Startpoint: a\nEndpoint: b\n 1.2 data arrival time\n -0.3 slack (VIOLATED)\n"
        with self.assertRaises(ValueError):parse_path(text+text)
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
    def test_icg_test_pin_requires_proven_case_zero_connection(self):
        design={"ports":{"testEnable":{"direction":"input","bits":[9]}},"cells":{"g":{"type":"CLKGATETST_X1","connections":{"SE":[9]}}}}
        warning="Warning: There are 1 unconstrained endpoints.\n  g/SE\n"
        with self.assertRaises(ValueError):constant_warnings(warning,design)
        self.assertEqual(constant_warnings(warning,design,["testEnable"]),["g/SE"])
        design["cells"]["g"]["connections"]["SE"]=[10]
        with self.assertRaises(ValueError):constant_warnings(warning,design,["testEnable"])
    def test_port_width_or_direction_mismatch_is_rejected(self):
        a={"x":{"width":1,"direction":"input"}}
        compare_interfaces(a,copy.deepcopy(a))
        with self.assertRaises(ValueError):compare_interfaces(a,{"x":{"width":2,"direction":"input"}})
        with self.assertRaises(ValueError):compare_interfaces(a,{"x":{"width":1,"direction":"output"}})
    def test_connection_proof_ignores_names_but_rejects_rewired_dff(self):
        from compact import topology
        from canonical import emit,bind
        old={"ports":{"clock":{"direction":"input","bits":[1]},"data":{"direction":"input","bits":[2]},"q":{"direction":"output","bits":[3]}},"netnames":{},"cells":{"original":{"type":"DFF_X1","parameters":{},"attributes":{},"port_directions":{"CK":"input","D":"input","Q":"output"},"connections":{"CK":[1],"D":[2],"Q":[3]}}}}
        new=copy.deepcopy(old)
        new["cells"]={"c0":new["cells"].pop("original")}
        bind(new,old,{"c0":"original"})
        self.assertEqual(topology(old),topology(new,True))
        new["cells"]["c0"]["connections"]["D"]=[1]
        self.assertNotEqual(topology(old),topology(new,True))
    def test_canonical_writer_emits_only_scalar_aliases(self):
        from canonical import emit
        m={"ports":{"x":{"direction":"input","bits":[1,2]},"y":{"direction":"output","bits":[1,2]}},"cells":{}}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"net.v";emit(m,"top",path)
            self.assertIn("assign n1 = x[0];",path.read_text())
            self.assertIn("assign y[1] = n2;",path.read_text())
            self.assertNotIn("assign {",path.read_text())
    def test_area_tamper_and_unknown_cell_are_rejected(self):
        # Minimal independently assembled mapped fixture, not a copy of synthesis output.
        from hashlib import sha256
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp); lib=d/"cell.lib";lib.write_text("cell (DFF_X1) { area : 2.0; }\n")
            net=d/"mapped.v";net.write_text("fixture")
            m={"modules":{"top":{"ports":{"x":{"direction":"input","bits":[1]}},"cells":{"r":{"type":"DFF_X1"}}}}}
            (d/"mapped.json").write_text(json.dumps(m));(d/"synthesis.log").write_text("Chip area for module top: 2.0\n")
            digest=lambda p:sha256(p.read_bytes()).hexdigest()
            s={"pass":True,"exit_code":0,"cell_count":1,"ports":{"x":{"direction":"input","width":1}},"top":"top","library_sha256":digest(lib),"mapped_sha256":digest(net),"mapped_json_sha256":digest(d/"mapped.json"),"cell_histogram":{"DFF_X1":1},"cell_area_sum":2.0}
            (d/"summary.json").write_text(json.dumps(s));mapping_audit(d,lib)
            for mutate in (lambda r:r.update(cell_count=True),lambda r:r.update(cell_count=2),lambda r:r["ports"]["x"].update(width=2)):
                bad=copy.deepcopy(s);mutate(bad);(d/"summary.json").write_text(json.dumps(bad))
                with self.assertRaises(ValueError):mapping_audit(d,lib)
            s["cell_area_sum"]=1.0;(d/"summary.json").write_text(json.dumps(s))
            with self.assertRaises(ValueError):mapping_audit(d,lib)
            s["cell_area_sum"]=2;m["modules"]["top"]["cells"]["r"]["type"]="UNKNOWN"
            (d/"mapped.json").write_text(json.dumps(m));s["mapped_json_sha256"]=digest(d/"mapped.json")
            (d/"summary.json").write_text(json.dumps(s))
            with self.assertRaises(ValueError):mapping_audit(d,lib)



EVIDENCE=Path(__file__).resolve().parent/"evidence/20261020-cost"


def frozen(relative):
    p=EVIDENCE/"files"/relative
    return p.read_bytes() if p.exists() else gzip.decompress(p.with_name(p.name+".gz").read_bytes())


def assessment():return json.loads(frozen("assessment.json"))


class CompleteTimingGates(unittest.TestCase):
    def test_complete_real_profiles_and_actual_tcl(self):
        for key,row in assessment()["results"].items():
            summary=row["timing"]
            self.assertEqual(len(validate_profiles(summary)),5)
            folder={"o1-fu":"o1-fu-sta-03","o2-fu":"o2-fu-sta-02","o1-parent":"o1-parent-sta-08","o2-parent":"o2-parent-sta-01"}[key]
            for profile in summary["profiles"]:
                validate_tcl(frozen(folder+"/"+profile["profile"]+"/timing.tcl").decode(),profile,summary["boundary"])

    def test_missing_extra_and_empty_path_sets_rejected(self):
        for key,row in assessment()["results"].items():
            original=row["timing"]
            for mutation in (lambda p:p.update(paths={}),lambda p:p["paths"].pop("r2r"),
                             lambda p:p["paths"].update(extra=copy.deepcopy(p["paths"]["r2r"]))):
                value=copy.deepcopy(original);mutation(value["profiles"][0])
                with self.subTest(key=key),self.assertRaisesRegex(ValueError,"path inventory"):validate_profiles(value)

    def test_all_parent_special_paths_are_required(self):
        original=assessment()["results"]["o2-parent"]["timing"]
        for key in ("vdot_r2r","vdot_i2r","vdot_r2o","gate_enable"):
            value=copy.deepcopy(original);value["profiles"][0]["paths"].pop(key)
            with self.subTest(key=key),self.assertRaises(ValueError):validate_profiles(value)

    def test_numeric_boolean_nonfinite_and_profile_duplicates_rejected(self):
        original=assessment()["results"]["o1-fu"]["timing"]
        for mutation in (lambda s:s["profiles"][0].update(period_ns=True),lambda s:s["profiles"][0].update(load_ff=float("nan")),
                         lambda s:s["profiles"][0]["paths"]["r2r"].update(exists=1),
                         lambda s:s["profiles"][0]["paths"]["r2r"].update(arrival_ns=float("inf")),
                         lambda s:s["profiles"][0]["paths"]["r2r"].update(slack_ns=True),
                         lambda s:s["profiles"].__setitem__(1,copy.deepcopy(s["profiles"][0]))):
            value=copy.deepcopy(original);mutation(value)
            with self.assertRaises(ValueError):validate_profiles(value)

    def test_tcl_overrides_missing_reports_and_wrong_selectors_rejected(self):
        profile=assessment()["results"]["o1-fu"]["timing"]["profiles"][0]
        text=frozen("o1-fu-sta-03/nominal/timing.tcl").decode()
        for mutate in (lambda t:t+"set_load 20 $outputs\n",lambda t:t+"set_false_path -from [all_inputs]\n",
                       lambda t:t.replace("set inputs {}","set inputs [get_ports reset]"),
                       lambda t:t.replace("-from $q -to $d","-from $inputs -to $d"),
                       lambda t:"\n".join(line for line in t.splitlines() if not line.endswith("/ready.rpt"))):
            with self.assertRaises(ValueError):validate_tcl(mutate(text),profile,"fu")

    def test_path_nonfinite_duplicate_slack_or_mixed_no_path_rejected(self):
        valid="Startpoint: a\nEndpoint: b\n 1.2 data arrival time\n -0.3 slack (VIOLATED)\n"
        for text in (valid+" -0.2 slack (VIOLATED)\n",valid+"No paths found.\n",
                     valid.replace("1.2", "9"*400)):
            with self.assertRaises(ValueError):parse_path(text)

    def test_actual_frozen_fu_audit_and_empty_paths_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);manifest=json.loads((EVIDENCE/"manifest.json").read_text())
            prefixes=("o1-fu-map-02/","o1-fu-sta-03/")
            for record in manifest["entries"]:
                if record["path"].startswith(prefixes):
                    data=(EVIDENCE/"files"/record["stored"]).read_bytes()
                    if record["gzip"]:data=gzip.decompress(data)
                    self.assertEqual(hashlib.sha256(data).hexdigest(),record["sha256"])
                    path=root/record["path"];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
            mapping=root/"o1-fu-map-02";directory=root/"o1-fu-sta-03"
            metadata=json.loads((mapping/"summary.json").read_text())
            design=json.loads((mapping/"mapped.json").read_text())["modules"][metadata["top"]]
            summary=timing_audit(directory,mapping,design)
            summary["profiles"][0]["paths"]={};(directory/"summary.json").write_text(json.dumps(summary))
            with self.assertRaisesRegex(ValueError,"path inventory"):timing_audit(directory,mapping,design)

    def test_rtl_inventory_empty_missing_extra_and_size_boolean_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/"rtl").mkdir()
            names=["filelist.f","VDotProducts.sv","VDotReduce.sv","CommonFuCostTop.sv"]
            for name in names:(root/"rtl"/name).write_bytes(b"x")
            receipt=dict(boundary="fu",rtl={"rtl/"+name:dict(bytes=1,sha256=hashlib.sha256(b"x").hexdigest()) for name in names})
            verify_rtl(root,receipt)
            for mutate in (lambda r:r.update(rtl={}),lambda r:r["rtl"].pop("rtl/filelist.f"),
                           lambda r:r["rtl"]["rtl/filelist.f"].update(bytes=True)):
                bad=copy.deepcopy(receipt);mutate(bad)
                with self.assertRaises(ValueError):verify_rtl(root,bad)
            (root/"rtl/unrecorded.sv").write_text("new input")
            with self.assertRaises(ValueError):verify_rtl(root,receipt)

    def test_live_cli_rejects_invalid_receipts_under_optimized_python(self):
        here=Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for script,filename,body in (("timing.py","summary.json",dict(pass_flag=False)),("synthesize.py","result.json",dict(exit_code=True))):
                directory=root/script;directory.mkdir();(directory/filename).write_text(json.dumps(body))
                result=subprocess.run([sys.executable,"-B","-OO",str(here/script),str(directory),str(root/(script+"-out"))],capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0)
                self.assertIn("ValueError",result.stderr)
                self.assertFalse((root/(script+"-out")).exists())




class LiveGenerationSources(unittest.TestCase):
    def fixture(self, root):
        (root/"src").mkdir();(root/"src/A.scala").write_text("object A {}")
        for name in ("team/optimizations/o4/GenerateVDotCost.scala","team/optimizations/o4/elaborate.py"):
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text("reviewed source")
        subprocess.run(["git","init","-q",str(root)],check=True)
        subprocess.run(["git","-C",str(root),"add","."],check=True)
        subprocess.run(["git","-C",str(root),"-c","user.name=O4 Test","-c","user.email=o4-test@example.invalid","commit","-qm","fixture"],check=True)

    def test_clean_compiler_and_harness_sources_bound(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(elaborate.live_inputs,"dependency_snapshot",return_value=([],{})):
            root=Path(tmp);self.fixture(root)
            receipt=elaborate.capture_sources(root)
            self.assertIn("src/A.scala",receipt["files"])
            self.assertIn("team/optimizations/o4/GenerateVDotCost.scala",receipt["files"])
            elaborate.verify_sources(root,receipt)

    def test_dirty_harness_or_production_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(elaborate.live_inputs,"dependency_snapshot",return_value=([],{})):
            root=Path(tmp);self.fixture(root)
            for name in ("src/A.scala","team/optimizations/o4/GenerateVDotCost.scala"):
                path=root/name;original=path.read_bytes();path.write_bytes(original+b"\nchanged")
                with self.assertRaisesRegex(ValueError,"commit O4 compiler"):elaborate.capture_sources(root)
                path.write_bytes(original)

    def test_new_untracked_compiler_input_rejected_after_capture(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(elaborate.live_inputs,"dependency_snapshot",return_value=([],{})):
            root=Path(tmp);self.fixture(root);receipt=elaborate.capture_sources(root)
            (root/"src/New.scala").write_text("new compiler input")
            with self.assertRaises(ValueError):elaborate.verify_sources(root,receipt)

    def test_changed_head_rejected_even_if_compiler_files_identical(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(elaborate.live_inputs,"dependency_snapshot",return_value=([],{})):
            root=Path(tmp);self.fixture(root);receipt=elaborate.capture_sources(root)
            subprocess.run(["git","-C",str(root),"-c","user.name=O4 Test","-c","user.email=o4-test@example.invalid","commit","-qm","new identity","--allow-empty"],check=True)
            with self.assertRaisesRegex(ValueError,"compiler inputs changed"):elaborate.verify_sources(root,receipt)




class GenerationFailureReceipt(unittest.TestCase):
    def test_real_tool_zero_does_not_accept_failed_source_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/"attempt"
            args=SimpleNamespace(mode="o1",boundary="fu",output=output)
            source=dict(source_commit="a"*40,files={"src/A.scala":"a"*64})
            native=dict(compilers=dict(firtool=dict(path="/actual/tools/firtool")))
            with patch.object(elaborate.argparse.ArgumentParser,"parse_args",return_value=args),patch.object(elaborate,"capture_sources",return_value=source),patch.object(elaborate,"verify_sources",side_effect=ValueError("source drift")),patch.object(elaborate.build_recipe,"capture",return_value=native),patch.object(elaborate.subprocess,"run",return_value=SimpleNamespace(returncode=0)):
                with self.assertRaises(SystemExit) as stopped:elaborate.main()
            self.assertEqual(stopped.exception.code,1)
            result=json.loads((output/"result.json").read_text())
            self.assertEqual(result["tool_exit_code"],0)
            self.assertEqual(result["exit_code"],1)
            self.assertIs(result["source_inputs_unchanged"],False)
            self.assertIn("source drift",result["verification_error"])
            self.assertEqual(result["command"][1],"-c")
            self.assertIn(str(Path("/actual/tools/firtool").parent),result["command"][2])

if __name__=="__main__":unittest.main()
