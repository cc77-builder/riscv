# P分组候选：源码范围与最小验证建议

## 结论与本次审查范围

**所读源码未见阻塞性的Scala、分组消费或signed-row问题，可以按已有局部流程推进实际生成。** 最小而有力的算术方案是：原样复用成熟 `verify_csa.py`，对一份新实际生成CSA运行一次完整结构证明；另三份实际CSA必须与之逐字节相同。继续强制“无丢弃carry、raw row0[18]=1、raw row1[18]=0”。不需要再造算术校验器或重启此前超时的乘法SAT。

本审查只读取云端源、冻结合同和既有校验器，没有执行 `derive_source.py` 的main、Scala编译、SV生成、FU、EDA、PC或Pro操作；没有修改首席的source/controller。以下静态核对不授予新候选工程PASS。

| 审查输入 | 字节 | SHA256 |
| --- | ---: | --- |
| base datapath | 8,780 | `1d02d8a34772e7d9b9947f997f32465f3e946f4b24cacc66159eef7ee10ab3bb` |
| candidate datapath | 9,850 | `1f9a4c807b30b8aa769e65595ce6b54619b190a5f2b5af1d531413de9970b90c` |
| derive_source.py | 6,611 | `dbb3e6f1dfdff8efcf710fcf50482365bfa658b70348fd201ebba22fd0f009c8` |
| source-derivation.json | — | `b757bddd341c5dae1188b6a45a1a88ba32ed7b856864e4fbc6e503283b13a630` |
| base/candidate wrapper（相等） | 8,999 | `912c1a038ef8e9a1ac56cfa349161ae1c582d763acfce5352b08ebde2a227f92` |
| base PREFIX_CONTRACT.md | 9,048 | `22a4b7b6319f8c97a2f20a02e3c25237bce48d4fd77258ed54172547c493bf40` |
| 原verify_csa.py | 14,051 | `e6924e406792fe9e2b82f27be5a591b37466fb7b3ee23ec93935698934e397de` |

## 1. 新源码与派生脚本的静态结果

用Python AST只读取派生脚本的常量，独立重组候选字节并核对逆变换。candidate恰好替换base的唯一 `object VDotCarrySaveRows`；该对象之前的源码、R finish整个尾部及wrapper均逐字节不变，manifest中的before/after也与实际字节一致。未调用有写入作用的派生main。

局部逻辑核对：

- `HeapBit`只在Scala elaboration中保存name及两个Int分数，发出的wire仍只有原一位算术逻辑；没有引入RTL状态、时钟、复位或新的端口。位宽19、两条row、512项partial product及符号取反条件、列18/11修正常量、十个限高均保持。
- `old`排序以 `(compressorDepth, gateDepth, 原位置)` 为key，长度和多重集合不变；每次仅截取旧层尚未消费的2/3个bit，再调整所选组的pin顺序。`consumed += count`以及`old.drop(consumed)`来自同一个排序后的old，不会因二次pin排序遗漏或重复旁路bit。本层next只参与高度计数，未成为本层选择输入。
- FA按gateDepth升序安排x/y/z，z确实不早于x/y。`xyDepth=max(x,y)+1`；`zDepth=max(xyDepth,z)+1`同时是sum深度和carry右支AND深度；carry的OR输出 `max(xyDepth,zDepth)+1`与显式表达式一致。HA两输出深度均为 `max(x,y)+1`。这里没有常量折叠，符合首席声明，不应与先前包含折叠的模型当成同一实现身份。
- `.sortBy`的整数tuple、Vector/ArrayBuffer类型、非空selected的max、两分支返回Int二元组以及String插值，静态阅读未见明显Scala类型或语法问题。尚未经过真实编译，不把这句话写成编译PASS。
- 新private case class会增加辅助class。原控制器的完整 `rglob` overlay清单可覆盖它；应记录新实际清单，不能复用旧“23类”数量或旧class哈希。metadata分数不决定电路正确性，只决定分组；分数或深度预测误差不等于算术错误，但会削弱优化依据。

## 2. 对全部2^128二态输入能证明什么

每个CSA模块输入为两路64bit，共128个自由bit。原校验器完整解析实际SV，逐项识别512个partial product的lane/bit/符号，验证每对FA/HA的局部真值表，检查完整DAG、早层来源、列位权、修正常量和每根算术bit恰有一个去向。它**没有固定FIFO分组或x/y/z次序假设**，因而适用于新分组，无需修改校验器。

局部恒等式 `x+y+z = sum+2*carry` 或 `x+y = sum+2*carry` 对每个二态组合成立；在完整位权和唯一消费成立时可以组合为整个heap的恒等式，而不必枚举2^128输入。partial product之间存在相关性不妨碍这种证明：局部真值表证明的输入域更宽。

每个signed-byte堆的补码修正偏置为32,512；八个堆加列18/11的常量满足：

`8×32,512 + 2^18 + 2^11 = 2^19`。

因此，**若没有丢弃carry**，两个无符号输出行满足精确整数关系：

`row0_u + row1_u = signed_dot8 + 2^19`。

进一步核实raw `row0[18]=1`、`row1[18]=0`，才得到：

`signed19(row0) + signed19(row1) = signed_dot8`。

这一步不可省。单纯 `(row0+row1) mod 2^19` 正确，足以支持普通19bit收尾，却不足以支持feature1把四条row**分别符号扩到20bit再求和**。强整数不变量使两半的和范围为[-260096,262144]，在signed20内；已有Finish20对任意四个20bit输入的模和证明即可组合使用。MSB守卫针对raw CSA输出，不能误写成P寄存器在所有模式下恒为1/0；dot8模式下高半两row按既有wrapper逻辑置零是正常路径。

范围仍仅二态组合算术，不是X/Z等价、完整FU顺序形式化、真实时序、父级或整核资格。

## 3. 必须绑定到新实际生成SV的检查

| 检查 | 最小做法与原因 |
| --- | --- |
| 新源码确实进入受测模块 | 原overlay编译与cost/FU×feature0/1四次真实生成；保存全部class及实际SV身份。不能用Python预测文本代替Scala实际产物。 |
| 新CSA算术 | 对一份真实 `VDotCarrySaveRows.sv` 用原校验器运行结构证明；要求完整解析、`all_inputs_equivalent=true`、实际RTL SHA匹配、verifier SHA匹配。另三份CSA与该文件逐字节相同。旧CSA报告不能套用新SHA。 |
| 保住signed-row前提 | 明确另查 `discarded_carries=[]`、row0首项为literal 1、row1首项为literal 0。校验器本身允许模2^19意义上的高carry舍弃，所以不能只看其总PASS字段。 |
| 本次生成边界 | module/完整64+64输入及19+19输出、四消费者实例/切片/P捕获/高半mask，沿原检查；记录FA=477、HA=17、层0..9及完整row，核对固定限高源码不变。计数不是等价定理本身的必要条件，而是本次只重排输入的范围守卫。 |
| R、wrapper与消费边界 | 同一feature的新Finish19/20实际SV分别与闭合prefix局部的对应SV逐字节相同；wrapper与两个公共top优先做完整字节比较，资源表/filelist沿原精确成员检查。接口不变时没有理由新增宽泛文本归一化。 |
| 优化假设 | 如需报告“9层/22单位”，从新实际SV的DAG计算相应依赖统计，明示无常量折叠的模型口径。此统计用于检查优化意图，不是算术PASS条件，更不是PPA结论。 |

原完整结构校验器足以排除错列、遗漏/重复bit、非法新层carry消费、错符号取反、sum/carry输入不一致、错误carry等问题。无需另写一套大型解析器或重新做全部401项代码审计；校验器未改时，其既有审查与负例证据可继续说明同一checker的行为。

## 4. 复用什么，重跑什么

**可精确复用：**原完整C++/vectors/coverage/completion与identity/wen/high/cancel观察负控程序；原CommonFuCostTop、库、映射算法和五类STA模板；在新旧实际SV逐字节相等、旧PASS及原完整证据身份核实后，Finish19/20的任意输入模和SAT。这两份小SAT无需重复运行；结果写明 `reused_from` 及相同实际RTL SHA。

**本候选实际需要运行：**新源码编译与四消费者生成；上述新CSA结构证明；两feature原完整FU流程及观察负控分类；两feature同边界map/STA。FU可复用测试程序，不能复用旧PASS代替新二进制实际执行。保持原E0接收、E1转移、E2最早响应/无阻塞II1、stall/kill/reset、模式与异常路径的既有检查；不另造新时序或吞吐合同。

**此次局部筛选不需要：**新的乘法SAT、额外随机算术大扫、完整FU顺序SAT、父级长跑、整核或完整应用跑测。PPA若值得继续采用，再按已有项目合同补相应父级/整核阶段；这些阶段的旧PASS不迁移。局部结果中parent/fullcore/application/core-cost继续未授予，不以“代码只改组合逻辑”偷换范围。

**旧乘法miter记录尤其要分开。** 原CSA的 `UNKNOWN_EXTERNAL_TIMEOUT` 仍是该旧源码的历史结果；新分组CSA字节不同，其本轮独立乘法SAT应为 `NOT_RUN`，不能直接复制旧 `independent_miter` 对象造成新源码曾被求解的印象。可以另存 `upstream_independent_miter` 和原日志身份。新候选的算术依据是新实际SV结构证明；它不把旧UNKNOWN改成solver PASS。

保留本轮新源码、实际生成物、结构报告、FU与失败日志、map/STA及输入/终态pins即可。无需为了这项局部变化重建或重扫无关整核依赖，也不需要改变已经完成的代码交付。若新生成出现未识别语法或证明前提失败，应保留原件并定位原因，不能为取得PASS削弱原校验器。
