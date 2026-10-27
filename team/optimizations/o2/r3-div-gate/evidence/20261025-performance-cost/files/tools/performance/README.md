# DIV取消关钟修复前后周期检查

**36项实际EMU和原始日志复算通过；96对正式窗口周期完全一致，退化0；四次额外重放一致。**
完整478个校验窗口包括first/warmup和重放，正式统计为192窗组成96对。

- [实际结果](results/RESULT.md)
- [逐窗差值](results/paired-windows.csv)
- [全部样本](results/samples.csv)
- [复算回执](results/verification.json)
- [测量合同](CONTRACT.md)

本轮before为原O2/H1，after为O2/H1加DIV取消关钟修复；不是旧B0/H1实验。
同镜像微基准加速比：single 1.200704×、chain 2.929725×、batch 3.067873×、stream 1.004878×。
相对各自同镜像RVV，修复前后完全相同。没有GEMV、LLM或实测功耗结论。

本地原始根：/home/riscv/riscv-lab/o2-r3-div-gate-performance-20261025。
compare.py为只允许新输出的执行器；已完成campaign不可重复启动。
recheck.py是本轮正式离线复算/导出入口，读取原stdout/stderr与固定输入；
results.py保留启动时冻结的派生工具快照，其中旧模板文字不作为本轮报告入口。
新控制器按SHA及运行前快照冻结，原有检查器同时绑定Git blob。旧合同/结果未修改。
后续成本与STA见[成本入口](../cost/README.md)。未推送GitHub。
