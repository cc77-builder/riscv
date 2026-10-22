"""Fail-closed UART/retirement checks for the supplemental O2 G3 diagnostic."""
import hashlib
import json
from pathlib import Path
import re

def require(ok,message):
    if not ok:
        raise ValueError(message)

def marker_position(uart, marker):
    matches=list(re.finditer("^"+re.escape(marker)+"$",uart,re.M))
    require(len(matches)==1 and uart.count(marker)==1,"missing/duplicate/noncanonical marker: "+marker)
    return matches[0].start()

def verify_build(build):
    build=Path(build)
    receipt=json.loads((build/"build.json").read_text())
    require(receipt["status"]=="O2_DIAGNOSTIC_BUILD_PASS","build did not pass")
    for group in ["source_sha256","generated_sha256","images_sha256","am_libraries_sha256"]:
        for name,digest in receipt[group].items():
            path=Path(name) if Path(name).is_absolute() else build/name
            require(hashlib.sha256(path.read_bytes()).hexdigest()==digest,"diagnostic artifact drift: "+name)
    return json.loads((build/"data/manifest.json").read_text())

def check(uart,manifest,exit_code,analysis):
    require(exit_code==0,"diagnostic EMU nonzero exit")
    uart=uart.replace("\r\n","\n")
    require(not re.search(r"O2_DIAG_FAIL|HIT BAD TRAP|different at pc|DIFFTEST FAIL|ABORT|Assertion.*failed",uart),
            "diagnostic failure marker")
    begin="O2_DIAG_BEGIN cases=10 fixed_dots=128 contract=vdot-s8x8-r32-v0.1"
    require(uart.count(begin)==1 and uart.count("O2_DIAG_BEGIN")==1,"missing/duplicate diagnostic begin")
    control="O2_DIAG_CHECKER_CONTROL highbit_detected=1"
    require(uart.count(control)==1 and uart.count("O2_DIAG_CHECKER_CONTROL")==1,"missing checker control")
    position=marker_position(uart,begin)
    control_position=marker_position(uart,control)
    require(control_position>position,"checker control before begin")
    position=control_position
    for i,case in enumerate(manifest["cases"]):
        marker=f'O2_DIAG_CASE_PASS seq={i} id={case["id"]} dots={case["counts"]["vdot"]} register_bytes=512 csr_fields=7'
        found=marker_position(uart,marker)
        require(found>position,"reordered diagnostic case")
        position=found
    require(uart.count("O2_DIAG_CASE_PASS")==len(manifest["cases"]),"extra case marker")
    expected=manifest["expected_vdot_commits"]
    summary=f'O2_DIAG_SUMMARY cases={len(manifest["cases"])} dots={expected} failures=0'
    require(marker_position(uart,summary)>position and uart.count("O2_DIAG_SUMMARY")==1,
            "missing/duplicate/reordered summary")
    require(uart.count("HIT GOOD TRAP")==1 and uart.index("HIT GOOD TRAP")>uart.index(summary),"missing final GOOD TRAP")
    require(analysis["status"]=="O2_TRACE_PASS","diagnostic trace not complete")
    require(analysis["counts"].get("COMMIT")==expected,"diagnostic retirement mismatch")
    require(analysis.get("pending_count")==0 and analysis.get("unfinished_rob_count")==0,"diagnostic failed to drain")
    return dict(status="O2_DIAGNOSTIC_PASS",cases=len(manifest["cases"]),expected_vdot_commits=expected,
                checked_register_bytes=len(manifest["cases"])*512,csr_fields_per_case=7,
                observation_counts=analysis["counts"],performance_measured=False)

def check_control(uart,manifest,exit_code,analysis):
    require(exit_code==0,"control diagnostic EMU nonzero exit")
    uart=uart.replace("\r\n","\n")
    require(not re.search(r"O2_CONTROL_FAIL|HIT BAD TRAP|different at pc|DIFFTEST FAIL|ABORT|Assertion.*failed",uart),
            "control diagnostic failure marker")
    begin="O2_CONTROL_BEGIN groups=16 trials=256 contract=vdot-s8x8-r32-v0.1"
    require(uart.count(begin)==1 and uart.count("O2_CONTROL_BEGIN")==1,"missing/duplicate control begin")
    position=marker_position(uart,begin)
    for group in manifest["groups"]:
        marker=f'O2_CONTROL_GROUP_PASS id={group["id"]} trials=16 register_bytes=8192'
        found=marker_position(uart,marker)
        require(found>position,"reordered control group")
        position=found
    require(uart.count("O2_CONTROL_GROUP_PASS")==len(manifest["groups"]),"extra group marker")
    summary="O2_CONTROL_SUMMARY groups=16 trials=256 register_bytes=131072 failures=0"
    require(marker_position(uart,summary)>position and uart.count("O2_CONTROL_SUMMARY")==1,"invalid control summary")
    require(uart.count("HIT GOOD TRAP")==1 and uart.index("HIT GOOD TRAP")>uart.index(summary),"missing final GOOD TRAP")
    require(analysis["status"]=="O2_TRACE_PASS","control diagnostic trace incomplete")
    expected=manifest["expected_vdot_commits"]
    require(analysis["counts"].get("COMMIT")==expected,"control diagnostic retirement mismatch")
    require(analysis.get("pending_count")==0 and analysis.get("unfinished_rob_count")==0,"control diagnostic did not drain")
    return dict(status="O2_CONTROL_DIAGNOSTIC_PASS",expected_vdot_commits=expected,
                checked_register_bytes=manifest["whole_vector_bytes_checked"],
                observation_counts=analysis["counts"],performance_measured=False)
