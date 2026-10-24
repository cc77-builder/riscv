"""Cross-image fairness, targeted rejection checks and preregistered decisions.

Read-only on builds/runs. Outputs must be new. No EDA or EMU is launched.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import struct
import tempfile

import screen as s

e, g = s.e, s.g
LABELS = ("b4", "h4", "h0", "h1", "h2", "h3")


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def sections(raw):
    need(raw[:6] == b"\x7fELF\x02\x01", "ELF64 little-endian required")
    start = struct.unpack_from("<Q", raw, 40)[0]
    size, count, strings = struct.unpack_from("<HHH", raw, 58)
    need(size == 64 and start + size * count <= len(raw), "ELF section table bounds")
    rows = [struct.unpack_from("<IIQQQQIIQQ", raw, start + i * size) for i in range(count)]
    names = raw[rows[strings][4]:rows[strings][4] + rows[strings][5]]
    for row in rows:
        if not row[2] & 2:
            continue
        name = names[row[0]:].split(b"\0", 1)[0].decode()
        need(row[1] == 8 or row[4] + row[5] <= len(raw), "ALLOC data bounds")
        yield dict(name=name, type=row[1], flags=row[2], address=row[3], offset=row[4], size=row[5],
                   alignment=row[8], data=b"" if row[1] == 8 else raw[row[4]:row[4] + row[5]])


def normalized(raw, label):
    """Mask only the 4-byte ELF selector and the one allocated contract string."""
    need(label in tuple("h" + str(i) for i in range(5)), "hoisted layout label")
    elf = g.ELF(raw)
    choice = int(label[1])
    s.selected(elf, choice)
    selector, width = elf.symbols["hoisted_rvv_choice"][:2]
    need(width == 4, "selector symbol width")
    original_contract = ("r2-s3-caller-screen-v2-" + label).encode()
    canonical_contract = b"r2-s3-caller-screen-v2-h4"
    need(len(original_contract) == len(canonical_contract), "contract length")
    changed = bytearray(raw)
    spans = []
    selector_found = contract_found = 0
    for row in sections(raw):
        if row["type"] == 8:
            continue
        address, data, offset = row["address"], row["data"], row["offset"]
        if address <= selector and selector + 4 <= address + len(data):
            relative = selector - address
            need(data[relative:relative + 4] == struct.pack("<I", choice), "selector bytes")
            changed[offset + relative:offset + relative + 4] = bytes(4)
            spans.append(dict(kind="selector", address=selector, bytes=4))
            selector_found += 1
        count = data.count(original_contract)
        need(count <= 1, "duplicate contract within ALLOC")
        if count:
            relative = data.index(original_contract)
            changed[offset + relative:offset + relative + len(original_contract)] = canonical_contract
            spans.append(dict(kind="contract", address=address + relative, bytes=len(original_contract)))
            contract_found += 1
    need(selector_found == contract_found == 1, "unique ALLOC selector/contract")
    rows = []
    for row in sections(changed):
        row = dict(row)
        row.pop("offset")
        row["data"] = bytes(row["data"]).hex()
        rows.append(row)
    return dict(entry=struct.unpack_from("<Q", changed, 24)[0], sections=rows), g.ELF(bytes(changed)).binary(), spans


def preflight(root, historical):
    records, valid, manifests, images = {}, {}, {}, {}
    for label in LABELS:
        build = root / ("build-" + label + "-01")
        br = e.read(build / "build.json")
        need(br["accepted"] is True and br["exit_code"] == 0, "incomplete build: " + label)
        for name, pin in br["artifacts"].items():
            need(g.sha(build / name) == pin, "build artifact changed")
        raw = (build / "vdot-perf.elf").read_bytes()
        need(g.ELF(raw).binary() == (build / "vdot-perf.bin").read_bytes(), "ELF/BIN differs")
        records[label] = br
        valid[label] = e.read(build / "elf-validation.json")
        manifests[label] = e.read(build / "source/manifest.json")
        images[label] = raw
    base = records["b4"]
    keys = ("software_files", "toolchain", "external_files", "parent_identity_sha256", "am_home", "am_revision", "source_commit")
    for label in LABELS:
        br, v, m = records[label], valid[label], manifests[label]
        need(all(br[key] == base[key] for key in keys), "cross-build fixed inputs differ")
        need(m["plan"] == manifests["b4"]["plan"] and m["inputs"] == manifests["b4"]["inputs"], "plan/datasets differ")
        need(len(m["plan"]) == 36 and m["expected_dots"] == 672 and len(m["rows"]) == 2,
             "full-only manifest coverage")
        need(v["contract"] == "r2-s3-caller-screen-v2-" + label and v["image_sha256"] == br["artifacts"]["vdot-perf.bin"],
             "build report identity")
        need(m["selected_rvv"] == int(label[1]) and m["caller_variant"] == ("baseline" if label == "b4" else "hoisted"), "manifest selection")
        for name in ("caller.h", "main.c", "demo.c", "timers.S", "gemv.S", "gemv.h", "Makefile", "strong.S"):
            need((root / ("build-" + label + "-01/source") / name).read_bytes() ==
                 (root / "build-b4-01/source" / name).read_bytes(), "non-caller generated source differs: " + name)
        wanted = s.h.BASE_PINS["caller.c"] if label == "b4" else s.DRAFTS["caller.c"]
        need(g.sha(root / ("build-" + label + "-01/source/caller.c")) == wanted, "caller code identity")
        commands = {name: [a.replace(br["build_root"], "<build>") for a in argv]
                    for name, argv in v["actual_c_compilation"].items()}
        baseline_commands = {name: [a.replace(base["build_root"], "<build>") for a in argv]
                             for name, argv in valid["b4"]["actual_c_compilation"].items()}
        need(commands == baseline_commands, "compiler command changed")
    canonical, binary, _ = normalized(images["h4"], "h4")
    rows = {}
    for label in ("h0", "h1", "h2", "h3", "h4"):
        shape, image, spans = normalized(images[label], label)
        need(shape == canonical and image == binary, "ALLOC/BIN differs outside selector and contract")
        rows[label] = dict(image_sha256=records[label]["artifacts"]["vdot-perf.bin"], allowed_spans=spans,
                           normalized_binary_sha256=sha(image), vdot_path_sha256=valid[label]["paths"]["0"]["path_sha256"])
        need(rows[label]["vdot_path_sha256"] == valid["h4"]["paths"]["0"]["path_sha256"], "common vdot path differs")
    prior = None
    if historical:
        old = e.read(historical / "build.json")
        for key in ("toolchain", "external_files", "parent_identity_sha256", "am_home", "am_revision"):
            need(old[key] == base[key], "historical fixed inputs changed: " + key)
        need(old["artifacts"]["gemv-reference.o"] == base["artifacts"]["gemv-reference.o"], "historical reference object changed")
        prior = dict(build_record_sha256=g.sha(historical / "build.json"), plan_reused=False,
                     role="identity/history only; matched new b4 is the performance baseline")
    return dict(status="HOISTED_PREFLIGHT_PASS", build_records={k:g.sha(root / ("build-" + k + "-01/build.json")) for k in LABELS},
                images=rows, complete_alloc_including_bss=True, full_bin_comparison=True,
                fixed_input_keys=list(keys), historical_reference=prior, new_emu_runs=0)


def rejections(root):
    s.configure("hoisted", 4)
    s.h.install()
    build = root / "build-h4-01"
    tester = g.load("screen_mutations", e.HERE / "selftest.py")
    parent_result = tester.run(build)
    original = e.read(build / "build.json")
    raw = (build / "vdot-perf.elf").read_bytes()
    elf = g.ELF(raw)
    mutations = (
        ("selector", elf.symbols["hoisted_rvv_choice"][0], 0, "screen selector identity"),
        ("unused-table-entry", elf.symbols["hoisted_rvv_entries"][0], elf.symbols[s.RVV[4][0]][0] & 0xffffffff, "screen complete RVV table"),
        ("unused-extra-rvv", elf.symbols[s.RVV[3][0]][0], 0x00000013, "screen qualified RVV leaf changed"),
    )
    results = []
    with tempfile.TemporaryDirectory(prefix="hoisted-binding-rejections-") as temporary:
        copy = Path(temporary) / "build"
        shutil.copytree(build, copy)
        for name, address, word, wanted in mutations:
            modified = tester.patch_word(raw, address, word)
            (copy / "vdot-perf.elf").write_bytes(modified)
            (copy / "vdot-perf.bin").write_bytes(g.ELF(modified).binary())
            receipt = deepcopy(original)
            for artifact in ("vdot-perf.elf", "vdot-perf.bin"):
                receipt["artifacts"][artifact] = g.sha(copy / artifact)
            g.save(copy / "build.json", receipt)
            try:
                e.verification(e.ROOT, copy)
            except ValueError as exc:
                need(wanted in str(exc), "wrong rejection: " + str(exc))
                results.append(dict(name=name, status="EXPECTED_REJECTION", gate=str(exc)))
            else:
                raise ValueError("mutation accepted: " + name)
    shape, binary, _ = normalized(raw, "h4")
    modified = tester.patch_word(raw, elf.symbols["caller_full"][0], 0x00000013)
    bad_shape, bad_binary, _ = normalized(modified, "h4")
    need(shape != bad_shape and binary != bad_binary, "layout mask swallowed caller mutation")
    results.append(dict(name="unapproved-alloc-code-byte", status="EXPECTED_REJECTION", gate="outside precise layout whitelist"))
    return dict(status="HOISTED_BINDING_REJECTIONS_PASS", parent_checks=parent_result,
                cases=results, rejected=parent_result["rejected"] + len(results), new_emu_runs=0)


def stats(root, label):
    run = root / ("run-" + label + "-01")
    state = e.read(run / "state.json")
    result = e.read(run / "results.json")
    v = result["validation"]
    need(state["status"] == "CALLER_CAMPAIGN_PASS" and state["new_emu_runs"] == 3 and
         state["active_pid"] is None and v["windows"] == 36 and v["formal_windows"] == 24 and
         v["committed_vdot"] == 672 and v["contract"] == "r2-s3-caller-screen-v2-" + label, "campaign incomplete")
    need(v == e.read(run / "runs/recovery/validation.json") == e.read(run / "runs/replay/validation.json"), "replay changed")
    need(len(v["summary"]) == 1 and v["summary"][0]["scope"] == "full", "non-full summary")
    summary = v["summary"][0]
    for method in ("vdot", "rvv"):
        group = summary[method]
        values = group["by_dataset"]
        need(group["samples"] == 12 and [x["dataset"] for x in values] == [0, 1, 2] and
             all(len(x["cycles"]) == 4 and all(type(c) is int and c > 0 for c in x["cycles"]) for x in values), "formal sample coverage")
        need(group["total"] == sum(sum(x["cycles"]) for x in values), "sample total differs")
    return summary


def stage1(root):
    baseline, candidate = stats(root, "b4"), stats(root, "h4")
    rows = []
    for method in ("vdot", "rvv"):
        b, c = baseline[method], candidate[method]
        by_dataset = [dict(dataset=d, baseline=sum(b["by_dataset"][d]["cycles"]), candidate=sum(c["by_dataset"][d]["cycles"])) for d in range(3)]
        ok = 100 * c["total"] <= 95 * b["total"] and all(100 * row["candidate"] <= 101 * row["baseline"] for row in by_dataset)
        rows.append(dict(method=method, baseline_total=b["total"], candidate_total=c["total"],
                         cycle_reduction=1 - c["total"] / b["total"], by_dataset=by_dataset, passed=ok))
    passed = all(row["passed"] for row in rows)
    return dict(status="HOISTED_STAGE1_COMPLETE", decision="CONTINUE_RVV_SCREEN" if passed else "STOP_SCREEN", comparisons=rows)


def selection(root):
    initial = stage1(root)
    need(initial["decision"] == "CONTINUE_RVV_SCREEN", "stage1 did not qualify")
    values = {i: stats(root, "h" + str(i)) for i in range(5)}
    winner = min(values, key=lambda i: (values[i]["rvv"]["total"], i != 4, i))
    anchors = []
    for d in range(3):
        totals = [sum(values[i]["vdot"]["by_dataset"][d]["cycles"]) for i in range(5)]
        anchors.append(dict(dataset=d, totals=totals, maximum_ratio=max(totals) / min(totals), passed=100 * max(totals) <= 101 * min(totals)))
    winner_rows = values[winner]
    vdot_wins = all(1000 * sum(winner_rows["vdot"]["by_dataset"][d]["cycles"]) <=
                    995 * sum(winner_rows["rvv"]["by_dataset"][d]["cycles"]) for d in range(3))
    anchors_pass = all(row["passed"] for row in anchors)
    method = ("vdot" if vdot_wins else "rvv") if anchors_pass else None
    return dict(status="HOISTED_SCREEN_COMPLETE", decision="QUALIFIED_OPTIONAL_CALLER" if anchors_pass else "HOLD_CONTEXT_VARIATION",
                stage1=initial, rvv_winner_index=winner, rvv_winner_symbol=s.RVV[winner][0],
                selected_method=method, anchors=anchors, results=values,
                scope="five byte-distinct qualified RVV classes, 8x32, three fixed datasets, full-only contract",
                stable_default_changed=False, hardware_changed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("preflight", "rejections", "stage1", "selection"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--historical-build", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    need(not args.output.exists(), "output must be new")
    result = preflight(args.root, args.historical_build) if args.action == "preflight" else globals()[args.action](args.root)
    result.update(checker_sha256=g.sha(__file__))
    g.save(args.output, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
