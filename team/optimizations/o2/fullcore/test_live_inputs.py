"""Reject additions, omissions and dependency drift at live reuse boundaries."""
from pathlib import Path
import copy
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import live_inputs


class InventoryTests(unittest.TestCase):
    def test_live_g3_boundary_accepts_schema3_and_rejects_changed_lowering_phase(self):
        recipe = live_inputs.build_recipe
        roles = ("cxx", "cc", "java", "bash", "sh", "time", "mill", "verilator", "verilator_bin",
                 "firtool", "python", "make")
        contract = dict(schema=3, profile="split-v1", make_args=list(recipe.SPLIT_MAKE_ARGS),
            phases=copy.deepcopy(recipe.SPLIT_PHASES), recipe_sha256="a" * 64,
            split_script_sha256="b" * 64, environment_sha256="c" * 64,
            mill_launch=["/tools/sh", "/tools/mill"],
            launch_metadata={".mill-version": dict(value="0.12.3", sha256="d" * 64)},
            compilers={role: dict(path="/tools/" + role, sha256="e" * 64, version="fixture") for role in roles})
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "src").mkdir()
            (root / "src/Candidate.scala").write_bytes(b"object Candidate\n")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            inventory = live_inputs.hardware_files(root)
            dependencies = {"dependency/source.scala": "f" * 64}
            pins = dict(files=inventory, dependency_files=dependencies, native_build_contract=contract)
            # Exercise the production live G3 gate, inventory comparison and
            # schema validator; only the unrelated recursive dependency setup
            # is substituted, so this test needs no installed HDL toolchain.
            with patch("build_inputs.verify_dependencies"), \
                    patch.object(live_inputs, "dependency_snapshot", return_value=([], dependencies)):
                live_inputs.verify(root, pins)
                changed = copy.deepcopy(pins)
                changed["native_build_contract"]["phases"][2]["firtool_args"].remove("--mlir-disable-threading")
                with self.assertRaisesRegex(ValueError, "unsupported split native build contract"):
                    live_inputs.verify(root, changed)
                missing_tool = copy.deepcopy(pins)
                del missing_tool["native_build_contract"]["compilers"]["python"]
                with self.assertRaisesRegex(ValueError, "native tool identity: python"):
                    live_inputs.verify(root, missing_tool)
                linked = copy.deepcopy(pins)
                native = linked["native_build_contract"]
                native.update(profile="split-clang-v2", compiler_commands=dict(recipe.CLANG_COMMANDS),
                    native_link=dict(recipe.CLANG_LINK),
                    compiler_runtime=dict(roles=list(recipe.NATIVE_RUNTIME_ROLES), files={
                        "/lib/libclang-cpp.so.19.1": "a" * 64, "/lib/libLLVM.so.19.1": "a" * 64}),
                    verilator_support=dict(root="/verilator", files={
                        name: "a" * 64 for name in ("include/verilated.mk", "include/verilated.h",
                                                   "include/verilated.cpp", "bin/verilator_includer")}))
                for role, name in recipe.CLANG_COMMANDS.items():
                    native["compilers"][role].update(path="/tools/" + name,
                        payload_path="/tools/clang", version="clang version 19.1.1")
                for role in ("ar", "ld", "ldd", "perl"):
                    native["compilers"][role] = dict(path="/tools/" + role, sha256="a" * 64, version="fixture")
                live_inputs.verify(root, linked)
                missing_linker = copy.deepcopy(linked)
                del missing_linker["native_build_contract"]["compilers"]["ld"]
                with self.assertRaisesRegex(ValueError, "native tool identity: ld"):
                    live_inputs.verify(root, missing_linker)
                missing_template = copy.deepcopy(linked)
                del missing_template["native_build_contract"]["verilator_support"]["files"]["include/verilated.mk"]
                with self.assertRaisesRegex(ValueError, "incomplete Clang link/runtime contract"):
                    live_inputs.verify(root, missing_template)
                missing_implementation = copy.deepcopy(linked)
                del missing_implementation["native_build_contract"]["compiler_runtime"]["files"]["/lib/libclang-cpp.so.19.1"]
                with self.assertRaisesRegex(ValueError, "missing native compiler implementation libraries"):
                    live_inputs.verify(root, missing_implementation)

    def test_macro_and_untracked_additions_and_omissions_are_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root/"macros").mkdir()
            (root/"macros/A.scala").write_text("object A")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            inventory = live_inputs.hardware_files(root)
            self.assertIn("macros/A.scala", inventory)
            with patch("build_inputs.verify_dependencies"), patch.object(live_inputs, "dependency_snapshot", return_value=([], {"dep/a":"a"*64})):
                pins = dict(files=inventory,dependency_files={},native_build_contract={})
                with self.assertRaisesRegex(ValueError, "dependency compiler inventory"):
                    live_inputs.verify(root, pins)
                (root/"macros/B.scala").write_text("object B")
                with self.assertRaisesRegex(RuntimeError, "inventory changed"):
                    live_inputs.verify(root, pins)
                with self.assertRaisesRegex(RuntimeError, "inventory changed"):
                    live_inputs.verify(root, dict(pins, files={}))


if __name__ == "__main__":
    unittest.main()
