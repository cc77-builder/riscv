"""Independent host tests for expanded inventory, decisions and timing guards.

These fixtures test controller rejection logic; they are not EMU executions or
runtime qualification. No protected source, existing receipt, or default changes.
"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("expanded_matrix_under_test", HERE / "matrix.py")
matrix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(matrix)
BOOT = "12345678-1234-1234-1234-123456789abc"


def image_set():
    result = []
    for shard in (1, 3, 5, 7):
        for dataset in (0, 1, 2):
            for variant in ("firstdot", "config-reuse"):
                name = f"performance-{variant}-d{dataset}-s{shard:02d}"
                result.append(dict(name=name, suite="performance", shard=shard,
                                   dataset=dataset, variant=variant,
                                   path="/separate-build/images/" + name,
                                   image_sha256=hashlib.sha256(name.encode()).hexdigest()))
    return result


def cells(samples=12):
    units = {
        ("firstdot", "basic", "vdot"): 140,
        ("firstdot", "basic", "rvv"): 130,
        ("firstdot", "reuse", "vdot"): 110,
        ("firstdot", "reuse", "rvv"): 120,
        ("config-reuse", "basic", "vdot"): 135,
        ("config-reuse", "basic", "rvv"): 130,
        ("config-reuse", "reuse", "vdot"): 100,
        ("config-reuse", "reuse", "rvv"): 115,
    }
    return [dict(variant=v, software=sw, method=method, samples=samples,
                 total=unit * samples, mean=unit, minimum=unit, maximum=unit,
                 instructions=[10])
            for (v, sw, method), unit in units.items()]


def cell(rows, variant, software, method):
    return next(x for x in rows if (x["variant"], x["software"], x["method"]) ==
                (variant, software, method))


def timing_record(pid, start=10, end=20):
    return dict(pid=pid, process_started=True, monotonic=dict(
        boot_id=BOOT, pid=pid, start_ns=start, end_ns=end,
        scope="popen_wait_bracket"))


def recovery_pair():
    image = next(x for x in image_set() if
                 (x["shard"], x["dataset"], x["variant"]) == (3, 0, "config-reuse"))
    normal_ref = "/separate-reference/normal.so"
    negative_ref = "/separate-reference/negative.so"
    base = dict(image, contract=matrix.CONTRACT, mode="merged", replay=0,
                process_started=True, files={normal_ref: "a" * 64})
    negative = dict(copy.deepcopy(base), **timing_record(101, 10, 20),
                    negative=True, status="EXPECTED_VDOT_HIGHBIT_REJECTION",
                    exit_code=1, reference=negative_ref,
                    environment_overrides={"XS_NEGATIVE_VECTOR_TARGET": "vdot"},
                    negative_details=dict(word="0x0388000b", vd=0, bit=100, pc="0x80002000"))
    negative["files"][negative_ref] = "b" * 64
    normal = dict(copy.deepcopy(base), **timing_record(102, 21, 40),
                  negative=False, status="R2_DIFFTEST_WINDOWS_AND_O2_PROTOCOL_PASS",
                  exit_code=0, reference=normal_ref,
                  environment_overrides={"XS_NEGATIVE_VECTOR_TARGET": None})
    return negative, normal


class InventoryTests(unittest.TestCase):
    def test_fixed_complete_four_shapes_three_datasets_two_variants(self):
        value = matrix.inventory()
        expected = {(s, d, v) for s in (1, 3, 5, 7) for d in (0, 1, 2)
                    for v in ("firstdot", "config-reuse")}
        self.assertEqual(len(value), 24)
        self.assertEqual({(x["shard"], x["dataset"], x["variant"]) for x in value}, expected)
        self.assertTrue(all(x["suite"] == "performance" for x in value))
        self.assertEqual(matrix.SHAPES, {1: (4, 8), 3: (8, 32), 5: (16, 64), 7: (4, 13)})

    def test_fresh_33_process_inventory_negative_recovery_formal_replay(self):
        specs = matrix.run_specs(image_set())
        self.assertEqual(len(specs), 33)
        self.assertEqual(len({s["label"] for s in specs}), 33)
        self.assertEqual(sum(s["negative"] for s in specs), 1)
        self.assertTrue(specs[0]["negative"])
        self.assertFalse(specs[1]["negative"])
        self.assertEqual(specs[0]["image"], specs[1]["image"])
        self.assertEqual((specs[0]["image"]["shard"], specs[0]["image"]["dataset"]), (3, 0))
        normal = [s for s in specs if not s["negative"] and s["replay"] == 0]
        replay = [s for s in specs if s["replay"] == 1]
        self.assertEqual(len(normal), 24)
        self.assertEqual(len(replay), 8)
        self.assertEqual({(s["image"]["shard"], s["image"]["dataset"], s["image"]["variant"])
                          for s in normal},
                         {(x["shard"], x["dataset"], x["variant"]) for x in image_set()})
        self.assertEqual({(s["image"]["shard"], s["image"]["dataset"], s["image"]["variant"])
                          for s in replay},
                         {(k, 0, v) for k in (1, 3, 5, 7) for v in ("firstdot", "config-reuse")})

    def test_missing_image_rejected(self):
        with self.assertRaises(ValueError):
            matrix.run_specs(image_set()[:-1])

    def test_duplicate_replacing_required_image_rejected(self):
        values = image_set()
        values[-1] = copy.deepcopy(values[0])
        with self.assertRaises(ValueError):
            matrix.run_specs(values)

    def test_extra_image_rejected(self):
        with self.assertRaises(ValueError):
            matrix.run_specs(image_set() + [copy.deepcopy(image_set()[0])])

    def test_unknown_or_wrong_typed_selection_rejected(self):
        for key, value in [("shard", 9), ("dataset", 3), ("variant", "s1"),
                           ("suite", "smoke"), ("shard", True), ("dataset", False)]:
            with self.subTest(key=key, value=value):
                values = image_set()
                values[0][key] = value
                with self.assertRaises(ValueError):
                    matrix.run_specs(values)


class DecisionTests(unittest.TestCase):
    def test_twelve_samples_and_strict_both_win_candidate(self):
        value = matrix.assess(cells(), [], True)
        self.assertEqual(value["decision"], "PERFORMANCE_CANDIDATE")
        self.assertEqual(value["candidate_total"], 1200)
        self.assertEqual(value["firstdot_total"], 1320)
        self.assertEqual(value["fastest_current_rvv_total"], 1380)

    def test_four_sample_dataset_cell_is_explicit(self):
        self.assertEqual(matrix.assess(cells(4), [], True, samples_per_cell=4)["decision"],
                         "PERFORMANCE_CANDIDATE")

    def test_missing_duplicate_or_extra_cells_rejected(self):
        for rows in [cells()[:-1], cells() + [cells()[0]], cells()[:-1] + [cells()[0]]]:
            with self.assertRaises(ValueError):
                matrix.assess(rows, [], True)

    def test_wrong_sample_count_or_type_rejected(self):
        for field, val in [("samples", 4), ("samples", 12.0), ("samples", True),
                           ("total", 0), ("total", -1), ("total", True), ("total", 12.0)]:
            with self.subTest(field=field, val=val):
                rows = cells()
                rows[0][field] = val
                with self.assertRaises(ValueError):
                    matrix.assess(rows, [], True)

    def test_wrong_control_or_replay_type_rejected(self):
        for controls, replay in [([], "yes"), ("text", True), ([False], True)]:
            with self.assertRaises(ValueError):
                matrix.assess(cells(), controls, replay)

    def test_tie_firstdot_is_reject(self):
        rows = cells()
        cell(rows, "config-reuse", "reuse", "vdot")["total"] = 1320
        self.assertEqual(matrix.assess(rows, [], True)["decision"], "REJECT")

    def test_fastest_rvv_is_both_versions_and_both_methods(self):
        for variant, sw in [("firstdot", "basic"), ("firstdot", "reuse"),
                            ("config-reuse", "basic"), ("config-reuse", "reuse")]:
            rows = cells()
            cell(rows, variant, sw, "rvv")["total"] = 1190
            # If the paired baseline was made faster, keep candidate nonregressing.
            if variant == "firstdot":
                cell(rows, "config-reuse", sw, "rvv")["total"] = 1190
            with self.subTest(variant=variant, software=sw):
                self.assertEqual(matrix.assess(rows, [], True)["decision"], "REJECT")

    def test_any_control_drift_makes_winner_and_loser_inconclusive(self):
        for candidate in (1200, 1400):
            rows = cells()
            cell(rows, "config-reuse", "reuse", "vdot")["total"] = candidate
            self.assertEqual(matrix.assess(rows, ["unchanged RVV differs"], True)["decision"],
                             "INCONCLUSIVE")

    def test_replay_drift_is_inconclusive(self):
        self.assertEqual(matrix.assess(cells(), [], False)["decision"], "INCONCLUSIVE")

    def test_nonprimary_regression_is_inconclusive(self):
        for sw, method in [("basic", "vdot"), ("basic", "rvv"), ("reuse", "rvv")]:
            rows = cells()
            cell(rows, "config-reuse", sw, method)["total"] = (
                cell(rows, "firstdot", sw, method)["total"] + 1)
            with self.subTest(software=sw, method=method):
                self.assertEqual(matrix.assess(rows, [], True)["decision"], "INCONCLUSIVE")

    def test_no_artificial_percentage_threshold(self):
        rows = cells()
        cell(rows, "config-reuse", "reuse", "vdot")["total"] = 1319
        self.assertEqual(matrix.assess(rows, [], True)["decision"], "PERFORMANCE_CANDIDATE")

    def test_shape_requires_all_three_dataset_keys(self):
        for datasets in [{0: cells(4), 1: cells(4)},
                         {0: cells(4), 1: cells(4), 3: cells(4)}]:
            with self.assertRaises(ValueError):
                matrix.decide_shape(cells(), datasets, [], True)

    def test_shape_passes_only_when_all_three_datasets_pass(self):
        self.assertEqual(matrix.decide_shape(cells(), {d: cells(4) for d in range(3)},
                                             [], True)["decision"], "PERFORMANCE_CANDIDATE")

    def test_single_dataset_main_tie_not_hidden_by_aggregate(self):
        datasets = {d: cells(4) for d in range(3)}
        cell(datasets[2], "config-reuse", "reuse", "vdot")["total"] = 440
        aggregate = cells()
        cell(aggregate, "config-reuse", "reuse", "vdot")["total"] = 1240
        self.assertEqual(matrix.assess(aggregate, [], True)["decision"], "PERFORMANCE_CANDIDATE")
        self.assertEqual(matrix.decide_shape(aggregate, datasets, [], True)["decision"], "REJECT")

    def test_single_dataset_nonprimary_regression_not_hidden_by_aggregate(self):
        datasets = {d: cells(4) for d in range(3)}
        cell(datasets[2], "config-reuse", "basic", "vdot")["total"] = 561
        aggregate = cells()
        cell(aggregate, "config-reuse", "basic", "vdot")["total"] = 1641
        self.assertEqual(matrix.assess(aggregate, [], True)["decision"], "PERFORMANCE_CANDIDATE")
        self.assertEqual(matrix.decide_shape(aggregate, datasets, [], True)["decision"], "INCONCLUSIVE")

    def test_aggregate_must_equal_dataset_totals(self):
        datasets = {d: cells(4) for d in range(3)}
        cell(datasets[1], "firstdot", "basic", "vdot")["total"] += 1
        with self.assertRaises(ValueError):
            matrix.decide_shape(cells(), datasets, [], True)

    def test_dataset_keys_must_not_be_bool_aliases(self):
        for datasets in [{False: cells(4), 1: cells(4), 2: cells(4)},
                         {0: cells(4), True: cells(4), 2: cells(4)}]:
            with self.assertRaises(ValueError):
                matrix.decide_shape(cells(), datasets, [], True)

    def test_decision_public_data_survives_json_round_trip(self):
        value = matrix.decide_shape(cells(), {d: cells(4) for d in range(3)}, [], True)
        self.assertEqual(json.loads(json.dumps(value)), value)



class TimingTests(unittest.TestCase):
    def test_four_overlapping_envelopes_allowed_at_four_workers(self):
        value = matrix.validate_timing([timing_record(i) for i in range(1, 5)], 4, BOOT, bounds=(1, 100))
        self.assertIsNotNone(value)

    def test_five_overlaps_rejected_at_four_workers(self):
        with self.assertRaises(ValueError):
            matrix.validate_timing([timing_record(i) for i in range(1, 6)], 4, BOOT)

    def test_three_limit_rejects_four_overlaps(self):
        with self.assertRaises(ValueError):
            matrix.validate_timing([timing_record(i) for i in range(1, 5)], 3, BOOT)

    def test_equal_boundary_is_not_overlap(self):
        matrix.validate_timing([timing_record(1, 10, 20), timing_record(2, 20, 30)], 1, BOOT)

    def test_invalid_worker_budget_rejected(self):
        for workers in (0, 5, True, 1.0):
            with self.assertRaises(ValueError):
                matrix.validate_timing([timing_record(1)], workers, BOOT)

    def test_invalid_pid_time_scope_or_boot_rejected(self):
        for key, value in [("start_ns", True), ("end_ns", 20.0), ("end_ns", 9),
                           ("end_ns", 10), ("pid", False), ("pid", 0), ("pid", 2),
                           ("boot_id", "other-boot"), ("scope", "utc_elapsed")]:
            rec = timing_record(1)
            rec["monotonic"][key] = value
            with self.subTest(key=key, value=value):
                with self.assertRaises(ValueError):
                    matrix.validate_timing([rec], 1, BOOT)

    def test_duplicate_pid_rejected(self):
        with self.assertRaises(ValueError):
            matrix.validate_timing([timing_record(1), timing_record(1, 21, 30)], 2, BOOT)

    def test_missing_monotonic_and_empty_records_rejected(self):
        for records in [[], [dict(pid=1)]]:
            with self.assertRaises((ValueError, KeyError)):
                matrix.validate_timing(records, 1, BOOT)

    def test_campaign_bounds_enforced(self):
        for bounds in [(11, 100), (1, 19), (30, 1)]:
            with self.assertRaises(ValueError):
                matrix.validate_timing([timing_record(1)], 1, BOOT, bounds=bounds)


class ImageScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.bins = []
        self.common = {"/fixed/source.py": "c" * 64}
        for n in range(12):
            p = root / str(n) / "vdot-perf.bin"
            p.parent.mkdir()
            p.write_bytes(f"comparison{n}".encode())
            self.bins.append(str(p))
            self.common[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()

    def test_all_twelve_exact_comparisons_removed_only_from_process_map(self):
        original = dict(self.common)
        self.assertEqual(matrix.process_inputs(self.common, set(self.bins)),
                         {"/fixed/source.py": "c" * 64})
        self.assertEqual(self.common, original)

    def test_unknown_extra_comparison_rejected(self):
        common = self.common | {"/unexpected/vdot-perf.bin": "0" * 64}
        with self.assertRaises(ValueError):
            matrix.process_inputs(common, set(self.bins))

    def test_missing_comparison_key_rejected(self):
        common = dict(self.common)
        common.pop(self.bins[0])
        with self.assertRaises(ValueError):
            matrix.process_inputs(common, set(self.bins))

    def test_wrong_comparison_digest_or_missing_bytes_rejected(self):
        for kind in ("digest", "missing"):
            with self.subTest(kind=kind):
                if kind == "digest":
                    common = self.common | {self.bins[0]: "0" * 64}
                else:
                    common = self.common
                    Path(self.bins[0]).unlink()
                with self.assertRaises(ValueError):
                    matrix.process_inputs(common, set(self.bins))

    def test_symlink_comparison_rejected(self):
        p = Path(self.bins[0]);q = p.with_name("original.bin")
        p.rename(q);p.symlink_to(q)
        with self.assertRaises(ValueError):
            matrix.process_inputs(self.common, set(self.bins))


class RecoveryTests(unittest.TestCase):
    def test_exact_same_bin_normal_reference_recovery(self):
        matrix.validate_recovery(*recovery_pair())

    def test_changed_image_identity_rejected(self):
        for key, value in [("name", "different"), ("shard", 5), ("dataset", 2),
                           ("variant", "firstdot"), ("image_sha256", "c" * 64),
                           ("path", "/different-build"), ("suite", "other")]:
            neg, normal = recovery_pair();normal[key] = value
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    matrix.validate_recovery(neg, normal)

    def test_wrong_status_exit_replay_or_started_rejected(self):
        for key, value in [("exit_code", 1), ("exit_code", False), ("replay", 1),
                           ("process_started", False), ("negative", True),
                           ("status", "FAILED"), ("mode", "legacy"), ("contract", "different")]:
            neg, normal = recovery_pair();normal[key] = value
            with self.subTest(key=key, value=value):
                with self.assertRaises(ValueError):
                    matrix.validate_recovery(neg, normal)

    def test_fault_must_be_actual_high_bit_and_vector_destination(self):
        for key, value in [("word", "0x00000000"), ("vd", 1), ("bit", 31)]:
            neg, normal = recovery_pair();neg["negative_details"][key] = value
            with self.assertRaises(ValueError):
                matrix.validate_recovery(neg, normal)

    def test_fault_fixture_cannot_be_normal_reference(self):
        neg, normal = recovery_pair();normal["reference"] = neg["reference"]
        with self.assertRaises(ValueError):
            matrix.validate_recovery(neg, normal)

    def test_golden_reference_digest_mismatch_rejected(self):
        neg, normal = recovery_pair();normal["files"][normal["reference"]] = "c" * 64
        with self.assertRaises(ValueError):
            matrix.validate_recovery(neg, normal)

    def test_same_pid_and_overlap_or_boot_mismatch_rejected(self):
        for change in ("pid", "overlap", "boot"):
            neg, normal = recovery_pair()
            if change == "pid":
                normal["pid"] = normal["monotonic"]["pid"] = neg["pid"]
            elif change == "overlap":
                normal["monotonic"]["start_ns"] = 19
            else:
                normal["monotonic"]["boot_id"] = "different-boot"
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    matrix.validate_recovery(neg, normal)

    def test_wrong_fault_environment_rejected(self):
        neg, normal = recovery_pair();normal["environment_overrides"]["XS_NEGATIVE_VECTOR_TARGET"] = "vdot"
        with self.assertRaises(ValueError):
            matrix.validate_recovery(neg, normal)


def normal_records():
    return [dict(copy.deepcopy(s["image"]), label=s["label"], phase=s["phase"],
                 replay=s["replay"], negative=False, status=matrix.NORMAL_PASS,
                 process_started=True, exit_code=0, contract=matrix.CONTRACT,
                 mode="merged", samples=[dict(seq=n) for n in range(24)])
            for s in matrix.run_specs(image_set()) if not s["negative"]]


class RecordTests(unittest.TestCase):
    def test_exact_normal_and_replay_inventory(self):
        self.assertEqual(len(matrix.validate_records(normal_records(), image_set())), 32)

    def test_missing_duplicate_extra_or_reordered_record_rejected(self):
        records = normal_records()
        for mutated in [records[:-1], records + [records[0]],
                        records[:-1] + [records[0]],
                        [records[1], records[0], *records[2:]]]:
            with self.assertRaises(ValueError):
                matrix.validate_records(mutated, image_set())

    def test_record_identity_cannot_substitute_another_image(self):
        for key, value in [("shard", 5), ("dataset", 2), ("variant", "firstdot"),
                           ("name", "unexpected"), ("path", "/elsewhere"),
                           ("image_sha256", "0" * 64), ("suite", "unknown")]:
            records = normal_records()
            records[0][key] = value
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    matrix.validate_records(records, image_set())

    def test_record_status_replay_types_and_window_count(self):
        for key, value in [("replay", False), ("replay", 1), ("exit_code", False),
                           ("exit_code", 1), ("negative", 0), ("negative", True),
                           ("process_started", 1), ("status", "FAILED"),
                           ("contract", "old"), ("mode", "old"),
                           ("phase", "formal"), ("label", "unexpected"),
                           ("samples", [dict(seq=n) for n in range(23)])]:
            records = normal_records()
            records[0][key] = value
            with self.subTest(key=key, value=value):
                with self.assertRaises(ValueError):
                    matrix.validate_records(records, image_set())


# This integration double never launches a target process. It exercises the
# real controller's schedule, callbacks, JSON schema and read-only audit shell.
import ast
from datetime import datetime, timezone
import json
import statistics
import threading
from types import SimpleNamespace
from unittest.mock import patch


class HostCampaignDouble(matrix.Matrix):
    def __init__(self, root):
        self.root = Path(root)
        self.repo = self.root / "fake-source"
        self.repo.mkdir()
        self._images = image_set()
        for image in self._images:
            path = self.root / "build" / "images" / image["name"]
            (path / "data").mkdir(parents=True)
            (path / "vdot-perf.bin").write_bytes(image["name"].encode())
            image["path"] = str(path)
            image["image_sha256"] = matrix.sha(path / "vdot-perf.bin")
            rows = [dict(software=sw, method=method, config_reuse_proof=dict(
                        removed=image["variant"] == "config-reuse" and sw == "reuse"))
                    for sw in ("basic", "reuse") for method in ("vdot", "rvv")]
            matrix.save(path / "data/manifest.json", dict(rows=rows))
        ref = self.root / "normal-reference.so"
        ref.write_bytes(b"HOST-ONLY-NOT-A-REAL-NEMU")
        self.identity = dict(configuration=dict(reference=str(ref)),
                             hardware_profile=dict(kind="HOST_TEST_DOUBLE_NOT_HARDWARE"))
        self.identity_path = self.root / "identity.json"
        matrix.save(self.identity_path, self.identity)
        self.precondition = dict(kind="HOST_TEST_DOUBLE")
        self.common = {str(ref): matrix.sha(ref), str(self.identity_path): matrix.sha(self.identity_path)}
        self._comparisons = set()
        for n in range(12):
            p = self.root / "comparisons" / str(n) / "vdot-perf.bin"
            p.parent.mkdir(parents=True)
            p.write_bytes(("HOST-COMPARISON-" + str(n)).encode())
            self._comparisons.add(str(p))
            self.common[str(p)] = matrix.sha(p)
        self._pid = 700000
        self._pid_lock = threading.Lock()
        self.g = SimpleNamespace()
        # Use the frozen summarizer body unchanged, with its only globals.
        frozen = HERE.parents[2] / "clean-02/checkout/source/team/optimizations/o2/r2-config-reuse/runtime_experiment.py"
        tree = ast.parse(frozen.read_text(), filename=str(frozen))
        summarize = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "summarize")
        scope = dict(g=SimpleNamespace(require=matrix.require), VARIANTS=matrix.VARIANTS,
                     statistics=statistics)
        exec(compile(ast.Module(body=[summarize], type_ignores=[]), str(frozen), "exec"), scope)
        self.a = SimpleNamespace(summarize=scope["summarize"], negative_target=lambda image: 0x80002000)
        self.baseline_records = [dict(image, replay=0, samples=self.samples(image))
                                 for image in self._images if image["variant"] == "firstdot"]

    def selected(self, build):
        return copy.deepcopy(self._images)

    def external(self, output, extra=()):
        matrix.require(not Path(output).exists(), "new host-double output required")

    def physical(self):
        return copy.deepcopy((self.identity, self.common, self.identity["hardware_profile"]))

    def comparison_bins(self):
        return set(self._comparisons)

    def common_inputs(self, build, images, m, physical):
        return dict(self.common)

    def samples(self, image):
        result = []
        for n, (sw, method) in enumerate((sw, method) for sw in ("basic", "reuse")
                                         for method in ("vdot", "rvv")):
            cycles = cell(cells(), image["variant"], sw, method)["mean"]
            for repeat in range(6):
                result.append(dict(seq=6*n+repeat, repeat=repeat, cycles=cycles, instructions=10,
                    phase="measured" if repeat >= 2 else ("first" if repeat == 0 else "warmup"),
                    variant=image["variant"], shard=image["shard"], software=sw, method=method,
                    image_sha256=image["image_sha256"]))
        return result

    def runtime(self):
        def verify_files(files):
            for path, digest in files.items():
                matrix.require(matrix.sha(path) == digest, "host-double file drift")
        def now():
            return datetime.now(timezone.utc).isoformat()
        def fake_spawn(argv, cwd, stdout, stderr, record, persist, **kwargs):
            with self._pid_lock:
                self._pid += 1
                pid = self._pid
            record.update(pid=pid, process_started=True)
            persist()
            return 0
        f = SimpleNamespace(now=now, spawn=fake_spawn)
        def build_negative(repo, cfg, out):
            out.mkdir()
            p = out / "fault-reference.so"
            p.write_bytes(b"HOST-ONLY-NOT-A-REAL-FAULT-NEMU")
            value = dict(binary=str(p), negative_sha256=matrix.sha(p))
            matrix.save(out / "fixture.json", value)
            return value
        def execute(repo, cfg, image, destination, common, fixture, replay, progress):
            destination.mkdir(parents=True)
            reference = fixture["binary"] if fixture else cfg["reference"]
            record = dict(image, replay=replay, negative=fixture is not None,
                          contract=matrix.CONTRACT, mode="merged", process_started=False,
                          started=now(), reference=reference, status="HOST_DOUBLE_RUNNING",
                          files=dict(common), environment_overrides={
                              "XS_NEGATIVE_VECTOR_TARGET": "vdot" if fixture else None})
            record["files"][str(Path(image["path"]) / "vdot-perf.bin")] = image["image_sha256"]
            if fixture:
                record["files"][reference] = fixture["negative_sha256"]
            def persist():
                matrix.save(destination / "result.json", record)
                progress(record)
            f.spawn([], destination, None, None, record, persist)
            record.update(status=matrix.NEGATIVE_PASS if fixture else matrix.NORMAL_PASS,
                          exit_code=1 if fixture else 0, finished=now())
            if fixture:
                record["negative_details"] = dict(word="0x0388000b", vd=0, bit=100, pc="0x80002000")
            else:
                record["samples"] = self.samples(image)
            persist()
            return record
        m = SimpleNamespace(verify_files=verify_files, build_negative=build_negative, execute=execute,
                            NORMAL_PASS=matrix.NORMAL_PASS, NEGATIVE_PASS=matrix.NEGATIVE_PASS)
        return f, m


class ControllerAuditIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="matrix-host-only-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.p = HostCampaignDouble(self.root)
        self.build = self.root / "build"
        self.campaign = self.root / "synthetic-campaign"
        self.audit = matrix.load("matrix_host_schema_audit", HERE / "raw_audit.py")

    @staticmethod
    def fake_record_audit(repo, g, f, m, cfg, image, directory, common,
                          outer_contract, **kwargs):
        record = matrix.read(Path(directory) / "result.json")
        return dict(record=record, audit=dict(
            status="HOST_DOUBLE_NOT_RAW_REPARSE", negative=kwargs["negative"],
            windows=0 if kwargs["negative"] else len(record["samples"])))

    def run_campaign(self):
        # If any path unexpectedly attempts to spawn a real process, fail.
        with patch.object(matrix.os, "sched_getaffinity", return_value={0, 1, 2, 3}), \
                patch.object(matrix.subprocess, "Popen", side_effect=AssertionError(
                    "real process spawn is forbidden in the host double")):
            return self.p.run(self.build, self.campaign, "HOST_SCHEMA_TEST_NOT_HARDWARE", workers=4)

    def audit_campaign(self):
        with patch.object(self.audit, "record_audit", side_effect=self.fake_record_audit), \
                patch.object(matrix.subprocess, "Popen", side_effect=AssertionError(
                    "real process spawn is forbidden in the host double")):
            return self.audit.audit_matrix(self.p, self.build, self.campaign)

    def test_real_schedule_receipt_hooks_summary_schema_and_audit_join(self):
        result = self.run_campaign()
        state = matrix.read(self.campaign / "state.json")
        self.assertEqual(result["summary"]["measured_windows"], 384)
        self.assertEqual(len(result["runs"]), 32)
        self.assertEqual(state["new_emu_runs"], 33)  # synthetic receipts, not real EMU
        self.assertEqual(state["active_pids"], {})
        self.assertEqual(len(list((self.campaign / "runs").iterdir())), 33)
        for record in result["runs"]:
            saved = matrix.read(self.campaign / "runs" / record["label"] / "result.json")
            self.assertEqual(saved, record)
        audited = self.audit_campaign()
        self.assertEqual(audited["formal_windows"], 384)
        self.assertEqual(audited["normal_all_windows"], 768)
        self.assertEqual(audited["replay_window_pairs"], 192)
        self.assertEqual(audited["baseline_firstdot_windows"], 288)
        self.assertEqual(audited["decisions"], result["decisions"])
        self.assertLessEqual(audited["timing"]["peak_process_envelopes"], 4)
        self.assertTrue(audited["campaign_evidence_unchanged"])

    def test_changed_cached_nested_summary_rejected(self):
        self.run_campaign()
        path = self.campaign / "results.json"
        cached = matrix.read(path)
        cached["summary"]["measured_windows"] = 383
        matrix.save(path, cached)
        with self.assertRaisesRegex(ValueError, "cached.*statistics"):
            self.audit_campaign()


    def test_each_shape_keeps_its_own_full_firstdot_control_decision(self):
        result = self.run_campaign()
        prior = next(r for r in self.p.baseline_records if (r["shard"], r["dataset"]) == (1, 0))
        prior["samples"][0]["instructions"] += 1
        _, decisions, replay = self.p.evaluate(result["runs"], self.p._images, None)
        self.assertTrue(replay)
        self.assertEqual(decisions["4x8"]["decision"], "INCONCLUSIVE")
        self.assertTrue(all(row["decision"] == "PERFORMANCE_CANDIDATE"
                            for shape, row in decisions.items() if shape != "4x8"))

    def test_unchanged_rvv_control_checks_unmeasured_first_window(self):
        result = self.run_campaign()
        record = next(r for r in result["runs"] if (r["shard"], r["dataset"], r["variant"], r["replay"]) ==
                      (3, 2, "config-reuse", 0))
        first = next(s for s in record["samples"] if
                     (s["software"], s["method"], s["repeat"]) == ("basic", "rvv", 0))
        first["instructions"] += 1
        _, decisions, replay = self.p.evaluate(result["runs"], self.p._images, None)
        self.assertTrue(replay)
        self.assertEqual(decisions["8x32"]["decision"], "INCONCLUSIVE")
        self.assertTrue(any("RVV six-window differs" in issue for issue in
                            decisions["8x32"]["unexplained_controls"]))
        self.assertTrue(all(row["decision"] == "PERFORMANCE_CANDIDATE"
                            for shape, row in decisions.items() if shape != "8x32"))

    def test_replay_compares_complete_sample_dict_not_cycle_signature(self):
        result = self.run_campaign()
        record = next(r for r in result["runs"] if (r["shard"], r["variant"], r["replay"]) ==
                      (5, "config-reuse", 1))
        record["samples"][0]["repeat"] = 99
        _, decisions, replay = self.p.evaluate(result["runs"], self.p._images, None)
        self.assertFalse(replay)
        self.assertEqual(decisions["16x64"]["decision"], "INCONCLUSIVE")
        self.assertTrue(all(row["decision"] == "PERFORMANCE_CANDIDATE"
                            for shape, row in decisions.items() if shape != "16x64"))


if __name__ == "__main__":
    unittest.main()
