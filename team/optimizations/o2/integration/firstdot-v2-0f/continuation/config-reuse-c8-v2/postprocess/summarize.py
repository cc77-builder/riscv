from pathlib import Path
import json,hashlib,re
from datetime import datetime,timezone
W=Path("/home/riscv/riscv-lab/software-import-20261026")
HERE=Path(__file__).resolve().parent
OUT=W/"config-reuse-c8-02";PRE=W/"reviews/config-reuse/c8-preflight-02"
ARCH=W/"reviews/config-reuse-c8-final-archive-03"
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
state=read(OUT/"state.json");audit=read(OUT/"audit-01.json");runs=read(OUT/"run-01/results.json")["runs"]
receipt=read(PRE/"pipeline.command.json");archive=read(ARCH/"manifest.json")
assert state["status"]=="CURRENT_CONFIG_REUSE_8X32_C_QUALIFIED" and receipt["exit_code"]==0
assert audit["status"]=="CURRENT_CONFIG_REUSE_C_RAW_AUDIT_PASS" and audit["normal_output_replay_equal"] is True
assert len(runs)==3 and [r["exit_code"] for r in runs]==[1,0,0]
assert len(audit["target_cases"])==12 and audit["target_custom_commits_per_normal"]==192
assert read(W/"config-reuse-c8-01/state.json")["new_emu_runs"]==0
assert read(PRE/"host-tests-01.command.json")["exit_code"]==0
assert read(HERE/"physical-after.json")["matches_before"] is True
whole_program=[]
for label in ("recovery","replay"):
 text=(OUT/"run-01/runs"/label/"stdout.log").read_text()
 counters=re.findall(r"instrCnt = (\d+), cycleCnt = (\d+)",text)
 guest=re.findall(r"Guest cycle spent: (\d+)",text)
 assert len(counters)==1 and len(guest)==1
 whole_program.append(dict(run=label,instructions=int(counters[0][0]),cycles=int(counters[0][1]),
  guest_cycles=int(guest[0]),scope="Whole correctness program including startup/scalar checks/UART; not a kernel performance sample"))
matrix=read(W/"reviews/config-reuse/expansion-root-01/final/record.json")
perf=matrix["performance"]["8x32"]
assert perf["samples_per_cell"]==12 and perf["candidate_total"]==3276 and perf["firstdot_total"]==3387 and perf["fastest_current_rvv_total"]==3588
profile=read(OUT/"run-01/hardware-profile.json")
build=read(OUT/"build-01/build.json");manifest=read(OUT/"build-01/source/manifest.json")
record=dict(
 record_id="CONFIG-REUSE-C8-DIVFIX0F-CLEAN02-20261027-02",status="ORDINARY_C_FUNCTIONAL_AND_RAW_AUDIT_PASS",
 recorded_at=datetime.now(timezone.utc).isoformat(),scope="Current 8x32 config-reuse ordinary C in Nexus-AM bare metal; complete16-function fixture retained",
 parent_matrix_record=matrix["record_id"],contract=state["contract"],
 contract_file=ref(W/"reviews/config-reuse/c8-v2/CONTRACT.md"),
 source_commit=matrix["source_commit"],selected_hardware_commit=matrix["selected_hardware_commit"],
 hardware_identity=ref(W/"clean-02/identity/current.json"),
 hardware_profile_file=ref(OUT/"run-01/hardware-profile.json"),
 hardware=dict(emu_sha256=profile["emu_sha256"],nemu_sha256=profile["reference_provenance"]["binary_sha256"],
  configuration="MinimalConfig / one core / EMU_THREADS=1 / VLEN128"),
 configuration=read(OUT/"run-01/configuration.json"),
 input_identities=dict(outer_manifest=ref(OUT/"outer-inputs.json"),runtime_manifest=ref(OUT/"run-01/runtime-inputs.json"),
  build_record=ref(OUT/"build-01/build.json"),source_manifest=ref(OUT/"build-01/source/manifest.json"),
  bin=ref(OUT/"build-01/vdot-perf.bin"),elf=ref(OUT/"build-01/vdot-perf.elf"),
  reference_object=ref(OUT/"build-01/gemv-reference.o"),public_source_qualification=ref(OUT/"qualified-public/qualification.json")),
 comparison=dict(new_cycle_measurement=False,new_performance_samples=0,
  interpretation="Functional C caller only; previous full-call performance matrix is separately identified, not remeasured here.",
  matrix_anchor=ref(OUT/"build-01/current-matrix-anchor.json"),leaf_byte_comparisons=48,target_leaf_comparisons=12,
  case_reordering="8x32 group first; dataset0 reuse vdot first; complete48-case multiset unchanged",
  scalar_oracle="Every output row: low32 signed dot, high96 zero; full16byte result checked in executed C"),
 execution=dict(started_at=receipt["started"],finished_at=receipt["finished"],pipeline_receipt=ref(PRE/"pipeline.command.json"),
  actual_started_processes=3,selected_processes=3,normal_exit0=2,expected_negative_exit1=1,interrupted=0,
  prior_attempt_emu_processes=0,cpu_affinity=[0,1,2,3],max_simultaneous_target_processes=1,
  monotonic=audit["timing"],utc_chronology="PASS_UNMODIFIED_INNER_C_CHECKER",
  runs=[{k:r.get(k) for k in ("negative","replay","pid","exit_code","status","started","finished","command","cwd","reference",
   "image_sha256","current_c_monotonic","negative_details","validation")} for r in runs]),
 host_tests=dict(count=20,status="PASS",receipt=ref(PRE/"host-tests-01.command.json"),
  scope="Real GNU/ELF anchors, exact case table, input pins, real host subprocess forwarding and monotonic rejection tests"),
 metrics=dict(target=dict(shape="8x32",functions=4,datasets=[0,1,2],distinct_cases=12,normal_calls=24,
  custom_commits_per_normal=192,normal_output_bytes_checked=12*8*16*2),
  whole_fixture=dict(functions=16,distinct_cases=48,normal_calls=96,custom_commits_per_normal=manifest["expected_dots"]),
  negative=runs[0]["negative_details"],software_fault_controls=5,replay_equal=True,whole_program_diagnostics=whole_program),
 verification=dict(gnu_build="PASS",linked_model="PASS",ordinary_c_caller="PASS",full128_scalar_outputs="PASS",
  fullcore_difftest="PASS_CURRENT_C_PROGRAM_ONLY",o2_protocol="PASS",negative_recovery="PASS",
  replay="PASS",raw_audit="PASS",physical_identity="PASS",new_full_regression_suite="NOT_TESTED",
  standalone_fu="NOT_TESTED",real_parent="NOT_TESTED",new_cycles="NOT_TESTED",area_sta="NOT_TESTED",power="NOT_TESTED",
  independent_machine_or_human_reproduction="NOT_TESTED",library_packaging="NOT_TESTED",default_switch="NOT_PERFORMED"),
 prior_performance=dict(record_id=matrix["record_id"],source=ref(W/"config-reuse-expanded-01/run-01/results.json"),
  shape="8x32",selected_api="config_reuse_gemv_8x32_reuse_vdot",firstdot_cycles=perf["firstdot_total"]/12,config_reuse_cycles=perf["candidate_total"]/12,fastest_rvv_cycles=perf["fastest_current_rvv_total"]/12,
  speedup=299/273,cycles_reduction_percent=(282.25-273)/282.25*100,formal_samples_per_cell=12,
  measured_in_this_c_program=False),
 decision=dict(current="QUALIFIED_8X32_REUSE_VDOT_ORDINARY_C_CANDIDATE",default_changed=False,hardware_changed=False,
  github_uploaded=False,other_shapes="Functional collateral only; prior INCONCLUSIVE decisions unchanged",
  next="Review stable entry scope; separately attribute4x8/16x64 unchanged-RVV control drift; retain4x13 RVV"),
 preserved_failures=[dict(path=str(W/"config-reuse-c8-01"),status="FAILED_BEFORE_EMU",new_emu_runs=0,
  error="TypeError: spawn wrapper accepted6 positional arguments, compiler helper supplied8",
  resolution="Separate V2 adapter accepts positional and keyword env/timeout; inner checker/hardware unchanged",
  receipt=ref(W/"reviews/config-reuse/c8-preflight-01/pipeline.command.json"))],
 evidence=dict(raw_audit=ref(OUT/"audit-01.json"),physical_after=ref(HERE/"physical-after.json"),
  archive_manifest=ref(ARCH/"manifest.json"),archive_members=archive["count"],archive_raw_bytes=archive["raw_bytes"],
  archive_stored_bytes=archive["stored_bytes"],archive_status=archive["status"],
  archive_limit="Byte archive and local raw audit, not independent portable reproduction"),
 postprocess_failures=[dict(stage="archive02",status="FAILED_BEFORE_ARCHIVE_CREATION",new_emu_runs=0,reason="Pinned /usr/bin cross-compiler is a symlink; archive_v3 stores exact resolved target plus input alias metadata",receipt=ref(HERE/"archive.command.json"))],
 limitations=["No new speedup from ordinary C run","No default switch/dispatcher/static library",
  "8x32 scope only for performance candidate; other shapes not promoted",
  "No production RTL change or new PPA","Agent-executed same-machine validation; not human signoff"])
assert not (HERE/"record.json").exists()
save(HERE/"record.json",record)
lines=["# 8×32 配置复用：普通 C 调用验证","",
"当前 O2＋H1＋DIV 取消保持修复（0f）硬件上，**8×32 配置复用普通 C 调用验证通过**。本轮补齐实际 C ABI 调用的正确性、拒错、恢复和重放证据，未修改生产 RTL或稳定默认入口，未上传 GitHub。","",
"## 本轮验证了什么","",
"| 项目 | 实测结果 |","| --- | --- |",
"| 8×32 范围 | 4 个公共函数（basic/reuse × vdot/RVV）× 3 数据集，12 个不同用例；两轮正常运行共 24 次调用 |",
"| 完整夹具 | 保留 16 函数、48 不同用例；两轮共 96 次正常调用，全部通过 |",
"| 全宽结果 | 每行低 32 位 INT32 点积与标量模型一致，高 96 位清零；逐字节检查 |",
"| 边界与状态 | 输入不变、前后 canary、未用输出行及向量 CSR 检查通过；5 种软件错误自检全部检出 |",
"| 差分拒错 | 在8×32 reuse vdot内注入 vd0 的bit100错误，唯一mismatch被拒绝；同BIN恢复与独立重放通过 |",
"| O2 观察器 | 两轮均完整闭合；每轮1008次自定义提交，其中8×32为192次，无残留事务 |",
"| 机器码对应 | 16公共函数与此前12个配置复用矩阵单元逐字节匹配，共48次比较；8×32占12次 |",
"| 主机与原文审计 | 20项主机检查通过；GNU/ELF、原始UART/O2日志、版本/镜像/工具身份复核通过 |","",
"## 真实运行与输入身份","",
f"- 新目标进程共3个，严格串行：1个预期拒错exit1、2个正常exit0；无中断。命令起止：{receipt['started']} 至 {receipt['finished']}。",
f"- 同一个C程序BIN：{record['input_identities']['bin']['sha256']}。",
f"- 实际注入PC：{runs[0]['negative_details']['pc']}，指令字0x0388000b；不是复用性能探针的PC。",
f"- 软件源码基点：{record['source_commit']}；硬件：{record['selected_hardware_commit']}。",
f"- EMU SHA256：{record['hardware']['emu_sha256']}；NEMU SHA256：{record['hardware']['nemu_sha256']}。",
"- MinimalConfig、单核、EMU_THREADS=1、VLEN128；guest上限2,000,000 cycles、seed1、128MB RAM；每个进程外部超时7200秒，CPU亲和0–3。",
"- 保留原C检查器的严格UTC顺序验收，另用同boot单调Popen/wait包络与真实PID核对串行。包络不等于精确OS调度时刻。",
"- 普通C主程序和Makefile保持冻结原文。仅将48条调用表稳定排序，把8×32/dataset0/reuse/vdot放首项；输入数据及完整case多重集合不变，以保证负控命中目标函数。","",
"## 如何使用这个公共函数","",
"本次使用Nexus-AM裸机C程序，接口为普通RV64 lp64d双指针ABI；实际测试经C函数指针调用。该资格不扩展为Linux用户态运行或完整LLM推理验收。","",
"~~~c","void config_reuse_gemv_8x32_reuse_vdot(const int8_t *packed_ax, void *output_slots);","~~~","",
"输入为行优先8×32有符号INT8矩阵A，紧接32项向量x，共288字节。输入和输出各自16字节对齐、互不重叠。输出为8个16字节槽，共128字节；每槽低4字节是INT32结果，高12字节为零，不能按连续8个int32_t读取。环境须启用向量状态，并支持VLEN128及当前自定义vdot编码；函数会覆盖允许的向量/调用者状态。",
"实际构建源、头文件和C调用程序保存在qualified-public及仓库精简材料public目录。静态库、dispatcher和默认入口未在本轮新增。","",
"## 性能结论的边界","",
"两次正确性程序的整程序计数（含启动、标量检查、UART，不是点积性能窗口）：" + "；".join(f"{x['run']}: {x['cycles']} cycles / {x['instructions']} retired instructions" for x in whole_program) + "。","",
"本C正确性程序未采集新的性能窗口。上一轮4尺寸×3数据集矩阵中，8×32为firstdot 282.25 → 配置复用273.00 cycles，比firstdot少3.2772%；同场最快RVV为299.00 cycles，加速比1.095238×，每格12个正式样本。这些是上一轮完整调用窗口的数据，不能写成本C程序新跑出的加速比。",
"本次确认这些已测函数可以经普通C调用并正确工作；性能采用候选具体为8×32 reuse vdot，basic等函数只分别保留各自已有数据。4×8、16×64和4×13的性能资格不随功能通过升级；此前控制差异与K13较慢的结论继续保留。","",
"## 失败记录与后续","",
"首次V1运行在EMU启动前因进程包装器未接收位置参数env/timeout而失败，新增EMU为0。原源码、构建、回执保留；V2修复参数透传并补真实主机子进程测试，再在新目录完成本轮。未改内层冻结验证器或放宽门禁。",
"归档首次因固定系统编译器为符号链接而拒绝，未生成档案；新版仅对构建回执中已固定的工具链路径保存链接文本、实际目标与相同SHA，其他链接仍拒绝。原失败回执保留，无新增EMU。",
"下一步可评审8×32候选的稳定入口范围；4×8/16×64仍先只读归因未改RVV控制窗差异，4×13保留较优RVV。若改调用/调度/布局，须验证相应新路径，不能直接继承旧周期数。","",
"## 留档","",
f"- 记录ID：{record['record_id']}；统一数据档案第26条。",
f"- 原始输出：{OUT}",
f"- 工具：{W/'reviews/config-reuse/c8-v2/c8.py'}",
f"- 原文审计：{OUT/'audit-01.json'}",
f"- 本地归档：{ARCH/'manifest.json'}",
f"- 归档包含{archive['count']}项，manifest SHA256：{sha(ARCH/'manifest.json')}。逐文件压缩前后SHA及回读通过；这是本地字节封存，不是独立机器复现。",
"- 完整版本、配置、镜像、命令、PID、退出码和失败记录保存在配套JSON。新周期、面积、STA、功耗、成员人工复现均为NOT_TESTED。"]
(HERE/"RESULT.md").write_text("\n".join(lines)+"\n")
print("C8_RESULT_AND_RECORD26_PREPARED_FROM_ACTUAL_PASS")
