# T12 全核控制回归

状态：实施与实测中，尚未验收。基线为 `6bf3c2c3be0c88ff3a020786ff10cbec9aa126d3`。本机使用独立本地分支 `local/t12-regression`，未取得或宣称共享分支推送窗口；本轮不向 main、zjhwork、James_Hotten 写入。

## 范围与完成标准

1. 原有数学模型、组合/FU/解码与全核合法/异常矩阵继续通过，保存各自验证层次。
2. 新程序四组各 512 条 vdot，覆盖 RAW/WAW/v0 别名、VL/CSR 紧邻更新、共享 VFEX4 混合操作和反复 ROB/FTQ 绕回。每组 32 个检查点，每个检查点核对全部 32×128 位向量寄存器；另核对 512 次 vcsr 读回。
3. 256 次延迟条件分支尝试，每次保存完整目的寄存器；硬件观察必须证明年轻指令真实发射并因重定向取消。源程序包含分支，不代表命中取消覆盖。
4. 观察 FU 接收/结果/反压/取消、ROB 分配/提交和共享执行单元等待。要求事务守恒、身份绑定、高 96 位为零、取消指令不提交、ROB/FTQ 多次绕回。
5. 写回反压、FU 内取消等未命中的项记为 `T12_COVERAGE_INCOMPLETE`。不得通过降低门槛或修改期望来消除缺口。
6. 完整保存真实退出码、原始日志、源版本与差异、二进制/参考库/flash/测试输入摘要。失败种子和运行保留，修复后使用新目录重跑。

本轮不涵盖委托/虚拟化、性能比较、综合、STA 或功耗；不能用于关闭 T13/PPA。

## 可观测性

生产 Scala 中的观察代码仅在生成硬件时设置 `VDOT_T12_TRACE=1` 才实例化。代码只读取真实握手、身份和重定向，不改变驱动信号、延迟或仲裁。测试采用真实 MinimalConfig/单核/48 项 ROB/8 项 FTQ，保持断言和 DiffTest。首次启用观察或仅切换环境开关时，必须使用新的硬件输出目录并保存启用参数，因为 Make 不一定把环境变量变化视为构建输入。不能把旧的无观察仿真器当成本轮覆盖证据。本轮修复计数器时先归档旧二进制、源码差异与日志，再由实际 Scala 变化触发完整 RTL 重生成和 C++ 重编，并记录新旧摘要。

硬件 printf 和 UART 使用不同输出路径。运行分别保存 `stdout.log`（UART/宿主消息）和 `stderr.log`（硬件 printf），禁止在采集时合流。`stdbuf` 无法保证加载的运行库不重置缓冲；合流尝试仍发生截断，已排除。`run.log` 仅为明确标注的派生视图，逐字节等于 stderr + stdout；归档保留并分别校验两份原始流。判定器拒绝残缺记录，并在原 stdout 顺序中核对 summary 与 GOOD TRAP。

ROB/VFEX4 的观察计数器每个全核周期递增；FU 使用现有门控时钟，空闲时不递增。依据 `ExeUnit.scala` 的组合 Dispatcher 连接，VFEX4 与选中 FU 的输入握手同拍；`uncer_en_reg` 在接收后保持时钟，直到结果握手（取消后亦不会提前关钟）。判定器将每条 FU 接收与父 VFEX4 的 vdot 接收按身份一一对应，使用事务内门控时钟增量换算全核时间，并检查其位于原 stderr 中相邻全核事件之间。缺父握手、身份错误、时间映射越界均拒绝。原始计数值不修改；不把门控计数直接当全核周期。分层 ResetGen 仍明确拒绝。合成反例只用于验证判定器，并非硬件运行证据。

## 本机运行

```bash
# 完整源码目录中，先激活团队工具环境。
source team/scripts/activate.sh
VDOT_T12_TRACE=1 make emu CONFIG=MinimalConfig NUM_CORES=1 EMU_THREADS=1 JVM_XMX=12G -j2

export T12_RUN_ROOT=/绝对路径/新的回归输出目录
bash team/scripts/t12-regression.sh build-workload
export T12_NEMU_ROOT=/绝对路径/已验证的vdot-reference检出
bash team/scripts/t12-regression.sh run
```

脚本拒绝覆盖已有构建/运行证据。退出码 2 表示覆盖缺口时，查看 result.json 的具体未命中项。构建/参考来源失败或程序结果错误则不产生通过结论。原 T05/T11 黄金数据保持原字节；T12 使用独立生成器和输出目录。

## 当前结果

本次主机单测已增加到 101 项并全部通过；原数学模型另 35 项及 5 文件一致性通过。组件层真实结果：组合 RTL 10022 组完整 128 位，FU 6 组/71258 周期，解码 RTL 131109 次事务。新全核运行仍在等待编译，不能把这些前置结果当作 T12 全核通过。

同一压力测试镜像已在独立 standalone NEMU 执行并以 exit0/GOOD TRAP 结束；其 UART 在该独立模式下不输出本程序的 summary，故仅记为 standalone 执行检查，不单独记作全核验收。

已知失败与中断均单列在 [证据目录](../evidence/t12-regression-20261014/README.md)，包括观察计数器/缓冲问题、密集序列负控 PC 对应失败、未记录完成退出的旧分片。最新可复核结果将在本轮实测结束后补齐。人工评审仍需另一名成员完成，观察点涉及核心文件的变更须按团队要求复核。

## 全套运行入口与来源

`team/scripts/run-t12-suite.py` 接收已经完成构建的 EMU、reference、控制镜像及 8 个功能分片，逐项检查来源并运行。使用 `--help` 查看全部路径参数；每次 `--output` 必须是不存在的新目录。该入口不代替构建，不覆盖旧日志，默认同时运行两个仿真进程，也支持 `--jobs 4`。本机 WSL 配置约 20 GiB 内存且有 6 个逻辑 CPU，重跑使用四进程；这仅改变宿主调度，不改变被测单核配置。

固定硬件输入记录包含顶层源码和实际使用的子模块文件摘要、MinimalConfig/单核/48 项 ROB/8 项 FTQ、`VDOT_T12_TRACE=1`、工具版本及构建参数。运行前后均核对 EMU、正常 reference、flash 和测试镜像摘要；正常参考库另经 `artifact_guard.py nemu-runtime` 验证补丁 1.1.0、NMIE/MDT/xTVAL 平台配置与编译来源。

8 个分片使用 T11 原生成器与原数据：`VDOT_LOG_COMPACT=1`、`VDOT_COVERAGE_PROFILE=legacy`、`VDOT_RANDOM_COUNT=32`、`VDOT_SMOKE_RANDOM_COUNT=32`、`VDOT_SHARD_COUNT=8` 和 `VDOT_SHARD_INDEX=0..7`，逐片采用新的绝对路径 `VDOT_DATA` / `TEAM_EVIDENCE_DIR` 执行 `bash team/scripts/vdot-tests.sh build-xs full`。AM 库构建有序进行；仿真可分片并行。新入口严格比较每个分片与原始母用例，确保 117 唯一项、124 实际项，额外 7 项仅为重复 D00 对照。

负控使用仓库既有 `team/evidence/t10-t11-fullcore-20261013/matrix/negative-fixture.c`，链接本轮验证过的正常 reference。它只在返回给 DiffTest 的状态副本翻转 bit100；验收要求对应 vdot 的 PC、目的寄存器、机器字和差分位完全匹配，随后同一 shard-0 镜像换回正常 reference 必须完整通过。

离线入口 `team/scripts/check-t12-archive.py` 用于重新核对归档字节、退出码、运行记录、完整 UART/事件日志、负控与恢复、分片并集。调用时显式传入已审阅的源码及 EMU/reference/flash 摘要。离线复核不是重新执行处理器，也不是密码学签名或人工评审。
