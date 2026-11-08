# Booth3 增量算术与位宽审查

2026-11-08。只读云端候选与 Booth9 父源，未运行候选生成器、Chisel、SV、EDA、PC 或 checker 负控。**未发现本次三行 P / 三、六行 R 适配的确定算术阻塞。** 新 R 尚须使用自己的实际生成结果与新证明，旧两行／四行 SAT 不适用于整个新 R。

## 固定身份与完整逆变换

- `VDotDatapath.scala`：10266 B / `880ba4c2046721985560b788bf871cc69d930ebfe27561628ba7b930370ff680`。
- `VDotElastic.scala`：9181 B / `1bc162257ab7d53671a06b0d24015045026330c8680ee25dae482dbf7a316238`。
- `source-derivation.json`：18751 B / `202bc499e58ee12cac8986a65d2ec9a4e5ccd78b0e530370c22516b6edbac876`。

独立逆转11项新增 edits，每项匹配恰好一次，完整恢复 Booth9 的 `f0a8bbe5…` datapath 与 `0fcc5df1…` wrapper。继续逆转原5项 edits，完整恢复最初 prefix 基板的两份文件。derivation 的 false/required 字段与实际一致：整个 finish 源已改变，只保留从 `p0/g0` 开始的并行前缀网络后缀；需要新的三行／六行无约束输入证明。

## 算术及接口判断

Booth recoder、独立 neg、符号位反相与350208偏置的整个源区块逐字不变。P 仅删去最后 `limit=2` 层，保留三行；前七层及行内权重保持。因此三行 unsigned 总和仍为 `S8+2^19`，没有新增算术修正项。

wrapper 按低半0/1/2、高半0/1/2顺序连接新 R。feature0 为3×19位，逐行截取 low19；feature1 为6×20位。dot8 高半完整保存 `(2^19,0,0)`，第三行也在接收时明确捕获／归零，没有悬空或借用下一请求模式。

R 中每个3→2压缩使用 `s=a^b^c` 与 `carry=((a&b)|((a^b)&c))<<1`，只丢弃模W范围之外的进位，故 `s+carry ≡ a+b+c (mod 2^W)`。W19直接送该二行给前缀；W20的低／高3→2彼此并行，再依次压缩 `low_sum,low_carry,high_sum` 和 `cs0_sum,cs0_carry,high_carry`，完整覆盖六个输入，无重复或遗漏。每次 concat 都保持 W 位。

feature0 偏置模19消失；feature1 两个偏置模20相消。dot16 极值仍为 `[-260096,262144]`，signed20 足够。P 增加一行寄存数据，R 增加组合压缩；外部 FU 接口、P/R valid/ready、控制/perf、异常、flush、复位相关语句未改，也未增加寄存级。因此 E0/E1/E2 和无阻塞 II=1 的控制结构保持。57/120是源声明的 P 数据位数，不是实际映射后触发器计数或面积结论。

## 已真实执行的轻量整数检查

命令为 `python -B review/arithmetic/check_arithmetic.py`，退出0，约0.28秒。脚本检查固定源身份和两级逆还原，复用已穷举且本次逐字不变的 Booth 数学关系，独立重建七层数字堆与新 R 位运算；未执行被审代码。

| 检查 | 数量与结果 |
|---|---|
| 七层 P 堆 | 272 FA、19 HA，最终至多三行，无高位丢弃路径 |
| P→R feature0 dot8 | 1081向量全部相等 |
| P→R feature1 dot8，高半偏置零 | 1081向量全部相等 |
| P→R dot16 | 1083组合／极值全部相等 |
| 任意三个19位输入行 | 2132个有限样本等于模19总和 |
| 任意六个20位输入行 | 2897个有限样本等于模20总和 |

P 向量包含49个均匀边界、8个单 lane 激励、1024个固定种子随机向量。任意 R 行包含零／一／全一组合、每端口每位单热点和固定随机输入。该有限测试不是无约束 SAT，也不是实际生成 SV 的证明；结果记录明确 `fresh_sat_executed=false`、`old_finish_sat_reused=false`。

原始结果：`arithmetic-result.json`，SHA256 `c85996c5ed6324af6a08264cad4542abe80a0b7f1c7be3943e9b5eff4762683d`。测试脚本与结果仅保存在本审查目录，候选和旧证据未改。没有新增验收门槛；实际生成绑定、新 R 证明、FU 和成本仍由既定主线完成。
