# O2 G3 全核工作负载清单

本文件描述 G3 输入与验收接口。新增程序已交叉编译并核验指令序列；运行结果以本轮新 O2 EMU 的原始日志和总验收文件为准。编译通过、源码包含密集请求或分支，都不能证明硬件覆盖已经触发。

## 1. 原有冻结输入

沿用 O1 全核脚本逐字节固定的 12 项作业：

| 作业 | 本机输入位置（共同前缀 /home/riscv/riscv-lab/） | 验收用途 |
| --- | --- | --- |
| hello/vadd | t12-regression-20261013/repo/team/workloads/hello-vadd/build/hello-vadd-riscv64-xs.bin | 环境和 RVV 回归，vdot 接受/提交为零 |
| 8 个功能/异常分片 | t12-regression-20261013/runs/t11-matrix-canonical/build-{0..7}/vdot-exceptions.bin | 117 个唯一用例、124 次实际执行；完整向量和异常状态 |
| 高位故障参考库 | 同一 build-0/vdot-exceptions.bin + t12-regression-20261013/build-evidence/negative-reference.so | 第 100 位参考结果故障须被 DiffTest 拒绝，随后正常库同镜像恢复 |
| 原 F2v 控制压力 | t14-optimization-20261015/runs/control-sweep-02/vdot-regression.bin | 保留原 7 项控制覆盖要求，不修改原程序或黄金数据 |
| dense batch128 | t13-performance-20261015/runs/images-v3/performance-d0-s06/vdot-perf.bin | 密集请求、原全状态及窗口自检，本轮不作公平性能结论 |

正常参考库：/home/riscv/riscv-lab/t12-regression-20261013/nemu/reference/build/riscv64-nemu-interpreter-so，SHA-256 efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4。故障库 SHA-256 为 9b3aecf362b7c7ddb4f8bace355c2e0ee2cc919fd5f59eefc641db220ab40df0，其链接的正常参考库绝对路径不能随意迁移。

完整镜像、flash、源码、数据和参考库身份继承冻结输入核验，本表不代替 SHA 校验。

## 2. O2-A3 固定工作量诊断

源文件为 workloads/generate.py、main.c，固定 seed=o2-g3-20261019-v1。每个算术诊断完整展开 128 条 vdot，没有循环、读 cycle/instret，也没有向量寄存器 spill。

| 名称 | 路数 | 运算安排 | 用途 |
| --- | --- | --- | --- |
| shared-input | 1 / 2 / 4 | 轮换 v16..v19 目的，所有请求读取相同 v8、v9 | 观察相同输入、不同目的在途行为 |
| distinct-input | 1 / 2 / 4 | 轮换目的，各路使用独立源对 | 与 shared-input 区分输入因素 |
| recurrence | 1 / 2 / 4 | 每路以上一次目的作为 vs1，vs2 固定 | 区分真实依赖延迟和独立吞吐 |

“路”表示软件独立目的/依赖链，不是扩展硬件 lane，也不改变 8 对 int8 语义。每个 case 初始化并检查全部 32 个 128 位寄存器（512 字节），同时检查 vtype/vl/vstart/vxrm/vxsat/vcsr/fflags 7 项控制状态。

第 10 个 case 包含 vdot、VIDiv、VFDiv 全部 9 种有序相邻类型组合，共 18 条运算，各类 6 条。读取前一结果、计算下一次 vsetvli 的 AVL 建立真实依赖，避免凭汇编排列假定实际切换顺序。VIDiv 使用四组无符号整数除法；VFDiv 使用可精确表示的有限值除法，预期 fflags=0。实际切换仍须由观察器确认。

精确 vdot 提交数 **1158**（9×128+6）。C 程序额外翻转目的第 127 位，要求自身检查器拒绝并还原；这是软件检查器负控，不是 RTL 故障注入。

当前构建：/home/riscv/riscv-lab/o2-fullcore-20261019/diagnostic-build-02/o2-diag.bin。
SHA-256：ed35725a24708fc7ffb4efb617248fe5e6911f18c803280a6e75be3f8ad6dfc7。

## 3. 新增取消与写回竞争诊断

源文件为 workloads/generate_control.py、control.c。冻结 F2v 镜像保持原样，该程序为新增 G3 输入。

- 16 组，每组同一条件分支执行 16 次，共 256 次确定性、不规则分支结果。
- 每次重新初始化全部 32 个寄存器；旧 VIDiv 和一条旧 vdot 位于分支前，8 条年轻 vdot 位于可取消路径。
- 分支条件依赖标量无符号除法；F2v 写回竞争 burst 从 1 到 16，分支后的普通整数指令间隔按 0..3 扫描。
- 每次保存、逐字节核验全部向量寄存器，总检查 **131072 字节**。检查最终向量 CSR 和浮点异常标志，停止必须排空。
- 精确架构 vdot 提交数 **1208**，由确定性分支数据与软件模型计算，不从 DUT 日志反推。

目标补充 FULL_STALL、KILL_P、KILL_R、PARTIAL_KILL 等实际事件。能否触发由全核轨迹决定；缺失须记为覆盖不足，不能用 GOOD TRAP、G1/G2 结果或另一类取消替代。它不掩盖冻结 F2v 原有 7 项覆盖的回退。

当前构建：/home/riscv/riscv-lab/o2-fullcore-20261019/control-diagnostic-build-04/o2-control.bin。
SHA-256：45cdf2a6cb6848b3bcb56d860c36bc26a975a8aa96bfe1411d33dce6036bd305。

构建 02/03 编译成功但符号审计失败，原记录保留；04 改用 nm 完整符号表后，全部 16 组的 9 条静态 custom 指令核验通过。这些构建尝试尚不是 EMU 执行记录。

## 4. 复现与严格验收

从完整 checkout 执行，输出为尚不存在的 checkout 外绝对目录：

    python3 -B -m unittest discover -s team/optimizations/o2/fullcore/workloads -p 'test_*.py' -v
    python3 -B team/optimizations/o2/fullcore/workloads/build.py --output /absolute/new/diagnostic
    python3 -B team/optimizations/o2/fullcore/workloads/build.py --kind control --output /absolute/new/control

使用 activate.sh 配套工具，ARCH=riscv64-xs MARCH=rv64gcv -j2，禁用 C 自动向量化。先复制源码再编译；build.json 记录源码副本、生成数据、ELF/反汇编/bin、nexus-am 库、工具链和编译指令审计。后续源编辑不会追改已构建镜像。

workloads/check.py 的 API：

- verify_build(build)：核验构建状态及源码、数据、镜像、AM 库 SHA，返回 manifest。
- check(uart, manifest, exit_code, analysis)：固定工作量诊断，成功值 O2_DIAGNOSTIC_PASS。
- check_control(uart, manifest, exit_code, analysis)：新增控制诊断，成功值 O2_CONTROL_DIAGNOSTIC_PASS。

两者都要求退出码 0、唯一有序的完整 UART 标记、最终 GOOD TRAP、O2_TRACE_PASS、精确提交数、无未终结 FU/ROB 请求。总运行门禁负责真实 DiffTest banner、正确参考库、原始失败文本及新覆盖；UART 检查器不替代这些门禁。

观察器仅把以下 9 个精确标签归入 UART，其他未知 O2_* 仍拒绝：

O2_DIAG_BEGIN、O2_DIAG_CHECKER_CONTROL、O2_DIAG_CASE_PASS、O2_DIAG_SUMMARY、O2_DIAG_FAIL、O2_CONTROL_BEGIN、O2_CONTROL_GROUP_PASS、O2_CONTROL_SUMMARY、O2_CONTROL_FAIL。

本轮诊断不设性能阈值、不据单次周期作采用判断、不修改冻结 16 镜像。G4 须另行冻结 O1/O2 相同镜像与配置后公平比较。

## 5. 构建后的检查器修正

冻结两份 bin 与源副本之后，运行检查器单独加强了 UART 行边界与顺序验证，并将控制诊断的 CRLF 处理改为真实换行转换。新增 CRLF、标记后缀、检查器负控标记顺序的主机反例测试。这不修改程序语义或镜像；运行门禁另存当前检查器的源码 SHA 和 Git 提交，不能把构建副本中的旧 check.py 当作实际运行检查器。
