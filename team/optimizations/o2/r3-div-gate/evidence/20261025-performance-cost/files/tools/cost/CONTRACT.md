# R3 DIV取消关钟：同约束面积与STA

2026-10-25，周期检查完成后执行。修复前使用已封存的原H1完整FU/父级综合与五档STA，修复后新生成、综合与STA；旧目录只读。
旧H1六个目录的完整载荷集合/字节逐项对照封存manifest；生产/构建/O4工具源码只有ExeUnit.scala不同。
相同Yosys/ABC/OpenSTA可执行文件与动态库、Nangate45 typical库、未修改O4脚本。
复用对照不是新运行；分别记录旧/新原始目录、时间和SHA。若任一旧输入不匹配则不能沿用。

边界为完整FU与真实VFEX4父级自由输入/完整输出，全部trace关，保留VIDiv/VFDiv和3个ICG。
同1000ps ABC目标、BUF_X1、5fF映射负载，STA nominal(1ns,5fF)、
period050(.5ns,5fF)、period200(2ns,5fF)、load001(1ns,1fF)、load020(1ns,20fF)。
0.05ns时钟uncertainty和transition，0.1ns输入/输出delay，0.05ns输入transition，
5K_hvratio_1_1线负载；parent testEnable=0；不额外false-path。
每版70类/档路径对照，覆盖r2r/i2r/r2o/i2o/ready、父级VDot子集及ICG使能。
新网表规范化必须通过逐bit拓扑绑定、未知单元/动态未约束端点拒收。

两版VDot存储都为32位，公开128位输出高96位清零；算术/控制/perf寄存器组不得随修复改变。
面积按Liberty单元之和；记录DFF、ICG及总单元数。流程有效、面积变化和时序收敛分开判定。
保留所有负slack及变差路径。本轮不包含整核面积、布局布线、CTS/SPEF、实测功耗或整核Fmax。
局部门禁证明减少空闲钟脉冲，不能换算成功耗百分比。全部本地，正式报告后置。
