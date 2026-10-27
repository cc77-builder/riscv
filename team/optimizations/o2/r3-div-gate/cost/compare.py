#!/usr/bin/env python3
"""Audit preserved H1 and newly mapped DIV-gate candidate under identical conditions."""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "team/optimizations/o4"))
spec = importlib.util.spec_from_file_location("h1_cost_shared", ROOT / "team/optimizations/o2/result-width/h1/compare_cost.py")
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
require, sha, read = shared.require, shared.sha, shared.read
EXE = "src/main/scala/xiangshan/backend/exu/ExeUnit.scala"

def compare(work, baseline, tools):
    pins = read(work / "candidate-inputs.json")
    state = read(work / "campaign-state.json")
    require(state["hardware_steps_complete"], "new mapping/STA incomplete")
    require(pins["source_commit"] == "0f12df675378556670afd0dd2153f47fcb330610", "wrong candidate")
    for name, digest in pins["files"].items():
        require(sha(Path(name)) == digest, "input drift: " + name)
    baseline_pins = read(baseline / "candidate-inputs.json")
    relevant = {n: d for n, d in baseline_pins["source_sha256"].items()
                if n.startswith("src/") or n in ("build.sc", ".mill-version")
                or n.startswith("team/optimizations/o4/")}
    require([n for n,d in relevant.items() if sha(ROOT/n) != d] == [EXE],
            "unexpected source changes beyond ExeUnit")
    require(baseline_pins["source_sha256"][EXE] ==
            hashlib.sha256(subprocess.check_output(["git","show",
                "8b5024fcbd96986871cc40ce8c9fb71a67c495eb:"+EXE],cwd=ROOT)).hexdigest(),
            "cost baseline is not preserved H1 ExeUnit")
    sealed = ROOT / "team/optimizations/o2/result-width/h1/evidence/20261021-local/manifest.json"
    require(sha(sealed) == "73fe5f79d3209937a3278a16f8bfc70f90333fc46657de161810bcf9c2d8974a",
            "H1 sealed manifest drift")
    entries = read(sealed)["entries"]
    identities = read(tools / "tools/executable-identities.json")
    libraries = {}
    for name, rec in identities.items():
        require(sha(tools/"tools/root/usr/bin"/name) == rec["sha256"] == baseline_pins["tools"][name],
                "tool identity mismatch")
        for path, digest in rec["shared_library_sha256"].items():
            require(sha(Path(path)) == digest, "dynamic library changed: " + path)
            libraries[path] = digest
    require(sha(tools/"library/NangateOpenCellLibrary_typical.lib") ==
            baseline_pins["library_sha256"], "reference library changed")
    result = {}
    for boundary in ("fu", "parent"):
        names = tuple(boundary+s for s in ("-cost-01","-map-01","-sta-01"))
        before = shared.audit_one(baseline, names, boundary, 32, tools)
        shared.check_sealed_inventory(before["input_hashes"], entries)
        after = shared.audit_one(work, names, boundary, 32, tools)
        require(read(work/names[0]/"result.json")["source_commit"] == pins["source_commit"],
                "generation source commit mismatch")
        shared.AUDIT.compare_interfaces(before["ports"], after["ports"])
        for key in ("mapped_metadata", "structure_register_groups"):
            require(before[key] == after[key], "VDot state changed: " + key)
        require({k:v["body_sha256"] for k,v in before["arithmetic"].items()} ==
                {k:v["body_sha256"] for k,v in after["arithmetic"].items()}, "dot arithmetic changed")
        require(before["storage"]["stored_bits"] == after["storage"]["stored_bits"] == 32
                and before["storage"]["child_output_high96_zero"] and after["storage"]["child_output_high96_zero"],
                "H1 full128 contract lost")
        changes = shared.timing_changes(before["timing"], after["timing"], boundary)
        result[boundary] = dict(before=before, after=after,
            area_delta=after["area"]-before["area"],
            area_delta_percent=100*(after["area"]-before["area"])/before["area"],
            cell_delta=after["cell_count"]-before["cell_count"],
            dff_delta=after["dff_count"]-before["dff_count"],
            timing_changes=changes)
    return dict(status="R3_DIV_GATE_COST_AUDIT_PASS", finished_utc=datetime.now(timezone.utc).isoformat(),
        before_source="8b5024fc (H1), exact sealed earlier local H1 PPA source",
        after_source=pins["source_commit"], baseline_method="Reused sealed H1 raw generation/mapping/STA",
        new_mapping_count=2,new_sta_profiles=10,new_path_reports=70,
        baseline_raw_root=str(baseline),candidate_raw_root=str(work),results=result,
        library_sha256=baseline_pins["library_sha256"],
        tools=baseline_pins["tools"],shared_libraries=libraries,
        source_differences=[EXE], source_files_compared=len(relevant),
        timing_signoff=False,power_measured=False,whole_core_ppa_measured=False,
        source_and_input_unchanged=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--work",type=Path,required=True)
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--tools",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    require(not a.output.exists(),"output exists")
    report=compare(a.work,a.baseline,a.tools)
    a.output.mkdir(parents=True)
    (a.output/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    rows=[]
    lines=["# R3 DIV取消关钟修复：同约束综合与STA","",
        "修复前复用完整封存H1，修复后本轮重新生成、映射与STA。相同完整接口、工具、库和约束；审计PASS不表示1ns时序收敛。","",
        "| 边界 | 修复前面积 | 修复后面积 | 增量 | 增量比例 | DFF | ICG |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |"]
    for boundary,rec in report["results"].items():
        b,c=rec["before"],rec["after"]
        lines.append(f'| {boundary} | {b["area"]:.3f} | {c["area"]:.3f} | {rec["area_delta"]:+.3f} | {rec["area_delta_percent"]:+.6f}% | {b["dff_count"]}→{c["dff_count"]} | {b["icg_count"]}→{c["icg_count"]} |')
        for profile,value in rec["timing_changes"].items():
            for kind,path in value["paths"].items():
                rows.append(dict(boundary=boundary,profile=profile,path=kind,
                    before_arrival_ns=path["baseline"]["arrival_ns"],
                    after_arrival_ns=path["candidate"]["arrival_ns"],
                    delta_ps=1000*path["arrival_delta_ns"],
                    before_slack_ns=path["baseline"]["slack_ns"],
                    after_slack_ns=path["candidate"]["slack_ns"],
                    before_startpoint=path["baseline"]["startpoint"],
                    before_endpoint=path["baseline"]["endpoint"],
                    after_startpoint=path["candidate"]["startpoint"],
                    after_endpoint=path["candidate"]["endpoint"]))
    require(len(rows)==70,"incomplete path table")
    with (a.output/"timing.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    lines+=["","| 边界/nominal路径 | 前arrival(ns) | 后arrival(ns) | 差值(ps) | 后slack(ns) |",
            "| --- | ---: | ---: | ---: | ---: |"]
    for row in rows:
        if row["profile"]=="nominal":
            lines.append(f'| {row["boundary"]}/{row["path"]} | {row["before_arrival_ns"]:.6f} | {row["after_arrival_ns"]:.6f} | {row["delta_ps"]:+.3f} | {row["after_slack_ns"]:.6f} |')
    nominal=[row for row in rows if row["profile"]=="nominal"]
    lines+=["",f'70组比较中arrival变大 {sum(x["delta_ps"]>0 for x in rows)} 组，变小 {sum(x["delta_ps"]<0 for x in rows)} 组。',
        f'nominal所报路径仍有负slack：修复前{sum(x["before_slack_ns"]<0 for x in nominal)}类，修复后{sum(x["after_slack_ns"]<0 for x in nominal)}类。',
        "完整五档含1/5/20fF与0.5/1/2ns单变量敏感性；逐条起止点、slack及差值见timing.csv。",
        "Nangate45典型参考库单元面积(μm²)，布局前理想时钟/线负载模型。没有整核面积、CTS/布线/SPEF、实测功耗或Fmax。",
        "局部测试证明取消后空闲钟脉冲消除；本表的面积和延迟不能直接换算成动态功耗节省。",
        "未推送GitHub；正式比赛报告后置。"]
    (a.output/"RESULT.md").write_text("\n".join(lines)+"\n")
    print(report["status"])

if __name__=="__main__": main()
