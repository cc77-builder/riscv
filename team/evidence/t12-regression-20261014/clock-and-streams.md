# 观察计数与输出流的处理依据

## 原始输出为何仍会交错

固定 DiffTest 的 `difftest/src/test/csrc/common/common.cpp` 在初始化阶段调用 `setbuf(stderr, mybuf)`。它发生在进程启动后，因此 `stdbuf -o0 -e0` 不能保持 stderr 无缓冲。Chisel 生成的观察代码通过 `$fwrite(32'h80000002, ...)` 写入 stderr；UART 写 stdout。把两者重定向到同一文件时，缓冲刷新边界可以从中间打断记录。该问题在真实 hello/vadd 日志重现，旧合流采集已排除。

最终采集分别保存 stdout.log 与 stderr.log，各自保留原始字节和摘要。run.log 是派生视图，严格等于 stderr.log + stdout.log，不声称保留两个流之间的墙钟交错顺序。程序 begin、结果、summary、GOOD TRAP 均按原 stdout 的顺序验收；硬件事件按原 stderr 内顺序及计数值验收。两份原始流都必须归档，不能只保留派生视图。

## FU 计数为何不等于全核周期

`ExeUnit.scala` 的现有时钟门控在 FU 空闲时关闭时钟。局部 GTimer 即使在 when 外创建，也只能计数实际送到 FU 的时钟沿。默认功能逻辑未改，不能为了日志简单而关闭门控或改变硬件时序。

同一源码中的 Dispatcher 使用组合 ready/valid 直连；VFEX4 的 vdot 接收与该 FU 接收同拍，rob 身份一致。对不确定延迟 FU，uncer_en_reg 在输入握手置位并在输出握手清零，在事务内部（包括反压和取消）时钟持续开启。因此可以逐笔使用父接收的全核周期作为时间原点，加上 FU 在本笔事务内的局部计数增量。

验收器要求父/子接收数量与身份逐笔一致、仅一笔未完成事务、事务时间不重叠、结果/反压不早于 E3、换算时间不越过原 stderr 中相邻全核事件。固定 FuType.vdot 为 bit35（0x800000000）；不从成功输出反推任意功能类型或时钟偏移。原始 FU 计数完全保留。此处理只适用于本次固定的单核 MinimalConfig 和源码，不用于其他未知时钟/复位配置。

新增合成反例检验缺父握手、错误父身份、门控空闲间隔、时间越界和全核时间倒序；合成检查不是 DUT 运行结果。前缀诊断同样不计作完整通过。
