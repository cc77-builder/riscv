# O1：受控 vdot→vdot 同拍交接候选

最新续做：已补齐 [FTQ/CSR窗口扩展](TRACE-EXTENDED.md)，新的O1 EMU完成117唯一矩阵/124执行、真实DiffTest负控及正常恢复、8项控制覆盖和25计数窗口；见[完整记录](../../docs/o1-complete-20261018.md)。72项主机检查与15类真实日志破坏检查通过。O1默认关闭，完整软件计划与同源码性能A/B仍待完成；以下保留各来源阶段的独立证据。

基点 `9e7cce9c9dc090e5280f1a7f8791551612777cc6`，目标 `cc77-builder/riscv:zjhwork2`。依据是 O0 batch128 的真实日志：738 次旧响应当拍父级 busy 阻塞，同一请求在下一拍接受。该数字不等于候选可以节省的周期数。本页是开发记录，不是 T16 最终报告。

**当前状态（James_Hotten，2026-10-18）：baseline/T14/O1 三模式真实 FU 及 VFEX4 父级仿真通过。父级包含生产整数/浮点除法器与真实时钟门控；O1响应2拍、接受间隔2拍，10311次同拍交接通过。修复三模式取消后的时钟保持位未清除。O1默认关闭，全核尚未验收。** 新证据与限制见[父级优化](../../docs/o1-parent-20261018.md)，前轮见[整合审查](../../docs/james-o1-integration-20261018.md)。此前 CONTRACT.md 和下文原分支记录保留，不覆盖旧证据或代签人工 ACK。

## 改动

2026-10-18 补充并入 zjhwork@c3c417a26：FU 负控要求准确的注入类型、失败原因、行序和真实 exit=1；漏检单独返回 exit=3，不能当作预期检出。构建入口保留 James 的 HEAD 补丁与未跟踪输入保护，并纳入负控检查器来源。该分支的[三模式 FU 证据](evidence/20261018-fu-validation/README.md)绑定 db0408aa4，独立于 James 的父级/全核运行，不将两批计数混合。其两处 FuType.vdot.U 修复已在 James 存在，合并未改生产 RTL。

- `VDot.scala`：仅 O1 模式允许 RESP/out.ready 且无 reset/redirect/kill 时接收下一请求；该边沿锁存新乘积与非法标志，下一状态为 REDUCE，旧结果在边沿前继续有效。
- 该模式用独立 `RegEnable` 保存 vec/v0 写使能，与基类已寄存的 ROB、pdest、vpu、perf 字段保持同一事务；不让 DataHoldBypass 的新输入覆盖旧响应控制。不修改通用 FuncUnit 或 utility。
- `ExeUnit.scala`：仅含 VDot 的 VFEX4 候选路径增加 activeIsVDot；只允许 vdot→vdot 交接，不放行 div→vdot、vdot→div 或 div→div 的同拍重叠。redirect/reset 时不接收新请求。完成+接受同拍时 busy 保留新请求。
- 保留原 Dispatcher 的所有 ready 相与、输出 one-hot 选择、端口及仲裁优先级，增加父级/VDot 的 in.fire 一致性断言。本轮已通过真实除法器检查 ready 交互，并复用父级 busy/ROB 取消判断清除 VFEX4 的时钟保持位。
- ISA、8 路乘法与归约、NEMU、原22+10000黄金输入不变。FU与父级延迟/接受间隔已实测；没有CPU整体收益、Fmax、面积或功耗的新实测结论。

## 开关与测试入口

新增独立 `VDOT_O1_TRACE=1` 同拍观察器，默认关闭，可覆盖下表三模式；它不自动启用O1，也不兼容旧T12/T13观察器。协议、字段、复现与验收边界见 [TRACE.md](TRACE.md)，本轮证据见[观察器验证](../../docs/o1-trace-20261018.md)。真实父级三模式观察日志与独立C++账本一致，关闭观察器的RTL与上一轮逐字节相同；全核状态以该记录为准。

| VDOT_T14_FUSED_INPUT | VDOT_O1_HANDOFF | 所选结构（FU及真实VFEX4父级实测，非全核） |
|---|---|---|
| 0 或未设 | 0 或未设 | 原基础模式，响应 3 拍/接受间隔 4 拍 |
| 1 | 0 或未设 | 原 T14 模式，响应 2 拍/接受间隔 3 拍 |
| 1 | 1 | 新候选：FU响应 2 拍/接受间隔 2 拍 |
| 非 1 | 1 | 拒绝生成 |

O1 开关只在 elaboration 选择结构，不生成运行时切换器。`VDOT_O1_HANDOFF` 非 0/1 字符串拒绝。候选同时要求旧 `VDOT_T12_TRACE`、`VDOT_T13_TRACE` 不为 1：旧解析器按不重叠协议配对门控时钟，当前不得通过放宽它来声称新 T12 已通过。正常 DiffTest 功能不因此关闭；控制观测要另行补 O1 协议后验收。

在完整、已初始化固定依赖的 Linux/WSL 仓库根目录执行：

```bash
bash team/optimizations/o1/check-handoff.sh "$PWD/team/out/o1-validation-new"
```

真实父级另有入口：`bash team/optimizations/o1/check-parent.sh /absolute/new/output`。它执行三模式 lint、实际时钟门控下的事务/混合除法回归、取消后空闲时钟检查及四类负控，成功标记为 `VFEX4_PARENT_RUNNER_PASS_FULLCORE_PENDING`。依赖子模块必须处于已初始化的固定干净版本。`parent.vlt`只豁免已审阅且由表达式守卫约束的一行除法器位宽告警；其余警告仍阻止通过。

输出目录必须不存在。脚本依次运行原基础版和 T14 的未修改 FU 回归，再用真实 VDotFuTestTop 生成候选，并运行 `handoff_test.cpp`。只修改环境变量不保证旧产物重编，必须按脚本使用新的 RTL/对象输出目录。

新 C++ 检查器逐边沿先比较旧输出，再结算旧响应/取消/复位，最后登记新接受；drain 时明确 valid=0，避免噪声被当作新事务。测试包含原 10022 数值向量连续交接、0/1/2/7 拍反压、96 条合法/非法交替、vec/v0 和身份变化、48 个年龄/环绕/时点/ready 重定向组合、3 个复位时点、10000 拍随机控制，以及身份/写使能/高位/取消读回破坏检出。原分支仅做主机检查；James_Hotten已运行真实FU，实际计数见当前整合审查及新证据，不改写原分支的verification.json。

成功标记限定为 `O1_FU_ONLY_PASS` 和 `O1_FU_RUNNER_PASS_PARENT_ELABORATION_AND_FULLCORE_PENDING`；它们也不代表完整父级/CPU 验证。脚本使用现有 vdotFu 构建目标，会编译 XiangShan Scala，但生成顶层只实例化 FU，未实例化真实 ExeUnit。原 FU 测试文件和旧脚本未修改。

主机检查：

```bash
python3 -B -m unittest discover -s team/optimizations/o1 -p 'test_contract.py' -v
```

contract_model.py 是独立接口约定模型，不解释或执行 Chisel。其假设的除法 5 拍仅作切换刺激，不表示真实除法器延迟。源码字符串检查只防意外漂移，不是形式等价或硬件测试。

## 来源分支的原始验证与限制（并入前）

原 [候选阶段回执](evidence/20261018-candidate-host/verification.json)记录 17 项主机检查、shell 语法、C++ 在仅端口声明桩下的 -fsyntax-only 及真实 RTL 入口缺 Mill 时的 exit=2。C++ 声明桩没有 DUT 行为，没有链接或执行仿真。目录 verification.json 现指向 zjhwork 后续 FU 实测；已有 O0 性能数据只作为决策依据，不当成新核结果。

提交前已核对两个生产文件的原始 Git blob；增量之外的源码未变，候选关闭时保留原 Scala 分支。**尚未生成旧模式与候选 RTL，因此没有生成物等价、Chisel 类型正确性或组合环排除证据。** 原冻结源码、基类、时钟门控和其他 FU 的完整联调仍须实测。

下一步门禁：当前O1 original/lean完整软件计划 → 同源码、相同镜像baseline/T14/O1性能A/B → 独立复现。FTQ与计数窗口、当前O1完整功能/异常矩阵及DiffTest负控和正常恢复已通过，详见[本轮验证](../../docs/o1-complete-20261018.md)。后续未通过前不切换默认模式、不合入main，不把父级II2或观察协议通过等同于CPU优化验收完成。
