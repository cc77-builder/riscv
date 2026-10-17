# 三人团队：项目计划与开发入口

> **2026-10-17 四项目统一测试交付至 zjhwork。** 同一香山基础版本/MinimalConfig/VLEN128下，四个实现64个全核镜像、860个窗口通过；正式性能样本384个。四路独立点积加速比：本项目1.496×、Jade2.605×、试水2.322×、Redoop＋dot8适配0.929×。见 [完整结果](docs/unified-vdot-comparison-20261017.md)、[程序](workloads/unified-vdot/README.md) 和 [验证归档](evidence/unified-vdot-20261017/README.md)。这是T15后的补充比较，未自动推进T16或新增人工ACK；下方“未上传”等为历史时点快照。

> **T15 成果交付至 zjhwork。** 用户已授权上传成果 `13851b2482603ac9f96c850795c697f4e3a6bf44` 及本次交付入口说明。新增 s16x8/r64 独立参数单元、参考模型、94＋10000 组扩展数据、协议测试和 Linux/Windows 离线核验材料。实际正式验证源码为 `65f6159`，本发布批次只补充说明。见 [T15 报告](docs/t15-parameter-extension.md) 和 [最新计划进度](docs/progress-t15-20261017.md)。下方及密封材料中的“未上传”保留为发布前历史记录；人工复核仍待完成，下一项为 T16。

> **2026-10-17 T15 本地自动验收完成，尚未上传。** 已验证 8 对 int16 的独立参数单元，94 定向＋10000 随机完整结果、单请求协议与跨平台离线复核通过。T14/T15 两项 G5 开发验证已具备，下一项是 T16 材料整合；人工复核待完成。见 [T15 报告](docs/t15-parameter-extension.md) 和 [最新计划进度](docs/progress-t15-20261017.md)。本轮没有扩展全核 ISA。

> **2026-10-17 T14 成果，本次交付目标 zjhwork。** 用户已授权上传已验收成果 `458b7170bfdf41814dac785b41027114bddd512d`；本次另补充进度说明，不改变硬件或测试数据。**技术主线到 T14，处于 G5；下一项为 T15 参数扩展。** 完整状态见 [T00–T18 进度表](docs/progress-20261017.md)。团队人工复核、语义歧义确认及最终比赛交付仍待完成；下方和报告中的“未上传”为发布前历史记录。

> **2026-10-17 T14 本地自动验收完成，尚未上传。** 输入拍锁存乘积使 FU 响应 3→2 拍、最小 II 4→3；完整回归、126 次相同镜像运行、1,404 个性能窗口及 Linux/Windows 离线复核通过。128 次独立点积约 1.29×，256 次依赖链约 1.14×，访存场景收益很小。见 [结果与局限](docs/t14-optimization.md)、[合同](spec/t14-ablation.md)、[外部建议评估](docs/t14-suggestion-review.md) 和 [离线回执](evidence/t14-offline-review-20261017/README.md)。默认基础模式保留，团队人工复核及物理时序评估待完成。

> **T13 交付至 zjhwork。** 用户已明确授权将本轮成果上传到 `cc77-builder/riscv` 的 `zjhwork`。代码、报告和验证证据版本为 `4526d857937def29ea1598a7c878aa539e2ef1f6`，本发布批次只补充入口说明，未改变硬件、工作负载或测量数据。见 [性能报告](docs/t13-performance.md) 和 [离线复核](evidence/t13-offline-review-20261015/README.md)。下方及归档中的“未上传”是发布前快照；队友人工复核仍待完成，不能把上传当作人工验收。

> **2026-10-15 T13 本地自动验收完成，未上传 GitHub。** 固定版本的 RVV/vdot 公平周期对照通过 108 次全核功能调用与 1,404 个性能窗口，3 次重放一致。见 [T13 报告](docs/t13-performance.md)、[测量约定](spec/measurement.md) 和 [离线证据](evidence/t13-performance-20261015/README.md)。T12 已按用户要求发布到 `zjhwork`；T13 位于独立本地分支 `local/t13-performance-20261015`，待队友复核，未代签 ACK。后续可按计划 G5 选择单一优化做 A/B；PPA、虚拟化及人工签字仍未完成。

> **2026-10-14 历史记录：当时本机 T12 自动回归通过，待人工复核/发布。** 11 项全核运行满足预期，控制压力覆盖和原功能矩阵通过。当前成果仅在独立本地分支 `local/t12-regression`；共享远端进度没有随本地结果自动改变。见 [T12 报告](docs/t12-regression.md) 和 [完整证据](evidence/t12-regression-20261014/README.md)。下方 10 月 13 日及更早文字为历史阶段记录。

> **2026-10-13 历史验收：** T10 最小全核接入和 T11 固定功能矩阵已通过，117唯一用例（80合法/37异常）、vdot bit100差分负控及同镜像正常恢复均有完整原始日志。详见 [当前验收报告](docs/t10-t11-acceptance-20261013.md) 和 [证据入口](evidence/t10-t11-fullcore-20261013/README.md)。下方早期“尚未接入/未实现NEMU”等进度是历史快照，以本段链接的分层状态为准；仍未完成全核乱序控制压力、虚拟化、性能及PPA验收。

> **2026-10-13 历史发布状态：已完成合并发布。** 用户确认双方无人开发后，已将验收候选 `734353d01e963610ac864fdddd81e01e91f521fe` 普通快进发布到团队及 Fork 的 zufan，两端 SHA 回读一致。见 [发布记录](merge/2026-10-13-zjhwork-into-zufan.publication.md)；[完整局部验收](merge/2026-10-13-zjhwork-into-zufan.codex-review.md)通过组合 22+10000 组、FU 6 类/71258 周期。后续两人共享 zufan，下一班须核对最终 SHA 并记录 ACK/START。

本队以《香山 vdot 赛题：执行计划》和《香山 vdot 赛题：三人分工与 Git 协作》作为项目计划文档，分别安排里程碑、验收标准和三人职责。成员先阅读两份计划，再按认领的任务推进开发。

本目录同时保存本队在 2026-10-09 完成的环境搭建、hello/vadd 源码和阶段一证据，并提供按当前仓库位置运行的脚本。香山硬件基线为 `16ae9ddcda54fc9a2fddffad73174cf793ac7814`。`zjhwork` 已提供 vdot 数学模型、RTL 接口设计、组合算术和已通过控制测试的 FU 包装层；香山全核接入和 NEMU 扩展尚未实现。计划中的后续任务按实际验收结果更新进度。

| 内容 | 入口 |
| --- | --- |
| 四项目统一测试、公开实现对比与验证记录 | [结果](docs/unified-vdot-comparison-20261017.md) · [程序](workloads/unified-vdot/README.md) · [证据](evidence/unified-vdot-20261017/README.md) |
| T15 独立参数扩展、验证结果与边界 | [T15 报告](docs/t15-parameter-extension.md) · [参数合同](spec/t15-parameters.md) |
| T15 原始证据与跨平台核验 | [证据](evidence/t15-parameters-20261017/README.md) · [离线复核](evidence/t15-offline-review-20261017/README.md) |
| T15 完成后的计划状态 | [最新进度](docs/progress-t15-20261017.md) |
| T14 单一优化消融、完整数据与局限 | [T14 报告](docs/t14-optimization.md) |
| T14 原始证据及跨平台核验 | [证据](evidence/t14-optimization-20261016/README.md) · [离线复核](evidence/t14-offline-review-20261017/README.md) |
| T13 公平周期性能对比、完整数据与局限 | [T13 报告](docs/t13-performance.md) |
| T13 可搬迁离线复算与原始证据 | [T13 证据包](evidence/t13-performance-20261015/README.md) |
| 当前协作机制：无 Actions、共享分支交接、Fork 按需同步 | [三人两线协作机制](docs/collaboration-current.md) |
| 项目计划：阶段目标、执行步骤与验收标准 | [香山 vdot 赛题：执行计划](香山vdot赛题_执行计划.md) |
| 项目计划：A/B/C 分工、评审与 Git 协作 | [香山 vdot 赛题：三人分工与 Git 协作](香山vdot赛题_三人分工与Git协作.md) |
| vdot 指令语义、候选编码、测试与待确认问题（第一版草案） | [vdot.vv 规格](spec/vdot.md) |
| 独立数学模型、定向/随机测试数据及一键检查（T05） | [vdot 模型与数据](models/vdot/README.md) |
| T05 主机检查结果、数据来源与已知边界 | [模型验证记录](evidence/model-20261012/README.md) |
| T06 接口草案：VFEX4 接入、逐拍时序、异常与验证矩阵 | [RTL 接口与接入设计](spec/rtl-interface.md) |
| T07-A 组合算术 RTL、独立构建和一键验证 | [点积算术单元](rtl/vdot/README.md) |
| 22 组定向 + 10,000 组随机完整 128 位比较结果 | [RTL 算术验证证据](evidence/rtl-datapath-20261012/README.md) |
| T07-B 真实 FU：反压、取消、身份、异常及一键测试 | [FU 包装层](rtl/vdot/FU.md) |
| 6 类场景、71,258 周期、事务守恒和预期拒错 | [FU 验证证据](evidence/rtl-fu-20261013/README.md) |
| WSL、工具版本、安装方法、配套依赖 | [环境说明](docs/environment.md) |
| 构建和运行命令、启动问题、通过标准 | [阶段一说明](docs/stage1.md) |
| hello/vadd 测试源码 | [workloads/hello-vadd](workloads/hello-vadd/) |
| 路径可配置的执行脚本 | [scripts](scripts/) |
| 昨天的通过日志、配置、反汇编和事件 CSV | [历史证据](evidence/stage1-20261009/) |
| 今天用仓库内脚本重新运行的验证结果 | [脚本验证记录](evidence/script-check-20261010/README.md) |
| 源码锁定版本 | [versions.env](versions.env) |

## 历史开发进度（T07 时点）

T05 数学模型、T07-A 组合算术和 T07-B 独立 FU 均已有通过证据；T06 人工评审及接入验证仍待完成。FU 在真实香山 Bundle/RobPtr 下通过 10,022 组算术输入、反压、非法配置、取消、复位和随机控制测试。复现运行 `bash team/scripts/check-vdot-fu.sh`；纯算术入口 `bash team/scripts/check-vdot-datapath.sh` 继续保留。下一步按计划推进 NEMU 扩展与 T10 译码/VFEX4 接入，再做全核 DiffTest，见 [RTL 设计第 8 节](spec/rtl-interface.md#8-实施顺序三人交接与完成标准)。

## 新成员操作顺序

先接受私有仓库邀请。在 Ubuntu 22.04 / WSL2 的 Linux 文件系统中：

```bash
# 取得团队代码后核对最终 SHA，记录接收，再开始开发
git clone --branch zufan --recurse-submodules https://github.com/cc77-builder/riscv.git
cd riscv
bash team/scripts/prepare-dependencies.sh
# 按 docs/environment.md 安装匹配的工具，已有环境可跳过安装
bash team/scripts/check-environment.sh
export TEAM_EVIDENCE_DIR="$PWD/team/out/my-stage1"
bash team/scripts/stage1.sh nemu
bash team/scripts/stage1.sh emu
bash team/scripts/stage1.sh workload
bash team/scripts/stage1.sh run
```

配套 xs-env 默认位于 `$HOME/riscv-lab/xs-env`。需要放在其他位置时，先 `export TEAM_XS_ENV_ROOT=/你的目录/xs-env`。脚本把当前团队仓库作为 `NOOP_HOME`，配套环境只提供 NEMU、nexus-am、DRAMsim3 及安装工具入口。

历史成员环境路径为 `/home/riscv/riscv-lab/xs-env/XiangShan`，不能假定其他电脑存在同一路径。本次独立本机检出位于 `/home/lizufan/xiangshan-validation-20261013/repo`，只做组合/FU验证，未建立完整 NEMU/全核环境。已有仿真器仅在源码/配置完全对应时复用。

默认采用 MinimalConfig、单核、单仿真线程、JVM 12G、构建并行度 2。`BUILD_JOBS`、`JVM_HEAP` 可显式调整；普通运行不生成波形，使用 `DUMP_WAVE=1 bash team/scripts/stage1.sh run` 可生成 FST。各步骤输出保存到 `team/out/`，不会自动进入 Git。

## Git 协作（2026-10-13 当前约定）

请先阅读 [三人两线协作机制](docs/collaboration-current.md) 和根目录 [AGENTS.md](../AGENTS.md)。目标为 `zufan` 两人共享开发线、`James_Hotten` 另一开发线，`main` 保持稳定；`zjhwork → zufan` 已完成合并发布与局部验收，不自动删旧分支。

两人**独立工作区并行开发/验证**，仅团队共享远端 `zufan` 的 Push 在 START → RELEASE → ACK 协议下错峰进行；所有验收绑定实际 SHA，不强推、不让后续代码静默改变已评审 PR。交接主记录位于团队仓库的一个统一位置，Issue/Discussion 或 Markdown 均可，不强制 Issue。

协作、回归与 Fork 按需同步**均不依赖 GitHub Actions**；源仓库现有 workflow 文件保留作参考。Fork `LiZufan001/riscv` 并非实时自动镜像，正常快进同步前必须比较源/目标分支，不覆盖独有提交。

### 历史说明：旧版单任务功能分支流程（不是当前共享线的默认操作）

**历史用法（合并前记录，不是当前推送指令）：** 从数学模型这一步开始，开发内容曾先提交和推送到 `zjhwork` 分支，暂不合并或推送到 `main`。现有本机仓库使用 `git push team zjhwork`；新克隆仓库使用 `git push origin zjhwork`。其他成员取得本轮内容后，运行 `bash team/scripts/check-vdot-model.sh` 复核。

团队常规协作使用任务分支并通过 Pull Request 合并；该历史阶段以 `zjhwork` 约定为准。需要另开任务分支时，先约定基准分支和合并目标。新成员克隆目录的团队远程是 `origin`；现有本机仿真目录的团队远程是 `team`。

```bash
git switch -c feat/自己的任务名
git add 具体文件
git commit -m "feat: describe the change"
git push -u origin feat/自己的任务名
```

在现有本机仿真目录，将最后一行的 `origin` 换为 `team`。NEMU 源码仍是外部配套仓库；后续修改 NEMU 或香山子模块时，需把其提交推送到团队可访问的对应仓库并更新版本引用。
