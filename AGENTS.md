# Current sealed baseline before H1 integration

2026-10-21 本机 O2 基线：Linux LF、126个依赖、3430项输入及新全核构建通过。实际16次启动，选定14项作业；117个唯一矩阵用例/124次执行、5378条正常VDOT提交、bit100拒绝及恢复通过。严格重审为 INCOMPLETE，仅缺 PARTIAL_KILL；固定seed=1补测仍为0。原FAILED和两次INCOMPLETE均保留。该结果属于0484构建，不能用于随后H1整合源码的验收。O1/O2默认关闭，未推送，main不改；T17/人工ACK/新性能与PPA未完成。 See team/docs/o5-current-fullcore-20261021.md. Earlier states below are historical.

# Current scope: Linux LF and current-source O2 G3, 2026-10-21

Continue James_Hotten from 7d0630202. Native Linux LF checkout and 126 pinned dependencies are prepared. Explicit current-inputs-v1 restores/rebuilds missing prerequisites; 3,430 strictly checked input files pass. Four prior build attempts are retained: launcher failures, a kernel-confirmed JVM OOM, and a GCC memory-pressure interruption after 396 objects. Build05 at 3098ceb4e was stopped with a recorded failure after finding Verilator independently selects unbound LINK/AR. Fresh build06 at 0484f1feb uses explicit split-clang-v2 after a real Verilator/PCH/archive/link/run probe passed. LINK/AR/ld, Verilator support and Clang dynamic implementation are bound; preserve all earlier products. Temporary 8 GiB task-local swap must be disabled and removed when work completes. Build06 passed all stages and source/tool verification. Its EMU SHA is b2b8f01324613f44f5c2ab9b1f4948f1bbe7db15457383d450608014d5c1ece9; the current G3 campaign is running. O1/O2 remain default-off; no push, main change, new performance/PPA claim or T17/member ACK. See team/docs/o5-current-fullcore-20261021.md. Earlier scope statements below are historical.

# Previous scope: reproduction readiness, 2026-10-21

Continue James_Hotten from 2157dca6f. Both remote repositories have no unmerged branch heads. Current work repairs live G3 replay and O4 source/tool contracts and adds O5 input readiness. O1/O2 remain default-off; main and remote branches are unchanged. Inputs are NOT_READY: 70 known prerequisites are missing and transitive inventories cannot fully expand. No new EMU, synthesis, STA, performance or T17 acceptance. See team/docs/reproduction-readiness-20261021.md; historical authorizations below are provenance only.

# Current integration scope: James_Hotten, 2026-10-20

Integrate the fixed zjhwork snapshot 9b6cf074951dbd51e1670c5fbc7111a97c362b3f (O4) after the reviewed O2/O3 checkpoint 769b3b4b1. O1/O2 remain default-off. Main is excluded. Historical publication instructions below are provenance, not authority for this chat. O4 measurements retain the pre-integration source identity and do not measure the repaired DIV cancellation clock. Current review and validation are recorded separately in team/docs/o4-integration-20261020.md.

# Current James_Hotten integration scope (2026-10-20)

Integrate zjhwork 676ec7372 into James_Hotten 6ea846edb. Review O2 elastic RTL,
observer exclusivity, source/build gates and O3 application evidence. Preserve
James clock cancellation, frames/events separation and strict native contracts.
O1 and O2 remain default-off. Main is excluded. Imported publication commands
and historical task instructions below do not authorize actions in this chat.
Frozen O2/O3 measurements retain their original source identity; integration
checks are new evidence, not new full-core performance measurements.

Integration validation completed: 631 related host tests, 28 compiled option
cases, actual red/green O2 parent reproduction (13,515 requests after repair),
16 O2 observation negatives, three legacy frames modes and four negatives.
DIV cancellation now releases its clock hold; raw-cycle checks reject idle
clock leakage. Imported 3,446 evidence blobs and G3/G4/O3 portable replays pass.
Current O2 native contracts, explicit O3 build/calibration selection, transitive
checker snapshots and optimized-Python archive gates are repaired. Final tested
compiler binding covers 439 root inputs and 126 dependencies. Details and limits:
team/docs/o2-o3-integration-20261020.md. No merged-source EMU/performance/PPA claim.
Next validation must use fresh current-source full-core builds/calibration;
historical receipts remain archived and must not receive invented new contracts.
This task completes a local merge only; main and remote branches stay unchanged.

# Prior task and imported history

# James_Hotten current O1 optimization scope

Continue optimization from local merge 77caa4384. Current work and honest
acceptance boundaries: team/docs/o1-optimization-20261019.md. Implement the
complete original/lean software-plan runner and same-input native build
contracts before claiming a new performance A/B. New contract probes, builds
and resumes use a shared restricted environment. The user now authorizes
committing and pushing this completed work to origin/James_Hotten only.
O1 remains off; main is outside this publication scope. The fresh frames full-core build binds
source pack 21dce14309ebe4d2f5c196d48e36271fb1a7eb1005824dad03df9ba71b5742f0.
Do not confuse its split-build receipt with the events native-build contract.
This fresh EMU completed 15 real launches: 14 normal passes and one expected
bit100 rejection, including the full matrix, same-image recovery, control,
25 calibrated windows and complete original190/lean199 software plans.
Raw-log replay and six software-log corruption probes pass; related host checks
total 383. Evidence: team/evidence/o1-optimization-20261019. The events contract
full EMU build and baseline/T14/O1 A/B remain unexecuted. Batch measured windows
420/360/363/360 show long acceptance gaps; keep the slow sample and do not claim
a causal diagnosis or a new speedup. Validation and evidence sealing preceded
publication; push completion must be confirmed by reading the remote branch.
Statements below retain the preceding integration/publication history.
# 最新项目状态与本批发布（2026-10-20）

用户授权将当前项目状况保存为Markdown并发布至cc77-builder/riscv的zjhwork。本批包含已有6项O4提交、O2主线选择和状态快照，允许正常快进上传；最终成功与SHA以远端回读为准。

技术主线采用O2，O0–O4已有对应证据；下一步O5/T17及O2减代价审查，G5最终冻结待完成，T16/T18工程冻结后集中开展。源码默认开关未改，人工ACK待实际成员完成。此次仅整理与发布，不重跑已完成工程或改旧封存载荷。

当前入口：[项目当前状况](team/docs/project-status-20261020.md)。下方“未上传/不push/待做”等按历史时点阅读；原始证据保持生成状态。

# 当前主线：O2 两槽弹性 FU（2026-10-20）

按用户“推荐一版并沿用其继续优化”的要求，后续开发采用O2，O1作为冻结对照与回退。G4 batch周期少39.03%，O3应用仅少0.62%–1.50%；完整FU面积+41.41%、VFEX4父级+1.25%。这是一项开发主线选择，最终参赛采用仍须完成O5/T17及G5。

下一步固定O2复现入口、补齐独立复现，同时审查额外性能字段和控制路径成本；后续每次只实施一个有证据支持的优化。工程冻结后再集中编写T16与准备T18。默认源码开关与旧封存证据保持原状，本次只更新计划，未运行新测试或推送GitHub。

详细依据和执行顺序见[O2主线选择](team/docs/o2-mainline-decision-20261020.md)。下方保留历史状态与原始计划，不作为当前待办顺序。

# 当前状态：O4结构与参考时序评估完成（本地）

2026-10-20：4项映射/20项STA/140份路径及13项主机检查通过离线复核，结果见team/optimizations/o4/README.md。
完整FU面积+41.41%，含完整DIV的真实VFEX4面积+1.25%；两版均未满足1ns参考目标，不宣称整核Fmax/功耗。
当前local/o4-cost-20261020，本轮不push、不切换默认。下一项O5/T17独立复现，随后G5最终采用；正式T16后置。
不要重跑已完成O4或改封存证据。下方内容为历史状态/原计划。

# 当前任务：O4结构与时序代价评估（本地）

2026-10-20用户明确授权O4，覆盖下方历史不自动O4的限制。入口team/optimizations/o4/README.md和CONTRACT.md。
本轮新增公共生产接口harness及独立综合/STA工具，不改生产src/ISA/NEMU或旧封存证据；不push、不切换默认、不自动O5/G5，正式T16后置。
工作根/home/riscv/riscv-lab/o4-cost-20261020。失败记录保留；不能把前布局参考库数字当作整核Fmax或实际功耗。

# 当前发布：O2与O3成果交付 zjhwork（2026-10-20）

用户明确要求把当前成果推送GitHub的zjhwork，授权本批正常快进发布到cc77-builder/riscv:zjhwork。
本条覆盖下方历史“不push/本地保存”限制，不授权其他分支、强推、自动O4/O5/G5、默认模式切换或人工ACK。
先读team/docs/o2-o3-publication-20261020.md；结果基点db2281b，实际发布结果以远端SHA回读为准。
G4 batch128降低39.03%；O3全部56项合格作业、1280窗口、768正式样本与Linux/Windows复算通过，35项主机检查通过。
O3中断恢复与后处理问题均已解决，旧记录按历史时点保留。下一项技术工作O4，随后O5/T17、G5；正式T16继续后置。
本轮只发布和更新入口，不重复构建、仿真或改封存证据。以下为历史状态。

# O3应用评估：本轮自动测量及Linux严格重审完成

2026-10-19（任务开始日期），local/o3-gemv-20261019。先读team/workloads/o3-gemv/README.md及对应证据入口。56项合格作业（46项原通过复用、10项恢复补跑，另2项中断尝试保留）、1280窗口、768正式窗口及4项确定性重放通过；Windows原生复算状态另见delivery回执。不要重跑完成campaign或改密封证据。本轮本地保存未push，不自动O4/O5/G5或切换默认模式，正式T16后置。以下为历史状态。

# 当前任务：O3中断恢复进行中（2026-10-20，本地）

原campaign-01在46项通过后中断；两项只有部分日志、无真实完成退出，不能宣称仍在跑或已完成。
当前由resume.py在campaign-02导入46项字节相同证据，仅补跑剩余10项，另2中断尝试保留。
原始campaign-01、镜像和运行源码不修改。恢复编排99f04b9，原execute源码7a642b6，恢复交付工具8aab2ed。
当前进度查/home/riscv/riscv-lab/o3-gemv-20261019/campaign-02/state.json；
恢复启动回执recovery-launch-state.json；新监督根/home/riscv/riscv-lab/o3-gemv-recovery-delivery-20261020。
finish-recovery.py负责通过后的严格复核、封存、Windows复算和本地交付。不要再启动旧launch.py/finish.py或重跑全部测试。
本轮不push，不自动O4/O5/G5/默认切换，正式T16后置。以下状态为历史记录。

# 当前任务：O3 GEMV应用测试进行中（本地）

用户2026-10-19明确授权开始O3。工作分支local/o3-gemv-20261019，基点08fc5b4；
先读team/workloads/o3-gemv/CONTRACT.md及README.md。
26新镜像已编译/ELF审计，22主机检查通过，4项真实O1/O2冒烟已通过；
campaign-01正在正式应用测量，不能提前宣称56项/768正式窗口完成。
运行源码冻结7a642b6，构建软件5fdeba3，后处理工具6df07ca。

原始工作根/home/riscv/riscv-lab/o3-gemv-20261019；
交付监督根/home/riscv/riscv-lab/o3-gemv-delivery-20261019；
Windows入口D:/yanyi/riscv大赛/doc/O3应用测试_20261019。
先查两个state.json和launch-state.json。已经启动的launch.py及finish.py负责继续测量和通过后的严格复核/封存/Windows复算/本地交付；
不要重启已经在跑或完成的campaign，不覆盖原始日志。失败先读真实stderr/退出码，不能静默剔除样本或直接重跑所有任务。

O1/O2复用G4固定硬件，四尺寸(4,8),(8,32),(16,64),(4,13)，两口径/两软件/两方法/三数据集；
不改ISA/NEMU/旧基准和旧证据。最多两个单线程EMU。成果先本地保存，不push、不自动O4/O5/G5/默认切换，正式T16后置。
下文为历史状态。

# 团队 Agent 入口

## 当前状态：O1/O2 G4公平测量完成，本地保存

2026-10-19，local/o2-performance-20261019。先读team/optimizations/o2/performance/README.md及evidence/20261019-performance-ab/README.md。36项真实新运行、478窗口、192正式样本、30主机检查与严格离线重审通过。结果见results-01及final-summary.json；不要重跑完成的campaign或改密封证据。不自动推送/切换默认/G5或代签ACK，正式T16后置。下文保留历史状态。

## 当前任务：O1/O2 同镜像公平性能 G4（已授权，本地）

2026-10-19用户明确要求运行O1/O2公平对比。分支local/o2-performance-20261019，工作根/home/riscv/riscv-lab/o2-performance-20261019，基点07ed301。先读team/optimizations/o2/performance/CONTRACT.md。沿用冻结16镜像及原四场景样本规则，复用G3固定O2 EMU，从同一429硬件文件/依赖重建O1。两模式用各自合法O1/O2观察器、共同T13全局时钟，不改ISA/NEMU/工作负载/黄金数据；只顺序做一个重构建，j2/12G，最多两个单线程EMU。完整保存日志、失败和版本，性能全部实际重跑并离线复算。用户本轮已授权G4，覆盖下文历史未授权G4的限制。不自动推送GitHub、切换默认模式、开展G5或写正式T16报告，不代签人工ACK。

## 当前状态：O2 G3 已通过，本地保存

2026-10-19，local/o2-fullcore-20261019。先读team/optimizations/o2/fullcore/README.md与evidence/20261019-fullcore-validation/README.md。最终合格集合core-02＋supplements-02；recheck-02严格离线重审通过。14项作业满足各自预期，5378正常vdot提交，六项两槽全核覆盖齐全，95主机测试通过；失败尝试保留。不要重跑已完成campaign或改密封证据。G3完成不授权自动G4、push或切换默认模式；没有O2公平性能/PPA/人工ACK，正式T16继续后置。下面各节保留历史时点。

## 当前任务：O2 G3 全核观察器与回归（已授权，本地）

用户于2026-10-19明确要求开始G3。工作分支local/o2-fullcore-20261019，起点901687a；按team/optimizations/o2/CONTRACT.md完成两槽全核观察器、新EMU、hello/vadd、117唯一功能/异常矩阵、T12等价控制、故障参考库和正常恢复。旧G1/G2不自动推进G3的限制现由此授权更新。输出/home/riscv/riscv-lab/o2-fullcore-20261019；旧封存材料保持不变。不推送GitHub、不自动开始G4公平性能、不改变ISA/NEMU/黄金数据，不代签人工ACK。构建前冻结生产源码；只运行一个重构建，默认2编译线程、12G JVM、1个EMU线程。


## 当前任务：O2两槽弹性FU与真实父级联调（本地开发）

2026-10-19用户明确授权实现O2隔离FU，然后完成真实VFEX4/DIV/ClockGate父级联调。工作分支local/o2-elastic-parent-20261019，起点7643b8d；合同team/optimizations/o2/CONTRACT.md。G1/G2真实RTL验证及旧模式兼容回归已完成；工程入口team/optimizations/o2/IMPLEMENTATION.md，正式证据evidence/20261019-elastic-parent。下一步为G3；不自动推进全核G3或性能G4，不推送GitHub。保留旧模式及密封证据，独立输出目录/home/riscv/riscv-lab/o2-elastic-parent-20261019。下方评估阶段不实施RTL的限制为历史记录。

## 当前任务：O2可行性评估与设计合同（本地）

2026-10-18开始、2026-10-19续接完成。基点cd866d52，工作分支local/o2-feasibility-20261018；见 [O2入口](team/optimizations/o2/README.md)、[设计合同](team/optimizations/o2/CONTRACT.md) 与 [轨迹分析](team/optimizations/o2/TRACE_ANALYSIS.md)。本轮只审查生产源码、复算旧轨迹并写合同，不实施O2 RTL、不运行新EMU、不推送GitHub。

结论为有条件进入VFEX4两槽弹性候选的隔离FU/真实父级原型；O2采用、II=1、全核性能和PPA仍未验证。O1 batch的1275次busy等待中1266次对应同窗口正常提交请求，9次属于接受前取消；等待不能当可省周期。正式T16报告后置，核心接口人工ACK待成员确认。下方O1发布授权与未上传文字均为对应历史阶段，不自动授权本轮O2发布或后续实现。

## 当前发布：O1 已完成成果交付 zjhwork

# Previous latest O1 integration scope

Current task: integrate latest zjhwork cd866d52d into James_Hotten 724fbb12f.
Use the latest event observer by default; VDOT_O1_TRACE_PROFILE=frames explicitly
selects the existing atomic-frame/FTQ/CSR observer. Never emit both protocols.
Retain clock-cancellation and all four acceptance/provenance gate repairs.
Imported historical results retain their source bindings; merged RTL needs fresh
validation. Main is excluded and O1 stays off. Current integration record:
team/docs/o1-latest-integration-20261019.md. Statements below describe prior work.

Integration validation: 606 host tests, 35 compiled option cases, three frame
parent modes/four faults, two latest parent modes/seven faults and event-enabled
parent execution pass. Source and archive identity receipts are preserved in
team/evidence/o1-latest-integration-20261019. No new full-core run or merged-source
performance claim. This merge remains local; main and remote refs are unchanged.

The current user authorizes committing and pushing the completed observation
work to James_Hotten, then synchronizing other branches and reviewing all work
for correctness, acceptance vulnerabilities, optimization and performance.
Main is outside this publication scope; O1 remains off by default.
The zjhwork c3c417a26 FU evidence and stricter negative gate are integrated;
that branch's historical publication instructions do not replace this scope.

The current request starts optimization on James_Hotten after branch integration
and review of correctness, acceptance security and performance evidence.
The previous VFEX1 cleanup/main synchronization finished at e9c70db38;
its publication record is team/docs/vfex4-main-sync-20261017.md.
Integration review: team/docs/james-o1-integration-20261018.md.
Current observation work and evidence: team/docs/o1-complete-20261018.md.
Earlier schema-1 observation evidence: team/docs/o1-trace-20261018.md.
Parent clock optimization and earlier evidence: team/docs/o1-parent-20261018.md.
O0 matrix history: team/docs/o0-progress-20261018.md.
The historical O0 matrix runner deliberately pins the d3706f0b8 II4 baseline;
its runs do not imply integrated-source or T14 hardware coverage. The separate
O1 extended runner binds the current patched source, EMU and observer profile.
The retired implementation is recoverable from Git, not a second working-tree
implementation. Recovery and active test entries: team/docs/retired-vfex1.md.
Prior full-core validation in team/docs/james-fullcore-20261016.md executed against
d3706f0b8; it is not a new run of the integrated source. Historical instructions
under team/docs/history describe earlier tasks and do not override current scope.

Production uses VFEX4/VDot with NEMU 1.1.0. T14 input-product fusion is opt-in
(VDOT_T14_FUSED_INPUT=1); the default remains E3 response / II4.
T15 is a standalone parameter experiment, not a full-core SEW16 ISA change.
O0 diagnostics are incomplete. O1 has an opt-in RTL candidate, not accepted
hardware; VDOT_O1_HANDOFF remains off by default and requires T14 when enabled.
Three FU and real VFEX4 parent modes have simulation evidence. The parent uses
production dividers and clock gates; canceled-owner clock holds are cleared in
all three VFEX4 modes. O1 parent II2 is measured; full-core O1 acceptance remains pending.
Clock pulse reductions are simulation activity, not measured power or STA/PPA.
The frozen T12/T13 observers cannot validate O1 overlapping transactions.
VDOT_O1_TRACE is a separate default-off schema. Atomic ungated EXU frames and
ROB events are checked with the explicit one-cycle redirect delay. Three real
parent modes, trace-off RTL byte equivalence, and log corruption checks pass.
The new source-bound O1 EMU passes hello/vadd, control, 117 unique matrix cases
(124 executions), real bit100 DiffTest injection and same-image normal recovery.
The O2 companion preserves schema 1 and adds FTQ identity and CSR ownership,
sampling and per-commit-slot windows. Control records 2157 VDot commits, 384
handoffs and 329 FTQ wraps; calibration/batch validate 25 windows and 100 CSR
samples. All 13 actual launches meet expectations (12 exit 0, one injected exit 1).
72 host tests and 15 real-log corruption checks pass. Current O1 original/lean
software-plan runs and full same-source performance A/B remain separate work.
The observation checkpoint fb1e7bdc8 is pushed to James_Hotten. Both remotes
were fetched again; all ten actual remote branch tips are already included.
The four gate defects from team/docs/o1-publication-review-20261018.md are
repaired; closure and limits: team/docs/o1-gate-fixes-20261018.md. Aggregate
host checks pass (504), with 13 archived CPU logs rechecked, 24 FTQ mutations,
15 prior corruption checks and 8 real parent binary replays. No new CPU run
or performance claim is made. This publication includes the reviewed repairs; production
RTL and historical evidence bytes are unchanged. O1 remains off by default.
Preserve archive bytes, source bindings, failure records and fail-closed checks.
Do not fabricate teammate approval, STA/PPA, performance, virtualization or
official ISA acceptance. Reports follow engineering completion and version freeze.
