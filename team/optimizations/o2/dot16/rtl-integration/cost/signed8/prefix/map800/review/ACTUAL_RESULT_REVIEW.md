# D800 固定 RTL 对照：实际结果复核

复核日期：2026-11-08（UTC）。范围为云端已有实际摘要、原 prefix 基线与约束记录；只新增本说明，未访问 PC、运行 EDA 或修改实现。

## 结论

这次 D800 对照已正常完成，具备与原 feature1 D1000 比较局部映射代价和五类 STA 路径的证据。它没有解决 1 ns 时序缺口：库面积增加 **71.554（约 0.3983%）**，最差 I2R 的 slack 只改善 **1.757 ps**，R2R 及其余三类路径的报告数值不变。建议结束本次对照及其参数探索，保留 D1000 为原参考、D800 为已完成的实验记录；这些结果不足以支持替换参考版本、追加参数扫描或据此继续改压缩树。

这不是功能失败判定。新映射网表的 **`mapped_netlist_equivalence_tested=false`**，本次完成的是固定 RTL 的映射与 STA 代价对照，功能和 PPA 资格均不扩大。

## 已闭合的执行与比较边界

直接读取的 [result.json](actual/local-01/result.json) 为 69083 B，SHA-256 为 `ccf63f790256bdc37f74550012d0fe037490523e8dd35d42064dc0f2ad271735`，状态为 `PREFIX_FEATURE1_MAP800_COST_COMPLETE`。记录时间为 02:52:13.549179 至 02:52:22.832478 UTC。

两项实际命令为 Yosys `map-feature1` 与 OpenSTA `sta-feature1`，均 `exit_code=0`、`reaped=true`、`group_absent=true`，总记录 `all_children_reaped=true`、`inputs_unchanged=true`。Yosys 日志写出了 `CommonFuCostTop` 面积并执行 JSON/Verilog 输出；STA 日志包含 `DOT16_GENERATED_FU_STA_COMPLETE`。上述清理结论限于这两个已记录子进程及进程组，不扩展为对本机其他任务的判断。

本次实际输入是**原 prefix 的 feature1 RTL**，不是 Pgroup RTL。四个被读取的 SV 文件，其新输入清单 SHA 与原 prefix `actual-result.json` 的 feature1 cost 生成记录及完整归档 manifest 中的 source snapshot 记录一致。嵌入的 `baseline_cost` 与原 prefix 实际结果中的 feature1 cost 对象完整相等；Yosys、ABC、OpenSTA 及 Nangate45 Liberty 的新旧输入清单 SHA 也一致。

对原 [mapping-constraints.json](../prefix-critical-path-review-01/mapping-constraints.json) 和实际脚本做文本核对：只替换隔离输出目录，并将 `map.ys` 中 `-D 1000` 改为 `-D 800` 后，三份脚本分别精确相等；`abc.constr` 原字节未变。读入的四个 RTL 路径、flatten/映射流程、库文件与顶层均相同。

因此 **D800 是 ABC 优化目标，不是将 STA 时钟改为 0.8 ns**。STA 仍为 1 ns 周期、0.05 ns uncertainty/clock transition、0.1 ns 输入/输出 delay、0.05 ns 输入 transition、5.0 fF 输出负载和 `5K_hvratio_1_1` wire-load model；路径分组及报告选项相同。端口记录仍为 220 个、合计 2888 bit，DFF 为 1678 个，总 cell 数为 9749，与基线一致。

## 五类真实路径与变化的含义

逐份解析实际 `.rpt` 的 startpoint、endpoint、arrival 和 slack，均与 `result.json` 对应项一致。以下单位为 ns，按 arrival / slack 列示，不复制已有完整度量表：

- **I2R**：[i2r.rpt](actual/local-01/i2r.rpt) 为 **1.161906 / −0.236249**；D1000 为 1.163662 / −0.238006。arrival 改善 1.756 ps，报告 slack 改善 1.757 ps，两个小数差异来自按报告精度分别相减。最坏起点由 `io_in_bits_data_src_1[75]` 变为 `io_in_bits_data_src_0[83]`，打印的终点均为 `_19423_`，不能称为同一输入路径改善了 1.757 ps。
- **R2R**：[r2r.rpt](actual/local-01/r2r.rpt) 为 **1.079437 / −0.156976**，与 D1000 相同，起止为 `_19477_` → `_18414_`。
- **R2O**：[r2o.rpt](actual/local-01/r2o.rpt) 为 **0.509852 / +0.340148**，与 D1000 相同，`_18625_` → `io_in_ready`。
- **I2O**：[i2o.rpt](actual/local-01/i2o.rpt) 为 **0.570335 / +0.279665**，与 D1000 相同，`io_flush_bits_robIdx_value[4]` → `io_in_ready`。
- **ready**：[ready.rpt](actual/local-01/ready.rpt) 为 **0.223495 / +0.626505**，与 D1000 相同，`io_out_ready` → `io_in_ready`。

I2R 只消除了原有 238.006 ps slack 缺口的约 **0.7382%**，还剩 **236.249 ps**；R2R 仍有 **156.976 ps** 缺口。`nominal_setup_met=false` 与原始报告一致。这里是固定映射结果之间的小幅确定性差异，没有重复运行统计，既不应称为随机测量噪声，也不应放大为有应用价值的性能提升。

面积由 **17965.374** 增至 **18036.928**，采用 **library area units（库面积单位）**；不标注为 μm²。总 cell 数和 DFF 数未变，但不据此假定所有组合单元或内部连接不变。此次更紧的映射目标确实生成了不同映射网表，实际交换是少量面积增加换取极小 I2R 改善，同时没有改善另一项违例 R2R。这足以支持停止当前小范围尝试，无需增加诊断或验收门槛来证明“不能继续”。也不能从单次结果推导所有未来 RTL 或映射方案均无效。

## 资格与保留范围

同 RTL 允许继续引用原 RTL 层已有功能证据；它**不等同于**新映射网表已通过形式等价、门级仿真或全部功能验证。实际记录明确：

- `mapped_netlist_equivalence_tested=false`；不能把历史 RTL PASS 转写为 D800 网表等价 PASS。
- 本次新增 RTL 编译、FU 运行、整核运行均为 0。
- `application_performance_qualified=false`、`core_cost_qualified=false`、`production_default_changed=false`。

五类局部 STA 与库面积比较不证明整核频率、实际应用收益、物理实现 PPA 或比赛资格。停止这项探索不需要补做这些测试；保存现有结果及原始证据，原参考和生产默认保持其原有状态即可。

主要交叉核对入口为 [实际输入清单](actual/local-01/inputs.json)、[完整归档 manifest](actual/ARCHIVE-MANIFEST.json)、[原 prefix 实际结果](../../source-review/prefix-candidate-v1/actual-result.json) 和 [原 prefix 输入清单](../../source-review/prefix-candidate-v1/actual-manifests/inputs.json)。本说明未重做完整 raw 归档的运输校验，也未声称在云端重新读取或验证其中的映射网表正文。
