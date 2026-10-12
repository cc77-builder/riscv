# RVV baseline 与后续性能测量合同

版本 `0.1.0-draft`，2026-10-12。适用候选合同 `vdot-s8x8-r32-v0.1`；baseline 标识 `rvv-vdot-s8x8-r32-v1`。本轮落实 T09 的软件序列与状态比较；T13 的硬件计时尚未运行，须在 T09/T12 均通过后验收。

## 1. 入口与出口

入口固定 VLEN=128、e8/m1、**实际 vl=8**、vstart=0、vill=0、VS 非 Off。四种 vta/vma 均支持，vxrm/vxsat 可取全部合法值。非法配置不在 baseline 合同内，不能用本序列替代单条 vdot 的精确异常验证。

序列只使用源低八字节，解释为 signed int8；从零求和。出口目的低 32 位为补码，高 96 位全零；vl/vtype 恢复实际入口值，vstart=0，vxrm/vxsat/vcsr 保持。成功后 VS Dirty。目的与源别名时，源中属于目的的寄存器按目的结果更新；其他源完整保持。

每个寄存器组合在生成时选定四个向量 scratch：偶数起始的两个 product 寄存器，以及独立 seed、reduction 寄存器。四个 scratch 不与 vd/vs1/vs2 或 v0 重叠；精确编号及掩码写入 baseline-manifest 和逐用例日志。例如 vd10/vs1=8/vs2=9 使用 v2/v3、v1、v4，允许破坏掩码 `0x1e`。不是默认排除所有临时寄存器。

比较全部 32 个向量寄存器中的非 scratch 寄存器，包含目的完整 16 字节、非目的源和所有其余哨兵。baseline 的四个 scratch 排除于两种序列的共同出口比较集合；单条 vdot 自身仍须按 ISA 严格保持除目的外的全部向量寄存器。

序列使用 t2 搬运结果、t3 保存实际 vl、t4 保存实际 vtype；这些 GPR 允许破坏。测试 stub 还用 t0 记录 mstatus，harness 使用普通 ABI 的 caller-saved GPR。不能声称两种完整软件调用除目的外所有架构状态相同；ABI、返回地址和观察操作应分别记录。

## 2. 普通 RVV 实现

在实际 vl/vtype 快照后：

1. e32/m1、vl4、tu/mu 下把 seed 整寄存器清零。
2. e8/m1、vl8、tu/mu 下 `vwmul.vv`，signed int8 乘积精确扩宽到 int16，product 的 EMUL=2，偶数对齐。
3. e16/m2、vl8、tu/mu 下 `vwredsum.vs`，八个 int16 乘积符号扩展后归约到 32 位，并加零 seed。只使用八项，排除其余 product 尾部。
4. e32/m1、vl4、tu/mu 下取出 reduction 的低 32 位到 t2，显式清零目的四个 32 位元素，再 `vmv.s.x` 写 element0。负结果只写低 32 位，tu 保持已清零的高 96 位。
5. 用 `vsetvl zero,t3,t4` 恢复真实入口 vl/vtype。

归约的 scalar seed/result 各占单个向量寄存器，不因 m2 要求其编号偶数；其余目的元素遵守尾部策略。上述清零和 tu 保证目的全宽确定。依据为 [RISC-V V 1.0 规范](https://docs.riscv.org/reference/isa/extensions/vector/_attachments/riscv-v-spec.pdf) §12.11、§14.2、§16.1。独立模型仍是数学整数求和，没有复制此指令序列。

本实现适配测试框架的寄存器入口，生成固定寄存器组合的汇编 stub；不是接受运行时寄存器编号的通用 C 库函数。

## 3. 计时边界与事件

每个 stub 的 `baseline_<word>_begin` 到 `_end` 是完整核心序列边界，包含两次 CSR 快照、seed 清零、乘法/归约、配置切换、标量搬运、目的清零及配置恢复，共 13 条 32 位指令；不含前面的 mstatus 记录与末尾跳转观察。将来单条 vdot 的相应区间也排除共同观察代码。

核心算术子区间从 `_multiply` 到 `_reduce + 4`，包含 vwmul、必需的 e16/m2 配置切换和 vwredsum，共三条指令。单独两条算术指令的事件可另列；不能把配置开销从完整 baseline 统计中隐去。seed、清零及恢复属于完整序列统计。

T13 须同时输出以下记录，当前均为待实测：

| 项目 | 两边共同口径 |
| --- | --- |
| 功能预检 | 相同输入、目的初值、政策位和 CSR；先验证完整结果及上述共同出口状态 |
| 核心延迟 | 分别记录执行输入就绪、结果写回/可被依赖指令读取的周期；baseline 包含配置切换的实际依赖 |
| 完整序列 | 从确定的开始事件到最后恢复配置完成；统一选择提交事件或序列化计数器读，不能混用 |
| 依赖延迟 | 按候选指令消费源低八字节设计链，记录链中数据变化和预期；不能只重复覆盖同一目的就称为依赖链 |
| 吞吐 | 使用互不依赖的输入、目的及预分配 scratch，记录批次长度、issue/提交周期、资源冲突 |
| 装载/存储 | 核心比较两边都排除共同装载/观察；端到端实验则两边都计入相同数量的搬运 |
| 环境 | 同一硬件 SHA、配置、单核、时钟、内存、warmup、重复次数及差分开关；保存原始事件/CSV |

若用 `rdcycle`，需先核验权限和本核执行/提交顺序，实施对称的序列化并测量读计数器开销；不得先假定读数自然包住乱序流水线。统计报告需注明延迟或吞吐，样本数、原始周期、剔除规则和计算式。NEMU 指令数、QEMU/Verilator 主机秒数都不作为处理器加速比。

## 4. T09 的验收边界

当前入口 CSR、出口 CSR、完整目的、非 scratch 寄存器与缓冲区哨兵由 workload 检查；高位错误、非 scratch 错误、CSR 错误应被负控检出，声明的 scratch 改变应被允许。生成器对全部 32³ 寄存器编号组合检查 scratch 分组与非重叠；实际运行覆盖 T05 定向/别名/v0/v31、四种政策和固定随机输入。

实际平台结果与复现命令见 [baseline workload](../workloads/rvv-baseline/README.md) 和 [T09 记录](../docs/t09-baseline.md)。T09 模型验收不能替代非作者复验、T11 故障检出、T12 全核回归或 T13 的真实 RTL 两种序列配对及性能测量。
