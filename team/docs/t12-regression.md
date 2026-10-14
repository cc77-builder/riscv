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

生产 Scala 中的观察代码仅在生成硬件时设置 `VDOT_T12_TRACE=1` 才实例化。代码只读取真实握手、身份和重定向，不改变驱动信号、延迟或仲裁。测试采用真实 MinimalConfig/单核/48 项 ROB/8 项 FTQ，保持断言和 DiffTest。构建必须使用新输出目录并保存启用参数；不可把旧的无观察仿真器当成本轮覆盖证据。

硬件 printf 和 UART 使用不同输出路径。运行必须使用 `stdbuf -o0 -e0`，防止缓存导致观察记录被从中间截断；判定器只剥离字段完整的观察记录，残缺记录直接拒绝，再检查 UART 的完整 summary 和 GOOD TRAP。观察计数器在 Chisel `when` 外创建，每拍递增；本观察配置拒绝启用分层 ResetGen，以保持模块间统一时间原点。合成反例只用于验证判定器，并非硬件运行证据。

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

待实际 RTL 运行后填写。前置主机检查通过不能代替此处结果。人工评审仍需另一名成员完成，观察点涉及核心文件的变更须按团队要求复核。
