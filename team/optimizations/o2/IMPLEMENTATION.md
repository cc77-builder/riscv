# O2 两槽弹性 FU 与真实父级联调

日期：2026-10-19。**G1、G2 自动验证完成，本地保存；下一步为 G3 观察器适配及全核回归。** 本记录是开发交接材料，正式 T16 报告仍后置。

## 改动与边界

新增 VDotElastic：P 槽保存 8 个乘积、完整控制和 perf 身份，R 槽保存完整输出包；旧 R 返回、旧 P 向 R 转移、新请求进入 P 可以同拍发生。每个槽分别按自身 ROB 判断取消，反压时保持整包响应。算术复用原 VDotProducts/VDotReduce，合法结果仍为低 32 位有符号点积、高 96 位清零。

父级仅在启用 O2 的 VFEX4 路径改变：用被选 FU 的 ready 原子派发；vdot 的两槽真实占用和 DIV 的独立忙态分别管理；DIV 与 vdot 互斥，并等待 DIV 旧输出撤销、ready 恢复。vdot 时钟由真实占用、输入握手和 reset 维持，取消当天也保留清除边沿。FuConfig 继续使用 piped=false、UncertainLatency，不改通用 Dispatcher。

VDOT_O2_ELASTIC 默认关闭。启用要求 VDOT_T14_FUSED_INPUT=1、VDOT_O1_HANDOFF=0；当前 G1/G2 模式拒绝旧 T12/O1/T13 观察协议。ISA、NEMU、数学模型、黄金数据、旧算术和原封存证据保持不变。

## 实测结果

| 检查 | 结果 |
| --- | --- |
| G1 隔离真实 FU | 22 定向＋10,000 随机向量的完整 128 位结果通过；另有非法、反压、取消、reset、20,000 拍随机控制 |
| 连续流接收能力 | FU 与真实父级均为 II=1；10,022 条连续请求、10,021 个相邻间隔均为 1 拍 |
| 无阻塞首次响应 | 两个环境均为接受后第 2 拍；不把等待反压的响应延迟也写成恒定 2 拍 |
| G1 事务守恒 | 23,311 接受 = 22,460 响应 + 739 取消 + 112 reset 清除，最终在途 0 |
| G2 真实父级 | 实例化真实 ExeUnit、VDotElastic、VIDiv、VFDivSqrt 与 ClockGate，共 34,356 拍通过 |
| G2 事务守恒 | 13,515 接受 = 13,037 响应 + 418 取消 + 60 reset 清除，最终在途 0 |
| G2 身份与结果 | 完整 128 位结果及三个写回数据副本、ROB/pdest、异常/写使能、完整 VPU/perf 绑定通过 |
| G2 关键控制覆盖 | 全部 9 种 FU 切换 × 3 种停顿；128 组 redirect、14 组 reset 场景及 20,000 拍随机控制 |
| 部分取消 | 仅 P 取消 39 次、仅 R 取消 49 次、两槽取消 39 次；覆盖接受顺序与 ROB 年龄反向、flag 环绕 |
| 真实门控 | R 返回而 P 幸存且无新接受 337 次；TE=0 reset 33 拍，其中空闲 22 拍；最终空闲门控通过 |
| 检查器负控 | FU 4 项，父级 16 项均按预期退出码及错误类别拒绝 |
| 兼容性回归 | 默认/T14/O1 三模式 FU，以及 T14/O1 两模式真实父级均通过 |
| 独立离线重算 | 逐拍身份、槽迁移、ROB 取消、DIV 排空、门控、前缀守恒、摘要与连续 II 复算通过；41 项主机测试通过 |

父级接受量分解：vdot 11,825、VIDiv 859、VFDiv 831。所有实际结果、命令与 SHA 见 [证据入口](evidence/20261019-elastic-parent/README.md) 和 [机器结果](evidence/20261019-elastic-parent/verification.json)。

这些是 FU/父级接口指标。**II 从 O1 的 2 降到 O2 的 1，不代表整核程序快两倍，也不是已测得新的 RVV 加速比。** 上游供数、调度、写回和程序依赖仍须全核测量。O1 已有 batch128 的 362.50 拍、1.870× 结果仍是上一轮全核数据。

## 源码与运行身份

工作分支：local/o2-elastic-parent-20261019；起点 7643b8d。生产 RTL 在 a7d32f1 固定后未再修改。

| 证据 | 构建/检查源码 | 正式外部目录 |
| --- | --- | --- |
| G1 | a7d32f1d03eef251ce7845bb89a8b42cebe096ad | g1-attempt-01 |
| G2 | 3e4280dbd6c781dc261d4729be58ca9167708269 | g2-attempt-02 |
| 最终离线检查 | 781043ad92b623aa8f49b21560edec914199f9af | postcheck-02 |

所有目录位于 /home/riscv/riscv-lab/o2-elastic-parent-20261019。源码清单、构建前后一致性、依赖 pin/清洁状态、工具版本、生成 RTL 和二进制 SHA 均已保存；实际 C++ 编译器为日志记录的 clang++。工具包括 Java 21、Mill 0.12.3、firtool 1.62.1、Verilator 5.052、clang 19.1.7；完整版本以归档原输出为准。

探索性 g2-attempt-01 运行通过，但其构建期两处观察负控代码曾短暂修改并恢复，所以正式验收采用新冻结源码重新构建的 g2-attempt-02。两轮正例轨迹相同，不把它们当新增独立随机样本。

离线工具首版在独立审查中发现两个缺口：DIV 反压后撤销 valid、伪造切换场景名仍可能通过。修复后增加对应反例，在 postcheck-02 重新读取同一未修改原始日志通过；没有重跑 RTL 来替代检查器修复。探索与旧检查材料仍完整保留。

## 复现命令

在上述完整香山 Git 检出目录下执行；每次输出目录必须是新的绝对路径。runner 自动激活配套环境并设定 O2 开关、2 个编译线程和 JVM 内存。

```bash
python3 -B team/optimizations/o2/run_rtl.py fu /home/riscv/riscv-lab/o2-reproduce-g1
python3 -B team/optimizations/o2/run_rtl.py parent /home/riscv/riscv-lab/o2-reproduce-g2

python3 -B -m unittest discover -s team/optimizations/o2/parent -p 'test_*.py' -v
python3 -B -m unittest discover -s team/optimizations/o2 -p test_negative_fu.py -v
python3 -B team/optimizations/o2/parent/check_trace.py --log /home/riscv/riscv-lab/o2-reproduce-g2/result.log --output /home/riscv/riscv-lab/o2-reproduce-g2/independent-replay.json
```

旧模式检查需显式关闭 O2：

```bash
VDOT_O2_ELASTIC=0 VDOT_O1_TRACE=0 bash team/optimizations/o1/check-handoff.sh /home/riscv/riscv-lab/o2-reproduce-old-fu
VDOT_O2_ELASTIC=0 VDOT_O1_TRACE=0 bash team/optimizations/o1/parent/check-parent.sh /home/riscv/riscv-lab/o2-reproduce-old-parent
```

旧模式测试的场景安排与 O2 不同，不能用测试总周期数相除宣称加速。独立离线检查不重新执行硬件，也不重新计算完整 payload；数据正确性由 live C++ scoreboard 验收。

## 已知边界与下一步

- 负控在 C++ 观察值上注入错绑、漏取消、误杀、重复/丢失响应、反压变包、路由/时钟错误，验证检查器是否拒错；没有把生产 RTL 改坏再运行。
- 初始 bootstrap 和旧 DIV reset 使用 TE=1。O2 vdot 的空/P/R/满槽及 reset+flush 定向使用 TE=0；没有声称整个 DIV 复位体系已改为 TE=0。
- 旧 DIV 取消当拍仍可能有 raw output：VIDiv 11 次、VFDiv 16 次，按 KILL 记账且下一拍无幽灵宽限；其旧门控策略未修改。两项辅助计数 idle_clock_samples、cancel_idle_clock_on 未由离线工具再次重算。
- 这里只验收 G1/G2；全核、DiffTest、真实应用性能、时序/面积、T17 独立干净检出和两位成员人工 ACK 仍待完成。源码自动审查记录见 [实现审查](IMPLEMENTATION_REVIEW.md)。
- 下一步 G3：适配两槽全核观察协议，明确每笔接受、P→R、响应、逐槽取消及 reset 丢弃身份；再构建固定版本 EMU，跑原功能/异常/控制矩阵，补两条在途与 DIV 切换压力。
- G3 通过后进入 G4：保持冻结镜像/参考库/配置的 O1/O2 公平比较；batch 相对 O1 降低至少 10% 是内部投入参考，其他场景退化超过 2% 需调查，不是官方评分标准。

成果只在本地提交，尚未推送 GitHub，也没有合并 main 或将 O2 设为默认模式。
