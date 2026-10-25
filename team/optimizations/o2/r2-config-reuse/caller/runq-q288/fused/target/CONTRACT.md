# 完整Q融合目标与受控比较合同 v1

合同 `r2-s3-runq-q288-fused-target-v1`，在首次本合同EMU之前冻结。继承固定T17单核、AM、原NEMU/flash、原四CSR计时/退休协议及既有高位负控转接；官方程序和RTL不变。该合同独立于acc8十Q诊断，不能把旧PASS转移到新融合入口。

## 范围与输入

完整288×288/GS32、预量化且预打包的Q投影，同ELF、同packed W/X/Ws/Xs及输出/槽地址。packed W是静态const数组，全部82944字节、两侧guard、所有golden、方法/顺序/指针表均绑定实际ELF并与冻结fixture核对；不在本合同执行或计时pack。只讨论一次指定方法selfwarm后的完整Q成本，不宣称普遍稳态、首次调用、量化、完整模型、token或ASIC收益。另一个合同负责pack证据。

五种方法为AV=原acc8+vdot，AR3=原acc8+RVV3（split_entries[4]），AR4=原acc8+RVV4（[5]），FV=新的完整Q融合vdot，FR=新的完整Q融合RVV4。原acc8完整机器体、全部六个整数叶、共同计时器必须与冻结ELF逐字相同；新两融合体必须与独立screen已验证的真实GNU ELF完整机器体相同，并重做整数核及完整地址/数值路径。

## 事前计划与全部计数

先做FV/x1、FR/x1、FV/x2、FR/x2四个非计时功能Q。其后两个固定块，所有warm和timed均使用x0：

| 块 | 计时顺序 |
|---|---|
| 0 | AR4、AV、AR3、FV、FR、AR4 |
| 1 | AR4、FR、FV、AR3、AV、AR4 |

每个计时窗严格执行公共prepare→同一方法完整selfwarm→完整结果检查→公共prepare→计时完整Q→完整结果检查。输入地址在warm/timed间不变；每种方法采用相同策略。AR4每块开头/末尾是共同锚点，**全部四次同时属于该方法的有效观察**，不能因role字段而从比较中删除更快的末尾点。其他方法各两点。

每个完成的正常进程或独立重放进程：12个timed、12个selfwarm、4个功能，共28 Q；AV/AR3/AR4/FV/FR分别4/4/8/6/6次。16个acc8 Q共5184次普通整数叶调用；12个融合Q内部执行3888个整数核；全部核心9072次。10个vdot Q共103680条custom，加隔离probe一条=**103681 COMMIT**。其中timed内custom只有41472，其余有明确阶段。48 COUNTER_ENQUEUE、48 CSR_SAMPLE；函数体FP逻辑元素convert/add各72576、mul145152。负控进程只要求预定失败前缀。

28次调用的stage/arm/dataset执行记录在结束后逐项输出并与固定计划闭合；完整自定义PC序列必须等于probe+每个既定vdot调用的真实ELF路径，覆盖功能、warm、timed，不能仅用窗口外“任意剩余提交”补齐计数。RVV非计时调用由独立DiffTest、每次准备/完整输出判定、冻结方法指针和执行记录共同见证，不虚称它们全部有T13计时窗退休日志。

## 正确性与证据

RNE，逐行g0→g8，严格signed int32转换、乘Ws、乘Xs、加sum；无FMA/重结合。每次Q都真实检查288输出全部位、最后一组8个完整128位槽、guard、全部context指针和vl/vtype/vstart/vcsr/frm；共8064输出和224个末组槽观察。功能首次调用后有5个真实判定破坏负例（输出、低32槽、高位槽、guard、context）且全部恢复。const packed的guard通过volatile读实际观察。

实际ELF地址模型约束只读输入、完整输出写覆盖、全部callee-saved与sp/gp/tp；新融合体的整数核须连续执行324次。对每个方法/dataset显式重做路径，各输入复用PC路径前须证明完全一致。共同split_measure机器体固定，marker到marker前后缀逐字固定，目标退休、4CSR值、模型指令数闭合；压缩ROB不允许隐藏branch/jal/jalr。所有UART留到整个批次末尾。

真实 `negative→recovery→replay`，三个独立PID，同BIN/seed；负控在首条隔离probe vdot的实际PC注入vd0 bit100并被原DiffTest拒错，随后方可恢复。正常与重放完整validation JSON须相同；重放不是额外统计样本。单EMU，总CPU≤4；每进程12M guest cycles、7200秒墙钟上限。任何正确性、退出、身份、路径、负控、重放或预算失败停止并保留，不加样本直至通过。

## 比较规则

先检查四个AR4锚点：`100*max <= 101*min`。不通过则`HOLD_CONTEXT_VARIATION`，只报告观察和正确性，不给性能优选。

软件融合的两项对应比较为FV对AV、FR对AR4。全局收益门槛为`200*max(candidate) <= 199*min(baseline)`，并列出每块结果；AR4基线必须纳入全部四点，每块用两个AR4中较快者。这0.5%是冻结研发决策阈值，不是比赛分数。

FV对强RVV集合的判定必须直接采用`200*max(FV) <= 199*min(AR3两点、AR4四点、FR两点)`；不能先按均值挑一个RVV再漏掉其他更快反证。报告全部观察及每种方法均值，但不把两个固定顺序观察称为统计显著性。上下文稳定且完整执行闭合后，才报告本计划限定范围内的收益；不自动切换稳定默认，不解除其他合同的HOLD。

计划内建议入口分别对AV/FV按同一全RVV最坏/最好分离门槛筛选，再在通过者中选均值较低者；不能先按均值挑vdot再漏掉另一条合格候选。若两者均未通过，则保留本次RVV集合中均值较低者。选项同时记录wrapper及leaf，因acc8三种方法共用同一wrapper。上下文门禁失败时不选入口。

该集合保留了已有不同caller中发生排序反转的RVV3/RVV4，并加入同样融合消费的RVV4；仍未穷尽全部六路Q。因此只称“本次纳入的强RVV集合”，不能写成击败所有RVV或全部应用性能。软件融合收益与vdot/RVV整数路径差异分别报告，不冒称新的RTL收益。
