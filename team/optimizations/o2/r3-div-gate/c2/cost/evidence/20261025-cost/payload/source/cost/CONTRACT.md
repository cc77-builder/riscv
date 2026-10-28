# C2 成本筛选及条件后继合同

2026-10-25。用户本轮明确授权：先做同约束综合与五档STA，全部通过后再进入全核与周期验证；沿用未上传GitHub的安排。本文件扩展前轮C2局部合同的执行范围，不改写其已封存边界和任何筛选阈值。

固定候选6704ce3502a7235cdb81697638c01ed23f6914f6，ExeUnit SHA256 febbce48c4865ac5e1c7909f8494599a01ae2fee643ee53396635a0f403323a6；基线0f12df675378556670afd0dd2153f47fcb330610。生产RTL不改，当前保留基线、被否决C1与已完成局部验证保持。新输出独立于旧输出。

## 固定输入和边界

- 新生成完整生产CommonParentCostTop（真实VFEX4，O2、融合输入开启，O1关闭，所有trace关闭），不使用补充测试顶层/新增层级观察。
- 复用O4的固定elaborate/synthesize/timing入口、Yosys0.9/ABC1.01/OpenSTA2.0.17及其已记录共享库；Nangate45 typical 25°C/1.1V库SHA 8d540a4d4cf6d09d27c87ad067857a9c0c2eeb023ab7a56e058cd3113db4e9b1。
- ABC -D1000ps，BUF_X1驱动、5fF负载；STA ideal clock，5K wire-load，clock uncertainty/transition均0.05ns，IO delay0.1ns，parent TE=0。
- 五档：(1ns,5fF)、(0.5ns,5fF)、(2ns,5fF)、(1ns,1fF)、(1ns,20fF)。未知单元为0，三ICG，边界端口/库/约束相同。
- 0f既有完整映射和五档STA来自原封存manifest 9bda2d8c8ee254786ac8928588d3372b2b269bca89d6ec720eb1abf2c936be77，逐输入校验后复用；额外控制D/ICG查询两边都按同条件执行。
- 独立FU未改。核实其生产源码/生成模块一致后注明成本复用，不重复综合相同FU，不借用为新父级成本。
- 局部前置证据：C2 manifest 5fe7ea1cd978cf14ef371380a51e64d942673e1c62c7ac3748698418237b1428；FU/原父级/补充父级与结构审查PASS。输入不变时不重跑局部测试。

## 筛选线与顺序

1. 新生成、1次父级综合、5档完整STA，再两边各5次定向控制STA。所有实际命令/退出码、路径起止点/slack、源/依赖/生成物/工具/库SHA均记录；工具成功与筛选通过分别记录。
2. 45项：每档r2r、i2r、vdot_r2r、vdot_i2r、vdot_r2o、ready及FP/INT/VDot三个ICG.E；每项arrival≤0f同档101%。基线正slack的ICG保持非负。
3. 全部busy/owner及任何残余DIV保持寄存器D端nominal最差≤1.737526ns；基线控制最差必须重现1.930584ns。父级面积≤284614.946×1.001=284899.560946库单位。未知/缺失路径不能当0，旧hold意外残留或范围不符须先解释/拒绝。
4. 全部门槛通过并独立审查后，才新建C2全核构建与同镜像周期控制器。复用已固定NEMU/flash/镜像必须逐身份核对；构建新EMU，严格全宽结果/控制/拒错恢复等回归后才性能。若筛选失败，保留0f，关闭本候选的全核/周期入口；不临时放宽门槛、不修改RTL重筛。
5. 数据作为新的C2-cost永久记录追加至版本档案。不得将新结果覆盖C2-local当时未测的记录；失败/退化和未执行层级保留。

这些是工程内部筛选线，不是官方比赛门槛；pre-layout结果不代表布局后时序、整核Fmax或功耗。若后续有依据继续改RTL，仍先向用户说明。无GitHub写入。
