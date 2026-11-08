# SP1-E B4-R2：宿主修复通过，完整调用覆盖失败即停

**结论：STOPPED / HOLD；正式验收保持17/20。** B4-R2最小raw dst范围修复与宿主准入通过；新独立批次bit100拒错通过，候选o2-control完整程序GOOD_TRAP、256次试验零错误、1208次退休完整128位重算一致，但原覆盖门KILL_P/PARTIAL_KILL未触发，整批按合同STOPPED。仅启动2/6目标，其余4个NOT_RUN，清理正常、旧FAIL和锁保留。候选1562.610640秒超过原正式1500秒，低于本轮2400秒；不授完整校准或正式验收资格，进度仍17/20，默认保持0f＋firstdot V2＋原C8。

## 实际角色结果

| 用例/角色 | 结果 | guest cycles | 活跃墙钟/s |
| --- | --- | ---: | ---: |
| o2-control bit100 | NEGATIVE_PASS | 9243 | 20.617259 |
| o2-control candidate-full | 程序完整结束、数值证据一致；覆盖FAIL | 702861 | 1562.610640 |
| o2-control baseline-full | NOT_RUN | — | — |
| 原C8普通C48 bit100 | NOT_RUN | — | — |
| 原C8普通C48 candidate-full | NOT_RUN | — | — |
| 原C8普通C48 baseline-full | NOT_RUN | — | — |

## 准入、执行与归因

只修历史32槽指令环raw dst范围（uint8 0..255），选出的当前提交组仍要求架构目的地<32；槽顺序、尾指针、当前组、ELF/ROB、完整128位、CSR及bit100判据保持。没有把历史dst32改写为vd28。真实旧日志与26项差异验证一次PASS；运行器4项差异验证一次PASS，复用原10+5项未变证据。两例各339项执行冻结通过，独立宿主审查通过，900秒宿主预算经验估计分别235.921543秒和213.416454秒。新合同、授权、消费锁及独立输出生效，旧FAIL和锁保留。

每例最多3目标：bit100 300秒/10万guest，候选及0f各2400秒/150万guest；每例目标5100/宿主900/外层6000秒，整批最多6目标/10200秒目标/12000秒外层，CPU4/整组4线程/RSS12GiB/每例日志2GiB。实际只启动2个，目标累计1583.227898秒，case宿主8.742916秒，case总1591.970814秒，batch总1593.974286秒，guardian总1594.082341秒。candidate-full峰值1线程、74.625MiB，29005份采样；没有资源或墙钟限制触发。guardian以GUARD_FAIL/CHILD_EXIT_1收口，清理正常，无遗留本批目标。后4个角色未启动，没有重试、加时或跳过失败继续。

候选stdout记录16组、256次试验、131072字节寄存器检查、failures=0及GOOD_TRAP，进程exit0。离线使用冻结观察器验证状态关系，并从真实输入独立重算1208次退休的完整128位结果，全部一致，高96位同时检查。CSR证据是冻结目标的结束自检、DiffTest及程序摘要，不能写成逐trial打印了CSR快照。

原collector还要求KILL_P、KILL_R、PARTIAL_KILL发生。真实轨迹5283个STATE中pValid=1为0、outready=0为0，最大占用1；1618次ACCEPT均DIRECT_R，ENQUEUE_P/MOVE为0，KILL_R=26、KILL_P=0、PARTIAL_KILL=0。这是实际覆盖缺口，不是简单事件名漏翻译。数值证据不能越过原覆盖门；没有生成正常角色完整validation，不能将完整校准写成PASS。本轮没有据此认定RTL算错，也未宣称P槽取消在所有情况下不可达。冻结源码支持在持续ready前提下P为空；真实父级写回priority1仍有仲裁依赖，其他写回竞争负载可能占用P，须单独评估。

candidate-full活跃1562.610640秒，超过原正式1500秒62.610640秒（4.174%），低于本轮独立校准2400秒。原1500/6300/7200正式合同仍HOLD；不能自动沿用2400作为正式新限额。0f O2与C48正常调用时长仍未测，不能用短bit100或本次候选吞吐外推。没有同核精确重放，没有公平计时加速比；17/20不增加。

## 三项指标

本轮新增加速比、面积、时序均为NOT_TESTED：完整功能校准没有公平RVV计时窗，也未做EDA。下面仅为历史同口径复用，不是本轮新跑分。


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


## 保存与接续

操作ID：SP1-E-B4-R2-20261106-01；@cc77-builder / Agent；2026-11-06T14:49:09.465823+08:00～2026-11-06T15:38:51.986292+08:00。历时包含仿真等待，不等同人工工时。

基点 347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e，分支 local/zjhwork-integration-20261024；默认仍0f＋firstdot V2＋原C8。445份生产源码和277份旧B4文件未变，旧FAIL/授权/锁完整保留。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。

[只读归因](terminal-review/FAILURE_ATTRIBUTION.md) · [实际预算](calibration-budget/RESULT.md) · [下一轮指令](NEXT_STEP.md) · [完整身份](RESULT.json) · [证据清单](EVIDENCE_MANIFEST.json)。
