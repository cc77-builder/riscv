# SP1-E micro single-d1 合同与宿主准入结果

**GO（宿主准入）：single-d1合同、运行器适配、正负控、预算评审与执行冻结完成，可在下一轮明确指令后启动一次五角色有界探针。** 本轮未运行EMU/NEMU，single-d1的SP1目标正确性及加速比仍NOT_TESTED；默认0f＋firstdot V2＋原C8不变。

@cc77-builder / Agent；操作ID 20261105-cc77-builder-sp1-e-single-d1-host；2026-11-05T06:00:59.972544+00:00 至 2026-11-05T14:09:17.047795+08:00，仅任务跨度，非人工工时。基点 347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e；分支 local/zjhwork-integration-20261024。

## 完成项与资格

运行器97项（47机制＋50适配）、独立预冻结114项和冻结后32项全部通过。核查single-d1专用镜像/数据与12窗/6custom，负数点积完整128位000000000000000000000000fffe0400、退休逻辑17/21及instret12/16、CSR、专用bit100、两方法各2%精确门槛和八类原始精确重放；误用d0图像、case、raw、收据、旧freeze均拒绝。冻结5426项/143源码，实际12个模块及5个动态JSON全部闭合；缺失运行授权在启动前拒绝，锁未消费。

物理身份537项、候选源码398项、生产src 445项未变；执行冻结5426项。复用原ELF/BIN不重编译，首条PC 0x8000114c、word 0x0294050b、vd10的bit100恰好一次。保留12窗/6custom，VDOT与RVV各自最多2%退化，AB/BA只保留次序及报告，不套用chain10%门槛。

[合同](CONTRACT.md) · [运行器](runtime-review/RESULT.md) · [独立复核](independent-review/REVIEW.md) · [冻结](EXECUTION_FREEZE.json)。宿主假进程、合成bit100诊断及旧0f日志不能充当新SP1目标PASS。

## 预算准入

d1历史完整0f为72465 guest、12窗/6custom、3387546字节日志，完整程序核查通过。与d0的kernel/main源和.text逐字一致，仅0x80003aa8的dataset打印常量0→1及数据区38字节不同，没有删减验证。最近同运行时single-d0五角色实测单调834.652753秒、目标771.211695秒、非目标63.441059秒，提供完整机制参考，不转授d1资格。新d1完整收据解析1.665232322秒；最终5426项/687207816字节冻结的根级完整verify为1.526349759秒，独立verify＋import观察4.274064319秒。取较大观察值按12轮verify加26次正常解析作保守工作量投影约94.585秒，低于900秒宿主预留。负控解析、监督/身份、序列化和清理仍计入完整外层；这些是观测与投影，不是未来数学最坏保证。依据足以准入一次有界尝试，资源或输入漂移时仍HOLD，6300/7200秒硬上限不变。

[预算依据](budget-review/RESULT.md)。固定拒错300秒/100k guest，四个正常角色各1500秒/300k guest；合计6300秒目标、7200秒外层，CPU4/整组4线程/RSS12GiB/日志2GiB。预算是硬停止上限，不是完成保证。

## 三项指标

| 工作负载与资格 | 0f VDOT/RVV cycles | SP1 VDOT/RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT |
|---|---:|---:|---:|---:|
| chain-d0，历史第51条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| chain-d1，历史第58条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| chain-d2，历史第60条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| single-d0，历史第62条 | 71.0/85.25 | 70.0/85.25 | 1.200704× | 1.217857× |
| **本轮single-d1新五角色** | NOT_TESTED | NOT_TESTED | NOT_TESTED | NOT_TESTED |

| 历史同约束成本 | 0f | SP1一拍候选 |
|---|---:|---:|
| FU面积/μm² | 17298.246 | 18322.878 |
| 含FU父级面积/μm² | 284614.946 | 285241.642 |
| nominal FU setup slack/ns | -0.268520 | -0.790381 |
| nominal父级setup slack/ns | -2.393998 | -2.337809 |

| SP1历史STA档位 | 周期/ns | 负载/fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| SP1历史nominal关键路径 | arrival/ns | required/ns | slack/ns | 起点→终点 |
|---|---:|---:|---:|---|
| FU/ready | 0.218001 | 0.85 | 0.631999 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| FU/all_max | 1.709455 | 0.919074 | -0.790381 | io_in_bits_data_src_0[14] (input port clocked by core_clk) → c8968 (rising edge-triggered flip-flop clocked by core_clk) |
| 父级/ready | 0.303064 | 0.85 | 0.546936 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| 父级/gate_enable | 1.713544 | 0.877842 | -0.835702 | c201714 (rising edge-triggered flip-flop clocked by core_clk) → c203281 (rising clock gating-check end-point clocked by core_clk) |
| 父级/all_max | 3.259825 | 0.922016 | -2.337809 | io_in_bits_vpu_vsew[1] (input port clocked by core_clk) → c201899 (rising edge-triggered flip-flop clocked by core_clk) |

新single性能及新PPA均NOT_TESTED。历史chain三数据集VDOT周期下降均13.772213%，single-d0为71→70cycles、下降1.408451%；C8第53～55条资格保持自身范围。成本为原G2 Nangate45 Typical1.1V25℃、trace-off局部FU/含FU父级，不是全核面积或频率签核；负slack及旧P4失败保留，最终选型由用户决定。

## 保留失败与审计限制

本轮运行器、独立静态/正负控和两轮实际freeze/verify均通过，无新增目标。预算脚本准备阶段一次嵌套字符串SyntaxError在执行前被拒绝，原记录位于budget-review/HOST_PREPARATION_FAILURE.json；没有目标副作用或目标重试。上轮single-d0的宿主失败记录保留在原目录。本轮组装器排除活动输出日志，输出关闭后才写盘，未再出现日志自引用pin漂移。

single-d0历史UTC与单调墙钟差52.776291707秒及未知根因继续保留；不改时钟或原始日志，预算仅认单调时钟。CPU0～3与队友冻结输入保护保持，Issue仅只读，无GitHub写入。默认0f＋firstdot V2＋原C8不变，d1新功能、周期和新EDA均NOT_TESTED。

## 下一轮指令

开始 SP1-E micro single-d1 五角色有界探针，按 NEXT_STEP 先核查已有进程、冻结输入和资源，再依次完成 bit100 拒错、候选恢复、0f 校准、候选重放和0f重放。保持6300/7200秒预算、CPU4/整组4线程、原guest/RSS/日志上限、完整12窗和6次custom、VDOT与RVV各自最多2%退化、逐窗控制相等及精确重放门槛。失败即停，不重试、不加时、不扩围、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新加速比、面积、时序，给出结论和下一轮指令。

执行冻结尚未消费；本轮没有真实目标授权，C48预算HOLD与完整SP1-E未验收状态保持。
