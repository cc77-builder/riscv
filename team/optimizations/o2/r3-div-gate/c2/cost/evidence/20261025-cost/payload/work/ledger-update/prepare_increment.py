"""Generate a C2 cost ledger increment only; never invoke hardware tools."""
import argparse, datetime, hashlib, json
from pathlib import Path
CANDIDATE="6704ce3502a7235cdb81697638c01ed23f6914f6"
BASELINE="0f12df675378556670afd0dd2153f47fcb330610"
REL="team/optimizations/o2/r3-div-gate/c2"
ARCHIVE=REL+"/cost/evidence/20261025-cost/manifest.json"
PROFILE=["nominal","period050","period200","load001","load020"]
KINDS=["r2r","i2r","vdot_r2r","vdot_i2r","vdot_r2o","ready","icg0","icg1","icg2"]
def read(p): return json.loads(p.read_text(encoding="utf-8"))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,j): p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def native(p):
    s=str(p).replace("\\","/"); prefix="//wsl.localhost/Ubuntu-22.04"
    return s[len(prefix):] if s.startswith(prefix) else s
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,default=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo"))
    p.add_argument("--work",type=Path,default=Path(__file__).resolve().parent.parent)
    p.add_argument("--baseline",type=Path,default=Path("/home/riscv/riscv-lab/o2-r3-div-gate-cost-20261025"))
    p.add_argument("--tools",type=Path,default=Path("/home/riscv/riscv-lab/o4-cost-20261020"))
    a=p.parse_args(); out=a.work/"ledger-update"
    required=[a.work/x for x in ["parent-map-01/summary.json","parent-sta-01/summary.json","screen-01/result.json"]]
    if not all(x.exists() for x in required): raise SystemExit("PENDING: complete receipts required; no final files written")
    mapping,timing,screen=[read(x) for x in required]
    bm=read(a.baseline/"parent-map-01/summary.json")
    assert mapping["pass"] and timing["pass"] and screen["candidate_head"]==CANDIDATE
    assert [x["profile"] for x in timing["profiles"]]==PROFILE
    rows=sorted(screen["comparisons"],key=lambda x:(PROFILE.index(x["profile"]),KINDS.index(x["path"])))
    assert len(rows)==45 and {(r["profile"],r["path"]) for r in rows}=={(p,k) for p in PROFILE for k in KINDS}
    failed=[r for r in rows if not r["pass_"]]
    accepted=screen["status"]=="C2_SCREEN_PASS"
    assert screen["status"] in ["C2_SCREEN_PASS","C2_SCREEN_REJECT"]
    assert accepted==(not screen["failures"])==screen["fullcore_authorized_by_gate"]
    run=read(a.work/"campaign.json"); controls=read(a.work/"screen-01/state.json")
    assert all(x["exit_code"]==0 for x in run["steps"])
    assert len(controls["steps"])==10 and all(x["exit_code"]==0 for x in controls["steps"])
    dff=lambda x:sum(v for k,v in x["cell_histogram"].items() if k.startswith("DFF"))
    limit=bm["cell_area_sum"]*1.001
    toolp=a.tools/"tools/executable-identities.json"; archive=a.main/ARCHIVE
    contract=a.main/REL/"cost/CONTRACT.md"
    record=dict(
      record_id="C2-cost-20261025-01",label="C2 同约束真实父级面积与五档 STA 筛选",
      identity_ids=["DIV-fix0f","C2"],source_ids=["c2_cost"],
      contract_refs=[REL+"/cost/CONTRACT.md"],source_commit=CANDIDATE,baseline_commit=BASELINE,
      contract_sha256=sha(contract),source_snapshot_manifest_sha256=sha(a.work/"inputs.json"),
      configuration=dict(boundary="complete production CommonParentCostTop / real VFEX4",
        mode="O2_ELASTIC=1,FUSED_INPUT=1,O1_HANDOFF=0,all traces=0,TE=0",
        tools="Yosys0.9/ABC1.01/OpenSTA2.0.17",library="Nangate45 typical 25C/1.1V",
        abc="-D1000ps; BUF_X1 drive; 5fF load",
        sta="ideal clock; 5K wire-load; uncertainty/transition=0.05ns; IO delay=0.1ns",
        profiles=[{k:x[k] for k in ["profile","period_ns","load_ff"]} for x in timing["profiles"]]),
      summary=f"1 new parent synthesis + 5 standard STA + 10 targeted control STA; {45-len(failed)}/45 path items within frozen tolerance; {screen['status']}.",
      decision=screen["status"]+("_AWAIT_INDEPENDENT_REVIEW_BEFORE_CORE" if accepted else "_NOT_ADOPTED_KEEP_DIV_FIX0F"),
      verification={k:"NOT_TESTED" for k in ["numeric_rtl","fu","real_parent","fullcore_difftest","cycles","power","fullcore_fmax","independent_human_rebuild"]},
      prior_qualification=dict(record_id="C2-local-20261025-01",evidence_manifest_sha256=screen["local_manifest_sha256"],reuse_note="Existing unchanged FU/parent qualification; no new simulation in this cost run."),
      input_identities=dict(emu_sha256="NOT_TESTED",nemu_sha256="NOT_TESTED",images_manifest_sha256="NOT_TESTED",
        toolchain_manifest_sha256=sha(toolp),toolchain_manifest=native(toolp),library_sha256=mapping["library_sha256"],
        generated_rtl_manifest_sha256=mapping["generation_sha256"],mapped_netlist_sha256=mapping["mapped_sha256"],
        mapped_json_sha256=mapping["mapped_json_sha256"],baseline_manifest_sha256=screen["baseline_manifest_sha256"]),
      execution=dict(started_at=run["started"],finished_at=controls["finished"],new_parent_synthesis=1,new_standard_sta=5,
        new_targeted_sta=10,reused_parent_synthesis=1,reused_standard_sta=5,commands=run["steps"]+controls["steps"],
        standard_sta_receipts=native(a.work/"parent-sta-01"),new_fullcore_processes=0,new_cycle_comparison_processes=0),
      metrics={k:screen[k] for k in ["area_before","area_after","area_delta_percent","control_before_ns","control_after_ns","control_delta_percent"]},
      raw_evidence_location=ARCHIVE,evidence_manifest_sha256=sha(archive) if archive.exists() else "PENDING_ARCHIVE_FINALIZATION",
      result_path=REL+"/cost/RESULT.md",
      limitations=[
        "Pre-layout area/STA only; not placement/routing, power, fullcore Fmax or contest score.",
        "Frozen engineering thresholds, not official contest thresholds; tool success differs from screen acceptance and timing closure.",
        "All profiles, endpoints/slack and failures are retained; source identity must be validated for FU cost reuse.",
        "No new fullcore/NEMU or fair-cycle run in this record; subsequent work gets a separate record.",
        "Baseline original cost run predates final 0f commit; source equivalence is established by frozen source manifests, not a claim its original run HEAD was 0f."])
    record["verification"]["area_sta"]="PASS_REPORTS_"+("SCREEN_PASS" if accepted else "SCREEN_REJECT")
    record["metrics"].update(area_limit=limit,area_gate_pass=screen["area_after"]<=limit,dff_before=dff(bm),dff_after=dff(mapping),
        cell_count_before=bm["cell_count"],cell_count_after=mapping["cell_count"],unknown_cells=mapping["unknown_cells"],
        icg_count=mapping["cell_histogram"]["CLKGATETST_X1"],control_limit_ns=1.737526,
        control_gate_pass=screen["control_after_ns"]<=1.737526,path_items_total=45,path_items_passed=45-len(failed),
        path_items_failed=len(failed),comparisons=rows,all_screen_failures=screen["failures"],
        positive_slack_icg_preserved=all(x["before"]["slack_ns"]<0 or x["after"]["slack_ns"]>=0 for x in rows if x["path"].startswith("icg")),
        fullcore_entry_open_by_numeric_screen=screen["fullcore_authorized_by_gate"])
    pins=[contract,toolp]+[a.work/x for x in ["inputs.json","dependencies.json","preflight.json","campaign.json","parent-map-01/summary.json","parent-sta-01/summary.json","screen-01/result.json","screen-01/state.json","screen-01/inputs.json"]]
    pins+=list((a.work/"parent-cost-01").glob("*.json"))
    audit_specs=[
      ("independent-review/final-audit-01/audit.json","C2_COST_INDEPENDENT_AUDIT_PASS"),
      ("independent-review/portable-audit-01/audit.json","C2_PORTABLE_COST_AUDIT_PASS"),
      ("independent-review/generated-production-audit.json","C2_COST_PRODUCTION_MODULES_PASS")]
    audit_receipts=[]
    for rel,status in audit_specs:
        ap=a.work/rel; data=read(ap)
        assert data["status"]==status
        if "screening_pass" in data:
            assert data["screening_pass"]==accepted and data["paths"]==45 and data["path_pass_count"]==45-len(failed)
            assert data["screen_result_sha256"]==sha(a.work/"screen-01/result.json")
        audit_receipts.append(dict(path=native(ap),sha256=sha(ap),status=status))
        pins.append(ap)
    for rel in ["independent-review/final-audit-01/inputs.json","independent-review/portable-audit-01/inputs.json",
                "independent-review/final-audit-01.command.json","independent-review/portable-audit-01.command.json"]:
        ap=a.work/rel
        if ap.exists():
            if rel.endswith(".command.json"): assert read(ap)["exit_code"]==0
            pins.append(ap)
    record["independent_audit"]=dict(status="PASS",receipts=audit_receipts,note="Read-only audits, not independent human rebuild or new simulation.")
    record["decision"]=screen["status"]+("_ELIGIBLE_FOR_NEW_FULLCORE_NOT_ADOPTED" if accepted else "_NOT_ADOPTED_KEEP_DIV_FIX0F")
    save(out/"source-pins.json",[dict(origin=native(x),bytes=x.stat().st_size,sha256=sha(x),archive_manifest=ARCHIVE) for x in pins])
    save(out/"record.json",record)
    save(out/"full-timing.json",dict(baseline=read(a.baseline/"parent-sta-01/summary.json"),candidate=timing,
        targeted_control={side:{profile:read(a.work/"screen-01"/side/profile/"paths.json") for profile in PROFILE} for side in ["before","after"]}))
    save(out/"tool-identities.json",read(toolp))
    lines=["## 9. C2-cost-20261025-01：同约束真实父级成本筛选","",
      "这是 C2-local 后新增的独立成本记录；旧轮当时的面积/STA、全核和周期 NOT_TESTED 保留。",
      "",f"候选 {CANDIDATE}；对照 {BASELINE}。完整生产 CommonParentCostTop / VFEX4，O2 弹性和融合输入开启，O1/trace 关闭，TE=0。沿用第 5 节同一参考库、工具、综合及五档约束。",
      "",f"新执行 1 次父级综合、5 次标准 STA、两边共 10 次控制专项 STA；结果 **{screen['status']}**，45 项中 {45-len(failed)} 项通过、{len(failed)} 项失败。",
      "","| 指标 | fix0f | C2 | 变化 / 门槛 |","| --- | ---: | ---: | --- |",
      f"| 父级单元面积和 | {screen['area_before']:.3f} | {screen['area_after']:.3f} | {screen['area_delta_percent']:+.6f}%；上限 {limit:.6f} |",
      f"| 父级 DFF | {dff(bm)} | {dff(mapping)} | 实际映射 |",
      f"| nominal 控制 D 最差 ns | {screen['control_before_ns']:.6f} | {screen['control_after_ns']:.6f} | {screen['control_delta_percent']:+.6f}%；上限 1.737526 |",
      f"| 未知单元 / ICG 数 | {len(bm['unknown_cells'])} / 3 | {len(mapping['unknown_cells'])} / {mapping['cell_histogram']['CLKGATETST_X1']} | 完整生产边界 |",
      "","五档完整筛选如下。数值为 arrival / slack（ns）；arrival 上限为对照的 101%，原有正 slack 的 ICG 保持非负。icg0/1/2 是原报告查询标识，语义和起止点在 JSON 与原报告中保留。",
      "","| 档位 | 路径 | fix0f arrival / slack | C2 arrival / slack | arrival 变化 | 筛选 |","| --- | --- | ---: | ---: | ---: | --- |"]
    for x in rows:
        b,c=x["before"],x["after"]
        lines.append(f"| {x['profile']} | {x['path']} | {b['arrival_ns']:.6f} / {b['slack_ns']:.6f} | {c['arrival_ns']:.6f} / {c['slack_ns']:.6f} | {x['delta_percent']:+.6f}% | {'PASS' if x['pass_'] else 'FAIL'} |")
    lines+=["","全部筛选失败原因：",""]+["- "+x for x in screen["failures"]]
    if not screen["failures"]: lines+=["- 无数值筛选失败，仍须独立复核。"]
    lines+=["",("本候选未通过冻结成本合同，保留 fix0f，本候选全核与周期入口关闭。" if not accepted else "数值筛选通过；独立复核通过后才进入新全核与同镜像周期任务。"),
      "本成本记录的新全核/NEMU、新同镜像 cycles、功耗和整核 Fmax 均为 **NOT_TESTED**。此前 C2-local 的 FU/父级资格按固定来源复用，本轮未重跑局部仿真。",
      "","这是布局前工程筛选，不是官方赛题门槛；不能把负 slack 忽略、将 arrival 倒数当整核 Fmax，或将相对改善当作已经完成 1ns 时序收敛。",
      "","[合同](../optimizations/o2/r3-div-gate/c2/cost/CONTRACT.md) · [完整结果](../optimizations/o2/r3-div-gate/c2/cost/RESULT.md) · [证据 manifest](../optimizations/o2/r3-div-gate/c2/cost/evidence/20261025-cost/manifest.json)。全部标准与专项路径、起止点和 slack 保留在 JSON 与原始报告中。"]
    lines += ["", "独立原文复算 C2_COST_INDEPENDENT_AUDIT_PASS、便携审计 C2_PORTABLE_COST_AUDIT_PASS、生产生成物审计 C2_COST_PRODUCTION_MODULES_PASS；审计通过确认数据与拒绝结论一致，不代表候选通过筛选。审计来源及 SHA 已追加至 JSON。"]
    (out/"append-section.md").write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n")
    before=read(out/"before.json"); old=read(a.main/"team/docs/version-data-ledger.json")
    assert len(old["records"])==18
    for x in old["records"]:
        assert hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()==before["record_sha256"][x["record_id"]]
    save(out/"increment-check.json",dict(status="C2_COST_LEDGER_INCREMENT_PREPARED",record_id=record["record_id"],old_records_unchanged=18,comparisons=45,screen_status=screen["status"],manifest_pending=not archive.exists(),main_files_written=False))
    print(json.dumps(dict(status="C2_COST_LEDGER_INCREMENT_PREPARED",path_failures=len(failed),decision=record["decision"])))
if __name__=="__main__": main()
