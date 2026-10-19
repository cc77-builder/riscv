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

用户明确授权将真实父级联调、全核回归和T14/O1公平性能结果普通快进上传至 cc77-builder/riscv:zjhwork。见 [交付说明](team/docs/o1-publication-20261018.md)。本条覆盖下方“本地保存/未上传”的当前限制；密封证据保留生成时点状态。实际推送结果以远端SHA回读回执为准，O1默认关闭，不重复已完成仿真，不自动开始下一项任务。

## 当前任务：T14/O1 同镜像公平性能比较完成，本地保存

独立batch128平均周期 453.25→362.50，降低20.02%；O1相对实测RVV为1.870×。36次主运行、478窗口、192正式样本、4次额外确定性重放及完整原始日志离线复算通过；最后22项主机检查通过。

见 [工程入口](team/optimizations/o1/performance/README.md)、[合同](team/optimizations/o1/performance/CONTRACT.md) 和 [证据](team/optimizations/o1/evidence/20261018-performance-ab/README.md)。实际执行检查器、受测硬件源码、二进制和后续导出工具身份分别记录。不要重启已经完成的campaign或覆盖原始/密封证据。

分支local/o1-performance-20261018，工作根/home/riscv/riscv-lab/o1-performance-20261018。成果本地保存，未推送GitHub，O1默认关闭；O2按收益/接口成本另行决定，O3应用、O4时序代价、O5/T17独立复现及人工ACK仍未完成，正式T16报告继续后置。

## 前一轮：O1 全核功能与控制回归、严格离线复核通过

用户 2026-10-18 要求的 O1 观察器适配及本轮全核回归已完成，工作分支为 `local/o1-fullcore-20261018`。MinimalConfig 单核 EMU 的硬件构建源码为 `18c0ce08a40e889654bfe76d5435f272854ad7d0`，原运行检查器冻结在 `518c05674d5ecfed04a944cf01c99cea488b6c8a`；运行结束后以 `d110002006001d45a39dbc00591a299672940818` 集成严格日志门禁，并对同一份未修改原始日志完成离线全套重审，没有再次运行 EMU。十二项作业全部符合预期（十一项正常通过、一项 bit100 差分负控按预期拒错），同镜像正常参考库恢复通过；主机检查 41＋25＝66 项通过。先读 [全核工程入口](team/optimizations/o1/fullcore/README.md)、[日志门禁](team/optimizations/o1/audit/README.md) 和 [归档证据](team/optimizations/o1/evidence/20261018-fullcore-validation/README.md)。

正常程序共提交 3,012 条 vdot；功能矩阵为 117 个唯一用例（80 合法、37 异常），八分片共执行 124 次。控制程序独立满足八项覆盖，记录 303 次同拍交接、62 拍 vdot 写回反压、3 次在途取消；密集程序的 12 个窗口通过，另有 725 次同拍交接及 2 次取消。全核共享 FU 覆盖 vdot 与 VIDiv，未覆盖 VFDiv；所观察到的 vdot 取消仅在 reduce 阶段，不扩大为所有取消阶段或 DIV 取消已验收。

当前 `fullcore_validation_pass=true`、`offline_full_suite_recheck_pass=true`，完成范围仅为本轮固定配置的功能、异常和控制验证；没有新性能 A/B、PPA、T17 或团队人工 ACK 结论。下一项技术工作为同镜像 T14/O1 公平性能对照；本轮成果本地保存，不推送 GitHub，O1 默认关闭，正式 T16 报告继续后置。下文保留各历史阶段的状态。

## 前一轮：真实 VFEX4 父级联调已通过，本地保存

用户 2026-10-18 要求“开始真实 VFEX4 父级联调，包含 DIV 切换、反压及取消”。在本地分支 `local/o1-parent-validation-20261018` 完成，实际受测源码 `99d5f6c751234622b8f824ed7fcee39f3aae711d`；本轮没有新 Push，不改远端分支。下方 FU 已发布状态和旧父级未验证状态为历史记录。

先读 [父级工程记录](team/optimizations/o1/parent/README.md) 与 [原始证据](team/optimizations/o1/evidence/20261018-parent-validation/README.md)。`parent-02` 的真实两模式、七项检查器负控通过；O1 接受 13659、响应 13087、取消 510、复位丢弃 62、同拍交接 10343 次。所有原始失败/探针记录保留，本轮生产 src、依赖、ISA/NEMU/黄金数据未变化。交付后唯一测试源变动是纠正一条过强注释，非注释行一致，补丁单独归档；不因文档/注释重跑构建。

T14 baseline 在 reset/redirect 周期抑制输入 valid 是测试限制，不是已证明的系统合同。DIV 取消当拍旧 valid 和取消后门控仍开已如实记录；不能据此宣称 ROB 提交/整核验证通过。当前 `parent_exu_elaborated=true`、`parent_validation_pass=true`、`fullcore_difftest=false`、`performance_measured=false`。下一项为 O1 观察器、全核回归，然后同镜像性能 A/B；默认 O1 仍关闭，正式 T16 报告继续后置，不代签人工 ACK。


## 前一轮：O0/O1 复用与三模式 FU 验证（已发布的历史记录）

2026-10-18，用户明确要求“接下来复用 O0，沿用 O1 候选，先修这两处，再跑三模式 FU 验证。先拉取到本地，本地测试通过再上传 zjhwork”。本轮已在独立本地分支复用 `zjhwork2@75dce60`，本地验证通过；授权将该批成果及修复普通快进推送至 `cc77-builder/riscv:zjhwork`。发布前核对实时远端与祖先关系，发布后回读 SHA，实际推送以回执为准。本节覆盖下方历史分支限制，保留 zjhwork2 原记录，不授权写入其他分支或自动展开下一项任务。

先读 [O1 工程入口](team/optimizations/o1/README.md)、[本轮证据](team/optimizations/o1/evidence/20261018-fu-validation/README.md) 和 [优化入口](OPTIMIZATION.md)。真实构建源码为 `db0408aa42afc13e3ff93e865f26a2d5bfb02c93`。修复包括激活环境后再预检工具、严格负控及独立漏检退出码，以及首轮编译发现的 `ExeUnit.scala` 两处 `FuType.vdot.U` 类型比较。保留 `fu-01` 编译失败和 `fu-02` 三模式通过证据，不覆盖旧归档，不因文档提交重复构建。

O0 113 项、O1 26 项主机检查通过；真实 FU 延迟/最小接受间隔为原基础 3/4、T14 2/3、O1 2/2 拍。O1 接受 13626、响应 13212、取消 388、复位丢弃 26，同拍交接 12237 次、反压 26659 拍。原 10022 算术向量加控制场景通过；候选与旧模式控制矩阵不同，四项负控属于 C++ 观测值破坏检错。不得将主机合同测试或 Scala 编译称为真实父级联调。

当前 `parent_exu_elaborated=false`、`fullcore_difftest=false`、`performance_measured=false`；O1 默认关闭，无新增全核加速比或 PPA 证据。下一步为真实 VFEX4 父级（含 DIV）联调。正式 T16 报告继续后置，开发命令、版本与原始证据持续保存；不代签成员 ACK。

## 本轮发布：四项目统一测试上传 zjhwork

用户明确要求“上传github到zjhwork分支，留个记录”，授权将三项统一测试本地提交及本轮结果/证据/入口说明普通快进推送至 `cc77-builder/riscv:zjhwork`。发布前远端为 `05e07deaf7ba1f8c0dbb2d2c2bd2d2db7e051a37`，是本地成果的祖先。本节覆盖下方历史上传限制，不授权自动开始后续任务。

先读 [本次交付记录](team/docs/unified-vdot-publication-20261017.md)、[结果](team/docs/unified-vdot-comparison-20261017.md) 和 [证据](team/evidence/unified-vdot-20261017/README.md)。64镜像、860窗口、384正式性能样本已通过；本次仅整理上传，不重复运行硬件或改动既有生产RTL。原归档的未上传状态保留为历史快照。推送后必须回读远端SHA，实际回执放在Windows `doc/四项目统一测试_20261017/Git交付/`。上传不代表人工ACK、官方排名或完成PPA/T16。

## 本轮发布：T15 上传 zjhwork

用户已明确要求“把这次 T15 的成果上传到 zjhwork 分支”，授权将成果提交 `13851b2482603ac9f96c850795c697f4e3a6bf44` 及本次交付入口说明普通快进推送到 `cc77-builder/riscv:zjhwork`。发布前远端为 `6fea2969d05dc4cb168795a60e2e6ee9ca1f9988`，是本地祖先。本节覆盖下方对本次 T15 暂不上传的历史限制；后续任务按新的明确指示推进。

当前状态见 [T15 后计划进度](team/docs/progress-t15-20261017.md)。本发布批次只更新交付与计划入口，不改变硬件、模型、测试数据或密封证据。实际正式验证源码仍为 `65f6159e305adc10b4f8bd67812f3a6460ccf360`。普通推送后回读最终远端 SHA；回执保存在 Windows `doc/T15参数扩展/Git交付/`。原报告和离线包中的“未上传”为生成时点的历史快照。上传不代表人工 ACK；T15 仍为独立单元参数验证，T16 尚未开始。

## 历史状态：T15 独立参数单元已完成，本地保存

2026-10-17。用户要求完成 T15 后先不上传 GitHub，禁止本轮 push、PR 或更改 main/zufan/zjhwork。当前分支 local/t15-s16x8-20261017，工作区 `/home/riscv/riscv-lab/t15-parameter-extension-20261017/repo`，起点为已发布 T14 6fea296。

先读 [T15 报告](team/docs/t15-parameter-extension.md)、[参数合同](team/spec/t15-parameters.md)、[最新进度](team/docs/progress-t15-20261017.md) 和 [跨平台复核](team/evidence/t15-offline-review-20261017/README.md)。实际正式验证源码 65f6159e305adc10b4f8bd67812f3a6460ccf360；runs/unit-02 为最终验收，两个单元配置、8 个非法参数、错误检出及 Linux/Windows 离线核验通过。不要重复启动已完成任务或覆盖密封证据。

本轮为 s16x8/r64 独立算术/实验包装，不是全核 SEW=16 指令；原生产 src 树、NEMU、ISA 和 T05 向量保持不变。初次 Windows manifest 路径失败及修复记录保留；生成器路径改为 POSIX，四份数值文件未变化。T14 现有主频/PPA 边界继续有效。没有新增人工 ACK，不自动开始 T16。Windows 交付入口 D:\yanyi\riscv大赛\doc\T15参数扩展。

## 本轮发布：T14 上传 zjhwork

用户于 2026-10-17 明确要求“把这次 T14 的成果上传到 zjhwork 分支”，并查看计划进度。授权将 T14 成果提交 `458b7170bfdf41814dac785b41027114bddd512d` 及本次进度/入口说明普通快进推送至 `cc77-builder/riscv:zjhwork`。发布前回读 zjhwork 为 `3b337a5b186ed60163a8d11edaeb3677dfd67750`，是本地祖先。本节覆盖下方对本次 T14 暂不推送的历史限制；不授权向 main/zufan 推送或自动发布后续 T15。

当前计划进度见 [T00–T18 / G0–G7 清单](team/docs/progress-20261017.md)。本次只补充进度与发布入口，不改变硬件、程序、验证结果或密封证据；不把上传视为成员 ACK。普通推送后必须回读远端 SHA，实际回执保存在 Windows `doc/T14优化/Git交付/`。原始未上传状态按生成时点保留。

## 历史状态：T14 完成本地自动验收，发布前记录

2026-10-17 完成交付复核。工作区 `/home/riscv/riscv-lab/t14-optimization-20261015/repo`，分支 `local/t14-fused-input-20261015`。T13 已发布到 zjhwork；该次上传授权不代表自动发布 T14。本轮不得推送 main、zufan 或 zjhwork。

先读 [T14 报告](team/docs/t14-optimization.md)、[合同](team/spec/t14-ablation.md)、[建议评估](team/docs/t14-suggestion-review.md) 和 [跨平台回执](team/evidence/t14-offline-review-20261017/README.md)。唯一优化是 VDOT_T14_FUSED_INPUT=1 输入拍乘积锁存；默认 0 保留基础版。实际构建源码 2443fb1c101dfc5974ac208275a8b86d68a11e0f，只有 VDot.scala 的生产硬件变化；文档提交不是新构建。

两模式 FU 完整测试、候选全核回归、13 个校准窗口、48 个固定镜像共 126 次运行及 1,404 个性能窗口通过。runs/fullcore-02/campaign-state.json 为 T14_CANDIDATE_FULLCORE_PASS；runs/t14-postprocess-state.json 为 LINUX_ARCHIVE_AND_REPORT_COMPLETE。Linux 与 Windows 离线复算均通过，图表自动及模型视觉复核完成。不得重复启动已完成的长任务或覆盖原证据。

runs/fullcore-01 的原始写回反压覆盖不足完整保留；同一个补充 F2v 扫描镜像在基础/候选均通过（反压 137/138 周期），其他 10 个已完成 T12 作业逐字节复用并有来源回执。不能把复用称作重跑。基础/候选所有性能镜像、参考库与测量边界固定。

证据 team/evidence/t14-optimization-20261016 已封存；新核验材料放在相邻目录，不改旧归档。Windows 交付入口 D:\yanyi\riscv大赛\doc\T14优化。原 T12/T13 构建及数据只读保留。尚无综合/STA/Fmax/PPA 证据，尚未完成团队人工 ACK 或新机器完整构建复现；不自动开始 T15 或切换默认模式。

## 历史交付：T13，目标 zjhwork

用户最新明确指示“上传到 zjhwork 分支”，授权本轮将已验收 T13 提交 `4526d857937def29ea1598a7c878aa539e2ef1f6` 及这次入口说明普通快进推送到 `cc77-builder/riscv` 的 `zjhwork`。本次发布前已确认远端为 T12 基线 `2c0bf8e283d400c1c946ca75f890f266d7758411`，是本地成果的祖先。本节覆盖下方旧任务中的暂不上传、禁止写 zjhwork 等历史限制；不授权写入其他分支或任意后续推送。

本批次只更新文档入口，实际硬件、程序、校验器与证据仍以 T13 报告和固定摘要为准。普通推送成功后需回读远端 SHA；发布操作回执保存在本地 T13 交付目录。下方和归档中“未上传”为当时状态，原字节保留。没有新增人工 ACK；后续优化仍须按既有计划复核。

## 历史阶段：T13 公平周期比较完成时的发布前记录

先读 [T13 报告](team/docs/t13-performance.md)、[测量约定](team/spec/measurement.md) 与 [离线证据](team/evidence/t13-performance-20261015/README.md)。T12 已按用户指示发布到 zjhwork，基线为 `2c0bf8e283d400c1c946ca75f890f266d7758411`；本轮 T13 在独立本地分支 `local/t13-performance-20261015` 完成，用户明确要求做完先不上传 GitHub。没有 Push、PR、main 合并或新的人工 ACK。

本轮 108 次全核功能调用、1,404 个性能窗口及 13 个校准窗口通过；三个全新 EMU 重放逐窗口一致。硬件仅添加观察器，实际 EMU 来源与后续软件/文档提交分开固定。先由队友复核测量合同和离线数据，再按计划 G5 选择一个优化做 A/B。不能把通用调用中 CSR 管理开销产生的最大比值宣传为通用应用收益；PPA、虚拟化、官方语义确认及人工签字未由本轮补齐。

## 历史阶段：T12 自动回归通过时的记录

先读 [T12 报告](team/docs/t12-regression.md) 与 [可离线复核的证据](team/evidence/t12-regression-20261014/README.md)。本轮本地分支 `local/t12-regression` 基于 `6bf3c2c3be0c88ff3a020786ff10cbec9aa126d3`；11 项实际运行满足预期，主机 108 项检查通过。硬件源码、执行软件 SHA 和实际二进制摘要分别列出，不把文档提交当作重新构建。共享分支尚未发布本轮成果；禁止据此虚构 START/RELEASE/ACK 或人工评审。下一项为公平 RVV/vdot 周期对照；T13、PPA、虚拟化和人工签字均未完成。以下保留 T10/T11 历史阶段信息。

## 历史阶段：T10 最小全核接入、T11 固定功能矩阵已验收

先读 [本轮验收与边界](team/docs/t10-t11-acceptance-20261013.md)、[可独立复算的实际证据](team/evidence/t10-t11-fullcore-20261013/README.md) 和 [两线协作约定](team/docs/collaboration-current.md)。固定被测源码 `1bd6f1d9c9485695876ff37a77fbb175a5125983`，其生产 RTL / build.sc 与实际 EMU 来源 `fcb16a8764d342339670df0bbf1bc67ef2028b86` 相同。后续发布提交只增加验收器修复、来源记录与文档。

本轮真实 MinimalConfig 全核 DiffTest 通过 117 个唯一用例（48 定向、32 固定随机、37 精确异常）；8 片仅 D00 重复，124 条 extension 记录，另有56个自检和24个harness预期拒错。vdot 的 bit100真实差分注入在对应 PC/目的寄存器报错；同一镜像换回正常参考库后 shard-0 完整通过。不能把这批功能矩阵当成所有乱序/虚拟化/性能验收。

## 已授权开发与交接

团队唯一上游为 `cc77-builder/riscv`，共享开发目标为 `zufan`；个人 `LiZufan001/riscv` 只是按需快进同步。用户本轮要求完成剩余任务，本轮发布仍须先核对实时远端和无冲突的快进关系。本文不伪造两位成员的 ACK，不创建锁，不授权读到文件即自动开工。最终完整提交 SHA、Push 与双远端回读以实际任务回执为准，不在包含自身的提交中预填。

两人使用独立工作树和输出目录；仅共享远端 Push 按 START → RELEASE → ACK 有序交接。保留既有未提交和未发布成果，不 reset/clean/stash 掩盖他人工作；不强推、不改写历史、不删除 zjhwork，不向 main/James_Hotten/zjhwork 写入。GitHub Actions 完全不依赖，原 workflow 未改。

## T10/T11 时点的后续工作（历史）

优先 T12：需要真实触发与观察的 VL/CSR 紧邻依赖、RAW/WAW、共享 VFEX4 与写回竞争、年轻 vdot 发射后被取消、ROB/FTQ 绕回；随后做公平 RVV 配对周期测量。M/HS/VS 委托与虚拟化尚未验证；综合/STA/功耗、官方规格确认、人工接口签字仍未完成。现有 FU 的 E0/E2/E3/II4 仅是局部握手时序，不是全核指令周期或频率。

原模型、datapath、FU、decode 入口在 `team/scripts/`；每次真实运行用新输出目录。当前 NEMU 补丁为1.1.0及显式平台配置；禁止混用旧参考库、跳过vdot差分或修改黄金结果来消除错误。原Windows WIP目录保留；本轮Linux发布工作区见验收报告，不直接覆盖原开发目录。

旧入口见 [历史快照](team/docs/history/AGENTS-before-t10-closure-20261013.md)，旧阶段报告、测试日志、补丁1.0.0原字节均保留。
