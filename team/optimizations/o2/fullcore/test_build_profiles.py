"""Observation choices must not weaken native tool selection or replay identity."""
import copy
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import build_fullcore as build
import build_recipe as recipe
import split_recipe as split


def contract(profile="direct"):
    roles = ("cxx", "cc", "java", "bash", "sh", "time", "mill", "verilator", "verilator_bin", "firtool")
    item = dict(schema=2, make_args=list(recipe.MAKE_ARGS), environment_sha256="a" * 64,
                recipe_sha256="b" * 64, mill_launch=["/tools/sh", "/tools/mill"],
                launch_metadata={".mill-version": dict(value="0.12.3", sha256="c" * 64)},
                compilers={k: dict(path="/tools/" + k, version="fixture", sha256="d" * 64) for k in roles})
    if profile != "direct":
        item.update(schema=3, profile=profile, phases=copy.deepcopy(recipe.SPLIT_PHASES),
                    make_args=list(recipe.SPLIT_MAKE_ARGS), split_script_sha256="e" * 64,
                    compiler_commands=dict(recipe.CLANG_COMMANDS), native_link=dict(recipe.CLANG_LINK),
                    verilator_support=dict(root="/runtime", files={n: "f" * 64 for n in
                        ("include/verilated.mk", "include/verilated.h", "include/verilated.cpp", "bin/verilator_includer")}),
                    compiler_runtime=dict(roles=list(recipe.NATIVE_RUNTIME_ROLES), files={
                        "/lib/libclang-cpp.so.19": "f" * 64, "/lib/libLLVM.so.19": "f" * 64}))
        for k in ("python", "make", "ar", "ld", "ldd", "perl"):
            item["compilers"][k] = dict(path="/tools/" + k, version="fixture", sha256="d" * 64)
        for role, name in recipe.CLANG_COMMANDS.items():
            item["compilers"][role].update(path="/tools/" + name, payload_path="/payload/clang",
                                           version="clang version 19.1.1")
    return item


class BuildProfiles(unittest.TestCase):
    def test_probe_binds_selected_firtool_bytes_even_if_version_is_identical(self):
        import test_build_recipe
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tools = test_build_recipe.NativePayloads().tools(root)
            chosen = root / "explicit bin"
            chosen.mkdir()
            executable = chosen / "firtool"
            executable.write_bytes(b"first selected implementation")
            selected_commands = []
            def which(name):
                selected_commands.append(name)
                return str(executable) if name == str(executable) else str(tools[Path(name).name])
            with patch.object(recipe.shutil, "which", side_effect=which), \
                    patch.object(recipe.subprocess, "check_output", return_value="identical version"):
                before = recipe.probe_tools(firtool_dir=chosen)
                executable.write_bytes(b"second selected implementation")
                after = recipe.probe_tools(firtool_dir=chosen)
            self.assertIn(str(executable), selected_commands)
            self.assertEqual(before["firtool"]["path"], str(executable.resolve()))
            self.assertEqual(before["firtool"]["version"], after["firtool"]["version"])
            self.assertNotEqual(before["firtool"]["sha256"], after["firtool"]["sha256"])

    def test_trace_and_recipe_are_independent_and_default_is_observe(self):
        for profile in ("direct", "split-clang-v2"):
            for trace in ("observe", "cost"):
                item = contract(profile)
                flags = build.profile_flags(trace)
                shell = build.build_shell(item, flags, Path("/pins.json"), Path("/receipt"))
                self.assertEqual(flags["VDOT_O1_HANDOFF"], "0")
                self.assertEqual(flags["VDOT_O2_ELASTIC"], "1")
                self.assertEqual(flags["VDOT_T14_FUSED_INPUT"], "1")
                self.assertEqual(flags["VDOT_O2_TRACE"], "1" if trace == "observe" else "0")
                self.assertEqual(flags["VDOT_T13_TRACE"], "1" if trace == "observe" else "0")
                self.assertEqual(flags["VDOT_O1_TRACE"], "0")
                self.assertEqual(flags["VDOT_T12_TRACE"], "0")
                self.assertIn("export CHISEL_FIRTOOL_PATH=/tools\n", shell)
                self.assertEqual("split_recipe.py" in shell, profile != "direct")
        self.assertEqual(build.profile_flags("observe"), build.FLAGS)
        with self.assertRaises(ValueError):
            build.profile_flags("split-clang-v2")

    @unittest.skipUnless(os.name == "posix", "real POSIX quoting")
    def test_explicit_directory_reaches_shell_and_split_without_evaluation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "team/scripts").mkdir(parents=True)
            (root / "team/scripts/activate.sh").write_text("")
            directory = str(root / "firtool 'quoted' $(touch SHOULD_NOT_EXIST) bin")
            item = contract("split-clang-v2")
            item["firtool_directory"] = directory
            command = shlex.join([sys.executable, "-c", "import os; print(os.environ['CHISEL_FIRTOOL_PATH'])"]) + "\n"
            with patch.object(recipe, "execution_command", return_value=command):
                shell = build.build_shell(item, build.profile_flags("cost"), root / "pins", root)
            result = subprocess.check_output(["bash", "-c", shell], cwd=root, text=True)
            self.assertEqual(result.strip(), directory)
            self.assertFalse((root / "SHOULD_NOT_EXIST").exists())
            with patch.dict(os.environ, {"CHISEL_FIRTOOL_PATH": directory}, clear=True):
                self.assertEqual(split.environment(dict(native_build_contract=item))["CHISEL_FIRTOOL_PATH"], directory)
            with patch.dict(os.environ, {"CHISEL_FIRTOOL_PATH": "/foreign"}, clear=True), self.assertRaisesRegex(ValueError, "firtool configuration"):
                split.environment(dict(native_build_contract=item))

    def test_explicit_selection_recaptured_and_legacy_shape_preserved(self):
        for profile in ("direct", "split-clang-v2"):
            item = contract(profile)
            with patch.object(recipe, "capture", return_value=item) as capture:
                recipe.verify(Path("/repo"), item)
            capture.assert_called_once_with(Path("/repo"), profile)
            item["firtool_directory"] = "/chosen/compiler"
            with patch.object(recipe, "capture", return_value=item) as capture:
                recipe.verify(Path("/repo"), item)
            capture.assert_called_once_with(Path("/repo"), profile, firtool_dir="/chosen/compiler")
            changed = copy.deepcopy(item)
            changed["compilers"]["firtool"]["sha256"] = "0" * 64
            with patch.object(recipe, "capture", return_value=changed), self.assertRaisesRegex(ValueError, "contract changed"):
                recipe.verify(Path("/repo"), item)
        for selection in (None, "relative", "/path/../other", 7):
            item = contract(); item["firtool_directory"] = selection
            with self.assertRaises(ValueError):
                recipe.validate(item)

    @unittest.skipUnless(os.name == "posix", "native POSIX capture")
    def test_capture_passes_explicit_selector_to_probe_and_binds_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".mill-version").write_bytes(b"0.12.3\n")
            for profile in ("direct", "split-clang-v2"):
                item = contract(profile)
                captured = item["compilers"] if profile == "direct" else {k: item[k] for k in
                    ("compilers", "verilator_support", "compiler_runtime")}
                with patch.object(recipe.subprocess, "check_output", return_value=json.dumps(captured)) as probe:
                    plain = recipe.capture(root, profile)
                    explicit = recipe.capture(root, profile, root / "custom bin")
                self.assertNotIn("firtool_directory", plain)
                self.assertEqual(explicit["firtool_directory"], str(root / "custom bin"))
                self.assertIn("firtool_dir", probe.call_args.args[0][2])
                recipe.validate(explicit)


if __name__ == "__main__":
    unittest.main()
