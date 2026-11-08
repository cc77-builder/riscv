# 第19项最小观测与定点补测设计评审结果

**最小观察方案设计GO；第19项定点修订/目标补测HOLD。** 现有证据不足以给出可信FEX0/VDOT碰撞窗口。正式仍19/20，默认0f＋firstdot V2＋原C8不变；第20项PASS保持。

记录103，操作ID `SP1-E-ITEM19-OBS-DESIGN-20261107-01`；cc77-builder / Agent；基线保存 2026-11-07T20:19:47.366915+08:00，记录 2026-11-07T20:27:09.729472+08:00（UTC+08:00）。早于快照的只读检索未单独记时，不补造人工工时。Git `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`，分支 `local/zjhwork-integration-20261024`。本轮没有代码修改、EMU/NEMU、GNU/全核构建、EDA、切默认或上传。

## 本轮得到的具体设计

1. 真实MinimalConfig向量写回口3上FEX0优先于VFEX4；需要观察FEX0的vector分支valid/ready，不能用FEX0总valid推断碰撞。
2. I2v与vialu拆分微操作共享父ROB；canEnqueue只为firstUop分配。需要按真实u.robIdx、first/last/uopIdx和pdest建立动态分配代，避免把非first的allocatePtr当身份。
3. PerfDebugInfo没有PC，ExeUnit.pc也不普遍存在；新增独立ROB微操作映射，连接PC/psrc、FU接收、输出与实际写回。
4. 前递使用EXU结果valid；producer可用、WB grant、consumer接收必须分开，不能把RF写回当唯一操作数释放时点。
5. 最小拟议观察范围四个文件，默认关闭，不改VDotElastic和现有SP1/T13协议；详细字段、事件及反例合同已形成。

## 为什么没有批准直接补测

一拍候选只需在A输出/B接收的关键一拍出现真实高优先级写回，结构上就可能形成P入队；但当前M1日志未记录竞争方何时请求，不能推导可靠的软件移动量。R5旧事实和NOT_HIT继续保留；本轮不生成M2、不扫描phase、不重复同镜像目标。

新观察器必须先完成实现、默认关闭和局部中性检查，再单独构建诊断EMU。当前EMU构建EMU_TRACE=0，缺失历史不能靠运行参数补出来。观察方案GO仅表示可以做最小实现，不是新核/诊断运行准入，也不是第19项通过。

## 有界合同

未来诊断提案最多bit100→M1正常两个串行进程，原M1完整41调用/84UART/77custom不减；300/900秒、10万/30万guest，目标1200/宿主900/外层2100秒及原CPU4/4线程/RSS12GiB/日志2GiB。它们尚未成为授权或可信完工上界，新的打印开销未测，预算准入继续HOLD。诊断只采时序，必须保留NOT_HIT标签；正式S0/S1与精确重放要求不放宽。

## 交付物

- [最小观察设计与证据边界](DESIGN.md)
- [观察记录规格](OBSERVATION_SCHEMA.md)
- [有界诊断和定点触发合同](BOUNDED_CONTRACT.md) · [机器可读设计合同](DESIGN_CONTRACT.json)
- [源码/生成物身份](SOURCE_PINS.json) · [带行号源码节选](SOURCE_EXCERPTS.md)
- [下一轮指令](NEXT_STEP.md) · [终态审计](FINAL_AUDIT.json)

## 三项指标

# 第19项观察设计：三项指标留档

本轮只读设计，EMU/NEMU、新构建及EDA均0；新加速比、面积、时序和新观察器运行开销全部 **NOT_TESTED**。正式19/20，默认0f＋firstdot V2＋原C8。以下为按原合同复用的历史事实，不是新构建实测，也不自动批准候选切换。记录102的timed DIV/SQRT九格保护PASS继续有效，不能当作VDOT加速比。

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](METRICS.json)。

