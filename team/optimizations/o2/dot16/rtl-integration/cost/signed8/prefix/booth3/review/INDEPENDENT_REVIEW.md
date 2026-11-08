# Booth3 流水边界：有限独立审查

2026-11-08 云端增量审查，05:45 UTC 开始。仅核候选 source、派生记录和 `verify_booth.py`，执行独立轻量整数模型与 checker 输入变体；未访问 PC、主仓或 Windows，未执行候选生成器、Chisel、EDA、SAT 或实际 FU，未修改候选及父版本。

**结论：未发现当前三行 P／新 R 方案的确定算术、位宽、接口或逆向闭包阻塞。** 可以继续既定的实际生成、局部 FU、全新 R 证明和同口径成本验证。当前审查没有给予实际 RTL 或性能资格，也没有新增验收门槛。

## 固定身份与改动闭包

| 文件 | 字节数 | SHA256 |
|---|---:|---|
| `derive_source.py` | 9653 | `37f42bc92375810f046bcb12730c98cec8c4f8318cd46087811fcb6e47f1f37e` |
| `source/VDotDatapath.scala` | 10266 | `880ba4c2046721985560b788bf871cc69d930ebfe27561628ba7b930370ff680` |
| `source/VDotElastic.scala` | 9181 | `1bc162257ab7d53671a06b0d24015045026330c8680ee25dae482dbf7a316238` |
| `source/source-derivation.json` | 18751 | `202bc499e58ee12cac8986a65d2ec9a4e5ccd78b0e530370c22516b6edbac876` |
| `controller/verify_booth.py` | 17469 | `c0181c3c099a4a4e3ce4fcfcd1af3c34d337031675b6533ad303327ad632d587` |
| `controller/verifier-derivation.json` | 1333 | `e085ca5d3b32b43012c3acc9d488dc9c3de64cdf397ad674b2e4388aee6d3958` |

11 项新增 source 编辑匹配唯一，逐项逆还原完整恢复固定 Booth2 两份 Scala；继续逆用原5项编辑恢复原 prefix 基板。checker 的8项编辑也完整逆还原原 `b3044e…`。这些是实际字节比较，未执行派生脚本。

## P／R 连接与位宽

P 只删除最后一个 limit=2 压缩层，保留 limit=3 的三条 unsigned20 行。Booth recode、独立 neg 与偏置常量保持原源；因此三行模和仍为 `S8+2^19`。每层仍只消费旧层输入，新增 row2 有完整输出及接收时保存。

| 模式 | 保存与 R 输入 | 偏置处理 |
|---|---|---|
| feature0 dot8 | 3×19bit；逐行 low19 | 模19消去 `2^19` |
| feature1 dot16 | 6×20bit，低半0/1/2后接高半0/1/2 | 两个半偏置相加后模20消去 |
| feature1 dot8 | 低半三行；高半保存 `(2^19,0,0)` | 与低半相同偏置相消 |

wrapper 的行展平顺序与新 R3/R6 端口完全对应。R 先将每半三行分别压成两行；W19直接进入 prefix，W20将所得四行再经两级3→2得到最终两行。每个压缩满足 `x+y+z = sum+2*carry`，carry 左移并截为 W 位，故全链保持模W求和。低、高半首层并行，未引入寄存器、时钟或新增架构周期。

外部128bit FU接口、valid/ready/move/flush、控制/perf身份、异常路径和有效位复位语句保持。新增 row2 在同一个 `io.in.fire` 下保存，停顿时不会被新输入或模式改写；E0接收/E1推进/E2最早响应、无阻塞II=1的控制拓扑不变。名义 P 数据位从38/80增至57/120，不是综合后的实际触发器数。P减少一层压缩、R增加逐半3→2层，其时序及面积效果只能由实际 map/STA 决定。

**整个 R finish 已改变。** 保持原字节的仅为 `p0/g0` 之后的 prefix 网络后缀；旧两行／四行 SAT 结论不适用于新三行／六行入口。derivation 正确记录 `old_prefix_finish_source_retained=false`、`fresh_three_six_row_unconstrained_proofs_required=true`，本审查没有复用旧 PASS。

## 已执行的轻量验证

独立算术子助手只建立固定源方程的 Python 整数模型，退出0，约0.28 s：

- P 重建得到 **272 FA、19 HA、7层**，每列最终至多三位。
- feature0/feature1 dot8 各1081组、dot16共1083组及全局极值全部正确；dot16极值为262144和−260096。
- 对新 R 另作任意行有限测试：2132组三个19bit输入、2897组六个20bit输入，均等于模W总和。这不是无约束 SAT，也不是实际生成 SV 仿真。

算术报告 `arithmetic/ARITHMETIC_REVIEW.md`：3835 B / `0a855934f6b862751b87c07f6c37afdf2309d233e0afc51789d7b3f8decb4585`。原始结果 `arithmetic/arithmetic-result.json`：3084 B / `c85996c5ed6324af6a08264cad4542abe80a0b7f1c7be3943e9b5eff4762683d`。脚本 `arithmetic/check_arithmetic.py`：9029 B / `b8d4d43789fdd6dceec1b6e8050addc65e5b6f0b6723f319fef9b1bfb87cedad`。

主审复用上一轮固定的 synthetic checker 夹具，仅在内存调整输出接口、将一个既有 weighted token 从 row0移至row2。没有生成或实现候选 RTL；该夹具仍有原八层压缩，不用于证明新 P 的七层结构。

| checker 输入变体 | 实际结果 |
|---|---|
| 三行接口，第三行全零 | 接受 |
| 同权重 token 从 row0移入非零row2 | 接受 |
| 原两行接口 | 拒绝：端口不匹配 |
| 缺 row2 driver | 拒绝：完整声明/驱动覆盖 |
| 漏掉 row2 token | 拒绝：消费次数0 |
| 重复 row2 token | 拒绝：消费次数2 |
| row2 token移到错误位 | 拒绝：输出算术权重 |
| row2拼接只有19位 | 拒绝：必须完整20bit |

共2个正例、6个负例符合预期。checker 前后源字节相同，仍明确 `wrapper_binding_verified=false`、`sequential_fu_qualified=false`。原始结果 `row2-result.json`：10718 B / `c1bc3518c3d6fa2a94e4372f98d10275b39400496e56ba864c63fc2caf327e8c`；脚本 `check_row2.py`：4478 B / `668e826e4926a83faa5c0ca8fcd94176070d12f8d1ea6151d0856cfcbb7bc8db`。每个输入变体的 SHA 与拒绝信息均保留。

## 后续适用边界

未发现需要修复当前候选源码的具体问题。按根端既定流程，对实际生成的三行 P 运行新 checker，对实际新 R19/3及R20/6各作无约束输入的全新证明，并以新 wrapper binding/FU 核对保存与模式行为即可；本次有限模型和手工输入变体不替代这些原定工作。整核、应用和 PPA 均未获得资格。控制器由根端接续，本报告未扩展为控制器审查。
