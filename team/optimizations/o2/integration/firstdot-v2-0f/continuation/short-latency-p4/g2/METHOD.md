# P4-G2 执行口径与覆盖审计

权威门槛为 [G0 CONTRACT 第4节](../g0/CONTRACT.md)。本页说明执行方式，不修改原门槛。

## 输入和构建

- 使用当前 G1 的445份源码，HEAD 10b71ad4bff25cd2070e775c74a4717b01602f75；只通过编译期环境变量 VDOT_P4_ONE_CYCLE=0/1 选择两拍0f行为和一拍候选。
- 两模式各新生成 CommonFuCostTop 与 CommonParentCostTop：完整生产接口，无测试观察口。父级为真实 VFEX4/ExeUnit、整数DIV、双浮点DIV/SQRT和三只真实门控。
- 两模式各重新综合并跑五档 STA。关闭开关生成逻辑与历史0f一致；只正规化断言Scala行号，以及无输出调试模块的JVM对象标识/三个打印语句排序。比较工具与原始差异保留。
- 旧成本锁21,707项复核仅VDotElastic.scala、VDotO2.scala是预期G1差异；其他21,705项匹配。另锁G1完整输入、当前源码、成本脚本、库、二进制及动态库。
- 默认开关仍关闭；没有修改生产RTL、NEMU、后端接口、旧合同或旧实验。

## 综合和约束

复用原 O4 的 elaborate.py、synthesize.py、timing.py，不修改它们。Yosys/ABC/OpenSTA和动态库按旧哈希；Nangate45 typical 25°C/1.1V。ABC 驱动BUF_X1、负载5fF、目标1000ps；三门控按原等价低相锁存器映射CLKGATETST_X1。

五档为 nominal(1ns/5fF)、period050(0.5ns/5fF)、period200(2ns/5fF)、load001(1ns/1fF)、load020(1ns/20fF)。共同使用原wireload、0.05ns时钟不确定度/转换时间、0.1ns输入/输出延迟、0.05ns输入转换；父级testEnable=0。没有加入false path、multicycle或删除端点。

## 防止新槽或直写路径漏测

1. 原FU五组、父级九组各五档，全部执行原脚本。
2. 在同一已映射网表上，增加全局max/setup、P/R数据D、P/R整槽D、真实源操作数到P/R数据D，共七组×两边界×五档。
3. 按映射前后Q-net真实别名绑定寄存器；精确分类pProducts/pResult、pCtrl/pPerf、rPacket_res_data/ctrl/perfDebugInfo与两个valid。所有物理VDot DFF都必须计入槽，两个槽不得被合并；控制/身份数量相对基线不变。
4. FU和父级补充查询使用无损canonical网表；逐cell类型、参数、连接图、IO和拓扑哈希复核。补充运行的旧组到达/裕量必须与原脚本六位小数逐值相等。
5. 原两拍基线没有“源操作数组合直达R”的路径，只有这一组允许明确No paths found（2边界×5档=10项）。候选两条源→P/R都必须存在，空报告即FAIL。
6. setup检查只允许已由网表证明的常量输出和case固定的ICG SE；任何新未约束非恒定端点、未知单元、锁存器或Tcl错误不得通过。
7. Q取完整报告最差setup裕量：Q=T−min(slack)。独立FU和父级都判门槛；35项控制/输出保护与两项面积单列，不能用父级大DIV路径隐藏局部退化。
8. 10项主机负向/边界检查验证超门槛、缺报告、Tcl错误及非恒定未约束端点被拒绝。它们是分析工具检查，不扩大为硬件验证。

## 失败保存

第一次补充分析 off-fu-coverage-01 因寄存器别名写成rPacket_data/rPacket_perf而被缺组断言拒绝，未执行STA。旧脚本、日志和失败状态原样保留。仅修正分析工具为生成网表实际的rPacket_res_data/rPacket_perfDebugInfo及父级真实源端口名；用新输出目录重跑，未修改RTL或放宽覆盖要求。

最终所有超限均保留。G2筛选不通过就NO-GO，不进入全核；候选1拍协议PASS不是应用速度或物理时序闭合。CLKBUF仅指库单元统计，不能据此声称已做CTS/功耗估计。
