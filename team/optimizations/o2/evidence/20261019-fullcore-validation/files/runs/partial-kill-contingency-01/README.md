# PARTIAL_KILL 缺失时的最小定向备用方案

状态：**设计草案，未修改源码、未生成候选、未编译、未启动 EMU。** 本方案只在两份冻结补充镜像完成、完整验收后的覆盖合集中 PARTIAL_KILL 仍为 0 时启用。当前冻结控制程序仍可能命中该窗口，必须先让其正常结束，不能用前缀计数提前判定失败。

当前源码与相关文件身份见文末表及 source-manifest.json。硬件配置来自现有 core-02/hardware-pins.json，仅用于确认设计适用的结构；本次没有重新运行 EMU，也没有把该文件身份等同于新的实测结果。主任务转述的 dense/控制前缀计数属于调度背景，本文件不把它们当最终验收数据。

## 要修正的时间关系

现有程序把老 vdot v16 放在 scalar divu/bne 前，却没有使它依赖该 divu。老请求可能先完成；分支错误路径上的多个年轻点积随后占满两槽，得到 BOTH_KILL 而没有老幸存者。

备用程序把同一次 scalar divu 的商同时接到两条真实依赖路径：

    divu 的商 Q
      ├─ fmv.w.x → 首条 vfmv.v.f v8 → 老/年轻 vdot 的源 v8
      └─ L 条串行 addi → bne 的比较操作数

这样老 vdot 在除法结果产生之前不可能接受/响应。分支相对向量通路的偏移由短整数依赖链 L 调节，不再靠无关 nop/addi 改变偶然时序。目标是老 v16 在 R、唯一年轻 v20 在 P 时，真实父级 redirect 到达。

单个探针只保留一条老点积和一条年轻点积。两条目的不同、输入相同，不形成 vdot→vdot 数据依赖。这样减少“两年轻填满 P/R”的竞争；接受顺序仍须由真实轨迹确认，不能假定调度器必定按程序顺序接受。

## 真实硬件依据

- Parameters.scala:422–462：FEX0 的 F2v 使用 VfWB/V0WB port 3、priority 0；VFEX4 中 VDot/VIDiv/VFDiv 使用相同 port 3、priority 1。标量 divu 位于整数 BJU3，与 VFEX4 的向量除法不是同一个资源。
- VecDecoder.scala:737 与 DecodeUnitComp.scala:382–405：vfmv.v.f 分成 F2v 临时向量写回和后续向量操作。共享 port 3 的竞争来自 F2v 微操作，不能误称整个 vfmv 只有一个微操作或直接从 FEX0 写最终架构寄存器。
- WbArbiter.scala 按 priority 排序；RFWBConflictChecker.scala:114–132 的 RealWBArbiter 选择最前面的 valid 输入。因此 F2v 输出重叠时能压住低优先级 VFEX4 的真实 ready。此结构允许竞争，不保证程序执行时必然重叠。
- ExeUnit.scala 的 O2 admission 使向量 DIV 与 VDot 排他；本最小探针不加入 vdivu/vfdiv，避免向量 DIV 占用把整个点积窗口推迟。原冻结程序和其他 G3 作业继续承担 DIV 转换/取消验证。
- VDotElastic.scala：R 被阻塞时可保持结果，空 P 可接受一条新请求；两槽有效时若 R 老于分支、P 年轻于分支，则逐槽 needFlush 可只取消 P，R 同周期或稍后响应。
- MinimalConfig 的 ROB=48、VFEX4 队列=10；广播存在拆分微操作，故首先只使用最多 8 条广播和 1+1 条点积，不先扩大为长串数十条。实际资源占用和时序仍需 trace 确认。

## 最小探针骨架

以下为待实现的结构描述，不是已生成/编译的汇编文件。进入探针前恢复 32 个向量寄存器与测试 CSR；num、den、compare 预先从确定性表加载。

    divu t2, num, den                # Q，所有关键路径的共同晚到生产者
    fmv.w.x ft1, t2                  # 位搬运，非数值转换
    vsetivli zero,4,e32,m1,tu,mu
    vfmv.v.f v8,ft1                  # 首条广播：真正阻止老点积提前执行
    vfmv.v.f v24,ft1                 # B-1 条独立目的广播，B=8 时到 v30
    ...                             # 不覆盖 v8/v9/v16/v20
    vsetivli zero,8,e8,m1,tu,mu
    vdot v16,v8,v9                   # 唯一老请求，始终架构执行
    addi t4,t2,1
    addi t4,t4,1                    # 总计 L 条，每条消费上一条结果
    ...
    bne t4,compare,skip_young
    vdot v20,v8,v9                   # 唯一年轻请求
    skip_young:
    保存完整向量/标量/FP/CSR 快照，检查并有限排空

这里沿用既有合法 SEW32 的 vfmv 与 SEW8/VL8 的 vdot。不能在 SEW8 下生搬浮点广播；vset 之间的旧/新向量配置身份也须由实际输入字段核对。剩余广播与老点积同依赖 Q，可能在老结果进入 R 时继续争用 port 3，但若 B 条广播全部先结束，仍不会产生想要的阻塞窗口。

选取 Q 为有限单精度位型，例如 0x3f800001 + trial_index（限制在非 NaN、非 Inf 范围），den 为固定非零大整数，num=Q*den+remainder，0<=remainder<den 且 num<2^64。独立模型校验 num//den==Q。fmv.w.x 做 bitcast，因此 ft1 的完整 64 位预期为 0xffffffff00000000|Q；v8 完整 128 位为 little-endian Q 连续四份，不需要浮点数值舍入模型。长除法的实际延迟仍待测，不承诺固定拍数。

compare 表预先设置为 Q+L（不跳过年轻请求）或 (Q+L)^1（跳过）。每个参数点使用同一个静态分支 PC 的 24 个确定性 trial：前 8 次不跳过作训练，后 16 次为冻结的混合序列。训练只提高误预测机会，不当作误预测证据；若实际没有 redirect，先排查预测行为，不盲目加宽广播。

不要让 bne 依赖 v16 的提取结果：这会要求老点积先写回，反而消除“老 R 尚存时取消年轻 P”的目标窗口。不要把无关 addi 或 fence 当作等效的可调数据依赖。

## 小规模参数安排与停止条件

仅扫描两个主参数：广播总数 B、分支串行依赖链长度 L。先尝试 B=8，L=4/8/12，共 3 点。只在 trace 表明有必要时补 B=4 或 B=1 的相同 L，最多形成 9 点；B=1 也可用于区分纯时序命中与额外 F2v 竞争。每点 24 trial，架构点积提交数可由冻结分支表精确计算，不含任何推测次数猜测。

按完整 witness 决定调整方向：

- 分支先冲刷、年轻点积还未 ACCEPT：适度增加 L，检查两槽是否能装入。
- 老 v16 已在 redirect 前 RESPONSE：适度减小 L；若同时已有可见 STALL，则检查其窗口与 redirect 的距离。
- 老 v16 持续受阻，但年轻请求未入 P：检查输入 ready/valid、源 v8 就绪、VFEX4_WAIT、配置与调度压力，不能只增加 L。
- 广播全部先结束，R 没有反压：先用现有三个 L 判断是否能在无反压的短窗口命中；需要重排或新增参数时单独记录第二轮设计，不无限增大当前网格。
- 有 occupancy=2，但属于跨 trial 请求：先修复 trial 排空依赖并重新冻结输入，不把它冒称同探针老/年轻 witness。

单个参数点必须完整结束、DiffTest/全状态/全轨迹通过后才能贡献覆盖；不能发现一次 partial 后截断仿真并宣称通过。达到合格 PARTIAL_KILL witness 后停止扩展网格，保留失败/未覆盖点及原始日志。若 9 点仍缺失，如实保留缺口，依据真实时序再设计，不能降低原定义。

## 排空和全部状态验证

1. 每个 trial 保存全部 v0…v31，共 512 字节，按独立 Python 字节模型逐字节比较。v8 及 B-1 个广播目的为 Q 的四份；v9 保持初值；v16 必须为 signed int8×8 的低 32 位结果且高 96 位清零；v20 仅在架构不跳过时同样更新，否则保持完整 128 位哨兵。其余寄存器保持初值，包括未使用广播目的。高位故障检测负控沿用已有“翻转结果 bit127 应被拒绝”的思路，但作为新测试自身记录，不改黄金数据。
2. 汇编在调用 C 检查器之前保存 x0…x31、f0…f31 的原始快照。未修改的寄存器与入口快照逐位一致；受控临时寄存器按 num/den/Q/Q+L/compare 和已知指针偏移计算；ra/sp/gp/tp 保持调用约定，地址值使用入口指针关系，不伪造跨运行固定地址。ft1 为上述 NaN-boxed Q，其余 FP 寄存器不变。快照基址寄存器自身也保存其约定值，先保存再复用临时寄存器读取 CSR。
3. CSR 检查采用明确集合：vtype=0、vl=8、vstart=0、vlenb=16、vxrm=3、vxsat=1、vcsr=7、frm=0、fflags=0、fcsr=0。mstatus 只检查事先约定的权限/FS/VS 相关位，避免把硬件允许变动的 dirty 状态当常量。cycle/instret 只记录，不拿不同时间读取的数值作等值黄金。本方案不声称比较全部机器 CSR。
4. 全部向量存储后，从刚保存的 v16、v20 读取数据构造 drain token；下一 trial 的 divu 分子必须真实依赖该 token（例如与预期 token 相消后恢复下一行 num），确保上轮两个点积结果已可见再释放下轮关键链。不使用同寄存器 xor 归零等可消除依赖的写法。快照 compare 不应只依赖控制分支来推断已完全排空。完整结束时 analyze 仍须证明 P/R/DIV 均有限排空。
5. 精确提交数为每 trial 的 1 条老请求加“实际架构不跳过”的 1 条年轻请求。软件检查、NEMU DiffTest 和观察器 full128/身份/ROB/逐槽守恒分别成立，任何一层失败都不能纳入合格覆盖。新增程序要有独立源/生成物/镜像 SHA 和 manifest，不能改名冒充原冻结两镜像。

## 目标 witness 与验收边界

要求由原严格 analyze 重算，并额外保存可人工审查的同一 trial 窗口：

- ENQUEUE.pc/word 区分 v16 与 v20；ACCEPT 的 seq/rob/pdest 绑定各自真实身份。架构 vd 从指令字取出，不能把物理 pdest 当 v16/v20。
- 父级 VFEX4_REDIRECT 当拍，STATE.pvalid=rvalid=1，R 是该 trial 老 v16，P 是该 trial 年轻 v20。
- 依据完整 ROB flag:value 和 self 独立判定 killp=1、killr=0。O2_REDIRECT 与 VFEX4_REDIRECT 的一拍边界不能混用。
- P 有唯一 KILL，年轻请求不提交；老 R 同拍或稍后有唯一完整正确 RESPONSE，随后 COMMIT。被取消 P 不得再响应。幸存者同拍响应合法，不要求必须跨到下一拍。
- 同时保存 outready/STALL，说明窗口是否借助反压；仅证明 ready 受阻时，不在没有仲裁赢家证据的情况下断言某一条具体广播正是原因。

新探针只补充 G3 控制覆盖，不改变冻结矩阵、原 F2v 七项覆盖、正常恢复/负控等既有门槛，也不产生 G4 性能结论。只有原两补充镜像结束且合格 union 仍缺 partial 时，再由主任务决定是否实现本方案；本次交付止于这份设计。

## 读取身份

- 当前 Git HEAD：e2d9c063ac716665f4596bc95a806bd62a56d3a7
- hardware-pins 内硬件提交：b218cbc6e6b135e4ff219a902a9284a59d3c82c9
- hardware-pins SHA256：3752438404f544b9006c52b4234f5f05906b2de0fe4fbfa63c2006a30884dbf9
- hardware-pins 声明的 EMU SHA256：ac0123280bf6c742d27a7650505bc1d91db350d1519806edfd0be9c7ea208a57（本次未重新运行或重建）

| 相对路径 | SHA256 | 等于当前 HEAD | 等于硬件 pin |
| --- | --- | --- | --- |
| team/optimizations/o2/fullcore/workloads/generate_control.py | 209fb1f5a9231f047ae72004039c09e0a6e08026f1e55bc2bad47d6b5c14909a | 是 | 未列入硬件文件集合 |
| team/optimizations/o2/fullcore/workloads/control.c | 6b0f5ce7524f2a8e31d499f06aa12f66bfccafb9f0029060866500e715c5c8e8 | 是 | 未列入硬件文件集合 |
| team/optimizations/o2/fullcore/workloads/generate.py | 98a4bf8bc090ead18cd8cff8e1caa43a9f4821ed9e60b85e6a34ae9464c9df9c | 是 | 未列入硬件文件集合 |
| team/optimizations/o2/fullcore/workloads/main.c | a9e512ab496a136a5ba152684ca2627681af0b8268d32846c36a385eef17f733 | 是 | 未列入硬件文件集合 |
| team/optimizations/o2/fullcore/analyze.py | 27d9fe451c035157848625e84c2a229ac1d83073eb56ba3ebc25131e5569d496 | 是 | 未列入硬件文件集合 |
| team/optimizations/o2/fullcore/SCHEMA.md | 3f71ff3c4e4b83fc6744547a22b0f0eb450e3fbc2b8b2c12de8d493f7c3fe356 | 是 | 未列入硬件文件集合 |
| src/main/scala/xiangshan/Parameters.scala | 4ce4019b34a71bbc62c467c4209993e36ad63c29212c56f4bdf5e60faf2db907 | 是 | 是 |
| src/main/scala/top/Configs.scala | febd1212adf7b3c7069f378c0f54373e40ade36ee902e0d1cf63503c300d6fd2 | 是 | 是 |
| src/main/scala/xiangshan/backend/decode/VecDecoder.scala | 2ae12df34733075ab01fb012cb3a889ca36bb1cdde5e53ce72c9460e784cb3df | 是 | 是 |
| src/main/scala/xiangshan/backend/decode/DecodeUnitComp.scala | fd94a3008053b6bdf54da23adb5a7bced34bd6a74be42a5322c3b13f7be4b618 | 是 | 是 |
| src/main/scala/xiangshan/backend/fu/FuConfig.scala | 35cb5475c78a33a613ab70c30f443045473ae1b398062ed2f3799fd2068fea18 | 是 | 是 |
| src/main/scala/xiangshan/backend/fu/fpu/IntFPToVec.scala | 113be751fcbff240d41ac68a96c020dbeb231b5a6d0200d7f47194d097675fb4 | 是 | 是 |
| src/main/scala/xiangshan/backend/datapath/WbArbiter.scala | da263ea553f27a25cb9fc98c209138dffb700248a6ef5b64104bdc8abb5abbb4 | 是 | 是 |
| src/main/scala/xiangshan/backend/datapath/RFWBConflictChecker.scala | 7e361eeac818d69b3a910a84fbc499a60776925a0ebe5673c6488c30bef15f8b | 是 | 是 |
| src/main/scala/xiangshan/backend/exu/ExeUnit.scala | 166f70c704cc2ec477d316bc5d3ffb40498118e6f8c1c498209fc4b706070f1e | 是 | 是 |
| src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala | 20981203b19e57658c35ee76d134a1aaee918ce4c317d0f139df97c75460491a | 是 | 是 |
