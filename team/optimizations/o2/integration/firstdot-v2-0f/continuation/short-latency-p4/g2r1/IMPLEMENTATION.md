# P4-G2R1：R 元数据完整三路选择

父合同仍为 `p4-short-latency-g0-v1`；[R0 最小修订合同](../g2r0/REVISION_CONTRACT.md)不变。用户明确授权本地实现与验证，改前已说明文件/信号；不开展综合、STA、全核/NEMU或上传。

## 唯一生产修改

相对 G1，仅 `src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala` 的 `if (oneCycle)` 分支变化：

    holdR = !(move || directR)
    rPacket.ctrl := Mux1H(holdR -> oldRctrl,
                         move -> oldPctrl,
                         directR -> acceptedCtrl)
    rPacket.perfDebugInfo := Mux1H(holdR -> oldRperf,
                                  move -> oldPperf,
                                  directR -> inputPerf)

实际实现使用 Seq 和原 Bundle 类型，完整字段不裁剪。增加 `PopCount(Seq(holdR, move, directR)) === 1.U` 运行期断言；未增加有状态对象或新开关。

数据32位仍使用原 `when(move)/elsewhen(directR)` 写入，输出高96位清零保持。P槽、pValid/rValid、所有 ready、接受、取消、复位方程、DIV/SQRT/ICG及共享端口不改。旧P仍取沿前值；flush只阻断新接受，不阻断存活P搬移。没有在R无效时任意刷新或删除保持。

默认关闭 else 分支逐字保持，VDotO2.scala 未改。相对 HEAD 的总补丁仍含原 G1 两文件；本轮增量只含 VDotElastic.scala。不得把总补丁的两个文件都算成本轮改动。

## 复现入口

本轮重用原 G1 已冻结工具与 checker，使用新的独立目录：

    python3 -B tools/run_campaign.py <完整仓库> <预先建立并锁定输入的本轮输出目录>

本轮目录 `/home/riscv/riscv-lab/software-import-20261026/p4-g2r1-local-20261030-01`。入口依次执行候选FU、真实父级、SQRT、默认关FU、默认关父级，以及默认未设置和8项非法配置；每个子包重新生成、编译实际二进制、运行正向/负控。继承工具的状态字仍是 P4_G1_LOCAL_RUN_PASS，外层通过源码manifest与新输出归属为本轮，不是借用旧二进制。

资源串行、CPU4–7，mill/Verilator make各2 jobs；配置与依赖由每个run/env.json、dependencies.json、commands.json固定。Issue#2只读至6511950608，队友tailrows叶位于不同工作区且保护CPU0–2；本地启动前无旧重任务。不发Issue消息、不推送，未使用受保护目录。

工具与模型数据保持，22定向＋10000随机向量及manifest未重新生成；prepare_vectors只将既有数据转为本轮TSV，SHA256仍为901a7be30e62b81bcd3df55b20538a5ba9c879ba9c7c34f28b8c0421d8e6a327。

## 收尾检查与资格

`tools/verify_local.py` 核查445源码、313冻结分析/测试/历史输入、五个实际二进制/生成物、正负检查退出码、事务守恒、旧正向日志逐字相等、默认关生成逻辑以及配置拒错。`tools/review_generated.py` 专门检查新表达导致的父级生成物传播差异。两个工具都不启动综合/STA/全核。

默认关 HDL 使用原 G1 严格规范化：只规范化 Scala 断言行号，LogPerfEndpoint 限无输出/恰3条带条件fwrite的JVM编号与调用顺序。不能宣称原始HDL逐字相同。候选主动改变元数据表达，其生成图不要求与G1相同，也不声称形式等价。

证据中保留完整结果、命令、版本、配置、依赖、所有正负日志及新二进制哈希。负控是观察/日志破坏，非物理RTL故障或形式证明。新的面积、STA、程序cycles/加速比一律NOT_TESTED，后续按原G0门槛另行筛选。
