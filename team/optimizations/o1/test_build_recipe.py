"""Native compiler payload and launcher metadata acceptance boundaries."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import shlex
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import build_inputs
import build_recipe as recipe


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class NativePayloads(unittest.TestCase):
    def tools(self, folder):
        tools = {name: folder / name for name in
                 ("g++", "gcc", "java", "bash", "sh", "time", "mill", "verilator", "verilator_bin", "firtool")}
        for name, path in tools.items():
            path.write_bytes(("compiler fixture " + name).encode())
        with zipfile.ZipFile(tools["mill"], "w") as archive:
            archive.writestr("mill/compiler.class", b"bound compiler payload")
        return tools

    def probe(self, tools):
        with patch.object(recipe.shutil, "which", side_effect=lambda name: str(tools[Path(name).name])), \
                patch.object(recipe.subprocess, "check_output", return_value="same reported version"):
            return recipe.probe_tools()

    def test_same_version_verilator_payload_drift_is_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            tools = self.tools(Path(tmp))
            before = self.probe(tools)
            tools["verilator_bin"].write_bytes(b"changed compiler with same version")
            after = self.probe(tools)
            self.assertEqual(before["verilator"], after["verilator"])
            self.assertEqual(before["verilator_bin"]["version"], after["verilator_bin"]["version"])
            self.assertNotEqual(before["verilator_bin"]["sha256"], after["verilator_bin"]["sha256"])
            self.assertEqual(after["verilator_bin"]["sha256"], digest(tools["verilator_bin"]))

    def test_forwarding_mill_wrapper_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            tools = self.tools(Path(tmp))
            tools["mill"].write_bytes(b"#!/bin/sh\nexec /unbound/mill.jar \"$@\"\n")
            with self.assertRaisesRegex(ValueError, "directly.*JAR payload"):
                self.probe(tools)

    def test_missing_verilator_payload_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            tools = self.tools(Path(tmp))
            tools["verilator_bin"].unlink()
            with self.assertRaisesRegex(ValueError, "missing sibling Verilator"):
                self.probe(tools)

    def test_mill_jar_payload_drift_is_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            tools = self.tools(Path(tmp))
            before = self.probe(tools)
            with zipfile.ZipFile(tools["mill"], "a") as archive:
                archive.writestr("mill/extra.class", b"changed executable code")
            after = self.probe(tools)
            self.assertEqual(before["mill"]["version"], after["mill"]["version"])
            self.assertNotEqual(before["mill"]["sha256"], after["mill"]["sha256"])

    def test_verilator_payload_override_is_not_inherited(self):
        with patch.dict(recipe.os.environ, {"VERILATOR_ROOT": "/foreign", "VERILATOR_BIN": "foreign_bin"}):
            self.assertFalse({"VERILATOR_ROOT", "VERILATOR_BIN"} & recipe.environment().keys())

    @unittest.skipUnless(shutil.which("bash") and Path("/bin/bash").is_file(), "native POSIX launcher test")
    def test_shebang_free_executable_jar_is_probed_via_bound_posix_shell(self):
        with tempfile.TemporaryDirectory() as tmp:
            tools = self.tools(Path(tmp))
            tools["bash"] = Path("/bin/bash").resolve()
            tools["sh"] = Path("/bin/sh").resolve()
            # Match Mill's supported format: shell preamble plus ZIP payload,
            # with no kernel shebang. A direct execve raises ENOEXEC.
            tools["mill"].write_bytes(b"printf 'polyglot compiler version\\n'\nexit 0\n")
            with zipfile.ZipFile(tools["mill"], "a") as archive:
                archive.writestr("mill/compiler.class", b"compiler")
            tools["mill"].chmod(0o755)
            real = subprocess.check_output
            calls = []
            def execute(command, **kwargs):
                calls.append(command)
                return real(command, **kwargs) if str(tools["mill"]) in command else "fixture version"
            with patch.object(recipe.shutil, "which", side_effect=lambda name: str(tools[Path(name).name])), \
                    patch.object(recipe.subprocess, "check_output", side_effect=execute):
                captured = recipe.probe_tools()
            self.assertEqual(captured["mill"]["version"], "polyglot compiler version\n")
            self.assertIn([str(tools["sh"]), str(tools["mill"]), "--version"], calls)


class MetadataContract(unittest.TestCase):
    def contract(self, root):
        # Probe output is supplied independently; exercise the actual capture,
        # metadata hashing and schema validation outside native Linux execution.
        tools = {role: dict(path="/tools/" + role, sha256="a" * 64, version="test")
                 for role in ("cxx", "cc", "java", "bash", "sh", "time", "mill", "verilator", "verilator_bin", "firtool")}
        with patch.object(recipe.subprocess, "check_output", return_value=json.dumps(tools)):
            result = recipe.capture(root)
        recipe.validate(result)
        return result

    def test_current_capture_binds_version_bytes_and_detects_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            version = root / ".mill-version"
            version.write_bytes(b"0.12.3\n")
            before = self.contract(root)
            self.assertEqual(before["schema"], 2)
            self.assertEqual(before["launch_metadata"][".mill-version"]["sha256"], digest(version))
            version.write_bytes(b"0.12.3\r\n")
            after = self.contract(root)
            self.assertEqual(before["launch_metadata"][".mill-version"]["value"],
                             after["launch_metadata"][".mill-version"]["value"])
            with patch.object(recipe, "capture", return_value=after), \
                    self.assertRaisesRegex(ValueError, "contract changed"):
                recipe.verify(root, before)

    def test_legacy_or_incomplete_contract_cannot_authorize_new_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".mill-version").write_bytes(b"0.12.3\n")
            original = self.contract(root)
            mutations = (lambda c: c.update(schema=1),
                         lambda c: c.pop("launch_metadata"),
                         lambda c: c["launch_metadata"][".mill-version"].pop("sha256"),
                         lambda c: c["compilers"].pop("verilator_bin"),
                         lambda c: c.pop("mill_launch"))
            for mutate in mutations:
                changed = copy.deepcopy(original)
                mutate(changed)
                with self.assertRaises(ValueError):
                    recipe.make_command(changed)

    def test_hardware_inventory_includes_mill_version_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            version = root / ".mill-version"
            version.write_bytes(b"0.12.3\n")
            subprocess.run(["git", "-C", str(root), "add", ".mill-version"], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            before = build_inputs.hardware_files(root)
            self.assertEqual(before[".mill-version"], digest(version))
            version.write_bytes(b"0.12.4\n")
            with patch.object(build_inputs, "verify_dependencies", return_value={}), \
                    self.assertRaisesRegex(RuntimeError, "inventory changed"):
                build_inputs.verify_hardware_files(root, before)

    @unittest.skipUnless(Path("/usr/bin/time").is_file() and Path("/bin/bash").is_file(),
                         "native GNU time/Make dispatch test")
    def test_make_uses_bound_external_time_for_shebang_free_mill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".mill-version").write_bytes(b"0.12.3\n")
            contract = self.contract(root)
            mill = root / "mill payload"
            mill.write_bytes(b"printf 'timed polyglot version\\n'\nexit 0\n")
            with zipfile.ZipFile(mill, "a") as archive:
                archive.writestr("mill/compiler.class", b"compiler")
            mill.chmod(0o755)
            for role, path in (("bash", Path("/bin/bash").resolve()), ("sh", Path("/bin/sh").resolve()),
                               ("time", Path("/usr/bin/time")), ("mill", mill)):
                contract["compilers"][role].update(path=str(path), sha256=digest(path))
            contract["mill_launch"]=[contract["compilers"]["sh"]["path"], str(mill)]
            timing = root / "timing output.log"
            (root / "Makefile").write_text("TIMELOG := " + str(timing) + "\nemu:\n\t$(TIME_CMD) " +
                                          shlex.quote(str(mill)) + " --version\n", encoding="utf-8")
            result = subprocess.run(shlex.split(recipe.make_command(contract)), cwd=root,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("timed polyglot version", result.stdout)
            self.assertIn("Exit status: 0", timing.read_text())


if __name__ == "__main__":
    unittest.main()
