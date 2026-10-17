# 团队开发入口

**2026-10-17：James_Hotten 已并入 zjhwork / zjhwork2 的 T14、T15、统一测试与 O0 工具。** 当前进度见 [progress.md](progress.md) 和 [同步记录](docs/james-sync-20261017.md)。当前分支原 T12/T13 全核复验见 [报告](docs/james-fullcore-20261016.md)；该证据绑定旧源码 d3706f0b8。默认 VFEX4 基础模式保持 II4，T14 候选仅显式开启；本轮不推送、不改 main。

| 内容 | 入口 |
| --- | --- |
| 项目计划 | [执行计划](香山vdot赛题_执行计划.md)、[分工](香山vdot赛题_三人分工与Git协作.md) |
| 当前合同与架构 | [指令合同](spec/vdot.md)、[RTL接口](spec/rtl-interface.md) |
| 独立模型与输入 | [模型一](models/vdot/README.md)、[模型二与软件测试](tests/README.md) |
| VFEX4 算术/FU | [算术](rtl/vdot/README.md)、[FU](rtl/vdot/FU.md) |
| NEMU 1.1.0 | [固定补丁与配置](patches/nemu/README.md) |
| T10/T11 历史117矩阵 | [报告](docs/t10-t11-acceptance-20261013.md) |
| T12 控制与功能回归 | [报告](docs/t12-regression.md)、[归档复验](evidence/t12-regression-20261014/README.md) |
| T12 软件/RVV 对照 | [zufan 整合](docs/t12-zufan-integration-20261014.md)、[原始归档](evidence/t12-r2-20261014/README.md) |
| T13 校准与性能 | [测量合同](spec/measurement.md)、[来源结果](docs/t13-performance.md)、[工具](workloads/vdot-perf/README.md)、[本轮复核证据](evidence/james-t13-integration-20261016/README.md) |
| James 的旧实现及原证据 | [历史候选](legacy/james-vfex1/README.md)、[原进度](docs/history/progress-before-james-integration-20261015.md) |
| 环境与脚本 | [环境](docs/environment.md)、[脚本](scripts/) |

## 验证入口及适用范围

- 主机：`python3 -B -m unittest discover -s team/tests`；独立数学模型位于 `team/models/vdot/tests`。
- 当前 VFEX4：`check-vdot-datapath.sh`、`check-vdot-fu.sh`、`check-vdot-decode.sh`；构建与日志应使用全新输出目录。
- 当前带观测的全核控制：`t12-regression.sh` / `run-t12-suite.py`，须固定实际 EMU 与参考库来源；已存日志可用 `check-t12-archive.py` 离线复验。
- `t12-tests.py` / `verify_t12_evidence.py` 明确绑定历史 trace-off VFEX4 来源与固定 EMU，保留拒绝不同源码的门禁；需在记录的历史提交另建工作区复现，不能直接将旧二进制用于当前 trace 源树。
- `vdot-core-smoke.sh` 与 James 构建来源门禁仍保留，运行时必须重新构建/绑定当前 VFEX4 和参考配置。旧20项运行是历史，不是新的全核验收。
- `vdot-fu-tests.sh` / `vdot-decode-tests.sh` 是已退休的 VFEX1 入口，明确退出并指向新入口。`team/hardware/vdot` 仅为历史执行器独立实验。

不能把历史归档复算、主机测试或组件仿真当作新的全核运行。不能宣称尚未完成的官方规格冻结、人工签字、虚拟化、STA/PPA或性能成绩。旧入口原文见 [历史快照](docs/history/README-before-james-integration-20261015.md)。

| 新并入内容 | 入口 |
| --- | --- |
| T14 可选输入乘积融合及消融 | [合同](spec/t14-ablation.md)、[来源报告](docs/t14-optimization.md) |
| T15 独立 s16x8/r64 单元 | [合同](spec/t15-parameters.md)、[来源报告](docs/t15-parameter-extension.md) |
| 四项目统一微基准 | [程序](workloads/unified-vdot/README.md)、[来源结果与限制](docs/unified-vdot-comparison-20261017.md) |
| O0 诊断与 O1 未实现草案 | [归档重放](optimizations/o0/ARCHIVE_REPLAY.md)、[O1 合同](optimizations/o1/CONTRACT.md) |
| 后续执行顺序 | [优化方案](香山vdot_后续优化方案_20261017.md)：工程优化、回归、独立复现完成后再集中编写 T16 |
| 来源分支入口历史 | [zjhwork2 原始 README](docs/history/README-zjhwork2-20261017.md) |
