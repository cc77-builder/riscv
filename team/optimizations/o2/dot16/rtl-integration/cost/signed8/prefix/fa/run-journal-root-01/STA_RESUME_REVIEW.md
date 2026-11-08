# FA 同一映射点有限 STA 续接：独立静态审查

## 结论

**未发现必须修改后才能执行这一次已冻结 STA 的静态阻塞。** 此实现显式记录一种完整、无碰撞的单元名称双射，仍使用固定旧 circuit() 核全部图字段；不是忽略名字、删除常量或改写旧失败。STA只消费已存在的序列化网表副本，不运行Yosys、ABC或重新映射。

本审查没有运行控制器、EDA或本机命令，也没有重新计算大图；它核的是当前代码、合同和云端既闭合输入记录。真实native plan-only和随后唯一一次STA仍各自保留实际回执，静态审查不授予STA成功或性能资格。

## 审查身份

- `fa_sta_resume.py`：16,152 B，SHA256 `efba4c76e503cc4319c6e3b04d8abcf6c5e28c6b7bd3373220228ed07605348f`。
- `STA_RESUME_CONTRACT.md`：4,065 B，SHA `8eca702338c12ac015d103e59350205753be755c408fb25d468b6d418138ad7b`。
- 被复用的 `fa_serialization.py`：13,071 B，SHA `82738e4ca6c0d84de04cb8a77e9143ab2d646bc025e087dddc3ff62a12109a8a`，本地身份与控制器EXPECTED相符。
- 只读核对 `sta-resume-actual-input/` 中的输入清单、原TCL、原序列化脚本及失败回执；未访问仍在运行的输出。

## 1. 完整图保持没有被缩减成统计比较

代码先固定原图、split图、回读图、已有Verilog及原circuit源码的完整SHA。原图与split图仍直接通过原 circuit() 比较。

名称规则仅为：原cell键以 `$` 开头时加一个字面前导反斜杠，其他名称保持。代码要求6150项、值无碰撞、值集合恰好等于全部回读cell键，5196项改名，并核整个映射SHA `9d8441a6457bb230eee9404f9c131e0c906aae00738ac2bb53d6ef49c04c41d7`。没有lstrip、任意模糊匹配或基于cell数量接受未知映射。

随后只建立 `renamed['cells']` 的逆命名副本，cell内容与net/port数据均不改变；原固定circuit()重新生成全部终端标签，仍比较cell type/parameters/所有方向与引脚位宽、top port方向/位宽/offset/upto/signed/位序、全部终端连接分区和0/1/x/z常量，并保留memory/process/init拒绝。完整图SHA还须为 `4bf4c350e4a464e4e875a4f32cb9b7e44f207f80b62bfe3fd0519de24ba32acd`。

这足以界定此显式双射下的同一已映射电路，而不是把先前原始名字比较失败重新写为通过。原两份FAILED及对应错误字符串均是执行前必核输入，新合同单独记录允许的唯一表示差异。`mapped_netlist_equivalence_tested=false`和不授原RTL到完整网表EQ的边界保留。

## 2. 输入继承、网表复制和TCL边界明确

静态对照实际10,190B序列化inputs（SHA `340ed65c…`）：15项EXPECTED与其49项originals、5项generated合并得到62条既有pin，**无冲突**；随后另绑定本次两份源。当前可见捕获元数据中的对应SHA也无冲突，固定STA、Liberty和两个helper身份均在继承集合中。代码先拒绝不一致的重复pin，再核全部文件，避免后写覆盖固定身份。

输入网表固定为2,177,588B / SHA `b1557c027795810779995e60032c3493fcb53d3f194a2cce76e516bad01d8e23`，只读入后复制到新 `sta-resume-01/mapped.v`，立即核完整SHA相同，没有对实际网表执行名称替换或重写。

实际原TCL含7处目录路径：一个read_verilog与六个报告输出。代码的7处检查与输入相符，替换后逆变换逐字恢复原TCL。原库、1ns、uncertainty/transition、I/O delay、load、wire-load及路径选择全部保持；没有替换单元或增加另一轮映射。当前源唯一一次显式外部工具调用是原OpenSTA。

## 3. 进程、信号与最终pin状态

原local-01和serialization-01的两个FAILED状态、精确错误原因、原命令序列、rc0/reaped/group_absent及旧进程组消失都在前置检查中。新输出须不存在；CPU3/nice5，一次STA上限30秒、执行段总60秒，原输入与其他运行输出分开。

STA子进程使用独立进程组；超时、错误或已锁存信号进入失败路径，finally按原helper清理并保存reaped/group_absent。成功还要求无STA Error/not found、唯一完成标志及五类路径存在，不以rc0单独判定通过。

输入pin在成功前逐项重查，finally又检查全部原/派生输入并记录changed_inputs；变化、不可读或已锁存信号会把状态置为FAILED。末尾只有最终状态仍为 `PREFIX_FA_BIJECTION_STA_COMPLETE` 才正常返回。未发现自动重试、加时或回写旧结果的路径。

## 4. 面积与五类时序的结论范围

面积从实际回读cell histogram与固定真实Liberty独立求和，要求无未映射单元、954 FA、1678 DFF和原完整端口边界。全图比较另外保留更完整的端口属性，不因对照表只列部分字段而丢弃位序检查。

五类R2R/I2R/R2O/I2O/ready均按原helper解析，常量警告按实际回读design核对；arrival与slack分别与原D1000基线比较。只有所测五类路径全部满足，结果才给该局部检查的nominal_setup_met，不将面积或单一路径改善转换成应用速度、核频率或完整ASIC PPA。

实际OpenSTA能否完成当前文本与report解析仍由这一次运行决定；若拒绝，保留新FAILED即可。本静态审查不要求额外预演或新增FU/core验收，也不建议在失败后自动放宽已有范围。

## 源02修正复核

**六组预算修正未发现新增静态阻塞。** 本节仅复核源02的计时与超时结果处理；前文是源01的历史审查，保持原文。源01确有总截止在前置核查后才开始、finally最终重哈希及落盘后缺少截止核对的预算缺口，前次审查未指出；源02补足这两处既有合同要求。没有重新审查完整图、改变STA点或追加工程验收条件，也未运行控制器、测试或EDA。

本次身份：

- `fa_sta_resume.py`：16,785 B，SHA256 `258da7f1f301d1f70c51fee9f5d213f1ee8a833d3cadef197cf0ce4226c8a074`。
- `STA_RESUME_CONTRACT.md`：4,353 B，SHA256 `f81ea953a7db24fe64d45925326359e9a0ae827eda018a8af3711ce4f282e3d5`。

只在内存中反向替换这六组预算改动，可精确恢复源01的16,152 B及SHA256 `efba4c76e503cc4319c6e3b04d8abcf6c5e28c6b7bd3373220228ed07605348f`。因此本次源码差异没有夹带图比较、网表、约束、工具调用或资格字段变更。

1. `overall_started`及同一60秒`deadline`现在在main入口、前置核查之前建立；execute分支不再于预检结束后重置。plan-only的deadline为None，但在所有截止比较前返回，不会产生None数值比较。
2. 原来重新起算60秒的位置改为核对已有总截止。若预检已经超过预算，代码在创建新输出和启动STA之前失败；预检用时不会被排除。
3. STA的`until = min(deadline, now + row['budget_seconds'])`在打开日志及Popen前确定，且不在Popen或首次结果写入后重新起算。子进程轮询、退出后核查及原回收路径继续使用同一上限，成功仍须STA在自身及总截止内完成。
4. finally完成全部最终输入哈希后记录入口起算的elapsed_seconds，并核total_budget_exceeded。此时超时会将状态写为FAILED；若本来已有异常，失败及非零退出保持，不存在异常路径恢复成功的分支。
5. 正常控制流在最终result落盘及恢复信号处理器之后再次核总截止；若落盘跨越截止，会另存FAILED和total_budget_exceeded=true。随后最终状态门禁拒绝正常返回。
6. 最终门禁只扩充失败说明文字，接受条件仍精确要求PREFIX_FA_BIJECTION_STA_COMPLETE。合同新增预算段与上述执行次序一致，没有放宽原失败、回收或输入不变要求。

上述结论限定为预算统计和成功资格判定的静态检查。失败后的必要回收及FAILED持久化仍可能晚于截止，不能把60秒成功判定预算解释为所有Python同步I/O可被到点瞬时抢占。本次没有新增运行或真实STA结果；源02的native plan和唯一一次实际STA应继续由各自回执说明。
