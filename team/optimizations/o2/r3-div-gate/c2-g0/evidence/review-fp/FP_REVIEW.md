# C2-G0：浮点 DIV／SQRT 双 lane 控制不变量审查

2026-10-25。范围：固定 0f12df6 与 C1 共享的浮点 FU 控制逻辑，只读源码／生成 SV，建立独立控制抽象和穷举机检。**未改生产 RTL，未重新构建、仿真、综合或 STA，未写 GitHub。**

**局部结果：通过。** 在已有效复位、按真实父级接收／取消协议驱动的 FP 子系统中，没有找到“父级 divBusy=0、浮点 FU 不 ready”的合法控制反例。此结论由细状态穷举得出，没有将目标不变量作为筛选状态的前提。它是 FP 局部控制抽象结论，需要主系统的整数／浮点互斥、ROB 和门控证明组合；不是全 RTL 形式等价或新候选动态回归资格。

## 1. 源码和生成物身份

共享源文件逐字节一致：

- src/main/scala/xiangshan/backend/fu/wrapper/VFDivSqrt.scala
- src/main/scala/xiangshan/backend/fu/vector/VecNonPipedFuncUnit.scala
- yunsuan/src/main/scala/yunsuan/vector/VectorFloatDivider.scala
- yunsuan/src/main/scala/yunsuan/vector/vfsqrt/fpsqrt_vector_r16.scala
- utility/src/main/scala/utility/ClockGate.scala

对应两份成本生成的 VFDivSqrt、VectorFloatDivider、VectorFloatDividerR64、fpsqrt_vector_r16、ClockGate SV 也逐字节一致。主仓 HEAD=0f12df675378556670afd0dd2153f47fcb330610，C1 HEAD=3be0e3d9e500bd1aa772bcc8d4f8b023a2877c66。所有输入路径及 SHA256 在 fp-control-result.json；脚本执行前后保护输入哈希一致。

进一步读取现行全核 build/rtl，核心状态转移正文与成本生成物一致，复位敏感表不同：

| 模块 | 成本 SV 的 FSM 正文 | 全核 SV 的 FSM 正文 | 复位 |
| --- | --- | --- | --- |
| VectorFloatDividerR64 | 1094–1109 | 744–759 | 成本同步；全核 always @(posedge clock or posedge reset) |
| fpsqrt_vector_r16 | 412–425 | 396–409 | 成本同步；全核 always @(posedge clock or posedge reset) |

去空白后的上述正文完全相同。原文、行号、完整文件哈希与敏感表在 quotient-result.json。该小范围比较不证明整个网表等价；全核生成物的封存清单绑定由主审查完成。

## 2. 固定实例的精确控制关系

### 2.1 顶层双 lane

VFDivSqrt.scala 20–28 行：128 位被分成两个 64 位 VectorFloatDivider。25 行用 fuOpType bit 0 选择 SQRT。57–71、86–87 行：

~~~text
每个 lane.start_valid = wrapper.io.in.valid
每个 lane.finish_ready = wrapper.io.out.ready AND wrapper.io.out.valid
每个 lane.flush = thisRobIdx.needFlush(io.flush)
wrapper.ready = lane0.ready AND lane1.ready
wrapper.out_valid = lane0.finish_valid AND lane1.finish_valid
每个 lane.is_vec = true
~~~

成本 VFDivSqrt.sv 174、182–183、254–267、274–287 行实际生成了这组连接。先结束的 lane 不能自行离开输出状态，因为所有 lane 收到的 finish_ready 必须等待两者均 finish。机检允许各 lane 任意不同的迭代完成时刻，并未假设同步完成。

### 2.2 每个 lane 内 DIV 与 SQRT 互锁

VectorFloatDivider.scala 33–59 行：

~~~text
sqrt.start = opcode_sqrt AND wrapper_valid
div.start = NOT opcode_sqrt AND wrapper_valid
lane.ready = div.ready AND sqrt.ready
lane.finish_valid = div.finish_valid OR sqrt.finish_valid
两者使用同一个 flush、finish_ready 和 reset
~~~

成本 VectorFloatDivider.sv 59、73、85–89 行与源码相符。进入父级接收时所有 ready 均为 1；仅选中 DIV 或 SQRT 启动，另一模块保持 idle。即便输入 opcode 在运行时变化，父级忙时 child.valid=0，因此不会再启动另一模块。这个无重叠结论是模型检查结果，不是预设目标不变量。

源码第 21 行残留“must false, not support sqrt now”注释与实际双模块连接不一致；不能用这个旧注释跳过真实存在的 SQRT 控制路径。本轮检查的是其控制结构，不宣称 SQRT 算术验证完成。

### 2.3 DIV 细 FSM

VectorFloatDivider.scala 149–161、174–224 行，编码为：

| 状态 | ready | finish | 正常后继 |
| --- | ---: | ---: | --- |
| PRE_0 | 1 | 0 | 无 start 保持；start 到 PRE_1 |
| PRE_1 | 0 | 0 | PRE_2 |
| PRE_2 | 0 | 0 | ITER |
| ITER | 0 | 0 | 未 final 保持；final 到 POST_0 |
| POST_0 | 0 | 0 | POST_1 |
| POST_1 | 0 | 1 | finish_ready 到 PRE_0；否则保持 |

有效 reset 或被采样 flush 优先回 PRE_0。

这里必须使用**固定向量实例**：VFDivSqrt.scala 71 行把 is_vec_i 恒置 true，VectorFloatDivider.scala 488、530–540 行在 start_handshaked 捕获它。因此源码中标量 early-finish、power-of-two 提前进入 POST 和 POST_0 输出路径在本实例不可达。成本 SV 1098–1109、1594–1595 行已常量化为上表；全核 SV 748–759、1829–1830 行相同。特殊值／非正规数仍可能影响计算数据与迭代条件，但不会绕过这组 ready／finish 控制。模型将每个 ITER 的 final_iter 当作独立任意布尔量，保守涵盖更宽的完成时长，不假定固定 latency。

### 2.4 SQRT 细 FSM

fpsqrt_vector_r16.scala 50–58、569–571、1479–1492 行：

| 状态 | ready | finish | 正常后继 |
| --- | ---: | ---: | --- |
| PRE_0 | 1 | 0 | 无 start 保持；start 按 need_2_cycles_init 到 PRE_1 或 ITER |
| PRE_1 | 0 | 0 | ITER |
| ITER | 0 | 0 | 未 final 保持；final 到 POST_0 |
| POST_0 | 0 | 1 | finish_ready 到 PRE_0；否则保持 |

有效 reset 或被采样 flush 优先回 PRE_0。

**更正上轮通用范围描述：** SQRT 源码虽然有 early_finish 分支，但 645–651 行明确在 vector_mode_i=true 时将它置 false；本实例 vector_mode 恒为 true。因此固定生成物没有特殊值直接从 PRE_0 到 POST_0 的早完成路径。成本 SV 412–425、804–805 和全核 SV 396–409、947–948 均支持上述表。模型保守允许两个 lane 独立选择初始化分支并独立完成 ITER，但没有把不可达的标量 early_finish 当成已测向量路径。

## 3. 归纳义务与为什么双 lane 不产生反例

FP 局部模型使用状态：

~~~text
(parentBusy, parentRob, childRob, div0, sqrt0, div1, sqrt1)
~~~

父级输入按现有源码约束：已有 busy、任一输出、整体未 ready、flush 或 reset 时不接受；收到请求才同拍保存 parent ROB 与 child outCtrl。没有用“busy=0 则 ready”筛掉输入或状态。

归纳路线：

1. 有效初始化后四个子 FSM 都为 PRE_0，父级 busy=0。
2. 接收时全部 idle，parent／child 保存同一个 ROB，两个 lane 同时启动相同子类型，父级置 busy。
3. 正常推进或等待时，选中子 FSM 始终处于非 idle；先完成的 lane 保持输出态，等待共同 finish_ready。父级 busy 不提前释放。
4. 两个 lane 都 finish 且外部 ready 时，共同 finish_ready 让全部选中子 FSM 同拍回 idle，父级也清 busy。
5. 父级匹配取消时，busy 期间整体 ready=0，因此 VFDivSqrt.scala 51–61 行选择已保存 child ROB；该 ROB 与父级保存值相同，所以所有 lane 收到匹配 flush。旧 hold 保留该采样边沿，子 FSM 回 idle、父级清 busy。
6. 无关 redirect 可以改变输入 ROB，但不会误取消正在用保存 ROB 的事务。没有新接收，身份也不改变。

模型的 redirect 使用对两个符号 ROB 身份的任意 kill 谓词，包括“都不杀／只杀其一／都杀”。这比特定 ROB 排序条件更宽，可以检验身份相等带来的取消一致性；它不能替代主系统对实际 RobPtr、flag、flushSelf、回绕的绑定。

## 4. 复位必须分开说明

两个策略分别完整穷举：

- **sync 成本／父级夹具策略：** 子 FSM 只有实际门控边沿才采 reset。已初始化在途 FP 使用旧 busy hold，reset 当拍 TE=0 也保留边沿。若删掉这个边沿，负控立即产生反例。
- **async 实际全核策略：** reset 直接清 parent busy 和子 FSM，无须门控边沿。模型按异步清除后父级 busy 已为 0 处理，不错误地依赖旧 hold；子 FSM 仍独立复位。

初始状态表示**已经发生过有效复位**，不是任意上电值。无有效 bootstrap、父级 idle 但一个孩子处于 ITER 的状态会立即违反目标；它被明确记录为边界反例，不能被证明结果隐藏。模型未验证异步 reset 的 recovery／removal、ICG 模拟毛刺或模拟电路时序。

## 5. 机检结果

fp_control_model.py 仅使用 Python 标准库；不运行任何 RTL 工具。

| 项目 | sync | async |
| --- | ---: | ---: |
| 可达状态 | 38 | 38 |
| 枚举转移 | 11,184 | 11,184 |
| lane finish 不同步状态 | 12 | 12 |
| DIV lane 阶段不同步状态 | 12 | 12 |
| SQRT lane 阶段不同步状态 | 8 | 8 |
| busy=0 但 FP 不 ready | 0 | 0 |
| busy=1 但全部 ready | 0 | 0 |
| 在途父子 ROB 不同 | 0 | 0 |
| 同 lane DIV／SQRT 重叠 | 0 | 0 |
| 跨 lane 操作类型不同 | 0 | 0 |

这些是有限抽象图中的状态／转移数，不是动态测试样本数量，也不能与过去 35,075 拍仿真相加宣称覆盖率。

本轮主动搜索并保留以下反例：

| 控制破坏／环境边界 | 最短反例深度 | 结果 |
| --- | ---: | --- |
| 取消时不送旧保持边沿 | 2 | 父级清 busy，子 FSM 仍忙 |
| 同步 reset 时抑制 hold、TE=0 | 2 | 父级清 busy，子 FSM 未复位 |
| 父取消、遗漏 child flush | 2 | 父子状态分离 |
| child ROB 捕获错误 | 2 | 对 parent 匹配的取消无法清孩子 |
| 任一 lane 完成便释放 parent，孩子仍按两 lane AND 完成 | 3 | 另一个 lane 仍在运行 |
| 未有效 bootstrap，父 idle／子 ITER | 0 | 初始目标即失败 |

前五项是模型故障注入，最后一项是明确的无初始化环境反例；**它们不是当前生产 RTL 的合法反例**。当前指定协议／复位域内没有找到合法控制反例。

## 6. 向主系统 I／R／O 模型的保守映射

映射：

~~~text
DIV: PRE_0 -> I; PRE_1/PRE_2/ITER/POST_0 -> R; POST_1 -> O
SQRT: PRE_0 -> I; PRE_1/ITER -> R; POST_0 -> O
~~~

商模型：I 收到 start 到 R；R 可保持或到 O；O 收到 done 到 I，否则保持。采到 flush／有效 reset 回 I；关钟保持。async reset 无需边沿。

check_quotient.py 枚举**所有合法细状态**及 start、done、flush、reset、clock_edge 的布尔组合，并覆盖 sync／async 策略：640 个输入组合、660 条具体后继的映射均包含在商模型后继集合中。该商模型允许比实际更多的 R→O 时机，因此只要主系统在这个更宽的模型中证明安全不变量，就不依赖精确迭代周期。

同时检查对应全核／成本的 FSM 正文相同、仅复位敏感表不同。注意这仍是手动源码映射＋机检包含关系，不是对全部生成 RTL 自动形式化提取的证明。

## 7. 接口、复现与接续

主系统可直接只读导入 fp_control_model.py：

- d_next(state, start, done)：DIV 状态编号 0～5，返回所有可能后继。
- s_next(state, start, done)：SQRT 状态编号 0～3，返回所有可能后继。
- 导入无执行副作用；两个函数只表示普通有效时钟边沿，flush／reset／关钟由上层处理。
- 文件已经冻结，主模型应记录其 SHA256。

命令与 exit 0：command.json、quotient-command.json。日志：model.log、quotient.log。完整输入身份／可达状态／负控轨迹：fp-control-result.json。细化包含与全核正文：quotient-result.json。

**接续条件：** 主系统需组合 INT、FP 与 VDot 排空、两个旧 hold／C1 owner 的门控关系，证明父级全局不变量及 P_j 与 fire_j 精确相等；确认实际全核异步 reset 身份，并决定 C2-G0 是否通过。即便通过，也仅支持后续候选合同；新 RTL 实现与真实回归仍未发生。
