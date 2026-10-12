# vdot 组合算术单元与 RTL 验证（T07-A）

2026-10-12 已实现并验证合同 `vdot-s8x8-r32-v0.1` 的组合算术：每源低 8 个 signed int8 相乘求和，结果符号扩展到低 32 位，高 96 位清零。**22 组定向和 10,000 组随机数据均通过完整 128 位比较。** [验证证据](../../evidence/rtl-datapath-20261012/README.md)保存命令、工具版本、源文件摘要与结果。

这是 T07 的算术部分。模块没有时钟、ready/valid、ROB/目的寄存器、flush 或配置检查，尚未接入香山执行单元或 NEMU；其组合正确性不能代表指令已在 CPU 上运行，也不能推导指令周期或频率。

## 1. 一键复现

在已有依赖和工具的完整香山仓库中运行：

```bash
git switch zjhwork
bash team/scripts/check-vdot-datapath.sh
```

脚本可从其他目录通过绝对路径调用。依赖安装见[环境说明](../../docs/environment.md)。独立 Mill 目标仍使用仓库根 `build.sc`，首次读取构建定义需要现有子模块；不能仅复制 `team/` 后当成独立工程运行。

采用项目固定 Scala 2.13.15、Chisel/插件 6.6.0，生成 RTL 使用 firtool 1.62.1，仿真使用 Verilator 5.052。JDK 默认 `/opt/graalvm-jdk-21`；firtool 默认 `$HOME/.cache/llvm-firtool/1.62.1/bin`，可通过 `JAVA_HOME`、`CHISEL_FIRTOOL_PATH` 指定已有匹配工具。当前 Verilator 的本地构建配置选择 clang++ 19.1.7；详细编译命令保存于构建日志。脚本记录 clang++ 与 g++ 版本，后者是原环境的配套编译器。

默认构建并行度为 2，独立生成进程 JVM 上限 2G，避免触发完整 SoC 编译。每次输出到被 Git 忽略的 `team/out/vdot-datapath/<时间-进程号>/`。如需指定位置：

```bash
VDOT_OUT_DIR="$PWD/team/out/vdot-datapath/my-run" \
  BUILD_JOBS=2 bash team/scripts/check-vdot-datapath.sh
```

指定目录的同名日志和生成文件会更新，保留历史时使用新目录。生成的 SV、C++、二进制和 TSV 不纳入 Git；只有精简证据需要人工归档。

脚本成功应同时出现：

```text
VDOT_DATAPATH_SUITE_PASS suite=directed count=22
VDOT_DATAPATH_SUITE_PASS suite=random count=10000
VDOT_DATAPATH_PASS directed=22 random=10000 total=10022
FAULT_DETECTION_PASS bit=0 expected_exit=1
FAULT_DETECTION_PASS bit=127 expected_exit=1
VDOT_DATAPATH_CHECK_PASS (combinational RTL only; no FU protocol/CPU/NEMU validation)
```

`check.status` 记录整体退出码；任一构建、输入校验、比较或预期故障拒绝失败时，脚本返回非零。

## 2. 模块与文件

生产源码：[VDotDatapath.scala](../../../src/main/scala/xiangshan/backend/fu/vector/VDotDatapath.scala)。三个模块均为无 Parameters 依赖的 Chisel `RawModule`，IO 是静态组合端口。

| 模块 | 输入 | 输出 | 作用 |
| --- | --- | --- | --- |
| `VDotProducts` | `io.vs1/vs2: UInt(128.W)` | `io.products: Vec(8, SInt(16.W))` | 每个低字节先转 signed8，再做精确乘法；忽略高 64 位 |
| `VDotReduce` | `io.products: Vec(8, SInt(16.W))` | `io.result: UInt(128.W)` | 用 `+&` 建立 16→17→18→19 位平衡树；和扩到 signed32 后拼高 96 位零 |
| `VDotDatapath` | `io.vs1/vs2: UInt(128.W)` | `io.result: UInt(128.W)` | 连接前两模块，作为本轮组合 RTL 验证顶层 |

范围端点为 `-130048` 和 `131072`；19 位有符号和覆盖两端。`-8` 的完整输出为 `0x000000000000000000000000fffffff8`。后续 FU 包装层可在两个子模块之间插乘积寄存器，不需要复制算术实现。

| 文件/入口 | 作用 |
| --- | --- |
| [仓库 build.sc](../../../build.sc) 的 `vdotDatapath` | 仅编译生产算术文件和生成入口，复用项目 Scala/Chisel 版本，无全核 moduleDeps |
| [GenerateVDot.scala](GenerateVDot.scala) | ChiselStage 生成三个真实模块的 SystemVerilog |
| [prepare_vectors.py](prepare_vectors.py) | 校验合同、schema、模型源码摘要、JSONL 摘要/数量/字段，原样导出 TSV |
| [datapath_test.cpp](datapath_test.cpp) | 输入和输出按 4 个低字在先的 uint32_t 访问 Verilator 128 位端口，逐例比较全部 128 位 |
| [check-vdot-datapath.sh](../../scripts/check-vdot-datapath.sh) | 校验、生成、编译、运行及比较器故障注入的一键入口 |

测试器只从已有 JSONL 取得期望结果，不再执行一套点积算法生成期望。输入/期望保持原十六进制位序；lane 0 为寄存器最低字节。输入文件非空、每行格式、重复 ID 和两组数量都有检查，避免少跑或空跑后仍报 PASS。

## 3. 测试内容与证据边界

- 22 组定向包含正/负/零、极值、单 lane 定位、源高半部干扰和负结果高 96 位清零。
- 10,000 组随机直接读取 T05 固定数据及 manifest，不重新生成、不改变种子或期望值。
- 每组给 DUT 赋两个 128 位源，调用 Verilator `eval()` 使组合逻辑求值，再比较四个输出字。没有时钟推进，因此不报告周期或吞吐。
- 比较器自检分别在第一组 D00 的实际读回结果翻转 bit 0 / bit 127；两次都必须产生 `VDOT_DATAPATH_MISMATCH` 且返回 1。它证明读回比较路径能检测低/高位错误，不是 RTL 故障覆盖率或 DiffTest 故障注入。
- 出错日志包含 suite、id、完整 vs1/vs2、expected/actual。数据/CLI 格式错误返回 2，正常结果不匹配返回 1。

组合输出本身没有“非法配置”概念：SEW/LMUL/VL/vstart/vill、寄存器别名的重命名行为、v0 物理路径和精确异常属于后续包装/接入层。当前不消费 `state.jsonl` 去假装这些性质已通过。

## 4. 下一步

按照 [RTL 接口设计](../../spec/rtl-interface.md) 实现 T07-B 的 `VDot` 包装层：快照源和身份，放置乘积/结果寄存器，实现单请求状态机、反压、`RobPtr.needFlush` 取消和异常响应。T07-B 单元通过后再做译码、VFEX4 接入及全核验证；本轮不提前改变 FU 配置或指令译码。

工作保存在 `zjhwork`；核心接口人工评审仍须由团队其他两位成员完成，自动检查与代码审查不代替人工签字。
