# 三人团队：项目计划与开发入口

本队以《香山 vdot 赛题：执行计划》和《香山 vdot 赛题：三人分工与 Git 协作》作为项目计划文档，分别安排里程碑、验收标准和三人职责。成员先阅读两份计划，再按认领的任务推进开发。

本目录同时保存本队在 2026-10-09 完成的环境搭建、hello/vadd 源码和阶段一证据，并提供按当前仓库位置运行的脚本。香山硬件基线为 `16ae9ddcda54fc9a2fddffad73174cf793ac7814`。已有 T05 模型/数据、T05-E 异常程序、T08 NEMU 和 T09 RVV baseline 实现及本地验收；vdot RTL 和全核 DiffTest 尚未完成。计划中的后续任务按实际验收结果更新进度。

| 内容 | 入口 |
| --- | --- |
| 项目计划：阶段目标、执行步骤与验收标准 | [香山 vdot 赛题：执行计划](香山vdot赛题_执行计划.md) |
| 项目计划：A/B/C 分工、评审与 Git 协作 | [香山 vdot 赛题：三人分工与 Git 协作](香山vdot赛题_三人分工与Git协作.md) |
| 当前进度与 James_Hotten 分支的 T03 初步评审 | [进度与评审记录](progress.md) |
| vdot 指令语义、候选编码、测试与待确认问题（第一版草案） | [vdot.vv 规格](spec/vdot.md) |
| 配置依赖、完整写回路径与分层控制验收（草案） | [RTL 接入接口](spec/rtl-interface.md) |
| 精确非法异常、陷阱处理与状态观察（基础设施已实现，扩展验收待完成） | [异常测试方案](spec/exception-tests.md) |
| T05 独立数学模型、定向/随机数据与检查入口 | [模型与测试数据](tests/README.md) |
| T05-E 异常程序、运行自测与香山目标构建 | [异常 workload](workloads/vdot-exceptions/README.md) |
| T05/T05-E 实现检查、证据及剩余边界 | [实现与合理性初评](docs/t05-t05e-review.md) |
| T08 NEMU 实现、补丁复现、standalone 验收与参考库 | [NEMU 实现与验收](docs/t08-nemu.md) |
| 固定 NEMU 基线加 vdot 补丁、源码/配置/二进制版本记录 | [NEMU 补丁交付](patches/nemu/README.md) |
| T08 两轴复核、构建来源检查与修复 | [T08 复核](docs/t08-review.md) |
| T09 普通 RVV 序列、模型/CSR/scratch 验收 | [baseline 实现](docs/t09-baseline.md) |
| 已交付任务的实现、覆盖与来源漏洞及完成度评估 | [综合审查](docs/completed-tasks-audit.md) |
| 综合审查问题的源码修复、负控与复审 | [修复与复审](docs/audit-fixes.md) |
| baseline 状态比较、scratch 与 T13 计时事件 | [测量合同](spec/measurement.md) |
| WSL、工具版本、安装方法、配套依赖 | [环境说明](docs/environment.md) |
| 构建和运行命令、启动问题、通过标准 | [阶段一说明](docs/stage1.md) |
| hello/vadd 测试源码 | [workloads/hello-vadd](workloads/hello-vadd/) |
| 路径可配置的执行脚本 | [scripts](scripts/) |
| 昨天的通过日志、配置、反汇编和事件 CSV | [历史证据](evidence/stage1-20261009/) |
| 今天用仓库内脚本重新运行的验证结果 | [脚本验证记录](evidence/script-check-20261010/README.md) |
| 源码锁定版本 | [versions.env](versions.env) |

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

## Git 协作

每个任务从 `main` 建分支并通过 Pull Request 合并。新成员克隆目录的团队远程是 `origin`；现有本机仿真目录的团队远程是 `team`。

```bash
git switch -c feat/自己的任务名
git add 具体文件
git commit -m "feat: describe the change"
git push -u origin feat/自己的任务名
```

在现有本机仿真目录，将最后一行的 `origin` 换为 `team`。NEMU 源码仍是外部配套仓库；后续修改 NEMU 或香山子模块时，需把其提交推送到团队可访问的对应仓库并更新版本引用。
