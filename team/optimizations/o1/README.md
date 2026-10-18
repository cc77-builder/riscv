# O1：受控 vdot→vdot 同拍交接候选

**2026-10-18：三模式真实 FU 验证通过，本轮交付目标为 `cc77-builder/riscv:zjhwork`。** 复用 `zjhwork2@75dce60` 的 O0/O1 成果，修复测试入口及真实编译发现的问题后，实际构建源码固定为 `db0408aa42afc13e3ff93e865f26a2d5bfb02c93`。本页为工程记录；正式 T16 报告继续后置。

[本轮验证证据](evidence/20261018-fu-validation/README.md) 保存首轮 `fu-01` 的编译失败及修复后的 `fu-02` 成功记录。三模式都已执行 Chisel 生成和 Verilator 仿真；生成顶层只实例化真实 VDot FU，尚未实例化真实 ExeUnit。状态为 `fu_validation_pass=true`、`parent_exu_elaborated=false`、`fullcore_difftest=false`、`performance_measured=false`。默认 O1 开关仍为 0。

## 实现与本轮修复

- `VDot.scala`：仅 O1 模式允许旧响应被接收的同拍接受下一条 vdot；边沿前输出旧结果与旧身份，边沿后锁存新乘积与非法标志。vec/v0 写使能独立寄存，避免 DataHoldBypass 将新控制混入旧响应。
- `ExeUnit.scala`：候选 VFEX4 路径记录 activeIsVDot，仅允许 vdot→vdot 同拍交接；完成与接受同时发生时 busy 保留新请求。原分流、输出选择和时钟使能逻辑继续使用，DIV 交接限制等待真实父级联调验证。
- `check-handoff.sh`：先加载 `activate.sh`，再检查 Java 等工具，消除已安装工具被误报缺失的问题。
- 负控：漏检使用独立 `O1_FU_FAULT_ESCAPED` 标记和退出码 3；`check_negative.py` 要求退出码 1、唯一注入标记及对应的唯一失败原因，拒绝漏检、无关失败和重复标记。
- 首轮真实 Scala 编译发现 `ExeUnit.scala` 两个硬件比较右侧使用了 Scala `OHType`（FuType 枚举对象）；均改为 `FuType.vdot.U`。`fu-01` 失败日志原样保留；`fu-02` 在上述固定源码重新运行并通过。

ISA、8 路乘法/归约、NEMU 和原 22＋10000 黄金输入保持原合同。O1 开关只在 elaboration 选择结构；要求 `VDOT_T14_FUSED_INPUT=1`，非法开关值拒绝生成。旧 T12/T13 观察协议尚不支持同拍交接，O1 当前拒绝同时启用这两个旧 trace 开关，正常 DiffTest 功能不因此关闭。

## 实际 FU 结果

| VDOT_T14_FUSED_INPUT | VDOT_O1_HANDOFF | 首次响应延迟 | 无反压最小接受间隔 |
|---|---|---:|---:|
| 0 | 0 | 3 拍 | 4 拍 |
| 1 | 0 | 2 拍 | 3 拍 |
| 1 | 1 | 2 拍 | 2 拍 |

延迟和接受间隔由逐周期握手断言、连续输入及 0/1/2/7 拍反压验证，是独立 FU 指标；尚无新全核加速比或物理时序/PPA 结论。

O1 实际累计接受 **13626**、响应 **13212**、取消 **388**、复位丢弃 **26**，满足事务守恒；同拍交接 **12237** 次，输出反压 **26659** 拍。原 10022 个算术向量均比较完整 128 位结果，此外执行 96 条合法/非法交替、48 个重定向组合、3 个复位时机及 10000 拍随机控制。候选与旧模式的控制矩阵不同：候选用 8 类非法配置代表值，旧模式覆盖 22 个具体非法值，不能将三模式称为完全相同的控制测试。

身份、写使能、高位结果和取消泄漏四项 **C++ 观测值破坏**均被对应断言检出，并通过严格负控校验；这些是检查器检错能力证据，不是生产 RTL 改写注入。O0 **113** 项、O1 **26** 项主机检查也已通过；主机检查不替代硬件验证。

## 复现入口

在完整、已初始化固定依赖的 Linux/WSL 仓库根目录执行，输出目录必须不存在：

```bash
python3 -B -m unittest discover -s team/optimizations/o1 -p 'test_*.py' -v
bash team/optimizations/o1/check-handoff.sh "$PWD/team/out/o1-validation-new"
```

脚本依次运行原基础版、T14 版和 O1 候选，使用独立 RTL/对象目录，保存源码摘要并在结束时复核。成功标记为 `O1_FU_ONLY_PASS` 和 `O1_FU_RUNNER_PASS_PARENT_ELABORATION_AND_FULLCORE_PENDING`。原 FU 测试文件及旧脚本保留。`contract_model.py` 是独立接口约定模型，其中假设的除法 5 拍仅作主机刺激，不表示真实除法器延迟。

下一步是**真实 VFEX4 父级联调，包含 DIV 及 vdot/DIV 切换、busy、ready 反馈和时钟门控**；之后补 O1 观察器、全核功能/异常与 DiffTest、控制压力、同镜像性能 A/B 和独立复现。当前默认模式继续关闭 O1，不把 FU 的 II=2 当成整核优化验收完成。

## 历史：zjhwork2 候选阶段

原基点为 `9e7cce9c9dc090e5280f1a7f8791551612777cc6`，原提交目标为 `cc77-builder/riscv:zjhwork2`。依据是 O0 batch128 日志中的 738 次旧响应当拍 busy 等待、下一拍接受，其中每个正式窗口有 125 次匹配；这些次数不等于可节省的周期数。

原 [候选阶段回执](evidence/20261018-candidate-host/verification.json) 保留当时 17 项主机检查、声明桩语法检查及缺少 Mill 的退出记录；`CONTRACT.md` 保留实施前草案。它们属于历史状态，本轮真实验证以新证据目录为准，不覆盖旧证据或代签人工 ACK。
