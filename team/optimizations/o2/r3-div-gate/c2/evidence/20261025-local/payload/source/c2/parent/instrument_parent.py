#!/usr/bin/env python3
"""Add read-only hierarchical observations to a NEW generated TEST TOP only."""
import hashlib
import json
from pathlib import Path
import re

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def instrument(rtl, receipt):
    rtl=Path(rtl).resolve();receipt=Path(receipt).resolve()
    if receipt.exists():
        raise ValueError("refuse to replace observer receipt")
    top=rtl/"VDotElasticParentTestTop.sv"
    files=sorted(p for p in rtl.rglob("*") if p.suffix in (".sv",".v"))
    before={p.relative_to(rtl).as_posix():sha(p) for p in files}
    t=top.read_text()
    if "io_fp_lane_finish" in t:
        raise ValueError("top is already instrumented")
    exu=(rtl/"ExeUnit.sv").read_text()
    fp=(rtl/"VFDivSqrt.sv").read_text()
    assert re.search(r"\bExeUnit\s+dut\s*\(",t)
    assert re.search(r"\bVFDivSqrt\s+Vfdiv\s*\(",exu)
    for lane in (0,1):
        for signal in ("start_ready_o","finish_valid_o"):
            assert re.search(r"\bwire\s+_vfdivs_"+str(lane)+"_io_"+signal+r"\s*;",fp)
    busy=re.findall(r"^\s*reg\s+(\w*divBusy)\s*;",exu,re.M)
    if len(busy)!=1:
        raise ValueError("DIV busy binding is not unique: "+repr(busy))
    old="module VDotElasticParentTestTop(\n"
    assert t.count(old)==1 and t.count("\nendmodule")==1
    t=t.replace(old,old+"""  output [1:0] io_fp_lane_ready,
               io_fp_lane_finish,
  output       io_div_busy,
""")
    observation="""  // C2 test-only hierarchical reads; no production nets are driven.
  assign io_fp_lane_ready = {dut.Vfdiv._vfdivs_1_io_start_ready_o, dut.Vfdiv._vfdivs_0_io_start_ready_o};
  assign io_fp_lane_finish = {dut.Vfdiv._vfdivs_1_io_finish_valid_o, dut.Vfdiv._vfdivs_0_io_finish_valid_o};
  assign io_div_busy = dut.%s;
""" % busy[0]
    t=t.replace("\nendmodule","\n"+observation+"endmodule")
    original=receipt.parent/"observer-original-top.sv.txt"
    if original.exists():
        raise ValueError("refuse to replace original test top")
    original.write_bytes(top.read_bytes());top.write_text(t)
    after={p.relative_to(rtl).as_posix():sha(p) for p in files}
    changed=[name for name in before if before[name]!=after[name]]
    assert changed==["VDotElasticParentTestTop.sv"],changed
    receipt.write_text(json.dumps(dict(status="C2_READONLY_OBSERVER_BOUND",
        before=before,after=after,changed=changed,div_busy="dut."+busy[0],
        production_modules_unchanged=True,original_test_top=str(original),
        original_sha256=sha(original),observer_script_sha256=sha(Path(__file__))),indent=2)+"\n")
    return receipt

if __name__=="__main__":
    import sys
    instrument(sys.argv[1],sys.argv[2])
