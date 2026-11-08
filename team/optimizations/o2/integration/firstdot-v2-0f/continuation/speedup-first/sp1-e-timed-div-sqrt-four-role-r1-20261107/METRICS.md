# 第20项四角色 R1：新保护结果与历史三项指标

第20项四角色 R1 已通过：候选正常、0f正常、候选重放和0f重放全部完成，九格配对及两次精确重放通过。正式验收由18/20推进到 **19/20**；第19项继续 HOLD。默认仍为 **0f＋firstdot V2＋原C8**，没有切换或上传。

## 本轮新增 timed DIV/SQRT 测量

以下每格均值仅取 repeat2～5。first/warmup 不进入均值，但仍通过完整结果、CSR、退休及重放检查。九格全部满足候选/0f ≤ 1.02；8格相同，dataset0/vdivu下降0.25周期（0.168067%）。这是共享执行资源的保护验收，不是新增VDOT加速比。

|dataset|算子|0f均值 cycles|候选均值 cycles|候选相对0f变化|原2%门槛|
|---|---|---:|---:|---:|---|
|0|vdivu|148.75|148.50|-0.168067%|PASS|
|0|vfdiv|208.00|208.00|0.000000%|PASS|
|0|vfsqrt|216.00|216.00|0.000000%|PASS|
|1|vdivu|149.00|149.00|0.000000%|PASS|
|1|vfdiv|208.00|208.00|0.000000%|PASS|
|1|vfsqrt|224.00|224.00|0.000000%|PASS|
|2|vdivu|124.00|124.00|0.000000%|PASS|
|2|vfdiv|208.00|208.00|0.000000%|PASS|
|2|vfsqrt|216.00|216.00|0.000000%|PASS|

本轮 VDOT/RVV 加速比、面积和 STA 新测均为 **NOT_TESTED**；没有运行VDOT性能负载或EDA。下列已有测量按原合同复用，未改写成此次实测。完整新54窗×4角色数据见 [all-windows.csv](all-windows.csv)，原始摘要见 [qualification.json](target-01/qualification.json)。

## 历史加速比、面积与时序（复用）

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
