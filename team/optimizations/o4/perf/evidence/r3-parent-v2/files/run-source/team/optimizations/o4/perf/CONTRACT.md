# R3 perfDebugInfo 消费者与父级覆盖合同 v2

操作 ID：20261025-LiZufan001-r3-perf-0001。发布基点：`5640b7fda828109a875bc4e2dfb9d9a1da0266da`。
本合同为新的团队验证子项；旧 G1/G2、H1、O4 合同、源码提交、黄金数据与封存结果保持原版本，不把新验证身份回填旧 PASS。

## 问题、假设与停止条件

现有 G2 完整 child perf 相等检查确实存在，但 8 个64位字段具有同值激励；最终 ExeUnit debugInfo 只独立输出 issue/rename 两字段。
本子项要证明完整外部输入经过真实 VFEX4 的子 FU 和最终输出仍保持同一事务，并把消费者、配置和映射成本分开。
若消费者或观察合同不允许裁剪，就保留生产 RTL；不得把 577 位字段总量当作可删除寄存器、功耗或整核面积收益。

## 固定设计与边界

- 生产 src/、官方依赖、NEMU、数学模型和22+10000黄金向量不变。本轮修改仅团队测试适配器、C++驱动、严格结果复核与工程说明。
- MinimalConfig，单核、ROB48、VLEN128；两个128位输入各取低8个 signed INT8；低32位精确结果，高96位清零。O2+H1，实际时钟及真实 ClockGate，reset清有效位，取消遵循各槽 ROB 环绕身份。
- 接受 E0、P→R E1、最早响应 E2；无停顿 II=1，最多两条在途。保留非法配置响应、完整控制、反压、逐槽取消、TE=0复位和真实 VIDiv/VFDiv 切换。
- PerfDebugInfo 为9×64+1=577位。测试输入视作不参与功能判定的 opaque payload；任意值不代表真实时间戳。按当前 Bundle 打包，低端依次 tlbResp/tlbFirst/checkpoint/writeback/issue/select/enq/dispatch/rename，最高位 eliminatedMove。
- 新输入端口驱动整个包；期望值取外部请求原文，不能以 DUT 输入 tap 生成期望。子 FU 输入、子 FU 输出、实际父级 debugInfo 输出三处分别比较。原 VPU 噪声 tag 独立保留。
- 保留原12组控制/算术场景；新增第13组577个两槽配对：walking-one与walking-zero各577条，带满槽反压、噪声输入拒绝和排空。所有正常请求的9个64位字段独立生成，不再全部等值。

## 验收

1. 实际 Scala/Chisel 生成与 Verilator 仿真；全部冻结算术/控制检查、事务守恒、两拍/II=1及13组结束条件通过。
2. 原16项 C++观察负控，加输入路由、同值旧字段互换、父级非issue/rename位、跨槽父级身份4项。必须退出1并具有精确 INJECT/FAIL类别；这些是观察值负控，不称生产RTL故障注入。
3. metadata.log完整记录原始接受包、child/parent观察和各终结；独立 Python复核与控制原文逐周期/事务对齐，逐位比较、检查全部walking实际响应、拒绝缺失/多余/重复或截断记录。对真实日志的8类篡改必须拒收。
4. 记录源码、依赖、生成RTL、实际二进制、工具、命令/退出码和前后哈希。先验证生产源与发布基点相同，再复用历史功能/PPA上下文。
5. 消费者审查须区分 ROB独立副本、CtrlBlock覆盖、条件性能计数器、固定utility的ChiselDB条件、DiffTest dontTouch和O2 trace观察性；检查实际T17生成物，不只搜索字段名。

资源：隔离Windows工作区及WSL原生源码/输出；重任务合计最多4核，JVM上限按实际可用内存设定并记录。既有caller与T17物理输入只读。
本轮没有新生产RTL候选，故不重建全核、不重跑已有EMU矩阵、不生成无对应硬件修改的新ASIC时序成绩。测试适配器不得作为面积综合顶层。

## 复现入口

在完整、依赖已固定的源码检出中，输出必须不存在并位于仓库外：

~~~bash
VDOT_RTL_JOBS=4 VDOT_RTL_JAVA_OPTS='-Xmx5G -Xss8m -XX:ActiveProcessorCount=4' \
  python3 -B team/optimizations/o2/run_rtl.py parent /absolute/new/r3-parent
python3 -B team/optimizations/o4/perf/audit.py \
  --control /absolute/new/r3-parent/result.log \
  --metadata /absolute/new/r3-parent/metadata.log \
  --negative-checks --output /absolute/new/r3-parent/metadata-negative-audit.json
~~~

完整使用结果、失败尝试及确切身份在 RESULT.md；没有结果不提前称通过。旧日志无perf_contract=2时沿原控制合同检查，不授予新的577位资格。
