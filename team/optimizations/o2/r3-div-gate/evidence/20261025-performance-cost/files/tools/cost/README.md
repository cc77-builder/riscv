# DIV取消关钟修复：同约束成本与STA

**两份新映射、十组新STA和完整原文审计已完成。**
完整FU面积及五档时序不变；父级面积284879.882→284614.946μm²（−0.092999%），
映射DFF17171→17172、ICG仍3个。额外DFF回溯到既有整数DIV余数寄存器位，
VDot的算术、结果/控制/perf寄存器分组不变。

父级nominal r2r到达时间增加94.304ps、i2r增加119.132ps、gate_enable增加32.965ps；
ready减少47.603ps。两版均未达到此参考流程的1ns目标。面积/周期/时序结论分别保留。

- [总结果和取舍](../PERFORMANCE_COST_RESULT.md)
- [成本结果](results/RESULT.md)
- [全部70条时序对照](results/timing.csv)
- [完整审计JSON](results/summary.json)
- [合同](CONTRACT.md)

修复前复用完整封存H1并逐字节核验，修复后本轮实际运行；不是两版均重新运行。
原始工作根：/home/riscv/riscv-lab/o2-r3-div-gate-cost-20261025。
run_after_performance.py已完成，不可重复启动同一输出。
compare.py只读复算；review_paths.py/review_dffs.py分别回溯最差路径和映射寄存器差异。
所有失败、命令和原始路径保留。未测整核PPA/Fmax/功耗，未推送GitHub。
