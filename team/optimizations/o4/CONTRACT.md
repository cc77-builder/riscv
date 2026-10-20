# O4结构与时序代价评估合同 v1

2026-10-20用户授权开始O4。起点676ec737291b3818c0f4bf3d9f542f85fddb53c7，本地分支local/o4-cost-20261020。
不push、不改变默认模式、不自动O5/G5，不写T16正式报告。

## 同条件比较

O1为FUSED_INPUT=1/HANDOFF=1/ELASTIC=0，O2为1/0/1。
同一生产src树、依赖、MinimalConfig单核/VLEN128/ROB48；全部T12/T13/O1/O2 trace明确关闭。
只新增O4公共接口harness及Mill入口，不改算术、生产RTL、ISA/NEMU或旧测试/密封证据，不重构建全核EMU。

边界分别为完整FuncUnit生产接口和真实VFEX4 ExeUnit生产接口（含全部原DIV与门控）。
O1/O2各边界顶层端口名称、方向、位宽须完全相同。输入保持自由变量、输出完整可观察；不使用旧scoreboard/tap测试top估面积。
FU的额外pipelineStatus未向顶层引出，父级正常消费真实占用；FU数值不包含父级新增占用/门控成本。
保留完整默认MinimalConfig的vpu/perf输出字段；如父级优化裁剪这些字段，以父级结果另列，不把全FU保留成本直接当芯片增量。

## 工具与工艺参考

工具以Ubuntu Jammy固定版本deb解包到工作根tools/root，不sudo、不升级系统或既有工具。
Yosys0.9、BerkeleyABC1.01、OpenSTA2.0.17；deb及可执行文件摘要和版本保留。
映射参考为OpenROAD-flow-scripts固定提交bf3f9b344bf7d9d999f199778a722833bccbd33c中
NangateOpenCellLibrary_typical.lib，SHA256 8d540a4d4cf6d09d27c87ad067857a9c0c2eeb023ab7a56e058cd3113db4e9b1。
典型角25C/1.10V，Liberty时间单位ns、电容单位fF；原始文件、头部及平台许可证保留。
这是开源单元库的同条件前布局比较，不是香山实际工艺签核或芯片实现结论。

## 综合与时序口径

两模式同一脚本/工具/Liberty、无波形与动态功耗估计。SYNTHESIS定义下排除assert/printf，不保留测试观察状态。
报告未映射RTLIL寄存器位、算术节点/宽度、映射单元种类数量及Liberty area之和，按完整FU/完整父级分别列。
ABC目标1000ps，同驱动/负载约束；组合映射与DFF映射身份完整保留，未知单元/未映射时序单元不得通过。
如ClockGate映射到CLKGATETST_X1，必须核对低电平透明锁存TE|E、CK&EN及CK/E/SE/GCK连接，记录原黑盒和替代模型；不以常开钟替代门控。

主STA约束：周期1ns，uncertainty0.05ns，非clock输入最大延迟0.1ns，输出最大延迟0.1ns，
输入转换0.05ns、输出5fF；不排除reset/flush/ready路径。parent的testEnable在功能时序中设为0，并报告此case约束。
补0.5/2ns周期与1/20fF输出负载敏感性（同一映射，不冒称不同目标重新优化）。
记录r2r、i2r、r2o、i2o和out_ready→in_ready路径，所有约束/单位/端点/原始路径及setup检查保留。
无放置、布线、CTS、SPEF或片上variation；时钟理想、互连只有工具可获得的引脚/负载模型。不能直接倒数得到整核Fmax，不宣称实际功耗。
如果某一边界无法可信映射或STA，保留失败并将该部分结论限定为结构/路径审查，不用不完整STA填数。

## 复核和交付

源码/环境/工具/库/约束/生成RTL/网表/日志/真实退出码逐项绑定。两模式端口、算术复用、映射闭合、路径和统计完整性须核验。
分析器拒绝缺模式、不同约束/库、缺时序路径/未知单元、被静默忽略的工具错误和不一致面积。初始失败不得删除。
工具运行一次只安排一个重型生成/综合，Mill最多2并发任务，不占用旧build/emu；工作根/home/riscv/riscv-lab/o4-cost-20261020。
输出为可复现工程比较、明确的适用边界及G5所需代价依据；最终采用仍需O5/T17与人工复核。
