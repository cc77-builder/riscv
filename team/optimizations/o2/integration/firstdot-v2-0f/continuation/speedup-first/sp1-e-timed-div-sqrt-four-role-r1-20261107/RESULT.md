# 第20项四角色 R1 有界验收结果

第20项四角色 R1 已通过：候选正常、0f正常、候选重放和0f重放全部完成，九格配对及两次精确重放通过。正式验收由18/20推进到 **19/20**；第19项继续 HOLD。默认仍为 **0f＋firstdot V2＋原C8**，没有切换或上传。

记录 **102**，操作 ID `SP1-E-TIMED-DIV-SQRT-FOUR-R1-20261107-01`，执行者 **cc77-builder / Agent**。开始 2026-11-07T16:14:37.817328+08:00，归档记录 2026-11-07T19:34:48.366405+08:00；执行等待不算人工投入，UTC标注不能代替单调预算计时。分支 `local/zjhwork-integration-20261024`，Git基点 `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`，工作树源码以冻结清单为准。

## 最小修订和宿主准入

原记录101第07项使用 `rows[2]`，实际命中dataset0/vfsqrt/repeat0首调用，不属于repeat2～5计分窗口。本轮只将该负控改为语义键 `(d, op, r)=(0, 0, 2)` 唯一选行，断言正好命中一行且周期实际增加10000；保留原比较口径。原第01～06项方法AST、正常夹具和运行模块不变，复用6项PASS；第07、08两项新测通过，包括授权拒绝和冷进程导入。宿主外部监督耗时 3.190177 秒，清理成功。

118项执行冻结全部匹配。runtime runner/adapter/protection/supervisor/watchdog及各比较模块相对上一轮字节未变；只更新本轮操作身份、用户授权绑定及宿主修订和证据。历史bit100真机拒错证据经身份、输入、收据和日志核查后复用，没有启动第5个目标。

## 四角色完整运行

|角色|结果|单调计时活动秒数|guest cycles|完整窗口/算子|峰值线程|峰值RSS MiB|
|---|---|---:|---:|---:|---:|---:|
|candidate-normal|PASS|3389.801730|1265777|54/432|1|74.629|
|baseline-normal|PASS|3274.078525|1265427|54/432|1|72.375|
|candidate-replay|PASS|2698.085476|1265777|54/432|1|71.625|
|baseline-replay|PASS|2741.615482|1265427|54/432|1|72.750|

四次正常角色均为 `PROTECTION_NORMAL_PASS`。每角色覆盖 **54窗、432条DIV/SQRT算子**、完整128位结果、源值、CSR及退休/父级接收/输出绑定。总216窗、1728条算子是同一覆盖的四次执行，不是216个独立用例。候选与0f九格配对通过后才启动两次重放；两次均 `EXACT_REPLAY_PASS`，包含 rows、t13、div_binding、观察摘要和计数，且均有独立真实运行身份。

## 预算与资源

- 每角色均未超过4800秒和200万guest；4次启动、无重试。
- 目标活动累计 **12103.581212 / 19200秒**。
- 执行阶段宿主核查累计 **27.808091 / 900秒**；前置宿主准入另为 3.190177 秒。
- 外层监督 **12131.477884 / 20100秒**（约3小时22分11秒），`GUARD_PASS`，所有本轮进程已清理。
- 绑定CPU4、整组最多4线程、RSS12GiB和日志2GiB合同保持；实际目标峰值1线程、RSS约74.629MiB，目标stdout/stderr合计25345676字节。

预算依原监督器 `time.monotonic()` 核算。各角色UTC起止差值与单调耗时不相等，原时间戳和差值完整保存在 [CLOCK_AUDIT.json](CLOCK_AUDIT.json)。原因未确认，本轮未调整时钟或服务；不得用UTC相减替代预算或推导性能。此项为审计备注，不新增门槛，也未触发补跑。

## 九格性能保护

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

均值采用冻结repeat2～5；first/warmup保持完整检查。九格最大退化0%，八格不变，一格下降0.25周期。这只证明本镜像的DIV/SQRT共享资源保护满足原2%门槛，不能改写为VDOT或应用端新加速比。

## 版本与证据保全

收尾核查确认445份生产源码、398份候选源码、505份受保护历史文件和118项冻结输入未改变。原记录99超时、记录101宿主FAIL、各旧锁及本轮锁完整保留。没有改RTL/目标镜像，没有GNU或全核构建，没有EDA、默认切换、Git提交或上传。默认仍为0f＋firstdot V2＋原C8；候选保持待最终选择状态。

## 结论与必要缺项

第20项 **PASS**，SP1-E正式进度 **19/20**。仅第19项整核S0/S1反压/P入队及相关取消覆盖与重放仍HOLD；本轮保护结果不替代它。下一轮建议只设计缺失时序观测与定点触发合同，参见 [NEXT_STEP.md](NEXT_STEP.md)，不自动执行。

## 三项指标留档

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


## 证据入口

- [执行合同](CONTRACT.json)、[执行冻结](EXECUTION_FREEZE.json)、[授权](RUN_AUTHORIZATION.json)
- [宿主结果](host/RESULT.json)、[四角色摘要](RUN_SUMMARY.json)、[批次结果](target-01/batch.json)
- [配对结果](target-01/qualification.json)、[候选重放](target-01/candidate-replay.json)、[0f重放](target-01/baseline-replay.json)
- [独立算术/身份收尾核查](POST_RUN_AUDIT.json)、[数据档案](RESULT.json)、[证据manifest](EVIDENCE_MANIFEST.json)
