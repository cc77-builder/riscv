# functional-1 完成后的非法 FU 语义复核

本目录补充最终时点的语义结论；04目录是更早的不可变部分快照。当时尚未出现非法 FU 请求，不能将那段时间限定说明当作最终覆盖结果。

原正式结果为 VDOT_MATRIX_SHARD_PASS / O2_TRACE_PASS。此次仅独立复核后两笔真实 illegal=1 请求，以及合法/非法写使能差异；没有重复别名审计，没有运行 EMU。原始日志只读复制，SHA 与正式 result.json 对齐。冻结解析器为 e2d9c06，独立复核脚本和真实返回码在本目录。

| 用例 | seq / ROB / pdest | ACCEPT → MOVE → RESPONSE | ROB self redirect → 父级 redirect |
|---|---|---|---|
| X09-v31，vd=vs1=vs2=31、vl=7 | 11 / 0:16 / 139 | 712191 → 712192 → 712193 | 712198 → 712199 |
| X10-3-0，vd=10、vs1=8、vs2=9、vl=7 | 12 / 0:34 / 124 | 741883 → 741884 → 741885 | 741896 → 741897 |

两笔在 ACCEPT 时都标记 illegal=1，同时保留输入目的写使能 vecwen=1、v0wen=0；MOVE 和 RESPONSE 均清除为 vecwen=0、v0wen=0，exception=0x4，即异常向量 illegalInstr 位2（架构 mcause=2）。完整128位返回数据为0，seq/ROB/pdest/vpu/perf 保持一致。合法11笔在 MOVE/RESPONSE 保持 vecwen=1、v0wen=0、exception=0。

两笔均先完成 FU 响应，再由 ROB 对自身 self=1 重定向；没有正常 COMMIT，没有 P/R KILL。因此 ACCEPTED_THEN_SQUASHED=2 表示这两条异常指令的 ROB 终结，不表示年轻错路指令取消，也不构成槽级 KILL 覆盖。原计数 ACCEPTED_YOUNGER_SQUASHED=0、KILL=0 与此相符。

本分片最终覆盖13次 ACCEPT/MOVE/RESPONSE、11次 COMMIT，其中2次真实非法 FU 请求。仍无v0请求、双槽同时占用、反压或槽级取消覆盖；这些不能从本分片推断。最终 G3 验收仍依赖整套核心和补充回归，不能由本语义复核替代。
