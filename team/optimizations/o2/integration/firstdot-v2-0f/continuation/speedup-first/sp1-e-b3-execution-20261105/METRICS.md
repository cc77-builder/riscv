# 三项指标：本轮未产生新目标实测

本轮加速比、面积、时序均为 NOT_TESTED；两例保护程序没有合格 RVV 计时对照，不能从功能通过或宿主开销推算加速比。以下为此前 B2 同镜像五角色结果和原 G2 局部成本的历史复用，未重新运行。

| 历史工作负载 | 0f VDOT cycles | SP1 VDOT cycles | 0f/SP1 RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT | VDOT周期下降 |
|---|---:|---:|---:|---:|---:|---:|
| B2 stream performance-d0-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d1-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d2-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |

| 历史局部成本 | 0f | SP1 |
|---|---:|---:|
| FU 面积 μm² | 17298.246 | 18322.878 |
| 含 FU 的真实父级面积 μm² | 284614.946 | 285241.642 |
| nominal FU setup slack ns | −0.268520 | −0.790381 |
| nominal 父级 setup slack ns | −2.393998 | −2.337809 |

Nangate45 Typical 1.1V 25℃，原 G2 trace-off 局部 FU/真实父级综合；不是整核面积、签核或 Fmax。负 slack 和原严格 G2 NO-GO 均保留。新 trace-on 成本仍 NOT_TESTED。

| SP1历史五档 | 周期ns | 负载fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

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

全部来源、关键路径和逐窗历史重放资格保存在 METRICS.json；本轮宿主失败不改写既有性能结果，也不新增 SP1 功能资格。
