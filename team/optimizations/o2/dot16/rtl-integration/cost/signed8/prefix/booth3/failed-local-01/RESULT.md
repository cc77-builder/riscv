# Booth3 原 local-01：R20/6 SAT 超时失败记录

日期：2026-11-08 UTC。合同 `dot16-prefix-booth3-local-v1`。

**原 local-01 已以 `FAILED` 闭合。** 实际 P 结构证明及四份生成wrapper绑定完成，新的 R19/3 无约束输入证明通过；R20/6在固定30秒solver限制内未完成证明，工具返回1。记录没有发现算术反例，也没有证明R20/6等价。按原合同，FU及成本阶段未执行，Booth3未取得整体算术、FU或性能资格。

本入口只描述这次原始 `dot16-prefix-booth3-20261108-main/local-01`。任何后继配方与执行另立身份，不修改、覆盖或重新解释本次FAILED原件。

## 已完成与未完成的实际证据

| 部分 | 原 local-01 实际结果 | 适用范围 |
| --- | --- | --- |
| 编译与生成 | overlay编译和cost/FU × feature0/1四次生成均exit0 | 生成成功，不等于FU或成本测量完成 |
| P结构证明 | `BOOTH3_CSA_STRUCTURAL_EQUIVALENCE_PASS`；272 FA、19 HA、7层 | 实际三行Booth堆的组合算术关系 |
| 四份wrapper绑定 | 两态cost/FU的输入半区、P捕获、偏置零、R连接、非数据更新与架构输出检查均通过 | 实际生成物的静态绑定，未进行本次动态FU验证 |
| R19/3新SAT | PASS，exit0；命令耗时0.067273秒 | 三个无约束19位输入的模2^19组合求和 |
| R20/6新SAT | FAILED，exit1；solver timeout，未证明、未发现反例 | 六个无约束20位输入的证明未闭合 |
| FU / mapping / STA | 未运行；`fu_results=[]`、`cost_results=[]` | 没有本次FU、面积、DFF、时序或PPA结果 |

实际P检查解析整个模块，核7168个recode情形、256个signed-byte分解、FA/HA布尔恒等、层间依赖、权重与唯一消费，建立每半区全部 `2^128` 个二态操作数输入的关系：

`(row0 + row1 + row2) mod 2^20 = (signed_dot8 + 2^19) mod 2^20`。

记录没有丢弃carry；该证明不覆盖X/Z语义，也不代替新R或完整FU证明。实际P模块为78,845 B，SHA `2ff5f11e28694d2b3bdfbb24303fc4dd5a0b47255c4daf24af0c8d3ee7256c4e`。

本候选设计为每半区三条P行：feature0保存3×19位，feature1保存6×20位，feature1 dot8高半在接受时保存 `(2^19,0,0)`。契约保持128位架构接口、上升沿时钟、同步高有效valid复位、P/R两弹性槽，以及无阻塞E0接受/E1推进/E2最早响应、II=1。**这些契约与静态绑定不构成本次动态延迟/吞吐验证**；源声明的P位数也不是实际综合DFF计数。

## R19通过与R20超时的原始判据

两份R均为本次真实生成的新模块，旧两行/四行R的SAT结论未复用：

| 实际模块 | 字节数 | SHA-256 |
| --- | ---: | --- |
| [VDotPrefixFinish19.sv](actual-rtl/VDotPrefixFinish19.sv)，3个输入 | 1,325 | `48c5946c60753e2aa9123ea5aef035214618327050e30ce895ba5e373fe2e691` |
| [VDotPrefixFinish20.sv](actual-rtl/VDotPrefixFinish20.sv)，6个输入 | 2,031 | `bee47acb860892ca52e081750a29eb8668ecf7551b4e46404d68a5748c6a18e2` |

[R19完整日志](actual-prefix-19-miter.log) 为6820 B，SHA `be715c2eccdd3a8ceed48f74a59fc6a80a428db0b522352f91db7f6c2963f3f1`，明确记录 `SAT proof finished - no model found: SUCCESS!`。result中的 `solver_equivalence_proved=true`、`counterexample_found=false` 与日志一致。0.067273秒是整个证明命令区间，不是硬件时延。

[R20完整日志](actual-prefix-20-miter.log) 为6396 B，SHA `957987acdcf4a9a90f8762444b0bad0c65b4618b19cf7e563201fb99094486a8`，明确记录 `ERROR: Called with -verify and proof did time out!`。本次solver上限30秒、命令预算60秒；命令实际区间为31.043164秒，exit1。`solver_equivalence_proved=false`、`counterexample_found=false`：**没有反例不等于已证明，超时也不等于存在算术反例。** 原配方未重试。

因此 [result.json](result.json) 保持 `arithmetic_equivalent=false`，表示整体算术验收链未完成，不是发现了算术不等价。`fu_qualified`、`local_cost_recorded`、`parent_qualified`、`fullcore_qualified`、`application_performance_qualified`、`core_cost_qualified` 均为false；没有名义1 ns闭合或任何面积/时序改善结论。此前单体乘法miter的历史UNKNOWN及本次该miter的NOT_RUN也不补充R20的证明资格。

## 执行失败与正常回收

[run-host-final.json](run-journal-01/run-host-final.json) 的host起止为 **05:55:17.658444–05:56:10.0856108 UTC**，记录执行时长 **52,387 ms**，exit1、`cleanup_complete=true`、`timed_out=false`、`cancelled=false`。内层result区间为05:55:18.602090–05:56:09.870936 UTC，CPU affinity `[2]`为单核，nice5。

**host外层没有超时；超时发生在R20工具内部的固定solver限制。** 工具返回失败后，控制器按原判据停止下游。共8条实际子命令，7条exit0、R20一条exit1；全部reaped/group_absent=true。唯一exit1属于本次证明失败，不归类为预期负控。

本次候选datapath SHA为 `880ba4c2046721985560b788bf871cc69d930ebfe27561628ba7b930370ff680`，wrapper SHA为 `1bc162257ab7d53671a06b0d24015045026330c8680ee25dae482dbf7a316238`。result为 **110,068 B**，SHA `7eb958143cc41f98cad195e0e7089b8924f827af340c51abca18ba573174d050`。resident、原cache及生产默认未改；新增整核构建与运行均为0。

## 失败原件归档

[raw.zip](raw.zip) 为 **1,549,236 B**，SHA `3c1a56a5f6ccef535fcc9531bc661962649e3a333290f22a4b8ed02bd2edd085`；包含 **129个原始payload文件 / 4,985,867 B**，省略文件数为0。

[audit.json](audit.json) 为1755 B，SHA `5af285f6d6c03215358a8a9080b1de1a3f79e2481b1b66a68a8fb615fc154a64`，状态为 `BOOTH3_FAILED_ARCHIVE_VERIFIED`。审计记录成员SHA/CRC通过、源未变、715项原始输入pins、23份准备输入及94项已记录产物pins核验通过，全部记录进程组不存在；归档期间0新增EDA、0新增guest、无重试。

**`missing_final_success_manifest=true` 如实保留。** 94项已记录产物核验和129文件零省略不替代缺失的最终成功清单，也不把原运行改写为成功。归档完整性只针对这次失败时保留下来的证据；后续研究必须引用或保留该失败记录，另建结果入口。
