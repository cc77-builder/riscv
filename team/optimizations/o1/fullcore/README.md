# O1 观察器适配与全核回归

这是工程复现入口，正式 T16 报告继续后置。真实全核构建已通过，十二项回归进行中；不能据编译、主机检查或生成 RTL 的结构审查宣称全核回归通过。

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

结果以对应运行目录的 result.json 和原始日志为准。当前工作根为 `/home/riscv/riscv-lab/zjhwork2-review-20261018`，本轮不推送 GitHub，不代签团队人工 ACK。
