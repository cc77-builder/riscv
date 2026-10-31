# P4-G1 两份RTL与父级oracle独立只读审查

审查者：/root/p4g1_fu；时间 2026-10-28T16:56:42.744031+00:00。未修改任何冻结材料或RTL、未启动生成/编译/仿真。当前源码哈希列于末尾。

**静态结论：未发现功能阻断问题；生成物、真实运行及负控资格必须由根Agent实测。** 不能把本审查当RTL PASS、形式等价或时序结论。

## RTL逐项

| 合同 | 审查 |
| --- | --- |
| 默认关闭与严格0/1 | VDotO2.scala:5–8,13–17,35–40；未设置/0关闭，1要求O2；任何其他值报错 |
| 非法组合 | P4要求O2/T14，排斥O1及T12/O1观察；P4与旧O2_TRACE不兼容，T13也不能绕开该限制 |
| 编译期而非运行时MUX | oneCycle是Scala Boolean；if(oneCycle)在展开时选择，不增加运行时模式信号 |
| 原两拍分支 | VDotElastic.scala:123–136，与修改前的状态/数据赋值块去注释和空白比较完全一致；reduce在false分支仍来自pProducts |
| 一拍组合算术 | 83,100–103：同一份Products→Reduce，pResult低32；非法incomingResult置零；旧符号扩位运算模块未改 |
| 两槽/优先级 | 102–120：directR=fire&&!liveP&&rReady，enqueueP其余接受；旧move与directR互斥；旧P优先R，新包仅更新P |
| 完整身份 | 107–120：P/R的ctrl和perf与各自data同沿保存；同时move/newP时R读沿前旧P，符合Chisel非阻塞时序 |
| 异常 | 60–61,88–95,101：合法性不变，两个写使能受illegal抑制，异常包照常排队、非法结果零 |
| 输出128位 | 73–77：只来自R寄存器，低32＋高96零，无输入或P组合穿透 |
| 取消/复位 | 62–72,105–106：匹配kill先屏蔽live；任意flush/reset禁新接受；killR且P活只在沿上move；reset使两valid清零 |
| 反压 | rReady/pReady公式不变；R blocked时move/directR均不能覆盖R；保留原全包heldResponse断言 |
| raw占用与DIV | 56–58仍输出raw P/R；父级生产ExeUnit/DIV未改，不得把更早清槽误解为同拍跨FU接收 |
| 配置 | 类中继续要求piped=false/UncertainLatency、128位目的、Vec/V0类；不引入CertainLatency或早唤醒 |

## 必须由生成/仿真回答的两点

1. pProducts在P4分支仍有声明（43行），但不被读取，也没有赋值。它是为保留旧生成路径所留的无效对象。本审查不假设FIRRTL必定接受/消除；需实际elaboration成功，并检查候选生成VDotElastic中不再存在pProducts保存组。若初始化检查失败，应采用不影响关闭分支的条件声明，而不是把无用128位寄存器接回功能通路。
2. 去注释/空白后的旧else块一致只证明局部代码保留；关闭模式的完整生成物/结构相等仍须实际比对。源码中变量作用域/自动命名可能影响生成文本，不能宣称逐字等价已通过。

## 父级oracle审查

父级C++以自身p/r/div Pending为状态，先检查DUT真实槽位（184–188），计算每槽ROB取消与live/ready（190–194），并校验parent-ready、child-fire原子性和实际输出owner（224–248）。接受只在已核对ready后取DUT fire；该顺序不构成“拿DUT错误ready自证”的明显漏洞。

directR/enqueueP（236–238）及沿后事务顺序（311–329）符合冻结合同：先终结取消/响应，旧P移R，然后新包依directR选择R/P；满槽pop/move/push不会把新输入覆盖旧P。随后核查沿后真实p/r/occupancy（349–355），下一拍对完整data/ctrl/perf核对旧P身份（250–287）。这一正向检查能发现实际RTL把新包错误放到R。

**可改善的负控语义：** 当前名为priority的负控在 r&&p&&inf&&of 的当前周期对旧R的dest翻位（260行），实际上证明的是满槽重叠时“当前R身份错误能被发现”，并未单独触发“沿后R错误选择新输入而不是旧P”的错误。建议full-triple沿先armed，下一拍旧P响应时注入；或明确该负控覆盖边界。本子任务FU priority已在oldP被满槽重叠提升后的响应上严格注入。此问题不推翻父级正向oracle，但不应把旧父级负控包装成已专门验证next-R选择。

direct_identity当前在R无P且同时新dot接受时翻旧R dest，主要验证directR替换重叠不污染旧响应；空槽新包的第一次R身份由正向包快照和FU directRidentity负控补充。

物理DIV ready/out使用真实子单元观察是既有variable-latency协议所需；不会由P4改变。其独立数值、busy恢复、时钟及SQRT双lane验证仍须实际执行。

## 来源哈希

- src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala: d542b29ee384042a6cdfd11d073271aa5a7f8f4f6c3d630516d6fc46ec6eff87
- src/main/scala/xiangshan/backend/fu/wrapper/VDotO2.scala: e15e394fb48b04752da9993e1cd8054a414146c3bac2c38343f431e208f1aba4
- team/optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g1/parent/parent_test.cpp: 34dfb6ba3cf1f9f3ada94912e3a3b2b5489e86964ce686fa0b96c1d01396099e

旧else块去注释/空白对照：PASS。没有改动冻结FU测试材料。
