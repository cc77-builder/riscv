# supplements-01 控制补充程序最终观察审计与 partial witness

这是本轮唯一最终证据目录。只读复制已结束的完整原流，冻结 e2d9c06 分析器执行 require_complete=True；原流 SHA 对齐正式 result.json。没有修改任何冻结工具、原始日志或运行作业，没有启动 EMU。08为此前唯一中期快照，本目录完成后不再持续写快照。

该控制程序正式 O2_SUPPLEMENT_PASS / O2_CONTROL_DIAGNOSTIC_PASS / O2_TRACE_PASS；16组256次试验，检查131072字节，1208条vdot正常提交。独立复核返回 FINAL_PARTIAL_KILL_SURVIVOR_CHECK_PASS，最终FU/DIV/ROB未完成计数均0。

最终观察：1643 ACCEPT、1615 MOVE、1590 RESPONSE、53 KILL（P28/R25），256 DIV接受并响应；984次双槽占用、744次三事件同拍、0次满槽反压、16次双槽同时取消、1次双槽部分取消。FULL_STALL=0不因其他事件改写；整个G3的该项应由其余已验证作业提供。

唯一 PARTIAL_KILL 位于cycle609217，P_KILL_R_SURVIVES=1：
- ROB前一拍609216发出0:43/self0 redirect，父级609217收到同一边界。
- P槽seq1741/ROB1:2/pdest49为年轻事务，被取消，无MOVE/RESPONSE/正常COMMIT。
- R槽seq1740/ROB0:41/pdest14较老，正常幸存并在609217同拍响应；609283正常COMMIT，PC0x80002978、FTQ1:2匹配。
- R完整链609191入ROB→609215接受→609216移动→609217响应→609283提交；源数据独立重算的128位结果000000000000000000000000ffffe421，控制与perf身份保持一致。
- 609218双槽空，原因是P取消、R已经响应，不是R丢失。记录严格满足occupancy=2且killP!=killR，未将BOTH_KILL或单槽取消冒充partial。

完整链和原始行号见 survivor-check.json / raw-event-excerpts.txt；完整最终分析见 complete-analysis.json。这里只确认 supplements-01 的 control 单项与观察语义，不宣称首轮整个 supplements 或联合G3通过，也不推断写回仲裁赢家或性能收益。主任务将独立处理诊断程序的软件修复及新轮联合验收，原数据继续保留。
