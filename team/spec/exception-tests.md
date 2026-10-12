# vdot 异常测试方案

版本：`0.1.2-draft`，2026-10-12。适用合同：`vdot-s8x8-r32-v0.1`。

状态：异常 workload、陷阱处理程序、判定器与运行脚本已实现；QEMU harness 自测和负控通过，固定 nexus-am 的香山目标编译通过。T08 的真实 vdot standalone 合法/异常验收及补丁复现已通过，见 [T08 记录](../docs/t08-nemu.md)；RTL/NEMU 全核 DiffTest 尚待 T11/T12。实现入口见 [异常 workload](../workloads/vdot-exceptions/README.md)，范围与证据见 [T05/T05-E 初评](../docs/t05-t05e-review.md)。B/C 复核程序与采集判定，A 复核 RTL 异常路径；这些沿用计划角色，不代替成员认领或签字。

关联：[vdot 规格](vdot.md) §4.3、E01/E02；[RTL 接口](rtl-interface.md)；[进度](../progress.md) R02/R03。算术合法用例先按 T05/T07/T08 推进，异常方案落实为 T05-E，完整执行验收进入 T08/T11/T12。

## 1. 验收边界

必须证明异常来自指定 vdot 或指定非法机器字，且没有该指令的部分架构更新。不是只检查程序非零退出，也不能把未扩展处理器拒绝合法 vdot 当作扩展通过。

| 检查项 | 通过条件 |
| --- | --- |
| 前置合法对照 | 同一套运行环境中，合法 vdot 用例无意外陷阱，完整结果正确 |
| 陷阱次数 | 每个预期异常用例恰好一次；正常对照为零次 |
| `mcause` | 同步异常，异常码为 2；中断位不得置位 |
| `mepc` | 等于本用例 `fault_pc` 标签；准备指令、CSR 读取或恢复阶段报错均失败 |
| `mtval` | 记录实际值。标准允许非法指令携带零或指令信息；先固定平台约定，再比较 RTL/NEMU，不宽松忽略双方差异 |
| 目的值 | 128 位均与指令前预填值一致；至少包含全 FF 和交替位模式 |
| 向量状态 | 依实际构造的非法初态比较 vl/vtype/vstart/vxrm/vxsat/vcsr，不与合法默认值比较 |
| 其他状态 | 检查参与源、代表性非目的寄存器及内存哨兵；完整寄存器覆盖另登记，不能用抽样声称覆盖全部 |

陷阱本身改变 mepc/mcause/mtval 和特权入口状态，记录区、处理程序栈及明确列出的标量临时寄存器也会变化。这些与“vdot 不产生部分向量结果”分开比较，不比较全部架构状态逐位不变。M 模式陷阱 PC 和 mtval 的标准背景见 [RISC-V Machine ISA](https://github.com/riscv/riscv-isa-manual/blob/main/src/priv/machine.adoc)；本方案仍须在固定平台验证。

## 2. workload 与陷阱处理流程

实现目录：[team/workloads/vdot-exceptions](../workloads/vdot-exceptions/)，包含裸机 C 调度、生成的固定 `.S` 用例和陷阱入口。已查清固定 nexus-am 的默认 M 模式启动路径，保存/恢复 mtvec/mscratch/mie/mstatus，临时安装 direct mtvec 和独立处理程序栈，并屏蔽中断。该路径在 QEMU 和 standalone NEMU 验证；香山 RTL 的实际运行仍待验收。

每个用例按以下顺序执行：

1. 在合法向量状态下装载源、预填完整目的、保存源/目的预期快照；配置记录区、`fault_pc` 和显式 `resume_pc` 标签。
2. 设置本用例的非法配置。若配置可读，保存实际 CSR 初态；确认非法条件实际可达，其他条件尽可能保持合法。WARL 写入未达到目标值的案例记为 `UNREACHABLE`，不计通过。
3. 将 armed 标志置位，执行固定 32 位机器字；机器字由候选编码常量生成并经反汇编/字段检查。不通过未知助记符或无约束内联汇编发射。
4. 陷阱入口先保存约定的 GPR，使用标量指令记录 mcause/mepc/mtval/mstatus 和陷阱次数。只有 armed、预期 PC、同步异常码 2 都匹配时才进入恢复；否则转非预期陷阱失败路径，不静默跳过。
5. 在向量 CSR 可访问时先记录原始 post-trap CSR，再做任何向量配置恢复。处理程序初段不得执行向量操作或调用可能破坏被测寄存器的运行库。
6. 保存证据后将 mepc 指向预先登记的 `resume_pc` 并 mret；不对任意陷阱统一 mepc+=4。fault 指令长度、恢复地址和陷阱处理程序的 GPR 保存/恢复均须核验。
7. 恢复用于观察的合法状态，保存完整 16 字节目的和源/哨兵，比较快照。区分被测指令行为与处理/观察操作造成的状态变化。
8. 清除 armed，恢复下一用例的环境，输出逐项结果。没有陷阱而直接到达 resume 的用例必须报告 `MISSING_TRAP`。

嵌套陷阱设置有界保护和独立失败记录；超时、意外陷阱、缺失记录、未达到目标初态均不得归入 PASS。大批用例前先通过陷阱入口自测和一个合法 vdot 对照。

### 2.1 VS Off 与非法初态的观察

- VS Off 用例先准备并保存向量状态，最后关闭 VS；其后直到 fault 指令不得再读向量 CSR 或执行向量操作。陷阱入口只先记录 mstatus 的 VS 字段。
- 证据保存后才重新启用 VS，且不重写原向量数据；先读取可访问的向量 CSR，再设观察配置并读回目的。记录“VS 恢复”是测试操作，不能把恢复后的 mstatus 当作异常现场。
- `vstart!=0` 用例先完成所有加载、快照和向量配置，最后写 vstart，立即用标量读回核对；fault 前不再执行会清除它的向量准备指令。异常后先记录 vstart，再将其置零供结果读回。
- vill 用例通过实际受支持的 `vset*` 构造非法 vtype，保存实际读回；vill 与 vl=0 的联动同时记录，不能据此宣称隔离检出了 vill 条件。
- 结果读回可能改变 vl/vtype/vstart。只有先捕获的异常现场 CSR 用于无副作用判定；完整结果在合法观察配置下读取，例如 e32/m1/vl4 保存四个元素。

VS Off 时向量 CSR/指令的访问限制及 vset 对 vstart 的影响，参考 [Vector 1.0](https://github.com/riscvarchive/riscv-v-spec/blob/v1.0/v-spec.adoc)。这些规则约束测试准备，不定义本项目的自定义 vdot 合法域。

## 3. 用例矩阵

合法基准为 VLEN=128、e8/m1、vl8、vstart0、vill0、VS 启用、vm1；源与目的均在设置非法条件前准备完成。

| ID | 构造 | 必须观测及隔离限制 |
| --- | --- | --- |
| X00 | 合法基准，分别测正数和 D03 负数 | 零陷阱，128 位结果正确；这是异常批次的合法对照 |
| X01 | e16/m1，AVL=8，读回实际 vl/vtype | 不合法 SEW；仍为 vl8 时能隔离该条件，否则记录联动 |
| X02 | e8/m2；补充目标平台支持的 e8/mf2 | 实际 LMUL 非 m1；源目的预填不受准备阶段破坏 |
| X03 | e8/m1，分别设置 vl=0、1、7、9、16 | 每个实际读回值均独立记录；vl0 对本自定义合同预期非法，不套用标准空操作行为 |
| X04 | 合法配置后最后设置 vstart=1、7 | 实际非零，异常后仍保留该值，直到处理程序主动恢复 |
| X05 | 使用经核验的非法 vtype 编码 | 实际 vill=1；记录与 vl0 的联动，不伪造单条件覆盖 |
| X06 | 最后关闭 VS | fault 前不读向量 CSR；捕获 VS Off，恢复访问后确认目的未更新 |
| X07 | 保持 32 位长度及 custom-0，把 vm 改为 0 | 模型拒绝；确认无其他扩展占用后，全核预期非法 |
| X08 | 保持 opcode/vm，分别翻转 funct6/funct3 的固定比特 | 模型均不匹配 vdot；逐字检查现有译码占用后，选确实未定义的字做全核异常测试 |
| X09 | 正常源/目的、vd=vs1、vd=vs2；补充 v0/v31 | 在上述代表性非法条件下，完整源/目的快照不被部分覆盖 |
| X10 | 预置 vxrm 的四值、vxsat=0/1 | 代表性非法配置后保持实际 vcsr/vxrm/vxsat 初态；样本覆盖明确登记 |

模型的“不是 vdot”与处理器的“非法指令”是两个判断。不得把所有 mask 位翻转都用于异常测试：修改 opcode 可能变成其他合法指令，修改低两位可能改变指令长度。合法寄存器字段遍历属于编码/合法执行测试，不属于预期非法测试。

每个用例保存覆盖标签，区分单条件、状态联动、别名子例及不可达状态。X09/X10 不盲目做全组合；先覆盖边界和代表例，扩大覆盖时公布实际数量。

## 4. 三层执行与失败检出

| 层次 | 实现与验收 | 依赖 |
| --- | --- | --- |
| 模型/编码 | 合法性判定与拒绝原因；数学 oracle 不充当特权异常实现 | T03/T05 |
| standalone NEMU | 运行同一 workload，确认实际陷阱入口、PC、CSR 与快照；单独保存配置与 SHA | T05-E/T08；先验证固定 NEMU 的启动与陷阱支持 |
| RTL + NEMU DiffTest | 对照真实全核异常及恢复过程，逐用例确认合法对照、精确异常和无部分更新 | T05-E/T10/T11 |

先在原有指令上做处理程序自测，例如明确的 ebreak 并检查对应原因/PC；这个自测只验证 harness，不算 vdot 异常通过。合法 vdot 对照需要扩展后的平台才能运行。

加入三种 harness 负控：故意填错 expected PC、故意改变目的快照预期、构造异常Dirty→Initial降级，确认判定器检出。准备完后显式设置并读回VS，合法Initial/Clean操作必须置Dirty；非Off异常不得降级，允许Initial/Clean保持或升Dirty。T11 再使用可控 RTL/NEMU 故障验证协同比较，而不是屏蔽异常或目的高位差异。

## 5. 输出与整体判定

每个实际用例记录：

```text
run_id,contract_id,test_id,variant,rtl_sha,nemu_sha,workload_sha,
instruction,fault_pc,resume_pc,expected_cause,actual_cause,actual_epc,
actual_tval,trap_count,pre_vector_csrs,raw_post_vector_csrs,
csr_capture_phase,pre_vd128,post_vd128,source_check,guard_check,result
```

`result` 为 `PASS/FAIL/UNREACHABLE`。正常执行记录 trap_count=0，预期异常记录 trap_count=1；CSR 不可访问的阶段明确标注，不能补造读数。运行日志输出实际 ID 与原因，汇总同时显示 planned/executed/passed/failed/unreachable。

整体通过需：全部必需用例实际执行且通过，合法对照通过，无意外/嵌套陷阱和超时，DiffTest 启用，退出码 0。必需状态不可达时报告覆盖缺口，交 A/B/C 处理，不能只降低分母获得通过。

## 6. 实现交付清单

- [x] 已实现入口、GPR 保存、用例 arm/resume、日志和失败汇总；B/C 人工复核待完成。
- [x] QEMU harness 七项自测与三种负控通过，完成全部 32 个完整向量寄存器的观察比较；目标平台复验待完成。
- [ ] A 复核 late illegal 与早期非法的路径；不产生故障指令架构写回。
- [ ] X00～X10 的实际状态、用例子集和不可达状态均有记录。
- [x] standalone NEMU 自测、合法 vdot 对照及 37 个异常子例通过；新检出补丁复现通过。
- [ ] 全核 RTL/NEMU DiffTest 运行通过，包含合法对照、精确异常和完整状态比较。
- [ ] 原有 hello/vadd 仍通过；本方案和运行产物使用相同合同及配套 SHA。

当前交付为方案、基础设施代码与本地自测/编译证据。X00 对应 D00/D03 等合法对照；已生成 X01～X11 的 37 个异常子例。37 个异常子例已在 NEMU 实际通过；A/B/C 人工复核及 T11/T12 全核验收仍待完成，不能将 standalone 或自测通过标作全核通过。

当前37例包含新增X11的Initial/Clean异常状态；真实指令前pre32与输入逐字节比较，失败输出源快照/完整目的/首个post错误字节和PC，编译及执行来源强制绑定。修复和覆盖依据见 [综合审查修复](../docs/audit-fixes.md)。此前T08的35例归档仍保留原规模，不改写历史日志。
