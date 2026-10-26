# 实际活动输入 FP32→QKV 目标合同 v1

身份：`r2-s3-runq-active-qkv-target-v1`。这是独立的新实验，不重判历史目标结果、不修改官方或冻结的参考、验证器、硬件和既有入口。

## 边界与输入

从已通过 `active/check.py` 的三状态活动 forward 捕获选定层 0、位置 0/1（token 1/7）；模型是确定性未训练权重，不包含质量结论。固定选择在目标计时前作出，输入归档 SHA-256 为 `4b926d3c459e52ad3e9c8ec78c2dd22f090498b06a1b11b5188d7f1e75353913`。位置 0 是全部正式计时输入；位置 1 只作两路功能验证。三组 288×288、GS32 权重与其既有持久 pack 在 ELF 中预先固定，pack 成本不计入本实验。

共同 `qkv_boundary` 从真实 288 个 FP32 输入开始，运行一次量化，然后按 Q/K/V 顺序调用三个完整 Q。两路共用同一函数、量化器、输入、输出、slots 和数据地址，仅 kernel 表项选择 TA=`q288_tail_vdot` 或 FR=`q288_fused_rvv4`。两函数及公共 `split_measure` 的完整机器字须和已合格来源相同；不把旧 ELF 周期移到新 ELF。

计时包括调用、一次量化、三投影和返回，不包括 pack、RMSNorm、RoPE、attention、KV 写入、FFN、classifier、token 或完整 forward。全活动 forward 的独立宿主验证不升级成目标整模型性能资格。

## 量化语义

原样上游 `runq.c`（提交 `350e04fe35433e6d2941dce5a1f53308f87058eb`）定义：每 32 元素计算最大绝对值，binary32/RNE `s=max/127.0f`，再 binary32/RNE `z=x/s`，最后 `round(double(z))` 转 int8。新标量固定循环用同源 `fsgnjx.s`、`fmax.s`、静态 RNE 的两次除法位置，以及静态 RMM `fcvt.w.s`。不使用倒数乘法，不修改 `frm`。

定义域在主机冻结输入前检查：所有输入有限，每组最大值非零，scale 有限且正，每个 FP32 商有限且 `round(z)∈[-128,127]`（等价 `-128.5<z<127.5`）。正 scale 本身不足够：最大正数为 `128·2^-149` 时 scale 为 `2^-149`，商 128 必须拒绝。全零、NaN、Inf、scale 舍入为零、超出 int8 的五个反例均不得进入上游未定义强转或目标正式样本。

原上游量化经独立宿主适配器生成全部 q/scale 位模式，并与活动捕获一致。第三个 9 组语义输入覆盖四个半整数的前驱/精确/后继及负号、±0、子正规 scale、商下溢、正规/子正规边界、非二次幂 scale 和大有限数。实际目标先执行这三个非计时量化探针并比较全部字节；主机明确核对最小子正规 scale 未被清零。`frm=RNE` 保持；允许 NX/UF，拒绝 NV/DZ/OF。不要求主机 libm 和目标的 fflags 相等；原始 DiffTest 不放宽。

规范依据：[RISC-V F 2.2](https://docs.riscv.org/reference/isa/v20260120/unpriv/f-st-ext.html) 的舍入模式与转换定义；[C 委员会草案 N1570](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf) 6.3.1.4、7.12.9.6。对有限非负幅值，固定 fmax 扫描与原 if 比较选同一 maximum；FP32 商提升到 double 精确，RMM 对应 round 的中点远离零。

## 事前计划与判定

计时顺序 `FR,TA,FR | FR,TA,FR`，每窗先运行相同方法的一次完整边界 selfwarm，warm 与 measured 各自相同 prepare。位置 1 额外 TA、FR 各一次功能调用。共 14 边界、42 完整 Q、12096 输出；TA 为 5 边界/15 Q，FR 为 9 边界/27 Q。边界内量化 14 次，加 3 个独立量化探针，共 17 次/153 组/4896 元素。

正常全过程 custom COMMIT=155521（含一个高96位故障探针）；计时 custom=62208；CSR_SAMPLE 与 COUNTER_ENQUEUE 各24。四个 FR 全部保留，锚点要求 `100*max(FR)<=101*min(FR)`。正确性和锚点成立后，只有 `200*max(TA)<=199*min(FR)` 才选择 TA，否则该边界选 FR；锚点失败 HOLD。两区块完整保留，不删窗、不增加样本追寻有利结果。replay 是复现检查，不是独立性能样本。

选择仅适用于该最终 ELF、所选层/位置/输入、具名 FR、共同标量量化和预热规则。它不能代表全局最优 RVV 量化、所有上下文或机制的独立净收益，也不把历史百分比相乘。

## 验证与保存

GNU 实际构建命令、完整源闭包、生成文件再生成、ELF/BIN、旧权威 object/函数字节、输入数组及路由表均逐位核对。新路径适配器只解释共同 wrapper 和固定量化循环的整数控制/地址；FP 值不参与控制。三次 Q 使用原有实际 ELF 数值/地址/ABI 模型。验证完整路径、一次量化、顺序共享输入、所有量化读写、三输出、栈及保留寄存器；最终目标值由原样量化 golden、独立 Q golden、全输出检查及原 DiffTest 共同核对。

每次 warm/functional/measured 都比较全部量化字节、scale、864 输出、三个末尾 slots、guard 和返回状态。六项运行内 judge 反例覆盖 q、scale、K 输出、高位 slot、输出边界和 context。离线变异覆盖新增 FP32/路由/量化舍入和 selector 判定面。

复用 T17/NEMU/AM/flash 实物，单 EMU 串行 negative→recovery→replay；总 CPU≤4，正常每进程至多18000000 guest cycles、7200秒。第一次 custom 的既有高位错误必须被拒绝，恢复和重放须通过且完整验证结果相同。所有源/输入前后身份不变。保留原命令、原始输出、失败记录及可独立复算的归档，不用摘要代替证据。R5 默认与历史回退不变。
