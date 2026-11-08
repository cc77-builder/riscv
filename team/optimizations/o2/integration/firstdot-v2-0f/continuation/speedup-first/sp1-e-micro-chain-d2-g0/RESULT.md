# SP1-E micro chain-d2 合同与宿主准入结果

**GO：chain-d2 的合同、宿主准入及执行输入冻结完成，可进入下一轮单独授权的五角色有界探针。** 本轮未运行 EMU/NEMU，SP1 chain-d2 目标正确性及加速比仍为 NOT_TESTED，默认保持0f＋firstdot V2＋原C8。

@cc77-builder / Agent；操作ID 20261105-cc77-builder-sp1-e-chain-d2-host；开始 2026-11-05T04:38:53.794288+00:00，结束 2026-11-05T12:48:46.027709+08:00。记录任务跨度，不计人工工时。基点 347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e，分支 local/zjhwork-integration-20261024。

## 已完成及资格边界

运行器69项宿主门禁、独立预冻结100项、冻结后31项全部通过。覆盖错误dataset、全部128位结果与高96位、接收源、退休数量/融合分组、CSR、缺窗、bit100绑定、10%/2%精确边界、AB/BA与原始精确重放。实际加载12个Python模块及4个动态JSON均在执行源闭包中；缺失目标授权在启动前拒绝，宿主假进程不能冒充真实EMU。

物理身份核对448项、候选源码398项、生产文件445项未变；执行冻结4548项，宿主freeze/verify及独立post-freeze通过。新镜像仍使用G0原始ELF/BIN，没有重新编译。首条bit100保持PC 0x8000114c、word 0x0295050b、vd10、恰好一次。候选/0f各全新恢复和精确重放；first/warmup保留，完整12窗/1536custom不变。

[完整合同](CONTRACT.md) · [运行器检查](runtime-review/RESULT.md) · [独立检查](independent-review/REVIEW.md) · [执行冻结](EXECUTION_FREEZE.json)。宿主假收据和历史日志只验证检查器，不能当作新SP1 d2目标结果。

## 预算依据

d1/d2的主计算.text、kernel/main/linker/generator及加载布局相同；唯一可执行字节差为打印数据集编号1→2，输入/期望数据区68字节变化。历史d2完整0f为120824 guest cycles、12窗/1536custom；同EMU/NEMU的d1正常角色最慢328.155秒、完整五角色1468.527秒，均按单调计时留档。新d2完整宿主解析实测4.956863秒；26次解析与12次旧闭包重哈希的固定工作量投影157.362秒，小于900秒宿主预留。最终4548项冻结共651590256字节，实际包含全部verify的31项终检耗时1.402076秒，未出现实质增加的宿主成本。以上完整程序与实测证据支持一次有界尝试，不能保证未来调度下一定完成，也不能证明d2已有收益；外层单调硬限保持有效。

[预算明细](budget-review/RESULT.md)。上限继续为300秒/100k拒错、1500秒/300k×4正常，共6300秒目标、7200秒外层，CPU4/整组4线程、12GiB RSS、2GiB合并日志。依据不足或未来执行触限均停止，不重试、不加时、不删覆盖。

## 三项指标留档

本轮没有新目标或EDA成绩，历史已合格数据不代填chain-d2。加速比=同硬件RVV/VDOT；相对0f的VDOT周期下降另列。历史chain-d0/d1下降均为13.772213%，只授各自case。

| 工作负载与测量范围 | 0f vdot/RVV cycles | SP1 vdot/RVV cycles | 0f 加速比 | SP1 加速比 |
|---|---:|---:|---:|---:|
| chain-d0，历史第51条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| chain-d1，历史第58条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| **本轮 chain-d2 新同镜像五角色** | NOT_TESTED | NOT_TESTED | NOT_TESTED | NOT_TESTED |

| 历史同约束成本 | 0f | SP1 一拍候选 |
|---|---:|---:|
| FU面积/μm² | 17298.246 | 18322.878 |
| 含FU真实父级面积/μm² | 284614.946 | 285241.642 |
| nominal FU setup slack/ns | -0.268520 | -0.790381 |
| nominal 父级 setup slack/ns | -2.393998 | -2.337809 |

| SP1历史STA档位 | 周期/ns | 负载/fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| SP1历史nominal关键路径 | arrival/ns | required/ns | slack/ns | 起点 → 终点 |
|---|---:|---:|---:|---|
| FU/ready | 0.218001 | 0.85 | 0.631999 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| FU/all_max | 1.709455 | 0.919074 | -0.790381 | io_in_bits_data_src_0[14] (input port clocked by core_clk) → c8968 (rising edge-triggered flip-flop clocked by core_clk) |
| 父级/ready | 0.303064 | 0.85 | 0.546936 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| 父级/gate_enable | 1.713544 | 0.877842 | -0.835702 | c201714 (rising edge-triggered flip-flop clocked by core_clk) → c203281 (rising clock gating-check end-point clocked by core_clk) |
| 父级/all_max | 3.259825 | 0.922016 | -2.337809 | io_in_bits_vpu_vsew[1] (input port clocked by core_clk) → c201899 (rising edge-triggered flip-flop clocked by core_clk) |

成本来自原G2 Nangate45 Typical 1.1V 25℃、trace-off局部FU与含FU真实父级；非全核面积或频率签核。负slack及旧P4失败保留；本轮沿用加速比优先的已冻结成本探索政策，不新增更紧PPA门槛，最终采用由用户决定。

## 宿主修订与时钟记录

预算分析脚本适配历史JSON字段时出现的FAIL、错误提示文字对比FAIL和报告生成格式错误均留档；修订仅涉及宿主解析或文档生成，原始目标日志及已测运行器未改，不存在目标重试。adapter有一处诊断文字仍写exact d1 case binding，实际CASE_ID与固定输入均为d2；此非行为差异已注明。

chain-d1原始UTC与单调时钟约99秒差异及未知根因继续保留。预算以冻结time.monotonic()为准，不拿UTC或EMU自报Host time替换，不修钟、不改历史日志。CPU0～3的队友保护范围继续避让；Issue只读核实，无GitHub写入。

## 下一轮指令

开始 SP1-E micro chain-d2 五角色有界探针，按 NEXT_STEP 先核查已有进程、冻结输入和资源，再依次完成 bit100 拒错、候选恢复、0f 校准、候选重放和0f重放。保持6300/7200秒预算、CPU4/整组4线程、原guest/RSS/日志上限、完整12窗和1536次custom、10%收益、2% RVV退化、AB/BA及精确重放门槛。失败即停，不重试、不加时、不扩围、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新加速比、面积、时序，给出结论和下一轮指令。

执行冻结未消费；本轮未生成真实目标运行授权。C48预算HOLD、其他case未验收及SP1-E整体未完成状态保持。
