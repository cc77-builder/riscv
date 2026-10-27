from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json,hashlib
W=Path("/home/riscv/riscv-lab/software-import-20261026")
HERE=Path(__file__).resolve().parent
OUT=W/"config-reuse-expanded-01"
ARCH=W/"reviews/config-reuse-expanded-final-archive-01"
DEST=HERE/"final"
def read(p):return json.loads(p.read_text())
def pin(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
assert read(HERE/"pipeline-02.command.json")["exit_code"]==0
assert read(OUT/"completion.json")["status"]=="EXPANDED_MATRIX_AND_RAW_AUDIT_PASS"
audit=read(OUT/"audit-01.json");result=read(OUT/"run-01/results.json")
state=read(OUT/"run-01/state.json");identity=read(W/"clean-02/identity/current.json")
archive=read(ARCH/"manifest.json")
assert audit["actual_target_processes"]==33 and archive["actual_target_processes"]==33
assert not DEST.exists();DEST.mkdir()
receipts=[]
for p in sorted((OUT/"run-01/runs").glob("*/result.json")):
 r=read(p)
 receipts.append(dict(label=r["label"],status=r["status"],exit_code=r["exit_code"],pid=r["pid"],
    image=r["name"],image_sha256=r["image_sha256"],reference=r["reference"],
    monotonic=r["monotonic"],raw_sha256=r["raw_sha256"],receipt=pin(p)))
assert len(receipts)==33 and len({r["pid"] for r in receipts})==33
assert Counter(r["exit_code"] for r in receipts)=={0:32,1:1}
record=dict(record_id="CONFIG-REUSE-MATRIX-DIVFIX0F-CLEAN02-20261027-01",
 status="FUNCTIONAL_AND_RAW_AUDIT_PASS_PER_SHAPE_DECISIONS",
 recorded_at=datetime.now(timezone.utc).isoformat(),
 previous_probe_record="CONFIG-REUSE-DIVFIX0F-CLEAN02-20261027-01",
 baseline_clean_record="CLEAN-FIRSTDOT-V2-DIVFIX0F-20261027-01",
 contract=result["contract"],contract_file=pin(HERE.parent/"expansion-v1/CONTRACT.md"),
 source_commit=identity["source_commit"],selected_hardware_commit="0f12df675378556670afd0dd2153f47fcb330610",
 hardware_identity=pin(W/"clean-02/identity/current.json"),configuration=identity["configuration"],
 hardware_profile=identity["hardware_profile"],images=read(OUT/"build-01/images.json")["images"],
 source_pins=read(HERE/"review-02.json")["frozen_files"],
 comparison=dict(shapes=[[4,8],[8,32],[16,64],[4,13]],datasets=[0,1,2],variants=["firstdot","config-reuse"],
  same_hardware_and_inputs=True,same_complete_BIN=False,fixed_link_layout_and_call_plan=True,
  c_abi_call_and_return_included=True,overhead_subtraction=False,formal_samples_per_shape_cell=12,
  formal_samples_per_dataset_cell=4,formal_windows=384,normal_windows_including_replay=768,
  full_replay_window_pairs=192,firstdot_against_qualified_clean_same_BIN_windows=288,
  dataset_definitions={"0":"alternating INT8 boundaries and mixed signed/zero matrix",
   "1":"deterministic signed modular sequences","2":"seeded random INT8; seed=0x20261019+m*1009+k"}),
 execution=dict(actual_started_processes=33,qualified_normal_processes=32,expected_negative_processes=1,
  interrupted_processes=0,old_probe_processes_reused=0,processes=receipts,
  stages={n:pin(OUT/(n+".command.json")) for n in ["build","run","audit"]},
  cpu_affinity=state["cpu_affinity"],workers=state["workers"],monotonic_proof=state["monotonic_proof"]),
 host_tests=dict(passed=92,receipt=pin(HERE/"host-tests-02.command.json"),
  earlier_88_pass=pin(HERE/"host-tests.command.json"),
  excluded_launch=pin(HERE/"pipeline.command.json"),
  excluded_launch_reason="late test-only additions rejected by frozen source lock before output/build/EMU",
  earlier_host_failures="H03 JSON integer/string decision key mismatch retained in TEST_REVIEW.md; fixed before target execution"),
 metrics=result["summary"],performance=result["decisions"],
 verification=dict(functional="PASS",full128_live_DiffTest="PASS",raw_audit="PASS",
  all_window_replay=result["all_window_replay"],baseline_firstdot_controls=audit["firstdot_controls"],
  final_physical_identity_unchanged=True,evidence_byte_archive="PASS",
  new_RTL_FU_parent="NOT_TESTED",new_area_STA_power="NOT_TESTED",
  expanded_ordinary_public_C_application="NOT_TESTED",member_manual_reproduction="NOT_TESTED"),
 decision=dict(stable_default_changed=False,production_rtl_changed=False,github_uploaded=False,
  candidate_shapes=[s for s,d in result["decisions"].items() if d["decision"]=="PERFORMANCE_CANDIDATE"],
  next_step="8x32 ordinary public C qualification; 4x8/16x64 read-only control-drift attribution; 4x13 retain existing RVV. No stable default switch."),
 evidence={n:pin(p) for n,p in {
  "build":OUT/"build-01/matrix-build.json","run":OUT/"run-01/results.json","raw_audit":OUT/"audit-01.json",
  "completion":OUT/"completion.json","identity_after":OUT/"identity-after.json",
  "archive_manifest":ARCH/"manifest.json","runtime_inputs":OUT/"run-01/runtime-inputs.json",
  "root_review":HERE/"review-02.json"}.items()},
 limitations=["Current fixed MinimalConfig and deterministic 3-dataset complete C-ABI windows only.",
  "Per-shape/per-dataset decisions; no pooled overall speedup or statistical significance claim.",
  "Software images differ; hardware/data/layout/call plan are fixed.",
  "Monotonic Popen/wait envelopes conservatively prove capacity, not exact OS scheduling overlap.",
  "Raw audit depends on pinned local physical files; archive readback is not portable rebuild.",
  "No new RTL, ordinary public C application, area, STA, power, or member manual validation.",
  "Prior clean fullcore UTC capacity anomaly remains historical; this new run uses monotonic envelopes."])
record["source_import"]=dict(upstream="fcf4a11fc569cb2a8fcb4e18d96ec2764b228557",new_files=26,
 verify_only_dependencies=39,manifest=pin(HERE.parent/"adapter-v3/import-manifest.json"))
record["control_drift_analysis"]=pin(HERE/"control-drift-analysis.json")
record["formal_control_input_snapshot"]=pin(HERE/"formal-24-receipts.json")
record["static_instruction_removals"]={}
for image in record["images"]:
 if image["variant"]=="config-reuse":
  manifest=read(Path(image["path"])/"data/manifest.json")
  record["static_instruction_removals"][image["name"]]={
   row["software"]+"/"+row["method"]:len(row["config_reuse_proof"]["removed"]) for row in manifest["rows"]}
(DEST/"record.json").write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n")
lines=["# 配置复用：四尺寸、三数据集扩展结果","",
"本轮在当前 O2 + H1 + DIV 取消保持修复（0f）硬件上，比较 firstdot 与配置复用软件。24 个新镜像、33 个新目标进程已完成；功能、全128位结果、NEMU差分及原文审计通过。各尺寸的性能采用结论见下表，稳定入口尚未切换。","",
"## 比较口径","",
"- 尺寸为矩阵 M×K，分别为4×8、8×32、16×64、4×13；输入为有符号INT8，K=13保留真实尾部处理成本。",
"- dataset0覆盖INT8极值、正负和零；dataset1为固定模运算序列；dataset2为固定种子的随机数据。",
"- 完整C ABI调用窗口包含调用/返回、配置、装载、计算和存储，不扣空测开销。相同硬件、数据、布局和计划，软件BIN不同。",
"- 每个尺寸的每个比较格含12个正式样本（3组数据各4次）。同时保留首次/预热以及dataset0独立重放。",
"- 比较对象包含firstdot/config-reuse × basic/reuse × vdot/RVV八格；RVV分母使用本轮最快的合格格。","",
"## 各尺寸结果","",
"| 尺寸 | firstdot reuse vdot cycles | 配置复用 reuse vdot cycles | 最快RVV cycles | 比firstdot减少 | RVV/vdot | 判定 |",
"| --- | ---: | ---: | ---: | ---: | ---: | --- |"]
for row in result["summary"]["rows"]:
 shape="x".join(map(str,row["shape"]));d=result["decisions"][shape]
 first=row["firstdot_reuse_vdot"]["mean"];cand=row["config_reuse_vdot"]["mean"];rvv=row["fastest_rvv"]["mean"]
 lines.append(f"| {shape} | {first:.4f} | {cand:.4f} | {rvv:.4f} | {100*(1-cand/first):.4f}% | {rvv/cand:.6f}x | {d['decision']} |")
lines+=["","cycles为完整调用窗口的正式均值。PERFORMANCE_CANDIDATE要求聚合及每组数据均严格快于firstdot和最快RVV，同时无未解释控制漂移或其他格退化；REJECT与INCONCLUSIVE均保留原始数据。","","## 逐数据集（局部指标；最终采用以含控制检查的总体判定为准）","",
"| 尺寸 | 数据集 | firstdot cycles | 配置复用 cycles | 最快RVV cycles | RVV/vdot | 局部指标判定 |",
"| --- | --- | ---: | ---: | ---: | ---: | --- |"]
for shape,d in result["decisions"].items():
 for dataset,v in d["dataset_decisions"].items():
  f,c,r=[v[x]/4 for x in ["firstdot_total","candidate_total","fastest_current_rvv_total"]]
  lines.append(f"| {shape} | {dataset} | {f:.4f} | {c:.4f} | {r:.4f} | {r/c:.6f}x | {v['decision']} |")
 for problem in d["unexplained_controls"]:
  lines.append("\n该尺寸保留的异常："+problem)
lines+=["","## 验证与留档","",
"24个镜像GNU/布局/再生检查通过，12个firstdot对照BIN及ELF装载内容与干净版本一致。实际启动33次：32次正常退出、1次预期bit100负控失败，随后同BIN恢复正常。新轮次未借用旧探针运行。",
"原文审计复核768个正常窗口，其中384个正式窗口；192个重放窗口对、288个firstdot历史同BIN对照窗口分别核对完整sample字典。重放一致性："+str(result["all_window_replay"])+"。",
"并发使用4个CPU，按同boot的单调时钟Popen/wait包络与阶段屏障检查；峰值："+str(state["monotonic_proof"]["peak_conservative_envelopes"])+"。该包络不表示精确操作系统调度重叠。","",
"92项主机测试通过。此前JSON键类型问题在主机组合测试中发现并修复；第一次启动因测试文件仍更新被源码锁拒绝，未构建或启动EMU，该失败回执保留。",
"原始证据归档逐文件回读通过："+str(archive["count"])+"项，manifest SHA256："+pin(ARCH/"manifest.json")["sha256"]+"。这不是新的便携环境重建。",
"固定版本、配置、24个镜像哈希、33个进程身份、全部32个比较格和逐数据集判定保存在record.json。","",
"## 当前选择与下一步","",
"本轮只完成数据集与尺寸扩展；生产RTL、默认入口和GitHub未改动。普通公共C应用路径尚未为配置复用版新增验证，面积/STA/功耗也没有新测量。",
"8×32优先补普通公共C调用路径验证；4×8和16×64先做只读控制差异归因，4×13保留既有较优RVV路径。相关门禁闭合后再考虑稳定入口。",
"只读复核确认12个firstdot镜像的288个完整样本与干净基线一致；15个未改动RVV控制格的完整8 KiB槽位逐字节相等。4×8、16×64、4×13的部分控制窗仍有周期差异，其微架构原因尚未确认，不能把它们当作噪声删除或放宽门禁。","",
"原始工作目录："+str(OUT),"","完整数据档案记录ID："+record["record_id"]]
(DEST/"RESULT.md").write_text("\n".join(lines)+"\n")
print(json.dumps(dict(record=record["record_id"],decisions={s:d["decision"] for s,d in result["decisions"].items()})))
