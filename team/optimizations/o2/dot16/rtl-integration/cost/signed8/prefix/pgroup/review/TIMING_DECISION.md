# Pgroup实际时序：停止继续调排序，保留一次映射目标对照

## 决策

**不建议继续修改P树分组或排序，也不建议凭R2R一项改善将Pgroup替换原prefix。** 本次小试有价值：新实现已取得局部算术/FU证据，确认源级深度改善没有解决当前I2R瓶颈。保留这个已验证备选及全部原始结果即可；它不是功能失败，也没有在所有指标上被原prefix支配。

如果还做一个较简单的后续，建议冻结**原prefix feature1实际SV**，保持库、top、输入、load及全部STA约束不变，仅将映射目标 `abc -D 1000` 改为 `-D 800` 做一次敏感性对照。原1000点已有闭合证据，不必重编RTL、重新跑FU或扩大到整核。800是一个待测探索点，不是已证明的最优参数或新验收条件；若没有实质改善所需路径，停止这项探索，不继续扫参数或改树凑工作。

## 1. 同边界实际结果

源为`1f9a4c80…`，新result为208,017 B、SHA256 `0502f877c833cc4d25ab955ed4273f3e54b3b48ed9acbc57677bfdc0ffabc026`；原prefix result为`a0c4dd60…`。新结果状态为 `PGROUP_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE`，两态名义1ns仍未满足；没有新增parent/fullcore/application/core-cost资格。

| Feature / 指标 | 原prefix | Pgroup | 差值 |
| --- | ---: | ---: | ---: |
| f0库面积 | 14,171.948 | 14,171.682 | −0.266 |
| f0 i2r arrival / slack（ns） | 1.172514 / −0.251286 | 1.167782 / −0.247012 | arrival −4.732 ps |
| f0 r2r arrival / slack（ns） | 0.862744 / +0.061775 | 0.886941 / +0.035033 | arrival +24.197 ps |
| f1库面积 | 17,965.374 | 18,006.338 | +40.964（+0.228016%） |
| f1 i2r arrival / slack（ns） | 1.163662 / −0.238006 | 1.167922 / −0.247152 | arrival +4.260 ps；slack −9.146 ps |
| f1 r2r arrival / slack（ns） | 1.079437 / −0.156976 | 1.039090 / −0.113918 | arrival −40.347 ps（−3.737782%） |

DFF分别仍为1,639/1,678。f1总cell数由9,749增至9,796。面积仍低于20,000，但当前最坏负slack没有向目标改善；不能由R2R降低3.74%推出芯片频率或应用速度提高相同比例。

## 2. I2R为什么没有随单位深度下降

### 已有直接证据

原f1最坏I2R从 `src1[75]` 出发；新f1改为 `src0[30]`，新f0也从 `src0[30]` 出发。新f0/f1的路径在几乎整个单元序列、slew、cap和到达时刻上相同，只有末段存在很小差别，最终arrival相差0.140 ps。因此这不是同一条旧路径获得预期加速后的比较，而是两个完整映射结果各自最坏路径的比较。

对报告的单元输出弧直接求和：

| f1 I2R观测 | 原prefix | Pgroup |
| --- | ---: | ---: |
| 路径上的组合单元输出弧数 | 22 | 19 |
| 单元弧delay之和（ns） | 1.063370 | 1.067639 |
| XOR/XNOR总数 | 3 | 8 |
| 最长连续XOR/XNOR段 | 2级，0.106034 ns | **8级，0.499031 ns** |
| 报告中的外部input delay | 0.100000 ns | 0.100000 ns |
| arrival扣除上述单元delay及input delay后的余量 | 0.000292 ns | 0.000283 ns |

新路径中连续八个XOR/XNOR位于 `_12358_` 至 `_12461_`；加上前面的AND/OR链和后面的两个AOI21，总delay仍约1.068 ns。**单元数量少了，不等于按实际负载和转换方向计算的单元弧总延迟减少。** 这里直接net-delay增量合计不足0.3 ps，不能将结果简单归咎于大额布线传播延迟；cap/fanout/slew仍会通过单元弧查表影响delay。

新端点的setup要求也改变：旧required为0.925657 ns，新为0.920770 ns。arrival只多4.260 ps，较严的setup项再消耗约4.887 ps，所以报告slack总共恶化约9.15 ps。不能只比较arrival而忽略不同端点及转换方向对应的setup。

### 对模型的解释与边界

源级模型的30→22是固定FA/HA表达式的二输入单位门依赖深度，不含具体库弧、fanout、slew、buffer和匹配后的输入引脚。实际流程先 `synth -flatten`，再由ABC执行 `strash / ifraig / dc2 / &dch / &nf / buffer / upsize / dnsize`；它没有把源FA作为不可拆的实体，也没有承诺保留“晚输入接z”的局部拓扑。

真实路径已经是AND4、OR3、AOI/OAI、XOR/XNOR等映射网络，而不是模型的一串同延迟FA原语。因此，本次事实足以否定“这项单位深度改善必然转为同量I2R改善”的推断。**尚未证明**某一个ABC pass、某一组共享项或某种pin选择单独造成了全部差额；没有必要为做当前取舍再开展大范围pass溯源。

## 3. R2R改善也不能归因于R算法改变

R的源码和实际Finish19/20 SV保持原字节，本次复用的仍是原精确组合模和证明。旧f1最坏R2R起于 `pRows_0_0[2]`，新路径起于 `pRows_0_1[2]`。两条路径前段都仍有连续五个XOR/XNOR：

- 旧五个单元弧合计0.311063 ns，走到该段末端的arrival为0.419780 ns。
- 新五个单元弧合计0.315956 ns，该段末端arrival为0.424922 ns，反而晚5.142 ps。
- 最终arrival却由1.079437降到1.039090 ns，收益出现在后续被重新映射的链和不同端点比较中；总路径输出弧数（含clock-to-Q）由22变20。

这说明R2R的改善是本次完整映射的真实结果，不能写成“P重排消除了R前段XOR”或“修改了prefix收尾算法”。源逻辑改变影响全局映射/节点安排是与证据相容的解释；具体启发式原因未被隔离证明。

## 4. 为什么只建议一个mapping对照

原冻结 `map.ys` 已有 `-D 1000`，并非没有启用时序导向；新map日志也实际执行了 `&nf -D 1000`、`upsize -D 1000`、`dnsize -D 1000`。新ABC自身打印Delay=999.17 ps，所列起终点是 `src1[78]` 到一条P-row D输入；它并不是OpenSTA报告的 `src0[30]` 最坏路径。

原 `abc.constr` 只有 `set_driving_cell BUF_X1` 与 `set_load 5.0`。固定OpenSTA还具有1ns时钟、0.05ns uncertainty、0.1ns input delay、0.05ns input transition、DFF setup及 `5K_hvratio_1_1` wire-load。ABC日志则打印WireLoad="none"。这些边界不同，**不能把ABC的999.17 ps当成已通过OpenSTA 1ns**，也不能将两条不同路径的数值直接相减以精确分摊全部差额。

按新I2R端点只作预算估算，留给内部传播的时间约为 `1.0−0.05−0.1−0.02923=0.82077 ns`；因此800是一个有具体动机的更紧映射目标。它仍不等价于完整STA约束，也不保证收敛，更不允许更改STA约束来制造PASS。

建议对照只问一个问题：**同一份已经验证的原prefix feature1 SV，在原评估约束下，较紧的mapper目标能否换得有价值的时序/面积取舍？**

1. 固定原prefix那四件实际RTL、工具/库和输入身份，使用新隔离输出；唯一算法参数变化为-D1000→800。
2. 复用成熟map/STA流程已有检查，保持1ns、uncertainty、I/O delay/transition、load、wire-load及五类路径报告不变，同时报告面积/DFF/接口。无需新增FU或整核测试。
3. 只与相同RTL的原1000点比较；此试验不证明原prefix和Pgroup在所有mapping设置下谁更优。若没有改善主要负路径，或面积代价不合当前目标，结束该方向。

优先选择原prefix作此输入，是因为它有更小面积、略优I2R及已经完成的父级功能证据；这是降低接续成本的选择，不是宣称它支配Pgroup的R2R。若映射对照也无收益，当前证据支持停止围绕这棵压缩树微调，转回其他能影响项目目标的工作。

## 证据入口与本次操作范围

- 新：`../actual/local-01/result.json`、`map-1.log`及两feature的 `mapped/{i2r,r2r}.rpt`；新f1 I2R报告SHA `45a1a97d42dc58eeadd3bd69050fc90de502fd66d82fc31333b3e2e386a38ae6`，R2R报告SHA `304125dbba233a055bf24d375e5f13840bfd50725a77822e3f8588120364175e`。
- 原：`verification/prefix-critical-path-review-01/timing-paths.json`及拆出的报告；`mapping-constraints.json` SHA `bbcbc32f380bc0b5b4a7254e7debdc449d4c29d1be97423a5a9405e45fab3c87`；`mapping-headers.json`。原prefix的完整cost结果另由已取得的 `source-review/prefix-candidate-v1/actual-result.json`核对。
- 源码仍为9,850 B、`1f9a4c807b30b8aa769e65595ce6b54619b190a5f2b5af1d531413de9970b90c`。

本审查仅作云端只读解析和小型求和，未运行PC、Pro、EDA、候选或新映射，也未修改实现或增加验收要求。所有后续均为建议，当前工程资格仍以原实际结果为准。
