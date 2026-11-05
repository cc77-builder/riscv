# dot16 独立原型与完整 Q288 软件筛选

记录时间：2026-11-05 UTC。工程叶：`20261106-LiZufan001-mdot4x4-pro2`，当前范围为本 `dot16/` 目录；`nemu/` 由另一执行者独立维护。

## 1. 结论与采用边界

**本阶段完成了独立 Chisel/Verilator 原型、同条件 Nangate45 综合/STA，以及真实 GNU ELF 的完整 Q288 数值和地址筛选。尚未修改生产译码或 FU，也没有新整核、NEMU/DiffTest 或周期结果。**

后续硬件候选选择 `direct16`：16 对乘积在 P 槽保存，完整归约结果在 R 槽保存。`split16` 把最后一级加法移至 R→输出，虽然缩短寄存器间路径，却恶化本次最差约束，且略增面积，因此不作为当前接入方案。

新完整 Q288 函数实际执行 26,922 条指令。另一路 GS32 标准 RVV 也已进入候选筛选；优先利用现有 T17 测量其完整 Q 周期，再共同决定新硬件是否值得整核构建。这里不依据静态条数判定实际性能胜负，不将旧跨镜像收益相乘。

当前文件是候选源码与工程记录，尚无生产启用或性能合格结论。旧 dot8 编码、冻结实验、官方程序及旧检查器保持原样。

## 2. 规格、微架构与实现

新精确编码为 `MATCH=0x0e00000b`、`MASK=0xfe00707f`，旧 dot8 `MATCH=0x0200000b` 不变。合法 dot16 条件是 `vm=1`、`e8/m1/VL16`、`vstart=0`、`vill=0`，接受四种 vta/vma；源/目的别名和普通 v0 使用遵循完整源快照语义。

16 个 signed8 乘积的精确和范围为 `[-260096, 262144]`，需要 signed20；输出低 32 位符号扩展，高 96 位清零。旧 dot8 仅使用各源低 64 位；16 路原型在接受沿把旧操作的高 8 个乘积置零，因此后续阶段不依赖新输入的 mode。

三个原型均使用同步高电平复位，复位清有效位。理想时序为 E0 接受、E1 P→R、E2 最早响应；无阻塞时每周期可接受一条。P/R 分别保留各自身份，输出阻塞时保持，外部 `kill_p/kill_r` 决策控制取消；所有 redirect 禁止当拍新接受，无关 redirect 不取消旧 R 响应。

此原型的 tag 是 32 位简化身份，kill 由外部输入提供。它没有实际 RobPtr、完整 production control/perf bundle、DIV 仲裁、译码、CSR 或 DiffTest，不能冒充生产 FU/父级验收。

软件保持原 `P[t,g,row,k]` 权重布局：每 GS32、8 行加载 32B X 和 256B W，各字节恰好一次。X 使用 v16/v17，W 使用 v20…v23，两半结果使用 v0…v7/v24…v31；v8/v9 的 FP 累加值保留。16 条 dot16 后使用 **VL4/e32/m1** 的 8 条 vadd 合并，完整 raw slots 高 96 位继续为零。VL1 不适用于后续四行 packing。FP 仍逐组执行 `((float)dot * Ws) * Xs` 后累加，顺序不变。

## 3. 正确性验证

### 3.1 独立 RTL 原型

最终生成目录：

`/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prototype-v4-pro2-940aee3b`

三个变体都真实通过 Chisel 生成、Verilator 编译、原型测试及结果比较器故障注入拒绝。每个变体的记录为：185,810 个测试周期、139,396 次接受、139,263 个响应逐项比较、133 次取消；139,251 次响应/P→R/新接受重叠，46,387 个阻塞周期。`ready_kill_r` 与 `redirect_responses` 两种定向边界各命中 2 次。direct16/split16 各有 45 个非法响应，baseline8 有 69,651 个。

测试使用独立 signed 标量求和作为数值期望，检查完整 128 位输出、tag、非法状态、写使能和两槽流控；取消的接受不计为已比较算术输出。结果翻转注入检查的是原型比较器，不是 live DiffTest 负控。

| 变体 | 最终生成 RTL SHA256 |
|---|---|
| baseline8 | `add42cbb562c292234cb8707e11adb805b2c65006ea18d9d5df37c5f25ed4937` |
| direct16 | `f358fadd015ed9cad822668b12ab2de5e842e0bec10625cab6d0ce8310f23d79` |
| split16 | `1343f94bcd14f20f0353b4c178e15d60666efcbb6e9a4a0d17309d1dddfc6d24` |

### 3.2 真实 ELF 的完整 Q288 筛选

运行于 2026-11-05 22:52:20–22:52:22 UTC（运行器记录）：

`/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-software-screen-v1-pro2-1412712e`

状态 `DOT16_ACTUAL_ELF_SCREEN_PASS`。实际 GNU 编译/链接的 ELF SHA256 为 `1eb66bd106e6fc03a2ac7857040e0d250f189b2f30cd8a87a60bb6a7dfdc7cfd`；GNU 编译器 SHA256 为 `0c54895c55568be5b5fee49e2426abcc8fb05ca2c121ca5685dea2cbc24a1c13`。

独立机器字符号证明得到 61 字整数核：2 次配置、18 次加载、17 次地址加法、16 条 dot16、8 条 vadd；每组含公共 FP/循环部分为 82 字。核心 SHA256 为 `ddf1ae19143ba72369ec7f2235f7b965f1fbdf24d1d0624c5138c471d2e522a1`。完整函数 484B，动态执行 324 次整数核、5,184 条 dot16、2,592 条 vadd，共 26,922 条指令。

8 组测试包括 x0/x1/x0/x2 复用同一 packed W、min×min、max×max、min×max、zero weight，以及不同紧凑缓冲区偏移。每组检查：

- 288 个 FP32 输出逐位等于独立原生 C oracle，并与独立 Python 参考一致；保留严格 FMA 舍入见证。
- 最后 8 个完整 raw slots、全部输入/context 字节不变、逐字节完整读写 footprint。
- 标量/FP 被调用者保存寄存器、返回、最终 VL/SEW/LMUL/vcsr/frm；FP 元素操作数仍是 convert=2592、mul=5184、add=2592。
- wrong X half、旧 dot8 opcode、wrong W row、wrong partial reduction、VL1 packing 五个实际 ELF 变体，均由符号证明与数值路径分别拒绝。

这是有限 host 指令模型，未覆盖 NEMU、完整异常/fflags 或周期。旧 `FullQ.check_full` 没有被用于给新候选判 PASS；新 leaf 通过明确 MRO hook 执行新指令并独立检查新计数。

| 同一 ELF 中的函数 | 字节数 | 完整机器字节 SHA256 |
|---|---:|---|
| 保留旧 TA：q288_tail_vdot | 764 | `b318b99344d0ceabb2a5cab6ce671ab2bfcb189e4aacc9ffccb18488165971f3` |
| 保留旧 FR：q288_fused_rvv4 | 592 | `66a12c0ec3cb7c0d1cdceadf04e4c658607438d83a2a958892100422343117ab` |
| 新 q288_dot16_vdot | 484 | `ee92c07b7803b04c5340ba4412cb36326b8f5ed42fbf0677fc2f210bcd6711bb` |

旧 TA/FR 字节与原已合格 TA 镜像中的对应符号一致；新 ELF 的调用地址不同，因此性能仍需在新同镜像条件重测。这里没有把保留机器字节等同于新目标已运行。

## 4. 同条件综合与时序

最终目录：

`/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-cost-v5-pro2-8951c67e`

状态 `THREE_INDEPENDENT_PROTOTYPE_COSTS_RECORDED`；`result.json` SHA256 为 `12fa34225823f298aa61d972e6124019d2435ac4aea425a6297c54cd85aee0a5`。运行器记录 22:56:27–22:56:38 UTC；外层执行回执为 exit=0、cleanup_complete=true。

共同条件：Nangate45 typical、ABC 1000ps 目标、1ns 时钟、0.05ns uncertainty/clock transition/input transition、0.1ns input/output delay、5fF 负载、`5K_hvratio_1_1` 线负载。面积为 Liberty 单元面积之和，并与 Yosys stat 交叉校验；无未映射单元。DFF 是映射后的单元数。

| 指标 | baseline8 | direct16 | split16 |
|---|---:|---:|---:|
| 单元面积（库 area 单位） | 7173.222 | 13850.886 | 13867.112 |
| 单元数 | 5420 | 10693 | 10845 |
| DFF 单元数 | 230 | 358 | 364 |
| input→register arrival（ns） | 1.165737 | 1.242222 | 1.194682 |
| register→register arrival（ns） | 1.155945 | 1.226258 | 1.150119 |
| register→output arrival（ns） | 0.323454 | 0.332286 | 1.259741 |
| input→output arrival（ns） | 0.319318 | 0.329131 | 0.319318 |
| out-ready→in-ready arrival（ns） | 0.302887 | 0.311696 | 0.302887 |
| 最差 slack（ns） | -0.240952 | -0.317437 | -0.409741 |

**三者均不满足本次 1ns 约束。** `arrival` 是 STA 数据到达时间，输入类包含设定的 0.1ns 输入延迟；不能直接当纯组合门延迟跨类相加。direct16 面积约为本独立 baseline8 的 1.931 倍。split16 的关键输出终点是 `io_result[19]`，不是控制 ready；此代价不能只报较短的 P→R 路径而省略。

本结果不包含 production FU 的完整控制位、父级选择/布线或整核，不能作为整核面积、目标频率或功耗结论，也不代表赛事规定了 1GHz 硬门槛。

Yosys 为 0.9，OpenSTA 为 2.0.17。split16 的原映射网表具有 OpenSTA 不支持的拼接左值。最终适配仅将已明确检查的常量/符号扩展别名拆成两条连续赋值，保留原 `mapped.v`，另写 `sta-readable.v`；同 Yosys 重读两者后，完整模块图除源位置属性外逐项相同，图 SHA256=`d7abe51eec3fb7bcf98ed842ce69298d9ded216c2f396a9fae8a78f7210070c8`。单元和连接未改变；baseline8/direct16 无此转换，前后文件逐字相同。

## 5. 版本、复现与失败记录

参考源码核对点为 `352789e1975a3a409d39f67d143de6cf04938745`；运行使用常驻 WSL 的 `5c7cd127b12a46d4927ddb6f0ef359fde0ba4c91` 工作树加本 leaf。所需历史源码逐文件固定 SHA 并在运行前后检查，不能把两个仓库 HEAD 当成相同源码身份。

| 当前候选源 | SHA256 |
|---|---|
| CONTRACT.md | `425a67aa3eb083609b284737c435c56314662363b32736cd562b0283f87c66bf` |
| Dot16.scala | `cd45ab690d03751dad1f72ebd25c85f7875e88dcf8c2638e8cd230da82016624` |
| run_prototype.py | `844b84fac59f5355df3fa108c46f7e362d9d23d1ccfc01545326c79d2ec9d7a0` |
| prototype_test.cpp | `d8b7de85f73c04f89f3bcc945e098aac51e7a7b834c1f6c7053df566272f976e` |
| build.sc | `c8aab3b6ce62200acaf19fc6e6c6a639b9da8f461db8bbf3006e6ffe2355204d` |
| .mill-version | `01a507eda916863d2c56c6d24b13985c877640445bb13e272692d67ccf33f057` |
| cost.py | `0e6933428b7d66b7cce8989169ce61f4742958a9ad206f93c6cffc69a2d5d55e` |
| cost_helpers.py | `bee29ddcfb0b1b6281dd8e05637bd9a032587a7b5ec18abaf85e08dda26be209` |
| candidate.py | `ad6de7c872f2695297d91a0ed6cb88cb2d71169c7093cf05ff993b87c419e363` |
| screen.py | `c53224cfaeb990fd11f2e71a5201988de00ff86f5a9651083baa89b6c3c81006` |

原型依赖固定 `team/rtl/vdot/param/VDotParam.scala`，SHA256=`617292743d0e9515ffc18b6099f87c706099a12385e42f0ef60b6cc9b0680c39`。Nangate45 库 SHA256=`8d540a4d4cf6d09d27c87ad067857a9c0c2eeb023ab7a56e058cd3113db4e9b1`。每个输出目录另存完整输入/工具身份和命令，不依赖“旧报告 PASS”转移。

复现入口：`run_prototype.py --repo ... --output <新外部目录>/<变体> --variant baseline8|direct16|split16 --jobs 2`；三个变体完成后，`cost.py --repo ... --prototype <三变体目录> --control <同目录> --output <新外部目录> --library <固定库> --jobs 2`；软件入口为 `screen.py --repo ... --output <新外部目录>`。脚本须放在仓库本 leaf；所有构建/实验输出放在仓库外。

原型环境为 GraalVM JDK 21.0.12、Mill 0.12.3、Chisel 6.6.0、firtool 1.62.1、Verilator 5.052；运行器以 Bash 调用本机无 Unix shebang 的 Mill polyglot launcher。最终 firtool 采用仓库既有 `disallowLocalVariables,disallowPackedArrays` 选项，并对新生成 RTL 重新执行检查。

失败记录保留在同一 `runs` 根下：

| 运行 | 真实结果与处理 |
|---|---|
| dot16-prototype-v1-20261105-222655 | Mill 直接 exec 返回 Exec format error，尚未生成 RTL；改用显式 Bash。 |
| dot16-prototype-v2-20261105-222852 | 三原型通过；随后发现随机 flush 与 ready 相关，原测试未覆盖 ready=true 的定向边界。 |
| dot16-prototype-checker-v3-20261105-223308 | 在上述固定 RTL 上补齐定向 ready/flush 检查并通过；最终 v4 在兼容输出 RTL 上重新通过同一新版 checker。 |
| dot16-cost-v1-pro2-a9b0f4ec | 输入预检发现 WSL 与 Windows O4 helper 版本不同，未运行综合；用新 leaf 固定纯函数适配，旧文件不变。该预检发生在创建输出目录前，以执行失败回执为准。 |
| dot16-cost-v2-pro2-58b6e71a | Yosys 拒绝局部 automatic 声明；未完成映射。 |
| dot16-cost-v3-pro2-940aee3b | 三者映射完成，baseline8/direct16 STA 有效，split16 因 OpenSTA 拼接左值语法失败。 |
| dot16-cost-v4-pro2-5c3148bd | 尝试标准 splitnets 未解决旧 OpenSTA 语法；失败，不作为成本结论。 |
| dot16-cost-v5-pro2-8951c67e | 明确等价的输出别名表示转换经完整图核对后，三者成本全部记录完成。 |

未建输出目录的 cost-v1 失败回执为 `64a20bc02563ede90337a78e57578fe0.f5d58a4788f0ee52f2fa852841a7517b`；最终 cost-v5 成功回执为 `626659bd04cf00cf6a5fd074939373bd.5c5a36475a641149cfc5dee4a4751425`。时间以各自回执/运行器记录为准。

## 6. 接入前仍需完成的工作

1. 用现有硬件、同镜像及同计时/预热条件比较新 GS32 RVV 与原 TA/FR；保留实际较快的合格对照。
2. 若继续 dot16，单独协调生产 Instructions、VecDecoder、RiscvInst、VDot op 与 elastic FU 的接入范围，明确功能开关和版本。非 elastic/T14/O1 不默认获得新指令。
3. 新合法指令、仅 VL 非法、译码已知非法、别名、完整写回及新 NEMU profile 必须由新构建实际验证。静态源码表明“仅 VL 错”预计仍由 FU 检出并产生 xTVAL=0，但当前无新整核运行，不能转移旧 dot8 的异常 PASS。
4. 新硬件同一 ELF 对比 dot16、旧 TA、最快合格 RVV，再进入完整 QKV/forward 消费者；不得将 FU 吞吐或静态指令缩减直接当应用收益。

此阶段已释放 CPU，不存在仍在运行的本叶构建、仿真或 EDA；是否继续整核由上述实际收益和成本共同决定。
