# R2-S2：4×13 安全向量尾部候选

日期：2026-10-21。基点：`a89648d78bc954d9e27a78b987d3fef63cc1ab93`。
本轮只发布到 `cc77-builder/riscv:zjhwork2`，不修改 `zjhwork`。

**状态：S2 已实施，主机/交叉汇编/指令级模型/原渲染器集成检查通过；真实香山 EMU + NEMU DiffTest 与周期筛选尚未运行。不能宣布 R2 完成或 S2 提速。**

## 1. 改动范围

`candidate.py` 是独立、显式选择的候选入口，不改旧 `team/workloads/o3-gemv/generate.py`、原始黄金模型、生产 RTL、ISA、NEMU、默认模式或封存数据。固定原生成器、模型和原装配渲染器的 Git blob；身份变化时拒绝继续（允许普通 CRLF 检出转换）。

S0 始终产生原内核。S2 仅替换 `(M,K)=(4,13)` 的 vdot 标量尾部，支持 basic/reuse 和 core/endtoend。其他原形状、所有 RVV 和原标量尾部对照保留。16×64 是不应改变的控制形状，S0/S2 机器码已逐字节相同。

新的生成结果仍使用原四个 case、同一 C ABI、完整 128 位黄金输出、受保护向量寄存器、输入布局、计时 marker 和正反执行顺序；新合同标识与 `r2_variant` 防止候选冒充旧证据。S2 每个 4×13 vdot case 的 `dots` 已从 4 更新为 8，供后续真实运行严格核对，未通过放宽旧检查器绕过计数。

## 2. 安全尾部的具体实现

先完成前八项并把其部分和保存到原来的标量累加器。此时当前 A 块、x 块和部分和向量均可复用，不引入新的 scratch 寄存器或 spill。

1. `VL=8, e8, m1, tu, mu`，明确清零 `v24` 和当前组的 `v16..v19`（basic 仅用 v16）。
2. `VL=5, e8, m1, tu, mu`，分别加载 x 尾部及各行的五项。`tu` 保留刚清零的 lane 5..7。
3. 恢复 `VL=8`，再执行合法的 dot8；切换到原 e32 配置，累加尾部结果。
4. 输出形成、完整高 96 位零和原计时边界保持不变。补零、配置切换、读取和累加都在对应计时窗内。

4×13 紧凑输入总共 65 字节（52 字节 A + 13 字节 x）。reuse 的五次尾部读取为偏移/长度 `(60,5)、(8,5)、(21,5)、(34,5)、(47,5)`；完整调用读取的输入总字节数仍为 65。模型逐行检查读取范围，不仅检查分配区总长度，因而不会把读入下一行的数据当作合法补零。未使用行间 padding、预打包、计时外补零或 tail-agnostic 恰好为零的假设。

依据：RISC-V V 1.0 的 tail-undisturbed 保留旧值，而 tail-agnostic 允许保留或写全 1，不能依赖它补零。官方规范：
https://docs.riscv.org/reference/isa/v20260120/unpriv/v-st-ext.html （30.1.3.4.3）。

## 3. 实际编译后的指令变化

下表为计算主体（含 endtoend 的初始配置与输出存储），不把固定测量包围序列当作可省掉的工作。

| 4×13 reuse/endtoend | 原 S0 | S2 |
| --- | ---: | ---: |
| 主体总指令 | 117 | 83 |
| 连同原 12 条 marker/fence/计数包围序列 | 129 | 95 |
| 自定义 dot8 | 4 | 8 |
| `lb` | 25 | 0 |
| `mulw` | 20 | 0 |
| `addw` | 24 | 8 |
| `vle8.v` | 5 | 10 |
| `vmv.x.s` | 4 | 8 |
| `vsetivli` | 6 | 10 |
| 显式向量清零 `vmv.v.i` | 4 | 9 |

原 65 条标量尾部换成 31 条安全向量尾部，主体少 34 条（29.06%）。basic/endtoend 从 146 降至 118 条；其配置切换也明显增加。RVV reuse 仍为 62 条，16×64 reuse 的 vdot/RVV 仍为 818/614 条。不能只报告减少的指令，也必须保留新增 dot8、向量加载、配置与跨域搬运的代价。

**指令数减少不是周期加速比。** 本轮没有新的 cycle、IPC、ready/busy 停顿、功耗或时序结果，也没有证明 S2 已追平较快 RVV。

## 4. 本轮确实执行的验证

| 层级 | 结果 | 边界 |
| --- | --- | --- |
| 主机单元测试 | 21 项通过 | 包含 8 项故意破坏的候选负控，不是硬件故障注入 |
| 独立计算主体交叉汇编 | 24 份通过 | 两形状 × basic/reuse × core/endtoend × S0-vdot/S2-vdot/RVV |
| 原 ELF 字节对照 | 4/4 一致 | 四份 S0 reuse/endtoend 主体 SHA256 与上一轮真实 ELF 提取记录一致；不是重新校验整个旧 ELF 包 |
| 机器码指令级模型 | 7,452 次执行通过 | 4×13 的 533 组输入和 16×64 的 88 组输入，各 12 种配置；不是 NEMU 或 RTL |
| 原渲染器集成 | 24 组生成源码、96 个完整函数及 24 个 C ABI 对象编译通过 | 真实固定原渲染器；未链接为可执行 benchmark ELF、未执行完整 harness |
| 生产 RTL/真实 EMU | 0 次新构建、0 次新 EMU 运行 | 不因主机检查通过而宣布 DiffTest 或性能通过 |

533 组为 3 组原数据、5 组边界、13 组单 lane 定向和 512 组固定随机。88 组为 3 组原数据、5 组边界、64 组单 lane 和 16 组固定随机。不同配置复用这些输入，不把复用次数冒称更多独立向量。

模型直接解释 Clang 17 产生的机器码，不执行候选 Python 来生成 DUT 输出；另用标量数学公式检查结果。每次向量寄存器从非零随机污染状态开始，检查完整 128 位输出、输出存储、受保护寄存器、最终 CSR、dot8 合法 VL 和每行内存边界。它仅实现本批直线内核所需指令，未知指令拒绝；没有乱序、流水、缓存、异常/取消或周期建模，不能替代 NEMU/DiffTest。

八项候选负控：删除尾部清零；tu 改 ta；错误地读八项；遗漏恢复 VL=8；跨行加载；漏加尾部和；高 96 位未清零；破坏受保护寄存器。均被检测。源码漂移、未知指令、截断机器码、已有输出目录也有拒错检查。

详见 `evidence/validation.json`、指令统计与测试原始日志。两份完整报告及交叉汇编的命令、返回码、正文 `.S/.o/.bin`、反汇编和完整生成源码保存在本轮交付包；摘要记录完整报告 SHA256，未把大量可再生对象纳入日常源码。

## 5. 复现入口

从完整仓库根目录运行，Python 3.10+，Clang 带 RISC-V V 支持；本轮实用 Clang/LLVM 17。所有输出路径必须是新目录。

```bash
python3 -B -m unittest discover -s team/optimizations/o2/r2-safe-tail -p 'test_*.py' -v
python3 -B team/optimizations/o2/r2-safe-tail/screen.py \
  --repo "$PWD" --output /absolute/new/r2-s2-host-screen
python3 -B team/optimizations/o2/r2-safe-tail/integration.py \
  --repo "$PWD" --output /absolute/new/r2-s2-renderer-check
```

生成 4×13/endtoend/dataset0 冒烟源码（**不自动编译链接或启动 EMU**）：

```bash
python3 -B team/optimizations/o2/r2-safe-tail/candidate.py \
  --repo "$PWD" --variant s2 --dataset 0 --shard 7 --suite smoke \
  --output /absolute/new/r2-s2-smoke-data
```

改成 `--variant s0` 生成原软件对照。shard 4/5 是 16×64 core/endtoend，6/7 是 4×13 core/endtoend。不要调用旧 O3 `build.py` 后误以为它会选 S2；它仍使用原生成器。本轮不修改旧构建、检查或 campaign 入口。

## 6. 下一关：真实小规模 B0/H1 验证

当前环境有 Clang/LLVM，没有项目 B0/H1 EMU、NEMU 配套库、nexus-am 或原 WSL 构建目录；连接器检索也未提供可用的远端终端。本轮因此没有启动实际 EMU，不生成虚假的完成回执。

下一次应在匹配环境里编译链接新的 S0/S2 ELF，建立新输入 manifest 与候选感知的严格生成/ELF 校验入口。不能通过删除/放宽旧校验、沿用旧 S0 散列、禁用 DiffTest 或只找 PASS 字符串来接受新镜像。原 C 数学/CSR/寄存器/哨兵检查和 O2 事务门禁继续保留。

先做 4×13 冒烟，再补三数据集、两口径和 16×64 不变对照。B0/H1 两个硬件执行完全相同的新 ELF/数据；硬件身份分别按既有 B0/H1 pins 核对，不重建或切换默认 RTL。性能沿用 first/warmup/四轮正反顺序，三个数据集组成每单元格 12 个正式样本；与合格 RVV 中较快者比较。未实际执行前全部标记 pending。

S1 仅完成分配/对等方案审查，见 `S1_REGISTER_REVIEW.md`，没有实施 S1 内核或声称取得 S1 跑分。R4 独立复现、R5 最终采用不由本轮主机测试代替。
