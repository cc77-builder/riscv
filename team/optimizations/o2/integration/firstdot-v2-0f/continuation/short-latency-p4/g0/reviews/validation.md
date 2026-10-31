# P4-G0 独立验证合同审查

结论：**有条件 GO，仅允许下一轮获得用户授权后做隔离 RTL 原型、FU／真实父级验证与成本筛选。** 无需改变 FuConfig、提前唤醒、写回预留或 DIV 实际接收协议即可表达一拍候选；旧测试不能直接代表新候选通过。当前没有 P4 RTL、仿真、PPA 或全核性能资格。本轮仅查阅源码和既有证据，没有修改生产 RTL、编译、仿真、综合、STA 或 Git 写操作。

基线为保留的 0f O2＋H1＋DIV 取消关钟修复，不包括已否决的 C1/C2/C3。源码身份列于 summary.json。

## 1. 最小设计与配置边界

拟保留 P 尾槽/R 头槽、raw valid/occupancy，两个槽分别保存低32位结果和完整身份。乘法与归约成为输入组合逻辑；新输入在 !liveP && rReady 时直接写 R，否则写 P。旧 P 向 R 移动优先于同拍新输入。out.valid 只来自 liveR，新输入绝不能在接受同拍输出。

- 空队列/无反压持续流：E0接受、E1最早响应、II=1。
- 反压导致进入尾槽的请求可晚于一拍响应；保留 UncertainLatency()，不能为了“一拍”改成 CertainLatency(1) 或 piped=true。
- 默认关闭的编译期开关 VDOT_P4_ONE_CYCLE（拟议名）仅允许在O2条件下使用；非法组合生成前拒绝。不能放运行时选择MUX在关键数据通路，也不能通过环境变量把已有EMU变成新版本。
- 关闭新开关时，原O2及legacy/T14/O1的生产逻辑必须保留；以固定工具的生成功能逻辑/网表结构检查证明，仅不同模块命名、日志次序等非功能差异须单独解释。不能只凭Scala源码分支看起来相同宣称位等价。
- P4启用时，旧 O2_TRACE 在新全核观察器完成前明确拒绝，不能继续输出 latency=2/schema1 的伪旧轨迹。G1用独立测试顶层/观察合同；G3再做全核观察器。
- 编码、VLEN=128、8对signed INT8、高96位清零、非法配置与vec/v0禁写、ROB flag/pdest/完整VPU/perf、取消/复位、DIV互斥、真实ClockGate均不改变。

来源：src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala:28–34,57–74,82–107,127–146；FuConfig.scala:583–598；backend/exu/ExeUnit.scala:89–90,126–150,166–186,300–333。

## 2. 现有测试不能直接沿用的地方

| 位置 | 旧假设 | 候选要求 |
| --- | --- | --- |
| team/optimizations/o2/fu/fu_test.cpp:94–97,146,164 | tick+2推测P/R，首响应两拍 | 独立事件/事务模型，严格验证空队列E0→E1；不可删掉断言 |
| team/optimizations/o2/parent/parent_test.cpp:187–188,294–298,375–378 | 每次接受必写P；10022连续流overlap=10020、latency2 | 独立directR/enqueueP/move/response规则；一拍连续流理论overlap10021，按事件推导 |
| team/optimizations/o2/parent/check_trace.py:182–226 | MOVE方程及response≥2，旧状态更新必经P | 旧checker保留；P4独立schema/replay，不能只把2改1 |
| ExeUnit.scala:479–482,507,511,523–539 | ACCEPT写P seq、MOVE写R seq；schema1/latency2 | directR必须同边沿捕获新R身份/观察seq；明确输入目标槽，禁止伪造MOVE |
| team/optimizations/o2/fullcore/analyze.py:116–118,312–351,406–407 | schema1强约束、每响应先MOVE | G3独立适配并做负控；不在G1构建全核 |
| GenerateVDotElasticParent.scala:206–219 | raw P/R valid及实际全VPU/perf | 保留状态语义；父级门控不能改看掩码后的live occupancy |

观察只能反映功能，不能参与决策。新旧轨迹不应要求逐字节相同；相同请求序列应比较事务结果与终结类别，并独立验证各自周期合同。

## 3. G1 必须验收的覆盖

### G1a 独立FU

1. 原22定向＋10000随机向量及manifest不改；完整128位比较，包括符号边界、lane顺序、输入高半噪声、结果高96位零。
2. accepted-order队列与输入快照为独立oracle；逐笔校验data/exception/ROB flag和value/pdest/vec/v0/完整VPU/perf。非法请求占槽、仅终结一次。
3. 覆盖空队列directR、R弹出同拍directR、R阻塞新入P、满队列弹出＋旧P前移＋新入P、无新输入排空、满槽反压拒绝第三条。输入valid=false或blocked时持续扰动数据/身份，旧响应保持稳定。
4. 取消矩阵：杀R/杀P/两者/皆不杀；ROB年龄与接受顺序反向；flag边界/完整环绕、flushItself两值。redirect当拍禁新接收，kill优先于response，reset优先于kill。
5. 易漏角落：R杀P活仅在边沿移动，不能当拍偷出P；P杀R活且阻塞时R全包不变；无关redirect不撤回旧R；旧P移动与新输入同拍时不串身份。
6. 任意前缀接受＝响应＋取消＋reset丢弃＋在途，在途0..2；幸存响应有序；无幽灵/重复/遗漏。断言或oracle失败必须非零退出。
7. 无反压10022条：10021个II1间隔，所有最早响应1拍；尾槽/反压不强迫固定1拍。
8. 保留4类FU观察负控identity/wen/high/cancel，再补directR身份、旧P优先级、零拍偷响应、满槽误接收、reset重复终结反例；必须真实触发。观察值变异不是RTL故障注入。

### G1b 真实父级

使用真实 ExeUnit＋VDot＋VIDiv＋VFDivSqrt＋ClockGate，保持 GenerateVDotElasticParent.scala:18–45,225–251 的参数绑定/blackbox要求，不用替身DIV或常开钟。

- 保留原10022向量、128合法/非法/v0交错、76整数div/rem边界、9FP32 DIV/flags、9类FU切换×0/1/7反压、20000拍确定随机混合的覆盖意图；仅适配内部时序，不能让原场景在新时序下静默漏测。
- 父子fire原子且一子接收；子输出one-hot；三路完整128位写回相同；反压全包稳定。
- 任一旧VDot在途不得接DIV，最后响应/取消同拍仍不跨FU切换。DIV busy或物理out有效或未ready时不得接VDot，保留 divBusy || divOutValid || !divReady。
- 保留36组DIV取消、28组ROB关系/环绕；取消边沿必须给清理时钟，后续3个真空闲采样脉冲必须零；不新增grace窗口。
- R弹出后P活继续开钟，全杀边沿仍开钟，下一个真空闲才关闭；空/单/双槽TE0复位、取消重叠、恢复唤醒。
- 原DIV同步夹具reset用TE1，不得写成全部TE0已通过。
- 原16类父级观察负控保留，补directR/seq；原clock注入依赖move的触发条件需证明实际触发，不接受仅正向PASS。

### G1c SQRT和真实双lane补充

默认 parent_test.cpp:109–128,394–397 只有FP32 DIV。既有 r3-div-gate/c2/parent/ 的测试内容可迁入新P4测试目录，不导入C2门控RTL、不转授旧PASS：
15普通SQRT场景；48取消（双lane偏斜两方向×计算/一lane完成/双lane输出/反压四阶段×ready两值×三后继FU）；14ROB关系；20TE0动态reset/取消；18SQRT双向切换，共115场景标签。

**真实偏斜用FP64**：一个64位lane输入最小subnormal 2^-1074，另一个9，交换两lane，精确输出2^-537/3。TEST_CONTRACT.md:44 已证明FP32 vector初始化均两拍；不能用FP32 normal/subnormal混合声称偏斜。必须实际观察lane_finish=1与2，且指定取消边沿处于真实偏斜。原FP32 DIV四元素及flags覆盖另行保留。

SQRT oracle来自sqrt-oracle.json，正有限数用Fraction精确平方，特殊值验证canonical NaN/负零/正零/∞及flags，不用DUT或近似host sqrt自证。真实VFDivSqrt.scala:59–71,86–87规定两个lane ready/finish AND，单lane完成不能释放父级，先完成lane必须保持直到双lane与外部ready汇合。

C2 runner/checker仍绑定旧P→R模型；迁入前必须适配P4独立schema和0f的真实divBusy/hold，保留7类离线负控（busy、early-lane-join、opcode、TE、idleclock、missingaux、eraselanes）。有效TE1 bootstrap后TE0动态reset仅为同步夹具资格，不冒充全核异步reset电气签核。C2-G0控制证明本身不是SQRT数值RTL仿真。

## 4. 组合路径及归因风险

新输入组合路径为8×8 signed乘法→4×17位加法→2×18位加法→19位和→32位扩展/illegal零值→directR/P写入选择→寄存器D；ctrl/perf必须同实际边沿捕获，不能只压res而身份仍滞后。

后续分别报告FU/父级输入到P和R结果D、旧P到R D、ready、flush/ROB到valid/门控、结果Q到共享one-hot各输出。源码 ExeUnit.scala:635–638 的src普通连线没有内部寄存，父级MUX/缓冲和使能扇出不能从算术延迟推定。

BypassNetwork.scala:151–174 的dataSources(readReg/readV0/forward等)选择后，有 Backend.scala:645–653 的 NewPipelineConnect。候选不移动该边界，不能把整条上游旁路组合延迟机械加到FU输入，更不能把父级STA当整核Fmax。新选择和illegal MUX、门控输入须进入同约束真实父级筛选。

若必须改IQ提前唤醒、VFEX4写回优先级、FuConfig定时延或DIV接收协议才有收益，本最小合同NO-GO，应另立评审。

## 5. 分阶段停止线

| 阶段 | 门禁 | 未通过处理 |
| --- | --- | --- |
| G0本轮 | 源码可行性、组合锥、协议与未来量化筛选合同 | 只给条件GO，无新实测 |
| G1待授权 | 独立FU、真实父级、SQRT补充及完整负控 | 正确性/身份/取消/容量/门控/II1/最短1拍任一失败即停 |
| G2后续 | 同库同工具同约束FU和父级面积、五档STA | 超预设门槛即NO-GO或另立合同；不先跑全核掩盖成本 |
| G3仅G2后 | 新observer/parser、新EMU/NEMU功能异常与控制压力 | 新身份重新验证，旧0f资格不转授 |
| 性能/采用 | 同镜像custom/RVV、数据种子重复数测量窗，microbench与firstdot/C8适用集 | 1601只是模型，未解释退化不采用 |

上述为工程门槛，不是官方新面积/时序要求。本审查不产生新加速比/面积/STA测量。

## 6. 可复用命令与执行边界

以下现有两拍基线入口仅用于未来确需重验时；本轮均未执行：
~~~bash
cd /absolute/baseline/repo
python3 -B team/optimizations/o2/run_rtl.py fu /absolute/new/p4-baseline-fu
python3 -B team/optimizations/o2/run_rtl.py parent /absolute/new/p4-baseline-parent
python3 -B team/optimizations/o2/parent/check_trace.py --help
~~~

现有补充接口：
~~~bash
python3 -B /absolute/materials/c2/parent/run_c2_parent.py /absolute/repo /absolute/new/output
~~~
它使用旧状态模型，不可未经迁移直接验收P4。候选下一轮必须先建P4专用runner、C++/顶层、replay和manifest，再记录实际存在的命令；当前不虚构已存在的一拍验收脚本。未来最多一个重型构建，输出独立新目录，源码/依赖前后锁定，不覆盖旧证据。
