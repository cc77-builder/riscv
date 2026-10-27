"""Host-only evidence-integrity tests; no emulator or hardware build."""
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
import run_suite

import recheck as audit


def save(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


class RecheckSuiteTests(unittest.TestCase):
    def test_partial_inventory_never_satisfies_full_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for name in audit.JOB_NAMES[:2]:
                (base / name).mkdir()
                save(base / name / "result.json", dict(name=name, status="OLD_VERDICT", finished="2026-10-18T01:01:01+00:00"))
            self.assertEqual(len(audit.inventory(base, True)), 2)
            with self.assertRaisesRegex(ValueError, "12 completed"):
                audit.inventory(base, False)
            (base / "unregistered-job").mkdir()
            with self.assertRaisesRegex(ValueError, "unexpected"):
                audit.inventory(base, True)

    def test_full_inventory_rejects_missing_wrong_or_running_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for name in audit.JOB_NAMES:
                (base / name).mkdir()
                save(base / name / "result.json", dict(name=name, status="OLD_VERDICT", finished="2026-10-18T01:01:01+00:00"))
            self.assertEqual(set(audit.inventory(base, False)), set(audit.JOB_NAMES))
            p = base / "functional-0/result.json"
            row = json.loads(p.read_text())
            for field, value in (("name", "functional-1"), ("finished", None), ("status", "RUNNING")):
                bad = dict(row); bad[field] = value; save(p, bad)
                with self.subTest(field=field), self.assertRaises(ValueError):
                    audit.inventory(base, False)
            p.unlink()
            with self.assertRaises(ValueError):
                audit.inventory(base, False)

    def raw_fixture(self, base):
        stdout, stderr = b"UART result\r\n", b"OBSERVATION event\n"
        for name, raw in (("stdout.log", stdout), ("stderr.log", stderr), ("run.log", stderr + stdout)):
            (base / name).write_bytes(raw)
        (base / "exit-code.txt").write_text("1\n")
        command = ["fixture-command", "--diff=/frozen/negative.so"]
        files = {"/frozen/image.bin": "a" * 64, "/frozen/negative.so": "b" * 64}
        row = dict(name="negative-vdot", status="OLD_VERDICT", started="2026-10-18T01:01:00+00:00",
                   finished="2026-10-18T01:01:01+00:00", command=command, files=files,
                   negative_target="vdot", exit_code=1, raw_logs_sha256={n: audit.sha(base / n) for n in audit.RAW_NAMES})
        save(base / "runtime.json", row)
        return row, command, files

    def test_original_streams_kept_raw_with_explicit_parse_newline_normalization(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); row, cmd, files = self.raw_fixture(base)
            before = {n: (base / n).read_bytes() for n in audit.RAW_NAMES}
            rc, text = audit.check_raw_job(base, row, cmd, files, "vdot")
            self.assertEqual(rc, 1)
            self.assertEqual(text, "OBSERVATION event\nUART result\n")
            self.assertEqual(before, {n: (base / n).read_bytes() for n in audit.RAW_NAMES})

    def test_appended_original_log_fails_recorded_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); row, cmd, files = self.raw_fixture(base)
            for name in audit.RAW_NAMES:
                original = (base / name).read_bytes()
                (base / name).write_bytes(original + b"appended\n")
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, "raw log hash"):
                    audit.check_raw_job(base, row, cmd, files, "vdot")
                (base / name).write_bytes(original)

    def test_rehashed_derived_log_still_must_equal_separate_streams(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); row, cmd, files = self.raw_fixture(base)
            (base / "run.log").write_bytes(b"made-up combined log\n")
            row["raw_logs_sha256"]["run.log"] = audit.sha(base / "run.log")
            with self.assertRaisesRegex(ValueError, "stderr \+ stdout"):
                audit.check_raw_job(base, row, cmd, files, "vdot")

    def test_raw_inventory_exit_reference_input_and_receipt_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); row, cmd, files = self.raw_fixture(base)
            bad = copy.deepcopy(row); bad["raw_logs_sha256"].pop("stderr.log")
            with self.assertRaisesRegex(ValueError, "stream hashes"):
                audit.check_raw_job(base, bad, cmd, files, "vdot")
            (base / "exit-code.txt").write_text("0\n")
            with self.assertRaisesRegex(ValueError, "exit code mismatch"):
                audit.check_raw_job(base, row, cmd, files, "vdot")
            (base / "exit-code.txt").write_text("1\n")
            for key, value in (("command", ["fixture-command", "--diff=/wrong.so"]),
                               ("files", {"/frozen/image.bin": "c" * 64}), ("negative_target", None),
                               ("exit_code", True)):
                bad = copy.deepcopy(row); bad[key] = value
                with self.subTest(key=key), self.assertRaises(ValueError):
                    audit.check_raw_job(base, bad, cmd, files, "vdot")
            runtime = copy.deepcopy(row); runtime["started"] = "2026-10-18T01:00:00+00:00"
            save(base / "runtime.json", runtime)
            with self.assertRaisesRegex(ValueError, "runtime/result"):
                audit.check_raw_job(base, row, cmd, files, "vdot")

    def test_completed_only_cannot_upgrade_to_whole_suite_pass(self):
        for passed in (False, True):
            for selected in (False, True):
                result = audit.summarize_verdict(True, passed, selected)
                self.assertEqual(result["status"], "O2_PARTIAL_AUDIT")
                self.assertFalse(result["whole_suite_pass"])
                self.assertEqual(result["checks_passed"], selected)
        self.assertEqual(audit.summarize_verdict(False, True, True)["status"], "O2_OFFLINE_FULL_SUITE_RECHECK_PASS")
        self.assertFalse(audit.summarize_verdict(False, False, True)["whole_suite_pass"])

    def test_final_campaign_requires_source_pins_terminal_state_and_exact_receipts(self):
        rows = {name: {"name": name, "status": "OLD_VERDICT"} for name in audit.JOB_NAMES}
        state = {"status": "O2_CORE_REGRESSION_PASS", "finished": "2026-10-18T01:01:01+00:00"}
        preflight = {"hardware_pins_sha256": "a" * 64}
        pins = {"source_commit": "b" * 40}
        final = dict(state, hardware_pins_sha256="a" * 64, build_source_commit="b" * 40, runs=list(rows.values()))
        audit.validate_final_campaign(state, preflight, pins, rows, final)
        for field, value in (("hardware_pins_sha256", "c" * 64), ("build_source_commit", "c" * 40),
                             ("finished", "2026-10-18T01:01:02+00:00"), ("runs", list(rows.values())[:-1]),
                             ("runs", [rows["hello-vadd"]] * 12)):
            bad = dict(final); bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                audit.validate_final_campaign(state, preflight, pins, rows, bad)
        with self.assertRaisesRegex(ValueError, "has not ended"):
            audit.validate_final_campaign(dict(state, status="RUNNING"), preflight, pins, rows, final)


    def test_g3_requires_both_supplements_and_every_frozen_target(self):
        records = [dict(name='core-control', status='O2_CONTROL_LEGACY_PASS',
                        observation_status='O2_TRACE_PASS',
                        observation_counts={key:1 for key in audit.O2_TARGETS})]
        result=audit.combine_g3(True, records, None, run_suite)
        self.assertEqual(result['status'],'O2_G3_OFFLINE_RECHECK_INCOMPLETE')
        self.assertFalse(result['g3_complete'])
        supplement=dict(status='O2_SUPPLEMENT_OFFLINE_RECHECK_PASS', records=[
            dict(name=name,status='O2_SUPPLEMENT_PASS',observation_status='O2_TRACE_PASS',
                 exit_code=0,observation_counts={key:0 for key in audit.O2_TARGETS})
            for name in sorted(audit.SUPPLEMENT_NAMES)])
        result=audit.combine_g3(True,records,supplement,run_suite)
        self.assertEqual(result['status'],'O2_G3_OFFLINE_RECHECK_PASS')
        self.assertTrue(result['g3_complete'])
        self.assertEqual(result['suite_coverage']['sources']['TRIPLE_OVERLAP'],
                         [{'name':'core-control','count':1}])
        missing=copy.deepcopy(records)
        missing[0]['observation_counts']['PARTIAL_KILL']=0
        result=audit.combine_g3(True,missing,supplement,run_suite)
        self.assertEqual(result['status'],'O2_G3_OFFLINE_RECHECK_INCOMPLETE')
        self.assertEqual(result['suite_coverage']['missing'],['PARTIAL_KILL'])
        self.assertEqual(audit.combine_g3(False,records,supplement,run_suite)['status'],
                         'O2_G3_OFFLINE_RECHECK_FAILED')

    def test_g3_rejects_cached_unreplayed_partial_duplicate_or_failed_supplements(self):
        good=dict(status='O2_SUPPLEMENT_OFFLINE_RECHECK_PASS',records=[
            dict(name=name,status='O2_SUPPLEMENT_PASS',observation_status='O2_TRACE_PASS',
                 exit_code=0,observation_counts={key:1 for key in audit.O2_TARGETS})
            for name in sorted(audit.SUPPLEMENT_NAMES)])
        bads=[]
        for field,value in [('status','O2_SUPPLEMENTS_PASS'),('records',[])]:
            bad=copy.deepcopy(good); bad[field]=value; bads.append(bad)
        for field,value in [('name','o2-diagnostic'),('status','FAILED'),
                            ('observation_status','O2_PARTIAL_TRACE_AUDIT'),('exit_code',True)]:
            bad=copy.deepcopy(good); bad['records'][0][field]=value; bads.append(bad)
        for bad in bads:
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                audit.combine_g3(True,[],bad,run_suite)
        with self.assertRaisesRegex(ValueError,'policy drift'):
            audit.combine_g3(True,[],None,SimpleNamespace(O2_REQUIRED_COVERAGE=('MULTI_INFLIGHT',)))

    def test_git_blob_binding_survives_current_edit_but_rejects_wrong_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            def git(*args):
                return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.PIPE).decode().strip()
            git("init", "-q")
            for name in audit.DRIVERS:
                p = repo / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text("# original " + name + "\n")
            git("add", ".")
            git("-c", "user.name=O2 host test", "-c", "user.email=o2-test@example.invalid", "commit", "-qm", "original fixture")
            original = git("rev-parse", "HEAD")
            pins = {str(repo / n): audit.sha(repo / n) for n in audit.DRIVERS}
            (repo / audit.DRIVERS[0]).write_text("# separately edited current driver\n")
            blobs = audit.bind_original_drivers(repo, original, pins)
            self.assertNotEqual(blobs[audit.DRIVERS[0]], (repo / audit.DRIVERS[0]).read_bytes())
            git("add", ".")
            git("-c", "user.name=O2 host test", "-c", "user.email=o2-test@example.invalid", "commit", "-qm", "later driver")
            with self.assertRaisesRegex(ValueError, "Git source commit"):
                audit.bind_original_drivers(repo, git("rev-parse", "HEAD"), pins)
            with self.assertRaisesRegex(ValueError, "source commit"):
                audit.bind_original_drivers(repo, "HEAD", pins)
            bad = dict(pins); bad.pop(str(repo / audit.DRIVERS[-1]))
            with self.assertRaisesRegex(ValueError, "seven frozen"):
                audit.bind_original_drivers(repo, original, bad)


if __name__ == "__main__":
    unittest.main()
