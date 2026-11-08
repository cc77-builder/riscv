# Booth9 候选：实际算术、FU 与局部成本结果

日期：2026-11-08 UTC。合同 `dot16-prefix-booth9-local-v1`。

**Booth9 候选已通过新的实际算术结构检查和两态 FU 测试，完成局部映射及 STA；暂不替换原 prefix。** feature1 库面积从17,965.374降至17,190.516，减少4.313064%，但最差 I2R slack 从−0.238006退步至−0.254728 ns，差16.722 ps。两态均未满足名义1 ns；本次没有 parent、整核、应用或整核 PPA 资格。

## 实现与实际验证范围

本候选将 P 层的 Baugh–Wooley 部分积改为 radix-4 Booth9 有偏置编码。每半区为288个部分积位、32个独立neg补偿、288个FA、20个HA、8层压缩。结构计数降低不直接等于面积或时序收益，采用判断以实际结果为准。

架构请求/结果接口保持128位，上升沿工作、同步高有效valid复位，数据寄存器仍由valid保护；P/R两弹性槽、E0接受/E1推进/E2最早响应、无阻塞II=1保持。**内部数据表示确有修改**：feature0的P行仍为19位，feature1的四条P行从19增至20位；R仍为19/20位。feature1的dot8在接受时保存高半有偏置零 `(2^19,0)`，不再把高半行简单置零。因此不能宣称wrapper或全部状态位宽原样不变。

关键实际身份见 [result.json](result.json)：

| 对象 | SHA-256 |
| --- | --- |
| 候选 `VDotDatapath.scala` | `f0a8bbe58440c6113aa56f848387c6b4e4a487d71ec2832a1e43fca55d3a8245` |
| 候选 `VDotElastic.scala` | `0fcc5df10355ee1e6382678ba40bc9d7ddf830b560dcc469c46e6a6888441556` |
| 实际 `VDotCarrySaveRows.sv`（81,277 B） | `58dfeae9ec39cdc18e398dded21cd17e269706c62147a4e324901b859ca2752b` |
| 本次 result（208,177 B） | `bee65e3e79276f5ca6365f40d4e861692124c2322a727ac201b2c6a25cec4129` |

新结构检查解析实际生成模块，核7168个实际recode情形、256个signed-byte分解，以及FA/HA布尔恒等、层间依赖、权重和唯一消费，建立每半区全部 `2^128` 个二态操作数输入的组合恒等，不含X/Z语义结论；实际记录没有丢弃carry。每半区两行编码满足 `(row0+row1) mod 2^20 = (signed_dot8+2^19) mod 2^20`。四份实际cost/FU消费者另行完成输入半区、P捕获、19/20位保存、dot8有偏置零、前缀连接及架构输出绑定检查，不能用裸算术模块证明代替wrapper检查。

Finish19/20的实际字节与原无约束输入加法SAT产物相同，按完整证据身份精确复用；本次新的单体乘法miter为 `NOT_RUN`，历史 `UNKNOWN_EXTERNAL_TIMEOUT` 保持原义。这里不声明全FU顺序形式等价或RTL到映射网表等价。

两态均重新生成、构建并运行原FU套件，各含10,022条基础向量；feature1另有20,124次合法与40次非法比较，以及原混合流、取消、复位和背压覆盖。32条实际子命令中24条exit0，8条identity/wen/high/cancel观察注错（每态4条）exit1，紧随的8条原分类检查均exit0，确认预期拒错。注错记录的 `expected_exit` 为null，不能写成runner直接配置了expected_exit=1；观察注错也不等于RTL变异覆盖。所有32条命令均记录reaped/group_absent=true。

## 同边界局部成本与取舍

本次沿冻结CommonFuCostTop、Nangate45典型库、ABC D1000和既有1 ns STA条件记录；两态均保持与原prefix相同的220端口/2888bit接口。比较基线为原prefix result SHA `a0c4dd60fddc001f368b71ec283327f2d7fe0874080ac35304e3debe783116d0`，不是Pgroup或D800。面积单位为 **library area units（库面积单位）**，到达时间/slack为ns；没有布局布线或功耗测量。

| 实现 | feature | 库面积 | DFF | R2R arrival / slack | I2R arrival / slack |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原prefix | 0 | 14,171.948 | 1,639 | 0.862744 / +0.061775 | 1.172514 / −0.251286 |
| Booth9 | 0 | 13,761.244 | 1,639 | 0.905090 / +0.017123 | 1.185985 / −0.259803 |
| 原prefix | 1 | 17,965.374 | 1,678 | 1.079437 / −0.156976 | 1.163662 / −0.238006 |
| Booth9 | 1 | 17,190.516 | 1,682 | 1.041449 / −0.119946 | 1.180911 / −0.254728 |

- **feature0**：面积减少410.704（2.898007%），DFF不变；R2R slack减少44.652 ps但仍为正，I2R slack恶化8.517 ps。
- **feature1**：面积减少774.858（4.313064%），DFF实际增加4个；R2R slack改善37.030 ps，但更差的I2R slack恶化16.722 ps，仍有254.728 ps缺口。

实际feature1 [I2R报告](timing-feature1/i2r.rpt) 与 [R2R报告](timing-feature1/r2r.rpt) 的起止点、arrival和slack与结果文件一致。I2R最坏输入由原prefix的src1[75]换成src1[21]，不是固定同一路径的变化。其余三类Booth路径的slack为：

| feature | R2O | I2O | ready |
| --- | ---: | ---: | ---: |
| 0 | +0.316490 | +0.276713 | +0.626505 |
| 1 | +0.309378 | +0.263049 | +0.626505 |

两态 `nominal_setup_met=false`。局部成本流程完成不等于时序通过；面积与R2R改善没有消除更差的I2R问题。**当前保留原prefix及其既有整核证据，Booth9作为已完成局部验证的未采用候选留档。** 不将原prefix的parent/core、K288/K768或旧f149完整forward资格转授给它。原成本与历史资格入口见 [硬件成本记录](../../../RESULT.md)。

## 执行、归档与交付边界

[run-host-final.json](run-journal-01/run-host-final.json) 记录host起止为 **05:28:23.8890997–05:29:12.6860998 UTC**，执行时长48,750 ms，exit0、cleanup完成，未超时或取消；内层result区间为05:28:25.093995–05:29:12.493030 UTC。使用CPU affinity `[2]`（单核）、nice5。宿主耗时不作为硬件性能指标。

[raw.zip](raw.zip) 精确为 **32,185,935 B**，SHA-256 `011cae5620e05a8110914c4cd2bb114c11c0bae0bb2f40a46179b4312068b58d`；包含 **263个原始payload文件 / 78,765,824 B**，省略文件数为0。

[audit.json](audit.json)（1270 B，SHA `d12f96162bdf21e24519bf441a0c6d7017e4b14006b7d521d8b723c5e8c12665`）记录全部成员SHA/CRC通过、源未变、715项原始输入pins及35份准备输入核验通过、全部记录进程组不存在。归档阶段0新增EDA、0新增guest；归档成功不增加功能或性能资格。

实际新增结论为 `arithmetic_equivalent=true`、`fu_qualified=true`、`local_cost_recorded=true`。`parent_qualified`、`fullcore_qualified`、`application_performance_qualified`、`core_cost_qualified`及 `production_default_changed` 均为false，新增整核构建/运行均为0。resident、原cache/classpath和生产默认未改，原始及失败证据保留。
