# core-02/control 完成后的独立观察复核

已使用冻结 e2d9c06 检查器，直接复核这次已结束 control 的完整原始 stdout+stderr，require_complete=True。真实返回码和结果见 review.exit-code.txt / review-result.json；源流 SHA 与正式 result.json 相同。没有修改工具或原日志，没有运行或重启 EMU。运行中只作内存前缀检查，本目录一次性保存结束后的完整证据。

正式结果 O2_CONTROL_LEGACY_PASS / O2_TRACE_PASS。2254次接受=2249次响应+5次槽级取消；2157次提交。最终 pending=0、未终结 ROB=0。

六项新覆盖实测如下：双槽同时占用284次、响应/移动/接受三事件同拍57次、满槽反压13次、P槽取消3次、R槽取消2次、双槽部分取消0次。五项已命中，partial_kill 未命中。其余实测包括64个STALL、933个DIV接受、881个DIV响应、52个DIV逻辑取消、5403个父级WAIT。没有从outready或这些计数推断哪一个写回单元赢得仲裁。

五次槽级取消发生当拍 occupancy 均为1；已逐笔核对接收身份、P/R移动、ROB前一拍redirect、实际父级flush、本拍取消，以及随后没有该事务响应或正常提交。没有双槽部分取消，因此不存在可报告的 partial 幸存者生命周期。不能把单槽KILL、BOTH_KILL或已响应后ROB取消转换成partial覆盖。

first-coverage-examples.json 保存五种命中事件的首个全局周期及前后拍；all-five-slot-kills.json 保存全部取消链；raw-event-excerpts.txt 保留原始行号。完整独立分析为 independent-analysis.json。最终 G3 六项覆盖仍需与其他已验证作业联合判定，本目录不代替整体 G3 验收。
