# T05/T05-E 实现与合理性初评

本文保存 T05 阶段历史结论；后续已完成 NEMU 候选实现和 standalone 验收，最新状态见 [T08 记录](t08-nemu.md)。下文剩余项为当时的交接记录。

更新日期：2026-10-12（北京时间）。分支：`James_Hotten`。合同：`vdot-s8x8-r32-v0.1`；模型/生成器 `1.0.0`。基准提交 `e27db6158c6a0e583342dbab0ec78bceff138d69`，本轮代码和证据通过本分支提交交付，提交以分支历史为准。

**结论：T05 模型、测试数据及 T05-E harness 已落成，模型/判定器测试、QEMU 自测、未扩展平台失败检出及香山目标编译已有本地证据，可作为 T06/T08 的开发输入。尚无真实 vdot RTL/NEMU 实现，不能将 T05-E 标为完整全核验收通过。** 本文是 Codex 初评，仍需 A/B/C 人工复核，不代替成员签字或 T03 冻结。

## 1. 已执行检查

| 检查 | 实际结果与范围 |
| --- | --- |
| Python 标准库测试 | 13 个测试方法通过；含 65,536 单项乘积、32,768 编码组合、10,000 随机完整结果和编码/异常/日志判定 |
| 数据生成 | 48 定向 + 10,000 随机；实际输入和 128 位期望持久化；重复生成及已入库定向 fixture 比对通过 |
| 裸机烟雾数据 | 80 个合法/算术用例 + 35 异常子例已生成，真实 vdot 部分尚未执行通过 |
| C 判定器 | 18 项检查通过：错误/缺失/重复陷阱、PC/中断位、CSR、目的高位、非目的、内存哨兵、不可达/phase、合法指令错误被拒绝等 |
| QEMU harness 自测 | H00～H04 通过；包含真实 trap/mret、VS Off 恢复访问、vstart7、vill/vl0；退出 0 |
| 两项运行负控 | 错 expected PC 检出 ERR_PC；改错目的第 15 字节期望检出 VECTOR_CHANGED |
| 未扩展完整模式 | 完成 harness 自测后，第一条合法 vdot D00 被 QEMU 以 cause=2 拒绝；程序退出 3，extension_pass=false |
| 香山程序编译 | 固定 nexus-am 的 full ELF/bin 构建通过；未运行香山核心或 NEMU |
| 静态相邻编码 | 717 个命名表项均解析；X07/X08 的 10 个机器字无已检查香山表项冲突，NEMU 32 位主分派未匹配 |

编译器：RISC-V GCC 13.3.0 / binutils 2.42；自测平台：QEMU 8.2.2，virt、单核、RVV 1.0、VLEN=128、ELEN=64。这个环境只用于模型、harness 和编译，不替代团队已锁定的香山/Verilator 仿真环境。

运行产物位于 `team/out/`，其中通过日志、摘要和版本记录的小型归档见 [本次证据](../evidence/t05-t05e-20261012/README.md)。完整随机数据可按 [T05 入口](../tests/README.md) 重生成。源文件摘要与二进制摘要用于识别验证时未提交的代码，不能只拿基准 Git SHA 代表本轮产物。

## 2. 合理性与边界

| 审查点 | 结论与实现处理 |
| --- | --- |
| 独立数学基准 | 采用 Python 整数，不复制硬件加法树或截断；用文档明确数值、struct signed 字节解码及全乘积检查交叉核验 |
| 全宽结果 | 负数只编码低 32 位，高 96 位零；D07 验证 131072，不误用 18 位累加。裸机比较全部 32 个完整向量寄存器 |
| 输入别名 | 按寄存器实际初态生成；相同源编号共用一份值，重叠目的不能另填不一致旧值 |
| CSR 与 VS Off | 先记录现场，后进行观察配置；Off 时不读向量 CSR，恢复后读取标为 phase=2，不补造 raw CSR |
| vstart/vill 构造 | 最后写 vstart；非法 vset 产生的 vill/vl0 按实际联动核对，不宣称隔离了 vill 检查 |
| 精确异常与失败检出 | 单独校验 cause、PC、次数、状态；错误协议走 abort，缺陷不能靠退出零或最后一行 PASS 掩盖；负控实际被检出 |
| 编码拒绝 | 模型的 NotVdot 不等于处理器非法；邻近词保留 custom-0 及 32 位长度，按固定译码源码另核查 |
| 观测扰动 | 关键区无 C 调用，C 禁止向量化；全宽读回的配置改变与被测指令效果分开记录 |
| 环境与构建隔离 | AM 库在固定 Linux 检出编译；应用使用独立对象目录，避免将其目录变量传给递归库构建；不初始化计时中断或进入 S 模式 |
| 覆盖缺口 | UNREACHABLE 不是 PASS，完整模式必须实际执行所有必需 ID；合法对照失败时不继续宣称非法测试有效 |

本次初评未发现需改变候选 ISA 合同的错误。已修正/避免的实现风险包括别名输入不一致、VS Off 观察提前访问 CSR、仅检查低位、同一 AM 对象目录泄漏到递归库构建，以及自测日志被误当扩展通过。日志复核还独立核验 vadd 自测的已知结果和异常目的值与指令前值一致，拒绝仅改写 expected/post 为同一错误值的伪通过记录。

## 3. 源码核查依据

固定 nexus-am `086a238062fdfb3281b745a537b361983d0154b5` 的 riscv64-xs.mk 使用 nemu/boot/start.S 和 noop/trm.c，trm 初始化 UART 后调用 main，未在该默认路径调用 `__am_init_cte64`。本程序保存/恢复原入口并在 M 模式临时安装专用 mtvec，未修改启动库。

阅读入口：[固定架构构建](https://github.com/OpenXiangShan/nexus-am/blob/086a238062fdfb3281b745a537b361983d0154b5/am/arch/riscv64-xs.mk)、[固定 trm](https://github.com/OpenXiangShan/nexus-am/blob/086a238062fdfb3281b745a537b361983d0154b5/am/src/noop/isa/riscv/trm.c)。

相邻编码核查使用当前香山 [DecodeUnit.scala](../../src/main/scala/xiangshan/backend/decode/DecodeUnit.scala) / [VecDecoder.scala](../../src/main/scala/xiangshan/backend/decode/VecDecoder.scala)、固定 rocket-chip `bea0af5d855a871699b907c1988961141bbf28e7` 的 Instructions.scala / CustomInstructions.scala，以及 NEMU `a48a11f208ff81ad765591d83271d1b339fb3861` 的主 decode.c。Rocket 的 CUSTOM0 通配定义存在，但未作为本次实际命名表项接入；不能把依赖中的定义直接当作当前香山译码占用。

该静态脚本的范围为命名 literal BitPat 表项和 NEMU 32 位主分派；不执行 Chisel elaboration、整个扩展配置或真实指令。脚本会拒绝未解析名称，并保存输入源码摘要。后续启用新扩展或修改译码表后，重新检查 X07/X08 的预期非法身份。

## 4. 仍需完成

1. A/B/C 复核模型 API、数据格式、汇编/CSR 观察以及精确异常判定。T03 尚未人工冻结，Q01～Q07 的处理仍按原计划记录。
2. B 实现 T08 的真正 NEMU vdot 及其合法性/副作用；运行相同 workload 的 standalone selftest/full，确认 AM 入口与 CSR 行为在参考平台也成立。
3. A 接入 T06/T07/T10，验证实际 VL 生产者/配置快照、完整写回/v0、晚发现非法的完成和精确提交；本 harness 的串行状态测试不证明这些乱序依赖。
4. C 在 T11/T12 运行真实 DiffTest，复核实际向量/CSR 比较范围、mtval 一致性、故障注入和原有 hello/vadd 回归；保存配套版本及所有必需用例结果。
5. B/C 实现 RVV baseline，补 `measurement.md` 的 scratch、CSR 恢复与计时边界。硬件性能与取消压力覆盖不在本轮自测结果中。
