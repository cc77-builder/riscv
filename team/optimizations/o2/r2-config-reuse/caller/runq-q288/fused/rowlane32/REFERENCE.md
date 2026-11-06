# Row32 W8：现有 NEMU 参考功能补证

**结论：固定旧 NEMU 参考库中的正常八次调用通过，既有 wrong-X 负控被完整数值比较拒绝。** 本次补上实际参考执行、普通返回、返回 CSR 和 fflags 的有限输入证据。香山整核、DiffTest、周期、完整应用和 PPA 资格仍未取得。

本补件对应合同 `r2-s3-runq-rowlane32-reference-probe-v1`。原 [RESULT.md](RESULT.md) 与 [COST.md](COST.md) 保持首阶段快照；本次实际运行单独记录于 [summary.json](evidence/reference-v1/summary.json)，原始数据为 [raw.zip](evidence/reference-v1/raw.zip)，完整91成员清单为 [members.json](evidence/reference-v1/members.json)。

## 1. 原函数与原输入保持

原独立 ELF SHA256 为 `fdb39f36e351c3907b3184d52233d1ee16c33e94b98b1317046823045a41ed22`。把其中完整 FR 592B 和 rowlane32 836B 以字节块嵌入一个新的裸机镜像，链接后再次从实际 ELF 提取并逐字节比较；函数外的 padding 不计入身份。

| 函数 | 新入口 | 完整字节 SHA256 |
|---|---|---|
| q288_fused_rvv4，592B | 0x80000340 | `66a12c0ec3cb7c0d1cdceadf04e4c658607438d83a2a958892100422343117ab` |
| q288_rowlane32_i8，836B | 0x80000600 | `f74b1a753a731dec5d803c9fca6afb1e1ca293737a85414f974b715d5912ea00` |

实际机器字独立审查确认两函数各只有两条内部相对条件分支及末尾ret，没有外部调用或依赖原代码位置的数据寻址。新上下文的七个字段逐项按最终 ELF 地址核对；内核仍只读取原前六个指针。

权重、X、原row-major Ws/Xs、独立 C/Python golden 和原 wrong-X ELF 均从首阶段冻结快照复用，五个原记录的SHA在导入前和构建后核验。FR与row使用各自正确的packed-W格式，x0/x1/x0复用各自相同packed地址。原严格逐组FP顺序和FMA见证保持。

启动原样复用固定提交 `c981529dc6e493fb7deee8429b9ce05fd197497b` 的 `forward-host/stages/projection/entry.S`。原AM提交 `086a238062fdfb3281b745a537b361983d0154b5`、链接脚本和预建am/klib保持，实际构建使用 `-o am -o klib -j1`。新包装显式初始化全部被检查的输出、guard、状态和报告，覆盖该启动入口仅清TLS的边界。

## 2. 实际正常与负控

一次正常镜像中，x0、x1、再次x0、W/X全−128依次各调用FR与row，共8次。每次检查全部288个Y的32位结果、八个完整128位slot、所有输出guard、观测到的全部输入及context字节。min/min保持原W/X地址模16为12的字节对齐。

| 输入 | FR与row的完整Y/slots | 主要覆盖 |
|---|---|---|
| x0 | 逐位一致 | 原严格FP/FMA见证，Y[0]=+0 |
| x1 | 逐位一致 | 更换X及对应尺度 |
| 再次x0 | 逐位一致且与首次相同 | packed地址及残留向量状态下复用 |
| min/min | 逐位一致 | −128×−128整数边界及额外字节对齐 |

全部实际返回状态为 `vl=8,vtype=0,vstart=0,vcsr=7,frm=0,vlenb=16`。每次调用前清FCSR，调用后读取的fflags全部为1，FR/row成对一致；这是累计NX（inexact），没有要求合法标志为零。标志语义参见 [RISC-V F扩展的fcsr与异常标志定义](https://docs.riscv.org/reference/isa/v20260120/unpriv/f-st-ext.html)。

负控在同一新镜像中替换原已冻结的wrong-X候选函数体，仅一个指令字内的一个字节改变。两种镜像都到达成熟GOOD TRAP；比较器仍对负控中的x0/x1/x0三次row调用报告Y及slots不匹配，同时FR全部正确、输入/guard/CSR与完整调用完成条件保持。全−128输入各字节相等，所以该wrong-X变异不改变min/min结果；负控判据明确使用原x0的Y错误。

## 3. 执行身份与资源

复用 `reference-adapter-04/reference-runner`，SHA256 `567ab9b91e7596c6bf682b56baeb42b36334e307fb54657dfe730eb2e1d98b9d`；参考库SHA256 `8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9`。未重建参考库，未写TO_REF寄存器，异常由现成runner正常观察。

本次实际作业为 `bee1ca65369429068a98a24c112ef728.752f904b65dad2b16a0f1cabee8e1721`，UTC 2026-11-06 01:46:24.142337–01:46:25.661773，工具回执1433ms、exit0、cleanup=true；Linux完整观察0.822秒。执行核为经主端释放的CPU0单核，外层上限120秒；正常与负控各最多1000000 API步/30秒。两次各实际232524次API调用、232523条退休指令；这些包含启动及包装，也不是香山周期。

01:48:25 UTC回读的构建、两次reference和两次compare共5份命令记录全部exit0、直接子进程已回收、进程组已消失。输入身份前后没有变化。资源窗口 [6674603820](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6674603820) 已由 [6674660914](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6674660914) 关闭；叶WORK继续保留。

| 产物 | 字节数 | SHA256 |
|---|---:|---|
| 新probe.elf | 382344 | `1fcbdadaa8d92c807f84188fb2b3d1716a728871e0fa9da36ba1cfda146dac6d` |
| 正常probe.bin | 357296 | `8aeddf57be08a7bd1ed68000837878ac54289b722a2d55d94c5d2ce9eed9146d` |
| wrong-X镜像 | 357296 | `8bcdf733dbeace0705e70c24836b3f15a3235730fbfd9edabf462bd316de2418` |
| 本次raw.zip | 933597 | `111338bc0b4ae051ffb0586a54072c01791db30e8249f08911a2cdb70a324f4b` |

## 4. 复现与判断边界

ZIP保存本次全部自有源快照、现成命令helper副本、新ELF/bin、工具输入身份、两套原始reference日志与寄存器/CSR/RAM dump、比较器和回执。91个成员逐字节SHA核验通过，展开共3182732字节。最初归档汇总把展开字节数计算为0；原汇总与仅更正该元数据的记录均保存在summary中，ZIP未重建、参考未重跑。

复现还需保留父 [screen-v1/raw.zip](evidence/screen-v1/raw.zip)（SHA `7a26ca8ae38603a125c3105ccebe741df709e19eb245d0e843b66db001005d1c`）以及 `runtime-inputs.json`、`build/build.json` 指定的固定NEMU/AM/GNU外部依赖。固定源在ZIP的 `reference-probe-01/source-inputs/`；实际一次性调用脚本在 `control/probe-launch-v1.py`。新目录的生成/执行仍须遵守当前资源协调及一次性路径检查。

本次新NEMU为2次，新EMU为0次。未新增目标完整ABI poison、精确访问足迹仪器、NaN/Inf或非RNE覆盖；原有限模型的相应证明范围单独保留。packing只用于fixture准备，没有目标机packing计时。下一步是否值得进入整核性能比较，应结合实际更强RVV结果和资源安排另行判断；静态指令/uop减少及本参考执行时间均不能当作完整应用收益。
