# Redoop 统一测试移植审计

本记录对应 2026-10-17 的独立本地对比。公开仓库：[redoop/xiangshan-vdot](https://github.com/redoop/xiangshan-vdot)，实际 commit `fba90f8eb0818ed9539aa097691b371fd852f7a1`（提交日期 2026-08-25）。原始快照保存在 `references/redoop`，工作变体位于 `variants/redoop`。

当前状态：源码移植完成，配套 NEMU 已构建，统一 NEMU 功能验证通过。此记录自身不宣称 RTL 全核通过或任何周期性能结果；全核构建及仿真由统一运行流程另行记录。

## 原生指令与统一工作量

原项目并非八对 INT8 归约指令。它在 SEW=32 下把每个 32 位源 lane 解释为四个有符号 INT8，对每个目的 lane 做 `oldVd[j] + dot4(...)`，结果模 2^32。VLEN=128、LMUL=1、VL=4 时一条指令执行四组 dot4，即十六次乘法；保留向量掩码/尾部机制。编码 funct6=111001、funct3=010、OP-V=1010111，vm=1 时基础编码 `0xe6002057`。

统一测试要求低八对有符号 INT8 点积写入低 32 位、高 96 位清零，且输入高 64 位可以是任意填充。不能把 Redoop 原生指令的吞吐率直接充当这项工作的吞吐率。

单点积采用以下七条适配序列，所有指令均位于计时窗口内：

```asm
vsetivli zero, 4, e32, m1, tu, mu
vmv.v.i v2, 0
# native vdot v2, vs1, vs2: 0xe6002057 | (2<<7) | (vs1<<15) | (vs2<<20)
.word NATIVE_ENCODING
vmv.v.i vd, 0
vsetivli zero, 2, e32, m1, tu, mu
vredsum.vs vd, v2, vd
vsetivli zero, 8, e8, m1, tu, mu
```

原生指令虽计算全部四个 partial lane，归约只读取低两个，所以高 64 位填充不会污染八对点积。目的寄存器在原生指令读完源之后才被清零，因此支持 `vd=vs1`、`vd=vs2`、`vs1=vs2` 等别名。SEW32、VL4 下清零完整目的寄存器，随后采用 tail-undisturbed 归约，确保高 96 位保持零。v2 是显式可破坏的 scratch，不能与操作数重叠。最后恢复统一入口配置 e8、m1、VL8。

batch4 共享配置切换：切 e32/VL4、清四个 scratch、四条 native、清四个输出、切 e32/VL2、四条归约、恢复 e8/VL8，共 19 条，scratch 为 v16/v18/v20/v22。不能据此宣称原项目已经达到这项统一工作量的最佳软件调度。

## 忠实移植范围

统一香山上游 `16ae9ddcda54fc9a2fddffad73174cf793ac7814`；YunSuan `cadd3c2f43096e253d61296b33ac697be8354e29`。其余子模块从 T15 已固定检出独立共享克隆，未修改旧源码目录。

公开仓库提供的是基于较新香山版本的完整文件，直接覆盖会带入与 vdot 无关的配置/CSR/缓存变更。本次只抽取 vdot 所需 hunks，保留统一上游其余行为：

- 追加 FuType.vdot；加入 needVecCtrl/isVecArith/VecArithFuConfigs。
- 注册 VdotCfg：同原项目 CertainLatency(2)、piped=true、五源、128 位输出，挂 VFEX0，复用其读写口。
- 注册自定义 Vdot 指令；VecDecoder 使用 VEC_VVV。
- VecExceptionGen 要求 e32；DecodeUnit 的 vmaInsts 保留 VDOT_VV，保证读取 oldVd。
- 原样复制 VdotU、Vdot64b、VdotOpcode、Vdot64bSpec；从 package.scala 仅取 VdotType 与所需 import。没有改算术单元、流水级数或目的累加行为。
- 移植了统一 CSR/ROB 计时观察补丁 `common-observers.patch`，它与功能补丁分开保存。

`MinimalConfig` 继承默认的 VFEX0 功能单元列表，因此不需要额外改变 MinimalConfig。当前 Scala/Chisel API 与公开 VdotU 使用接口一致；实际编译成功仍需由构建日志确认。

原始完整文件与统一上游的差异保存在 `redoop-*.scala.diff`。功能补丁分别为 `redoop-xiangshan.patch`、`redoop-yunsuan.patch`；精确 SHA256 见 `redoop.json`。不包含公开仓库无关的 HasBitmapCheck 默认变动、缓存配置变动、XSDebugDecode 及其他新版本改动。

## NEMU 与已完成验证

NEMU 基于 `a48a11f208ff81ad765591d83271d1b339fb3861`，位于 `variants/redoop/benchmark-nemu`。完整拷贝公开 `nemu-golden/vdot_instr.c` 函数体并增加五处登记：vopmvv decode、VECTOR_INSTR_TERNARY、EHelper、函数声明和实现。使用统一 `riscv64-xs-ref_defconfig` 构建。补丁见 `redoop-nemu.patch`，构建日志见 `redoop-nemu-configure.log`、`redoop-nemu-build.log`。

共享对象：`variants/redoop/benchmark-nemu/build/riscv64-nemu-interpreter-so`，SHA256 `4762f99366fee5bab12559f902c722d1b01eb22a2780df5ce09fa2e00d5d0387`。

统一功能验证命令（工作区根目录下）：

```bash
python3 -B repo/team/workloads/unified-vdot/reference.py \
  --variant redoop \
  --reference variants/redoop/benchmark-nemu/build/riscv64-nemu-interpreter-so \
  --output runs/redoop-reference-01
```

运行结果 `PASS_REFERENCE_ONLY`：generic_vdot_pairs=10154、known=10022、batch=10022。验证包含完整 128 位结果、寄存器别名、RVV 基线、单次与 batch4 适配。代码、输入及 NEMU hash 位于 `runs/redoop-reference-01/result.json`。

另外 `redoop-adapter-check.py` 的独立 Python 语义模型运行 10004 对输入 × 5 种别名，共 50020 case 通过。它仅检验适配算法，不替代 NEMU、RTL 或全核验证。

## 结果解释边界

本次后续测得的数字将表示“Redoop 原始硬件加统一八对点积软件适配器在同版 MinimalConfig 下的性能”，不能当作原作者环境的复现，也不能用来否定其四路累加/GEMM 原生用途。适配开销被完整计入，因此较低加速比可能来自目标语义不匹配，而非点积乘法电路慢。其原文 8.2× GEMM/标量、1.78 cyc/native 等指标仍是不同工作负载与统计方法，不应并入本次排名。

公开快照未找到根 LICENSE，本任务只保存本地来源及对比材料，不执行发布。
