"""Mutation tests for fresh inputs without relaxing historical G3 identity."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import input_contract as contract


class InputContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "repo"
        self.root.mkdir()
        self.files = {}

        def put(path, body=b"input\n"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            self.files[str(path)] = contract.sha(path)
            return path
        self.put = put
        for name in (*contract.HELLO_SOURCES, contract.FIXTURE, *contract.MATRIX_HELPERS,
                     "team/workloads/vdot-exceptions/main.c", "team/workloads/vdot-exceptions/judge.c",
                     "team/workloads/vdot-exceptions/Makefile"):
            put(self.root / name)
        for args in (("init", "-q"), ("add", "."),
                     ("-c", "user.name=Contract Test", "-c", "user.email=contract@example.invalid", "commit", "-qm", "sources")):
            subprocess.run(["git", "-C", str(self.root), *args], check=True, stdout=subprocess.DEVNULL)
        self.rev = subprocess.check_output(["git", "-C", str(self.root), "rev-parse", "HEAD"], text=True).strip()
        put(self.root / "team/workloads/hello-vadd/identity.h")
        self.paths = {role: put(self.base / "inputs" / role / "image.bin", role.encode()) for role in contract.ROLES}
        for p in (self.paths["reference"].parents[1] / ".config",
                  self.paths["reference"].parent / "vdot-provenance.json"):
            put(p)
        self.matrix = self.base / "matrix"
        matrix_sums = [contract.sha(put(self.matrix / f"build-{i}/vdot-exceptions.bin", str(i).encode())) for i in range(8)]
        tools = {str(Path(sys.executable).resolve()): contract.sha(Path(sys.executable).resolve())}
        self.files.update(tools)
        am = self.base / "am"
        for name in (*contract.AM_LIBRARIES, "source.c"):
            put(am / name)
        put(self.paths["hello"].with_suffix(".elf"))
        put(self.paths["flash"].with_suffix(".o"))
        fixture = str(self.root / contract.FIXTURE)
        self.negative = dict(status="BUILD_PASS", source_commit=self.rev,
            reference_sha256=contract.sha(self.paths["reference"]), tools=tools,
            files={str(p): contract.sha(p) for p in (Path(fixture), self.paths["reference"], self.paths["negative"])},
            command=[next(iter(tools)), "-shared", "-fPIC", "-O2", "-Wall", "-Wextra", "-Werror",
                     '-DREF_SO="' + str(self.paths["reference"]) + '"', fixture, "-ldl", "-Wl,--no-as-needed",
                     str(self.paths["reference"]), "-o", str(self.paths["negative"])])
        self.hello = dict(status="BUILD_PASS", source_commit=self.rev, tools=tools,
            commands=[[sys.executable, *args] for args in contract.hello_commands(self.paths, self.root)], files=dict(self.files),
            am_home=str(am), am_revision="086a238062fdfb3281b745a537b361983d0154b5",
            am_source_sha256={"source.c": contract.sha(am / "source.c")})
        self.manifest = dict(schema_version=1, contract=contract.NAME, source_commit=self.rev,
            paths={key: str(value) for key, value in self.paths.items()},
            sha256={**{key: contract.sha(value) for key, value in self.paths.items()}, "matrix": matrix_sums},
            receipts={kind: str(self.base / (kind + ".json")) for kind in ("negative", "hello")})
        self.path = self.base / "contract.json"

    def write(self):
        for kind in ("negative", "hello"):
            path = Path(self.manifest["receipts"][kind])
            path.write_text(json.dumps(getattr(self, kind)), encoding="utf-8")
            self.files[str(path)] = contract.sha(path)
        self.manifest["files"] = dict(self.files)
        self.path.write_text(json.dumps(self.manifest), encoding="utf-8")

    def validate(self):
        self.write()
        # Only executable lookup is synthetic; argv, file inventory and Git
        # source binding run through the production implementation.
        with mock.patch.object(contract.shutil, "which", return_value=sys.executable):
            return contract.validate(self.path, self.paths, self.matrix, self.root)

    def matrix_receipt(self):
        sources = {str(self.root / name): self.files[str(self.root / name)] for name in
                   (*contract.MATRIX_HELPERS, "team/workloads/vdot-exceptions/main.c",
                    "team/workloads/vdot-exceptions/judge.c", "team/workloads/vdot-exceptions/Makefile")}
        image = self.matrix / "build-0/vdot-exceptions.bin"
        elf = self.put(image.with_suffix(".elf"))
        data = self.matrix / "data-0"
        generated = [self.put(data / name) for name in contract.MATRIX_DATA]
        row = dict(source_sha256=sources, images_sha256={str(p): contract.sha(p) for p in (image, elf)},
                   inputs_sha256={str(p): contract.sha(p) for p in generated}, data_dir=str(data), am_home=self.hello["am_home"],
                   am_rev=self.hello["am_revision"], am_source_sha256=self.hello["am_source_sha256"],
                   am_libraries_sha256={str(self.base / "am" / name): self.files[str(self.base / "am" / name)]
                                        for name in contract.AM_LIBRARIES})
        self.put(image.parent / "workload-provenance.json", json.dumps(row).encode())
        self.write()
        return row

    def test_accepts_complete_explicit_contract_and_binds_manifest(self):
        value, files = self.validate()
        self.assertEqual(value["contract"], contract.NAME)
        self.assertEqual(files[str(self.path)], contract.sha(self.path))

    def test_rejects_stale_bytes_even_with_valid_receipts(self):
        self.paths["negative"].write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "drift"):
            self.validate()

    def test_negative_command_cannot_change_target_or_trusted_fixture(self):
        original = copy.deepcopy(self.negative)
        for index, replacement in ((7, '-DREF_SO="/another/reference"'), (8, "/another/fixture.c"),
                                   (10, "-Wl,--as-needed")):
            with self.subTest(index=index):
                self.negative = copy.deepcopy(original)
                self.negative["command"][index] = replacement
                with self.assertRaisesRegex(ValueError, "negative command"):
                    self.validate()

    def test_rejects_self_consistent_changed_source_against_git(self):
        path = self.root / contract.FIXTURE
        self.put(path, b"changed fixture")
        self.negative["files"][str(path)] = contract.sha(path)
        self.hello["files"][str(path)] = contract.sha(path)
        with self.assertRaisesRegex(ValueError, "Git revision"):
            self.validate()

    def test_cannot_omit_runtime_tool_or_am_inventory(self):
        for key in (next(iter(self.negative["tools"])), str(self.base / "am/source.c")):
            with self.subTest(key=key):
                saved = self.files.pop(key)
                with self.assertRaisesRegex(ValueError, "not bound|not retained"):
                    self.validate()
                self.files[key] = saved

    def test_matrix_requires_exact_eight_bound_images(self):
        self.manifest["sha256"]["matrix"].pop()
        with self.assertRaisesRegex(ValueError, "eight shards"):
            self.validate()

    def test_supplement_needs_bound_image_and_receipt(self):
        build = self.base / "diagnostic"
        image = self.put(build / "o2-diag.bin")
        self.manifest["supplements"] = {"diagnostic": {"build": str(build), "sha256": contract.sha(image)}}
        with self.assertRaisesRegex(ValueError, "supplement receipt"):
            self.validate()
        self.put(build / "build.json")
        self.validate()

    def test_unknown_schema_and_unrelated_source_rejected(self):
        self.manifest["schema_version"] = 2
        with self.assertRaisesRegex(ValueError, "unknown fresh"):
            self.validate()
        self.manifest["schema_version"] = 1
        self.manifest["source_commit"] = "f" * 40
        with self.assertRaisesRegex(ValueError, "ancestor"):
            self.validate()

    def test_hello_rejects_wrong_arch_image_or_arbitrary_commands(self):
        original = copy.deepcopy(self.hello["commands"])
        for index, args in ((0, [sys.executable, "recorded-command"]),
                            (1, [sys.executable, "-c", "/another/boot.S"]),
                            (2, [sys.executable, "-O", "binary", "arbitrary.bin"])):
            self.hello["commands"] = copy.deepcopy(original)
            self.hello["commands"][index] = args
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, "hello commands"):
                self.validate()

    def test_matrix_cannot_rehash_mutated_judge_or_omit_required_source(self):
        receipt = self.matrix_receipt()
        contract.bind_matrix(self.manifest, self.root, self.matrix / "build-0", receipt)
        name = str(self.root / "team/workloads/vdot-exceptions/judge.c")
        removed = receipt["source_sha256"].pop(name)
        with self.assertRaisesRegex(ValueError, "complete"):
            contract.bind_matrix(self.manifest, self.root, self.matrix / "build-0", receipt)
        receipt["source_sha256"][name] = removed
        self.put(Path(name), b"judge always passes")
        receipt["source_sha256"][name] = self.files[name]
        self.write()
        with self.assertRaisesRegex(ValueError, "Git revision"):
            contract.bind_matrix(self.manifest, self.root, self.matrix / "build-0", receipt)

    def test_matrix_and_nemu_transitive_files_must_be_runtime_bound(self):
        receipt = self.matrix_receipt()
        key = str(self.base / "am/source.c")
        self.manifest["files"].pop(key)
        with self.assertRaisesRegex(ValueError, "AM source absent"):
            contract.bind_matrix(self.manifest, self.root, self.matrix / "build-0", receipt)
        root = self.paths["reference"].parents[1]
        source = self.put(root / "source.c")
        system = self.put(self.base / "system.h")
        self.write()
        provenance = {"source_sha256": {"source.c": contract.sha(source), "@system/" + str(system): contract.sha(system)}}
        contract.bind_reference(self.manifest, self.paths["reference"], provenance)
        self.manifest["files"].pop(str(system))
        with self.assertRaisesRegex(ValueError, "NEMU source absent"):
            contract.bind_reference(self.manifest, self.paths["reference"], provenance)

    def test_matrix_generated_elf_and_am_inventory_cannot_omit_members(self):
        receipt = self.matrix_receipt()
        for group in ("inputs_sha256", "images_sha256", "am_libraries_sha256"):
            changed = copy.deepcopy(receipt)
            changed[group].pop(next(iter(changed[group])))
            with self.subTest(group=group), self.assertRaisesRegex(ValueError, "incomplete matrix"):
                contract.bind_matrix(self.manifest, self.root, self.matrix / "build-0", changed)


if __name__ == "__main__":
    unittest.main()
