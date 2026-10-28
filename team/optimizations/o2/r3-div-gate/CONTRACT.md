# R3 DIV 取消关钟：局部验证合同

日期：2026-10-24；基点4669c487f3024ee5fce514c37270297f99066b2a。执行者：@cc77-builder / Agent。
本轮授权：实现最小O2 DIV关钟修复，严格FU与真实父级验证，成果仅保留本地。全核、周期比较、综合STA、发布不在本轮范围。

## 假设和修改范围

当前不定时延FU的uncer_en_reg仅接受置位、响应清零；DIV被匹配ROB重定向取消后可能不再产生响应，留下无效时钟。
在O2专属VFEX4中复用独立DIV的divBusy/divRobIdx.needFlush，取消边沿清理VIDiv/VFDiv的保持位。
父时钟寄存器的旧保持位保证取消当拍仍有清理边沿；随后空闲关闭，下个真实接受能唤醒。

保持VDot的P/R占用门控、32位结果保存及完整128位输出、ISA与异常、元数据身份、VDot算术、legacy/T14/O1分支、共享接口和默认配置不变。
修复限制于O2及VIDiv/VFDiv两个FU。原[O2合同](../CONTRACT.md)第5节“DIV保持现状”只在本新候选中以本合同取代；旧实验/证据/合同不修改。
这里不引入新的通用DIV复位门控合同；现有DIV初始化/复位仍使用TE=1，VDot原TE=0复位覆盖保持。

## 先失败、后通过

1. 在生产ExeUnit尚未修改时，用新严格父级测试生成/编译旧H1真实父级并运行。必须因取消后空闲DIV时钟未关闭而预期失败，不能把构建失败当红测通过。
2. 固定严格测试后，只应用上述最小RTL修复。独立FU跑原22定向＋10000随机向量和现有控制压力，保留4个观察值负控。
3. 真实父级使用真实ClockGate、VDot、VIDiv、VFDiv，完整跑相同向量和原控制压力，保留16个观察值负控。负控修改观察值，不冒称RTL故障注入。
4. 正向原始逐拍日志独立复算；只在其PASS、原文summary一致且严格时钟门禁成立时宣布本地G1/G2通过。

原36组DIV取消覆盖两DIV×三种后继FU×计算/可见/反压阶段×out.ready两值，每组取消后3拍真空闲再接新请求。
新增定向覆盖同ROB但不flushItself的非取消重定向、47/48与95/0环绕的杀/不杀、取消+reset重合及恢复。
严格检查必须包含原始clocks字段、取消/复位唯一终止、既有完整数据/身份/异常/反压/部分取消和FU互斥；不只信任cancel_idle_clock_on摘要。
离线检查器负例须同时篡改轨迹与汇总计数，仍因真实空闲规则失败，证明不是偶然汇总不匹配。

## 采用边界与停止条件

局部门禁：所有正向测试与原负控通过；无停顿II=1、首响应2拍；取消后的真实空闲时钟为零；正常/非取消redirect不丢响应；输入及子模块测试前后相同。
局部失败先定位最小案例，不降低门槛、不丢失败日志、不拿旧James绿色记录替代新H1组合运行。
局部通过仅形成候选，不宣告全核、同镜像周期、面积、时序、功耗或最终采用通过。下一阶段再以新硬件身份做受影响全核/NEMU与周期不退化、同约束STA。
如果新增时序/周期存在未解释退化，保留原H1回退；本轮时钟边沿统计不得换算成瓦数或加速比。

## 运行与证据

复用现有run_rtl.py，不修改冻结向量、旧证据或构建器；每次输出必须为检出外的新目录。
在仓库根执行：

~~~bash
python3 -B team/optimizations/o2/run_rtl.py parent /absolute/new/red-parent
# 红测确认后在源码应用最小RTL补丁，再依次运行：
python3 -B team/optimizations/o2/run_rtl.py fu /absolute/new/green-fu
python3 -B team/optimizations/o2/run_rtl.py parent /absolute/new/green-parent
python3 -B team/optimizations/o2/parent/check_trace.py --help
~~~

红测须使用旧ExeUnit与新严格测试；具体补丁、前后源码SHA、命令及退出码随本轮结果保存。不要在已经修复的源码上运行第一条并称为旧版红测。
使用既有WSL原生检出、独立输出、最多一个硬件构建；当前runner为mill -j2 / Verilator -j2 / Java 12G，禁止与本机其他重型任务抢用共享构建目录。

本轮只读核查协调Issue，未发布评论；现有T17是其他独立主机/目录的冻结运行，本机无旧构建/EMU进程。成果不会推送GitHub，不接管T17。
