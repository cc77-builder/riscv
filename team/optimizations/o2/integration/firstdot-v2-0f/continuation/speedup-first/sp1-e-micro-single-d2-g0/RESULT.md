# SP1-E micro single-d2 合同与宿主准入结果

**GO（宿主准入）：single-d2合同、运行器适配、正负控、预算评审与执行冻结完成，可在下一轮明确指令后启动一次五角色有界探针。** 本轮未运行EMU/NEMU，single-d2的SP1目标正确性及加速比仍NOT_TESTED；默认0f＋firstdot V2＋原C8不变。

@cc77-builder / Agent；操作ID 20261105-cc77-builder-sp1-e-single-d2-host；2026-11-05T06:38:14.593741+00:00 至 2026-11-05T14:47:50.796890+08:00，仅任务跨度，非人工工时。基点 347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e；分支 local/zjhwork-integration-20261024。

## 完成项与资格

运行器103项（50机制＋53适配）、独立预冻结114项和冻结后32项全部通过。核查single-d2专用镜像/数据与12窗/6custom，低8项有符号正负抵消为0、完整128位00000000000000000000000000000000，全部6次接受源及高96位独立校验；退休逻辑17/21及instret12/16、CSR、专用bit100、ENQUEUE身份、两方法各2%精确门槛和八类原始精确重放均有正负控。d0/d1镜像、case、raw、收据、旧freeze误用均拒绝。冻结5771项/152源码，实际12个自定义模块及5个动态JSON全部在闭包；缺授权在启动前拒绝，正式执行锁未消费。

物理身份537项、候选源码398项、生产src 445项未变；执行冻结5771项。复用原ELF/BIN不重编译，首条PC 0x8000114c、word 0x0294050b、vd10的bit100恰好一次。保留12窗/6custom，VDOT与RVV各自最多2%退化，AB/BA只保留次序及报告，不套用chain10%门槛。

[合同](CONTRACT.md) · [运行器](runtime-review/RESULT.md) · [独立复核](independent-review/REVIEW.md) · [冻结](EXECUTION_FREEZE.json)。宿主假进程、合成bit100诊断及旧0f日志不能充当新SP1目标PASS。

## 预算准入

d2历史完整0f为72465 guest、12窗/6custom、3387546字节日志，完整程序核查通过。与d1的kernel/main源和.text逐字一致，仅0x80003aa8的dataset打印立即数1→2及数据区70字节不同，没有删减验证。最近同运行时single-d1五角色实测单调801.857455595秒、目标737.658433015秒、非目标64.199022580秒，提供完整机制参考，不转授d2资格。CPU4完整d2收据解析运行器1.701140831秒、预算独立解析1.651666442秒，取较大观察值。最终5771项/701571765字节冻结根级完整verify为1.706213595秒，独立verify/import为1.675858319秒，完整独立子进程1.731043953秒。仍保留较慢继承哈希观察3.064420625秒作固定工作量投影：26次正常解析＋12轮哈希/verify约81.002709106秒，小于900秒预留。负控解析、监督/身份、序列化和清理仍计入完整外层；这些是完整程序证据、宿主观测和工作量投影，不是未来最坏墙钟保证。支持准入一次有界尝试，输入/资源漂移或准备预算不足仍HOLD；6300/7200秒硬上限不变。

[预算依据](budget-review/RESULT.md)。固定拒错300秒/100k guest，四个正常角色各1500秒/300k guest；合计6300秒目标、7200秒外层，CPU4/整组4线程/RSS12GiB/日志2GiB。预算是硬停止上限，不是完成保证。

## 三项指标

| 工作负载与资格 | 0f VDOT/RVV cycles | SP1 VDOT/RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT |
|---|---:|---:|---:|---:|
| chain-d0，历史第51条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| chain-d1，历史第58条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| chain-d2，历史第60条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| single-d0，历史第62条 | 71.0/85.25 | 70.0/85.25 | 1.200704× | 1.217857× |
| single-d1，历史第64条 | 71.0/85.25 | 70.0/85.25 | 1.200704× | 1.217857× |
| **本轮single-d2新五角色** | NOT_TESTED | NOT_TESTED | NOT_TESTED | NOT_TESTED |

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

新single性能及新PPA均NOT_TESTED。历史chain三数据集VDOT周期下降均13.772213%，single-d0/d1为71→70cycles、下降1.408451%；C8第53～55条资格保持自身范围。成本为原G2 Nangate45 Typical1.1V25℃、trace-off局部FU/含FU父级，不是全核面积或频率签核；负slack及旧P4失败保留，最终选型由用户决定。

## 保留失败与审计限制

本轮运行器、独立静态/正负控、身份与freeze/verify均通过，未新增目标、生产参考库加载或实际bit100。预算脚本准备阶段一次嵌套引号SyntaxError在执行前终止，原记录保存在budget-review/HOST_PREPARATION_FAILURE.json；没有目标副作用或目标重试。组装使用capture_output后落盘，并排除assemble活动输出，未发生日志自引用pin漂移。

single-d1历史准备boot与实际运行boot不同、原离线审计FAIL及R1修订、UTC与单调墙钟差59.611296345秒均按原记录保留。准备boot不约束未来运行boot；未来实际五角色的boot、PID、内核startticks和单调连续性仍须真实核验。时钟差原因未证实，不改系统时钟或日志，预算仅按冻结单调时钟。更早single-d0及P4等FAIL/NO-GO不改写。

CPU0～3及队友冻结输入保护，Issue只读；无GitHub写入。默认0f＋firstdot V2＋原C8不变。本轮single-d2的新SP1功能/周期和新面积/STA均NOT_TESTED，历史成绩仅按各case范围引用。

## 下一轮指令

开始 SP1-E micro single-d2 五角色有界探针，按 NEXT_STEP 先核查已有进程、冻结输入和资源，再依次完成 bit100 拒错、候选恢复、0f 校准、候选重放和0f重放。保持6300/7200秒预算、CPU4/整组4线程、原guest/RSS/日志上限、完整12窗和6次custom、VDOT与RVV各自最多2%退化、逐窗控制相等及精确重放门槛。失败即停，不重试、不加时、不扩围、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新加速比、面积、时序，给出结论和下一轮指令。

执行冻结尚未消费；本轮没有真实目标授权，C48预算HOLD与完整SP1-E未验收状态保持。
