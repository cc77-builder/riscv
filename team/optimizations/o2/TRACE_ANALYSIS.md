# O2 可行性：T14/O1 旧轨迹离线分析

2026-10-18完成旧轨迹分析，2026-10-19续接任务并核对工具身份、主机测试和结果。状态为 O2_OFFLINE_TRACE_FEASIBILITY_PASS；这是已封存O1/T14记录的再分析，没有新EMU运行或O2性能结果。

最终结果以 [with-allocation-fate/trace-result.json](evidence/20261018-feasibility/with-allocation-fate/trace-result.json) 为准，SHA256为 42d927532ac25cd92cd89a2262503eac01256cdd20ce35c72019635d581dd8d6。分析工具为 [analyze_trace.py](analyze_trace.py)，SHA256为 e8de7d95f72383f53cc7d2bc048f4bece5240ceb8d5215f1393d1f82bbe6e2e1。

## 输入与选择

- 固定来源：[O1公平性能密封归档](../o1/evidence/20261018-performance-ab/README.md)，manifest SHA256为 fceea6ba616cc513d76c019d60bab061fb89d5fef00a7b61619084625aee9354。
- 读取123份归档文件，逐份核对存储字节、解压后的原始字节及SHA256；复用已完成的DiffTest/窗口验收，并用密封版本的O1观察检查器重新解析每个完整日志，结果必须与原observation逐项一致。
- 选择24个原有性能作业：两种模式×四场景×三个数据集；每作业四个正式custom窗口，共96个。首次、预热、RVV及额外确定性重放不计入本次等待统计。原公平对比的192个正式性能窗口包含custom与RVV，不能把96与192混为一谈。
- 计时区间为半开区间 [sample_ticks[1], sample_ticks[2])，使用已校准的未门控全局周期，同时核对CSR读值差。没有使用FU门控局部时钟。
- 已接受事务通过父级seq及ROB分配代次绑定；WAIT没有seq，故按ROB与ENQUEUE代次追踪到后续ACCEPT、COMMIT或REDIRECT，防止ROB复用把旧投机等待误归给新请求。

所有选中窗口的接受、响应、提交数均与程序预定点积数一致；已接受事务全部在本窗口完成并提交。跨边界、缺失提交、恰好落在计时边界的事件计数均为0。

## batch的关键观察

下表每格汇总12个正式custom窗口，每窗口128次vdot：

| 观察量 | T14 | O1 |
| --- | ---: | ---: |
| 窗口平均cycles | 453.25 | 362.50 |
| ACCEPT／RESPONSE／COMMIT | 各1536 | 各1536 |
| VFEX4输入有效但未ready，且busy=1 | 3036 | 1275 |
| 上述WAIT最终绑定同窗口正常接受并提交 | 3036 | 1266 |
| 上述WAIT在被接受前取消 | 0 | 9 |
| WAIT最终归属未知、未解决或跨窗口 | 0 | 0 |
| 输出STALL／已接受vdot KILL | 0／0 | 0／0 |
| 同拍旧响应与新接受HANDOFF | 0 | 1467 |
| 首次到末次接受平均跨度 | 381 | 288.75 |

WAIT按周期记录，同一个请求可能等待多拍，并不代表表中有1266条不同的请求。O1中正常提交请求对应的WAIT平均为105.5次/窗口；这只能证明在现有执行过程中有有效需求受到入口限制，不能从362.50中减去105.5并作为O2预测。

每个窗口有127个相邻接受间隔，总计1524个。T14全部为3拍；O1为2拍1467次、3拍3次、4拍6次、9拍15次、11拍33次。2拍占96.26%，说明O1的接收改动实际生效，同时仍有更长间隔。

ENQUEUE比正式接受数多：T14为1548（多12），O1为1581（多45）。这些额外分配不能计为有用点积。增强版WAIT分代追踪已把其中造成等待的取消前投机活动与有用请求区分。

## 其他场景与解释边界

- single：每窗口仅一条vdot，响应延迟2拍，无相邻接受间隔，未记录入口WAIT。
- chain256：3060个相邻接受间隔全部7拍，未记录入口WAIT；单条响应仍为2拍。这说明当前依赖链不能仅靠放宽独立请求接收来保证提速，尚未从日志精确归因唤醒、发射或其他等待。
- stream64：两模式接受间隔均为16拍744次、17拍3次、18拍3次、21拍6次，未记录入口WAIT；不能因此断言缓存/带宽就是瓶颈。
- 96个选中custom窗口均无vdot输出STALL或在途KILL，但存在程序其他分支的REDIRECT；“无vdot取消”不等于整个窗口没有重定向。
- busy只是父级状态，WAIT可与运算、输出或其他级活动重叠。T14有1524次WAIT与响应同周期，O1为3次；这类重叠统计不能相加成互斥周期预算。
- 当前观察器没有完整上游issue队列需求、仲裁授权及全部供数状态。没有ACCEPT/WAIT的周期不能自动标为上游饿死；有WAIT也不能证明II=1后这些周期全部消失。
- 这些数据支持有条件进入两槽原型，不能证明O2已达到目标，也不能承诺应用、频率、面积或功耗收益。

## 复现

在完整仓库根目录运行，Python 3.10及以上，无需EMU或硬件工具：

    python3 -B -m unittest discover -s team/optimizations/o2 -p 'test_*.py' -v
    python3 -B team/optimizations/o2/analyze_trace.py --output /一个不存在的新目录/o2-trace-review

分析器默认从仓库内密封归档读取，不依赖原WSL绝对运行目录；可用 --archive 指定逐字节相同的归档目录。输出目录已存在会拒绝，避免覆盖历史证据。成功输出 O2_OFFLINE_TRACE_FEASIBILITY_PASS、24作业、96窗口、new_emu_executed=false。

[主机测试回执](evidence/20261018-feasibility/host-01/verification.json)记录18项通过，覆盖窗口边界、CSR差值、同拍身份、重复等待、ROB复用、投机取消/环绕、跨窗口归属、归档破坏与缺失样本。测试工具和分析器源快照同时保存。

## 版本记录

初版 [trace-result.json](evidence/20261018-feasibility/trace-result.json) 只统计等待总数，保留其原始字节与工具SHA；它尚未细分分配最终归属，不作为当前归因结论。中断前已在新目录生成with-allocation-fate增强版，未覆盖初版。当前保存的工具源对应增强版，其快照位于host-01；初版工具没有单独源快照，不能声称可用当前源逐字重生成初版全部元数据。
