"""Write engineering handoff only after the real strict G3 audit passes."""
import json,hashlib,re
from pathlib import Path
from datetime import datetime,timezone
r=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
w=Path("/home/riscv/riscv-lab/o2-fullcore-20261019")
read=lambda p:json.loads(p.read_text())
audit=read(w/"recheck-02/result.json")
assert audit["status"]=="O2_G3_OFFLINE_RECHECK_PASS" and audit["g3_complete"] and audit["whole_suite_pass"]
assert audit["normal_reference_recovery"] and audit["original_evidence_unchanged"]
core=read(w/"core-02/result.json");supp=read(w/"supplements-02/result.json")
assert core["status"]=="O2_CORE_REGRESSION_PASS" and supp["status"]=="O2_SUPPLEMENTS_PASS"
records=core["runs"]+supp["runs"]
normal=[x for x in records if x["name"]!="negative-vdot"]
assert len(records)==14 and len(normal)==13
assert all(x["observation_status"]=="O2_TRACE_PASS" and x["exit_code"]==0 for x in normal)
total=sum(x["observation_counts"].get("COMMIT",0) for x in normal)
assert total==5378
# Do not publish the old witness's cycles/identities as a new observation.
normalized=[re.sub(r"\s+","",line) for line in (w/"supplements-02/o2-control-diagnostic/stderr.log").read_text().splitlines()]
for prefix in [
    "O2_KILLcycle=609217seq=1741slot=Prob=1:2pdest=49redirect=0:43self=0",
    "O2_RESPONSEcycle=609217seq=1740rob=0:41pdest=14illegal=0data=0x000000000000000000000000ffffe421",
    "O2_COMMITcycle=609283rob=0:41pc=0x0000080002978ftq=1:2",
]:
    assert sum(line.startswith(prefix) for line in normalized)==1, ("final witness changed",prefix)
coverage=audit["suite_coverage"]
assert coverage["complete"] and not coverage["missing"] and len(coverage["required"])==6
assert all(coverage["sources"][k] for k in coverage["required"])
summary=dict(status="O2_G3_COMPLETE",created_utc=datetime.now(timezone.utc).isoformat(),
    campaigns=["core-02","supplements-02"],strict_recheck="recheck-02",
    jobs=14,normal_jobs=13,intentional_negative_jobs=1,vdot_commits=total,
    unique_matrix_cases=117,matrix_executions=124,matrix_vdot_commits=87,
    host_tests=95,coverage=coverage,build_source_commit=audit["build_source_commit"],
    core_tool_commit=audit["original_source_commit"],supplement_tool_commit=read(w/"supplements-02/preflight.json")["tool_source_commit"],
    emu_sha256=audit["emu_sha256"],performance_measured=False,github_pushed=False,
    raw_streams_rechecked=True,formal_T16_report_written=False,
    original_failed_supplements_retained="supplements-01",
    original_failed_recheck_retained="recheck-01",
    recheck_sha256=hashlib.sha256((w/"recheck-02/result.json").read_bytes()).hexdigest())
(w/"final-summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
rows=[]
labels={"MULTI_INFLIGHT":"两槽同时占用","TRIPLE_OVERLAP":"响应／移动／接受同拍","FULL_STALL":"满槽输出反压","KILL_P":"P槽取消","KILL_R":"R槽取消","PARTIAL_KILL":"只取消一槽、另一槽幸存"}
for key in coverage["required"]:
    sources=coverage["sources"][key]
    rows.append("| "+labels[key]+" | "+str(sum(x["count"] for x in sources))+" | "+"；".join(x["name"]+"："+str(x["count"]) for x in sources)+" |")
table="\n".join(["| 实际覆盖 | 合计事件数 | 合格来源 |","| --- | ---: | --- |"]+rows)
head=f"""# O2 G3 全核验证工程入口

**G3 自动验收及严格离线重审已通过，本地保存，未推送 GitHub。** 完成时间：{audit["finished"]}。正式 T16 报告继续后置。

本轮用新的 O2 MinimalConfig 单核 EMU 完成原十二项回归与两项补充诊断。最终合格集合为 core-02＋supplements-02；recheck-02 从原始 stdout/stderr、退出码、输入、Git blob 和真实硬件身份重新计算，结果 O2_G3_OFFLINE_RECHECK_PASS。首轮 supplements-01/recheck-01 失败保持原样，不能混入最终合格覆盖。

## 实际结果

- 14 项作业满足各自预期：13 项正常完整通过，1 项 bit100 故障参考库被 DiffTest 精确拒绝；同镜像换回正常库后完整恢复通过。
- 原矩阵为117个唯一用例（80合法、37异常），8分片执行124次，87条合法vdot提交。原F2v独立满足七项控制覆盖，dense独立完成十二窗口并覆盖两槽并发与三事件同拍。
- 最终合格正常程序共 **5378条vdot提交**：原十二项3012，修正后诊断1158，控制补充1208；全部完整128位及身份/元数据审计通过，没有未终结FU/DIV/ROB事务。
- 新诊断检查10×512＝5120字节寄存器状态与每病例7项CSR；控制补充检查256×512＝131072字节寄存器状态及最终CSR集合。
- 实际VFEX4接受序列覆盖vdot/VIDiv/VFDiv全部9种相邻类型组合，末段各6条；12条DIV全部正常完成。日志直接绑定6条vdot的PC/word；DIV日志没有逐条动态PC/word，不扩大该项观察主张。
- 六个独立固定工作量病例共观察到735次连续1拍接受、768次2拍响应；这是本轮协议覆盖，不是公平性能或应用加速比。
- 最终主机测试79＋16＝95项通过。主机负控、真实bit100差分注入与真实RTL/全核运行分别记录，不混为一类。

## 新的全核覆盖

{table}

最小部分取消窗口为控制补充中的周期609217：P请求seq1741取消，R请求seq1740同拍响应并在609283提交，完整128位结果为0x000000000000000000000000ffffe421。须以最终合格supplements-02原始轨迹及离线复核为准；live-observer-check-10核验最终合格原流，09保留首轮同镜像独立审查，身份与来源保持区分。全核运行期reset未注入，反向年龄等G1/G2覆盖不能自动移算为本轮全核覆盖。

## 版本与复现

| 身份 | 固定值 |
| --- | --- |
| 本地工作分支 | local/o2-fullcore-20261019 |
| G1/G2基点 | 901687a478370c829865ad42cf25183938532de5 |
| 真实硬件构建源码 | {audit["build_source_commit"]} |
| core-02运行工具 | {audit["original_source_commit"]} |
| supplements-02运行工具 | {summary["supplement_tool_commit"]} |
| EMU SHA-256 | {audit["emu_sha256"]} |
| ISA | vdot-s8x8-r32-v0.1，SEW8/VL8/VLEN128 |

使用O2_ELASTIC=1、O1_HANDOFF=0、T14_FUSED_INPUT=1、O2_TRACE=1、O1_TRACE=0、T12_TRACE=0、T13_TRACE=1，实际环境变量均带VDOT_前缀。默认O2开关仍为0。构建使用两编译线程、12GiB JVM，EMU单线程，最多同时两个EMU。

[观察协议](SCHEMA.md) · [工作负载及修复](WORKLOADS.md) · [复跑与离线核验](REPRODUCE.md) · [封存证据](../evidence/20261019-fullcore-validation/README.md)

工作输出：/home/riscv/riscv-lab/o2-fullcore-20261019。文档与归档工具提交不等于新硬件构建。

## 保留的失败及修正

1. build-01主动中止；build-02遇到Chisel子模块观察节点可见性错误。修复只读tap及reset观察方式，真实VFEX4 elaboration后build-03成功，功能控制未因此改动。
2. core-01首屏空R槽的原始ROB索引为63，旧检查器误将无效槽当作活跃请求。修复仅允许无效槽保存6位原值，有效请求仍严格0..47；主动中断记录保留。
3. supplements-01的第十诊断病例因SEW8的vmv.x.s提取宽度与生成器signed32常数不符，产生非法VL16并双重异常。修复仅六个AVL常数，原黄金寄存器/算术结果、前九病例与1158提交数不变；新的逐指令主机模型及实际ELF审计均检查8/32位符号扩展。
4. 同一错误日志同时出现CRITICAL ERROR、GOOD TRAP与退出码0；旧完整病例门禁已拒绝该运行。新增O2原始日志致命错误门禁，明确拒绝critical/double trap/PMA错误，保留bit100预期负控。
5. 现有原core十二项日志未重跑、未修改，由recheck-02重算；两项补充在新工具下重跑。首次集成测试桩缺新helper的失败与后续95项通过回执均保留。

## 完成边界与下一步

本轮完成G3功能、异常、控制和观察器验证；**尚无O2公平加速比、PPA或最终采用结论**。下一项是G4同镜像O1/O2公平性能比较，须使用冻结镜像、各自实测RVV及原样本规则；本次未执行。O3应用、O4时序/结构、O5/T17独立复现和两名成员人工ACK仍待完成，不代签。正式T16报告待工程结束后集中编写。

归档保存原始字节与失败历史，便携审计只复算字节及13份完整/1份故障部分轨迹，不在Windows重新执行EMU，不替代Linux输入来源和全部架构用例审计。
"""
(r/"team/optimizations/o2/fullcore/README.md").write_text(head,encoding="utf-8")
title="## 当前进度：O2 G3 全核自动验收通过，下一步 G4\n\n"
para="2026-10-19，新O2全核EMU的原十二项与两项补充验证已满足预期；117唯一矩阵、bit100差分拒错/正常恢复、原F2v七项、dense十二窗口及六项两槽覆盖均通过，正常程序共5378条vdot提交。95项主机检查及原始日志严格离线重审通过。见 [全核工程入口](team/optimizations/o2/fullcore/README.md) 与 [封存证据](team/optimizations/o2/evidence/20261019-fullcore-validation/README.md)。\n\n本轮仅本地保存，未推送；O2默认关闭。下一步G4公平O1/O2性能对比，本轮没有新增加速比/PPA/最终采用或人工ACK结论，T16报告继续后置。\n\n"
p=r/"OPTIMIZATION.md";s=p.read_text();s=s.replace("# 后续优化开发入口\n\n","# 后续优化开发入口\n\n"+title+para,1).replace("## 当前进度：O2 G1/G2 已完成，下一步 G3","## 前一轮：O2 G1/G2 完成时的进度",1);p.write_text(s)
p=r/"team/optimizations/o2/README.md";s=p.read_text();s=s.replace("# O2 开发入口\n\n","# O2 开发入口\n\n**2026-10-19：G3全核自动验收与严格离线重审通过。** 14项作业满足各自预期，正常程序5378条vdot提交，六项新覆盖完整；见 [全核工程入口](fullcore/README.md) 和 [证据](evidence/20261019-fullcore-validation/README.md)。下一步G4公平性能；尚无O2加速比或PPA，默认关闭，本地保存未推送，T16报告后置。\n\n以下为G1/G2完成时的历史说明。\n\n",1);p.write_text(s)
p=r/"AGENTS.md";s=p.read_text();s=s.replace("# 团队 Agent 入口\n\n","# 团队 Agent 入口\n\n## 当前状态：O2 G3 已通过，本地保存\n\n2026-10-19，local/o2-fullcore-20261019。先读team/optimizations/o2/fullcore/README.md与evidence/20261019-fullcore-validation/README.md。最终合格集合core-02＋supplements-02；recheck-02严格离线重审通过。14项作业满足各自预期，5378正常vdot提交，六项两槽全核覆盖齐全，95主机测试通过；失败尝试保留。不要重跑已完成campaign或改密封证据。G3完成不授权自动G4、push或切换默认模式；没有O2公平性能/PPA/人工ACK，正式T16继续后置。下面各节保留历史时点。\n\n",1);p.write_text(s)
print(json.dumps(dict(status=summary["status"],vdot_commits=total,coverage=coverage),ensure_ascii=False))
