# P2：当前0f依赖链轨迹的只读归因

状态：P2_CHAIN_OFFLINE_TRACE_ATTRIBUTION_PASS。只读取已资格的历史原始日志，**新增EMU/硬件构建/综合/STA均为0**。不是新性能测量。

## 输入身份与资格

原实验：o2-r3-div-gate-performance-20261025/campaign-01，after=0f12df675378556670afd0dd2153f47fcb330610；EMU SHA256 2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8。
原场景与当前计划相同：MinimalConfig、VLEN128、seed1、完整128位DiffTest，chain256、3数据集、每数据集4正式窗。当前源码相等由根的hardware-identity.json单独复核；不冒称本轮重新完成DiffTest。

先验证源归档manifest SHA256 9bda2d8c8ee254786ac8928588d3372b2b269bca89d6ec720eb1abf2c936be77；每份原始日志/历史结果/配置同时核对原路径哈希、归档payload哈希及gzip解压后的原字节。3个ELF/BIN、源manifest/kernels.S/main.c按旧artifact-pins逐字节绑定。全部选定输入前后哈希一致，完整清单见analysis-03/input-pins.json。

实际指令WORD=0x0295050b：v10 <- vdot(v10,v9)，唯一重复PC=0x8000114c。虽然manifest rows.operands列表的原始s1字段为8，chain生成器实际用目的v10替代s1；最终加载ELF及逐次完整128位输入确认真实自依赖。v10初值是固定poison；数据集改变v9，不把它称为3份独立A变化的GEMV。循环另含两个addi与一个bnez。

## 核心观测

| 间隔/计数 | 正式结果 | 解释 |
| --- | ---: | --- |
| 数据集 / 正式窗口 | 3 / 12 | 首次与预热另存，不混入正式统计 |
| 正式vdot / 相邻依赖边 | 3072 / 3060 | 每窗256指令、255边，不跨窗口配对 |
| ACCEPT→MOVE | 全部1拍 | 产品槽到结果槽之间的受控移动事件 |
| MOVE→RESPONSE | 全部1拍 | 响应握手时刻 |
| ACCEPT→RESPONSE | 全部2拍 | 当前FU实际已观测的接受到响应 |
| ACCEPT→下一依赖ACCEPT | 全部7拍 | 整核的依赖递推间隔，不是FU内部延迟 |
| RESPONSE→下一依赖ACCEPT | 全部5拍 | 聚合可观测区间，不能直接当作WB或单级延迟 |
| 下一消费者已在前条RESPONSE时分配ROB | 3060 / 3060 | 相对RESPONSE提前4～35拍；不能据此证明已进入目标IQ |
| RESPONSE→架构退休（边的producer） | 3048条为2拍；12条为5拍 | COMMIT不是RF写回，不能借这个字段声称WB耗时 |
| 正式完整计时窗 | 全部1857 cycles | gross，不扣开销 |

每个正式窗都严格分解为：

~~~text
1857 = 37（begin→首ACCEPT）
     + 255×7（相邻ACCEPT依赖间隔）
     + 2（末ACCEPT→末RESPONSE）
     + 33（末RESPONSE→end）
~~~

这给出明确的下一步筛选对象：两拍FU响应后的五拍“唤醒/选发/输送至下次接受”聚合区间值得结合静态RTL逐级检查；仅凭现有观察不能断言某一级浪费一拍，也不能证明缩短FU或更改latency参数安全。

## 绑定与错误拒绝

O2_ENQUEUE源码位于Rob.scala，实际表示ROB allocation，**不是IQ入队**。以整个日志的真实ROB allocation→ACCEPT→MOVE→RESPONSE→COMMIT生命周期追踪ROB flag/value代次，禁止ROB活跃重用。每次ACCEPT用seq/rob/pdest绑定MOVE/RESPONSE，并同拍核对真实VFEX4父级ACCEPT；COMMIT同PC/FTQ绑定唯一T13_RETIRE、word和count=1。
每个窗口4个真实CSR采样的时刻和值与原sample绑定，cycle/instret差值复算。全部256指令必须在对应窗口内，完整128位dot计算、固定v9、首v10初值和前条完整128位结果→下一条输入相等均检查。

15项主机测试通过：真实原文接受，加上丢响应、错误seq/pdest/ROB代次、响应bit100损坏、消费者高96位破坏依赖、错误opcode、父级接受丢失、架构退休缺失/计数错误、退休早于响应、窗口周期及原CSR篡改、初始manifest数据别名错误等拒绝。

analysis-01为首轮成功，analysis-02额外加强退休count=1；analysis-03依据源代码修正O2_ENQUEUE字段语义为ROB分配。三版数值相同，旧文件保留。test-01（14项）与test-02（15项）均保留，第三版只改结果字段标签与限制说明，没有修改算术/绑定算法。未发生DUT运行失败，因为没有启动新DUT。

## 边界

- 源观察器没有RF写回、调度器ready/select/issue或物理源寄存器编号事件；五拍不能仅凭此日志分成逐段实测。
- 完整数据链接与最终ELF证明架构依赖，不能替代缺失的物理psrc观测。
- 消费者已经分配ROB，只证明它已到达ROB分配阶段；不证明它已进入目标IQ，不排除dispatch停顿，也不代表就绪或赢得选择。
- 退休可以同拍多条，不能拿退休间隔当FU接受间隔或把COMMIT命名为WB。
- 若比较Jade，只能用其实际存在的RETIRE/CSR指标；没有Jade ACCEPT事件就不推导其FU延迟。
- 本轮只发出归因与候选筛选依据，不发布新加速比、面积、STA、功耗或Fmax，也不修改RTL。

## 重放本离线分析

~~~bash
python3 -B analyze_dependency.py --out <fresh-output-directory>
python3 -B test_dependency.py -v
~~~

固定输入原路径由脚本列出。迁移时必须另立输入映射并保持原哈希；不得把新的源码或日志替换旧路径。
