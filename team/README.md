# 团队开发入口

**2026-10-18：James_Hotten 已完成 FTQ/计数窗口观测、当前O1完整矩阵、DiffTest负控及正常恢复。** 13次实际启动满足预期，25计数窗口通过；O1默认关闭，完整软件计划及同源码性能A/B待完成，详见[本轮证据](docs/o1-complete-20261018.md)。zjhwork的[独立三模式FU验证](optimizations/o1/evidence/20261018-fu-validation/README.md)及严格负控已合并推送至James_Hotten；随后观测与回归成果保留本地，下文main同步为历史操作。

**2026-10-17：当前生产路线统一为 VFEX4；旧 VFEX1 实现及专用构建/测试入口已从工作树删除。** 用户授权本轮更新 James_Hotten 并同步 main，交付过程见 [清理与同步记录](docs/vfex4-main-sync-20261017.md)。进度见 [progress.md](progress.md)。T14 候选默认关闭；原全核证据绑定各自执行源码，不将此次清理或历史复算称为新的全核运行。

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
| 历史实现与证据追溯 | [Git 恢复说明](docs/retired-vfex1.md)、[原进度](docs/history/progress-before-james-integration-20261015.md) |
| 环境与脚本 | [环境](docs/environment.md)、[脚本](scripts/) |

## 验证入口及适用范围

- 主机：`python3 -B -m unittest discover -s team/tests`；独立数学模型位于 `team/models/vdot/tests`。
- 当前 VFEX4：`check-vdot-datapath.sh`、`check-vdot-fu.sh`、`check-vdot-decode.sh`；构建与日志应使用全新输出目录。
- 当前带观测的全核控制：`t12-regression.sh` / `run-t12-suite.py`，须固定实际 EMU 与参考库来源；已存日志可用 `check-t12-archive.py` 离线复验。
- `t12-tests.py` / `verify_t12_evidence.py` 明确绑定历史 trace-off VFEX4 来源与固定 EMU，保留拒绝不同源码的门禁；需在记录的历史提交另建工作区复现，不能直接将旧二进制用于当前 trace 源树。
- `vdot-core-smoke.sh` 与 James 构建来源门禁仍保留，运行时必须重新构建/绑定当前 VFEX4 和参考配置。旧20项运行是历史，不是新的全核验收。
- 旧 VFEX1 的 Scala/sbt 工程、测试入口及专用辅助脚本已删除；复验旧结果须使用 [对应历史提交](docs/retired-vfex1.md)，不得将旧实现恢复到当前生产路径。

不能把历史归档复算、主机测试或组件仿真当作新的全核运行。不能宣称尚未完成的官方规格冻结、人工签字、虚拟化、STA/PPA或性能成绩。旧入口原文见 [历史快照](docs/history/README-before-james-integration-20261015.md)。

| 新并入内容 | 入口 |
| --- | --- |
| T14 可选输入乘积融合及消融 | [合同](spec/t14-ablation.md)、[来源报告](docs/t14-optimization.md) |
| T15 独立 s16x8/r64 单元 | [合同](spec/t15-parameters.md)、[来源报告](docs/t15-parameter-extension.md) |
| 四项目统一微基准 | [程序](workloads/unified-vdot/README.md)、[来源结果与限制](docs/unified-vdot-comparison-20261017.md) |
| O0 诊断与 O1 未实现草案 | [当前进度](docs/o0-progress-20261018.md)、[运行入口](optimizations/o0/README.md)、[旧pilot重放](optimizations/o0/ARCHIVE_REPLAY.md)、[O1 合同](optimizations/o1/CONTRACT.md) |
| 后续执行顺序 | [优化方案](香山vdot_后续优化方案_20261017.md)：工程优化、回归、独立复现完成后再集中编写 T16 |
| 来源分支入口历史 | [zjhwork2 原始 README](docs/history/README-zjhwork2-20261017.md) |
