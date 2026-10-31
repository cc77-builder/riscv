# P4-G1 真实父级测试材料

本目录是新候选的独立夹具与观察协议，旧 O2 测试文件保持不变。生成顶层继续使用真实 GenerateVDotElasticParent、ExeUnit、VDot、VIDiv、VFDivSqrt 和 ClockGate；这里不创建替身 DIV，不改父级生产 RTL。

## 新状态／观察合同

schema=2，所有普通记录采用 P4_PARENT 前缀。输入 VDot 在没有更早的 live P 且 R 可替换时直接写 R，否则进入 P；旧 P 搬移优先。真实握手、ROB 取消、原始占用、DIV busy/实际 ready、严格取消后闲钟均保持。新 direct_r/enqueue_p 字段分别表示实际新事务目标槽；旧 p_to_r 只表示旧 P 搬移。响应使用沿前 R 身份，绝无输入/P组合穿透。

C++以输入事务快照与独立P/R/DIV状态为预期，不以DUT的valid推导预期槽状态。完整128位三路写回、原始数学向量、ROB/pdest、VPU/perf整包、异常/写使能和浮点标志逐事务核对。Python check_trace另从身份/ROB和控制事件重放；它不包含数据载荷，不替代C++全宽验证。

无反压10022向量要求最早响应1拍、10021个接受间隔为1、10021次接收/响应重叠。尾槽排队或反压仍为不定延迟，不强求每条固定1拍。

## 运行覆盖

保留原测试的13组覆盖意图，并增加1组显式directR空队列接收、R响应与直接替换、R阻塞入P及满槽pop/move/push旧P优先。原冻结22定向＋10000随机向量、128合法/非法/v0混合、76整数DIV/REM、9 FP32 DIV、9×3跨FU切换、36 DIV取消、28 DIV ROB关系、14×2×3两槽ROB关系、8 VDot TE0 reset、12 DIV TE1 reset、20000随机周期以及严格取消后3拍闲钟检查均保留。

一拍候选正常沿后不会出现P-only，因此旧单槽立即/等待场景现在都覆盖R；“杀R、P活”仍由独立ROB年龄反转的双槽场景覆盖，不能删除。候选最短路径变更不代表所有DIV验证通过；真正SQRT/双lane偏斜见相邻sqrt包，必须实际运行。

## 负控

20类观察层负控：identity、rob、high、metadata、wen、stall、route、double、clock、occupancy、kill_p、kill_r、survivor、duplicate、missing、reset，以及 direct_identity、priority、zero_cycle、full_accept。负控仅修改C++看到的观察值，不是RTL故障注入。每类必须真实触发、exit1，并且日志严格只有匹配的INJECT/FAIL两行（新增两类附具体origin触发与非零seq）；PASS、escape、错误退出和额外垃圾全部拒绝。

P4_SQRT_AUX_ENABLED只用于补充编译，增加lane_ready/lane_finish/div_busy的只读观察及严格时钟检查；普通生成顶层和普通二进制不需要补充端口。父级API保留给sqrt包复用，避免嵌入第二份不同步的Bench。

## 当前资格与命令

准备阶段主机检查55项通过；尚未构建或执行硬件，不能从该结果宣称P4父级PASS。实际硬件由根Agent统一运行并记录版本/输出，防止并行重型构建。

    python3 -B -m unittest discover -s /absolute/g1/parent -p 'test_*.py' -v

实际生成/Verilator命令由根runner固定并留档。独立正向重放入口：

    python3 -B /absolute/g1/parent/check_negative.py --positive --return-code 0 --log /absolute/new/result.log
    python3 -B /absolute/g1/parent/check_trace.py --log /absolute/new/result.log --output /absolute/new/replay.json

不得把旧O2 schema1/two-cycle轨迹传入本检查器，或修改旧冻结检查器降低门槛。

修订记录：构建前收紧两类负控。priority在实际满槽pop/move/push沿捕获旧P seq，等待该seq的随后响应才注入；direct_identity依据实际directR接受时记录的seq触发。正向协议及覆盖不变，旧准备版本保留于本轮parent-agent/pre-negative-strengthening-01。

构建后负控修订：首轮P4真实父级正向及strict replay通过，但identity观察变异发生在已阻塞的R包上，先触发stability，严格负控类别门禁正确拒绝。保留该失败；identity/rob/metadata改为仅在非held的匹配R响应注入，显式full pop/move/push后旧P成为新R且后有P可保证触发。未改变正向协议、DUT断言或check_negative允许类别；新二进制须重新验收。
