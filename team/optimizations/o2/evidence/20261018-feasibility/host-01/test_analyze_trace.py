"""Focused negative tests for window attribution, identities and archive integrity."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("o2_trace", Path(__file__).with_name("analyze_trace.py"))
trace = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trace)


def event(cycle, kind, **fields):
    return (cycle, 0, kind, dict(cycle=cycle, **fields))


def fixture():
    sample = dict(mode="o1", scenario="batch", dataset=0, repeat=2, image="test",
                  seq=0, dots=2, cycles=10, sample_ticks=[0, 10, 20, 25],
                  counter_values=[0, 100, 110, 30])
    txs = [dict(seq=1, accept_cycle=12, end_cycle=14, elapsed_cycles=2, outcome="response"),
           dict(seq=2, accept_cycle=14, end_cycle=16, elapsed_cycles=2, outcome="response")]
    events = [event(12, "ACCEPT", seq=1), event(13, "VFEX4_WAIT", fu=trace.VDOT, busy=1),
              event(14, "RESPONSE", seq=1), event(14, "ACCEPT", seq=2),
              event(14, "HANDOFF", oldseq=1, newseq=2), event(16, "RESPONSE", seq=2)]
    return sample, events, txs, {1: 15, 2: 17}


class WindowTests(unittest.TestCase):
    def test_same_cycle_handoff_keeps_old_new_identities(self):
        result = trace.window_stats(*fixture())
        self.assertEqual(result["accept_gap_histogram"], {"2": 1})
        self.assertEqual(result["counts"]["HANDOFF"], 1)
        self.assertEqual(result["accepted_and_committed_in_window"], 2)
        self.assertFalse(any(result["boundary_audit"].values()))

    def test_half_open_window_and_crossing_transaction_are_explicit(self):
        sample, events, txs, commits = fixture()
        events += [event(20, "ACCEPT", seq=3)]
        txs += [dict(seq=3, accept_cycle=20, end_cycle=22, elapsed_cycles=2, outcome="response"),
                dict(seq=0, accept_cycle=9, end_cycle=11, elapsed_cycles=2, outcome="response")]
        result = trace.window_stats(sample, events, txs, commits)
        self.assertEqual(result["counts"]["ACCEPT"], 2)
        self.assertEqual(result["boundary_audit"]["events_exactly_at_stop"], 1)
        self.assertEqual(result["boundary_audit"]["accepted_before_start_completed_inside"], 1)
        self.assertEqual(result["accept_gap_histogram"], {"2": 1})

    def test_absent_commit_and_late_response_are_reported(self):
        sample, events, txs, commits = fixture()
        txs[1]["end_cycle"] = 20
        del commits[2]
        result = trace.window_stats(sample, events, txs, commits)
        self.assertEqual(result["boundary_audit"]["accepted_inside_completed_at_or_after_stop"], 1)
        self.assertEqual(result["boundary_audit"]["accepted_inside_commit_outside_or_absent"], 1)

    def test_wait_busy_classes_and_overlap_are_not_summed(self):
        sample, events, txs, commits = fixture()
        events += [event(14, "VFEX4_WAIT", fu=trace.VDOT, busy=0),
                   event(15, "VFEX4_WAIT", fu=1 << 22, busy=1)]
        result = trace.window_stats(sample, events, txs, commits)
        self.assertEqual(result["vdot_wait_by_busy"], {"0": 1, "1": 1})
        self.assertEqual(result["counts"]["VFEX4_WAIT"], 3)
        self.assertEqual(result["wait_overlap_response_cycles"], 1)

    def test_duplicate_wait_rejected(self):
        args = fixture()
        args[1].append(copy.deepcopy(args[1][1]))
        with self.assertRaisesRegex(ValueError, "duplicate wait"):
            trace.window_stats(*args)

    def test_cycle_delta_drift_rejected(self):
        args = fixture()
        args[0]["cycles"] += 1
        with self.assertRaisesRegex(ValueError, "CSR/global"):
            trace.window_stats(*args)

    def test_counter_value_delta_drift_rejected(self):
        args = fixture()
        args[0]["counter_values"][2] += 1
        with self.assertRaisesRegex(ValueError, "CSR value"):
            trace.window_stats(*args)

    def test_duplicate_accept_cycle_rejected(self):
        sample, events, txs, commits = fixture()
        txs[1]["accept_cycle"] = 12
        with self.assertRaisesRegex(ValueError, "non-increasing"):
            trace.window_stats(sample, events, txs, commits)

    def test_commit_identity_across_rob_reuse(self):
        events = [event(1, "ENQUEUE", rob="0:1"), event(2, "ACCEPT", rob="0:1", seq=7),
                  event(4, "COMMIT", rob="0:1"), event(4, "ENQUEUE", rob="0:1"),
                  event(5, "ACCEPT", rob="0:1", seq=8), event(7, "COMMIT", rob="0:1")]
        self.assertEqual(trace.commit_cycles(events), {7: 4, 8: 7})

    def test_unbound_commit_rejected(self):
        with self.assertRaisesRegex(ValueError, "unbound commit"):
            trace.commit_cycles([event(1, "COMMIT", rob="0:1")])

    def test_missing_formal_samples_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing formal samples"):
            trace.summarize([])


class AllocationWaitTests(unittest.TestCase):
    def test_rob_reuse_does_not_rebind_old_speculative_wait(self):
        events = [event(1, "ENQUEUE", rob="0:1"),
                  event(2, "VFEX4_WAIT", rob="0:1", fu=trace.VDOT, busy=1),
                  event(3, "REDIRECT", rob="0:0", self=0),
                  event(4, "ENQUEUE", rob="0:1"),
                  event(5, "VFEX4_WAIT", rob="0:1", fu=trace.VDOT, busy=1),
                  event(6, "ACCEPT", rob="0:1", seq=1),
                  event(8, "COMMIT", rob="0:1")]
        waits = trace.wait_allocation_generations(events)
        self.assertNotEqual(waits[2]["generation"], waits[5]["generation"])
        self.assertEqual(trace.wait_fate(waits[2], 0, 10), "cancelled_before_accept")
        self.assertEqual(trace.wait_fate(waits[5], 0, 10), "accepted_and_committed_in_window")

    def test_wait_committed_outside_window_is_separate(self):
        entry = dict(accept_cycle=15, commit_cycle=21)
        self.assertEqual(trace.wait_fate(entry, 10, 20), "committed_outside_or_accepted_outside_window")

    def test_same_cycle_rob_redirect_and_younger_accept_retains_cancel(self):
        events = [event(1, "ENQUEUE", rob="0:1"),
                  event(2, "VFEX4_WAIT", rob="0:1", fu=trace.VDOT, busy=1),
                  event(3, "REDIRECT", rob="0:0", self=0),
                  event(3, "ACCEPT", rob="0:1", seq=1)]
        waits = trace.wait_allocation_generations(events)
        self.assertEqual(trace.wait_fate(waits[2], 0, 10), "accepted_then_cancelled")

    def test_opposite_rob_flag_equal_index_is_younger(self):
        events = [event(1, "ENQUEUE", rob="1:1"),
                  event(2, "VFEX4_WAIT", rob="1:1", fu=trace.VDOT, busy=1),
                  event(3, "REDIRECT", rob="0:1", self=0)]
        waits = trace.wait_allocation_generations(events)
        self.assertEqual(trace.wait_fate(waits[2], 0, 10), "cancelled_before_accept")

    def test_unbound_vdot_wait_rejected_but_other_fu_not_misattributed(self):
        other = [event(1, "VFEX4_WAIT", rob="0:1", fu=1 << 22, busy=1)]
        self.assertEqual(trace.wait_allocation_generations(other), {})
        with self.assertRaisesRegex(ValueError, "unbound waiting"):
            trace.wait_allocation_generations([event(1, "VFEX4_WAIT", rob="0:1", fu=trace.VDOT, busy=1)])


class ArchiveTests(unittest.TestCase):
    def test_payload_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = b"accepted original evidence"
            raw = trace.gzip.compress(payload, mtime=0)
            (root / "data.gz").write_bytes(raw)
            entry = dict(source="/old/run/log", source_sha256=trace.digest(payload),
                         source_bytes=len(payload), archive="data.gz",
                         archive_sha256=trace.digest(raw), archive_bytes=len(raw), storage="gzip")
            file_map = json.dumps([entry]).encode()
            (root / "file-map.json").write_bytes(file_map)
            manifest = json.dumps(dict(files={"file-map.json": trace.digest(file_map),
                                             "data.gz": trace.digest(raw)})).encode()
            (root / "archive-manifest.json").write_bytes(manifest)
            with patch.object(trace, "MANIFEST_SHA", trace.digest(manifest)):
                archive = trace.Archive(root)
                self.assertEqual(archive.read("/run/log"), payload)
                (root / "data.gz").write_bytes(raw + b"tamper")
                with self.assertRaisesRegex(ValueError, "stored bytes changed"):
                    archive.read("/run/log")

    def test_manifest_drift_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "archive-manifest.json").write_bytes(b"{}")
            with self.assertRaisesRegex(ValueError, "sealed manifest changed"):
                trace.Archive(root)


if __name__ == "__main__":
    unittest.main()
