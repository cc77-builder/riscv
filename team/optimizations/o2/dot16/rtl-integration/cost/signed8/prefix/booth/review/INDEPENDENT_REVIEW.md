# Booth9 局部候选：独立 RTL 与 checker 审查

审查时间为 2026-11-08 05:13–05:18 UTC。范围为两份候选 Scala、两个派生脚本、source derivation 和 `verify_booth.py`；另由原生子助手独立推导算术、检查 wrapper 差分并运行轻量整数模型。未访问 PC/Pro，未执行候选生成器、Chisel、编译、EDA 或 FU 仿真；所有新增文件均在 `review/`。结束时六件被审文件 SHA 与开始时一致。

**结论：未发现当前源的确定算术错误或本次 checker 的假 PASS 缺陷，可以继续既定的实际生成及局部验证。** 当前结果是源码审查、独立整数模型和 checker 反例测试；不构成实际候选 SV、时序 FU、整核、应用或 PPA 资格。

## 1. 审查身份与派生

| 文件 | SHA256 |
|---|---|
| `derive_source.py` | `a6a28232c07ba54dd1a3390da584ef1cffcf158cba5e7090f26da76e9f025e02` |
| `source/VDotDatapath.scala` | `f0a8bbe58440c6113aa56f848387c6b4e4a487d71ec2832a1e43fca55d3a8245` |
| `source/VDotElastic.scala` | `0fcc5df10355ee1e6382678ba40bc9d7ddf830b560dcc469c46e6a6888441556` |
| `source/source-derivation.json` | `72b19ecbc899c0175c86a31e1032607b65897999c17117e2de21f21fac7c7eae` |
| `derive_verifier.py` | `9579bbd6d605b9bd123da7930a6e0b09faeb0223d1de985d5ccf68197461da18` |
| `controller/verify_booth.py` | `b3044e637a5f312b71497de1eaa44503e27894cb7fd313ee389208a8fc351dc5` |

source derivation 的全部编辑能完整逆还原 `prefix-pgroup-candidate-01/base/source`。新的 heap 和 P-row 保存方式是实际设计改动；R prefix 的整个源码后缀保持原字节。外部 128bit 接口、输入 byte halves 绑定、P/R valid/flush/control/perf、同步有效位复位以及 E0 接收/E1 推进/E2 最早响应、无阻塞 II=1 的控制语句未改变。数据寄存器仍未增加复位。

未执行派生脚本；通过读取 AST 中的文字块、固定父 checker 和派生规则，独立重建新 checker 字节，与实际 `verify_booth.py` 完全一致。其完整 SV parser、FA/HA Boolean 检查与 DAG 基础来自固定 `verify_csa.py` `e6924e406792fe9e2b82f27be5a591b37466fb7b3ee23ec93935698934e397de`。

## 2. 算术、位宽和关键边界

令 radix-4 digit 为 `low + mid - 2*high`。9bit selected/complement 保留独立 neg correction，翻转 row 的 bit8 后有 `unsigned(row) + neg = signed(a)*digit + 256`。其中 `a=-128,digit=-2` 时 row=511、neg=1，必须得到 512，再减偏置得 +256；若把补偿漏掉则错为 +255。

每 lane 的四个移位 row 偏置为 `256*(1+4+16+64)=21760`。八 lane 为 174080；加入 bit18、16、14、12、11 各一个常量，合计 350208，得到整半偏置 `2^19=524288`。因此两条 unsigned20 row 的模和编码 `S8+2^19`。

- feature0 保存每 row 的 low19，模 `2^19` 自动消偏置，真实 dot8 范围 `[-130048,131072]` 可精确作 signed19。
- feature1 保存完整20bit；dot16 两半各带 `2^19`，在 R20 中相消。真实 dot16 范围 `[-260096,262144]` 可精确作 signed20。
- feature1 的 dot8 必须在接收时保存高半 `(2^19,0)`。当前源正确；若误改成 `(0,0)`，全零输入就会输出 signed20 的 `-524288`。该错误位于 wrapper，超出只接收 `VDotCarrySaveRows` 的 checker 范围。

独立整数模型实际完成 2048 个单 digit 输入组合、256 个有符号 multiplier 分解、65536 个 signed8 pair 穷举，以及 1081 个八 lane heap 向量；每个向量核 feature0/feature1 dot8，并核 1083 个 dot16 组合含极值。各层按原源码规则消费旧层输入，实测模型形状为 288 FA、20 HA、8 层。测试通过，耗时约 1.04 s；这些是源码绑定的整数模型结果，不是生成 SV 仿真。

原始结果：`arithmetic/arithmetic-result.json`，4091 B / `48430b16886e56284ef391617aabae24c8581f5c6addb5339753e004d77d4a9c`。脚本：`arithmetic/check_arithmetic.py`，10317 B / `ccfa4dab5024659ffd9c57a79f84ddeb42a2a1ceeeb760312e6fd7ad57adc9aa`。

独立算术说明另见 `arithmetic/ARITHMETIC_REVIEW.md`，4673 B / `9c128dfc84b162fede1209c2506a5a73f1c61a44fe3df190717175b7ae111f71`。

## 3. Checker 证明链与真实反例测试

parser 消费完整模块，要求固定端口、全部声明/单驱动对应、无额外文本。全部 one/two/neg 以及 288 个 pp 的 AST 都严格匹配指定 lane/bit；仅对 lane0 穷举实际表达式不会遗漏其他 lane，因为其余 lane 已强制是同一表达式的精确 byte-index 替换。

FA/HA 各自检查完整 Boolean 真值表，输入必须来自更早层，所有算术 token 按权重恰好消费一次；常量 token 的列与数目固定。输出必须是完整20bit scalar concat。唯一可不消费的是 weight≥20 的 carry，符合模 `2^20` 结论；手工正确夹具实际无丢弃 carry。证明输出明确 `wrapper_binding_verified=false`、`sequential_fu_qualified=false`，没有将单模块结论升级。

运行 `python -B review/checker_fixture_review.py` 成功，直接调用固定 checker 的纯 `prove(raw)`。SV 均由独立 Python 手工生成并在 `checker-fixtures/` 明确保存，**不是 Chisel 生成物**。

| 夹具 | 实际结果/拒绝原因 |
|---|---|
| 正确 synthetic heap | 接受；7168 recode cases、256 分解、288 FA/20 HA/8 层、2384 局部 Boolean cases |
| 漏掉 `neg_0_0` correction | 拒绝：该 weighted token 消费次数为 0 |
| neg correction 移至错误列 | 拒绝：compressor arithmetic weight |
| 漏掉常量 bit18 | 拒绝：fixed Booth heap bias correction tokens |
| `pp_0_0_0` 的 vs1 lane 错绑 | 拒绝：exact Booth row bit/lane/sign |
| `neg_0_0` 改用错误 multiplier bit | 拒绝：exact Booth control expression |
| 漏掉 row bit8 反相 | 拒绝：exact Booth row bit/lane/sign |
| endmodule 后附加未知赋值 | 拒绝：extra module or text after endmodule |

共 1 个正例、7 个反例，均符合预期。原始结果：`CHECKER_TEST_RESULT.json`，7313 B / `cff768d85a5f658484aa16769a50efb51e9b0b5387b6376868f157268dbbb34b`；每份夹具的 SHA 与具体错误均在其中。测试脚本：`checker_fixture_review.py`，8163 B / `583c50518c5368677f129514e58a6e7fe4140822b2216d2ffebbd3a27fa6206a`。运行前后核 checker 源字节不变。

## 4. 对后续决定的直接影响

没有要求修复当前算法或新增诊断门槛。需要继续原计划已有的实际 SV 身份、wrapper binding 与 FU 验证：尤其低/高 byte half、feature0 截19位、feature1 存20位，以及 dot8 保存 biased zero。高半错误的数值反例不能冒称已被本单模块 checker 拒绝。

R prefix 源码相同是复用的依据之一；实际生成 SV 仍须满足原定逐字节匹配条件，才能引用原 R19/R20 证明。新 P 算术、wrapper 和顺序行为没有获得旧候选 PASS。能否采用仍由既定真实正确性及同口径 map/STA 结果决定，当前没有性能或面积收益数据。
