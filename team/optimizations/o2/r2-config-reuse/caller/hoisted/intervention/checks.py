"""Bounded rejection controls for the new table binding and raw experiment."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import shutil
import struct
import tempfile


def run(e, auditor, build=None, campaign=None):
    results = []

    def positive(name, action):
        action()
        results.append(dict(name=name, outcome="PASS"))

    def rejected(name, action):
        try:
            action()
        except (ValueError, AssertionError, RuntimeError) as exc:
            results.append(dict(name=name, outcome="EXPECTED_REJECTION", error=str(exc)))
        else:
            raise AssertionError("accepted bad control: " + name)

    targets = [dict(trial=t, arm=a, cycles=100, call_to_leaf_retirement_gap=0,
                    call_redirect=dict(status="NO_CONTINUOUS_ORIGIN")) for t, a in enumerate(auditor.ORDER)]

    def decision(rows, wanted):
        assert auditor.summarize(rows)["decision"] == wanted

    positive("no_association", lambda: decision(targets, "NOT_REPRODUCED_IN_THIS_PLAN"))
    full = copy.deepcopy(targets)
    for row in full:
        if row["arm"] == 0:
            row["call_to_leaf_retirement_gap"] = 9
            row["call_redirect"]["status"] = "UNIQUE_CONTINUOUS_ORIGIN"
    positive("all_blocks_association", lambda: decision(full, "REPRODUCED_PREDECESSOR_ASSOCIATION"))
    reverse = copy.deepcopy(targets)
    for row in reverse:
        if row["arm"] == 1:
            row["call_to_leaf_retirement_gap"] = 9
            row["call_redirect"]["status"] = "UNIQUE_CONTINUOUS_ORIGIN"
    positive("opposite_direction_not_old_pattern", lambda: decision(reverse, "NOT_REPRODUCED_IN_THIS_PLAN"))
    partial = copy.deepcopy(targets)
    partial[4] = copy.deepcopy(full[4])
    positive("partial_blocks_mixed", lambda: decision(partial, "MIXED_PREDECESSOR_ASSOCIATION"))
    ambiguous = copy.deepcopy(full)
    ambiguous[5]["call_redirect"]["status"] = "AMBIGUOUS_ORIGINS"
    positive("ambiguous_not_forced", lambda: decision(ambiguous, "INCONCLUSIVE_AMBIGUOUS_ORIGIN"))
    rejected("missing_target", lambda: auditor.summarize(targets[:-1]))
    wrong = copy.deepcopy(targets)
    wrong[4]["arm"] = 1
    rejected("wrong_arm_order", lambda: auditor.summarize(wrong))

    if build is not None:
        positive("real_build", lambda: e.verification(e.ROOT, build))
        with tempfile.TemporaryDirectory(prefix="context-rejections-") as temporary:
            clone = Path(temporary) / "build"
            shutil.copytree(build, clone)
            baseline = {name: (clone / name).read_bytes() for name in
                        ("vdot-perf.elf", "vdot-perf.bin", "build.json", "source/manifest.json")}

            def restore():
                for name, raw in baseline.items():
                    (clone / name).write_bytes(raw)

            manifest = json.loads(baseline["source/manifest.json"])
            manifest["plan"][0]["index"] = 2
            e.g.save(clone / "source/manifest.json", manifest)
            rejected("changed_manifest_order", lambda: e.verification(e.ROOT, clone))
            restore()

            def changed_table(symbol, replacement):
                restore()
                raw = bytearray(baseline["vdot-perf.elf"])
                parsed = e.g.ELF(bytes(raw))
                address, size = parsed.symbols[symbol][:2]
                assert len(replacement) == size
                phoff, = struct.unpack_from("<Q", raw, 32)
                phsize, phnum = struct.unpack_from("<HH", raw, 54)
                offsets = []
                for i in range(phnum):
                    kind, _, offset, vaddr, _, filesz, _, _ = struct.unpack_from("<IIQQQQQQ", raw, phoff + i * phsize)
                    if kind == 1 and vaddr <= address and address + size <= vaddr + filesz:
                        offsets.append(offset + address - vaddr)
                assert len(offsets) == 1
                raw[offsets[0]:offsets[0] + size] = replacement
                (clone / "vdot-perf.elf").write_bytes(raw)
                (clone / "vdot-perf.bin").write_bytes(e.g.ELF(bytes(raw)).binary())
                receipt = json.loads(baseline["build.json"])
                for name in ("vdot-perf.elf", "vdot-perf.bin"):
                    receipt["artifacts"][name] = e.g.sha(clone / name)
                e.g.save(clone / "build.json", receipt)

            elf = e.g.ELF(baseline["vdot-perf.elf"])
            order = list(auditor.ORDER)
            order[0], order[1] = order[1], order[0]
            changed_table("context_order", struct.pack("<20I", *order))
            rejected("rehashed_elf_order", lambda: e.verification(e.ROOT, clone))
            same = elf.symbols["r4_gemv_8x32_reuse_rvv"][0]
            changed_table("context_predecessors", struct.pack("<2Q", same, same))
            rejected("rehashed_duplicate_predecessor", lambda: e.verification(e.ROOT, clone))
            changed_table("context_target", struct.pack("<Q", same))
            rejected("rehashed_wrong_target", lambda: e.verification(e.ROOT, clone))
            restore()

    if campaign is not None:
        assert build is not None
        frozen = {str(path): e.g.sha(path) for path in (campaign / "runs/negative").glob("*.json")}
        positive("real_raw_audit", lambda: auditor.audit(e, e.ROOT, build, campaign))
        assert frozen == {str(path): e.g.sha(path) for path in (campaign / "runs/negative").glob("*.json")}
        results.append(dict(name="negative_originals_unchanged", outcome="PASS"))
        normal = campaign / "runs/recovery"
        receipt = e.read(normal / "result.json")
        with tempfile.TemporaryDirectory(prefix="context-raw-rejections-") as temporary:
            clone = Path(temporary) / "normal"
            clone.mkdir()
            original = {name: (normal / name).read_text() for name in ("stdout.log", "stderr.log")}

            observer = e.g.load("intervention_test_uart", e.ROOT / "team/optimizations/o2/fullcore/analyze.py")
            events = "|".join(sorted(observer.FIELDS, key=len, reverse=True))
            noise = r"(?:O2_(?:" + events + r")[ \t]+[^\n]*\n|T13_(?:COUNTER_ENQUEUE|CSR_SAMPLE|RETIRE)[ \t]+[^\n]*\n)*"

            def raw_control(name, old, new):
                changed = [i for i, (a, b) in enumerate(zip(old, new)) if a != b]
                assert len(old) == len(new) and len(changed) == 1
                position = changed[0]
                pattern = noise.join(("(?P<edit>" + re.escape(char) + ")") if i == position else re.escape(char)
                                     for i, char in enumerate(old))
                matches = [(filename, match) for filename, text in original.items() for match in re.finditer(pattern, text)]
                assert len(matches) == 1, "interrupted raw UART control must match once"
                stream, match = matches[0]
                offset = match.start("edit")
                for filename, text in original.items():
                    (clone / filename).write_text(text[:offset] + new[position] + text[offset + 1:] if filename == stream else text)
                rejected(name, lambda: auditor.normal(e, e.ROOT, build, clone, receipt))

            # UART may reside in stderr or stdout. Find its owning raw stream;
            # no normalization or rewritten baseline is used for the real audit.
            for old, new, name in (
                ("CI_CONTROLS detected=6 expected=6 restored=0", "CI_CONTROLS detected=5 expected=6 restored=0", "missing_judge_control"),
                ("CI_END windows=40 failures=0", "CI_END windows=40 failures=1", "bad_judge_summary"),
            ):
                raw_control(name, old, new)
            bad_receipt = dict(receipt, exit_code=1)
            rejected("nonzero_process", lambda: auditor.normal(e, e.ROOT, build, normal, bad_receipt))
            bad_receipt = dict(receipt, timed_out=True)
            rejected("timed_out_process", lambda: auditor.normal(e, e.ROOT, build, normal, bad_receipt))

        with tempfile.TemporaryDirectory(prefix="context-receipt-rejections-") as temporary:
            clone = Path(temporary) / "campaign"
            shutil.copytree(campaign, clone)
            completed = e.read(clone / "completed-runs.json")
            cached = e.read(clone / "results.json")
            changed = copy.deepcopy(completed[1])
            changed["command"][-1] = "--seed=2"
            completed[1] = changed
            cached["records"][1] = changed
            e.g.save(clone / "runs/recovery/result.json", changed)
            e.g.save(clone / "completed-runs.json", completed)
            e.g.save(clone / "results.json", cached)
            rejected("coherent_receipts_wrong_seed", lambda: auditor.audit(e, e.ROOT, build, clone))
            for name in ("runs/recovery/result.json", "completed-runs.json", "results.json"):
                shutil.copyfile(campaign / name, clone / name)
            observation = e.read(clone / "runs/negative/observation.json")
            observation["intervention_unobserved_extra_field"] = True
            e.g.save(clone / "runs/negative/observation.json", observation)
            rejected("changed_negative_observation", lambda: auditor.audit(e, e.ROOT, build, clone))

    return dict(status="INTERVENTION_CHECKS_PASS", checks=results, count=len(results),
                new_emu_runs=0, real_build_checked=build is not None, real_raw_checked=campaign is not None)
