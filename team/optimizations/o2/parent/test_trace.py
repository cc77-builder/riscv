"""Handwritten protocol fixture and corruption tests for offline G2 replay."""
import copy
import unittest
from check_trace import CYCLE_KEYS, FU_KEYS, PASS_KEYS, TraceError, check_trace


def record(cycle, **changes):
    row = {key: 0 for key in CYCLE_KEYS}
    row.update(schema=1, cycle=cycle, case="fixture", block_reason="none",
               ready=1, out_ready=1, child_ready=7)
    row.update(changes)
    return row


def fixture():
    # E0 reset; A then B; blocked R(A); kill only P(B); A responds while
    # accepting C; reset+redirect drops C exactly once. Then DIV starts,
    # stalls and is cancelled on its visible output. No terminal is duplicated.
    rows = [
        record(0, reset=1, te=1, ready=0, child_ready=6, clocks=7, block_reason="reset"),
        record(1, offered=1, rob=8, accept=1, accept_seq=1, child_fire=1,
               clocks=1, next_occupancy=1, accepted_total=1, inflight=1),
        record(2, p=1, pseq=1, occupancy=1, busy=1, offered=1, rob=12,
               accept=1, accept_seq=2, child_fire=1, p_to_r=1, clocks=1,
               next_occupancy=2, accepted_total=2, inflight=2),
        record(3, p=1, r=1, pseq=2, rseq=1, occupancy=2, busy=1, ready=0,
               child_ready=6, child_out=1, out_ready=0, stall=1, clocks=1,
               block_reason="vdot-full", next_occupancy=2, accepted_total=2, inflight=2),
        record(4, p=1, r=1, pseq=2, rseq=1, occupancy=2, busy=1, ready=0,
               offered=1, redirect=1, redirect_rob=10, kill_p=1, child_ready=6,
               child_out=1, out_ready=0, stall=1, clocks=1, block_reason="redirect",
               next_occupancy=1, accepted_total=2, cancels_total=1, inflight=1),
        record(5, r=1, rseq=1, occupancy=1, busy=1, offered=1, rob=20,
               accept=1, accept_seq=3, child_fire=1, child_out=1, response=1,
               response_seq=1, clocks=1, next_occupancy=1, accepted_total=3,
               responses_total=1, cancels_total=1, inflight=1),
        record(6, p=1, pseq=3, occupancy=1, busy=1, offered=1, ready=0,
               child_ready=6, reset=1, redirect=1, redirect_rob=10, reset_drop=1,
               clocks=1, block_reason="reset", accepted_total=3,
               responses_total=1, cancels_total=1, resets_total=1),
        record(7, kind=1, offered=1, rob=30, accept=1, accept_seq=4, child_fire=2,
               clocks=2, accepted_total=4, responses_total=1, cancels_total=1,
               resets_total=1, inflight=1),
        record(8, divseq=4, busy=1, ready=0, child_ready=5, clocks=2,
               block_reason="DIV", accepted_total=4, responses_total=1,
               cancels_total=1, resets_total=1, inflight=1),
        record(9, divseq=4, busy=1, ready=0, child_ready=5, child_out=2,
               out_ready=0, stall=1, clocks=2, block_reason="DIV",
               accepted_total=4, responses_total=1, cancels_total=1,
               resets_total=1, inflight=1),
        record(10, divseq=4, busy=1, ready=0, child_ready=4, child_out=2,
               redirect=1, redirect_rob=30, self=1, kill_div=1, clocks=2,
               block_reason="redirect", accepted_total=4, responses_total=1,
               cancels_total=2, resets_total=1),
        record(11, clocks=0, accepted_total=4, responses_total=1,
               cancels_total=2, resets_total=1),
        record(12, reset=1, ready=0, child_ready=6, clocks=3,
               block_reason="reset", accepted_total=4, responses_total=1,
               cancels_total=2, resets_total=1),
    ]
    per_fu = [{key: 0 for key in FU_KEYS} for _ in range(3)]
    for kind, pf in enumerate(per_fu):
        pf.update(kind=kind, latency_min=9999)
    per_fu[0].update(accepted=3, responded=1, killed=1, reset_dropped=1,
                     latency_min=2, latency_max=2, latency_samples=1, clock_edges=8)
    per_fu[1].update(accepted=1, killed=1, raw_killed_response=1,
                     latency_min=2, latency_max=2, latency_samples=1, clock_edges=6)
    per_fu[2].update(clock_edges=1)
    final = {key: 0 for key in PASS_KEYS}
    final.update(schema=1, cycles=13, accepted=4, responses=1, cancelled=2,
                 reset_dropped=1, overlaps=1, stalls=3, p_to_r=1,
                 full_cycles=2, full_blocked=1, kill_p_only=1,
                 te0_resets=2, empty_te0_resets=1, parent_tested=1)
    return rows, per_fu, final


def encode(rows, per_fu, final):
    def line(prefix, values):
        return prefix + " " + " ".join(f"{key}={value}" for key, value in sorted(values.items()))
    return "\n".join([*(line("O2_PARENT_CYCLE", row) for row in rows),
                       *(line("O2_PARENT_FU", pf) for pf in per_fu),
                       line("O2_PARENT_PASS", final)]) + "\n"


class TraceTests(unittest.TestCase):
    def test_div_cancel_idle_clock_leak_rejected_even_with_matching_summary(self):
        rows, fus, final = fixture()
        rows[11]['clocks'] = 2
        fus[1]['clock_edges'] += 1
        with self.assertRaisesRegex(TraceError, 'idle FU retained clock'):
            check_trace(encode(rows, fus, final), require_campaign=False)

    def assert_bad_row(self, index, changes):
        rows, fus, final = fixture()
        rows[index].update(changes)
        with self.assertRaises(TraceError):
            check_trace(encode(rows, fus, final), require_campaign=False)

    def test_manual_elastic_div_cancel_reset_sequence(self):
        result = check_trace(encode(*fixture()), require_campaign=False)
        self.assertEqual(result["recomputed"]["accepted"], 4)
        self.assertEqual(result["recomputed"]["reset_dropped"], 1)
        self.assertEqual(result["per_fu"][1]["raw_killed_response"], 1)

    def test_small_fixture_cannot_claim_completed_campaign(self):
        with self.assertRaises(TraceError):
            check_trace(encode(*fixture()))

    def test_perf_v2_summary_uses_explicit_schema(self):
        rows, fus, final = fixture()
        final.update(perf_contract=2, perf_bits=577, perf_inputs=4,
                     perf_observations=5, perf_walk_one=577, perf_walk_zero=577)
        result = check_trace(encode(rows, fus, final), require_campaign=False)
        self.assertEqual(result["perf_contract"], 2)
        self.assertEqual(result["perf_observations_recomputed"], 5)
        # This deliberately small schema fixture is never a completed campaign.
        with self.assertRaises(TraceError):
            check_trace(encode(rows, fus, final))

    def test_perf_v2_observations_are_recomputed(self):
        rows, fus, final = fixture()
        final.update(perf_contract=2, perf_bits=577, perf_inputs=4,
                     perf_observations=4, perf_walk_one=577, perf_walk_zero=577)
        with self.assertRaisesRegex(TraceError, "incomplete perf v2 summary"):
            check_trace(encode(rows, fus, final), require_campaign=False)

    def test_perf_unknown_or_incomplete_schema_rejected(self):
        for changes in (dict(perf_contract=3), dict(perf_bits=576),
                        dict(perf_extra=0)):
            rows, fus, final = fixture()
            final.update(perf_contract=2, perf_bits=577, perf_inputs=4,
                         perf_observations=5, perf_walk_one=577, perf_walk_zero=577)
            final.update(changes)
            with self.subTest(changes=changes), self.assertRaises(TraceError):
                check_trace(encode(rows, fus, final), require_campaign=False)
        rows, fus, final = fixture()
        final["perf_bits"] = 577
        with self.assertRaises(TraceError):
            check_trace(encode(rows, fus, final), require_campaign=False)

    def test_slot_sequence_swap_rejected(self):
        self.assert_bad_row(3, dict(pseq=1, rseq=2))

    def test_missing_cancel_rejected(self):
        self.assert_bad_row(4, dict(kill_p=0))

    def test_wrong_survivor_cancel_rejected(self):
        self.assert_bad_row(4, dict(kill_r=1))

    def test_reset_cannot_also_cancel_same_request(self):
        self.assert_bad_row(6, dict(kill_p=1))

    def test_rob_age_oracle_is_independent_of_logged_kill(self):
        self.assert_bad_row(2, dict(rob=6))

    def test_response_identity_rejected(self):
        self.assert_bad_row(5, dict(response_seq=2))

    def test_dropped_response_rejected(self):
        self.assert_bad_row(5, dict(response=0, response_seq=0))

    def test_missing_active_clock_rejected(self):
        self.assert_bad_row(3, dict(clocks=0))

    def test_missing_empty_reset_clock_rejected(self):
        self.assert_bad_row(12, dict(clocks=2))

    def test_false_ready_rejected(self):
        self.assert_bad_row(3, dict(ready=1))

    def test_false_busy_rejected(self):
        self.assert_bad_row(3, dict(busy=0))

    def test_parent_child_acceptance_mismatch_rejected(self):
        self.assert_bad_row(2, dict(child_fire=0))

    def test_double_output_rejected(self):
        self.assert_bad_row(3, dict(child_out=3))

    def test_ghost_after_div_cancel_has_no_grace(self):
        self.assert_bad_row(11, dict(child_out=2, ready=0, busy=1, block_reason="DIV"))

    def test_div_cancel_cannot_be_response(self):
        self.assert_bad_row(10, dict(response=1, response_seq=4))

    def test_running_counter_rejected(self):
        self.assert_bad_row(5, dict(accepted_total=2))

    def test_duplicate_accept_sequence_rejected(self):
        self.assert_bad_row(5, dict(accept_seq=2))

    def test_bad_final_summary_rejected(self):
        rows, fus, final = fixture()
        final["accepted"] = 5
        with self.assertRaises(TraceError):
            check_trace(encode(rows, fus, final), require_campaign=False)

    def test_bad_per_fu_summary_rejected(self):
        rows, fus, final = fixture()
        fus[1]["raw_killed_response"] = 0
        with self.assertRaises(TraceError):
            check_trace(encode(rows, fus, final), require_campaign=False)

    def test_stalled_div_valid_cannot_withdraw_without_kill(self):
        rows, fus, final = fixture()
        rows[8].update(child_out=2, out_ready=0, stall=1)
        rows[9].update(child_out=0, stall=0)
        # Preserve counters and adapt the first-visible latency; aggregate-only
        # checking would accept this invalid one-cycle withdrawal.
        fus[1].update(latency_min=1, latency_max=1)
        with self.assertRaisesRegex(TraceError, "stalled DIV valid withdrawn"):
            check_trace(encode(rows, fus, final), require_campaign=False)

    def test_unknown_transition_name_cannot_replace_real_pair(self):
        rows, fus, final = fixture()
        rows[1]["case"] = "switch-0-0-0"
        check_trace(encode(rows, fus, final), require_campaign=False)
        rows[1]["case"] = "switch-99-99-99"
        with self.assertRaisesRegex(TraceError, "unknown FU transition case"):
            check_trace(encode(rows, fus, final), require_campaign=False)

    def test_missing_cycle_rejected(self):
        rows, fus, final = fixture()
        rows.pop(3)
        with self.assertRaises(TraceError):
            check_trace(encode(rows, fus, final), require_campaign=False)

    def test_error_text_and_extra_pass_rejected(self):
        text = encode(*fixture())
        for extra in ("O2_PARENT_FAIL identity\n", text.splitlines()[-1] + "\n"):
            with self.subTest(extra=extra), self.assertRaises(TraceError):
                check_trace(text + extra, require_campaign=False)

    def test_duplicate_field_negative_integer_and_truncation_rejected(self):
        text = encode(*fixture())
        for invalid in (text.replace("schema=1", "schema=1 schema=1", 1),
                        text.replace("cycle=0", "cycle=-1", 1),
                        "\n".join(text.splitlines()[:-1])):
            with self.subTest(invalid=invalid[:80]), self.assertRaises(TraceError):
                check_trace(invalid, require_campaign=False)


if __name__ == "__main__":
    unittest.main()
