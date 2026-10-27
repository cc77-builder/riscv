# C2 真实父级补充测试合同建议与补丁说明

状态：DRAFT_READY_FOR_ROOT_APPLY。以下为测试草稿，不是 RTL 验证 PASS；未改生产源码，未启动硬件构建或 GitHub 写入。

## 1. 与原验收矩阵的关系

原 run_rtl.py、parent_test.cpp、13组正测、16项观察负控和原严格replay保持原样。原FU层22+10,000完整128位数据及4负控仍须对C2候选实跑。

本补充使用同一真实GenerateVDotElasticParent/VFEX4，复制既有C++ scoreboard形成独立c2_parent_test.cpp。同一完整结果/三写回总线、ROB/pdest、VPU/perf、异常/flags、反压稳定、生命周期守恒逻辑用于新增事务。仅新命令 --c2 进入六组补充campaign。原test函数保留作为审查参照，新runner不重复运行它，也不借其历史结果宣称新候选通过。

## 2. 最小可执行矩阵

| 层次 | 必须完成的运行 |
| --- | --- |
| 主机门禁 | 原FU/父级负控与strict replay单测；本补充Python AST、C++ syntax、数值常量精确核对 |
| FU | 新候选原runner fu：22定向＋10,000随机完整128位，原4负控 |
| 真实父级原套件 | 新候选原runner parent：原13组、原16负控、严格逐拍replay |
| 真实父级补充 | run_c2_parent.py：六组、下列115个定向场景与逐拍验证 |
| 补充门禁负控 | 在真实补充正日志上做7种离线观察变异，均须被拒绝 |

六组包含：
1. TE=1有效bootstrap；之后所有动态复位与正常运行TE=0。
2. **15** SQRT数值场景：5组向量 × 0/1/7拍反压。
3. **48** SQRT取消场景：两种真实双lane偏斜方向 × 计算/仅一lane完成/两lane输出/7拍反压 × 外部ready两值 × 后续三种FU。
4. **14** SQRT ROB场景：7种同龄不取消/新老关系/flag边界/完整wrap × 计算/反压。
5. **20** TE0 reset场景：整数DIV、FP DIV、SQRT × 计算/可见/7拍反压 × 与匹配取消交叠两值，共18；另加空闲两种交叠。
6. **18** SQRT切换场景：VDot/整数DIV/FP DIV三个peer × 两方向 × 0/1/7拍反压。

115为场景标签数，不是全部事务数；场景内包含恢复与唤醒事务。六组里的bootstrap不计115。

## 3. SQRT的源绑定与精确结果

VFDivSqrt.scala中opcode=fuOpType(0)，VectorFloatDivider.is_sqrt_i接它；opcode=1确实启动真实SQRT引擎。opa接vs2；vs1故意填非正常比特，验证不会作为平方根输入。VectorFloatDivider.scala的旧“not support sqrt now”注释与实际连线不符，不作为测试依据。

数值表：
- variant0：FP32的4、9、16、25 → 2、3、4、5。
- variant1：FP64 lane0最小正subnormal 0x0000000000000001即2^-1074 → 精确结果2^-537即0x1e60000000000000；lane1的9 → 3。
- variant2：交换variant1两个真实64位lane。
- variant3：FP32的-1、-0、+0、+∞ → canonical qNaN、-0、+0、+∞；NV聚合标志16。
- variant4：FP32的2^-148、2^-146、9、25 → 2^-74、2^-73、3、5。

所有正有限结果用Python Fraction逐位解码，并验证result^2 == operand，共12项（sqrt-oracle.json）；不使用host sqrt、target RTL、近似误差容忍作为oracle。特殊值依据当前实现的canonical NaN和flags规则；真实执行仍须验证。

**真实偏斜必须用FP64。** fpsqrt_vector_r16.scala:652–654对FP64用exp==0选择两拍初始化，正常数只需一拍；而FP32 vector模式恒为两拍，不能用FP32 normal/subnormal混合声称制造偏斜。先前FP32-only草稿未被运行，保留sqrt-oracle-draft-01.json仅作草稿历史。补充必须观察lane_finish=1和2两方向，且48取消中的偏斜相位实际取消当拍必须观测1或2。

## 4. 只读观测与完整输入身份

instrument_parent.py仅对新生成的VDotElasticParentTestTop.sv加3个顶层output：
- io_fp_lane_ready[1:0]：真实两个VectorFloatDivider的start_ready_o。
- io_fp_lane_finish[1:0]：真实两个VectorFloatDivider的finish_valid_o。
- io_div_busy：真实ExeUnit中寄存的divBusy，不能用组合occupied替代。

层级绑定检查实例名及真实net存在且唯一。脚本保存测试顶层原文，并对全部生成SV/V逐文件计算修改前后SHA，要求唯一改动是测试top；生产ExeUnit/VFDivSqrt/整数/SQRT模块须字节一致。runner在插入观测后生成正式generated-files manifest，再编译；所有观测仅作层级读，不驱动生产信号。该测试网表不用于面积/STA。

原严格trace schema1不扩展；补充额外输出逐拍C2_PARENT_AUX。专用checker先移除aux并执行原check_trace(require_campaign=False)（仅关闭原13组覆盖要求，状态/ready/clock/ROB/守恒检查仍全开），再校验：
- aux与cycle严格一一对应；
- 真divBusy与已接受身份一致，!divBusy => intReady && fpReady；
- wrapper ready/valid分别等于两个lane的AND；
- 每拍只有预期owner时钟开放（非reset/TE）；
- 两lane偏斜不得产生父级输出/结束；
- 54个取消事件后紧接3拍全门关闭，共162样本；
- 六组完整覆盖集合、TE0 reset与取消交叠、SQRT接受/存活opcode、真实偏斜两个方向。

negative_c2_parent.py在正日志上做7个独立离线变异：busy归属、提前lane汇合、SQRT opcode、把TE0 reset标成TE1、空闲多余时钟、缺aux、抹去lane偏斜。它们验证门禁敏感性，不能计为RTL故障注入。

## 5. 执行与适用边界

将以下5个文件放入候选专用模块目录：c2_parent_test.cpp、instrument_parent.py、check_c2_parent.py、negative_c2_parent.py、run_c2_parent.py。由主Agent在原FU/parent完成、同仓编译器空闲后顺序执行：

~~~bash
python3 -B <module>/run_c2_parent.py /absolute/candidate/repo /absolute/new/output
~~~

输出必须新建并位于仓库外。runner保留环境、工具版本、source/dependencies、生成物SHA、原测试top、观察修改证明、真实命令/退出码、正日志、独立replay、7个negative结果。源manifest覆盖补充所有Python/C++以及实际check_trace/test_trace。

本夹具仍是同步reset，因此首次TE=1有效初始化是合同前提。之后的TE0 reset验证只证明已bootstrap后的动态复位；不能冒充真实全核异步reset电气签核。未做全核、NEMU、周期性能、综合或STA；不根据本补充通过就采用C2。

## 6. 当前草稿自检

- Python AST：通过。
- C++ g++ -fsyntax-only：通过，使用旧真实生成header副本，只增加3个观察字段；无RTL执行。
- 第一次syntax由于错误/usr/share/verilator include路径失败，原记录保留；第二/三次改为实际/usr/local/share/verilator成功。
- instrument smoke：在旧生成物副本上通过，仅测试顶层改变；原冻结目录完全未写。
- Fraction数值常量：12个正有限精确平方关系通过。
- **尚未执行新补充RTL；最终以真实run日志为准。**
