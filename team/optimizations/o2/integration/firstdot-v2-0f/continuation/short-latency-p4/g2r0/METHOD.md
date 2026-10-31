# P4-G2R0 只读分析方法

输入为 G2 固定原始目录 `/home/riscv/riscv-lab/software-import-20261026/p4-g2-cost-20261030-01` 和原 Nangate45 Liberty；无需网络、编译器或 EDA 执行。本轮输出目录为 `/home/riscv/riscv-lab/software-import-20261026/p4-g2r0-readonly-20261030-01`。

运行如下命令时，--output 必须用新文件名，脚本拒绝覆盖：

    python3 -B tools/analyze_readonly.py \
      --g2-raw /home/riscv/riscv-lab/software-import-20261026/p4-g2-cost-20261030-01 \
      --library /home/riscv/riscv-lab/o4-cost-20261020/library/NangateOpenCellLibrary_typical.lib \
      --output /tmp/p4-g2r0-replay-new.json

另可用 `python3 -B tools/trace_ready.py G2原始目录 新输出.json` 复核 canonical 映射和 ready 原报告。两个脚本只读取输入、写指定JSON，不启动 subprocess/EDA。

方法：
- 明确选择 mapped.json 中 CommonFuCostTop/CommonParentCostTop，避免把空库单元模块误当顶层。
- 按 DFF Q 的 rPacket_ctrl/perfDebugInfo 别名找到元数据位；追踪 D 的直接驱动及 MUX 两数据输入的一级驱动，计数不同实例，避免重复面积。
- Liberty 用平衡大括号提取 cell/pin；pin 使用单词边界，不把 pg_pin 当信号引脚；记录真实函数/面积/电容。
- 父级 instance-binding.json 连接 STA canonical 单元名与 mapped.json；组合图正向到 DFF.D 停止，不穿越 DFF/ICG。所有分支是结构可达性，不作敏化、功耗或唯一因果证明。
- 布尔检查绑定冻结源码方程，抽象 ROB 命中；256控制×8单比特值=2048。四错误表达保留反例；不是RTL验证。
- 同脚本独立重放，完整JSON逐字相等。原G2五档ready报告直接归档，并以原screening.json校对六个失败。

本轮曾有交互式探查脚本选错库模块／计分板路径而失败；未启动硬件或改源。最终可复现脚本明确顶层和根目录计分板，正式运行与重放均通过。它们不是硬件失败或新性能结果。此前G2的全部硬件成本失败仍在原manifest中，不覆盖。

证据层次：
1. G2测量：已有综合单元/面积和STA到达数值，引用原身份。
2. 本轮新派生：R元数据实例归因、ready图分析、库函数手工等价构型、主机布尔检查。
3. 未测试：R1 RTL、实际综合面积、STA、全核/NEMU、程序cycles/加速比和功耗，一律NOT_TESTED。

输入哈希见 evidence/input-lock.json（41项＋445源码）；初始/复核记录见 evidence/input-validation.json。原G2完整manifest仍是其884项证据的权威；本轮不重新压缩数百MB网表，而用绝对路径/哈希引用，并保存必要的10份ready报告和可复现分析。离开本机重放网表分析需要取回原G2对应mapped.json与binding文件，不能只下载本轮小包。
