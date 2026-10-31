# P4-G1 FU／SQRT 交叉只读审查

执行者：/root/p4g1_parent；时间：2026-10-28T16:55:48.694291+00:00。
范围：只读已冻结输入，不改任何运行源码，不编译、不仿真。结论：**未发现阻止根Agent启动局部构建的静态问题**；这不是硬件PASS。

## FU独立oracle

- 新pending队列以实际接受顺序保存请求、接受时刻与最早可见边沿，不依赖DUT占用推导预期。空队列/前头响应后直写R产生accept+1最早可见；尾请求只有前头终结后的沿才能提升，due至少tick+1。
- 头取消、尾存活时，取消当拍out.valid仍为false；尾只在下一拍从R可见。无关flush不撤回存活头，任意flush均禁止accept。两项与G0合同一致。
- 两槽满且无输出响应时in.ready=false；满槽pop/move/push后oldP仍在newinput前。direct分类用处理旧终结后队列是否为空，与保留oldP优先的P/R方案一致。
- 冻结10022向量逐条验证完整128结果，连续流每条都要求acceptedAt+1响应，10021个II1间隔及总10023拍；没有仅测第一条延迟。
- 负控均有可达实际触发场景：directRidentity在首条可见direct结果，priority在显式满槽三事件的旧P下一响应，zerolatency在空队列沿前，fullaccept在显式满槽阻塞，resetdouble在有在途reset。独立receipt检查要求schema＋匹配trigger/tick＋匹配FAIL和exit1；不能仅凭非零退出通过。
- 边界：FU扁平顶层检查部分VPU字段与两个perf tag；全VPU/perf整包覆盖由真实父级夹具提供。因此不要将独立FU测试单独描述为所有隐藏元数据位已遍历。resetdouble是复位时幽灵输出观察负控，不是RTL重复终结故障注入；前缀守恒和后续valid检查共同约束终结。

## SQRT补充

- 包含同一份P4 parent Bench，避免复制旧两拍状态机；schema2和direct_r/enqueue_p计数与parent replay匹配。instrument只改新生成test top输出端口及只读层次assign，其余生产生成物必须SHA不变。
- 15普通、48取消、14ROB、20TE0 reset、18切换合计115标签正确。普通模式已有10022与完整DIV；补充不转授C2硬件PASS。
- FP64 lane交换向量为2^-1074与9，预期2^-537与3；真实单lane完成由postedge laneFinish=1/2等待，并在取消下一拍preedge再核验。没有将FP32不同数据误当可靠物理偏斜。
- AUX每拍（包括bootstrap/reset）打印；断言仅在适当非reset区间执行。checker逐周期一一配对，不允许缺/迟到AUX，普通replay只关闭完整旧campaign库存要求，协议/身份/时钟规则仍执行。
- 所有SQRT取消均检查原子禁止新接收并立即3个闲钟关闭；与6个ROB取消合计54窗口/162样本。真实DIV busy/ready、双lane join与单lane不可外露都有独立交叉核对。
- 7项离线变异均需找到实际目标，完整正日志先通过才变异；它们是观察日志错误检测，不是DUT fault injection。
- 边界：动态TE0 reset资格来自已经有效TE1 bootstrap后的同步夹具，不能写成全核异步复位电气签核。

## 运行后仍必须核对

所有fault实际receipt、完整positive/replay资格、lane双向实际计数、源码前后哈希与独立生成物绑定均须由根实际运行得到；静态审查不提前授予这些PASS。如构建或运行失败，保留失败并先定位，不更改冻结输入。

## 审查输入 SHA256

- fu/fu_test.cpp：24510b2faf6442f63e7bdc08d6cbb13b2fa49c9bd3d5a580a5aab2906c3deb70
- fu/check_negative.py：e3079997e7740c190233b951c8c91bccacc835b3f2e86890cc0780c91a6604c9
- sqrt/sqrt_parent_test.cpp：6f85250d8f90e15a7f8c3eed4b687332b813008b14f4af4c4728262a8dd98825
- sqrt/check_sqrt_parent.py：c33396c99b455b7d00d9b54682816520ae3df13db085ab38c5949698ddbadc1d
- sqrt/negative_sqrt_parent.py：2737ccc3b878df2d4603205e14f2b6143a6a8240847dda208e7e16cde564d4bc
- sqrt/instrument_parent.py：f09c015cd71e0852f4fc7d424fef4c2fe94ff7e3694b241fff80c9f45c1809ea
- sqrt/sqrt_vectors.hpp：ccbf4ca34c44a5001ac0db1a53088ca252c919509e557750f6d5706a013aa62c
