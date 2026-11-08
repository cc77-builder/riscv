# SP1-E micro chain-d1 合同与宿主准入结果

**GO：chain-d1 合同、宿主准入和执行输入冻结完成，可进入下一轮独立授权的五角色有界探针。** 本轮未运行目标；chain-d1 在 SP1 上的功能与性能仍 NOT_TESTED。

@cc77-builder / Agent；操作ID 20261104-cc77-builder-sp1-e-micro-chain-d1-host。原开始 2026-11-04T14:47:18.861904+00:00，本次恢复 2026-11-05T03:29:02.931653+00:00，结束 2026-11-05T11:49:44.043581+08:00。跨度包含中断，不是人工工时。

## 已完成与证据边界

冻结同镜像dataset1/chain256、12窗、1536custom及首条bit100 PC/word/vd；完整128结果、退休/CSR与精确重放合同不变。69项运行器及92项独立检查全部通过；独立宿主检查含历史d1日志离线重算及错误配置/高96/融合分组/CSR/缺窗/收益边界；它验证检查器，不能替代新候选目标验证。新运行器绑定真实/proc映像、argv、cwd、参考库映射、PID/starttime和原始日志，拒绝旧数据集、假目标及未授权run；失败和宿主调试记录留在原证据目录。

已核对448项原物理输入、398份候选源码和445份生产源码未变；实际执行闭包共4258项，完成freeze/verify。详见[宿主准入](HOST_ADMISSION.json)、[运行器](runtime-review/RESULT.json)、[独立复核](independent-review/REVIEW.json)与[执行冻结](EXECUTION_FREEZE.json)。

## 为什么预算 GO

d1和已通过d0的全部ELF section布局相同，14952字节主计算.text完全一致；唯一执行指令差异为打印数据集编号0→1，另外36字节为输入/期望数据。保留全部first、warmup和measured工作。当前0f历史d1完整120824 guest；同EMU/NEMU的d0五角色完整955.233秒，四正常角色213.454～235.934秒。G1采集机制已有完整实际运行，新检查器宿主开销另测并纳入900秒余量。

依据完整程序关系及完整历史运行，支持300+4×1500=6300秒目标预算、7200秒外层上限的一次有界尝试。它不保证任意宿主调度下一定完成，也不证明d1收益；发生超限仍立即停止。CPU4、整组4线程、12GiB RSS、2GiB原始日志和100k/300k guest上限保持。[预算明细](budget-review/REVIEW.md)。

## 三项指标与成本取舍

本轮没有新目标或EDA实测；下面已测数值均为历史复用。加速比=同硬件RVV/VDOT，chain-d0周期下降13.7722%另列；不能代填chain-d1。

| 工作负载（历史复用另注） | 0f vdot/RVV cycles | SP1 vdot/RVV cycles | 0f 加速比 | SP1 加速比 |
|---|---:|---:|---:|---:|
| chain256 dataset0，历史51 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| 原C8 reuse dataset0，历史53 | 273/299 | 272/299 | 1.095238× | 1.099265× |
| 原C8 reuse dataset1，历史54 | 273/299 | 272/299 | 1.095238× | 1.099265× |
| 原C8 reuse dataset2，历史55 | 273/299 | 272/299 | 1.095238× | 1.099265× |
| **本轮 chain-d1 新五角色** | NOT_TESTED | NOT_TESTED | NOT_TESTED | NOT_TESTED |

| 同约束历史成本 | 0f | SP1 一拍候选 |
|---|---:|---:|
| FU面积/μm² | 17298.246 | 18322.878 |
| 含FU真实父级面积/μm² | 284614.946 | 285241.642 |
| nominal FU setup slack/ns | -0.268520 | -0.790381 |
| nominal 父级 setup slack/ns | -2.393998 | -2.337809 |

| SP1历史档位 | 周期/ns | 负载/fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| SP1 nominal关键路径（历史） | arrival/ns | required/ns | slack/ns | 起点 → 终点 |
|---|---:|---:|---:|---|
| FU ready | 0.218001 | 0.85 | 0.631999 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| FU all_max | 1.709455 | 0.919074 | -0.790381 | io_in_bits_data_src_0[14] (input port clocked by core_clk) → c8968 (rising edge-triggered flip-flop clocked by core_clk) |
| 含FU父级 ready | 0.303064 | 0.85 | 0.546936 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| 含FU父级 gate_enable | 1.713544 | 0.877842 | -0.835702 | c201714 (rising edge-triggered flip-flop clocked by core_clk) → c203281 (rising clock gating-check end-point clocked by core_clk) |
| 含FU父级 all_max | 3.259825 | 0.922016 | -2.337809 | io_in_bits_vpu_vsew[1] (input port clocked by core_clk) → c201899 (rising edge-triggered flip-flop clocked by core_clk) |

面积/STA来源为原G2、Nangate45 Typical1.1V25℃、trace-off局部FU及含FU真实父级；非全核面积或签核频率。FU面积约+5.923%、父级约+0.220%；候选原SP0成本探索资格保持，不新增更严PPA门槛。用户要求优先加速比，允许成本代价；负slack和旧P4失败仍如实保留，周期减少与频率改变后的实际时间收益分开。完整五档路径见METRIC_SNAPSHOT.json。

## 下一轮

开始 SP1-E micro chain-d1 五角色有界探针：先核查已有进程、冻结输入和本轮 NEXT_STEP，使用已冻结运行器与同镜像、0f/SP1 EMU及NEMU；准入全部通过后，依次运行bit100拒错、候选恢复、0f校准、候选重放和0f重放。保持6300/7200秒、CPU4/4线程、原guest/RSS/日志上限，完整12窗和1536custom，10%收益、2%RVV退化、AB/BA均正及精确重放。失败即停，不重试、不加时、不扩围、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新加速比、面积、时序并给下一轮指令。

本轮未生成真实运行授权文件，EXECUTION_FREEZE未消费。执行前按runtime/ANNEX_REQUIREMENTS.md记录新一轮用户指令、绑定freeze SHA和新输出目录；这不需要更改已验收运行器源码。C48预算HOLD继续保留，不重开其他case。稳定默认仍0f＋firstdot V2＋原C8，最终选型由用户决定。
