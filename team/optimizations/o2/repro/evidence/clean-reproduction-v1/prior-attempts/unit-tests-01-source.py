"""Adversarial checks against real T17 support and completed spawn receipts."""
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import unittest

import clean_evidence as evidence
import clean_fullcore_evidence as fullcore


def replace_json(bundle, name, change):
    row = bundle["files"][name]
    value = json.loads(base64.b64decode(row["base64"]))
    change(value)
    raw = (json.dumps(value, indent=2) + "\n").encode()
    row.update(base64=base64.b64encode(raw).decode(), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


class SupportTests(unittest.TestCase):
    def setUp(self):
        self.bundle = copy.deepcopy(BUNDLE)

    def reject(self):
        with self.assertRaises((ValueError, KeyError, TypeError)):
            evidence.validate_support(self.bundle, IDENTITY)

    def test_real_support_chain(self):
        result = evidence.validate_support(self.bundle, IDENTITY)
        self.assertEqual(result["status"], "T17_SUPPORT_PROVENANCE_CHAIN_PASS")
        self.assertEqual(result["restored_repositories"], 145)

    def test_incomplete_input_inventory(self):
        del self.bundle["files"]["support/klib.stderr.log"]
        self.reject()

    def test_duplicate_original(self):
        self.bundle["files"]["prepare/prepare.log"]["original"] = self.bundle["files"]["prepare/prepare-state.json"]["original"]
        self.reject()

    def test_reused_generated_output(self):
        replace_json(self.bundle, "support/state.json", lambda s: s.update(generated_products_copied=True))
        self.reject()

    def test_wrong_reference(self):
        replace_json(self.bundle, "support/state.json", lambda s: s.update(reference_sha256="efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4"))
        self.reject()

    def test_changed_live_library(self):
        name = next(iter(self.bundle["live_am_libraries"]))
        self.bundle["live_am_libraries"][name] = "0" * 64
        self.reject()

    def test_failed_build_command(self):
        replace_json(self.bundle, "support/nemu-command.json", lambda s: s.update(exit_code=1))
        self.reject()

    def test_changed_command_even_with_matching_receipt(self):
        replace_json(self.bundle, "support/am-command.json", lambda s: s["command"].__setitem__(-1, "-j8"))
        replace_json(self.bundle, "support/state.json", lambda s: s["commands"]["am"].__setitem__(-1, "-j8"))
        self.reject()

    def test_changed_log_even_with_new_payload_hash(self):
        row = self.bundle["files"]["support/nemu.stdout.log"]
        raw = base64.b64decode(row["base64"]) + b"unrecorded output\n"
        row.update(base64=base64.b64encode(raw).decode(), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
        self.reject()

    def test_dependency_with_external_object_alternates(self):
        self.bundle["live_repository_facts"][next(iter(self.bundle["live_repository_facts"]))]["has_alternates"] = True
        self.reject()

    def test_wrong_support_timeline(self):
        replace_json(self.bundle, "support/am-command.json", lambda s: s.update(finished="2000-01-01T00:00:00+00:00"))
        self.reject()


class ProcessTests(unittest.TestCase):
    def test_real_completed_spawn(self):
        self.assertEqual(fullcore.spawn_binding(RUNTIME, RESULT)["pid"], RUNTIME["pid"])

    def test_mutation_of_each_bound_field(self):
        for key in fullcore.SPAWN_FIELDS:
            with self.subTest(field=key):
                changed = copy.deepcopy(RESULT)
                changed[key] = {"unrecorded": True} if not isinstance(changed.get(key), dict) else "unrecorded"
                with self.assertRaises(ValueError):
                    fullcore.spawn_binding(RUNTIME, changed)

    def test_non_execution_cannot_be_promoted(self):
        left, right = copy.deepcopy(RUNTIME), copy.deepcopy(RESULT)
        left["process_started"] = right["process_started"] = False
        with self.assertRaises(ValueError):
            fullcore.spawn_binding(left, right)

    def test_timeout_cannot_be_promoted(self):
        left, right = copy.deepcopy(RUNTIME), copy.deepcopy(RESULT)
        left["timed_out"] = right["timed_out"] = True
        with self.assertRaises(ValueError):
            fullcore.spawn_binding(left, right)

    def test_boolean_pid_rejected(self):
        left, right = copy.deepcopy(RUNTIME), copy.deepcopy(RESULT)
        left["pid"] = right["pid"] = True
        with self.assertRaises(ValueError):
            fullcore.spawn_binding(left, right)


class AliasTests(unittest.TestCase):
    def test_archive_builder_alias_preserves_runtime_metadata(self):
        evidence.install(REPO, IDENTITY, physical=False)
        _, archived, common = evidence.e.modules(REPO)
        runtime = evidence.ce.a.frozen_m
        self.assertEqual(runtime.META, IDENTITY["metadata_sha256"])
        self.assertEqual(len(runtime.META), 19)
        self.assertEqual(archived.META, {k: v for k, v in runtime.META.items() if k != "executed-builder.py"})
        self.assertIs(common.m, archived)
        self.assertEqual(IDENTITY["configuration"]["build_driver"],
                         str(Path(IDENTITY["configuration"]["build_record"]) / "executed-builder.py"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--identity", type=Path, required=True)
    parser.add_argument("--completed-job", type=Path, required=True)
    args = parser.parse_args()
    REPO = args.repo.resolve()
    BUNDLE = json.loads(args.support.read_text())
    IDENTITY = json.loads(args.identity.read_text())
    RUNTIME = json.loads((args.completed_job / "runtime.json").read_text())
    RESULT = json.loads((args.completed_job / "result.json").read_text())
    unittest.main(argv=[__file__], verbosity=2)
