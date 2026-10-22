# 补充控制程序首次双槽部分取消：完整幸存者链

这是唯一中期快照，完整作业尚需最终验收。原 stdout/stderr 只读复制，冻结 e2d9c06 检查器对完整周期前缀执行 require_complete=False；去除了最新周期全部事件和UART不完整末行，没有替换记录。源 SHA、截取边界、实际命令/返回码保存在 diagnostic.json。

真实 partial 发生于全局 cycle609217，两个槽同时有效：

| 槽 | seq / ROB / pdest | 该拍行为 |
|---|---|---|
| P | 1741 / 1:2 / 49 | killP=1，被取消，无MOVE/RESPONSE/正常COMMIT |
| R | 1740 / 0:41 / 14 | killR=0，outvalid=outready=1，该拍正常RESPONSE |

ROB 在609216发出 0:43/self0 的redirect，父级在609217接收同一redirect；ROB环绕年龄判定使P年轻而被取消，R较老而保留。父级flush禁止当拍新接受，P不移动。此事件符合 occupancy=2 且 killP!=killR，不是BOTH_KILL，也不是单槽取消。

幸存R完整链：ENQUEUE609191 → ACCEPT609215 → MOVE609216 → RESPONSE609217 → COMMIT609283，PC0x80002978/FTQ1:2不变。完整源值独立按低8个有符号字节重新计算，完整128位返回 000000000000000000000000ffffe421；高96位为0，seq/ROB/pdest/vpu/perf保持一致。下一拍609218双槽均空，因为R同拍成功响应，并非在flush后被丢弃。

完整原字段和两条生命周期见 survivor-check.json；原始行号见 raw-event-excerpts.txt。部分审计已命中 P_KILL_R_SURVIVES，仍不把本目录提升为整个补充作业或G3通过，也不据outready推断其他写回单元的仲裁行为。
