# O4最终合格集合与精简证据

2026-10-20；本地保存，未push。4个映射、20个STA profile、140份路径报告及13项主机测试通过。
[工程评估记录](../../O4结构与时序评估.md) · [复现命令](../../RUNBOOK.md)

- FU：O1 o1-fu-02/o1-fu-map-02/o1-fu-sta-03；O2 o2-fu-01/o2-fu-map-01/o2-fu-sta-02。
- 真实VFEX4：O1 o1-parent-01/o1-parent-map-01/o1-parent-sta-08；O2 o2-parent-01/o2-parent-map-01/o2-parent-sta-01。
- source-roles.json区分基点、实际生成receipt、最终审计/文档工具版本；identity-audit.json与g4-hardware-pin.json绑定429项硬件/21236依赖及旧EMU。
- tools/保存版本、deb/executable/shared-library摘要和本地help；library/保存固定typical库、来源及许可证。
- 每项映射保存原始RTL、Yosys脚本/日志/单元图/网表及实际退出码；STA保存全部实际Tcl、日志、setup检查、完整路径和敏感性。
- 父级额外保存canonical标准单元网表、Yosys重读图、实例绑定和完整驱动/时钟/常量/参数/输出位拓扑摘要。
- 127个父级无起点告警仅有124个0/1常量输出和3个已证明直连testEnable=0的SE测试端点；E端setup仍被检查，动态未约束例外为0。

manifest.json列出files/里每份文件的原始与保存形式SHA/字节数。大于256KiB的文件确定性gzip保存；
recheck.py在临时目录逐份核验/恢复，重算所有选定测量结果，不调用综合/STA/EMU。
原始工作根/home/riscv/riscv-lab/o4-cost-20261020保留全部尝试，禁止覆盖旧文件。

external-artifacts.json列出未重复纳入Git的失败尝试大型可重建中间产物（位置、大小和SHA）。
失败命令/日志/退出码、attempt-history.json和重建输入身份仍在精简包中；这些失败产物不参与最终验收。
原始工具安装目录、deb二进制、构建缓存和EMU不入包。

Linux与Windows原生离线复核回执放delivery/，在封存后生成，独立于测量manifest。
“审计通过”表示测量/连接/约束/统计一致，两版并未满足1ns参考setup目标。
这是Nangate45典型库/理想时钟/经验wire-load下的前布局比较，没有整核Fmax、实际功耗或版图面积结论。
O5/T17、最终G5、成员ACK及正式T16继续后置，本轮不自动执行。
