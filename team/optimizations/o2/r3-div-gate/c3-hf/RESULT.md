# C3-HF：FP DIV/SQRT 保持位最小试验结果

完成时间：2026-10-25T22:41:41.712685+08:00。**拒绝本候选，保留0f，结束当前门控试验。**

本轮唯一生产候选为77d0a1228f0da7d584d5c7375b404dcda9763cf3，从0f12df675378556670afd0dd2153f47fcb330610建立独立工作区。只替换FP DIV/SQRT保持寄存器的置位条件；原开钟公式、实际握手、取消释放、两个hold、busy/ROB、整数路径及VDot均保留。未推送GitHub。

## 1. 实际取舍

局部功能通过；五档45项路径 **20/45通过，25/45未通过**。父级面积 284614.946→285138.966（+0.184115%），最差控制D端 1.930584→1.609770 ns（-16.617459%）。

最终判定遵循冻结合同，不按单一有利指标取舍。工具运行和独立审计通过，表示数据可用；是否采用由全部功能、成本及后继资格决定。此记录没有新增全核/NEMU或应用周期，不改变既有加速比，不代表功耗或整核Fmax改善。

[冻结合同](CONTRACT.md)、[成本合同](cost/CONTRACT.md)、[精确生产补丁](c3-hf-production.patch)、[候选身份](candidate.json)。

## 2. 新局部功能结果

| 层级 | 本轮真实结果 |
| --- | --- |
| 主机检查 | 49父级＋2FU，共51项通过 |
| FU完整128位结果 | 22定向＋10000随机，31499拍；4运行时观察值故障注入被拒绝（非RTL变异） |
| 真实父级原回归 | 13组、35075拍；16运行时观察值故障注入被拒绝（非RTL变异）；原严格轨迹复算通过 |
| 补充父级 | 115场景、2959拍；SQRT、真实双lane偏斜、ROB、切换、TE0复位及取消；7坏观察被拒绝 |
| C3保持位观察 | 2958拍有效初始化域内，P=实际FP fire；FP/INT hold逐拍符合原fire递推；9坏观察被拒绝 |
| 新观察覆盖 | 143次FP接受、15次普通SQRT接受、54取消、291拍FP响应反压、20个TE0复位场景、40拍复位 |
| 取消后严格关钟 | 54窗口、162立即空闲采样，0多余时钟 |
| 独立局部审计 | 1103输入、126依赖；固定候选及实际日志/生成物/二进制/观察链通过 |

原父级和FU结果日志与旧固定输入输出一致；父级另外核对了原0f源绑定封存，不把旧run当时的HEAD改写为0f。旧C3-G0抽象只复用其固定方程与有效初始化边界，没有重复枚举或把其计数累计为新RTL覆盖率。

第一次supplement-01在编译测试观察器时因32位文件句柄逻辑非触发宽度告警，未执行RTL案例。只改测试表达式为显式==0，保留旧源码与失败记录，新supplement-02通过。解析器初次过严匹配和审计初检失败也保留；没有再改生产RTL、关闭warning或放宽验收。

## 3. 成本与时序原文

同一CommonParentCostTop/MinimalConfig(1)完整生产父级；工具、库、端口、约束一致，126依赖和143份原基线成本载荷核对。58个生成文件、56个SV中只有ExeUnit.sv改变，其余55个生产SV逐字节相同；无测试monitor、trace关闭。

下表为nominal参考约束（1ns、5fF），单位ns。五档完整原文、起止点和slack均归档。

| 路径 | 0f到达 | C3-HF到达 | 变化 | 相对门禁 |
| --- | ---: | ---: | ---: | --- |
| 父级 r2r | 3.261218 | 3.229321 | -0.978070% | PASS |
| 父级 i2r | 3.314103 | 3.283447 | -0.925017% | PASS |
| VDot r2r | 1.356106 | 1.318106 | -2.802141% | PASS |
| VDot i2r | 1.474949 | 1.566019 | +6.174451% | REJECT |
| VDot r2o | 2.776701 | 2.852312 | +2.723052% | REJECT |
| ready | 0.247821 | 0.268650 | +8.404857% | REJECT |
| FP ICG.E | 1.888362 | 1.975078 | +4.592128% | REJECT |
| INT ICG.E | 1.128021 | 1.262832 | +11.951107% | REJECT |
| VDot ICG.E | 0.873228 | 0.874722 | +0.171089% | PASS |

| 控制D端 | 0f / ns | C3-HF / ns |
| --- | ---: | ---: |
| divBusy | 0.870094 | 0.859954 |
| FP hold | 1.930584 | 0.557445 |
| INT hold | 1.506153 | 1.609770 |

三状态必须各自绑定不同DFF的D。C3有意保留双hold，未套用C2“旧hold应消失”的检查。全部控制D最差门槛为1.737526ns；面积上限284899.560946参考库单位；45项各自最多比同档0f增加1%，基线非负ICG slack仍须非负。缺失/NaN/重复数据不能当0。

全部失败项：

- area exceeds +0.1%
- nominal/vdot_i2r exceeds +1% (6.174451%)
- nominal/vdot_r2o exceeds +1% (2.723052%)
- nominal/ready exceeds +1% (8.404857%)
- nominal/icg0 violates +1%/positive-slack gate
- nominal/icg1 violates +1%/positive-slack gate
- period050/vdot_i2r exceeds +1% (6.174451%)
- period050/vdot_r2o exceeds +1% (2.723052%)
- period050/ready exceeds +1% (8.404857%)
- period050/icg0 violates +1%/positive-slack gate
- period050/icg1 violates +1%/positive-slack gate
- period200/vdot_i2r exceeds +1% (6.174451%)
- period200/vdot_r2o exceeds +1% (2.723052%)
- period200/ready exceeds +1% (8.404857%)
- period200/icg0 violates +1%/positive-slack gate
- period200/icg1 violates +1%/positive-slack gate
- load001/vdot_i2r exceeds +1% (6.174451%)
- load001/vdot_r2o exceeds +1% (2.747118%)
- load001/ready exceeds +1% (8.845151%)
- load001/icg0 violates +1%/positive-slack gate
- load001/icg1 violates +1%/positive-slack gate
- load020/vdot_i2r exceeds +1% (6.174451%)
- load020/vdot_r2o exceeds +1% (2.649358%)
- load020/ready exceeds +1% (9.991618%)
- load020/icg0 violates +1%/positive-slack gate
- load020/icg1 violates +1%/positive-slack gate

这是布局前参考库工程筛选。负slack、失败项、拓扑变化均保留；不能把到达时间倒数称整核最高频率，不能把VDot r2o误称纯点积加法树延迟。源码保持不变的模块也可能受完整父级共享逻辑、扇出和ABC重映射影响；此轮结果不自动证明某一布尔项是所有变化的唯一原因。

## 4. 执行与停止边界

实际执行一次新生产父级生成、一次综合、五档常规STA以及两边各五档定向STA。没有实施第二个候选，没有放宽阈值、设置新false path或挑映射重试。23项成本主机方法包含66个观察门槛拒错检查；独立审计重新核原始面积/映射/路径、绑定与完整判定。

下一步：关闭本轮门控优化，保留O2＋H1＋DIV取消修复0f，转回稳定集成和T17干净复现；新更大门控假设须另有具体证据，不自动尝试gate+hold。

保留基线ExeUnit SHA256 fd98aaced17c39dabd4776a53948f05650c8956178f6540bf5695d15753d60fa；原EMU SHA256 2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8。C3 ExeUnit SHA256 150baa7c78aa8948ff0f4fb771912f7d2058aaa802a0853ee99ea3a2dc0bb9b7。新全核/NEMU、同镜像周期、功耗、整核Fmax均NOT_TESTED。

## 5. 数据留档

本轮统一记录ID C3-HF-20261025-01。各层实测分别记资格，旧20条记录不覆盖。Agent独立复核不代替成员人工审查。

[完整证据manifest](evidence/20261025-trial/manifest.json)保存源码/命令/版本、实际结果、全部失败和关键输入；大文本无损压缩，二进制仅保留身份，构建对象与缓存不入日常归档。采用判定与真实成本值见同一封存中的work/cost-01/screen-01/result.json，局部见work/local-result.json，原文审计见work/independent-review/。证据完整性检查不等于再次执行硬件验证。
