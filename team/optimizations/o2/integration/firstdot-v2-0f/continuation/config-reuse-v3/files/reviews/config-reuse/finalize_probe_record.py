"""Append the actual bounded probe result; never edit historical records."""
import json,hashlib,copy,collections
from pathlib import Path
from datetime import datetime,timezone
W=Path("/home/riscv/riscv-lab/software-import-20261026")
M=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
D=W/"reviews/config-reuse";O=W/"config-reuse-clean02-02"
A=W/"reviews/config-reuse-final-archive-01"
def read(p):return json.loads(Path(p).read_text())
def pin(p):
    p=Path(p);return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
def save(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
def main():
    state=read(O/"state.json");result=read(O/"run-01/results.json");audit=read(O/"audit-02.json");completion=read(O/"completion-02.json")
    assert completion["status"]=="PROBE_V3_RUNTIME_AND_FIXED_READONLY_AUDIT_PASS"
    assert read(W/"config-reuse-audit-fix-01.command.json")["exit_code"]==0
    assert result["functional_status"]==audit["functional_status"]=="FUNCTIONAL_PASS"
    assert audit["status"]=="PROBE_LOCAL_RAW_AUDIT_PASS" and result["performance"]==audit["performance"]
    assert result["new_emu_runs"]==5 and result["measured_windows"]==32 and audit["normal_all_windows"]==96
    assert read(O/"identity-before.json")==read(O/"identity-after-02.json")
    assert read(A/"verification.json")["raw_and_stored_readback"] is True
    processes=[]
    for run,selected in [(W/"config-reuse-clean02-01/run-01",False),(O/"run-01",True)]:
        for path in sorted((run/"runs").glob("*/result.json")):
            v=read(path);processes.append(dict(selected=selected,status=v["status"],exit_code=v["exit_code"],receipt=pin(path)))
    assert len(processes)==7 and sum(x["selected"] for x in processes)==5
    assert collections.Counter(x["exit_code"] for x in processes)=={0:5,1:2}
    images=read(O/"build-01/images.json")["images"]
    old=read(W/"config-reuse-clean02-01/build-01/images.json")["images"]
    assert {x["variant"]:x["image_sha256"] for x in images}=={x["variant"]:x["image_sha256"] for x in old}
    perf=result["performance"];row=result["rows"][0]
    assert row["shape"]==[8,32] and row["datasets"]==[0]
    decision=perf["decision"]
    replay_ok=read(O/"run-01/state.json")["all_window_replay"]
    baseline_ok=not any("identical current qualified firstdot BIN" in x for x in perf["unexplained_controls"])
    action=("KEEP_FOR_EXPANDED_VALIDATION_ONLY" if decision=="PERFORMANCE_CANDIDATE" else "DO_NOT_ADOPT_PENDING_NEW_HYPOTHESIS")
    now=datetime.now(timezone.utc).isoformat()
    record=dict(record_id="CONFIG-REUSE-DIVFIX0F-CLEAN02-20261027-01",
      status="FUNCTIONAL_RAW_AUDIT_PASS_"+decision,candidate="redundant vector configuration elimination after firstdot",
      baseline="same clean EMU and freshly rebuilt firstdot",source_commit="c823a8786e052c6e26f6915563c42b6d730dd8e3",
      selected_hardware_commit="0f12df675378556670afd0dd2153f47fcb330610",
      source_import=dict(upstream="fcf4a11fc569cb2a8fcb4e18d96ec2764b228557",new_files=26,verify_only_dependencies=39,manifest=pin(D/"adapter-v3/import-manifest.json")),
      contract=read(O/"run-01/state.json")["contract"],contract_file=pin(D/"adapter-v3/CONTRACT.md"),
      adapter_sources={p.name:pin(p) for p in (D/"adapter-v3").glob("*.py")},
      hardware_identity=pin(W/"clean-02/identity/current.json"),configuration=read(O/"run-01/configuration.json"),
      baseline_clean_record="CLEAN-FIRSTDOT-V2-DIVFIX0F-20261027-01",images=images,
      comparison=dict(shape=[8,32],datasets=[0],variants=["firstdot","config-reuse"],
        same_hardware_and_inputs=True,same_complete_BIN=False,fixed_link_layout_and_call_plan=True,
        c_abi_call_and_return_included=True,overhead_subtraction=False,formal_samples_per_cell=4,
        formal_windows=32,normal_windows_including_replay=96,full_replay_window_pairs=48,
        firstdot_against_qualified_clean_same_BIN_windows=24,default_changed=False),
      execution=dict(actual_started_processes=7,selected_qualified_processes=5,
        excluded_V2_tool_failure_processes=2,interrupted_processes=0,actual_exit_counts={"0":5,"1_expected_negative":2},
        old_runtime_verdicts_reused=0,processes=processes,stages=state["stages"],
        pipeline_receipt=pin(W/"config-reuse-v3-pipeline-01.command.json"),completion_receipt=pin(W/"config-reuse-audit-fix-01.command.json"),completion=pin(O/"completion-02.json")),
      verification=dict(static_GNU_pair="PASS",NEMU_full128_and_O2_protocol="PASS",negative_bit100_recovery="PASS",
        all_48_replay_window_pairs="PASS" if result["status"]!="FAILED" and read(O/"run-01/state.json")["all_window_replay"] else "FAIL",
        independent_local_raw_audit="PASS",physical_identity_before_after="PASS", firstdot_same_BIN_24_window_control="PASS" if baseline_ok else "FAIL",
        host_tests="PASS_61_ADAPTER_PLUS_2_REAL_CAMPAIGN_AUDIT_SCOPE",full_multi_shape_dataset_matrix="NOT_TESTED",ordinary_public_C_application="NOT_TESTED",
        new_RTL_FU_parent="NOT_TESTED",new_area_STA="NOT_TESTED",power="NOT_TESTED",member_manual_reproduction="NOT_TESTED"),
      metrics=row,performance=perf,decision=action,adopted=False,
      production_RTL_changed=False,stable_default_changed=False,github_pushed=False,
      failed_attempts=[dict(attempt="V3 audit-01 and pipeline",status="FAILED_PRESERVED",new_target_runs=0,
        cause="Audit loop variable before shadowed initial physical identity tuple with a process dict; final comparison necessarily failed.",
        repair="New separately hash-bound read-only auditor renames two loop variables; unchanged identity/chronology/raw conditions. Actual complete campaign PASS plus deliberate final identity drift rejection test PASS.",
        old_frozen_runtime_sources_unchanged=True,old_target_receipts_unchanged=True,
        receipt=pin(O/"audit-01.command.json"),completion=pin(O/"completion-02.json")),
        dict(attempt="V2 config-reuse-clean02-01",pipeline_status="FAILED",actual_started=2,
        normal_target_exit=0,normal_uart_failures=0,runtime_qualification="FAILED_LOADED_IMAGE_MISMATCH",
        cause="Comparison BIN was in shared single-process files, legacy checker treated every /vdot-perf.bin as loaded.",
        repair="V3 binds loaded image only in per-run map, retains/checks comparison BIN in full shared closure before/after every run and independent audit.",
        original_receipts_unchanged=True,old_result_not_promoted=True,
        evidence=pin(W/"config-reuse-clean02-01/run-01/state.json")),
        dict(attempt="V3 host tests01",status="FAILED_2_FAILURES_1_ERROR",cause="Test harness imported historical and clean canonical modules in same process; fixed via isolated diagnostic subprocess. Runtime adapter unchanged.",
        receipt=pin(D/"adapter-v3-tests-01.command.json"),superseding_tests=pin(D/"adapter-v3-tests-02.command.json"))],
      evidence_manifest=pin(A/"manifest.json"),archive_verification=pin(A/"verification.json"),
      raw_audit=pin(O/"audit-02.json"),fixed_readonly_auditor=pin(D/"audit-scope-fix-v1/raw_audit_fixed.py"),audit_repair_review=pin(D/"audit-scope-fix-v1/ROOT_REVIEW.json"),root_execution_review=pin(D/"ROOT_REVIEW.image-scope-v3-01.json"),
      limits=["Only 8x32/dataset0/endtoend-C-ABI screening, four formal samples/cell; not 3-dataset/4-shape qualification or statistical population inference.",
        "Two candidate BINs differ; same hardware, data, link slots and call plan, not a same-complete-image comparison.",
        "Independent raw reparse requires original physical inputs; archive readback is not portable standalone reproduction.",
        "No default/public API selection switch. 4x13 retains qualified RVV fallback.",
        "New RTL/PPA/STA/power/LLM end-to-end performance and contest score NOT_TESTED."],finished=now)
    final=D/"final-result-01";assert not final.exists();final.mkdir()
    save(final/"record.json",record)
    j=M/"team/docs/version-data-ledger.json";md=M/"team/docs/version-data-ledger.md"
    oldj=read(j);oldmd=md.read_bytes()
    assert len(oldj["records"])==23 and all(x.get("record_id")!=record["record_id"] for x in oldj["records"])
    (final/"ledger-before.json").write_bytes(j.read_bytes())
    (final/"ledger-before.md").write_bytes(oldmd)
    new=copy.deepcopy(oldj);new["records"].append(record);new["last_append_at"]=now;new["last_append_note"]="Record24: bounded configuration reuse, preserve V2 tool failure, no defaults/RTL switch."
    save(j,new)
    lines=["\n## 14. 配置复用有界筛选：CONFIG-REUSE-DIVFIX0F-CLEAN02-20261027-01",
      "",f"第24条。结果：**{decision}**；功能与原文复算PASS。限定8×32/dataset0/C ABI完整调用窗，每格4正式样本。候选BIN不同，硬件、数据、布局和调用计划相同；不称同完整镜像比较。",
      "", "| 方法 | firstdot平均cycles | 配置复用平均cycles | 退休指令(firstdot→配置复用) |","| --- | ---: | ---: | --- |"]
    lookup={(r["variant"],r["software"],r["method"]):r for r in row["candidates"]}
    for sw,method in [("basic","vdot"),("reuse","vdot"),("basic","rvv"),("reuse","rvv")]:
        a=lookup[("firstdot",sw,method)];b=lookup[("config-reuse",sw,method)]
        lines.append(f"| {sw} {method} | {a['mean']:.2f} | {b['mean']:.2f} | {a['instructions']} → {b['instructions']} |")
    lines+=["",f"reuse vdot相对firstdot减少{perf['reduction_vs_firstdot']*100:.6f}%；相对本次最快RVV减少{perf['reduction_vs_fastest_rvv']*100:.6f}%，RVV/vdot={perf['fastest_current_rvv_total']/perf['candidate_total']:.6f}×。",
      f"未解释对照项：{perf['unexplained_controls']}。功能与性能结论分开；决策：{action}，本次不扩大矩阵、不切stable默认、不推送。",
      "", f"实际7个目标进程：V2的2个保留并排除，V3新5个功能通过；5次正常exit0、2次预期负控exit1。选用V3的32正式窗口、含重放96窗口、48对全窗口重放（一致={replay_ok}）；firstdot24窗口与原干净合格对照一致={baseline_ok}。高位bit100拒错及正常恢复、NEMU完整128位结果、CSR与O2生命周期均PASS。",
      "", "V2停止原因是对照BIN被工具误作实际加载BIN，正常目标exit0且UART failures=0，不能因此把原失败验收改为PASS。V3只修复测试适配层，保留共享对照哈希校验；61项主机检查PASS，含真实旧日志失败复现及错误镜像/篡改拒绝。原失败原样封存。",
      "", "V3首次独立审计又因循环变量遮蔽物理身份而误报；原失败保留。独立新审计器仅重命名两个循环变量，真实完整批次成功及模拟最终身份漂移仍拒绝两项检查PASS。新audit-02及completion-02通过，全程不新增EMU；冻结运行源码和旧日志不改。",
      "", "候选来源zufan fcf4a11的26文件＋39相同依赖；新适配器V3及执行器独立绑定。生产RTL仍0f；全核默认选择未变。新多形状/多数据集矩阵、普通公共C应用、面积/STA/功耗、成员人工复现均NOT_TESTED。4×13继续RVV回退。",
      "",f"本地原始输出：{O}。封存manifest：{record['evidence_manifest']['sha256']}；原文审计及所有版本/镜像/配置/命令/实测数值见配套JSON。档案验证仅为字节封存，原文复算仍依赖本地物理输入。",""]
    block="\n".join(lines);md.write_bytes(oldmd+block.encode())
    assert read(j)["records"][:-1]==oldj["records"] and md.read_bytes().startswith(oldmd)
    (final/"RESULT.md").write_text("# 配置复用限定筛选结果\n"+block)
    save(final/"append-verification.json",dict(status="RECORD24_APPENDED_OLD23_UNCHANGED",record=pin(final/"record.json"),json=pin(j),markdown=pin(md)))
    print(json.dumps(dict(status=record["status"],decision=action,metrics=perf),ensure_ascii=False))
if __name__=="__main__":main()
