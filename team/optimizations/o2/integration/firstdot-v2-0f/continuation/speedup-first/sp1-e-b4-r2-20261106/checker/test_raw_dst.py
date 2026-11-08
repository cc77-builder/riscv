"""B4-R2 finite delta controls using immutable original actual failure logs."""
from pathlib import Path
import hashlib, importlib.util, json, re
HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("b4_r2_case_adapter", str(HERE.parent / "o2-control/adapter.py"))
a = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(a)
OLD = HERE.parent.parent / "sp1-e-b4-calibration-host-20261106"
RAW = OLD / "cases-r1/o2-control/target-01/01-bit100"

def actual_text():
    return (RAW / "stdout.log").read_text() + (RAW / "stderr.log").read_text()

def once(text, old, new):
    assert text.count(old) == 1, repr(old)
    return text.replace(old, new, 1)

def ring_row(text, slot):
    found = [line for line in text.splitlines() if line.startswith(f"[{slot:02d}] commit ")]
    assert len(found) == 1
    return found[0]

def controls():
    text = actual_text()
    historical = ring_row(text, 6)
    current = ring_row(text, 12)
    need = a.need
    def invoke(raw, expected_group=True):
        result = a.negative(raw, "o2-control", "candidate", a.CONTRACT["runtime"]["negative_reference"]["path"],
                            1, "b4-r2-host-original-failure", "HISTORICAL_LOG")
        need(result["status"] == "B3_BIT100_LOG_PASS" and result["target_run_qualified"] is False, "host-only status")
        need(result["raw_sha256"] == hashlib.sha256(raw.encode()).hexdigest(), "unchanged full raw input identity")
        g = result["fault"]["current_group"]
        need([row["slot"] for row in g["instructions"]] == [10, 11, 12, 13], "exact actual current group")
        need(g["group_head_pc"] == 0x800002f8 and g["cmtcnt"] == 4 and g["instruction_ring_tail"] == 13, "actual group head/count/tail")
        need(result["fault"]["final_vd_writer"]["result"] == 0xffffe421, "full128 final writer")
        return result
    rows = [("actual_unmodified_failure_log_new_host_parser", False, lambda: invoke(text))]
    for value in (0, 31, 99, 100, 255):
        changed = historical.replace("dst 32", f"dst {value:02d}")
        raw = once(text, historical, changed)
        rows.append((f"historical_raw_dst_{value}_accepted", False, lambda raw=raw: invoke(raw)))
    for value in ("256", "999", "1000", "-1"):
        raw = once(text, historical, historical.replace("dst 32", "dst " + value))
        rows.append((f"historical_raw_dst_{value}_rejected", True, lambda raw=raw: invoke(raw)))
    for value in (32, 255, 17):
        raw = once(text, current, current.replace("dst 16", f"dst {value:02d}"))
        rows.append((f"current_custom_dst_{value}_rejected", True, lambda raw=raw: invoke(raw)))
    mutations = {
        "historical_slot_order": once(text, historical, historical.replace("[06]", "[05]")),
        "missing_one_ring_slot": once(text, historical + "\n", ""),
        "duplicate_instruction_tail": once(text, historical, historical + " <--"),
        "missing_instruction_tail": once(text, ring_row(text, 13), ring_row(text, 13).replace(" <--", "")),
        "wrong_current_group_count": once(text, "commit group [09]: pc 00800002f8 cmtcnt 4 <--", "commit group [09]: pc 00800002f8 cmtcnt 3 <--"),
        "current_group_count_outside_ring": once(text, "commit group [09]: pc 00800002f8 cmtcnt 4 <--", "commit group [09]: pc 00800002f8 cmtcnt 33 <--"),
        "wrong_current_word": once(text, current, current.replace("0294080b", "0294088b")),
        "wrong_current_ROB": once(text, current, current.replace("idx 01c", "idx 02a")),
        "wrong_current_low64": once(text, current, current.replace("00000000ffffe421", "00000000ffffe420")),
        "wrong_final_reference_full128": once(text, "v16: 0x0000000000000000_00000000ffffe421", "v16: 0x0000000000000001_00000000ffffe421"),
        "wrong_bit100_XOR": once(text, "right= 0x0000001000000000", "right= 0x0000000800000000"),
        "wrong_injected_PC": once(text, "pc=0x80000300 instruction=0x0294080b", "pc=0x80000304 instruction=0x0294080b"),
        "wrong_final_VL": once(text, "vl: 0x0000000000000008", "vl: 0x0000000000000004"),
    }
    for name, raw in mutations.items():
        rows.append((name, True, lambda raw=raw: invoke(raw)))
    return rows
