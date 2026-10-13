# 香山 vdot T10/T11 独立收尾审查

日期：2026-10-13（Asia/Shanghai）；固定候选审查；general 工程文档模板。所有行号以本工作区实际文件为准。

## 1. 范围与结论

**结论：需先修复验收工具和来源记录，再以明确边界发布开发候选。** 本次没有发现已证实的生产硬件 blocker；发现 3 项 high、4 项 medium、1 项 low，主要影响“独立证据是否足以认 PASS”。生产实现可继续保留为未完成全矩阵验收的开发候选，但当前包不能签发 T10/T11 完成结论。此结论不否定另一独立 Linux 工作区正在进行的真实验证，也不替代其结果。

审查对象为 `review-repo` 的 `1bd6f1d9c9485695876ff37a77fbb175a5125983`，base 为 `5ff189b8a44e58ee6a37d824e74c801c466c25d3`。仅写当前工作区 `REVIEW.md`、`REVIEW.json` 及 `scratch/`。未修改 review-repo 源码/测试标准/历史文件，未提交、Push、启动长编译、安装、联网、调用 WSL 或访问其他任务。未启动子 Agent；未伪造成员 ACK。

## 2. 输入与证据边界

固定 HEAD、生产 diff、补丁和七个 review-inputs 文件均已定位。682 个 Git 跟踪文件的物理字节与固定提交 blob 全部匹配；来源完整 SHA256 见 `scratch/source-inventory.json`。base→候选的生产 `src/`/`build.sc` diff 与 `review-inputs/hardware-integration.diff` 字节完全相同，SHA256=`e723a25af028e8718d66b3dea3a62010c43c9f4f595cdfcdcb4074f0ef11950e`。`fcb16a8764d342339670df0bbf1bc67ef2028b86`→候选的 `src/`/`build.sc` diff 为空，因此后续日志、分片和 tval 适配提交没有改这部分硬件。

| 输入 | 本次可确认 | 本次不能确认 |
| --- | --- | --- |
| 用户提供硬件构建/hello-vadd/部分 vdot 背景 | 作为任务背景保留；硬件源码树相等已核实 | 本包没有这些新运行的完整原始日志、EMU/config/构建回执，不能独立认运行 PASS |
| `partition-verified.json` | 明确是 INPUT_PARTITION_VERIFIED_NOT_EXECUTION、四片/117唯一项/120记录 | 不能当八片执行成功；本次重生成八片得到124记录，仅证明输入划分 |
| `tval-reference-api.json` | 有来源、时间、ABI、共享库/黄金文件 hash，且明确 public regcpy 不证明 CSR 可达性 | 未提供 runner、实际命令、退出码、配置与完整日志；10054/22 是给定摘要中的数字，未独立执行 |
| `prior-vdot-negative.json` | 明确负控 exit=1、bit100 上下文及 restore pending | 不能当正常恢复 PASS 或完整矩阵 PASS |
| 旧 `team/evidence` 与历史报告 | 归属于各自历史 SHA/日期 | 不转用为指定候选全核验收，不重写历史 |

`difftest` 子模块在本检出未初始化，只能确认 gitlink=`62e4540c03c03aa947bdb67f4b6bf66f1a29c5d0`，无法阅读其实际 CSR/128位比较实现。本次无 RTL、EMU、NEMU 执行。网络/其他工作区均未访问；远端仍为 base 属于用户提供背景，未直播确认。

## 3. 源码审查结果

### 3.1 译码、依赖、完成与取消

| 项目 | 定位与源码事实 | 验收边界 |
| --- | --- | --- |
| 精确编码 | `src/main/scala/xiangshan/backend/decode/Instructions.scala:5–9`、`isa/bitfield/RiscvInst.scala:93–98`、`VecDecoder.scala:190–194` 共用 MATCH=0200000b/MASK=fe00707f；17固定位邻居不匹配 | 静态32768编号组合通过，不代表真实 DecodeStage/Rename 执行 |
| vs1/vs2/v0 | `DecodeUnit.scala:857–862` 与 `DecodeUnitComp.scala:357–375` 使用原 RS1/RS2；旧 vd 与隐式 mask 禁用。`DecodeStage.scala:232–242` 保留源 v0 的显式依赖并路由目的 v0Wen；`datapath/BypassNetwork.scala:156–170` 将src3的v0数据送回普通源槽 | 未发现源槽颠倒/丢v0的确定缺陷；真实 RF/rename/bypass 和别名仍需矩阵与依赖压力测试 |
| 单uop与WB | `UopInfoGen.scala:198–202,245–252` 固定1uop/1WB，不受非法 LMUL 展开；复杂译码 latchedInst/UopInfo 位于`DecodeUnitComp.scala:131–172` | decode测试顶层只有 simple/complex decoder，没有 DecodeStage/v0 routing/Rename/ROB；不得据131072计划刺激宣布全核通过 |
| config与vstart | `DecodeUnit.scala:1033–1066` 保存vtype/vstart；`VecExceptionGen.scala:275–280` 在译码检查vstart和e8/m1；`DecodeUnitComp.scala:2047–2051` 最终覆盖flushPipe=false。VL仍为src4，`fu/vector/VecPipedFuncUnit.scala:54–55` 从renamed数据取值 | 静态路径合理；序列化harness的独立调用不能证明紧邻vsetvl/CSR依赖或推测恢复 |
| decode非法 | `DecodeUnitComp.scala:198` 合并EX_II；`rename/Rename.scala:340–344` 对已知异常置numWB=0 | 已知非法不应等待FU；应由真实异常路径核对寄存器/映射/vstart保持 |
| FU非法与ROB完成 | `fu/wrapper/VDot.scala:36–43,59–84` 接受时捕获非法状态、仍发out.valid异常响应但vec/v0Wen关闭；`datapath/WbArbiter.scala:177–224,356–379` 无RF写仍ready，完成通过fire送CtrlBlock；`rob/Rob.scala:1189–1201`取exception且非vls不更新vstart | 没有把“关闭RF写”误当成“取消ROB完成”；需真实非法VL恢复、目的旧映射和年轻消费者flush测试 |
| VFEX4与flush | `Parameters.scala:456` 加入已有VDotCfg；`fu/FuConfig.scala:583–595`128位/非流水/不确定时延；`exu/ExeUnit.scala:127–141,221–226,321–322,366–383`共享busy、单热结果与握手；VDot以真实RobPtr判kill，阻断flush同周期接受与被kill响应 | 静态没有确定bug；共享除法、反压、不同/匹配redirect及ROB绕回未由本次验收 |

VDot 原FU状态机和算术模块不在base→候选生产变更中。当前审查没有重新开发它们。存在源码断言不等于已执行断言；旧独立FU仿真也不替代共享VFEX4/全核测试。

### 3.2 NEMU xTVAL 平台适配

补丁`team/patches/nemu/vdot-s8x8-r32-v0.1.patch:130–134`的判定为精确vdot、vector_enabled、`(vtype & ~0xc0)==0`、vstart=0、vl!=8。这样仅ta/ma可变，vill/SEW/LMUL/保留位均被排除。`system/intr.c`补丁段`150–168`再限定EX_II，并在进入trap/修改上下文之前取值；其他指令、其他异常、组合非法条件走原fallback。EX_VI不会触发归零。没有引用DUT算术值、PC、用例ID或expected。

Kconfig新增项均default n，XS_TVAL选项依赖RVV，并由C编译条件要求CUSTOM_VDOT同时开启。`prepare-nemu-vdot.sh:66–80`显式启用CUSTOM_VDOT/XS_TVAL/TVAL_EX_II并要求NMIE=1、MDT=0；`artifact_guard.py:182–199`在运行前校验角色、patch、配置、source及binary provenance。固定XS的`fu/NewCSR/NewCSR.scala:73–74`和`u/NewCSR/MachineLevel.scala:553–554`分别支持MDT=0/NMIE=1（MachineLevel的实际完整路径见source inventory）。未发现通过skip-difftest、修改期望或按DUT值制造通过的候选改动；`rob/Rob.scala:1508–1512`仍使用既有skip来源，base→候选未改它。

固定XS依据可追到`DecodeUnitEnqIO`（`DecodeUnit.scala:775–779`）只有vtype/vstart，没有VL；`DecodeStage.scala:127–134,294–295`仅已知非法送trapInstInfo；`TrapInstMod.scala:59–84`保存/清理decode或CSR fault机器字；M/HS/VS TrapEntry分别在`:55/:57/:70`用valid选择机器字或0。VDot FU没有供给机器字的接口，因此对当前无竞争M模式程序，“译码合法、仅VL在FU发现非法”归零有直接源码依据。它不是对所有乱序/虚拟化状态的完成证明，详见R07。

当前patch hash=`6c165bf5f94ef0bfb4f894a5f06eb6d620d4a7e0e12f3b1400fa72811f5d24db`，manifest 1.1.0一致；旧1.0.0补丁hash=`7e508d84da2f2bbb93a103637c73a19bf27258ce2aa1b3bd2a56781ef3890006`与历史manifest一致，已保留。新增完整头文件hash匹配manifest。1.0.0→1.1.0的`vdot.h`算术/状态helper内容未变：缓存两源低64位，按数学signed int8求和，写32位补码并清高96位。新增部分属于架构可选平台trap行为，没有从RTL复制乘法/归约实现。未在本机应用补丁到未提供的NEMU基线，不能宣称七个应用后完整文件全部重新验证。

### 3.3 紧凑日志与分片

`team/workloads/vdot-exceptions/main.c:87–121`的C编码器与`team/scripts/check-vdot-run.py:39–75`字段顺序一致：0–12为instruction/陷阱与状态字段，13–18/pre CSR，19–24/post CSR，25–30为三个128位向量的低/高u64，31–33为all32/pre32/guards。最多34×11字节容量充分；回引用只指向先前字段；literal用unsigned LEB128，base64只传输字节。Python检查canonical base64、tag、前向引用、10字节uint64溢出、LEB128最短形式、截断、34字段和尾随字节。原语义检查继续校验cause/PC/CSR/VS/全128位期望及数量，不因compact而推断成功。

主机测试包含roundtrip与坏状态、缺summary、timeout、duplicate/mixed/unknown format和坏payload拒绝。实际C交叉测试及C tval边界测试因没有GCC而SKIP，不能把现有外部“C测试通过”背景重复称为本次实测；已有256随机C encoder测试仅覆盖合法PASS编码分支，失败/负控分支的C编码本次只有源码核对。verbose本来只记录all32判定标志，不逐字段保存全部32寄存器；compact保留的是已有日志字段，不扩大可还原范围。

生成器在`team/tests/generate_vdot_cases.py:220–256`保留母用例对象，先D00再按position mod n分片。八片重生成并核验为48定向+32随机+37异常=117唯一项，仅D00重复7次，合计124 extension记录；每片输入和expected逐对象相等。四片同样有117唯一项/120记录，两个计划hash均为`c6fec6194bbca496d0b4a128f866e7a1f4d1187d356c7d224f53e6eef699cfd1`，与给定摘要的计划hash一致。重生成manifest hash因当前生成器来源记录不同，不等于给定旧manifest hash；没有据此替换原始输入或宣布执行通过。

## 4. 分级问题与最小修复

blocker：0项（没有已证实的生产硬件阻断缺陷）。以下high阻止当前证据包签发验收结论；中低级问题也应在发布说明/来源闭包中处理。

### R01 · high · 并集检查器未把来源与运行产物绑定到固定候选

定位：`review-inputs/verify-union.py:67–69`；`review-inputs/verify-union.py:90–101`。

证据性质：`CONFIRMED_BY_SYNTHETIC_COUNTEREXAMPLE`。common_source 只比较片间一致，不比较母用例或当前生成器/模型实际 hash；team.sha 也只要求片间一致。runtime.sha256 只读取同名摘要，不验证 EMU 的构建来源、NEMU 配置/平台 profile、dirty/source 快照或实际加载字节。统一使用错误来源也会通过。生产 run-rtl 有来源门禁，但独立 aggregate 不消费其回执，不能据此独立证明来源闭包。

最小建议：加入显式 expected software candidate 与冻结 parent/source digest 参数；核对片、母用例及当前生成器/模型实际字节。消费并核验 build-verification.json、nemu-verification.json、source/working-tree/runtime 回执及 EMU 构建来源。分开记录软件候选与 RTL 构建 SHA：现有 fcb16a 的 EMU 可在生产源码树相等且 build/config/hash 对应时复用，无需为了后续测试提交强制重编。

复核依据：`all_receipts_bound_to_wrong_candidate`；`all_shards_claim_wrong_model_source`。

### R02 · high · full 模式不复核七条自检，实际执行顺序也未要求 D00 前置

定位：`review-repo/team/scripts/check-vdot-run.py:80–85`；`review-repo/team/scripts/check-vdot-run.py:107–139`；`review-inputs/verify-union.py:95–102`；`review-inputs/verify-union.py:122–124`。

证据性质：`CONFIRMED_BY_SYNTHETIC_COUNTEREXAMPLE`。full 模式切掉 VDOT_EXTENSION_BEGIN 之前的记录，只依赖 HARNESS_SELFTEST_PASS 文本和三个负控结果；aggregate 却直接报告 completed_selftests=7*n。执行 ID 使用 set/Counter 比较，不检查顺序，数据文件的 D00 前置不等于实际日志的 D00 前置。候选 main.c 的生产流程正确，但独立 checker 可接受缺失自检及异常先行的日志。

最小建议：对 extension 前的 H00～H06 逐条执行现有 selftest 语义检查，要求唯一、顺序及全部 PASS；在 extension 后核对实际序列等于 shard 法律性用例序列再接异常序列，至少严格要求首项 D00 成功且位于所有异常之前。完成计数从已核实记录计算。

复核依据：`missing_all_seven_selftest_records`；`exceptions_executed_before_D00`。

### R03 · high · 负控失败与同镜像正常恢复的证据尚未闭合

定位：`review-inputs/verify-union.py:107–123`；`review-inputs/prior-vdot-negative.json:1–8`。

证据性质：`CONFIRMED_BY_SOURCE_AND_SYNTHETIC_COUNTEREXAMPLE`。normal_image 来自 build-0 摘要，与 negative 摘要比较，但没有读取 run-0 实际运行镜像及其 provenance；缺少镜像文件时字节验证直接跳过。注入事件的 PC 不与 mismatch PC 比较，result.json 的 instruction 也不与原始注入字逐值绑定。仅寄存器号相同且 XOR 是 bit100 不能证明该 vdot 注入触发了该处失败；最后却无条件写 same_image_normal_restore=PASS shard-0。提供的旧负控摘要明确写恢复 pending。

最小建议：绑定 build-0、run-0 与 negative 的实际 image digest、数据、flash、EMU 和正常 ref/provenance；归档产物或完整冻结来源回执，缺项应拒绝或标 UNKNOWN。要求 injection、mismatch、result 的 PC/vd/instruction 逐值一致，核验 vd 等于机器字目的字段、唯一预期差分及注入器来源。仅在同镜像正常 run-0 的完成证据核实后写恢复 PASS。

复核依据：`negative_mismatch_at_different_pc`；`SYNTHETIC-aggregate accepted without workload/runtime provenance or image bytes`。

### R04 · medium · 完成事件没有绑定最终阶段，driver status 可出现互相矛盾的退出码

定位：`review-repo/team/scripts/check-vdot-run.py:128–139`；`review-inputs/verify-union.py:85–88`；`review-inputs/verify-union.py:104–106`；`review-repo/team/scripts/vdot-tests.sh:127–128`。

证据性质：`CONFIRMED_BY_SYNTHETIC_COUNTEREXAMPLE`。summary 缺失/计数错误和非零实际退出会被拒绝，这是正确的；但 GOOD TRAP/Difftest 只做全日志 substring 查询，GOOD TRAP 位于 extension 之前也能通过。driver status 使用多行 search，只要包含 exit_code=0 就接受，即使另有 exit_code=124。用户所述新机器入口严格最终完成标记没有提供源码/日志，不能把它当成当前 aggregate 已具备的约束。

最小建议：解析单个 run/session 的唯一实际退出值和唯一 driver 最终完成标记；必须无矛盾，且 target GOOD TRAP 在完整 summary 之后、driver 完成在 checker 成功之后。保留缺 summary、超时、截断、重复完成与拼接旧运行的拒绝测试。

复核依据：`good_trap_before_extension_without_terminal_event`；`contradictory_driver_status`；`summary_truncated_despite_exit_zero is correctly rejected`。

### R05 · medium · 导入 manifest 的十项 current_sha256 已过时

定位：`review-repo/team/docs/t10-t11-imports.json:23–47`；`review-repo/team/docs/t10-t11-imports.json:68–101`；`review-repo/team/docs/t10-t11-imports.json:140–164`；`review-repo/team/docs/t10-t11-imports.json:256–263`；`review-repo/team/docs/t10-t11-imports.json:338–344`。

证据性质：`CONFIRMED_BY_PHYSICAL_HASHES`。原始 sha256/source_blob 是历史导入证据，应保留；current_sha256 仍写原始值，已不对应候选 manifest、patch、日志编码器、生成器、运行门禁等十个文件。当前 NEMU 专用 manifest 与 patch digest 自身一致，因此这是来源记录缺陷，不是补丁字节损坏。

最小建议：保持 original sha256/source_blob/source_commit/size 不变，更新 current_sha256 并增加 modified、current_size、修改提交/原因追踪；记录新增测试和历史补丁文件的来源。用实际字节自动核对 Current 字段。

复核依据：`scratch/independent-checks.json: stale_current_hashes (10 entries)`。

### R06 · medium · 外置 checker 和参考 API 回执的复现材料不完整

定位：`review-inputs/verify-union-negative-tests.py:4–21`；`review-inputs/verify-union.py:130–132`；`review-inputs/partition-verified.json:1–12`；`review-inputs/tval-reference-api.json:1–35`。

证据性质：`CONFIRMED_INPUT_GAPS`。负测脚本硬编码另一 Linux 工作区并只复制四片，不能在授权目录直接运行；verify-union.py 默认 repo=parents[2] 在本包位置指向工作区外的父目录，须显式 --repo。提供的 partition 回执为四片/120记录，不是要求的八片/124记录。API 摘要有时间/来源/ABI/二进制及 golden hash，但无原始执行脚本、命令、实际退出码、config/provenance 与逐项日志；其 10054 legal/22 illegal 无法在本包独立复核，且公开 regcpy 注入明确不证明程序 CSR 可达性/顺序。

最小建议：将 parent/runs/repo 参数化，按 manifest 动态确定片数并保留四片历史回执，新增八片当前回执。归档原始 API runner、命令、退出码、测试域及 config/build/source/log hash；独立审查包包含来源清单与显式 --repo 示例，不能复制历史摘要充当当前执行证据。

复核依据：`scratch/independent-checks.json verifies regenerated 4 and 8 shard input plans only`；`Original Linux negative-test script NOT_RUN; equivalent local isolated six negatives executed`。

### R07 · medium · tval 平台适配的 M 模式依据成立，但虚拟化及竞争陷阱范围未证明

定位：`review-repo/team/patches/nemu/vdot-s8x8-r32-v0.1.patch:130–134`；`review-repo/team/patches/nemu/vdot-s8x8-r32-v0.1.patch:150–195`；`review-repo/src/main/scala/xiangshan/backend/fu/NewCSR/TrapInstMod.scala:59–84`；`review-repo/team/workloads/vdot-exceptions/README.md:21–21`；`review-inputs/tval-reference-api.json:34–34`。

证据性质：`EVIDENCE_GAP_AND_EXPLICIT_INFERENCE`。补丁在 trap entry 改上下文前捕获 vp_enable/vtype/vl/vstart，并复用到 vstval/stval/mtval；源码表达式窄化正确。但本包没有 NEMU 基线的 vp_enable 定义/虚拟 CSR 上下文实现或真实 S/HS/VS/delegation 矩阵，当前程序是 M 模式。TrapInstMod 还有 faultCsrUop 捕获入口且维护跨周期 valid，不能仅凭“vdot 不在 decode 捕获”就推广所有推测/并发场景必然 tval=0。年轻 decode 非法、CSR fault、redirect/FTQ wrap 与旧 VL 非法竞争是否正确清理，是待真实测试的推断风险，未发现已证实 RTL 错误。

最小建议：明确当前验证范围为固定源码下 M 模式且其余模式未验证；附完整 NEMU 基线 vp_enable/上下文及 XS 平台来源 SHA。若要发布虚拟化支持，补测 host VS Off/guest VS Off、合法 vtype 的非法 VL、decode 已知非法、EX_VI 不变、M/HS/VS 委托、以及年轻非法/CSR fault/flush 竞争；先复现再决定是否需源码修复，禁止放宽 expectation 或读取 DUT 值。

复核依据：`DecodeUnitEnqIO lacks VL; VecExceptionGen has vtype/vstart checks; VDot uses renamed VL`；`M/HS/VS TrapEntry select instruction only when trapInst.valid; no local runtime proof`。

### R08 · low · 当前入口仍把固定提交称为未提交 WIP，NEMU README 仍说明旧版本

定位：`review-repo/AGENTS.md:3–11`；`review-repo/AGENTS.md:24–26`；`review-repo/README.md:1–3`；`review-repo/team/README.md:3–7`；`review-repo/team/README.md:30–32`；`review-repo/team/docs/t10-t11-20261013.md:3–3`；`review-repo/team/docs/t10-t11-20261013.md:21–41`；`review-repo/team/patches/nemu/README.md:3–7`。

证据性质：`CONFIRMED_STALE_TEXT`。AGENTS 与本轮记录仍写全部未提交/无可用 RTL/NEMU；team README 写未实现接入/NEMU，NEMU README 写1.0.0/五文件，而当前 manifest 是1.1.0/七文件。这些历史事实有价值，但“最新/当前”入口易误导后续人员；根 README 只链接旧 team README。

最小建议：新增固定候选当前报告并在根 AGENTS/README、team README 与 NEMU README 顶部链接覆盖当前状态；旧 WIP、历史 PASS、旧 patch/manifest 原文保留并明确日期/来源。分别列硬件构建、部分真实运行、未完成矩阵、未验证控制/PPA，不将本次主机检查写成 RTL PASS，不填写成员 ACK。

复核依据：`fixed HEAD verified; patch manifest version=1.1.0; hardware diff and later commits verified`。

## 5. 实际检查与结果

| 检查 | 状态/实际退出 | 证据 |
| --- | --- | --- |
| 选定7个Python测试模块 | PASS：36项中34通过、2 SKIP，exit0 | `scratch/host-tests.log`；实际1.279s |
| production diff与fcb后硬件变化 | PASS：diff hash相同，fcb后生产diff为空，exit0 | `scratch/production-diff.log`、`hardware-since-fcb.log` |
| 静态编码/两oracle | HOST PASS，exit0；32768编码组合、17邻居、原22定向+10000随机 | `scratch/integration-static.json` |
| 四/八片输入精确并集 | INPUT ONLY PASS，exit0 | `scratch/parent`、`partition-4`、`partition-8`、`independent-checks.json` |
| 六个本地等价并集负测 | EXPECTED_REJECTION，检查脚本exit0 | 缺片、混parent、损坏输入、错index、单片错source、缺真实回执 |
| summary截断但exit0 | EXPECTED_REJECTION | 原checker拒绝“missing or duplicate summary” |
| 七个新增证据反例 | FAIL（checker意外认PASS）；审计脚本按发现问题返回exit0 | `scratch/counterexamples/`、`independent-checks.json`；全部明确SYNTHETIC，绝非真实RTL日志 |
| 固定源码物理字节 | PASS，682文件，0不符，exit0 | `scratch/source-inventory.json` |
| 实际C编译/encoder交叉/tval头 | SKIP | 没有GCC；未安装或寻找其他任务工具链 |
| ArtifactTests/原source注入检查 | SKIP | 前者包含scratch Git commit，后者会修改源码或外部NEMU；不在本次授权范围 |
| 原Linux负测脚本 | NOT_RUN；本地等价六负测已执行 | 硬编码外部工作区，禁止访问；未改原脚本 |
| 真实RTL/NEMU/完整matrix | NOT_RUN/未验证 | 由另一独立Linux工作区执行，本次未争用 |

审计辅助脚本第一次运行exit1：自身比较补丁分节时把末尾分隔换行当成helper内容差异。只修正scratch脚本为逐行比较后复跑exit0；`scratch/independent-checks.log`保留原始失败，不计成候选测试失败或删除证据。另有一次只读辅助CLI因参数解析方式拒绝`--oneline`，改为直接传Python argv后成功；未涉及候选源码修复。

Git只使用命令级`-c safe.directory=<本次授权review-repo>`处理不同账户的ownership检查；未写global config。Git读取全局ignore时Permission denied仅记录为warning，未重试或更改权限；实际文件字节核验不依赖该ignore。工作树status未报告变更。命令环境设`PYTHONDONTWRITEBYTECODE=1`，临时目录限制在scratch；最终Git读取还设`GIT_OPTIONAL_LOCKS=0`。

### 5.1 可复现命令

下列入口从当前工作区PowerShell执行；使用现有Python，不执行安装。`audit.py`逐个记录完整argv、cwd、UTC起止时间、退出码及log SHA256到`scratch/commands.jsonl`。JSON同时内嵌所有回执；源码SHA与输入文件SHA见source-inventory及independent-checks。

```powershell
python -B -X utf8 scratch/audit.py tests
python -B -X utf8 scratch/independent_checks.py
python -B -X utf8 review-repo/team/scripts/check-vdot-integration-source.py --output scratch/integration-static.json
python -B -X utf8 scratch/source_inventory.py
python -B -X utf8 review-inputs/verify-union.py --parent-data scratch/parent --runs scratch/partition-8 --repo review-repo --plan-only
```

`independent_checks.py`仅生成scratch数据和明确标注的合成回执，在隔离副本上运行反例并保存结果。其exit0表示审计脚本执行完且发现记录完整；不表示全部负控被checker拒绝，更不表示RTL PASS。生成器源码/预期文件没有修改，源工作区fixture没有覆盖。

以下是本次保留的实际命令回执（完整命令未省略）：

- `production-diff`：UTC 2026-10-13T13:57:14.874990+00:00 → 2026-10-13T13:57:14.927171+00:00；exit `0`。cwd=`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013`；log=`scratch\production-diff.log`；log SHA256=`e723a25af028e8718d66b3dea3a62010c43c9f4f595cdfcdcb4074f0ef11950e`。

```text
git -c safe.directory=D:/Projects/competitions/2026-10-CIE-RISCV-XiangShan/t10-t11-final-20261013/review-repo -C 'D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013\review-repo' diff 5ff189b8a44e58ee6a37d824e74c801c466c25d3 1bd6f1d9c9485695876ff37a77fbb175a5125983 src build.sc
```

- `host-tests`：UTC 2026-10-13T13:57:14.981316+00:00 → 2026-10-13T13:57:16.355329+00:00；exit `0`。cwd=`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013\review-repo\team\tests`；log=`scratch\host-tests.log`；log SHA256=`19e012c2d017062c1154b7b9ff672212e56db48a3cd9f22bfb5f4cb51cf8cf63`。

```text
'D:\Programs\Python\Python313\python.exe' -B -X utf8 -m unittest -v test_vdot_model test_vdot_log test_packed_vdot_log test_vdot_shards test_vdot_tval_policy test_nemu_reset_policy test_baseline
```

- `independent-checks`：UTC 2026-10-13T14:02:16.990837+00:00 → 2026-10-13T14:02:17.564189+00:00；exit `1`。cwd=`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013`；log=`scratch\independent-checks.log`；log SHA256=`00fb5492913fdac5eae402f719c1454341caf7832e0a825ad978baf35a524808`。

```text
'D:\Programs\Python\Python313\python.exe' -B -X utf8 scratch/independent_checks.py
```

- `integration-static`：UTC 2026-10-13T14:02:17.564693+00:00 → 2026-10-13T14:02:17.772733+00:00；exit `0`。cwd=`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013`；log=`scratch\integration-static.log`；log SHA256=`a3722aeb648d91ae07b8996288eb18939ec6253fceb6a78eea0b168c688db709`。

```text
'D:\Programs\Python\Python313\python.exe' -B -X utf8 review-repo/team/scripts/check-vdot-integration-source.py --output scratch/integration-static.json
```

- `independent-checks-v2`：UTC 2026-10-13T14:03:00.073308+00:00 → 2026-10-13T14:03:00.587131+00:00；exit `0`。cwd=`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013`；log=`scratch\independent-checks-v2.log`；log SHA256=`fd3ec380794cc1a4a6701013790d9194df1489ae41505b427e8f57097a77eef8`。

```text
'D:\Programs\Python\Python313\python.exe' -B -X utf8 scratch/independent_checks.py
```

- `candidate-history`：UTC 2026-10-13T14:04:30.877767+00:00 → 2026-10-13T14:04:30.911718+00:00；exit `0`。cwd=`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013`；log=`scratch\candidate-history.log`；log SHA256=`553539e809d2b58ce26033e7b5c599fc5bc843d8ee2320e1753be8787db4c46c`。

```text
git -c safe.directory=D:/Projects/competitions/2026-10-CIE-RISCV-XiangShan/t10-t11-final-20261013/review-repo -C 'D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013\review-repo' log --oneline 5ff189b8a44e58ee6a37d824e74c801c466c25d3..1bd6f1d9c9485695876ff37a77fbb175a5125983
```

- `hardware-since-fcb`：UTC 2026-10-13T14:04:30.912566+00:00 → 2026-10-13T14:04:30.944279+00:00；exit `0`。cwd=`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013`；log=`scratch\hardware-since-fcb.log`；log SHA256=`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。

```text
git -c safe.directory=D:/Projects/competitions/2026-10-CIE-RISCV-XiangShan/t10-t11-final-20261013/review-repo -C 'D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013\review-repo' diff fcb16a8764d342339670df0bbf1bc67ef2028b86 HEAD -- src build.sc
```

- `final-git-status`：UTC 2026-10-13T14:04:30.944720+00:00 → 2026-10-13T14:04:30.980008+00:00；exit `0`。cwd=`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013`；log=`scratch\final-git-status.log`；log SHA256=`67ac9add7403a7635fd1b15443abb957b140c2426916d554bea8fce3f42b546d`。

```text
git -c safe.directory=D:/Projects/competitions/2026-10-CIE-RISCV-XiangShan/t10-t11-final-20261013/review-repo -C 'D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013\review-repo' status --porcelain=v1
```

- `git-submodules`：UTC 2026-10-13T14:04:30.980461+00:00 → 2026-10-13T14:04:31.012320+00:00；exit `0`。cwd=`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013`；log=`scratch\git-submodules.log`；log SHA256=`ca565f4e862d0b6b6f48487a09418ddd2b14f38a28e8dbdcf75664d6ad5927c0`。

```text
git -c safe.directory=D:/Projects/competitions/2026-10-CIE-RISCV-XiangShan/t10-t11-final-20261013/review-repo -C 'D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013\review-repo' ls-tree HEAD difftest fudian huancun utility yunsuan
```

- `independent-checks-final`：UTC 2026-10-13T14:06:45.249242+00:00 → 2026-10-13T14:06:45.808115+00:00；exit `0`。cwd=`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013`；log=`scratch\independent-checks-final.log`；log SHA256=`fd3ec380794cc1a4a6701013790d9194df1489ae41505b427e8f57097a77eef8`。

```text
'D:\Programs\Python\Python313\python.exe' -B -X utf8 scratch/independent_checks.py
```

- `source-inventory`：UTC 2026-10-13T14:06:45.808628+00:00 → 2026-10-13T14:06:45.975178+00:00；exit `0`。cwd=`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013`；log=`scratch\source-inventory.log`；log SHA256=`fad083447823d2ccb9251ae00f16d1e9005e7265f68e46c513b8c0a8898b1b72`。

```text
'D:\Programs\Python\Python313\python.exe' -B -X utf8 scratch/source_inventory.py
```

- `independent-checks-release`：UTC 2026-10-13T14:18:58.705482+00:00 → 2026-10-13T14:18:59.150953+00:00；exit `0`。cwd=`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013`；log=`scratch\independent-checks-release.log`；log SHA256=`3d4e63eec0ea5c7e67f74bea3c9ec58cbad1bd21e5dadd0588d21e41822100fd`。

```text
'D:\Programs\Python\Python313\python.exe' -B -X utf8 scratch/independent_checks.py
```

- `source-inventory-release`：UTC 2026-10-13T14:18:59.151412+00:00 → 2026-10-13T14:18:59.297288+00:00；exit `0`。cwd=`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013`；log=`scratch\source-inventory-release.log`；log SHA256=`fad083447823d2ccb9251ae00f16d1e9005e7265f68e46c513b8c0a8898b1b72`。

```text
'D:\Programs\Python\Python313\python.exe' -B -X utf8 scratch/source_inventory.py
```

- `post-review-git-status`：UTC 2026-10-13T14:18:59.297777+00:00 → 2026-10-13T14:18:59.327764+00:00；exit `0`。cwd=`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013`；log=`scratch\post-review-git-status.log`；log SHA256=`67ac9add7403a7635fd1b15443abb957b140c2426916d554bea8fce3f42b546d`。

```text
git -c safe.directory=D:/Projects/competitions/2026-10-CIE-RISCV-XiangShan/t10-t11-final-20261013/review-repo -C 'D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\t10-t11-final-20261013\review-repo' status --porcelain=v1
```

## 6. 发布前动作与真实测试清单

主审先修R01–R04并用本文七个反例逐项复核为拒绝，再更新R05来源Current字段和R06可复现材料；R08用新报告覆盖当前入口，保留所有历史。R07可以通过明确限制当前平台范围并列未验证项目处理；若扩大虚拟化/竞争场景验收，须补真实证据。生产硬件没有因本报告被改动，也没有要求重做已完成构建。

发布开发候选时应明确“固定候选、部分真实运行、全矩阵尚未由独立审查确认”，不能把外部正在运行视作已完成。发布动作不属于本次授权，本次不操作远端。最终真实证据至少须覆盖：

1. 八片完整实际日志：117唯一项、124 extension记录、仅D00重复；各片七个selftest、三负控和合法对照前置，共56条selftest及24条harness负控可逐条复核。原输入/expected不变。
2. 每片实际exit0、完整summary、真实DiffTest启用、summary之后目标GOOD TRAP以及唯一driver最终完成标记；同EMU/ref/flash与明确的hardware/software来源、配置、镜像和日志hash。
3. bit100真实负控：精准机器字/目的/PC对应的唯一差分失败、真实非零退出；同输入/镜像/EMU/flash/正常ref完成恢复PASS，归档注入器来源与实际加载路径。
4. 固定已初始化difftest与实际NEMU库确实比较全部128位向量、xTVAL及向量CSR；本次只有gitlink和普通skip源码可读，未核实加载后的比较域。
5. VL物理依赖与vtype/vstart快照：紧邻vsetvl/CSR生产者消费者、别名/v0、非法恢复及年轻消费者；单次序列化harness不能代替这些场景。
6. ROB/flush/回压：mul/reduce/respond/响应stall时匹配与无关redirect、ROB/FTQ绕回、非法完成但无RF写回、旧物理映射恢复。
7. VFEX4共享Vfdiv/Vidiv/vdot及WB竞争/反压、普通除法回归；独立VDot FU PASS不等于共享EXU PASS。
8. tval组合条件：decode已知非法保留机器字、仅FU非法VL归零、VS Off/vill/e16/m2/vstart与vl组合保持正确分类；年轻decode非法/CSR fault竞争；若声称虚拟化支持，补M/HS/VS上下文与委托矩阵。
9. 周期性能、PPA、完整规格/接口人工签字另行验收；本文未声称这些完成，没有成员ACK。

当前审查已完成，交付后不等待其他工作区或用户交互。修复与复核由主审根据本文准确位置继续执行。
