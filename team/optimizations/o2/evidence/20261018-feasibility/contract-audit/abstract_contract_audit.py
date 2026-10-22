#!/usr/bin/env python3
"""Abstract, finite Boolean check of O2 contract; not an RTL simulation."""
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
inputs = ["team/optimizations/o2/CONTRACT.md", "team/optimizations/o2/INTERFACE_REVIEW.md"]
checks = 0
for pv, rv, reset, flush, rawkp, rawkr, ready, iv, allow in itertools.product((False, True), repeat=9):
    # Flush predicates cannot kill without a redirect. When invalid, raw predicates
    # are don't-cares; these redundant rows are counted explicitly, not deduplicated.
    if not flush and (rawkp or rawkr):
        continue
    p = "P-old" if pv else None
    r = "R-old" if rv else None
    kp = pv and rawkp
    kr = rv and rawkr
    lp = pv and not kp and not reset
    lr = rv and not kr and not reset
    of = lr and ready
    rr = not lr or ready
    move = lp and rr
    pr = not lp or rr
    ir = pr and allow and not flush and not reset
    inf = iv and ir
    nr_v = (lr and not of) or move
    np_v = (lp and not move) or inf
    nr = p if move else (r if lr and not of else None)
    np = "NEW" if inf else (p if lp and not move else None)
    assert bool(nr) == nr_v and bool(np) == np_v
    assert not (move and lr and not of)
    assert not (inf and lp and not move)
    # Contract says RESET has highest priority: drops and kills must be disjoint.
    kills = 0 if reset else int(kp) + int(kr)
    drops = int(pv) + int(rv) if reset else 0
    assert int(pv) + int(rv) + int(inf) == int(of) + kills + drops + int(nr_v) + int(np_v)
    prior = [x for x in (r, p) if x is not None]
    removed = set()
    if reset:
        removed = set(prior)
    else:
        if kp:
            removed.add(p)
        if kr or of:
            removed.add(r)
    expected = [x for x in prior if x not in removed] + (["NEW"] if inf else [])
    assert [x for x in (nr, np) if x is not None] == expected
    if lr and not ready:
        assert nr == r
    if reset:
        assert not any((nr_v, np_v, of, inf))
    if flush:
        assert not inf
    checks += 1

# Four uninterrupted inputs, always-ready output: earliest response is E2.
p = r = None
timeline = []
for edge in range(6):
    response = r
    move = p
    incoming = edge if edge < 4 else None
    r, p = move, incoming
    timeline.append({"edge": edge, "accepted": incoming, "moved": move, "response": response})
assert [x["response"] for x in timeline] == [None, None, 0, 1, 2, 3]
assert all(x["edge"] - x["response"] == 2 for x in timeline if x["response"] is not None)
result = {
    "status": "ABSTRACT_O2_TRANSITION_EXHAUSTIVE_PASS",
    "review_date": "2026-10-19",
    "combination_rows": checks,
    "raw_boolean_combinations": 512,
    "excluded_rows": 192,
    "filter": "Exclude non-redirect rows with asserted raw kill predicates; invalid-slot predicate don't-cares remain as redundant rows.",
    "checks": ["identity conservation", "no overwrite", "FIFO survivor order", "stalled R identity stable", "reset drops disjoint from kills", "no flush/reset input handshakes"],
    "sustained_input_timeline": timeline,
    "inputs_sha256": {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in inputs},
    "reviewer": "Codex subagent o2_final_contract_audit",
    "human_ack": False,
    "scope": "Boolean state equations and four-request timeline only; no RTL, ClockGate, real RobPtr.needFlush, DIV, parent handshake wiring, arithmetic or whole-core execution verified.",
    "reset_counting_assumption": "RESET priority from prose is applied to event accounting: effective kill = raw kill AND NOT reset.",
}
print(json.dumps(result, ensure_ascii=False, indent=2))
