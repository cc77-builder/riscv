# Booth3 balanced-Gold02：新算术证明与 FU 完成，STA 解析失败

合同：`dot16-prefix-booth3-balanced-gold-v1`，2026-11-08 UTC。

**本次整体状态保持 `FAILED`。新 R19/R20 SAT、实际 P 结构证明以及两种 feature 的 FU/负控已完成；feature0 STA 存在解析错误，成本门禁未完成。** 不能据其报告宣布时序闭合或 PPA 改善。是否以成熟 serializer 和独立新合同续接仅 STA 工作仍在审查，尚未决定；本记录不作最终停止 P3 路线的结论。

快速入口：[原始结果](result.json) · [归档审计](audit.json) · [完整原始归档](raw.zip) · [STA 错误日志](sta-0.log)。

## 与 failed01 的关系

原 local-01 因 R20/6 SAT 超时而失败，原结果 SHA256 `7eb958143cc41f98cad195e0e7089b8924f827af340c51abca18ba573174d050` 独立保留为 `FAILED`。本次是第2种冻结 Gold 配方及新 operation，不是重放旧操作或改写原失败。

唯一证明配方变化是把 R20 的六项左结合加法改为 `(a0+a1+a2)+(a3+a4+a5)`。六个输入仍各为独立 unsigned20bit，完整120位输入自由，比较全部20位输出；没有 assume、偏置域限制、范围假设或缩减位宽。两种行为加法均计算总和模 `2^20`，括号变化不依赖“不溢出”前提。R19 Gold 仍为 `a0+a1+a2`。

两份 Scala、P checker、实际 DUT 与 public-top SV 均保持 failed01 身份；控制器逐文件校验新生成 DUT/top SV 与旧失败点相同。这里没有新的硬件设计改动，允许的 extern 模块声明注释顺序不改变逻辑。

## 本次已取得的证据

| 检查 | 实际结果 | 适用范围 |
|---|---|---|
| P 三行 Booth heap | 新实际结构证明 PASS；272 FA、19 HA、7层，无丢弃 carry | 二态128位操作数组合恒等式；7168 recode、256有符号乘数分解、2252局部 Boolean cases |
| R19/3 | 新 SAT PASS，命令0.067294 s | 57位自由输入、完整19位模和输出 |
| R20/6 | 新 SAT PASS，命令 **13.305540 s** | 120位自由输入、完整20位模和输出 |
| feature0 FU | positive与原检查器通过，4类故障均被识别 | 10022向量，31595周期，23327接收、22476响应 |
| feature1 FU | positive与原检查器通过，4类故障均被识别 | 10022 paired vectors，20124次合法比较、40次非法比较；53205周期 |

两项 R 证明均为本次重新执行，退出0、明确 SUCCESS、无反例/ERROR；未沿用旧2/4行或 failed01 的 R19 PASS。solver上限仍为30 s、单命令60 s。证据：[R19 日志](actual-prefix-19-miter.log)、[R20 日志](actual-prefix-20-miter.log)、[P 结构证明](arithmetic-structure.json)、[实际 RTL](actual-rtl/)。

四套 cost/FU wrapper 绑定均完成：输入低/高 byte half、feature0 的3×19bit P数据、feature1 的6×20bit P数据、dot8高半 `(2^19,0,0)`、R端口及架构输出匹配。128bit外部接口、同步有效位复位、两槽请求身份、停顿/flush/非法行为、E0接收/E1推进/E2最早响应和无阻塞II=1保持；数据寄存器仍由valid保护，不新增复位。

两个 feature 各执行 `identity/wen/high/cancel` 四类注入，共8个故意 exit1；对应8次原故障检查器均 exit0。全流程共32条命令：24条 exit0、8条故意 exit1，全部直接子进程已回收且进程组消失。FU证据包含背压、取消、复位和重叠接收；它不等于整核差分或完整应用验收。

## 为何整体仍失败

feature0 map命令完成，随后 `sta-0` 也返回0，并打印 `DOT16_GENERATED_FU_STA_COMPLETE`。但 OpenSTA 2.0.17 在 `mapped.v` 的42133、42134、42135、42139、42140行报告5处 `unexpected '{', expecting ID`，对应 concat 左值语法。控制器按原“完整且无错误的同模板 STA”门禁抛出错误并停止。

因此六份 `i2o/i2r/r2o/r2r/ready/setup-checks` 报告只作[失败诊断证据](diagnostic-feature0/)，其路径、slack和所谓完成标记均不用于合格时序比较。feature1 cost RTL已生成，但尚未进入映射/STA，`cost_results` 为空。Nangate45、ABC D1000及1ns约束是本次计划口径，没有获得完整成本结果。

原结果字段保持如下，不能把中间完成状态改写为完整流程资格：

| 字段 | 原始值 |
|---|---|
| `status` | `FAILED` |
| `arithmetic_proof_completed` / `fu_tests_completed` | `true` / `true` |
| `arithmetic_equivalent` / `fu_qualified` | `false` / `false` |
| `local_cost_recorded` | `false` |

上述顶层资格只在完整成功门禁之后置真；本次没有到达该位置。独立整体乘法 miter仍为 `NOT_RUN`，旧 `UNKNOWN_EXTERNAL_TIMEOUT` 仅作历史记录；本次使用实际 P 结构证明加新 R 模和 SAT。没有 whole-FU顺序等价、RTL-to-mapped等价、parent/core/application或物理PPA资格；生产默认未改，未启动新整核构建或运行。

## 时间、身份与复现入口

宿主运行：2026-11-08 **06:16:39.3868287–06:17:33.3099109 UTC**，工具记录53.884 s、exit1、cleanup complete；控制器内实际区间为06:16:40.282639–06:17:33.078245 UTC。运行 operation：`0250d6044ba18f5fd71831ae3131d2ce.44e4fedb9f67b246b0b7c84e9c9db68b`。见[运行回执](run-journal-02/run-host-final.json)。

| 冻结文件 | SHA256 |
|---|---|
| `VDotDatapath.scala` | `880ba4c2046721985560b788bf871cc69d930ebfe27561628ba7b930370ff680` |
| `VDotElastic.scala` | `1bc162257ab7d53671a06b0d24015045026330c8680ee25dae482dbf7a316238` |
| `source-derivation.json` | `202bc499e58ee12cac8986a65d2ec9a4e5ccd78b0e530370c22516b6edbac876` |
| `verify_booth.py` | `c0181c3c099a4a4e3ce4fcfcd1af3c34d337031675b6533ad303327ad632d587` |
| `booth3.py` balanced控制器 | `9ced0b6414e37af9369e7ae5793f3dc8d1b6cb0f6a2f3e38c003c36f688e7bcd` |
| `BOOTH_CONTRACT.md` | `be1bb568849c8d431c9df82b6fac4885d55865cc7bd5a657b9c535211631960c` |

实际 P SV为78845 B / `2ff5f11e28694d2b3bdfbb24303fc4dd5a0b47255c4daf24af0c8d3ee7256c4e`；R19为 `48c5946c60753e2aa9123ea5aef035214618327050e30ce895ba5e373fe2e691`；R20为 `bee47acb860892ca52e081750a29eb8668ecf7551b4e46404d68a5748c6a18e2`。

最小复现须恢复[inputs.json](inputs.json)指定的冻结源码、工具/库、classpath、原基线及 failed01 的结果/实际SV；同时恢复冻结的13件staged输入和[overlay-classes.json](overlay-classes.json)，在新隔离输出中依运行回执原 argv 执行。仅下载结果摘要不能替代这些依赖。资源固定CPU2、nice5、make-j1，内层总预算300 s、外层360 s；保持官方程序、原输入、旧失败点和生产默认不变。

## 归档与接续边界

归档 operation：`0250d6044ba18f5fd71831ae3131d2ce.2f53b935d68f250e1491eb0a4677b054`，06:19:52.5485689–06:19:55.8433629 UTC，exit0、cleanup complete。见[归档回执](run-journal-02/archive-host-final.json)和[audit.json](audit.json)。归档核验737项原始pins、全部13件staged输入及98项已记录产物；leader组35290与32个命令组均已消失。缺失的是未生成的最终成功manifest，未伪造补齐。

完整 raw包含 **237个payload、69,615,392 B原始字节，零遗漏**，成员SHA/CRC已核验；`raw.zip`为 **31,549,555 B / `c6c39781ab12f22a8608dc5f8752825b02f5e2bdec7ad8d4f24a6b80f9812e84`**。权威 `result.json`为132331 B / `63cee9334942c7e60405cef939ef3020b1817e5ee147cc7e12b22339884d9121`。

已闭合的算术与FU原始证据可供后续评估适用性；本记录和 failed01 仍分别保持FAILED。仅STA的serializer续接方案尚待独立审查和主端决定，若形成新合同，其输入、运行和结果须独立记录，本次无成本资格的状态不随之回写。
