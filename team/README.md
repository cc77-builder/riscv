# 三人团队：项目计划与开发入口

本队以《香山 vdot 赛题：执行计划》和《香山 vdot 赛题：三人分工与 Git 协作》作为项目计划文档，分别安排里程碑、验收标准和三人职责。成员先阅读两份计划，再按认领的任务推进开发。

本目录同时保存本队在 2026-10-09 完成的环境搭建、hello/vadd 源码和阶段一证据，并提供按当前仓库位置运行的脚本。香山硬件基线为 `16ae9ddcda54fc9a2fddffad73174cf793ac7814`。`zjhwork` 已提供 vdot 数学模型、RTL 接口设计、组合算术和已通过控制测试的 FU 包装层；香山全核接入和 NEMU 扩展尚未实现。计划中的后续任务按实际验收结果更新进度。

| 内容 | 入口 |
| --- | --- |
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

## 当前开发进度

T05 数学模型、T07-A 组合算术和 T07-B 独立 FU 均已有通过证据；T06 人工评审及接入验证仍待完成。FU 在真实香山 Bundle/RobPtr 下通过 10,022 组算术输入、反压、非法配置、取消、复位和随机控制测试。复现运行 `bash team/scripts/check-vdot-fu.sh`；纯算术入口 `bash team/scripts/check-vdot-datapath.sh` 继续保留。下一步按计划推进 NEMU 扩展与 T10 译码/VFEX4 接入，再做全核 DiffTest，见 [RTL 设计第 8 节](spec/rtl-interface.md#8-实施顺序三人交接与完成标准)。

## 新成员操作顺序

先接受私有仓库邀请。在 Ubuntu 22.04 / WSL2 的 Linux 文件系统中：

```bash
git clone --recurse-submodules https://github.com/cc77-builder/riscv.git
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

已有本机环境仍使用原来的 `/home/riscv/riscv-lab/xs-env/XiangShan`，不用重新克隆或重新编译已有且配置相同的仿真器；直接从该目录运行上面的环境检查、workload 和 run 即可。

默认采用 MinimalConfig、单核、单仿真线程、JVM 12G、构建并行度 2。`BUILD_JOBS`、`JVM_HEAP` 可显式调整；普通运行不生成波形，使用 `DUMP_WAVE=1 bash team/scripts/stage1.sh run` 可生成 FST。各步骤输出保存到 `team/out/`，不会自动进入 Git。

## Git 协作（2026-10-13 当前约定）

请先阅读 [三人两线协作机制](docs/collaboration-current.md) 和根目录 [AGENTS.md](../AGENTS.md)。目标为 `zufan` 两人共享开发线、`James_Hotten` 另一开发线，`main` 保持稳定；`zjhwork → zufan` 仍待按合并任务单执行，不自动删旧分支。

两人**独立工作区并行开发/验证**，仅团队共享远端 `zufan` 的 Push 在 START → RELEASE → ACK 协议下错峰进行；所有验收绑定实际 SHA，不强推、不让后续代码静默改变已评审 PR。交接主记录位于团队仓库的一个统一位置，Issue/Discussion 或 Markdown 均可，不强制 Issue。

协作、回归与 Fork 按需同步**均不依赖 GitHub Actions**；源仓库现有 workflow 文件保留作参考。Fork `LiZufan001/riscv` 并非实时自动镜像，正常快进同步前必须比较源/目标分支，不覆盖独有提交。

### 历史说明：旧版单任务功能分支流程（不是当前共享线的默认操作）

当前按项目负责人的约定，从数学模型这一步开始，开发内容先提交和推送到 `zjhwork` 分支，暂不合并或推送到 `main`。现有本机仓库使用 `git push team zjhwork`；新克隆仓库使用 `git push origin zjhwork`。其他成员取得本轮内容后，运行 `bash team/scripts/check-vdot-model.sh` 复核。

团队常规协作使用任务分支并通过 Pull Request 合并；当前这一轮以 `zjhwork` 约定为准。需要另开任务分支时，先约定基准分支和合并目标。新成员克隆目录的团队远程是 `origin`；现有本机仿真目录的团队远程是 `team`。

```bash
git switch -c feat/自己的任务名
git add 具体文件
git commit -m "feat: describe the change"
git push -u origin feat/自己的任务名
```

在现有本机仿真目录，将最后一行的 `origin` 换为 `team`。NEMU 源码仍是外部配套仓库；后续修改 NEMU 或香山子模块时，需把其提交推送到团队可访问的对应仓库并更新版本引用。
