# P2：Jade 历史依赖链与通路只读审查

范围：固定本地 Jade a17e38128e589d745152f3ef4b595b4572b22b3d，10月17日统一基线16ae9ddcda54fc9a2fddffad73174cf793ac7814的封存数据。
本轮新增目标/EMU/NEMU/综合/STA运行均为0，没有改生产RTL，也没有拉取远端或上传。

## 结论

值得学习的是固定延迟执行通路及唤醒/旁路配合，不能直接搬“一拍点积”或只改latency字段。
历史数据对依赖链短一拍存在重复观测线索；但旧Jade只有退休/CSR观察，没有ACCEPT/RESP/WB，
不能精确归因该一拍发生在乘加、输出寄存器、唤醒还是调度路径。

Jade与当前0f的执行端口、调度元数据和硬件接口都不同。当前0f保留的1857是后续批次结果；
本审查的1857是10月17日T14控制。数值相同不使二者变成同轮对照。

## 重新核查的历史数据

各实现3个数据集、每数据集4个正式自定义窗和4个正式RVV窗。
本轮重新核对各chain镜像、原始stdout/stderr、EMU、NEMU、flash、生成manifest及源码哈希，未重跑目标。

| 指标 | 同批历史T14 | Jade |
| --- | ---: | ---: |
| chain256平均gross cycles | 1857.00 | 1601.25 |
| 同窗口RVV平均cycles | 5440.50 | 5440.50 |
| gross cycles/dot | 7.25390625 | 6.2548828125 |
| 正式相邻VDot退休边数 | 3060 | 3060 |
| 退休间隔主峰 | 7拍：3036条 | 6拍：3030条 |

差值255.75 cycles/256 dots只是单长度数据，不能作为已经测过的净斜率。
T14完整退休间隔分布为4拍12条、7拍3036条、10拍12条。
Jade为0拍3条、1拍6条、5拍9条、6拍3030条、7拍3条、12拍9条。
0拍表示ROB同周期成组退休，不表示依赖指令0拍执行。主峰不能直接当作FU延迟/接受间隔。

原文仅有T13_RETIRE、T13_COUNTER_ENQUEUE、T13_CSR_SAMPLE。
Jade ACCEPT/READY/RESP/WB/依赖唤醒均为NOT_OBSERVED。
没有统一工艺下Jade面积/STA/Fmax，也没有当前0f与Jade的新同批测量。

## chain256 实际依赖

最终manifest循环为：

~~~asm
li t6, 256
loop:
    vdot v10, v10, v9
    addi t5, t5, 1
    addi t6, t6, -1
    bnez t6, loop
~~~

Jade编码0xe6950557；旧T14编码0x0295050b。vd=vs1=v10，构成真实寄存器RAW链。
初始v10是固定哨兵7b8ea1b4c7daed001326394c5f728598，不是dataset_pair的A；v9取各dataset的B。
第一轮后低32位保留点积位型，高96位清零；下一轮又将低8字节解释为8个signed int8。
这不是对int32标量反复做整数乘法，也不是GEMV。本轮独立Python递推复核三个数据集256轮的完整128位期望，全部相等。

每窗还有循环控制、初末计数器和序列化开销。自定义1032 retired instructions，RVV2056。
标量指令可以重叠并存在融合计数，不能用指令条数直接推断周期。

## 静态执行路径对照

| 项目 | Jade固定实现 | 当前0f |
| --- | --- | --- |
| 解码 | FuType.vialuF，复用VIAluFix | 独立FuType.vdot |
| 执行配置 | VFEX0与VFEX2均含VialuCfg | VFEX4与DIV共享父级 |
| FU时序合同 | piped=true，CertainLatency(1) | piped=false，UncertainLatency；O2两槽弹性 |
| 算术 | 8乘法+4/2/1归约组合，结果/isVdot各RegEnable | E0保存乘积与身份，E1归约到低32位结果槽，E2最早响应 |
| 流控身份 | 跟随VecPipedFuncUnit/VIAluFix既有管线 | 独立P/R身份、实际接收、反压保留、取消和DIV排斥 |
| 非法状态 | 补丁补SEW/LMUL并沿用vstart>=vl不更新 | 严格vill/SEW/LMUL/vm/vstart==0/vl==8/fuOpType |

Jade实际相关源码已与封存hardware-source-manifest逐文件比对，包括Parameters、FuConfig、VIAluFix。
旧轨迹没有实际EXU编号，不能声称每条都走VFEX0。
共同合法域SEW8/LMUL1/VL8/vstart0/vm1支持统一chain比较，不支持全部异常/掩码/取消语义等价。

关键位置：
- 固定补丁：/home/riscv/riscv-lab/unified-vdot-benchmark-20261017/references/jade/patches/03-xiangshan-vdot.patch。
- 历史实际源码根：/home/riscv/riscv-lab/unified-vdot-benchmark-20261017/variants/jade/repo。
- 该根src/main/scala/xiangshan/backend/fu/FuConfig.scala:528–545，CertainLatency(1)在540行。
- wrapper/VIAluFix.scala:197–228为乘加与RegEnable，395–411为输出/异常选择。
- src/main/scala/xiangshan/Parameters.scala:448/452为两个VialuCfg执行位置。
- 当前src/main/scala/xiangshan/backend/fu/FuConfig.scala:583及wrapper/VDotElastic.scala。

## 后续建议

先以当前0f轨迹定位ACCEPT→MOVE→RESP→WB→依赖消费者的真实身份边。
如果空档在结果产生后，优先评估写回、唤醒/旁路对齐，不先压缩全部乘加。
若考虑固定延迟路径，必须证明端口冲突、反压和取消不会导致提前唤醒消费错误数据；
不能只将UncertainLatency改成CertainLatency(1)。

算术合并阶段是另一项且时序风险更高的候选。当前0f布局前1ns参考STA已有负slack；
周期更少不保证实际时间更短，Jade缺少同约束PPA不能被当作时序保证。
是否开P4由当前路径实测决定，不能仅凭本历史差值决定。
未来单候选仍需FU/真实父级、同约束PPA、全核NEMU及同镜像周期逐级筛选。

## 复现与失败保留

~~~bash
python3 -B /home/riscv/riscv-lab/software-import-20261026/p2-dependency-20261028-01/jade/analyze_history.py --out <新输出目录>
~~~

最终通过analysis-05/result.json，包含全部正式样本、36个自定义窗口（包括首次/预热）、两项ROI损坏拒绝、输入哈希。
analysis-03是加强最终档案身份前的中间通过。

保留三次分析器拒绝，均非DUT失败：
- analysis-01：误取summary的smoke链，日志hash拒绝；改为明确performance角色。
- analysis-02：错误要求退休周期严格递增，合法成组退休触发拒绝；改为(cycle,slot)严格有序。
- analysis-04：早期jade-harness-review的generator SHA为6fe170bf，最终发布为2aee4610。
  当前、原工作区、两份归档生成器均为后者且与最终文件校验.json一致。
  未改旧review，最终身份采用最终归档及实际镜像manifest；早期review仅为历史依据。
