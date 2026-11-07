# whole8：合并四行权重加载的源级候选

合同：`r3-dot16-whole8-source-v1`。本合同仅覆盖一个新软件变体的来源、变换和源级检查。**初始状态为 SOURCE_DERIVED_UNBUILT；没有 GNU、参考执行、整核或周期资格。** 当前 first-forward 四臂继续使用已冻结的 whole2，不由本文件改变。

## 目的与取舍

[whole2 的同镜像 Q288](q288-consumer/RESULT.md) 已实际通过，W 相对 plain dot16 平均少 15.7665% 周期。这里尝试进一步减少每个 GS32 组的地址计算和加载指令，不改变 dot16 指令语义、算术顺序、权重布局或生产 RTL。只有原候选的完整 forward 有价值且资源可用时，才安排新候选的小规模实测；这份源级推导不自动开启新 guest、扩大预算或替换稳定版本。

## 固定输入与变换

输入是既有 `host-01-evidence.zip` 中 `files/host-01/generated/whole2.S`，完整 SHA-256 为 `df2983a21ab85d982b51e7faa0710d536d2bd4afe5bc9c2b91577dd3450972c8`。也可使用相同 SHA 的已冻结副本。抽取并加上四行汇编头后的 whole2 单函数源 SHA 为 `7937fb177d0325622c16ddc4caa81a22c0c5134e64d8ba31cd70e92ec6bd1f18`，即本轮完整 forward 的实际源；原 whole2 机器函数 SHA 为 `b2b5b7fa44ecf9646a7c07fdaf971df8fad6430aec58161ffc3e2c3332d934a6`。最后一项只是历史对象的身份，不是新候选机器码证据。

`whole8.py` 仅增加 `q288_dot16_whole8`，完整保留输入源前缀。第一批四行的四组 `addi + vl2re8.v` 换成 `vl8re8.v v16,(a2)`；第二批换成 `addi t6,a2,128` 和 `vl8re8.v v16,(t6)`。仅另改新函数名及其两处局部循环标签。每项变换可逆，逆变换必须恢复原函数全部字节。

## 适用前提与数据路径

沿用既有固定 Q288 调用域：VLEN128、GS32、K288、288 行、九组每行、每 tile 八行，共 36 个 tile / 324 个组；入口清零 vstart。32B X 的两半分别保存在 v14/v15，各占一个 128 位寄存器。每批 W 的 128B 映射至 v16…v23；v16 对齐八寄存器组。两批地址分别为 `[a2,a2+128)` 和 `[a2+128,a2+256)`，与旧八次 32B 加载完全相同，不扩大分配范围。X 仍读取 32B。

按汇编程序顺序，第一批的低半、高半 dot16 均位于第二批加载之前，保留原有寄存器依赖。v8…v13 的 FP 状态、v0…v7 的低半结果、v24…v31 的高半结果互不覆盖。16 条 dot16、八条整数归并、FP 转换/乘法/累加、scale 读取、最终完整 128 位槽、输出、CSR 和 ABI 路径均保留；t6 是原有调用者保存临时寄存器，组后不消费其旧权重地址。

规范依据：[RISC-V Unprivileged ISA，2024-04-11，Vector Load/Store Whole Register Instructions](https://docs.riscv.org/reference/isa/v20240411/_attachments/riscv-unprivileged.pdf)。NFIELDS 支持 1/2/4/8，要求相应寄存器组对齐；当前 VL/SEW 不缩短 whole-register 传输。地址对齐按 EEW 和最小支持 SEW，而非 NFIELDS×VLEN 要求。此处仅使用 vstart=0 的既有正常路径，不新增中途异常恢复资格。

硬件、时钟/复位、FU 接口、两槽协议、最早 E2 响应及无停顿时 II=1 的既有条件均不改变；本变体没有新的硬件 PPA 结论。

## 预期计数与未验证项

| 项目 | whole2 | whole8 源级推导 |
| --- | ---: | ---: |
| 每组整数核心指令 | 43 | 30 |
| 完整函数静态指令 | 103 | 90 |
| 完整函数机器字节 | 412 | 360（待 GNU 核实） |
| 完整函数动态指令 | 21,090 | 16,878（待真实执行核实） |
| dot16 / 函数 | 5,184 | 5,184 |
| whole2 load / 函数 | 2,916 | 324 |
| whole8 load / 函数 | 0 | 648 |

静态推导少 4,212 条指令，约 19.97%；读取字节数与向量目的寄存器写入量没有减少。八寄存器加载的拆分、写回和使用者等待可能抵消前端收益，**不将指令减量换算为周期或完整应用收益**。

后续若执行，必须先核新 GNU 实际函数、前后缀/分支/寄存器和读写边界，再通过实际参考执行与既有完整输出/CSR/负控；新整核测量用独立合同和输出，在同镜像保留 whole2 与较快合格 RVV。现有 whole2 PASS 不转授新候选；当前四臂未完成时不抢占其四核，也不改变官方程序或冻结输入。

## 当前生产构建中的微操作依据

2026-11-07 只读核对了当前 EMU 的七份译码/向量访存源码，实际 SHA 均等于 `native-02/build-inputs.json` 的 `hardware_files` 项；该构建输入文件 SHA 为 `76853412c2c2f27e3e91fbdb0c25b89064023c908d648aa33491372fb5d6231e`，所属硬件见[整核身份与结果](../rtl-integration/fullcore/RESULT.md)。这项核对只支持静态实现分析。

`VecDecoder.scala` 将 VL2/VL8 都送到 `VlduType.vlr / VEC_US_LDST`。`UopInfoGen.scala` 的 whole-register 数量为 `nf+2`；`DecodeUnitComp.scala` 为每条加载生成一个基址 `i2v` 微操作，以及每个目的向量寄存器一个 load 微操作。因此，相同 128B 的四条 VL2 共 12 个译码微操作，一条 VL8 为 9 个；其中访存微操作均为 8 个。

| 每个 GS32 组的 W 加载及地址片段 | whole2 | whole8 |
| --- | ---: | ---: |
| 架构加载指令 | 8 | 2 |
| 地址 addi | 8 | 1 |
| 基址 i2v 微操作 | 8 | 2 |
| 访存微操作 / W 数据寄存器写入 | 16 / 16 | 16 / 16 |
| 上述片段译码微操作合计 | 32 | 19 |

`VSplit.scala` / `VecCommon.scala` 仍按 128-bit unit-stride 单位处理数据；VL8 不是一个 1024-bit 访存请求。未对齐时的后续拆流代价仍存在。较少的基址搬运和地址指令是可信的优化方向，但 9-uop 复杂指令按 rename 接收能力分拍输出，也可能遇到回压。

这里只给出所改片段的绝对计数；不能把全函数架构指令减少 19.97% 写成全函数微操作减少 19.97%。被删除的 `addi t6,a2,0` 在译码中可标为 move，尚未追查是否在 rename 消除，不能将所有被删 addi 都计作原本占用 ALU 的执行。无需为当前候选继续扩大静态审查，真实周期由后续小测决定。

## 仅生成源码

```text
python3 -B whole8.py --whole2-assembly <固定whole2.S> --output <新的绝对输出目录>
```

输出保留原输入、包含旧函数的新汇编、单独候选汇编及可逆变换/身份记录。脚本不会调用编译器、NEMU、EMU 或修改 Git。
