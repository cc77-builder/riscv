# O1：受控 vdot→vdot 同拍交接候选

基点 `9e7cce9c9dc090e5280f1a7f8791551612777cc6`，目标 `cc77-builder/riscv:zjhwork2`。依据是 O0 batch128 的真实日志：738 次旧响应当拍父级 busy 阻塞，同一请求在下一拍接受。该数字不等于候选可以节省的周期数。本页是开发记录，不是 T16 最终报告。

**当前状态（James_Hotten，2026-10-18）：候选已并入并修复父级 FuType 比较的 Scala 类型错误；baseline/T14/O1 三模式真实 FU 仿真通过，O1 在该单元测试中达到响应2拍、接受间隔2拍。默认关闭，真实父级与全核尚未验收。** 当前证据与限制见[整合审查](../../docs/james-o1-integration-20261018.md)。此前 CONTRACT.md 和下文原分支记录保留，不覆盖旧证据或代签人工 ACK。

## 改动

- `VDot.scala`：仅 O1 模式允许 RESP/out.ready 且无 reset/redirect/kill 时接收下一请求；该边沿锁存新乘积与非法标志，下一状态为 REDUCE，旧结果在边沿前继续有效。
- 该模式用独立 `RegEnable` 保存 vec/v0 写使能，与基类已寄存的 ROB、pdest、vpu、perf 字段保持同一事务；不让 DataHoldBypass 的新输入覆盖旧响应控制。不修改通用 FuncUnit 或 utility。
- `ExeUnit.scala`：仅含 VDot 的 VFEX4 候选路径增加 activeIsVDot；只允许 vdot→vdot 交接，不放行 div→vdot、vdot→div 或 div→div 的同拍重叠。redirect/reset 时不接收新请求。完成+接受同拍时 busy 保留新请求。
- 原 Dispatcher、输出 one-hot 选择、端口、仲裁优先级和时钟使能更新逻辑不变；增加父级/VDot 的 in.fire 一致性断言。尤其仍保留 Dispatcher 的所有 ready 相与，不能假定其他 FU 的 ready 行为已验证。
- ISA、8 路乘法与归约、NEMU、原 22+10000 黄金输入不变。没有吞吐、延迟、Fmax、面积或功耗的新实测结论。

## 开关与测试入口

| VDOT_T14_FUSED_INPUT | VDOT_O1_HANDOFF | 所选结构（已在FU顶层实测，非全核） |
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

输出目录必须不存在。脚本依次运行原基础版和 T14 的未修改 FU 回归，再用真实 VDotFuTestTop 生成候选，并运行 `handoff_test.cpp`。只修改环境变量不保证旧产物重编，必须按脚本使用新的 RTL/对象输出目录。

新 C++ 检查器逐边沿先比较旧输出，再结算旧响应/取消/复位，最后登记新接受；drain 时明确 valid=0，避免噪声被当作新事务。测试包含原 10022 数值向量连续交接、0/1/2/7 拍反压、96 条合法/非法交替、vec/v0 和身份变化、48 个年龄/环绕/时点/ready 重定向组合、3 个复位时点、10000 拍随机控制，以及身份/写使能/高位/取消读回破坏检出。原分支仅做主机检查；James_Hotten已运行真实FU，实际计数见当前整合审查及新证据，不改写原分支的verification.json。

成功标记限定为 `O1_FU_ONLY_PASS` 和 `O1_FU_RUNNER_PASS_PARENT_ELABORATION_AND_FULLCORE_PENDING`；它们也不代表完整父级/CPU 验证。脚本使用现有 vdotFu 构建目标，会编译 XiangShan Scala，但生成顶层只实例化 FU，未实例化真实 ExeUnit。原 FU 测试文件和旧脚本未修改。

主机检查：

```bash
python3 -B -m unittest discover -s team/optimizations/o1 -p 'test_contract.py' -v
```

contract_model.py 是独立接口约定模型，不解释或执行 Chisel。其假设的除法 5 拍仅作切换刺激，不表示真实除法器延迟。源码字符串检查只防意外漂移，不是形式等价或硬件测试。

## 来源分支的原始验证与限制（并入前）

verification.json 记录 17 项主机检查、shell 语法、C++ 在仅端口声明桩下的 -fsyntax-only 及真实 RTL 入口缺 Mill 时的 exit=2。C++ 声明桩没有 DUT 行为，没有链接或执行仿真。已有 O0 性能数据只作为决策依据，不当成新核结果。

提交前已核对两个生产文件的原始 Git blob；增量之外的源码未变，候选关闭时保留原 Scala 分支。**尚未生成旧模式与候选 RTL，因此没有生成物等价、Chisel 类型正确性或组合环排除证据。** 原冻结源码、基类、时钟门控和其他 FU 的完整联调仍须实测。

下一步门禁：三模式 FU 真实构建/运行 → 真实 VFEX4（含两种除法）父级联调与时钟/ready 反馈检查 → O1 观察器及双事务同拍配对 → 新 EMU hello/vadd、原功能/异常矩阵和 DiffTest 负控 → T12 控制压力 → 相同镜像性能 A/B → 独立复现。未通过这些门禁，不切换默认模式、不合入 main，不把“候选已提交”写成“II=2 优化完成”。
