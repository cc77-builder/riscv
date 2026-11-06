# P3校准运行器R1修订结果

**HOST_GO：冻结清单和触发快照修复通过，建议下一轮采用CPU4单核亲和重新做独立有界校准。**
本轮只做宿主机制验证，EMU/NEMU执行为0；真实拒错、正常QKV吞吐和7200秒预算仍未取得新资格。
生产保持0f＋firstdot V2＋原C8，镜像、RTL及全部预算不变，未上传GitHub。

## 1. 两项问题怎样修复

| 项目 | V1问题 | R1结果 |
| --- | --- | --- |
| 路径命名空间 | 通配导入覆盖HERE，枚举成父目录 | 使用pc_context.CAL_HERE；所有模块显式导入，无通配导入 |
| 本轮源闭包 | 6项源码/合同漏入预冻结 | 显式8项必需文件＋直接Python文件；父路径替换、缺项、漂移、额外源码和原V1错误freeze均拒绝 |
| 冻结时序 | 源清单不足 | **实际宿主测试前**写入4324项INPUT_FREEZE，包含运行器、合同、测试、宿主夹具/头文件/二进制及冻结对象；运行后复核原字节不变 |
| 触发记录 | 只有总数5，没有当次组成 | 触发判定使用的整组快照写入trigger.json并fsync，记录PID/PPID/PGID/SID、TID、出生ticks、comm/exe/cmdline、亲和及采样边界 |
| 清理及顺序 | 需要继续验证 | 首原因保留，整组回收；负控失败不进入正常阶段，最多两项，不重试 |
| 资源口径 | 整组4线程 | **仍为整组4线程**，shell/诊断辅助进程全部计入，未放宽为5或改成只统计EMU |

冻结文件：[evidence/INPUT_FREEZE.json](evidence/INPUT_FREEZE.json)，SHA256 0d06a4f8b40ca402b6f378ca4d7f21098bc25d857ac65f9be1aefcdb2eee834a。
本轮源集合为pc_context.py、bounded.py、calibrate.py、freeze.py、test_freeze.py、test_supervisor.py、host_fixture.cpp、CONTRACT.md。
prepared-target-descriptors仅提供候选命令，不能启动目标；宿主轮明确target_launch_authorized=false。
之后新增真正执行入口时，该入口也必须参与新的预冻结。

## 2. 宿主验证结果

**14组unittest全部通过，实际13个宿主进程用例，0个目标进程。**
本轮首次完整测试即通过；上轮冻结失败和目标中止记录全部保留。

- 8种一般进程机制：正常退出、墙钟、日志、RSS、线程、亲和、子进程及父进程先退后的回收。
- 1种控制器SIGTERM取消机制。
- 4次冻结运行时试验：四核基线、四核诊断、两次单核诊断。
- 冻结负控覆盖8项必需文件逐项遗漏、目录替换、源码/运行库/预算变化、父级pin漏项、旧错误freeze、禁止覆盖、无授权目标调用及失败即停。
- 触发证据负控覆盖线程总数、TID、出生标识和原因损坏，均拒绝。

宿主可执行文件只链接**原clean-02冻结构建的verilated.o、verilated_threads.o、spikedasm.o**，未链接生成的VSimTop或NEMU；没有运行EMU，也没有重建核。编译命令、对象哈希、符号检查和头文件身份留在host-build。
诊断占位程序仅在隔离的宿主PATH中延长存活时间，便于稳定采样；它不执行RISC-V指令，不能用作目标测试依赖。

## 3. 诊断子进程与4线程限制

| 宿主夹具配置 | 运行时线程数 | 实测整组峰值 | 结果 |
| --- | ---: | ---: | --- |
| CPU4–7，只有冻结运行时 | 4 | 4 | 正常结束 |
| CPU4–7，调用原spike_valid诊断路径 | 4 | 5 | THREAD_LIMIT，按原4线程门禁停止 |
| CPU4，诊断第1次 | 1 | 3 | exit0，0.971842秒 |
| CPU4，诊断第2次 | 1 | 3 | exit0，0.972371秒 |

四核诊断的触发快照明确捕获：运行时宿主PID422有4个TID，另有其子进程 **PID426 / sh / 1个TID**，合计5。PID及出生标识只描述本次宿主夹具，历史EMU那次没有完整触发明细，**不能追溯证明历史第5个就是同一种进程**。
证据：[trigger.json](evidence/host-tests/runtime4-diagnostic/trigger.json)。

固定VSimTop生成源码的threads()返回1；Verilator宿主运行时默认并行数依据可用CPU，宿主实验证明四核亲和会建立4个宿主线程。模型线程数与运行时池线程数必须分开记录。
把亲和收窄到CPU4后，同一批原始运行时对象建立1个宿主线程，为shell和诊断助手留下余量；两次夹具总峰值3。
这支持**无需改RTL、镜像或增加线程预算**的最小运行配置候选；并不证明真实NEMU差分已通过。

## 4. 保持的预算与资格

| 约束 | 当前值 |
| --- | --- |
| CPU允许范围 / 建议启动范围 | 4–7 / 仅4，属于原允许集合 |
| 整组OS线程上限 | 4，计入辅助进程 |
| bit100 / 正常 / 两项合计 | 300秒 / 2400秒 / 2700秒 |
| 每项guest上限 | 1000000；原生限额999984，预留退出统计16拍 |
| RSS / 原始日志合计 | 12GiB / 2GiB |
| 目标进程数 | 最多2串行；本轮实际0 |
| 正式探针 | 本轮禁止，不自动进入 |
| 新加速比 / 面积 / 时序 | NOT_TESTED / NOT_TESTED / NOT_TESTED |

/proc轮询不是原子快照或硬实时控制；每个进程保存采样起止和消失的TID，首触发证据对应作出判定的样本。保存和回收开销单列，不声称检测无延迟。状态机PASS、14组宿主PASS、单核夹具PASS各有范围，不能代替真实bit100拒错、完整CSR/O2/数值或公平周期测量。
7200秒预算仍HOLD：本轮没有产生正常QKV吞吐。

## 5. 身份、留档和下一步

HEAD 10b71ad4bff25cd2070e775c74a4717b01602f75，分支local/zjhwork-integration-20261024。固定ELF/BIN、0f EMU/NEMU和旧失败原样保留；4540项既有保护输入复核未变。
统一版本档案追加第46条HOST_TOOLS_ONLY，前45条及失败不覆盖；计分板和当前路线同步。
原始输出：/home/riscv/riscv-lab/software-import-20261026/p3-runner-revision-20261031-01。

下一轮指令见[NEXT_STEP.md](NEXT_STEP.md)。需要新执行合同和新运行目录；CPU4只是运行配置收窄，不能把本轮宿主结果补进上轮目标失败记录。
