# C3-HF 成本筛选执行合同

本文件落实上级 ../CONTRACT.md，不改变阈值或候选范围。候选77d0a1228f0da7d584d5c7375b404dcda9763cf3，ExeUnit SHA256 150baa7c78aa8948ff0f4fb771912f7d2058aaa802a0853ee99ea3a2dc0bb9b7；基线0f12df675378556670afd0dd2153f47fcb330610。生产修改仅浮点DIV hold SET，双hold保留。局部资格尚未齐全时不得启动成本工具。

- 固定 CommonParentCostTop /真实VFEX4/MinimalConfig(1)，T14=1/O2=1/O1=0、四种trace=0；不使用观察器或补充测试顶层。
- 原样复用候选的 O4 elaborate.py/synthesize.py/timing.py、GenerateVDotCost.scala、canonical.py、compact.py；生成入口 mill -i -j 2 vdotCost.runMain team.vdot.GenerateVDotCost parent。
- Yosys0.9/ABC1.01/OpenSTA2.0.17及已记录动态库；Nangate45 typical25°C/1.1V，库SHA 8d540a4d4cf6d09d27c87ad067857a9c0c2eeb023ab7a56e058cd3113db4e9b1。ABC -D1000ps，BUF_X1驱动，5fF负载。
- STA理想时钟，5K_hvratio_1_1 wire-load，uncertainty/transition各0.05ns，IO最大延迟0.1ns，TE=0。五档依次nominal(1ns,5fF)、period050(.5,5)、period200(2,5)、load001(1,1)、load020(1,20)。不新增false path/multicycle。
- 固定0f基线成本原manifest SHA 9bda2d8c8ee254786ac8928588d3372b2b269bca89d6ec720eb1abf2c936be77；143份原始成本文件逐个校验，复用其映射和标准五档。
- 仅一次新候选生成、父级综合与常规5档。标准完成后两版本各5档定向查询：busy、FP hold、INT hold三个D端以及FP/INT/VDot三个ICG.E；保存所有60条定向报告。定向查询绑定每一版自己的mapped.json与instance-binding，禁止复用c编号。
- 两版本都必须存在dut.elasticDivOccupied_divBusy、dut.uncer_en_reg、dut.uncer_en_reg_1，分别映射到不同DFF的D；不查询owner，不执行C2“旧hold须消失”检查。缺失、常量化、无驱动、非DFF、错D、状态别名或残留owner身份均拒绝。
- 45项=每档r2r/i2r/vdot_r2r/vdot_i2r/vdot_r2o/ready/三个ICG；每项arrival≤0f同档101%，基线非负ICG slack保持非负。nominal三个状态D最差≤1.737526ns；基线三状态分别须重现0.870094/1.930584/1.506153ns。
- 父级面积≤284899.560946，基线284614.946，未知单元0、3ICG、端口/库/约束一致。缺失/NaN/重复观察不能判0或PASS。
- WORK/cost-qualification.json独立冻结新C3八类局部通过回执、三份source.json及输入SHA；校验candidate和当前源码，C2旧PASS不转授。脚本本身、两层合同与qualification一起冻结并逐阶段复核。
- 工具exit0仅表示执行成功；screen.py若实质超线输出C3_HF_SCREEN_REJECT，保持0f、关闭本候选，不重映射择优。基础设施错误保留失败与修复依据，不误写为候选失败，不因此另做第二版RTL。
- 全过仍只表示成本筛选通过；脚本从不构建/运行全核。后继全核/NEMU/同镜像周期按上级授权与合同另行执行，不能拿旧EMU代替新验证。没有整核Fmax、功耗或官方分数结论。
