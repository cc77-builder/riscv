# Prefix feature1：FA_X1 映射筛查（未采用）

**该固定映射点未取得合格 STA，FA 路线已停止，未采用；生产默认不变。** 三段原始结果均保留 `FAILED`，没有因后续诊断或归档完成而改写。`16542.806` 仅是映射网表按固定单元库统计的面积，不构成时序、fmax、应用性能或完整 PPA 结论。

## 三段结果与停止原因

| 原生目录 | 实际结果 | 适用范围 |
| --- | --- | --- |
| `local-01` | Yosys 映射完成；OpenSTA 2.0.17 对 mapped.v 的 concat-LHS 报语法错误，控制器以 `incomplete STA` 失败。map/STA 子进程虽均返回0并回收，STA仍不合格。 | 映射结果含954个 FA_X1；库面积统计为16542.806。完成标志与进程返回码不能覆盖实际语法错误。 |
| `serialization-01` | 仅对既有 mapped.json 做 splitnets、Verilog 输出与回读；严格保留原始 cell 名的完整图比较不一致，在 STA 前停止。 | 该次原失败保持。后续诊断定位到名称表示差异，并未把这份原结果改为通过。 |
| `sta-resume-01` | 显式全量名称双射后，原完整终端图一致；同一既有网表的唯一一次 STA 续接触及30秒时限，回收后保持 `FAILED`。 | 无 setup-checks 及五类时序路径报告；总60秒预算未超时，失败来自内部STA的30秒上限。没有再次重跑或放宽时限。 |

完整名称双射覆盖全部6150个 cell：仅给原名以 `$` 开头的5196个 cell 增加一个字面前导反斜杠，其余954个名称不变。原固定 `circuit()` 对220个端口、10729个网、26529个端点及单元参数、引脚、位序和常量的比较保持不变，逆名称映射后终端图相同。此证据只证明既有已映射电路在该明确表示变换下保持连接，**不授予原RTL到完整网表的等价资格**。

续接复用已存在的 mapped.v，未重新运行 Yosys、ABC 或映射。其 STA 日志仅有启动 banner，缺少完成标志与阶段日志；不能进一步断言超时发生在读库、读网表、链接或时序传播的哪一步，也不能把没有 Error 文本解释为成功解析。

## 结论边界

`local-01/map-feature1.log` 中的 `Chip area` 为 **16542.806 library area units**，只说明这一固定映射网表的库面积统计。没有合格的 setup-checks，以及 R2R、I2R、R2O、I2O、ready 五类路径报告，故不报告时序通过、fmax、整核/应用收益或完整 PPA 改善；不将既有 RTL/FU/core 的历史 PASS 转给此映射候选。这条FA筛查未新增FU仿真、整核构建或EMU验证。

## 完整归档与闭合审计

原始证据见 [raw.zip](raw.zip)，闭合记录见 [audit.json](audit.json)。归档审计 `FA_FAILED_RUNS_CLOSED_ARCHIVE_PASS` 仅表示失败证据归档与回收检查完成，`sta_qualified=false`、`ppa_qualified=false` 保持。

| 项目 | 记录 |
| --- | --- |
| 原生内容 | 77个payload文件，未压缩总计30,283,426 B |
| ZIP成员 | 78个，含77个payload及1个manifest；零遗漏 |
| raw.zip | 1,420,115 B；SHA256 `25bbb1b15b8890604ad8bec8a0164ac14b7fe0242a9421862e3b03ff0b238e93` |
| audit.json | 1,924 B；SHA256 `a084168f0fe38aa5b75632509ddabde73c7e386e441c07ec502c612a10c334f5` |
| 内容核验 | 审计记录全部成员SHA/CRC核验通过，原库存及内容保持不变 |
| 输入闭合 | 68个实际输入pin通过最终核验：64个原始输入、4个生成输入 |
| 进程闭合 | 9个相关PGID均不存在：31999、32000、32003、32075、32076、32077、32078、32266、32267 |

归档保留7个原生目录：`input-01`、`input-serial-01`、`input-sta-01`、`input-sta-02`、`local-01`、`serialization-01`、`sta-resume-01`。其中 `input-sta-01` 仅作准备，唯一续接实际采用 `input-sta-02`；没有把两份准备源计作两次STA。三段原 `result.json` 的完整SHA及缺失报告清单均保存在审计中。

详细 STA 续接记录见 [sta-resume-run-pro2/RESULT.md](sta-resume-run-pro2/RESULT.md)，保留原报告字节。该报告的独立诊断建议不构成本轮继续运行的安排；本入口以三段失败闭合、停止FA路线和未采用为当前状态。
