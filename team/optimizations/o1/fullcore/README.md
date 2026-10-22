# O1 观察器适配与全核回归

这是工程复现入口，正式 T16 报告继续后置。2026-10-18 完成全新 EMU 构建、12 项实际全核运行及严格离线复核，分别取得 `O1_FULLCORE_SUITE_PASS` 与 `O1_OFFLINE_FULL_SUITE_RECHECK_PASS`。成果仅在本地分支 `local/o1-fullcore-20261018` 保存。


## 本轮实际结果

| 检查 | 实际结果 |
| --- | --- |
| hello/vadd | 正常 DiffTest、GOOD TRAP、HELLO_VADD_PASS，未出现 vdot 事务 |
| 完整功能矩阵 | 8 片全部通过；117 个唯一用例（80 合法、37 精确异常），124 次执行 |
| bit100 差分负控 | 预期 exit 1，唯一注入与唯一向量高位差分对应；同一镜像随后用正常参考库完整通过 |
| F2v 控制压力 | 2157 次 vdot 提交；941 次 VIDiv 请求；62 拍 vdot 写回反压；3 次 FU 在途取消；303 次同拍交接 |
| batch128 密集点积 | 12 个窗口通过；768 次提交；725 次同拍交接；2 次 FU 在途取消 |
| 统一门禁与离线复核 | 66 项主机测试（41＋25）通过，12 项原始日志重审通过，证据前后摘要不变 |

11 个正常作业合计 3012 次 vdot 提交、1028 次同拍交接、5 次 FU 在途取消；负控单独记录，不能将其预期失败称为正常 DiffTest 通过。完整观察结束时无未完成事务和 ROB 生命周期；负控只作显式 partial 轨迹审计。

F2v 的七项原控制覆盖和同拍交接共八项均由该程序自身触发，不需要跨程序补齐覆盖。62 拍写回反压来自 20 个事务，最长 6 拍；3 次取消均发生在接受后第 1 拍、reduce 状态。941 次共享请求是 **VIDiv**，本次全核控制程序没有 VFDiv 请求；响应/反压阶段取消和 VFDiv 的覆盖见上一轮真实父级联调，不能写成这次全核已覆盖。

密集程序全部 768 次响应均为 2 个全局周期，结束时 pending=0、unfinished ROB=0。它验证交接、结果和计数窗口；这次没有执行 T14/O1 配对性能实验，不发布新的加速比，也不将局部 II=2 视作全核每两拍完成一条指令。

## 证据与版本

完整工程证据见 [密封归档](../evidence/20261018-fullcore-validation/README.md)；[文件映射](../evidence/20261018-fullcore-validation/file-map.json) 绑定原路径、原始字节摘要及压缩后摘要，[归档清单](../evidence/20261018-fullcore-validation/archive-manifest.json) 固定全部载荷。原始 stdout/stderr、检查器快照、运行回执及失败尝试均在其中；不包含 EMU、编译对象或波形。

| 层次 | 固定身份 |
| --- | --- |
| 实际受测硬件源码 | `18c0ce08a40e889654bfe76d5435f272854ad7d0` |
| 原 12 项运行的六文件检查器 | `518c05674d5ecfed04a944cf01c99cea488b6c8a` |
| 运行结束后集成严格日志门禁 | `d110002006001d45a39dbc00591a299672940818` |
| 实际 EMU SHA256 | `b13b05a3b03d2dd178d5e07b55bda1e8d99d7a094d44cf30405241f9793170cb` |

构建和复核固定 427 个硬件源码文件、21236 个依赖文件、118 个工作负载/参考库输入。原仿真结束后才改日志门禁；新门禁集成与最终文档提交没有重新构建硬件，也没有改变原始运行结果。

当前 `fullcore_validation_pass=true`、`offline_full_suite_recheck_pass=true`、`performance_measured=false`。下一项为 T14/O1 同镜像、同参考库、同窗口的性能 A/B；PPA、虚拟化、新机器完整构建复现及团队人工 ACK 尚未由本轮完成。O1 默认仍关闭，未推送 GitHub。

## 固定条件

- 硬件：MinimalConfig、单核、EMU_THREADS=1、VLEN=128；ISA、正常 NEMU 和黄金输入沿用已验收版本。
- 开关：VDOT_T14_FUSED_INPUT=1、VDOT_O1_HANDOFF=1、VDOT_O1_TRACE=1、VDOT_T12_TRACE=0、VDOT_T13_TRACE=1。O1 默认仍关闭。
- 观察协议见 [SCHEMA.md](SCHEMA.md)：使用未门控全局周期，绑定旧响应与新接受身份；ROB 与 VFEX4 的真实重定向边界分别记录。
- 构建源码固定为 `18c0ce08a40e889654bfe76d5435f272854ad7d0`。后续 `518c05674d5ecfed04a944cf01c99cea488b6c8a` 仅修正 Python 检查器的环绕指针边界，生产硬件输入未变化。
- 本轮只验证全核功能与观察协议，密集程序同时校验计数窗口；尚未进行 T14/O1 同镜像性能 A/B，不从本轮结果推导新的加速比或 PPA。

## 运行方法

从完整且依赖已初始化的仓库根目录执行；输出目录必须不存在，构建前应保留原 build 目录，脚本不会删除它。当前冻结输入来自本机的 T12/T13/T14 归档，换机时应先恢复这些归档与匹配的参考库路径。

```bash
python3 -B -m unittest discover -s team/optimizations/o1/fullcore -p 'test_*.py' -v
python3 -B -m unittest discover -s team/optimizations/o1/audit -p 'test_*.py' -v
python3 -B team/optimizations/o1/fullcore/run_suite.py --preflight-only --output /absolute/new/preflight
python3 -B team/optimizations/o1/fullcore/build_fullcore.py --output /absolute/new/build-evidence
python3 -B team/optimizations/o1/fullcore/run_suite.py   --hardware-pins /absolute/new/build-evidence/hardware-inputs.json   --emu "$PWD/build/emu" --output /absolute/new/regression --jobs 2
```

构建脚本保存命令、开关、工具版本、硬件输入、126 个递归依赖的固定版本和二进制摘要；成功标记为 `O1_FULLCORE_BUILD_PASS`。回归逐项保存真实退出码、分开的 stdout/stderr 和派生 run.log，运行前后核对源码、检查器、输入与二进制摘要。

## 十二项实际仿真

| 顺序 | 项目 | 验收要求 |
| --- | --- | --- |
| 1 | hello/vadd | 正常参考库、HELLO_VADD_PASS、GOOD TRAP、无 vdot 事务 |
| 2 | vdot bit100 负控 | 精确注入标记、PC/目的寄存器/位差对应、真实差分退出 1；仅允许显式 partial 轨迹审计 |
| 3 | 同镜像正常恢复，矩阵第 0 片 | 在负控结束后换回正常参考库，完整功能与轨迹通过 |
| 4–10 | 矩阵第 1–7 片 | 与第 0 片合计 117 个唯一用例、124 次执行，覆盖合法结果与精确异常 |
| 11 | F2v 控制流压力 | 年轻请求取消、FU 在途取消、共享 VFEX4、父级等待、写回反压、ROB 与 FTQ 多次绕回 |
| 12 | batch128 密集点积 | 原程序/窗口检查器通过、精确 768 条 vdot 提交、真实同拍 HANDOFF>0 |

前三项顺序运行，剩余项目最多两项并行。每个正常作业须独立通过 DiffTest、原程序检查和 O1 完整轨迹；任一失败阻止总验收。

F2v 的七项原控制覆盖必须全部满足。如果该程序没有触发同拍交接，保留其局部 `O1_COVERAGE_INCOMPLETE`，只有独立密集程序的窗口与真实交接证据通过，才允许总覆盖成立，并明确记录覆盖分布在两个程序。不能把缺失其他控制覆盖也解释为通过。

## 保留的尝试与检查范围

首次构建 build-01 因新 ENQUEUE 标签未排除 ROB 重定向当拍而主动停止，日志及生成中间文件原样保留。build-02 修正该观察条件后从新 build 目录开始，不复用第一次的 RTL 产物。旧 T12/T13 观察器和历史证据保持原字节。

主机检查包含事件结构、printf 顺序、身份绑定、精确延迟与连续反压、取消与 ROB 生命周期、负控、运行门禁及 18,432 种环绕指针组合。它们检查验证工具，不替代真实全核运行。生成 RTL 的只读结构审计同样单独保存，不充当动态验证。

原驱动的 ANSI 颜色边界问题、严格门禁修复及两个 PC 字段的区别见 [日志复核说明](../audit/README.md)。66 项主机测试是最终集成检查；另外保留 30/30 真实 Scala 开关探针及 18,432 个指针组合检查，均不代替全核 DiffTest。

结果以对应运行目录的 result.json 和原始日志为准。当前工作根为 `/home/riscv/riscv-lab/zjhwork2-review-20261018`，本轮不推送 GitHub，不代签团队人工 ACK。

密封证据在 Git 中使用专属 `-text -whitespace` 规则，保留 gzip 及原始快照字节；[Git 存储检查](../evidence/20261018-fullcore-storage-check/README.md) 记录提交前发现的换行转换问题和修复后逐文件核对，原密封归档未改。
