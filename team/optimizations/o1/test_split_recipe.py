"""Explicit split profile, process sequencing and failure-preservation checks."""
import copy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import build_recipe as recipe
import split_recipe as split


def contract():
    roles = ("cxx", "cc", "java", "bash", "sh", "time", "mill", "verilator", "verilator_bin", "firtool", "python", "make")
    return dict(schema=3, profile="split-v1", make_args=list(recipe.SPLIT_MAKE_ARGS),
                phases=copy.deepcopy(recipe.SPLIT_PHASES), recipe_sha256="a"*64, split_script_sha256="b"*64,
                environment_sha256="c"*64, mill_launch=["/tools/sh", "/tools/mill"],
                launch_metadata={".mill-version": dict(value="0.12.3", sha256="d"*64)},
                compilers={role: dict(path="/tools/"+role, sha256="e"*64, version="fixture") for role in roles})


def clang_contract():
    item = contract()
    item.update(profile="split-clang-v1", compiler_commands=dict(recipe.CLANG_COMMANDS))
    for role, command in recipe.CLANG_COMMANDS.items():
        item["compilers"][role].update(path="/usr/bin/" + command,
            payload_path="/usr/lib/llvm-19/bin/clang", version="Ubuntu clang version 19.1.7\n")
    return item


class SplitProfile(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix", "native POSIX driver symlink contract")
    def test_clang_driver_target_drift_is_rejected_even_with_identical_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            item = clang_contract()
            (root / ".mill-version").write_bytes(b"0.12.3\n")
            item["launch_metadata"][".mill-version"]["sha256"] = split.sha(root / ".mill-version")
            item["split_script_sha256"] = split.sha(split.__file__)
            item["recipe_sha256"] = split.sha(recipe.__file__)
            payload = root / "clang-payload"
            payload.write_bytes(b"same compiler bytes")
            for name, tool in item["compilers"].items():
                path = root / recipe.CLANG_COMMANDS.get(name, name)
                if name in recipe.CLANG_COMMANDS:
                    path.symlink_to(payload)
                    tool["payload_path"] = str(payload)
                else:
                    path.write_bytes(name.encode())
                tool.update(path=str(path), sha256=split.sha(path))
            item["mill_launch"] = [item["compilers"][role]["path"] for role in ("sh", "mill")]
            selected = {name: item["compilers"][role]["path"] for name, role in
                        (("mill", "mill"), ("java", "java"), ("verilator", "verilator"), ("python3", "python"))}
            with patch.object(split.shutil, "which", side_effect=selected.get):
                split.verify_tools(item, root)
                replacement = root / "other-clang-payload"
                replacement.write_bytes(payload.read_bytes())
                driver = Path(item["compilers"]["cxx"]["path"])
                driver.unlink()
                driver.symlink_to(replacement)
                with self.assertRaisesRegex(ValueError, "payload target changed"):
                    split.verify_tools(item, root)

    def test_clang_capture_preserves_profile_and_compiler_driver_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".mill-version").write_bytes(b"0.12.3\n")
            tools = clang_contract()["compilers"]
            with patch.object(recipe.subprocess, "check_output", return_value=json.dumps(tools)) as probe:
                item = recipe.capture(root, "split-clang-v1")
            recipe.validate(item)
            self.assertEqual(item["schema"], 3)
            self.assertEqual(item["profile"], "split-clang-v1")
            self.assertEqual(item["compiler_commands"], recipe.CLANG_COMMANDS)
            self.assertIn("split-clang-v1", probe.call_args.args[0][2])
            commands = split.commands(item)
            for phase in ("fir-elaborate", "native-compile"):
                self.assertIn("CXX=/usr/bin/clang++-19", commands[phase])
                self.assertIn("CC=/usr/bin/clang-19", commands[phase])
                self.assertNotIn("CXX=/usr/lib/llvm-19/bin/clang", commands[phase])
            self.assertEqual(item["phases"], recipe.SPLIT_PHASES)
            self.assertEqual(item["make_args"], recipe.SPLIT_MAKE_ARGS)
            with patch.object(recipe, "capture", return_value=item) as capture:
                recipe.verify(root, item)
            capture.assert_called_once_with(root, "split-clang-v1")

    def test_clang_profile_rejects_mixed_contract_and_wrong_driver(self):
        for mutate in (lambda c: c.update(profile="split-v1"), lambda c: c.pop("compiler_commands"),
                       lambda c: c["compiler_commands"].update(cxx="g++"),
                       lambda c: c["compilers"]["cxx"].update(path="/usr/lib/llvm-19/bin/clang"),
                       lambda c: c["compilers"]["cc"].update(version="clang version 18.1.8"),
                       lambda c: c["compilers"]["cxx"].pop("payload_path"),
                       lambda c: c.update(make_args=recipe.MAKE_ARGS)):
            changed = clang_contract()
            mutate(changed)
            with self.assertRaises(ValueError):
                recipe.validate(changed)
        changed = contract()
        changed["profile"] = "split-clang-v1"
        with self.assertRaises(ValueError):
            recipe.validate(changed)

    @unittest.skipUnless(os.name == "posix", "native POSIX tool path contract")
    def test_path_python_cannot_override_bound_mem_generator_interpreter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);item=contract()
            (root/".mill-version").write_bytes(b"0.12.3\n")
            item["launch_metadata"][".mill-version"]["sha256"]=split.sha(root/".mill-version")
            item["split_script_sha256"]=split.sha(split.__file__)
            item["recipe_sha256"]=split.sha(recipe.__file__)
            for name,tool in item["compilers"].items():
                path=root/name;path.write_bytes(name.encode())
                tool.update(path=str(path),sha256=split.sha(path))
            item["mill_launch"]=[item["compilers"][name]["path"] for name in ("sh","mill")]
            selected={name:item["compilers"][role]["path"] for name,role in
                      (("mill","mill"),("java","java"),("verilator","verilator"),("python3","python"))}
            with patch.object(split.shutil,"which",side_effect=selected.get):split.verify_tools(item,root)
            selected["python3"]=str(root/"foreign-python")
            with patch.object(split.shutil,"which",side_effect=selected.get), \
                    self.assertRaisesRegex(ValueError,"activated native tool differs: python3"):
                split.verify_tools(item,root)

    def test_cannot_mix_direct_and_split_contracts(self):
        item = contract()
        recipe.validate(item)
        for mutate in (lambda c: c.update(schema=2), lambda c: c.update(make_args=recipe.MAKE_ARGS),
                       lambda c: c["phases"][2]["firtool_args"].remove("--mlir-disable-threading"),
                       lambda c: c["phases"][0]["environment"].update(JAVA_OPTS="-Xmx12G"),
                       lambda c: c.pop("split_script_sha256"), lambda c: c["compilers"].pop("python")):
            changed=copy.deepcopy(item);mutate(changed)
            with self.assertRaises(ValueError):recipe.validate(changed)

    def test_phase_commands_preserve_gcc_trace_and_memory_contract(self):
        item=contract();commands=split.commands(item)
        self.assertEqual(commands["scala-compile"][:2],item["mill_launch"])
        self.assertIn("CHISEL_TARGET=chirrtl",commands["fir-elaborate"])
        self.assertIn("--mlir-disable-threading",commands["fir-lower"])
        final=commands["native-compile"]
        for value in ("JVM_XMX=6G","JVM_XSS=16m","EMU_TRACE=0","OPT_FAST=-O3","OPT_SLOW=-O0","-j2","CXX=/tools/cxx"):
            self.assertIn(value,final)
        self.assertNotIn("JVM_XMX=12G",final)
        script=recipe.execution_command(item,"/receipt/pins.json","/receipt")
        self.assertIn("/tools/python",script)
        self.assertIn("split_recipe.py",script)
        self.assertIn(str(Path("/receipt") / "split"),script)

    def test_verify_recaptures_selected_profile(self):
        item=contract()
        with patch.object(recipe,"capture",return_value=item) as capture:
            recipe.verify(Path("/repo"),item)
        capture.assert_called_once_with(Path("/repo"),"split-v1")

    def test_postprocess_preserves_assertions_and_error_reporting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);rtl=root/"build/rtl";rtl.mkdir(parents=True)
            top=rtl/"SimTop.sv";top.write_bytes(b"module SimTop; initial begin $fatal; $error(\"bad\"); end endmodule\n")
            with patch.object(split.subprocess,"check_output",side_effect=[b"commit fixture\n",b""]):
                split.postprocess(root)
            body=top.read_bytes()
            self.assertTrue(body.startswith(b"//commit fixture\n"))
            self.assertIn(b"xs_assert_v2(`__FILE__, `__LINE__)",body)
            self.assertIn(b"$fwrite(32'h80000002, ",body)
            self.assertNotIn(b"$fatal",body)


class SplitExecution(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=(self.base/"repo").resolve();self.root.mkdir()
        self.output=self.base/"receipt"
        self.pins=self.base/"pins.json"
        self.pins.write_text(json.dumps(dict(source_root=str(self.root),native_build_contract=contract())))
        self.calls=[]

    def process(self,command,**kwargs):
        state=json.loads((self.output/"state.json").read_text())
        phase=state["phases"][-1]["name"]
        self.assertTrue(all(row["status"]=="PASS" for row in state["phases"][:-1]))
        self.calls.append(phase)
        rtl=self.root/"build/rtl"
        if phase=="fir-elaborate":
            rtl.mkdir(parents=True);(rtl/"SimTop.fir").write_bytes(b"fresh FIR")
        elif phase=="fir-lower":
            (rtl/"SimTop.sv").write_bytes(b"module SimTop; $fatal; endmodule\n")
            (rtl/"SimTop.sv.conf").write_bytes(b"memory config")
        elif phase=="native-compile":
            (self.root/"build/emu").write_bytes(b"new EMU")
        return SimpleNamespace(returncode=0)

    def execute(self,process=None):
        with patch.object(split,"verify_tools"),patch.object(split.subprocess,"run",side_effect=process or self.process), \
                patch.object(split.subprocess,"check_output",return_value=b"commit fixture\n"):
            return split.run(self.pins,self.output,self.root)

    def test_success_has_exact_order_separate_phases_and_unchanged_prepared_rtl(self):
        self.assertEqual(self.execute(),0)
        state=json.loads((self.output/"state.json").read_text())
        self.assertEqual(state["status"],"SPLIT_NATIVE_BUILD_PASS")
        self.assertEqual([row["name"] for row in state["phases"]],[row["name"] for row in recipe.SPLIT_PHASES])
        self.assertTrue(all(row["status"]=="PASS" for row in state["phases"]))
        self.assertEqual(json.loads((self.output/"prepared-rtl.json").read_text()),split.rtl_inventory(self.root))
        self.assertEqual(self.calls,["scala-compile","fir-elaborate","fir-lower","memory-generate","native-compile"])

    def test_clang_run_retains_explicit_profile_and_cpp_driver_command(self):
        self.pins.write_text(json.dumps(dict(source_root=str(self.root), native_build_contract=clang_contract())))
        self.assertEqual(self.execute(), 0)
        state = json.loads((self.output / "state.json").read_text())
        self.assertEqual(state["profile"], "split-clang-v1")
        self.assertEqual(state["status"], "SPLIT_NATIVE_BUILD_PASS")
        final = state["phases"][-1]["command"]
        for arg in ("CXX=/usr/bin/clang++-19", "CC=/usr/bin/clang-19", "OPT_FAST=-O3", "OPT_SLOW=-O0", "EMU_TRACE=0"):
            self.assertIn(arg, final)

    def test_failed_lowering_retains_exit_and_never_starts_native_compile(self):
        def fail(command,**kwargs):
            result=self.process(command,**kwargs)
            return SimpleNamespace(returncode=7) if self.calls[-1]=="fir-lower" else result
        with self.assertRaisesRegex(ValueError,"phase failed: fir-lower"):self.execute(fail)
        state=json.loads((self.output/"state.json").read_text())
        self.assertEqual(state["status"],"FAILED")
        self.assertEqual(state["phases"][-1]["exit_code"],7)
        self.assertNotIn("native-compile",self.calls)
        self.assertTrue((self.root/"build/rtl/SimTop.fir").exists())

    def test_make_regeneration_is_rejected_after_real_zero_exit(self):
        def regenerate(command,**kwargs):
            result=self.process(command,**kwargs)
            if self.calls[-1]=="native-compile":(self.root/"build/rtl/SimTop.sv").write_bytes(b"regenerated")
            return result
        with self.assertRaisesRegex(ValueError,"Make regenerated"):self.execute(regenerate)
        state=json.loads((self.output/"state.json").read_text())
        self.assertEqual(state["status"],"FAILED")
        self.assertEqual(state["phases"][-1]["exit_code"],0)

    def test_existing_build_is_preserved_and_rejected(self):
        existing=self.root/"build";existing.mkdir();(existing/"old.txt").write_bytes(b"preserve")
        with self.assertRaisesRegex(ValueError,"must not reuse"):self.execute()
        self.assertEqual((existing/"old.txt").read_bytes(),b"preserve")
        self.assertFalse(self.output.exists())


if __name__=="__main__":unittest.main()
