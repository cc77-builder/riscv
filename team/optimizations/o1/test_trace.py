"""Protocol examples and adversarial traces, independent of generated RTL text."""
import copy
import unittest

from check_trace import FRAME, HEX, TraceError, audit, killed, record


HEADER = dict(schema=1, cycle=0, mode=2, robsize=48, pdestbits=8, hart=0)


def line(tag, fields):
    return tag + " " + " ".join(f"{k}=" + (hex(v) if k in HEX else str(v)) for k, v in fields.items())


def frame(cycle, **changes):
    f = dict.fromkeys(sorted(FRAME), 0)
    f.update(cycle=cycle, ir=1, ready=1, iwv=1, vm=1, vl=8,
             a=0x0101010101010101, b=0x0202020202020202)
    f.update(changes)
    return f


def rob(cycle, rv, dest, **changes):
    f = dict(cycle=cycle, slot=0, rf=0, rv=rv, dest=dest, pc=0x80001000 + rv * 4, word=0x0200000b)
    f.update(changes)
    return f


def pair():
    # Results are literal expected sums: eight 1*2 products; then eight 1*3.
    # The response's destination and write class differ from the new request.
    return [
        ("O1_EXU_BEGIN", HEADER.copy()), ("O1_ROB_BEGIN", HEADER.copy()),
        ("O1_ROB_ENQ", rob(0, 1, 11)), ("O1_ROB_ENQ", rob(1, 2, 22)),
        ("O1_EXU", frame(2, iv=1, ca=1, irv=1, id=11)),
        ("O1_EXU", frame(3, busy=1, ir=0)),
        ("O1_EXU", frame(4, busy=1, iv=1, ca=1, irv=2, id=22, iwv=0, iw0=1,
                         b=0x0303030303030303, ov=1, cv=1, orv=1, od=11, owv=1, data=16, vec=16, v0=16)),
        ("O1_EXU", frame(5, busy=1, ir=0)),
        ("O1_EXU", frame(6, busy=1, ov=1, cv=1, orv=2, od=22, ow0=1, data=24, vec=24, v0=24)),
        ("O1_ROB_COMMIT", rob(8, 1, 11)), ("O1_ROB_COMMIT", rob(9, 2, 22)),
    ]


def encoded(rows):
    return [line(t, f) for t, f in rows]


class TraceTests(unittest.TestCase):
    def run_trace(self, rows):
        return audit(encoded(rows), 2, "fullcore")

    def reject(self, rows, reason):
        with self.assertRaisesRegex(TraceError, reason):
            self.run_trace(rows)

    def test_atomic_handoff_and_full_writeback(self):
        result = self.run_trace(pair())
        self.assertEqual((result["accepted"], result["responses"], result["overlap"]), (2, 2, 1))
        self.assertEqual(result["rob"], dict(allocated=2, committed=2))

    def test_old_identity_not_new_request(self):
        for key, value in (("od", 22), ("orv", 2), ("owv", 0), ("ow0", 1)):
            with self.subTest(key=key):
                rows = pair()
                rows[6][1][key] = value
                self.reject(rows, "identity|write enables")

    def test_full_128_bit_result_and_all_ports(self):
        for key in ("data", "vec", "v0"):
            rows = pair()
            rows[6][1][key] |= 1 << 127
            self.reject(rows, "writeback mismatch")
        rows = pair()
        rows[6][1].update(data=17, vec=17, v0=17)
        self.reject(rows, "independent VDot")

    def test_physical_vl_controls_illegal_result(self):
        rows = pair()
        rows[4][1]["vl"] = 7
        self.reject(rows, "independent VDot")
        rows[6][1].update(data=0, vec=0, v0=0, exc=4, owv=0)
        # The illegal transaction must be squashed by a trap, never committed.
        self.reject(rows, "commit without prior legal")

    def test_each_illegal_control_is_independent(self):
        for key, value in (("vill", 1), ("vm", 0), ("sew", 1), ("lmul", 1), ("start", 1), ("op", 1)):
            rows = pair()
            rows[4][1][key] = value
            self.reject(rows, "independent VDot")

    def test_missing_cycle_duplicate_cycle_and_truncated_tail(self):
        rows = pair()
        del rows[5]
        self.reject(rows, "missing busy")
        rows = pair()
        rows.insert(6, copy.deepcopy(rows[5]))
        self.reject(rows, "duplicate/reversed")
        self.reject(pair()[:8], "unfinished EXU")
        self.reject(pair()[:-1], "unfinished ROB")

    def test_child_handshake_and_busy_evidence(self):
        for index, key, value in ((4, "ca", 0), (6, "cv", 2), (5, "busy", 0)):
            rows = pair()
            rows[index][1][key] = value
            self.reject(rows, "acceptance mismatch|response mismatch|busy disagrees")

    def test_invalid_channels_do_not_assign_meaning_to_payload(self):
        rows = pair()
        rows[5][1].update(irv=63, orv=63, frv=63)
        self.assertEqual(self.run_trace(rows)["accepted"], 2)
        rows[4][1]["irv"] = 63
        self.reject(rows, "invalid ROB index")

    def test_mixed_fu_overlap_is_rejected(self):
        rows = pair()
        rows[6][1].update(kind=1, ca=2)
        self.reject(rows, "legal handoff|illegal shared-FU overlap")

    def test_ready_without_valid_still_obeys_flush_and_busy(self):
        rows = pair()
        rows[5][1]["ir"] = 1
        self.reject(rows, "ready advertised")
        rows = self.canceled()
        rows[9][1]["ir"] = 1
        self.reject(rows, "ready asserted during flush")

    def test_backpressure(self):
        rows = pair()
        rows[6][1].update(iv=0, ca=0, ir=0, ready=0)
        rows[7] = ("O1_EXU", frame(5, busy=1, ir=0, ready=0, ov=1, cv=1,
                                 orv=1, od=11, owv=1, data=16, vec=16, v0=16))
        rows[8] = ("O1_EXU", frame(6, busy=1, iv=1, ca=1, irv=2, id=22, iwv=0, iw0=1,
                                 b=0x0303030303030303, ov=1, cv=1, orv=1, od=11, owv=1, data=16, vec=16, v0=16))
        rows.insert(9, ("O1_EXU", frame(7, busy=1, ir=0)))
        rows.insert(10, ("O1_EXU", frame(8, busy=1, ov=1, cv=1, orv=2, od=22, ow0=1, data=24, vec=24, v0=24)))
        rows[-1][1]["cycle"] = 10
        self.assertEqual(self.run_trace(rows)["stalls"], 2)
        rows[7][1].update(data=15, vec=15, v0=15)
        self.reject(rows, "changed under backpressure")

    def canceled(self, redirect_cycle=5, flush_cycle=6):
        rows = pair()
        rows[8] = ("O1_EXU", frame(flush_cycle, busy=1, ir=0, fv=1, frv=2, self=1, kill=1))
        rows.insert(7, ("O1_ROB_REDIRECT", dict(cycle=redirect_cycle, rf=0, rv=2, self=1)))
        rows.pop()  # second instruction is architecturally squashed
        return rows

    def test_cancel_wins_and_explicit_redirect_delay(self):
        rows = self.canceled()
        result = self.run_trace(rows)
        self.assertEqual((result["canceled"], result["rob"]["squashed"]), (1, 1))
        self.reject(self.canceled(6), "exactly .1 cycle")
        rows[9][1].update(ov=1, cv=1)
        self.reject(rows, "cancel mismatch")

    def test_same_cycle_accept_before_registered_flush(self):
        # ROB redirect happens at cycle 4; EXU can still accept the doomed
        # second operation at cycle 4, then cancel it at cycle 5.
        rows = self.canceled(4, 5)
        del rows[8]  # replace the ordinary cycle-5 frame by the flush frame
        self.assertEqual(self.run_trace(rows)["overlap"], 1)

    def test_response_before_rob_squash(self):
        rows = pair()
        rows.insert(9, ("O1_ROB_REDIRECT", dict(cycle=7, rf=0, rv=2, self=1)))
        rows.insert(10, ("O1_EXU", frame(8, ir=0, fv=1, frv=2, self=1)))
        rows.pop()
        self.assertEqual(self.run_trace(rows)["rob"]["squashed"], 1)

    def test_rob_requires_allocation_response_and_identity(self):
        rows = pair()
        del rows[2]
        self.reject(rows, "without live")
        for key in ("dest", "pc", "word"):
            rows = pair()
            rows[-1][1][key] ^= 1
            self.reject(rows, "commit allocation identity")
        rows = pair()
        rows[-1][1]["cycle"] = 8
        self.reject(rows, "duplicate ROB event/slot")

    def test_same_cycle_rob_text_order_does_not_change_identity(self):
        rows = pair()
        rows[-1][1].update(cycle=8, slot=1)
        rows[-2], rows[-1] = rows[-1], rows[-2]
        self.assertEqual(self.run_trace(rows)["rob"]["committed"], 2)

    def test_removed_whole_transaction_cannot_pass_rob_join(self):
        rows = pair()
        rows[6][1].update(iv=0, ca=0)
        del rows[7:9]
        self.reject(rows, "commit without prior legal")

    def test_non_vdot_encoding_cannot_be_certified(self):
        rows = pair()
        rows[2][1]["word"] = rows[-2][1]["word"] = 0x13
        self.reject(rows, "not a VDot instruction")

    def test_reallocated_rob_pointer_is_a_new_transaction(self):
        rows = pair()
        for tag, original in pair()[2:]:
            f = original.copy()
            f["cycle"] += 100
            rows.append((tag, f))
        self.assertEqual(self.run_trace(rows)["rob"]["committed"], 4)

    def test_no_rob_or_fake_cpu_reset(self):
        rows = [x for x in pair() if not x[0].startswith("O1_ROB")]
        self.reject(rows, "matching EXU/ROB")
        rows = pair()
        rows.insert(7, ("O1_EXU_BEGIN", HEADER.copy()))
        self.reject(rows, "busy disagrees")

    def test_exact_schema_and_numeric_bounds(self):
        base = line("O1_EXU", frame(0))
        for damaged in (base + " iv=0", base + " extra=0", base.replace(" vl=8", ""),
                        base.replace(" vl=8", " vl=NaN"), base.replace(" vl=8", " vl=-1"),
                        base.replace(" vl=8", " vl=256"), base.replace(" iv=0", " iv=2"),
                        base.replace("a=0x101010101010101", "a=" + hex(1 << 128))):
            with self.subTest(damaged=damaged), self.assertRaises(TraceError):
                record(damaged)
        padded = reformat_padding(base)
        self.assertEqual(record(base), record(padded))

    def test_wrong_profile_mode_and_prefix(self):
        for key, value in (("schema", 2), ("mode", 0), ("robsize", 64), ("hart", 1), ("cycle", 1)):
            rows = pair()
            rows[0][1][key] = value
            self.reject(rows, "schema/mode|unsupported profile")
        lines = encoded(pair())
        lines[4] = "damaged " + lines[4]
        with self.assertRaisesRegex(TraceError, "damaged trace prefix"):
            audit(lines, 2, "fullcore")

    def test_rob_wrap_and_self(self):
        self.assertTrue(killed((1, 0), (0, 47, 0), 48))
        self.assertFalse(killed((0, 47), (1, 0, 0), 48))
        self.assertTrue(killed((0, 1), (0, 1, 1), 48))
        self.assertFalse(killed((0, 1), (0, 1, 0), 48))
        with self.assertRaisesRegex(TraceError, "ambiguous"):
            killed((1, 0), (0, 0, 0), 48)

    def test_parent_requires_seven_epochs_and_independent_ledger(self):
        rows = [("O1_EXU_BEGIN", HEADER.copy())]
        for _ in range(6):
            rows.append(("O1_EXU", frame(0, iv=1, ca=1, irv=1, id=11)))
            rows.append(("O1_EXU_BEGIN", HEADER.copy()))
        rows.extend(x for x in pair() if x[0] == "O1_EXU")
        text = encoded(rows)
        good = "VFEX4_PARENT_PASS mode=2 accepted=8 responses=2 canceled=0 reset=6 overlap=1 stalls=0"
        self.assertEqual(audit(text + [good], 2, "parent")["epochs"], 7)
        for summary in ([], [good, good], [good.replace("accepted=8", "accepted=7")]):
            with self.assertRaisesRegex(TraceError, r"C\+\+ ledger"):
                audit(text + summary, 2, "parent")


def reformat_padding(text):
    return text.replace("=", "=    ")


if __name__ == "__main__":
    unittest.main()
