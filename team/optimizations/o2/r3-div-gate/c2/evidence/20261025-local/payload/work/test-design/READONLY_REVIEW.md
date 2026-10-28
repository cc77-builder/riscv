# 冻结补充方案独立复核

审查范围：handoff.json列出的7个冻结文件。复核后全部SHA与handoff相同；未改任何.py/.cpp、未运行RTL或修改生产源码。

## 结论

可以进入真实构建/仿真。未发现必须先修复的数值oracle、端口方向、计数或取消相位错误。方案保留原13组/16负控作为独立验收前置；补充不能单独替代原完整验收。115场景、54取消关钟窗口、162即时关钟样本与循环范围一致。

## 核查依据

1. FP64非零subnormal的操作数是2^-1074，输出0x1e60000000000000的指数是486-1023=-537；平方严格恢复原操作数。9/3、FP32正常和subnormal也逐项成立。特殊值NV=16与RISC-V五位flags位序一致；负零保持符号。
2. 真实双lane偏斜取决于FP64初始化而非FP32。源码need_2_cycles_init在fp_format_i==2（SQRT内部编码，外部vsew==3）使用op_exp_is_zero_0；正常9与最小subnormal分别一拍/两拍初始化，其后相同13个迭代周期，所以两种lane位置能够产生相反的1拍finish偏斜。必须以实际aux观察为准；超时即失败，不能自动跳过。
3. c2Phase读取post-edge laneFinish才选择下一拍取消；取消当拍checker再次要求实际pre-edge lane_finish为1或2，避免捕获到此前一拍却已经完成汇合。
4. 原完整128位三总线、完整metadata、ROB/pdest及flags断言直接复用于SQRT数值与后续恢复事务。所有取消保持原有效取消边沿，紧接3拍无输入/flush/reset/TE且所有FU时钟为0。
5. 48取消包含12个真实偏斜相位（两方向各6）。ROB表中每相位3项kill，另6个窗口，总54个；54×3=162。
6. 18活跃TE0 reset各有首拍reset_drop=1，后一拍复位不得再次drop；两空闲场景drop=0。首次TE1 bootstrap是同步夹具约束，不是TE0冷启动证明。
7. instrument只驱动新增测试顶层output。真实生产模块由原始字节SHA锁定；SV/V唯一修改必须是测试顶层，实际仿真输入manifest在instrument之后生成。
8. 既有strict replay在require_campaign=False时仍执行字段/时序连续性、生命周期、ROB、输出一热、父子原子接受、ready、最低所需时钟、空闲多余时钟、守恒与终端计数。专用checker额外把非reset/TE时钟约束加强为每拍精确owner掩码，并逐拍检查真实divBusy下的ready不变量。
9. 新runner捕获实际补充Python/C++、原check_trace/test_trace及生产src、依赖、工具和所有命令。不能根据独立source等价或旧PASS跳过当前候选运行。

## 明确局限

- 当前仅草稿级语法、常量与源绑定检查；只有真实输出日志通过后才可写RTL PASS。
- 同步夹具只验证有效bootstrap后的TE0动态复位；真实全核异步复位域仍依G0源审查，下轮全核运行另验。
- SQRT只用RNE、精确正常数/subnormal与少量特殊值，没有系统验证所有舍入模式、非精确NX、NaN payload、全部FP16或尾掩码。
- 内部observer只读lane ready/finish，不读每个lane的内部结果寄存器；通过的是父级完整128位输出与身份，不能声称内部所有寄存器稳定性形式证明。
- 真实偏斜仅1拍；能检测汇合前误输出及偏斜取消，未声称覆盖任意长lane偏斜。G0抽象证明允许任意独立迭代时长，但那是不同验证层次。
- 补充checker的覆盖标签和C++驱动共同支撑具体case关系。它没有像生成器那样重新构造全部operand常量；数值证据依赖实际C++完整128位断言。日志本身不含payload，离线replay不是第二次数值仿真。
- reset engine标签、switch方向标签在C++生成器中固定。专用checker复核标签完整、SQRT存活opcode及总的事务一致性，但未针对“手工伪造一个内部自洽且错误标签的整个日志”建立密码学证明；实际运行的source/binary/log哈希与退出码是证据链必要部分。
- 七种新negative属于离线观察变异；原16负控也仅改变C++观察，二者都不是生产RTL故障注入或自动形式验证。

这些局限不阻止当前有界FU/父级阶段，但最终结果应如实保留；不因此扩大为全核、PPA或全部浮点正确性结论。
