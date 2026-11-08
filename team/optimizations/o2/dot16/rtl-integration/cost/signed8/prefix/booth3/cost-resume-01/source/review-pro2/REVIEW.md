# Booth P3：是否继续一次有界成本续接

2026-11-08，领域专家2。回应首席消息 `6499194bbcbc4b24a72b7c60d39bf6be`。仅审查、读取封存结果及脚本；本审查没有运行 Yosys、ABC、STA、FU、EMU 或新构建。

## 决策

**支持一次固定候选、固定约束的成本续接，随后停止这条工具适配分支。** 可复用的核心是已有 `splitnets` 序列化和完整终端图核对；旧 FA 控制器不能原样套用。若继续必须另写复杂 Verilog 重写器、改工具版本、改拓扑或继续扩大超时，就应停止 P3，保留已经得到的算术/FU结果。

值得做这一次的原因不是已经投入很多工作：P3 正好移动了已观察到的最坏 I2R 末级 carry，且第二次 R20 证明和两 feature 的 FU 测试已完成。真正的同约束面积与五类 STA 路径会决定 P3 是否值得保留，现有失败结果没有回答这个决策。此前 P2 是面积改善、最坏时序稍退的 Pareto 点；P3 可能改变选择，也可能因 R 链增加而被淘汰。它不改变 E2/II1，不能据此声称整应用周期收益。

**范围须说准确：feature1 尚未映射。** 如果要取得完整双 feature 成本，除了复用 feature0 的既有 mapped.json，还须完成 feature1 第一次、唯一一次同配方映射。不能把整个续接写成“零 mapping、只重跑 STA”。这仍是原候选一个成本点的未完成部分，不是新增参数扫描。

## 独立读到的实际状态

云端 `prefix-booth3-balanced-02/actual-detail.json`：126759 B，SHA256 `ef896318b9e2a9dbfe4675386df9bbc4d0e1e31fe0b110219db749ea8e97a055`。其中 R19 与 R20 新 SAT 均 PASS，R20 实际求解约13.31秒；两 feature 的10022向量及原负控通过。总结果仍为 FAILED，`cost_results=[]`，`local_cost_recorded=false`。`arithmetic_proof_completed/fu_tests_completed` 与最终整体资格字段不是同一层次，不能把整体 FAILED 改成整体 PASS。

随后通过 ChatPC 只读读取本机封存的 `dot16-prefix-booth3-20261108-main/local-02`：operation `0250d6044ba18f5fd71831ae3131d2ce.6c76cfff7677946c2b37691151b7d2cb`，06:26:34.9884591–06:26:36.5650673Z，1535 ms，exit0、cleanup=true。全部读取文件前后 SHA 相同。

| 文件 | 字节 | SHA256 |
|---|---:|---|
| result.json | 132331 | 63cee9334942c7e60405cef939ef3020b1817e5ee147cc7e12b22339884d9121 |
| cost-feature0/mapped/mapped.json | 5418334 | a0625a8f7d9f79d69e6118cfa84ec787c02e4dbb3c951c2bd2eb5a340d057a5d |
| cost-feature0/mapped/mapped.v | 828368 | b01481db8a1db4d2acff2cc7d91bf32bcdb8aa551f9c2036c3346c074eeeaa15 |
| cost-feature0/mapped/timing.tcl | 2674 | db69ed1d8252fe69f93fd60302108ce09821d6a708a44c2da3ceaaf5b1a4ff62 |
| cost-feature0/mapped/map.ys | 1580 | 9b382d57e13c08485a9f6bd3a936699b8df81951ac901ca9f5a9ea0767ce59d6 |

STA 日志报5次语法错误；实际网表共有9条 concat-LHS assign，因此不能把“5次错误”说成“只存在5条需处理语句”。它们属于 prefixSum.g/p 内部别名及常量赋值。不能只删除报错语句或把含 x 的项随意清零。应由已有官方 splitnets 导出，再用完整图保留所有常量/连接。

feature0 实际有6236 cells，全部原名以 `$` 开头；1658 DFF，220顶层 ports；没有 memory、process 或 net-init 属性。feature1 的 mapped 目录没有文件。未对错误解析产生的六份 rpt 赋予任何时序资格。

## 已有方法能复用到什么程度

实际旧链是 `read_json → splitnets → write_json → write_verilog -noattr -norename`，没有 `-ports`，也没有新的 synth/opt/ABC/dfflibmap。不是另设 `-noexpr` 方案。之后以相同 Liberty 回读 Verilog，执行 hierarchy/check 并导出 JSON。

已有 `fa_serialization.py`：13071 B，SHA `82738e4ca6c0d84de04cb8a77e9143ab2d646bc025e087dddc3ff62a12109a8a`。其中 `circuit()` 覆盖完整 top port 名字/方向/宽度/offset/upto/signed、全部 cell type/parameters/port方向及宽度、逐位终端连接分区和0/1/x/z常量，并拒绝 memory/process/init。保持此定义即可；无需新图算法或完整 RTL-to-mapped 证明器。

后续 `fa_sta_resume_source_02/fa_sta_resume.py`：16785 B，SHA `258da7f1f301d1f70c51fee9f5d213f1ee8a833d3cadef197cf0ce4226c8a074`，已核过唯一改名规则：原名以 `$` 开头才加一个字面反斜杠，其余原样。必须完整核对一一对应、无碰撞、目标集合完全相同，再仅将回读 cell 字典键反向改名，调用未改变的 `circuit()`。不能用删除字符、模糊名称匹配或仅比单元统计代替。

当前6236个名字全部以 `$` 开头，输入侧没有反斜杠美元名，适合该规则；**实际回读图仍待新执行核验**，不能把旧FA的双射 PASS 自动转授。原 JSON 与 split JSON 仍应首先严格相等，再核回读图。对新网表记录新 mapping/graph SHA，不沿用旧FA的6150cells、5196改名、954FA、1678DFF及旧graph SHA。

旧脚本的路径、原FAILED身份、上述 FA 计数和专有前置条件都写死，故“直接执行旧控制器”不成立。需要的适配只是固定新输入/结果身份、替换 FA 专属计数检查、复用转换和图函数、封装本候选两 feature 的既定流程。若这之外还需修图、手改网表或改约束，就已经超出本建议。

## 最窄执行与停止边界

建议先用 feature0 已有 mapped.json 验证同一种转换与 STA；失败即止，避免先做 feature1 映射。若通过，再完成原先未执行的 feature1 固定映射及同样转换/STA。新输出独立，旧 local-01/02 的FAILED和诊断报告保留；不重做已通过的算术/FU，不创建第三 Gold。

STA 的输入/输出路径可以替换，但反向替换须恢复原完整 TCL，库、1ns时钟、uncertainty、输入延迟/transition、输出负载、线负载模型和五类路径保持。新转换必须先无 concat-LHS、图检查通过，随后仍要求无 STA Error、完整路径和原常量端点检查；退出0和完成标记都不足以授予资格。

旧 FA 续接真实发生过30秒 STA 超时，只有 banner，故“转换方法已证明图相同”不等于“旧 OpenSTA 一定能完成”。本次保留一次固定的每步与总预算；建议继续使用30秒 STA 上限，超时、图不等、语法残留或任何错误就停止，不加时、不改第二种格式、不继续补丁。首次 feature1 映射次数单独记录，不能计成重映射既有 feature0。

如果两 feature 全部成本闭合，仅按实际面积及五类路径决定保留/回退；没有 >10% 整应用收益或 nominal 1ns 闭合保证。当前未核新续接控制器、未执行任何新转换或 STA，这份报告是决策建议，不是运行合格报告。
