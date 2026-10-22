# functional-1 别名与异常路径的部分检查

状态：O2_PARTIAL_TRACE_AUDIT，检查器真实退出码 0。这是部分诊断，不是全分片、全核或 G3 验收。使用冻结 e2d9c06 Git blob，原日志只读复制；截取完整行后再次舍弃最新周期全部事件，避免半拍记录。没有修改运行工具/原日志，没有启动或重启作业。

实际已核对 L04-8-8-8：从 ENQUEUE 的机器码独立解码得到 vd=vs1=vs2=8，ACCEPT 源寄存器完整128位相同，MOVE/RESPONSE 保持 seq/ROB/pdest/vpu/perf；完整128位结果由检查器重新计算并匹配。详细原字段见 diagnostic.json 的 alias_transactions。本分片 manifest 操作数寄存器为 [8,9,10]，不含 v0，不能声称本次覆盖 v0 身份。

UART 已报告首个异常 X02-m2；其观察记录为 ENQUEUE cycle626722、ROB1:17，ROB REDIRECT cycle626734/self=1，父级 REDIRECT cycle626735；没有 FU ACCEPT。这是进入 FU 之前被异常路径处理的分配，不能把它计作 illegal=1 的 FU 请求/写使能测试。本快照实际 illegal FU ACCEPT 数 0。其他已观察异常分配也保存在 unaccepted_cancelled_allocations。

已接受的合法事务、ROB/FTQ flag 变化和重用均由冻结检查器在完整前缀中审计；真实计数、原始来源 SHA、命令和返回码见 diagnostic.json。完整 UART payload 的最终功能判定仍交由正式 runner 的原矩阵检查器处理，本目录不借部分 UART 宣称全分片通过。
