"""Finalize only after the actual supplement and independent offline audit pass."""
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

R=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
W=Path("/home/riscv/riscv-lab/software-import-20261026")
O=W/"r5-g5-acceptance-01"
A=R/"team/optimizations/o2/integration/firstdot-v2-0f/acceptance"
LEAF=A.parent
RECORD="R5-G5-DIVFIX0F-FIRSTDOT-C8-20261027-01"

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
def need(x,m):
    if not x:raise RuntimeError(m)

def main():
    need(not (A/"record.json").exists(),"already finalized; do not append twice")
    full=read(O/"clock-supplement-03/results.json")
    audit=read(O/"composite-audit-01/results.json")
    need(full["status"]=="R5_G5_COMPOSITE_FULLCORE_PASS" and audit["status"]=="R5_G5_COMPOSITE_RAW_AUDIT_PASS","core gate")
    need(audit["source_result_sha256"]==sha(O/"clock-supplement-03/results.json"),"core audit binding")
    for filename in ("model.command.json","freeze.command.json","fu-parent-audit.command.json",
                     "selected-inputs-02.command.json","cost-archive.command.json",
                     "t15-offline-audit-02.command.json","clock-supplement-03.command.json","composite-audit.command.json"):
        need(read(O/filename)["exit_code"]==0,"incomplete command: "+filename)
    need(read(O/"t15-offline-audit-02.json")["status"]=="T15_OFFLINE_RECHECK_PASS","parameter gate")
    need(read(O/"selected-inputs-02/results.json")["status"]=="R5_SELECTED_INPUTS_AND_C8_EQUIVALENCE_PASS","selection")
    freeze=read(A/"freeze.json")
    for rel,digest in freeze["files"].items():
        need(sha(R/rel)==digest,"frozen input changed: "+rel)
    need(not subprocess.check_output(["git","diff","HEAD","--","src"],cwd=R),"production diff")
    need(subprocess.check_output(["git","rev-parse","HEAD"],cwd=R,text=True).strip()==freeze["head"],"HEAD changed")
    ledger_path=R/"team/docs/version-data-ledger.json"
    ledger=read(ledger_path);before=read(O/"ledger-before.json")
    need(ledger["records"]==before["records"] and len(ledger["records"])==28,"prior records changed")
    # Save pre-update navigation and append-only markdown for review.
    nav=O/"navigation-before";nav.mkdir()
    for rel in freeze["navigation_excluded"]:
        dest=nav/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/rel,dest)
    matrix=read(A/"acceptance-matrix.json")
    for row in matrix["items"]:
        if row["id"]=="fullcore":row["status"]="PASS_COMPOSITE_13_REUSED_PLUS_1_NEW"
        need(row["status"]!="PENDING","matrix pending: "+row["id"])
    matrix["status"]="R5_G5_ENGINEERING_ACCEPTED_WITH_DECLARED_LIMITS"
    save(A/"acceptance-matrix.json",matrix)
    # Bundle new receipts and code, retain failures; giant workspace snapshot stays external.
    evidence=A/"evidence";need(not evidence.exists(),"fresh evidence");evidence.mkdir()
    sources={}
    for p in O.rglob("*"):
        if p.is_file() and p.name!="frozen-workspace.tar.gz":
            sources["work/"+str(p.relative_to(O))]=p
    for p in A.iterdir():
        if p.is_file():sources["tools/"+p.name]=p
    entries=[]
    for logical,path in sorted(sources.items()):
        raw=path.read_bytes();compressed=len(raw)>262144
        stored="files/"+logical+(".gz" if compressed else "")
        dest=evidence/stored;dest.parent.mkdir(parents=True,exist_ok=True)
        content=gzip.compress(raw,compresslevel=6,mtime=0) if compressed else raw
        dest.write_bytes(content)
        entries.append(dict(path=logical,original=str(path),stored=stored,gzip=compressed,
                            raw_sha256=hashlib.sha256(raw).hexdigest(),raw_bytes=len(raw),
                            stored_sha256=hashlib.sha256(content).hexdigest(),stored_bytes=len(content)))
    save(evidence/"manifest.json",dict(contract="r5-g5-evidence-archive-v1",files=entries,
       excluded_giant_snapshot=read(O/"frozen-workspace.tar.gz.json"),
       old_fullcore_evidence="Existing clean-02 fullcore archive retained; reused13 raw sources bound in composite origins.",
       new_execution_only=1))
    for row in entries:
        content=(evidence/row["stored"]).read_bytes()
        need(hashlib.sha256(content).hexdigest()==row["stored_sha256"],"stored archive corruption")
        raw=gzip.decompress(content) if row["gzip"] else content
        need(hashlib.sha256(raw).hexdigest()==row["raw_sha256"] and len(raw)==row["raw_bytes"],"raw archive corruption")
    finished=dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat()
    clock=full["new_phase_clock"]
    new=next(x for x in full["records"] if x["name"]=="o2-control-diagnostic")
    manifest_rel=str((evidence/"manifest.json").relative_to(R))
    record=dict(record_id=RECORD,status=matrix["status"],recorded_at=finished,
      label="冻结0f＋firstdot V2＋显式C8候选，R5/G5工程总验收",
      source_commit=freeze["head"],selected_hardware_commit=freeze["hardware"],
      source_snapshot=dict(path=str((A/"freeze.json").relative_to(R)),sha256=sha(A/"freeze.json"),files=len(freeze["files"]),
                           dirty_snapshot=True,local_archive=read(O/"frozen-workspace.tar.gz.json")),
      configuration=read(W/"clean-02/identity/current.json")["configuration"],
      hardware_identity=dict(path=str(W/"clean-02/identity/current.json"),sha256=sha(W/"clean-02/identity/current.json")),
      comparison_contract=dict(path=str((A/"CONTRACT.md").relative_to(R)),sha256=sha(A/"CONTRACT.md"),
                               clock_scope="13 old raw rechecks + 1 preselected new control diagnostic; not fresh14"),
      actual_execution=dict(new_emu_runs=1,reused_fullcore_runs=13,selected_fullcore_runs=14,
                            new_process_result=new,clock=clock,selected_utc_capacity=full["selected_utc_capacity"],
                            failed_preflight_new_emu_runs=0,failed_attempts=read(O/"failed-attempts.json")),
      verification=dict(production_source_identity="PASS_398_FILES",host_model="PASS_35_TESTS",
                        fu_parent="PASS_REUSED_RAW_REPARSED",fullcore="PASS_COMPOSITE_13_PLUS_1",
                        fullcore_raw_audit="PASS",old_clean02_wall_clock="FAIL_PRESERVED",
                        selected_set_utc_capacity="PASS",new_supplement_monotonic_capacity="PASS",host_utc_clock_stability="NOT_ESTABLISHED_DELTA_MINUS_62_888356_SECONDS",
                        clean_build="PASS_REUSED_SAME_HOST_AGENT",c8_final_image="PASS_RECHECKED",
                        t15="PASS_REUSED_INDEPENDENT_UNIT_ONLY",historical_area_sta="EVIDENCE_VALID_TIMING_NOT_CLOSED",
                        new_performance="NOT_TESTED",new_ppa="NOT_TESTED",power="NOT_TESTED",
                        fullcore_fmax="NOT_TESTED",human_reproduction="NOT_TESTED"),
      retained_performance=[dict(record_id="CONFIG-REUSE-MATRIX-DIVFIX0F-CLEAN02-20261027-01",
                                shape="8x32",vdot_cycles=273,fastest_rvv_cycles=299,speedup=299/273,
                                prior_firstdot_cycles=282.25,new_measurement=False),
                            dict(record_id="DIV-fix0f-20261025",scenario="batch128",vdot_cycles=221,
                                 rvv_cycles=678,speedup=678/221,new_measurement=False)],
      evidence_manifest=dict(path=manifest_rel,sha256=sha(evidence/"manifest.json"),files=len(entries)),
      decision=dict(current="FREEZE_EXPLICIT_CANDIDATE_FOR_TEAM_USE",default_changed=False,rtl_changed=False,
                    github_uploaded=False,git_commit_created=False,next="Engineering candidate is frozen; no mandatory next optimization. Await user-directed release or one scoped new hypothesis."),
      limits=[row["limits"] for row in matrix["items"]])
    save(A/"record.json",record)
    md="# R5/G5 工程总验收结果\n\n"
    md+=f"完成时间：{finished}；执行者：@cc77-builder / Agent。**选定范围内的工程验收完成，候选已冻结；未上传 GitHub。**\n\n"
    md+="本次没有改生产RTL，也没有新做性能优化。硬件保持0f（O2两槽＋H1低32位结果保存＋DIV取消保持修复）；软件保留已合格firstdot V2四尺寸入口和独立显式C8 8×32入口，公共默认未切换。\n\n"
    md+="## clean-02 墙钟问题的处理\n\n"
    md+="原14项全核的UTC容量检查出现80.119ms表观四路重叠，原FAIL/WALL_CLOCK_LIMITED记录永久保留，未修改时间戳或门槛。按事前合同仅重新执行o2-control-diagnostic，其余13项全部从原始日志重新解析。\n\n"
    md+=f"最终组合14项通过功能、NEMU差分、O2覆盖和负控后同镜像恢复。**13项复用＋1项新执行，不是重跑14项**。选定记录的严格UTC并发峰值为{full['selected_utc_capacity']['peak']}（上限3）；新单进程以同boot/PID的单调时钟包络验证，峰值1，包络{clock['process_envelope_seconds']:.3f}秒。该耗时是宿主审计数据，不用于DUT加速比。\n\n"
    md+=f"新控制诊断检查{new['checked_register_bytes']}字节寄存器结果，退出{new['exit_code']}；独立离线审计再次通过。原13项没有单调时钟记录，不能追溯宣称原批次的实际OS并发已测量。\n\n"
    md+=f"本次UTC间隔与单调包络仍相差{clock['utc_minus_monotonic_seconds']:.6f}秒（UTC更短）。因此墙钟稳定性仍未证实；新占用审计依赖同boot的单调包络，而非容差修正UTC。该现象如实留档，不把旧批次或系统时钟标为已修复。\n\n"
    md+="## 验收矩阵\n\n| 项目 | 状态 | 依据及范围 |\n| --- | --- | --- |\n"
    for row in matrix["items"]:
        md+=f"| {row['id']} | {row['status']} | {row['evidence_summary']}；{row['limits']} |\n"
    md+="\n## 当前可使用的性能结论\n\n"
    md+="C8 8×32完整调用窗口为273 cycles，最快同场RVV为299，**1.095238×**；较firstdot 282.25少3.2772%。这些来自既有4尺寸×3数据集矩阵，本次只是验收和身份复核，没有新增跑分。四路batch128的3.067873×来自另一固定微基准合同，不代表应用端到端收益，不能与1.095238×混为一个总分。\n\n"
    md+="## 已知边界与下一步\n\n"
    md+="1ns STA尚未收敛，功耗、整核Fmax和布线后时序未测；保留真实成本取舍。独立INT16参数扩展不等于生产全核INT16支持。4×8/16×64配置复用控制漂移仍未归因，未纳入新采用项；4×13保留RVV。规格Q01–Q07待官方澄清，团队名称仍待确定；正式报告/PPT/视频和成员复核由团队另行安排。\n\n"
    md+="工程可以以此冻结候选为保底版本，不再为了收尾新增应用或强行优化。后续可由用户安排发布zjhwork、成员复核与比赛材料，或另选一个有明确收益假设的优化。未授权的发布本轮不执行。\n\n"
    md+=f"冻结文件{len(freeze['files'])}项，生产源码398项与0f及clean副本一致。快照在 {O/'frozen-workspace.tar.gz'}，已逐项回读，含工作树文件但不含Git历史和外部依赖。使用/回退见[README](README.md)，逐项身份见[数据记录](record.json)，原始新增证据见[manifest](evidence/manifest.json)。各失败尝试也已封存，没有覆盖旧28条数据档案。\n"
    (A/"RESULT.md").write_text(md)
    ledger["records"].append(record);ledger["last_append_at"]=finished;ledger["last_append_note"]=RECORD
    save(ledger_path,ledger)
    ledger_md=R/"team/docs/version-data-ledger.md"
    with ledger_md.open("a") as f:
        f.write(f"\n\n## 29. R5/G5 冻结与工程总验收（{finished}）\n\n"
                "状态：R5_G5_ENGINEERING_ACCEPTED_WITH_DECLARED_LIMITS。0f＋firstdot V2＋显式C8候选冻结；生产RTL与默认未改，未上传。\n\n"
                "仅新执行o2-control-diagnostic 1次，原13项原文重验；组合功能/差分/O2覆盖及独立原文复算PASS。原clean-02全14项UTC容量FAIL保留；新选择集合严格UTC峰值3、新单进程单调包络峰值1。不是fresh14。\n\n"
                "398生产源码、627个C8输入、31,440字节最终BIN和24,157冻结文件校验；35模型测试、11时钟门禁测试、FU/父级与T15旧归档复算通过。PPA证据审计不等于时序收敛；新性能/PPA/功耗/Fmax均NOT_TESTED。\n\n"
                f"[结果](../optimizations/o2/integration/firstdot-v2-0f/acceptance/RESULT.md) · [完整记录](../optimizations/o2/integration/firstdot-v2-0f/acceptance/record.json)。证据manifest SHA256：{record['evidence_manifest']['sha256']}。旧28条保留。\n")
    # Replace only current route preamble; historical body remains explicitly historical.
    route=R/"team/docs/development-route-current.md";text=route.read_text();index=text.index("\n更新：")
    title=text.splitlines()[0]
    route.write_text(title+"\n\n> 当前本地zjhwork候选：R5/G5工程总验收已完成。固定0f硬件＋firstdot V2四尺寸入口＋显式C8 8×32包；原13＋新1的组合全核/差分及原文审计通过，原clean-02墙钟FAIL保留。生产RTL、公共默认未改，未上传GitHub。\n"
       "> C8性能仍为原矩阵273 vs RVV299 cycles（1.095238×），本轮无新跑分。使用、冻结身份与完整限制见[最终结果](../optimizations/o2/integration/firstdot-v2-0f/acceptance/RESULT.md)。工程收尾已完成，不强制再开应用/优化；后续按用户安排发布、成员复核或另立有界优化。\n"
       "> 下文6d2/T17/R4等记录保留历史规划依据，不覆盖上面的当前0f验收状态。1ns时序未收敛、其他尺寸配置复用未决、官方语义待澄清等限制保持。\n"+text[index:])
    main_result=LEAF/"RESULT.md";text=main_result.read_text()
    main_result.write_text("> 当前最终状态：R5/G5工程验收完成，0f＋firstdot V2＋显式C8候选已冻结。原13＋新1组合全核与审计PASS，旧14墙钟FAIL不改写；未上传。见[最终结果](acceptance/RESULT.md)。以下为各阶段历史记录，旧“下一步”不再驱动当前任务。\n\n"+text)
    with (R/"开发计分板.md").open("a") as f:
        f.write(f"\n\n## R5/G5 冻结候选与总验收 — {RECORD}\n\n"
                f"- 时间：{freeze['created']} 至 {finished}；@cc77-builder / Agent；本地执行。\n"
                "- 工作：固定0f＋firstdot V2和显式C8，不改RTL；冻结24157文件并创建可回读快照。仅补控制诊断1进程，原13项重新解析，通过功能/差分/O2覆盖和独立审计；新UTC/单调时钟证据闭合所选组合，旧全14项墙钟FAIL保留。\n"
                "- 验证：35模型、11时钟门禁测试，398生产源码身份、627C8输入/最终镜像，FU/父级原文、T15原冻结环境和1008成本载荷审计通过。4次前置/环境检查拒绝保留，均0新EMU；未放宽门槛。\n"
                "- 取舍：工程所选范围验收完成；1ns负slack、功耗/Fmax未测、非目标尺寸未决、官方语义待答与人工事务不冒称通过。本轮无新性能，未提交或推送。\n"
                "- 证据：[最终结果](team/optimizations/o2/integration/firstdot-v2-0f/acceptance/RESULT.md)、版本档案第29条；外部r5-g5-acceptance-01。\n"
                "- 接续：已完成工程收尾；按用户后续安排发布zjhwork或另选单个有收益假设的优化，不自动扩大工程范围。\n")
    # Mechanical append/identity checks after documentation updates.
    after=read(ledger_path)
    need(after["records"][:-1]==before["records"] and len(after["records"])==29,"ledger preservation")
    need(ledger_md.read_text().startswith((nav/"team/docs/version-data-ledger.md").read_text()),"markdown history changed")
    for rel,digest in freeze["files"].items():need(sha(R/rel)==digest,"post frozen drift: "+rel)
    check=subprocess.run(["git","diff","--check"],cwd=R,capture_output=True,text=True)
    need(check.returncode==0,check.stdout+check.stderr)
    save(A/"final-qa.json",dict(status="R5_G5_FINAL_LOCAL_QA_PASS",finished=finished,
      frozen_files=len(freeze["files"]),prior_ledger_records_preserved=28,total_ledger_records=29,
      new_emu_runs=1,selected_fullcore_runs=14,new_raw_audit="PASS",source_identity="PASS",
      archive_files=len(entries),archive_sha256=sha(evidence/"manifest.json"),github_writes=False,
      git_commit_created=False,production_rtl_changed=False,new_performance="NOT_TESTED",new_ppa="NOT_TESTED"))
    print(json.dumps(read(A/"final-qa.json")))

if __name__=="__main__":main()
