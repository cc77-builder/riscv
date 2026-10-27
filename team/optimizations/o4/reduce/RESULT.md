# R3 / carry-save 归约真实 FU 筛选结果

操作 `20261025-LiZufan001-r3-reduce-0202`；实验合同 [r3-vdot-csa-reduce-v1](CONTRACT.md)。实际主工程从 2026-10-25 02:26:05 到 03:20:15（UTC+08:00）完成恢复、实现、验证与封存；此前按用户要求暂停处理 caller 交付。发布收束时间见 [Issue #2](https://github.com/cc77-builder/riscv/issues/2)。

## 决定

**STOP_SCREEN：不采用候选，关闭本次筛选。** 事前要求 nominal 完整 FU r2r 至少改善 10%、完整 FU 单元面积不增加、五种约束下其余路径不退化超过 1%。候选只满足正确性与接口门槛；r2r 改善不足、面积增加、i2r 退化均独立触发停止。没有降低门槛或选取有利配置改判。

生产 `VDotDatapath.scala`、稳定入口、官方程序及其判定器均未修改。候选仅以 [patch](candidate.patch) 和完整实验身份保存；没有扩大到父级 G2、整核、DiffTest 或应用周期。**本 R3 子项新增 EMU 为 0，无整核提频或 ASIC 评分结论。**

## 本轮新 AB

双方从相同源码基点 `6ffe7f94839b08df8de2558c35d482e1b90288e8` 独立生成完整生产 FU 边界：O2 两槽与 H1 结果寄存器，所有 trace 关闭，全部控制及 577 位 perf 信息保留。提交时基点前移到 `ae3cb558036a8d186350817465f280f6626fdd6d`，中间仅三份协作文档改变；实验身份没有转移。

Nangate45 typical 25°C / 1.1V；Yosys 0.9 / ABC 1.01 / OpenSTA 2.0.17。相同工具、库、生成选项、源码文件集和依赖，仅归约源码不同。约束详见合同和归档原始 Tcl；没有布局布线或功耗仿真。

| nominal 指标 | 新 baseline | CSA candidate | 变化 |
| --- | ---: | ---: | ---: |
| 完整 FU 标准单元面积 | 17298.246 | 17392.676 | +94.430，+0.54589% |
| 映射单元数 | 8894 | 9032 | +138 |
| DFF 位数 | 1742 | 1742 | 相同 |
| r2r 到达时间 / ns | 1.163404 | 1.153109 | −10.295 ps，−0.88490% |
| i2r 到达时间 / ns | 1.190323 | 1.213137 | +22.814 ps，+1.91662% |
| r2o 到达时间 / ns | 0.611317 | 0.560924 | −8.24335% |
| i2o 到达时间 / ns | 0.636728 | 0.585440 | −8.05493% |
| ready 到达时间 / ns | 0.253743 | 0.229774 | −9.44617% |

[comparison.json](evidence/comparison.json) 保留所有数值、停止原因及端点；[paths.csv](evidence/paths.csv) 列出全部 25 组路径对照。nominal 为 1 ns / 5 fF；另有 0.5 ns、2 ns、1 fF、20 fF。五组是同一映射网表上的不同 STA 约束，**不是五次独立综合**。r2r、i2r 到达时间在这些配置下相同，周期变化主要改变 slack；20 fF 下 baseline r2r 的最坏终点有切换，原报告完整保留。

nominal r2r slack 从 −0.240117 ns 到 −0.233016 ns，i2r 从 −0.268520 ns 到 −0.292491 ns；两者仍为负，不宣称 1 GHz 时序闭合。r2o/i2o/ready 改善不能抵消事前约定的面积和 i2r 门槛。

## 路径为何收益有限

从实际映射重读网表将 STA 寄存器名关联回 RTL：

| 路径 | baseline | candidate |
| --- | --- | --- |
| nominal r2r | pProducts_3[1] → rPacket_res_data[27] | pProducts_2[3] → rPacket_res_data[18] |
| nominal i2r | src_0[21] → pProducts_2[15] | src_0[37] → pProducts_4[15] |

关联原文见归档 `endpoint-binding.json`。baseline r2r 的前段为 5 个连续 XOR/XNOR，candidate 为 9 个；前缀末端到达时间约为 0.391469 ns 与 0.589815 ns。candidate 后续 `_10198_` 的 OAI33_X1 单元延迟为 124.950 ps、slew 为 101.514 ps。实际映射显示，增加的压缩前缀抵消了后续进位部分的收益；本轮不能仅凭抽象树深断言 CSA 会更快。

两边的最坏路径起终点不同，整个 FU 重新映射也会改变负载、单元选择与路径排序。i2r 退化并不证明 CSA 逻辑跨越了产品寄存器；双方生成的 `VDotProducts.sv` 字节相同。上述是这组映射结果的解释，不推广为所有 CSA 结构或其他工艺的结论。现有数据不足以支持继续枚举更多树或加法器。

## 真实 RTL 算术证明

成功方法是 [structural_proof.py](structural_proof.py) 生成/校验的**全输入域结构算术证书**，不是有限随机采样，也不是把手写模型当真实 RTL。

- 输入确认为 8 个独立 16 位产品，输出为完整 128 位；网表无状态、未知常量、环路或多驱动。baseline 的 7 个加法单元、符号扩展及范围通过逐项系数/区间核验，8 项恰好各使用一次，总和范围为 [−262144, 262136]。
- candidate 从实际生成网表识别 6 个 3:2 压缩器及一个最终 19 位加法，核实每个 XOR/AND/OR 的连接与位宽、carry 左移、42 个压缩单元互不重叠。对单比特的 8 种输入验证恒等式，再沿实际网络反向守恒归约至 8 个符号扩展输入，证明模 2^19 的和相等。
- signed19 范围充分，低 32 位符号扩展与高 96 位清零逐位校验。因此覆盖全部 128 位输入空间与完整 128 位输出。
- 5 个实际 SV 变异（bit100 翻转、lane0 零扩展、carry 错位、低32符号错误、lane 重复）经同一 Yosys 转换和证明器拒绝；每项保存具体反例，并由独立 Yosys `eval` 原文确认实际错误输出。

成功 `formal-struct-01/result.json` SHA256：
`9c804143bf75ab50663ff46af766270bf0df5ff6e01ea3f7dc07fee2462c423d`。

先前直接 Yosys SAT 300 秒超时、ABC CEC 输入次序预检查失败、ASCII AIG 格式不支持和二进制 AIG CEC 外层 150 秒超时均原样保留。没有把超时、exit 0 或缺少反例视为等价成功。CEC 解析器另通过 10 个针对性结果样本，包括矛盾决定标记的拒绝；本轮 CEC 结论仍是未证明。

## FU、接口与映射核验

候选真实 G1 使用现有团队 FU 运行器及四观察负控，新执行结果：

```text
O2_FU_PASS vectors=10022 cycles=31499 accepted=23311 responses=22460 cancelled=739 reset_dropped=112 overlaps=19856 stalls=4900 full=24901 partial_kill=322 both_kill=158 reset_cases=8 ii1_intervals=10021 latency2_probes=1
```

23,311 接受 = 22,460 响应 + 739 取消 + 112 复位丢弃。identity / wen / high / cancel 四个故障均以预期 exit 1 和严格标记被捕获。结果支持本候选的两槽身份、首响应 2 拍、无停顿 II=1、反压、同拍推进、取消与复位；不能转授父级或整核资格。

两边均为 220 个端口、1945 个输入位（含 clock，非 clock 约束输入 1944 位）和 943 个输出位。DFF 分组均为 products 128、result 32、stage_state 2、P/R control 各 213、P/R perf 各 577，总计 1742。未删除观测或控制状态，没有未知或未映射单元。

原始 candidate 网表含 3 个合法的拼接赋值，OpenSTA 2.0.17 无法解析；第一次 candidate STA 失败保留。适配器仅把它们拆成等价标量赋值，baseline 为 0 处修改。两边都用同一 Yosys 重读，去除非逻辑属性后完整网表结构一致；映射 JSON 原字节相同，未重新映射、换库或改约束。这是针对本次无相关语义属性的映射网表核验，不是可任意去除属性的通用等价规则。

原版 O4 原文审计器独立核验两组映射和全部 10 个 STA profile；封存后 [重检结果](evidence/recheck.json) 再次核验原文、证书、5 个算术反例、4 个 FU 故障及全部固定门槛，返回 `R3_SEALED_RECHECK_PASS / STOP_SCREEN`。全部辅助工具为团队新增，官方权威程序原样保留。

## 证据与接续

[归档](evidence/r3-evidence-v1.zip) 为 4824697 字节，SHA256 `a29aabaccbdbad2355e8b0b03c281c60dc16a48677db1d752f8e4b7be2c3c03d`；493 份原载荷总计 69867288 字节，外部省略清单为空。详细身份见 [archive.json](evidence/archive.json)、[handoff.json](evidence/handoff.json)，实际重检命令见 [README](README.md)。

归档保留成功/失败的生成、SAT/CEC、FU、综合、STA、适配、原文审计，以及原始源码/依赖/工具与编译产物身份；源码 Git 检出与已安装的工具二进制不重复打包。完整原生目录继续保留，未删改冻结或其他 Agent 成果。

首次 ChatPC 归档任务返回 `worker_start_result_unknown_do_not_replay`，标准输出/错误缺失，后续只读检查未发现对应 worker、Python 进程或归档目录。取消后旧目录锁仍在，第二个请求被 `mutation_busy` 拒绝且未执行。该未知回执保持未知；交付使用独立新输出目录，只读已完成证据，成功封存与重检。记录在归档 `transport-attempt.json`，没有重放未知操作或更改原目录。

当前合理后续是基于已测 caller 的打包/搬运成本提出新的对等软件实验；若再次改 caller，必须同路径优化并验证 RVV、测完整窗口、另立身份。该建议不把现有 hoisted 草稿提升为已验证实现，也不改变 R5 默认。
