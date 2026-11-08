# Pgroup local-01 实际结果独立审查

## 决策结论

**现有真实记录支持本次新 Pgroup 的局部算术与 FU 验证通过，并完成同口径局部映射/STA；未发现需要撤销这些局部结论的证据冲突。支持暂不采用 Pgroup 替换当前 prefix 候选，保留此次完整实验记录。**

暂不采用的依据是 feature 1 的取舍不利于当前关键约束：cell area 增加 40.964（约 0.2280%），I2R 到达时间增加 4.260 ps，I2R slack 恶化 9.146 ps；R2R 虽改善 40.347 ps，但仍有 -0.113918 ns slack，最差 I2R slack 仍为 -0.247152 ns。不能只用 R2R 改善宣称整体时序优化。

同时，**不能将此次结果写成“全部指标退化”或“功能失败”**：feature 0 的面积减少 0.266，I2R 到达时间改善 4.732 ps、最差 slack 改善 4.274 ps；两个 feature 的多个非关键输出路径也有改善。本次数据支持“局部功能合格，但没有足够理由替换当前候选”的决定。旧 prefix 本身也未满足 nominal setup，故“不满足 1 ns”不是区分两者的唯一依据；真正的比较依据是新候选没有改善 feature 1 的最差约束，且增加面积。

本审查只读取云端已归档文件、现有控制器/源码和直接 prefix 结果；未访问 PC、Pro 或网络，未修改 source/input/actual，未重新执行 helper、结构 checker、EDA、FU 或整核。没有追加验证门槛，也不要求为这一停止决定再运行实验。

## 1. 精确来源与归档范围

| 对象 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `summary.zip` | 691,942 | `3d3e1a7087f334b45a8e9f935ed58b0342cabebae3ad76ba2187010ae3866c9c` |
| `actual/ARCHIVE-MANIFEST.json` | 41,619 | `6563c276b6eba40a59b2100cbc780454b1a0251e253892be9649d8494cfe9806` |
| `actual/local-01/result.json` | 208,017 | `0502f877c833cc4d25ab955ed4273f3e54b3b48ed9acbc57677bfdc0ffabc026` |
| `actual/local-01/inputs.json` | 142,530 | `e42a6124ddea79a7b660ab63838195bf1db19c5b99746c0ba73d7159b91e8f1b` |
| `actual/local-01/final-artifact-pins.json` | 20,899 | `7c19def0b476728cf6c12f189c586d9d59825d77330bb91d2d500314350f6084` |
| `actual/local-01/arithmetic-structure.json` | — | `8b353cad466cc78b3f48da58efce202161204bc1002cba117cde1578d112f1db` |
| 实际执行控制器，输入/快照/归档清单绑定 | 45,126 | `794544ddfb3455b05deaffe8588d3c9715d02446ac04c50fe2710c6caaaafc0e` |
| 对比 prefix 实际结果 | 205,865 | `a0c4dd60fddc001f368b71ec283327f2d7fe0874080ac35304e3debe783116d0` |

独立重新计算了 zip SHA。zip 有 51 个唯一 member：manifest 本身和 50 个精选实际结果/日志/报告。逐 member 验证长度、SHA，并将 manifest 本身与落盘副本作字节比较，均一致；落盘 `actual/local-01` 的 50 个文件也全部匹配 manifest。

manifest 记录原实验目录的 244 个文件，`omissions=[]`，来源为：

`/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-pgroup-20261108-main`

本次独立逐字节核验的范围是 summary 中的 51 个 member；未把 manifest 中另外列出的文件误称为本次已全部重新读回。对于未包含在 summary 的生成 SV、binary、证明快照等，下面的核对是 result / pins / archive manifest 之间的身份链核对。归档声明为 byte transport，没有升级原资格。

## 2. 32 条真实命令与时间、回收状态

`result.json` 状态为 `PGROUP_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE`。状态记录的起止为：

- started：`2026-11-08T02:31:55.595912+00:00`
- finished：`2026-11-08T02:32:44.022702+00:00`
- 该状态区间为 **48.426790 秒**；32 条命令的记录耗时合计 **48.031309 秒**。这不是外层启动、前置输入 pin、传输和归档的总耗时，也不是应用性能指标。

命令构成与合同一致：compile 1、generate 4、新 CSA checker 1、两个 feature 的 FU 共 22、map/STA 共 4。32 个 label 和 32 个 PID 均唯一；全部记录按时间先后排列，没有重叠或倒序，每条 finished 不早于 started，每条实际时间小于其记录预算。结果记录 CPU `[2]`、nice 5、总预算 1,200 秒。

退出码为 **24 个 0、恰好 8 个 1**。八个退出 1 全部来自预定故障注入，不是漏报的失败：

| feature | 注入 fault | 注入实际退出码 | 注入原始日志 | 后续原 checker |
| --- | --- | ---: | --- | --- |
| 0 | identity | 1 | `O2_FU_INJECT identity` / `O2_FU_FAIL identity` | exit 0，`O2_FU_NEGATIVE_GATE_PASS identity` |
| 0 | wen | 1 | 对应 `INJECT wen` / `FAIL wen` | exit 0，`PASS wen` |
| 0 | high | 1 | 对应 `INJECT high` / `FAIL high` | exit 0，`PASS high` |
| 0 | cancel | 1 | 对应 `INJECT cancel` / `FAIL cancel` | exit 0，`PASS cancel` |
| 1 | identity | 1 | 对应 `INJECT identity` / `FAIL identity` | exit 0，`PASS identity` |
| 1 | wen | 1 | 对应 `INJECT wen` / `FAIL wen` | exit 0，`PASS wen` |
| 1 | high | 1 | 对应 `INJECT high` / `FAIL high` | exit 0，`PASS high` |
| 1 | cancel | 1 | 对应 `INJECT cancel` / `FAIL cancel` | exit 0，`PASS cancel` |

逐项核对了 checker argv：fault、`--return-code 1`、相应 feature/fault 的新注入日志路径都正确。正向和注入命令指向各自新 `fu-featureN/obj/VVDotElasticFuTestTop`，使用本次快照 `vectors.tsv`，没有运行旧 binary 的路径混用。

32 条命令均记录 `reaped=true`、`group_absent=true`，最终 `all_children_reaped=true`。这是对归档执行回执及成熟控制器回收逻辑的复核，没有另作本机实时进程查询。编译和四次生成的空日志与退出 0、后续生成身份及实际消费者一致，不将正常静默输出误判为未运行。

## 3. 输入与输出绑定

`inputs.json` 含 715 个 originals 与 35 个 snapshots。7 个落在本次 staging 范围内的 originals、全部 35 个快照，以及 `final-artifact-pins.json` 的 **97 个**固定输出/快照，均与原目录归档 manifest 对应 SHA 一致。原始完整 classpath 的本次记录 SHA 为 `d9a3071fc4f2cb1fb6766bcf3d3efdc0571bfc09986bace0b432b3b82d445902`，匹配固定原输入。

关键绑定包括：新 datapath `1f9a4c80…`、不变 wrapper `912c1a03…`、最终控制器 `794544dd…`、合同 `295dcec0…`、controller derivation `dd6046d7…`、source derivation `b757bddd…`、未修改的 verifier `e6924e40…`，以及精确 prefix 结果 `a0c4dd60…`。执行身份与此前完成静态审查的最终版本一致。

四个 generated consumer 的 20 个 SV 身份、长度均与 manifest 一致；相对于已闭合 prefix 生成记录，**每套只有 `VDotCarrySaveRows.sv` 的 SHA 改变**，对应 wrapper、R、top 和 extern 的 SHA 保持相同。两个新 FU binary 的结果 SHA 同时与 final pins 和 manifest 相等，两个 mapped.v / mapped.json 的结果 SHA 也与 manifest 相等。

最终结果记录 `inputs_unchanged`、`generated_inputs_unchanged`、`original_classpath_unchanged` 均为 true；resident/cache/default 未修改，`new_core_builds=0`、`new_core_runs=0`。此前静态审查确认的最后 manifest 后中断/deadline 检查位于成功状态更新之前，实际执行仍使用该版本。

## 4. 新 P 证明与旧 R 复用成立

### 新实际 P

原始 `actual-csa-structure.log`、独立 `arithmetic-structure.json`、结果内嵌结构报告三者一致；独立报告与内嵌对象完全相等。本次实际 CSA 为 **108,593 B / SHA `889066a85ec8c169dca78c4532c5e3cc6a1b458decbad3e2d452b2355e052213`**。四个新 consumer 全部绑定这个 SHA，且它与旧 prefix CSA 的 `68227036…` 不同。

报告为 `CSA_STRUCTURAL_EQUIVALENCE_PASS`：完整解析、512 个部分积、112 个带符号补码项、477 个 FA、17 个 HA、3,884 个局部布尔情形、所有节点无环、只引用更早层、全二态输入等价；验证器 SHA 精确为原样 `e6924e40…`。无丢弃 carry，row0 的最高位为 1、row1 最高位为 0。因此本次需要的整数 signed-row 条件也得到报告支持，不能只把模 `2^19` 等价作为 feature 1 符号扩展的依据。

结构报告自身仍把 wrapper、sequential FU、parent、full core、application 和 performance 资格留为 false，这符合其适用范围；完整控制器另记录四项实际 wrapper binding 完成，以及本次实际 FU 结果。没有把局部组合结构证明单独当成整条流水线证明。

### 相同 R 的既有证明

结果中的两项 prefix miter 与精确旧 prefix 结果完全相等。新 cost/FU 两套 19 位 R SHA 均为 `8cbaa598…`，新两套 20 位 R SHA 均为 `3ce276e8…`，分别等于对应旧 SAT 的 actual RTL SHA。两套 gold、gate、prove.ys、原始日志和 finish SV 的快照 pins 全部与 manifest 及 miter 字段对应。

此前已审原证明覆盖无约束输入的实际 R 模加法；这次绑定的实际 R 身份不变，因此复用适用。结果显式给出复用来源与条件。新 P 的 `arithmetic_structure_proof_reused=false`；新乘法 `independent_miter=NOT_RUN`、solver proved 为 false；旧 `UNKNOWN_EXTERNAL_TIMEOUT` 独立列在 historical 字段。未发现旧 P PASS 或旧 UNKNOWN 被冒记为新候选运行结果。

## 5. 本次完整 FU 的实际范围

两个正向日志都包含相应额外覆盖标记和 `O2_FU_PASS`，与 `fu_results.coverage` 一致：

| 项目 | feature 0 | feature 1 |
| --- | ---: | ---: |
| vectors | 10,022 | 10,022 |
| cycles | 31,595 | 53,205 |
| accepted | 23,327 | 43,699 |
| responses | 22,476 | 42,736 |
| cancelled | 739 | 835 |
| reset_dropped | 112 | 128 |
| reset_cases | 8 | 24 |
| ii1_intervals | 10,021 | 10,021 |
| latency2_probes | 1 | 1 |

两个 feature 均满足记录中的 `accepted = responses + cancelled + reset_dropped`。feature 0 的禁用新 op/未知 op 各拒绝 8 项；feature 1 另记录 10,022 paired vectors、20,124 legal compares、40 illegal compares、20,043 mixed II1 intervals、first latency 2、96 mixed cancel pairs 和 16 additional reset cases。八个实际负控如前表完成。

这些支持合同范围内的新算术与 FU 仿真资格。结果中的 `parent_qualified`、`fullcore_qualified`、`application_performance_qualified`、`core_cost_qualified` 仍为 false；不能据此声称整核、应用收益、完整 ASIC 或全 FU 时序形式化证明通过。

## 6. 同口径成本与真实时序

同口径依据是固定 common FU 边界、与旧 prefix 一致的端口记录和 top 身份，固定原 nominal map/STA 模板与约束，固定 Nangate typical 库、Yosys、STA 输入 SHA，以及此前审查过的模板路径替换与逆变换检查。实际 map/STA 命令使用相同工具路径，目标是本次独立生成和 mapped 目录。

原始 Yosys 日志给出的 cell area 为 14,171.682000 和 18,006.338000，与 JSON 数值一致；cell histogram 总数分别为 6,600、9,796，DFF 汇总分别为 1,639、1,678，与结果及旧 prefix 的 DFF 数相符。这里的面积是该库/边界的 cell area，不是整个 core 或版图后面积。

我独立从 10 份原始路径报告读取 arrival/slack，与结果 JSON 对比；又根据旧 prefix 实际值重新计算全部 `delta_from_prefix`，没有数值不一致。下表的 arrival/slack 单位为 ns，面积为同一库面积单位；差值均为新减旧。

| 指标 | feature 0 prefix | feature 0 Pgroup | 差值 | feature 1 prefix | feature 1 Pgroup | 差值 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cell area | 14,171.948 | 14,171.682 | -0.266 | 17,965.374 | 18,006.338 | +40.964 |
| DFF | 1,639 | 1,639 | 0 | 1,678 | 1,678 | 0 |
| I2R arrival | 1.172514 | 1.167782 | -0.004732 | 1.163662 | 1.167922 | +0.004260 |
| I2R slack | -0.251286 | -0.247012 | +0.004274 | -0.238006 | -0.247152 | -0.009146 |
| R2R arrival | 0.862744 | 0.886941 | +0.024197 | 1.079437 | 1.039090 | -0.040347 |
| R2R slack | +0.061775 | +0.035033 | -0.026742 | -0.156976 | -0.113918 | +0.043058 |
| R2O arrival | 0.512549 | 0.487942 | -0.024607 | 0.509852 | 0.488159 | -0.021693 |
| I2O arrival | 0.606580 | 0.569327 | -0.037253 | 0.570335 | 0.570073 | -0.000262 |
| ready arrival | 0.260263 | 0.223495 | -0.036768 | 0.223495 | 0.223495 | 0 |

I2R arrival 与 slack 的差值不同，不能互换。新报告中 I2R 的 required time 为 0.920770 ns，包含 0.050000 ns uncertainty 和 0.029230 ns setup；关键端点/路径已变化，因此 feature 1 的 arrival 增加 4.260 ps 对应 slack 恶化 9.146 ps。两个 feature 都明确记录 `nominal_setup_met=false`；feature 1 的 R2R 和 I2R 仍均违例。

两份 setup-checks 都报告 119 个 unconstrained endpoints；名单与结果中的既有常量端点名单及旧 prefix 完全一致。没有出现新的名单扩张，本次没有把该已知分类升级为新增阻塞。Yosys 的 SDFF 导入 warning 所指 scan cell 未被实际 cell histogram 使用；另外的 ABC multi-output/combinational warning 未形成工具失败。STA 两次均有完整结束标记，原始时序报告与数值一致。

## 7. 采用、保留与停止建议

1. **不替换当前 prefix 候选。** feature 1 的关键 I2R slack 与面积都变差；R2R 改善不足以改变最差约束或形成可宣称的完整性能收益。当前证据不支持为此继续消耗整核构建/应用测量资源。
2. **完整保留此次源、输入、实际证明、FU、负控与 cost 证据。** 它是一项真实完成、局部功能合格但优化取舍不佳的实验，不应记作测试失败或删除失败/不采用证据。
3. **保留有界结论，避免过度归纳。** feature 0 有小幅面积与 I2R 收益，feature 1 的 R2R 也有实测改善；本次不能证明“任何 P 分组优化都无效”。但这些结果也不足以立即引入按 feature 分叉实现或自动重试。后续只有出现能解释并针对实际 I2R 关键路径的具体新方案时，才值得重新评估。

审查开始：2026-11-08 02:38:49 UTC。主要证据及独立数值核对完成：2026-11-08 02:42:03 UTC。报告仅写入 `review/ACTUAL_RESULT_REVIEW.md`，不改变实际结果、候选或此前审查报告。
