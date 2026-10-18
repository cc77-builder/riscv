#!/usr/bin/env python3
"""Strict O1 schema-1 observer audit; never a replacement for CPU DiffTest.

EXU frames are pre-edge samples on the ungated parent clock. Resolve the old
owner before accepting the new one. ROB redirects reach EXU exactly one cycle
later (CtrlBlock.s2_s4_redirect). No inferred clock alignment is permitted.
"""
import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re


class TraceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise TraceError(message)


HEADER = set("schema cycle mode robsize pdestbits hart".split())
FRAME = set("cycle busy iv ir kind irf irv id iwv iw0 ca cv a b vl vill vm sew lmul start op ov ready orf orv od owv ow0 exc data vec v0 ff fv frf frv self kill".split())
ROB = set("cycle slot rf rv dest pc word".split())
REDIRECT = set("cycle rf rv self".split())
SCHEMAS = {"O1_EXU_BEGIN": HEADER, "O1_ROB_BEGIN": HEADER,
           "O1_EXU": FRAME, "O1_ROB_ENQ": ROB, "O1_ROB_COMMIT": ROB,
           "O1_ROB_REDIRECT": REDIRECT}
HEX = {"a", "b", "exc", "data", "vec", "v0", "pc", "word"}
BITS = set("busy iv ir irf iwv iw0 vill vm ov ready orf owv ow0 fv frf self kill rf".split())
SUMMARY = re.compile(r"VFEX4_PARENT_PASS mode=(\d+) accepted=(\d+) responses=(\d+) canceled=(\d+) reset=(\d+) overlap=(\d+) stalls=(\d+)")


def record(line):
    # Chisel decimal printf pads with spaces. Accept that padding, not missing,
    # duplicate, renamed or unrecognized fields, signed values, NaNs or junk.
    require(len(line) <= 4096, "oversized observer record")
    tokens = re.sub(r"=\s+", "=", line.strip()).split()
    tag = tokens[0]
    require(tag in SCHEMAS, f"unknown record {tag}")
    result = {}
    for token in tokens[1:]:
        pair = token.split("=")
        require(len(pair) == 2, f"malformed field {token}")
        key, value = pair
        require(key not in result and key in SCHEMAS[tag], f"duplicate/unknown field {key}")
        pattern = r"0x[0-9a-fA-F]+" if key in HEX else r"[0-9]+"
        require(re.fullmatch(pattern, value) is not None, f"invalid number {key}")
        result[key] = int(value, 16 if key in HEX else 10)
    require(result.keys() == SCHEMAS[tag], f"incomplete {tag}")
    if tag == "O1_ROB_ENQ":
        require(result["slot"] < 6, "invalid MinimalConfig rename slot")
    require(result["cycle"] < 2**64, "cycle overflow")
    for key in BITS & result.keys():
        require(result[key] in (0, 1), f"not a bit: {key}")
    for key in {"a", "b", "data", "vec", "v0"} & result.keys():
        require(result[key] < 2**128, f"128-bit overflow: {key}")
    for key, bound in {"pc": 2**64, "word": 2**32, "exc": 2**24,
                       "slot": 8, "kind": 4, "ca": 8, "cv": 8,
                       "vl": 256, "sew": 4, "lmul": 8, "start": 256,
                       "op": 512, "ff": 32}.items():
        if key in result:
            require(result[key] < bound, f"out of range: {key}")
    return tag, result


def killed(owner, redirect, size):
    # CircularQueuePtr comparison with an unambiguous live ROB window.
    age = (owner[0] * size + owner[1] - redirect[0] * size - redirect[1]) % (2 * size)
    require(age != size, "ambiguous ROB age")
    return bool(redirect[2]) if age == 0 else age < size


def dot_result(f):
    illegal = bool(f["vill"] or not f["vm"] or f["sew"] or f["lmul"] or
                   f["start"] or f["vl"] != 8 or f["op"])
    def signed_byte(value, lane):
        return ((value >> (lane * 8) & 255) ^ 128) - 128
    value = sum(signed_byte(f["a"], i) * signed_byte(f["b"], i) for i in range(8))
    return illegal, 0 if illegal else value & 0xffffffff


@dataclass
class Transaction:
    epoch: int
    cycle: int
    kind: int
    rob: tuple
    dest: int
    wens: tuple
    illegal: bool
    value: int
    end: int | None = None
    outcome: str | None = None


class ExuAudit:
    def __init__(self, mode):
        self.mode = mode
        self.header = None
        self.epochs = 0
        self.pending = None
        self.last = None
        self.stalled = None
        self.transactions = []
        self.flushes = []
        self.counts = Counter()

    def begin(self, h):
        require(h["schema"] == 1 and h["cycle"] == 0 and h["mode"] == self.mode,
                "schema/mode/start cycle mismatch")
        require(h["hart"] == 0 and h["robsize"] == 48 and h["pdestbits"] == 8,
                "unsupported profile (schema 1 audit supports single-core MinimalConfig)")
        if self.header is not None:
            require(h == self.header and self.last is not None, "changed/empty reset epoch")
        if self.pending:
            self.pending.outcome = "reset"
            self.counts["reset"] += 1
        self.header = h
        self.epochs += 1
        self.pending = self.last = self.stalled = None

    def frame(self, f):
        require(self.header is not None, "EXU frame before header")
        c = f["cycle"]
        if self.last is not None:
            require(c > self.last, "duplicate/reversed EXU cycle")
            require(not self.pending or c == self.last + 1, "missing busy EXU cycle")
        size = self.header["robsize"]
        for key, valid in (("irv", "iv"), ("orv", "ov"), ("frv", "fv")):
            # Invalid-channel payload is unspecified, but still has a physical
            # six-bit width. Only a valid channel carries a live ROB index.
            require(f[key] < 64 and (not f[valid] or f[key] < size), f"invalid ROB index: {key}")
        require(f["id"] < 256 and f["od"] < 256, "invalid physical destination")
        require(bool(f["busy"]) == bool(self.pending), "busy disagrees with transaction ledger")
        old = self.pending
        kill = bool(old and f["fv"] and killed(old.rob, (f["frf"], f["frv"], f["self"]), size))
        require(f["kill"] == int(kill), "kill disagrees with ROB age")
        if f["fv"]:
            self.flushes.append((self.epochs, c, f["frf"], f["frv"], f["self"]))
        accept = bool(f["iv"] and f["ir"])
        complete = bool(f["ov"] and f["ready"] and not kill)
        require(not f["fv"] or not f["ir"], "ready asserted during flush")
        if old and f["ir"]:
            require(self.mode == 2 and complete and old.kind == f["kind"] == 0 and not f["fv"],
                    "ready advertised without a legal handoff")
        if f["iv"] and not f["ir"]:
            self.counts["waits"] += 1
        require(f["ca"] == (1 << f["kind"] if accept else 0), "child/parent acceptance mismatch")
        require(f["cv"] == (1 << old.kind if f["ov"] and old else 0), "child/parent response mismatch")
        require(not f["ov"] or old is not None, "unsolicited response")
        if old and old.kind == 0:
            expected = not kill and c >= old.cycle + (3 if self.mode == 0 else 2)
            require(bool(f["ov"]) == expected, "VDot response latency/withdrawal/cancel mismatch")
        snapshot = tuple(f[k] for k in "orf orv od owv ow0 exc data vec v0 ff".split())
        if self.stalled is not None and not kill:
            require(f["ov"] and snapshot == self.stalled, "response changed under backpressure")
        if f["ov"]:
            require((f["orf"], f["orv"]) == old.rob and f["od"] == old.dest, "old response identity mismatch")
            require(f["data"] == f["vec"] == f["v0"], "shared/vector/v0 writeback mismatch")
            if old.kind == 0:
                require(f["data"] == old.value and f["exc"] == (4 if old.illegal else 0)
                        and f["ff"] == 0, "independent VDot result/exception/flags mismatch")
                wens = (0, 0) if old.illegal else old.wens
                require((f["owv"], f["ow0"]) == wens, "old write enables mismatch")
            if not f["ready"]:
                self.counts["stalls"] += 1
                if old.kind == 0:
                    self.counts["vdot_stalls"] += 1
        if accept and old:
            require(self.mode == 2 and complete and old.kind == f["kind"] == 0 and not f["fv"],
                    "illegal shared-FU overlap")
            self.counts["overlap"] += 1
        require(not (self.mode == 2 and f["fv"] and accept), "O1 acceptance during flush")
        if kill or complete:
            old.end = c
            old.outcome = "canceled" if kill else "responses"
            self.counts[old.outcome] += 1
            if kill and old.kind == 0:
                self.counts["vdot_canceled"] += 1
            self.pending = None
        self.stalled = snapshot if f["ov"] and not f["ready"] and not kill else None
        if accept:
            require(f["kind"] < 3 and self.pending is None, "invalid acceptance")
            require(f["iwv"] + f["iw0"] == 1, "invalid destination class")
            illegal, value = dot_result(f) if f["kind"] == 0 else (False, 0)
            new = Transaction(self.epochs, c, f["kind"], (f["irf"], f["irv"]),
                              f["id"], (f["iwv"], f["iw0"]), illegal, value)
            self.pending = new
            self.transactions.append(new)
            self.counts["accepted"] += 1
        self.last = c
        self.counts["frames"] += 1

    def finish(self):
        require(self.header is not None and self.last is not None, "empty EXU trace")
        require(self.pending is None, "unfinished EXU transaction at EOF")
        require(any(t.kind == 0 for t in self.transactions), "no VDot transactions")
        require(self.counts["accepted"] == sum(self.counts[k] for k in ("responses", "canceled", "reset")),
                "transaction conservation failure")


def join_rob(exu, headers, events):
    require(exu.epochs == 1 and headers == [exu.header], "full-core requires one matching EXU/ROB reset epoch")
    require(events, "missing ROB observations")
    redirects = [(1, f["cycle"] + 1, f["rf"], f["rv"], f["self"])
                 for tag, f in events if tag == "O1_ROB_REDIRECT"]
    require(redirects == exu.flushes, "ROB->EXU redirect must match at exactly +1 cycle")
    by_cycle = defaultdict(list)
    for tag, f in events:
        require(f["rv"] < 48, "invalid ROB index")
        if "dest" in f:
            require(f["dest"] < 256, "invalid ROB destination")
        by_cycle[f["cycle"]].append((tag, f))
    for t in exu.transactions:
        if t.kind == 0:
            by_cycle[t.cycle].append(("ACCEPT", t))
            require(t.end is not None, "full-core reset/truncated VDot")
    live, canceled, linked = {}, {}, set()
    counts = Counter()
    last_commit_flag = None
    # A canceled allocation remains matchable for one cycle, because an EXU
    # request can be accepted before the registered flush arrives. Reuse of the
    # same circular pointer later creates a fresh allocation, not a shared ID.
    for cycle in sorted(by_cycle):
        group = by_cycle[cycle]
        seen = set()
        for tag, f in group:
            if tag == "ACCEPT":
                continue
            identity = (tag, f.get("slot", 0))
            require(identity not in seen, "duplicate ROB event/slot")
            seen.add(identity)
        redirect = [f for tag, f in group if tag == "O1_ROB_REDIRECT"]
        require(not redirect or not any(tag in ("O1_ROB_ENQ", "O1_ROB_COMMIT") for tag, _ in group),
                "ROB allocation/commit during redirect")
        for tag, f in sorted((x for x in group if x[0] == "O1_ROB_COMMIT"), key=lambda x: x[1]["slot"]):
            key = (f["rf"], f["rv"])
            require(key in live, "commit without live allocation")
            enq, txn = live.pop(key)
            require(txn is not None and txn.outcome == "responses" and txn.end < cycle and not txn.illegal,
                    "commit without prior legal VDot response")
            require(all(f[k] == enq[k] for k in ("dest", "pc", "word")), "commit allocation identity mismatch")
            counts["committed"] += 1
            if last_commit_flag is not None and key[0] != last_commit_flag:
                counts["rob_wraps"] += 1
            last_commit_flag = key[0]
        for f in redirect:
            ptr = (f["rf"], f["rv"], f["self"])
            for key in list(live):
                if killed(key, ptr, 48):
                    enq, txn = live.pop(key)
                    canceled[key] = (cycle, enq, txn)
                    counts["squashed"] += 1
                    if txn is not None:
                        counts["accepted_squashed"] += 1
        for tag, f in sorted((x for x in group if x[0] == "O1_ROB_ENQ"), key=lambda x: x[1]["slot"]):
            key = (f["rf"], f["rv"])
            require(f["word"] & 0xfe00707f == 0x0200000b, "ROB allocation is not a VDot instruction")
            require(key not in live, "duplicate live ROB allocation")
            live[key] = (f, None)
            counts["allocated"] += 1
        for tag, t in group:
            if tag != "ACCEPT":
                continue
            key = t.rob
            if key in live:
                enq, prior = live[key]
                live[key] = (enq, t)
            else:
                require(key in canceled and canceled[key][0] == cycle,
                        "acceptance without live/recently redirected allocation")
                canceled_at, enq, prior = canceled[key]
                canceled[key] = (canceled_at, enq, t)
                counts["accepted_squashed"] += 1
            require(prior is None and enq["cycle"] < t.cycle and enq["dest"] == t.dest,
                    "duplicate or mismatched ROB acceptance")
            linked.add(id(t))
        # Check delayed physical cancellation, including responses that escaped
        # on the ROB redirect cycle but were architecturally squashed.
        for key, (at, enq, t) in list(canceled.items()):
            if at <= cycle and t is not None:
                require((t.outcome == "canceled" and t.end == at + 1) or
                        (t.outcome == "responses" and t.end <= at),
                        "squashed VDot survived registered redirect")
            if at < cycle:
                del canceled[key]
    require(not live, "unfinished ROB allocations at EOF")
    require(len(linked) == sum(t.kind == 0 for t in exu.transactions), "unlinked VDot execution")
    require(counts["committed"] > 0, "no VDot commits")
    require(counts["allocated"] == counts["committed"] + counts["squashed"], "ROB conservation failure")
    return dict(counts)


def audit(lines, mode, scope):
    require(mode in (0, 1, 2) and scope in ("parent", "fullcore"), "invalid mode/scope")
    exu = ExuAudit(mode)
    rob_headers, rob_events, summaries = [], [], []
    rob_last = None
    summary_seen = False
    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        try:
            if line.startswith("VFEX4_PARENT_PASS"):
                match = SUMMARY.fullmatch(line)
                require(match is not None, "malformed parent summary")
                summaries.append(tuple(map(int, match.groups())))
                summary_seen = True
            if not line.startswith("O1_"):
                require(re.search(r"\bO1_(?:EXU|ROB)", line) is None, "damaged trace prefix")
                continue
            require(not summary_seen, "trace continues after parent completion")
            tag, f = record(line)
            if tag == "O1_EXU_BEGIN":
                exu.begin(f)
            elif tag == "O1_EXU":
                exu.frame(f)
            elif tag == "O1_ROB_BEGIN":
                require(not rob_headers and not rob_events, "duplicate/late ROB header")
                rob_headers.append(f)
            else:
                require(rob_headers, "ROB event before header")
                require(rob_last is None or f["cycle"] >= rob_last, "reversed ROB cycle")
                rob_last = f["cycle"]
                rob_events.append((tag, f))
        except TraceError as error:
            raise TraceError(f"line {number}: {error}") from error
    exu.finish()
    result = {"schema": 1, "scope": scope, "mode": mode, "epochs": exu.epochs,
              **{k: exu.counts[k] for k in ("frames", "accepted", "responses", "canceled", "reset", "overlap", "stalls", "waits", "vdot_stalls", "vdot_canceled")}}
    result["accepted_by_kind"] = {str(k): sum(t.kind == k for t in exu.transactions) for k in range(3)}
    if scope == "parent":
        require(not rob_headers and not rob_events, "ROB trace in parent-only audit")
        require(exu.epochs == 7 and exu.counts["reset"] == 6, "parent reset coverage mismatch")
        expected = (mode,) + tuple(exu.counts[k] for k in ("accepted", "responses", "canceled", "reset", "overlap", "stalls"))
        require(summaries == [expected], "independent C++ ledger disagrees or is missing")
    else:
        require(not summaries, "parent ledger cannot attest a CPU run")
        result["rob"] = join_rob(exu, rob_headers, rob_events)
    result["status"] = "O1_TRACE_PROTOCOL_PASS_ARCHITECTURAL_VALIDATION_SEPARATE"
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("log", type=Path)
    ap.add_argument("--mode", required=True, type=int, choices=(0, 1, 2))
    ap.add_argument("--scope", required=True, choices=("parent", "fullcore"))
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    try:
        # Strict UTF-8, no replacement of corrupted bytes; digest the exact input.
        raw = args.log.read_bytes()
        result = audit(raw.decode("utf-8").splitlines(), args.mode, args.scope)
        result["log_sha256"] = hashlib.sha256(raw).hexdigest()
        code = 0
    except (TraceError, UnicodeError, OSError) as error:
        result = {"status": "O1_TRACE_FAIL", "error": str(error)}
        code = 1
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
