# P3 当前 GNU 产物：宿主完整数值、CSR/ABI 与拒错

结论：**HOST GO**。第五次尝试完成合同绑定与完整宿主检查。仅进入后续有界目标探针合同准备；**尚未证明目标端正确性、性能、fflags 或异常**。

| 项目 | 当前证据 |
|---|---|
| 供体 | ffd668bf1bc80850d382f514d13bb00316c85582，vendor 冻结源 |
| 根合同 SHA256 | ab0d65657ac1eea3e14048a2c6afdf127119652f23ab33257441b9e687429faa |
| 当前 GNU ELF SHA256 | 50004cbc4436c8bd52edfae198527be48c224fb1baffc1e9986038e8bc3109f1 |
| fixture.zip SHA256 | 4b926d3c459e52ad3e9c8ec78c2dd22f090498b06a1b11b5188d7f1e75353913 |
| 原始记录根目录 | /home/riscv/riscv-lab/software-import-20261026/p3-qkv-host-20261030-01/numeric/ |
| 最终精简记录 | evidence/attempt05/result.json、coverage-recount.json |
| 运行约束 | CPU6 单核；attempt05 退出码 0，19.825 秒；EMU/NEMU/QEMU 0 次 |

## 当前验证量

| 门禁 | 覆盖与结论 |
|---|---|
| 身份闭包 | 根合同 source_manifest SHA 已绑定；143 文件/4792448 字节，前后 SHA256/Git blob 全匹配 |
| 原始 FP32 量化 | 两个活动位置与九组语义夹具，共 864 个 FP32、864 个 q 字节、27 个 scale；逐位相同 |
| 独立数学 oracle | 标准库 Fraction 实现 binary32 精确 RNE；显式 RMM ties-away；不依赖 donor FP oracle |
| GNU 量化器实际字 | 独立有限解释器执行当前 ELF；576 次 load、297 次 div、288 次 RMM、288 次 q 写、9 次 scale 写/输入；完整边界、NaN boxing、整数/FP callee-saved |
| 原始 C 量化器 | 重新 GNU 宿主编译不改动的 oracle.c 与上游 runq.c；三个输入全部 q/scale 一致 |
| 五类域外拒错 | 零组、NaN、Inf、scale 归零、正有限 scale 但转换越界；独立 oracle 与当前 C adapter 均拒绝；C adapter 拒绝前未写 q/scale |
| 独立 QKV | 两位置×Q/K/V：1728 个唯一 FP32 输出逐位比较；运算顺序固定 float(float(dot)*ws)*xs 再 binary32 加 |
| 当前 GNU 投影 | 两位置×两方法×Q/K/V，12 次直接投影、3456 个输出比较；全部匹配独立 oracle |
| 完整 wrapper | 两位置×两方法，4 条实际字控制/地址路径，另执行 12 次投影；一次量化后 3 次有序 QKV，共用相同 x/xs，16B 栈及保存寄存器还原 |
| 每笔完整 128 位 | 直接模型与 wrapper 路径合计 **124416 次 vdot 寄存器写、192 次 slot store**；每笔独立比较低32与高96；另保留最终槽比对。计数由 JSON 独立重算，并非仅写死总数 |
| CSR | 模型返回 vl=8、e8/m1、vstart=0、vcsr=7、frm=RNE；实际字只写 vstart/vcsr，无 FRM/FCSR/FFLAGS 写 |
| 实际 ELF 机器字负控 | 11 项全部拒绝；舍入、边界地址、vcsr、整数 ABI、FP 指令子集、slot 来源、输出别名、wrapper 保存寄存器等 |
| 检查器值负控 | 14 项：slot bit100，Q/K/V 输出，context/x，s0/sp，fs0/fs11，vl/vstart/vcsr/frm，全部拒绝 |
| oracle 自测 | 6 项：代表值回环、RNE ties-even、RMM ties-away、subnormal scale 与 128 越界见证、signed zero、overflow |

full128_adapter.py 只增强宿主模型，不改 vendor。独立 store hook 使用原 fixture 对应行/组重算结果；独立 dot hook 读取执行前两个完整 int8×8 操作数，检查执行后完整16B。donor 的 FullQ 直接调用父类 execute，所以适配作用于当前导入的内存模型类；磁盘 vendor 源仍冻结。

## 保留的失败及修正

1. attempt01 未通过：独立 dot hook 首先覆写了被 donor 父级直接调用绕过的入口，观察计数为 0；另一条负控误假定输出地址寄存器是 a0，产生 StopIteration。没有用该轮作为合格证据。
2. 仅修宿主适配与负控匹配，加入每次投影动态计数断言，attempt02 通过。attempt03 进一步补上 FP ABI / CSR 检查器值负控和分别 Q/K/V 输出污染，完整重跑通过。
3. 审查发现早轮 identity.json 的 source_manifest 路径错误，值为 null。只修当前入口读取 vendor/source-manifest.json，新增前后 143 文件 SHA256/字节数/Git blob 与根合同哈希绑定。attempt04 因自写 Git blob NUL 转义错误在执行候选前拒绝；改用 bytes([0]) 明确构造头部，attempt05 完整重跑通过。冻结 vendor、GNU ELF 与算法均未变化。
4. 各轮 stdout/stderr、源码哈希及源码快照均保留。第一轮源码快照按该轮已保存哈希精确复原并核验一致。失败源与日志不覆盖。

## 证明边界

- 量化器 flags **模型值**：位置0/1为 NX，语义夹具为 NX|UF；flags 初值0。该值来自精确数学有限模型，不是目标硬件 CSR 观测。
- 投影的 FP32 数值与 NaN boxing、FRM 静态编码已检查；完整 IEEE 异常/fflags、目标端中断/异常/执行协议仍 NOT_TESTED。
- projection-fp-callee-saved 实际字变异被有限模型的“不支持指令”拒绝，**不声称这项证明了 FP ABI 检查器敏感性**。FP ABI 检查器的敏感性由 fs0/fs11 状态变异特定 full-width ordinary ABI 拒绝单独证明。
- 这是当前 GNU ELF 的宿主指令子集数值/地址/ABI 证据。不能称为 NEMU DiffTest、全核通过或性能提升。原有 0f＋firstdot V2＋C8 默认候选不变。
- 目标输入在调用前须满足冻结合法域及互不别名合同；目标汇编入口自身不增加异常域检测。
- 本轮不运行 target，不采纳 donor 的 0.5% 性能门槛。后续目标探针须按根合同保持 1% 锚点和 3% 保守收益门槛，并重新冻结最终镜像及计数。

## 重放入口

在 WSL 中，以新输出目录执行：

    taskset -c 6 python3 -B host-numeric/check.py --vendor vendor --elf /home/riscv/riscv-lab/software-import-20261026/p3-qkv-host-20261030-01/migration/image-01/probe.elf --manifest /home/riscv/riscv-lab/software-import-20261026/p3-qkv-host-20261030-01/migration/image-01/source/manifest.json --output /home/riscv/riscv-lab/software-import-20261026/p3-qkv-host-20261030-01/numeric/fresh-replay

当前目录须是 continuation/p3-qkv-v1。脚本拒绝覆盖已有输出。所有实际 mutated ELF 留于原始 W 路径；仓库记录包含变异 symbol/word index/before/after/SHA，可由冻结 ELF 重建。
