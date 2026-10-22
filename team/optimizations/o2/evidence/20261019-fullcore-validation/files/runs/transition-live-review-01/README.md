# 修复后 VFEX4 转换用例的真实接受顺序复核

结论：O2_TRANSITION_LIVE_REVIEW_PASS。新 diagnostic-build-03 的完整运行已结束，原始退出码为 0；使用本轮封存的分析器和检查器从完整 stdout/stderr 重新验证通过，并独立统计真实 VFEX4_ACCEPT 顺序。没有启动 EMU，没有修改冻结工具。

实际转换段为 seq1152…1169，共18次接受；VDOT、VIDiv、VFDiv 各6次。按真实接受顺序得到的17个相邻边覆盖全部9种有序类型组合。该结论来自动态事件，而非只读取汇编排列。

## 身份与完整通过证据

- 作业：/home/riscv/riscv-lab/o2-fullcore-20261019/supplements-02/o2-diagnostic
- 硬件源码提交：b218cbc6e6b135e4ff219a902a9284a59d3c82c9
- 工作负载源码提交：237f6a7d4158bd4f6ff83f092dfbd2a00124590f
- 检查工具提交：079351c122e35b77c1a0e01a6c3b60d562eac1cd
- 新镜像 SHA256：56915e3aaca02e02597c207de07ac18352ab53b6d06c4cb92a18fcddea1da4d4
- generate.py SHA256：8e10962413890a2715066a3c244c8059499f01a2e3b413fde2e08bdd2ce10f94
- main.c SHA256：a9e512ab496a136a5ba152684ca2627681af0b8268d32846c36a385eef17f733
- stderr SHA256：9c69ec88a805d55858523e9e152f863be5e508666c9874f524d553b1f96cd1f7
- stdout SHA256：0687dc5f0f0b31e2d345ebe7ca82cb00bb5be1d1f2529e41efba0c9ddc93c940

核对了 raw rc、原始流 SHA、run.log 的逐字节拼接、实际 EMU/参考库/flash/镜像身份、原 build receipt 的全部源码/生成物/镜像/AM 库 SHA。构建源码与工具源码均逐项绑定其记录提交的 Git blob。实际18条指令字还与 ELF LOAD 字节和 raw bin 对照。

全程序重新计算得到1158次 VDOT 接受、响应及提交，12次 DIV 正常完成，DIV取消0；VDOT、DIV、ROB均已排空。第十病例精确输出：

    O2_DIAG_CASE_PASS seq=9 id=vfex4-all-pairs dots=6 register_bytes=512 csr_fields=7
    O2_DIAG_SUMMARY cases=10 dots=1158 failures=0

该病例软件检查全部32×128位向量寄存器及7项CSR，检查逻辑与黄金值由绑定的源码/manifest确认。全部10病例完整通过，共5120寄存器字节；这些是软件检查与DiffTest证据，不声称每个CSR值都单独打印在O2轨迹中。

## 动态顺序及身份

| seq | 接受周期 | 实际FU类型 | ROB | 直接观测的动态PC | 静态ELF PC / word | 响应周期 |
| --- | --- | --- | --- | --- | --- | --- |
| 1152 | 111680 | VDOT | 1:11 | 0x80002be8 | 0x80002be8 / 0x294080b | 111682 |
| 1153 | 111701 | VDOT | 1:15 | 0x80002bfc | 0x80002bfc / 0x294088b | 111703 |
| 1154 | 111722 | VDOT | 1:19 | 0x80002c10 | 0x80002c10 / 0x294090b | 111724 |
| 1155 | 111743 | VIDiv | 1:24 | 未记录 | 0x80002c24 / 0x82a5a9d7 | 111756 |
| 1156 | 111775 | VDOT | 1:29 | 0x80002c38 | 0x80002c38 / 0x294080b | 111777 |
| 1157 | 111796 | VFDiv | 1:33 | 未记录 | 0x80002c4c / 0x82c698d7 | 111804 |
| 1158 | 111823 | VIDiv | 1:38 | 未记录 | 0x80002c64 / 0x82a5a957 | 111836 |
| 1159 | 111855 | VDOT | 1:42 | 0x80002c78 | 0x80002c78 / 0x294098b | 111857 |
| 1160 | 111876 | VIDiv | 1:46 | 未记录 | 0x80002c8c / 0x82a5a857 | 111889 |
| 1161 | 111908 | VIDiv | 0:2 | 未记录 | 0x80002ca0 / 0x82a5a8d7 | 111921 |
| 1162 | 111940 | VIDiv | 0:6 | 未记录 | 0x80002cb4 / 0x82a5a957 | 111953 |
| 1163 | 111972 | VFDiv | 0:11 | 未记录 | 0x80002cc8 / 0x82c699d7 | 111980 |
| 1164 | 111999 | VFDiv | 0:16 | 未记录 | 0x80002ce0 / 0x82c69857 | 112007 |
| 1165 | 112026 | VDOT | 0:21 | 0x80002cf8 | 0x80002cf8 / 0x294088b | 112028 |
| 1166 | 112047 | VFDiv | 0:25 | 未记录 | 0x80002d0c / 0x82c69957 | 112055 |
| 1167 | 112074 | VIDiv | 0:31 | 未记录 | 0x80002d24 / 0x82a5a9d7 | 112087 |
| 1168 | 112106 | VFDiv | 0:36 | 未记录 | 0x80002d38 / 0x82c69857 | 112114 |
| 1169 | 112133 | VFDiv | 0:41 | 未记录 | 0x80002d50 / 0x82c698d7 | 112141 |

六条VDOT使用ENQUEUE的PC/word和ACCEPT、RESPONSE、COMMIT直接关联，全部VL8、illegal=0，完整128位结果重新计算一致。12条DIV使用真实父/子接受及正常输出的fu/seq/rob/pdest绑定，均唯一正常完成。

**动态DIV PC限制：** 现有DIV事件没有PC/word，且本诊断未开启T13退休窗口（T13_RETIRE共0条）。因此表中的DIV静态PC仅是二进制顺序及类型对应，不能当作逐条动态PC直接观测。九种相邻类型覆盖仍由实际VFEX4接受顺序独立成立，不依赖这个静态对应假设。

## 真实相邻类型组合

| 组合 | 实际相邻出现次数 |
| --- | --- |
| VDOT->VDOT | 2 |
| VDOT->VFDiv | 2 |
| VDOT->VIDiv | 2 |
| VFDiv->VDOT | 1 |
| VFDiv->VFDiv | 2 |
| VFDiv->VIDiv | 2 |
| VIDiv->VDOT | 2 |
| VIDiv->VFDiv | 2 |
| VIDiv->VIDiv | 2 |

## 固定工作量病例中的协议观察

仅统计各病例内部相邻VDOT接受，排除跨病例间隔。下面说明真实整核能出现1拍接受间隔和2拍响应，不等同于应用加速比或公平O1/O2性能结果。

| 病例 | 实际接受数 | 内部1拍接受间隔次数 | 2拍响应次数 |
| --- | --- | --- | --- |
| shared-input-1 | 128 | 123 | 128 |
| shared-input-2 | 128 | 123 | 128 |
| shared-input-4 | 128 | 124 | 128 |
| distinct-input-1 | 128 | 122 | 128 |
| distinct-input-2 | 128 | 121 | 128 |
| distinct-input-4 | 128 | 122 | 128 |
| recurrence-1 | 128 | 0 | 128 |
| recurrence-2 | 128 | 64 | 128 |
| recurrence-4 | 128 | 94 | 128 |

review.json 保存完整事件绑定、直方图和SHA。review.py 为本次只读复核脚本；它只重算已有完整日志，不执行仿真器。失败旧批次仍保留，本审计仅声明修复后新诊断的结果，不替代整套G3合并验收。
