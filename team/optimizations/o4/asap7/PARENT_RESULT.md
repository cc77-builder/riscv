# ASAP7／Nangate45完整父级复验

2026-10-28，基于James_Hotten `e1815c0732dcef544d4ceefd7fd93f26155409a4`及本地ASAP7工具。双库完整父级综合、门控二值语义／连接及五档setup覆盖审查完成；两库1ns均未达标。最终时序采用parent-timing-04（明确关闭CRPR并回读确认），不是早期预检查结果。

## 固定范围

真实CommonParentCostTop／VFEX4，保留VDot、VIDiv、VFDiv和三个ClockGate，完整生产接口；不是测试观察顶层。421个生产源码／配置／成本入口文件按LF归一化与当前工作区核对，新生成56份SV。依赖及JDK21／firtool1.62.1复用既有父级验证环境，生成在新的Linux目录，不改冻结输入。

实验显式O2/H1开启、O1和trace关闭；生产O1/O2默认仍关闭，没有修改生产Scala源码或build.sc。这是实验配置的成本对照，不将其冒充默认配置的结果。

两库同一份RTL、Yosys0.9／ABC1.01／OpenSTA2.0.17、ABC目标1000ps。Nangate45 typical为1.10V/25℃，ASAP7 RVT/TT为0.70V/25℃。使用零互连wire-load，输入输出延迟均0.1ns、uncertainty0.05ns、输入与时钟transition0.05ns；五档分别1ns/5fF、0.5ns/5fF、2ns/5fF、1ns/1fF、1ns/20fF，同一映射网表做敏感性检查。与旧O4默认线负载不同，不混用旧成本数字。

## 性能／成本对比

| 指标 | Nangate45 | ASAP7 RVT/TT | 判读 |
| --- | ---: | ---: | --- |
| 映射单元数 | 203,210 | 197,332 | 少2.8926% |
| 标准单元面积合计（μm²） | 284,935.742 | 19,311.00588 | 少93.2227%，非布局／整核面积 |
| 1ns/5fF最差setup裕量（ns） | −2.006459 | −0.651433 | 改善1.355026ns，但均未达标 |
| 最差裕量对应路径arrival（ns） | 2.856458 | 1.501433 | 少47.4372%；路径端点不同，不是整核提频比 |
| 物理触发器数 | 17,173 | 17,174 | 不因数量接近宣称逻辑等价 |
| VDot物理触发器／真实ICG数 | 1,352／3 | 1,352／3 | 两库来源和时钟连接审查一致 |

面积逐项与固定1x LEF核对：Nangate66种、ASAP7 98种实际使用单元全部一致。两库各208个顶层端口的方向与位宽一致。三个ICG确实驱动寄存器，没有被旁路；扇出分别为2903／12908／1352与2903／12909／1352。触发器数量差异位于VIDiv相关来源，本轮未对整网表实施形式等价，不把同接口或同数量误作完整功能证明。

### 1ns/5fF分类路径

arrival含所报路径的时钟／输入预算，最差slack与最大arrival不一定对应同一条路径。

| 路径类别 | Nangate arrival（ns） | ASAP7 arrival（ns） | Nangate slack（ns） | ASAP7 slack（ns） |
| --- | ---: | ---: | ---: | ---: |
| 整体r2r | 2.775406 | 1.534848 | −1.854242 | −0.589397 |
| 整体i2r | 2.793484 | 1.490671 | −1.870047 | −0.545222 |
| 整体r2o | 2.814678 | 1.501433 | −1.964678 | −0.651433 |
| 整体i2o | 2.856458 | 1.484913 | −2.006459 | −0.634913 |
| ready返回 | 0.243529 | 0.267816 | +0.606471 | +0.582184 |
| VDot r2r | 1.329957 | 1.002074 | −0.406697 | −0.061665 |
| VDot i2r | 1.621862 | 1.009658 | −0.695828 | −0.069247 |
| VDot r2o | 2.571597 | 1.306898 | −1.721597 | −0.456898 |
| 门控E／ENA setup | 1.539090 | 0.561245 | −0.660581 | +0.343124 |

ASAP7并非所有路径均改善：ready返回arrival增加0.024287ns；虽仍满足本轮约束，也必须保留。父级VDot的内部、输入及写回路径仍有负裕量，不能继承先前独立FU的正slack结论。

### 五档敏感性：每档所检路径的最差slack

| 约束 | Nangate（ns） | ASAP7（ns） |
| --- | ---: | ---: |
| 1ns／5fF | −2.006459 | −0.651433 |
| 0.5ns／5fF | −2.506459 | −1.151433 |
| 2ns／5fF | −1.006459 | +0.348567 |
| 1ns／1fF | −1.985840 | −0.608940 |
| 1ns／20fF | −2.082654 | −1.134891 |

ASAP7仅在本轮2ns档下全部所检setup路径通过；没有进行布局布线、CTS、hold和电气约束全集检查，不能发布物理500MHz或1GHz签核结论。没有测量功耗，软件执行周期数也没有因替换工艺库改变。

## 门控及兼容性门禁

- Nangate使用CLKGATETST_X1：CK/E/SE/GCK对应CK/E/TE/Q。
- ASAP7使用ICGx1_ASAP7_75t_R：CLK/ENA/SE/GCLK对应CK/E/TE/Q。
- 从真实Liberty解析statetable及输出state_function，枚举CK/E/TE/旧锁存值的16种组合，必须与低电平透明的TE|E一致。七项主机测试含六种错误拒绝。该审查是二值状态语义，不代表模拟延迟／X传播或整网表形式等价。
- 不使用上游未定义宏时直通时钟的包装，不删除TE；映射后必须仍有三个实际ICG，SE必须直接连接顶层testEnable。功能时序设置testEnable=0，E/ENA仍参加setup检查。
- 映射无未知单元，canonical网表重读拓扑必须相同；分别提取整体r2r/i2r/r2o/i2o、ready、VDot子集及门控使能路径。
- check_setup仅允许证明为常量的输出及直连case-zero的SE端点；其他动态无约束、缺失要求路径、无时钟或工具警告均拒收。

### 已发现并处理的兼容性问题

1. Nangate触发器是Q输出；ASAP7 DFFHQNx1的QN为反相物理输出（Liberty的next_state为!D），综合器补偿极性。旧Q引脚选择及原始信号位选择都会漏掉ASAP7寄存器。前两次分类检查明确失败并保留；最终按保留的VDotElastic.sv来源定位实际触发器，再选择其实际输出引脚。两库均核对1352个VDot寄存器及唯一真实门控时钟来源。
2. 初版默认CRPR在理想ASAP7门控时钟上给VDot路径增加0.634547ns补偿，使该r2r路径出现+0.572881ns裕量。此补偿没有物理时钟树证据支持，本轮两库统一执行`sta::set_crpr_enabled false`并回读确认；重跑后该裕量为−0.061665ns。早期结果保留但不用于最终性能结论，另有负控确认默认CRPR旧结果被最终审查器拒收。
3. 原多库读取和模板保留、ps/ns单位转换、canonical网表重读拓扑门禁继续有效。最终每库五档／45条分类路径全部存在，共90条；无未解释动态无约束端点。setup覆盖检查通过与数值时序达标分开判定。

前期父级功能RTL验证仍只按其原源码和输入身份引用；本轮门控二值审查、STA及连接摘要不替代完整映射后门级仿真或形式等价，也不扩展为新的全核DiffTest。

## 运行与交付

新生成及映射目录为`/home/amesotten/.cache/codex-rvinno/asap7-current-cost-20261028`下的parent-generation-01／parent-map-01。最终分类为parent-timing-04，前三轮均保留。421生产文件及21,198依赖文件与复用来源分别核对；没有修改生产Scala源码或build.sc。原始[封存清单](../../../evidence/asap7-parent-20261028/manifest.json)、[最终时序](../../../evidence/asap7-parent-20261028/timing.json)、[结构审查](../../../evidence/asap7-parent-20261028/review.json)、[面积核验](../../../evidence/asap7-parent-20261028/area-check.json)及[证据包](../../../evidence/asap7-parent-20261028/parent-evidence.zip)提供具体来源。

复验入口依次为check_environment.py的`--rtl <parent-rtl> --top CommonParentCostTop`、parent_timing.py、verify_area.py、review_parent.py。所有运行输出为新目录；最终时序判断以timing.json为准，mapping.json中的简单预检查数值不是最终分类结论。

后续优化宜先以真实输入／写回关键路径定位瓶颈，同时保留ready退化监测；当前证据不足以自动修改流水级数、默认开关或声称全核性能提高。本轮未提交或推送。
