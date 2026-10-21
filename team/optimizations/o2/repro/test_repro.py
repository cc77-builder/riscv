"""Host tests for R0 fail-closed guards; no EMU, synthesis or hardware build."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


repro = load("r0_repro_test", HERE / "repro.py")
builder = load("r0_builder_test", HERE.parent / "fullcore/build_fullcore.py")


class R0Guards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def test_profile_builder_matches_observe_and_cost(self):
        for name in ("observe", "cost"):
            self.assertEqual(builder.profile_flags(name), repro.PROFILES[name])

    def test_builder_rejects_unknown_mode(self):
        with self.assertRaisesRegex(ValueError, "unknown O2 profile"):
            builder.profile_flags("o1")

    def test_profile_calls_do_not_mutate_defaults(self):
        original = dict(builder.FLAGS)
        builder.profile_flags("cost")["VDOT_O2_ELASTIC"] = "0"
        self.assertEqual(builder.FLAGS, original)

    def test_profile_file_mixing_o1_is_rejected(self):
        data = json.loads(json.dumps(repro.PROFILES))
        data["observe"]["VDOT_O1_HANDOFF"] = "1"
        path = self.base / "profiles.json"
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "mixes O1/O2"):
            repro.verify_profiles(path)

    def test_env_clears_inherited_flags_and_selects_profile(self):
        roots = {"java": self.base, "xs_env": self.base, "firtool": self.base}
        with patch.dict(os.environ, {"VDOT_O1_HANDOFF": "1", "VDOT_UNKNOWN": "1"}):
            env = repro.environment(roots, {"python3": self.base / "python3"}, "cost")
            self.assertEqual(env["VDOT_O1_HANDOFF"], "0")
            self.assertEqual(env["VDOT_O2_TRACE"], "0")
            self.assertNotIn("VDOT_UNKNOWN", env)
            self.assertEqual(os.environ["VDOT_O1_HANDOFF"], "1")

    def test_unset_variable_is_actionable(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "unset path variables: R0_MISSING"):
                repro.expand("${R0_MISSING}/file", self.base)

    def test_relative_path_is_config_relative(self):
        self.assertEqual(repro.expand("data", self.base), self.base / "data")

    def test_member_rejects_absolute_and_parent_traversal(self):
        for value in ("/tmp/escape", "../escape"):
            with self.assertRaisesRegex(ValueError, "unsafe logical path"):
                repro.member({"lab": self.base}, {"root": "lab", "path": value})

    def test_member_rejects_symlink_escape(self):
        outside = self.base.parent / (self.base.name + "-outside")
        link = self.base / "link"
        link.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "escapes root"):
            repro.member({"lab": self.base}, {"root": "lab", "path": "link/file"})

    def test_missing_artifact_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing input"):
            repro.verify_file(self.base / "missing", "0" * 64)

    def test_wrong_emu_bytes_are_rejected(self):
        path = self.base / "emu"
        path.write_bytes(b"wrong image")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            repro.verify_file(path, "0" * 64)

    def test_matching_artifact_is_accepted(self):
        path = self.base / "image"
        path.write_bytes(b"frozen")
        repro.verify_file(path, repro.sha(path))

    def test_unknown_config_overrides_rejected(self):
        path = self.base / "config.json"
        path.write_text(json.dumps({"schema_version": 1, "roots": {}, "locations": {},
                                    "tools": {}, "flags": {"VDOT_O2_ELASTIC": "0"}}))
        with self.assertRaisesRegex(ValueError, "unknown/missing config"):
            repro.load_config(path)

    def test_firtool_build_directory_must_select_the_verified_executable(self):
        roots = {name: str(self.base / name) for name in ("repo", "lab", "xs_env", "system", "java", "firtool")}
        locations = {name: dict(root="lab", path=name) for name in
                     ("t12", "t14", "dense", "g4_images", "o3_images", "cost_work",
                      "o2_pins", "o1_pins", "o2_emu", "o1_emu")}
        tools = {name: str(self.base / "tools" / name) for name in repro.TOOL_ARGS}
        path = self.base / "config.json"
        data = dict(schema_version=1, roots=roots, locations=locations, tools=tools)
        path.write_text(json.dumps(data))
        with patch.object(repro, "ROOT", self.base / "repo"):
            with self.assertRaisesRegex(ValueError, "differs from verified tool"):
                repro.load_config(path)
            tools["firtool"] = str(self.base / "firtool/firtool")
            path.write_text(json.dumps(data))
            _, selected_roots, _, selected_tools = repro.load_config(path)
            self.assertEqual(selected_roots["firtool"] / "firtool", selected_tools["firtool"])

    def test_tool_wrong_version_is_rejected(self):
        tool = self.base / "tool"
        tool.write_text("#!/bin/sh\necho WRONG_VERSION\n")
        tool.chmod(0o755)
        with patch.dict(repro.TOOL_ARGS, {"probe": []}, clear=True):
            with self.assertRaisesRegex(ValueError, "wrong version: probe"):
                repro.verify_tools({"tools": {"probe": {"sha256": repro.sha(tool),
                                                       "version_marker": "EXPECTED"}}},
                                   {"probe": tool}, self.base, os.environ.copy())

    def test_existing_build_is_preserved(self):
        root = self.base / "repo"
        (root / "build").mkdir(parents=True)
        sentinel = root / "build/emu"
        sentinel.write_bytes(b"keep-me")
        firtool = self.base / "firtool"
        firtool.mkdir()
        (firtool / "firtool").write_bytes(b"unused")
        with patch.object(builder, "ROOT", root):
            with self.assertRaisesRegex(ValueError, "existing build"):
                builder.main(self.base / "new-build-output", firtool_dir=firtool)
        self.assertEqual(sentinel.read_bytes(), b"keep-me")
        self.assertFalse((self.base / "new-build-output").exists())

    def test_dirty_hardware_does_not_start_build(self):
        root = self.base / "repo"
        root.mkdir()
        firtool = self.base / "firtool"
        firtool.mkdir()
        (firtool / "firtool").write_bytes(b"unused")
        with patch.object(builder, "ROOT", root), patch.object(builder, "git", return_value=b"dirty"):
            with self.assertRaisesRegex(ValueError, "commit hardware"):
                builder.main(self.base / "new-build-output", firtool_dir=firtool)
        self.assertFalse((self.base / "new-build-output").exists())

    def test_relocated_frozen_wrapper_is_rejected(self):
        linked = "/original/reference.so"
        locations = {"t12": self.base / "moved"}
        process = type("Probe", (), {"returncode": 0, "stdout": linked})()
        with patch.object(repro.subprocess, "run", return_value=process):
            with self.assertRaisesRegex(ValueError, "separately versioned wrapper"):
                repro.verify_binding({"negative_reference_binding": linked}, {}, locations)

    def test_build_command_uses_new_pins_and_explicit_profile(self):
        locations = {"t12": self.base, "t14": self.base, "dense": self.base}
        roots = {"java": self.base, "xs_env": self.base, "firtool": self.base}
        tools = {"python3": self.base / "python3", "mill": self.base / "mill"}
        recipe = repro.command_recipes(locations, roots, tools, self.base / "config",
                                       self.base / "lock", self.base / "output", "cost")
        self.assertFalse(recipe["commands_executed"])
        self.assertEqual(recipe["flags"]["VDOT_O2_TRACE"], "0")
        argv = recipe["fullcore_build"]["argv"]
        self.assertEqual(argv[argv.index("--profile") + 1], "cost")
        self.assertIn("NEW-BUILD/hardware-inputs.json", recipe["core_run"]["argv"])

    def test_tool_probe_uses_checkout_version_selection(self):
        tool = self.base / "tool"
        tool.write_bytes(b"frozen tool")
        process = type("Probe", (), {"returncode": 0, "stdout": b"EXPECTED", "stderr": b""})()
        with patch.dict(repro.TOOL_ARGS, {"probe": []}, clear=True):
            with patch.object(repro.subprocess, "run", return_value=process) as run:
                repro.verify_tools({"tools": {"probe": {"sha256": repro.sha(tool),
                                                        "version_marker": "EXPECTED"}}},
                                   {"probe": tool}, self.base, os.environ.copy())
                self.assertEqual(run.call_args.kwargs["cwd"], repro.ROOT)

    def test_untracked_hardware_is_rejected(self):
        def fake_git(*args, **kwargs):
            return b"src/untracked.scala" if args[0] == "ls-files" else b""
        with patch.object(repro, "git", side_effect=fake_git):
            with self.assertRaisesRegex(ValueError, "untracked production/build"):
                repro.verify_source({"source": {"baseline_commit": repro.BASE}},
                                    {"repo": self.base}, {})

    def test_arbitrary_build_sc_edit_is_rejected(self):
        (self.base / "build.sc").write_bytes(b"unreviewed")
        lock = {"source": {"baseline_commit": repro.BASE, "current_build_sc_sha256": "0" * 64}}
        pins = {"files": {"build.sc": "1" * 64}, "dependency_files": {}}
        with patch.object(repro, "git", return_value=b""):
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                repro.verify_source(lock, {"repo": self.base}, pins)


if __name__ == "__main__":
    unittest.main()
