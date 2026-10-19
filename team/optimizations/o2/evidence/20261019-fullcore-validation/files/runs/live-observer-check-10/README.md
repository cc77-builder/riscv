# 最终合格 supplements-02 的独立 partial witness

本目录直接读取并绑定 supplements-02/o2-control-diagnostic 最终原流，独立重算完整观察协议与部分取消幸存者链。未引用旧失败 campaign 的control作为最终运行证据。读取完毕后才创建本目录；没有中间快照、源代码修改或EMU执行。

本轮运行工具来源提交079351c122e35b77c1a0e01a6c3b60d562eac1cd，硬件仍为b218cbc。分析器从sup02实际归档tools复制，SHA与该campaign preflight一致；其字节也与之前e2d9c06语义分析器相同。新fatal门禁与修复后diag属于本轮工具/工作负载来源，preflight、campaign结果与job结果均随本目录保存。

当前原流SHA：
- stdout.log：561e729327cf9d49e2ffde3aea9cccc3b4fdbf62a7ee553d90b3857a8400fd9f
- stderr.log：c30b603f55afcda84be47887b9e3192015086a7e7ae3faa8591ece5a3c7ee4a1

sup02整体为O2_SUPPLEMENTS_PASS，control为O2_SUPPLEMENT_PASS / O2_CONTROL_DIAGNOSTIC_PASS / O2_TRACE_PASS。本次独立复核返回SUPPLEMENT_02_FINAL_PARTIAL_WITNESS_PASS，完整观察计数与该job正式结果一致，FU/DIV/ROB均无未完成事务。

唯一部分取消仍在cycle609217，但已基于本轮原流重新验证：
- ROB609216发出0:43/self0 redirect，父级609217收到同一边界。
- P槽seq1741/ROB1:2/pdest49被取消，无MOVE/RESPONSE/正常COMMIT。
- R槽seq1740/ROB0:41/pdest14保持有效，在同拍609217正常RESPONSE，609283正常COMMIT；PC0x80002978、FTQ1:2一致。
- R的ENQUEUE609191 → ACCEPT609215 → MOVE609216 → RESPONSE609217 → COMMIT609283，完整128位结果000000000000000000000000ffffe421与独立有符号点积计算一致。
- 当拍occupancy=2、killP=1/killR=0；下一拍两槽为空由P取消与R已响应共同解释，未丢失幸存事务。

最终本control：1208提交、MULTI984、TRIPLE744、FULL_STALL0、KILL_P28/KILL_R25、BOTH16、PARTIAL1。只报告本作业实际覆盖，满槽反压来自其他合格作业。整体G3结论以主任务独立joint recheck为准。survivor-check.json、complete-analysis.json和原始行号摘录可复核上述所有身份与时序。
