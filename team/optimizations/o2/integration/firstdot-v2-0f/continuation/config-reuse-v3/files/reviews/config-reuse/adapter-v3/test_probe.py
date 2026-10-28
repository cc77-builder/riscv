"""Host-only draft tests. No hardware, compiler or subprocess is started."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import probe


def rows():
    result = []
    values = {
        ("firstdot","basic","vdot"): 1300, ("firstdot","basic","rvv"): 1400,
        ("firstdot","reuse","vdot"): 1129, ("firstdot","reuse","rvv"): 1200,
        ("config-reuse","basic","vdot"): 1250, ("config-reuse","basic","rvv"): 1400,
        ("config-reuse","reuse","vdot"): 1092, ("config-reuse","reuse","rvv"): 1196,
    }
    for (variant,software,method),total in values.items():
        result.append(dict(variant=variant,software=software,method=method,total=total,samples=4))
    return result


class Decisions(unittest.TestCase):
    def decision(self, data=None, controls=None, replay=True):
        return probe.assess(rows() if data is None else data, [] if controls is None else controls, replay)

    def replace(self, total, key=("config-reuse","reuse","vdot")):
        data = rows()
        next(r for r in data if (r["variant"],r["software"],r["method"]) == key)["total"] = total
        return data

    def test_strict_both_win_only_probe_candidate(self):
        r = self.decision()
        self.assertEqual(r["decision"], "PERFORMANCE_CANDIDATE")
        self.assertFalse(r["default_changed"])
        self.assertFalse(r["full_matrix_qualified"])

    def test_tie_firstdot_reject(self):
        self.assertEqual(self.decision(self.replace(1129))["decision"], "REJECT")

    def test_worse_than_firstdot_reject(self):
        self.assertEqual(self.decision(self.replace(1130))["decision"], "REJECT")

    def test_one_cycle_gain_not_artificial_percentage_gate(self):
        self.assertEqual(self.decision(self.replace(1128))["decision"], "PERFORMANCE_CANDIDATE")

    def test_fastest_rvv_from_firstdot_basic(self):
        data = self.replace(1000, ("firstdot","basic","rvv"))
        # Keep the unchanged RVV control equal while isolating fastest-baseline selection.
        next(r for r in data if (r["variant"],r["software"],r["method"]) ==
             ("config-reuse","basic","rvv"))["total"] = 1000
        self.assertEqual(self.decision(data)["decision"], "REJECT")

    def test_fastest_rvv_from_candidate_reuse(self):
        data = self.replace(1000, ("config-reuse","reuse","rvv"))
        self.assertEqual(self.decision(data)["decision"], "REJECT")

    def test_replay_drift_inconclusive(self):
        self.assertEqual(self.decision(replay=False)["decision"], "INCONCLUSIVE")

    def test_unchanged_rvv_drift_inconclusive(self):
        self.assertEqual(self.decision(controls=["basic RVV full-window drift"])["decision"], "INCONCLUSIVE")

    def test_same_baseline_payload_context_drift_inconclusive(self):
        self.assertEqual(self.decision(controls=["baseline signature drift"])["decision"], "INCONCLUSIVE")

    def test_other_cell_regression_blocks_adoption(self):
        data = self.replace(1301, ("config-reuse","basic","vdot"))
        self.assertEqual(self.decision(data)["decision"], "INCONCLUSIVE")

    def test_other_regressions_block_both_winning_and_losing_main_candidate(self):
        for main_total in (1092, 1130):
            for software,method in (("basic","vdot"),("basic","rvv"),("reuse","rvv")):
                with self.subTest(main_total=main_total, software=software, method=method):
                    data = self.replace(main_total)
                    base = next(r["total"] for r in data if (r["variant"],r["software"],r["method"]) ==
                                ("firstdot",software,method))
                    next(r for r in data if (r["variant"],r["software"],r["method"]) ==
                         ("config-reuse",software,method))["total"] = base + 1
                    value = self.decision(data)
                    self.assertEqual(value["decision"], "INCONCLUSIVE")
                    self.assertIn("unexplained paired cell regression: "+software+"/"+method,
                                  value["unexplained_controls"])

    def test_explicit_controls_block_both_winning_and_losing_candidate(self):
        for main_total in (1092, 1130):
            for control in ("identical baseline drift", "unchanged RVV drift"):
                with self.subTest(main_total=main_total, control=control):
                    value = self.decision(self.replace(main_total), controls=[control])
                    self.assertEqual(value["decision"], "INCONCLUSIVE")
                    self.assertIn(control, value["unexplained_controls"])

    def test_main_candidate_regression_alone_remains_reject(self):
        value = self.decision(self.replace(1130))
        self.assertEqual(value["decision"], "REJECT")
        self.assertEqual(value["unexplained_controls"], [])

    def test_missing_cell_reject(self):
        with self.assertRaisesRegex(ValueError, "eight"):
            self.decision(rows()[:-1])

    def test_duplicate_cell_reject(self):
        data = rows(); data[-1] = copy.deepcopy(data[0])
        with self.assertRaisesRegex(ValueError, "inventory"):
            self.decision(data)

    def test_three_windows_reject(self):
        data = rows(); data[0]["samples"] = 3
        with self.assertRaisesRegex(ValueError, "four"):
            self.decision(data)

    def test_bool_cycle_reject(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            self.decision(self.replace(True))

    def test_float_cycle_reject(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            self.decision(self.replace(1092.0))

    def test_zero_cycle_reject(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            self.decision(self.replace(0))

    def test_replay_truthy_string_reject(self):
        with self.assertRaisesRegex(ValueError, "types"):
            self.decision(replay="true")


class SourceLocks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="config-probe-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"; self.repo.mkdir()
        self.adapter = self.root / "adapter"; self.adapter.mkdir()
        self.patch = patch.object(probe, "HERE", self.adapter)
        self.patch.start(); self.addCleanup(self.patch.stop)
        for name in ("probe.py","raw_audit.py","CONTRACT.md"):
            (self.adapter/name).write_text(name)
        files = []
        for n in range(65):
            name = "source-" + str(n)
            (self.repo/name).write_bytes(b"source")
            files.append(dict(path=name, bytes=6, sha256=hashlib.sha256(b"source").hexdigest()))
        self.manifest = dict(upstream_ref=probe.UPSTREAM, files=files[:26], already_present_dependencies=files[26:])
        self.persist()

    def persist(self):
        (self.adapter/"import-manifest.json").write_text(json.dumps(self.manifest))

    def test_closed_source_inventory(self):
        self.assertEqual(len(probe.imports(self.repo)), 69)

    def test_modified_source_reject(self):
        (self.repo/"source-0").write_bytes(b"tamper")
        with self.assertRaisesRegex(ValueError, "source drift"):
            probe.imports(self.repo)

    def test_source_missing_reject(self):
        (self.repo/"source-0").unlink()
        with self.assertRaisesRegex(ValueError, "source drift"):
            probe.imports(self.repo)

    def test_duplicate_source_reject(self):
        self.manifest["files"][0] = self.manifest["files"][1]
        self.persist()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            probe.imports(self.repo)

    def test_escape_source_reject(self):
        self.manifest["files"][0]["path"] = "../outside"
        self.persist()
        with self.assertRaisesRegex(ValueError, "unsafe"):
            probe.imports(self.repo)

    def test_import_count_reject(self):
        self.manifest["files"].pop()
        self.persist()
        with self.assertRaisesRegex(ValueError, "inventory"):
            probe.imports(self.repo)

    def test_historical_ref_reject(self):
        self.manifest["upstream_ref"] = "old"
        self.persist()
        with self.assertRaisesRegex(ValueError, "upstream"):
            probe.imports(self.repo)

    def test_symlink_source_reject(self):
        (self.repo/"source-0").unlink()
        (self.repo/"source-0").symlink_to(self.repo/"source-1")
        with self.assertRaisesRegex(ValueError, "source drift"):
            probe.imports(self.repo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
