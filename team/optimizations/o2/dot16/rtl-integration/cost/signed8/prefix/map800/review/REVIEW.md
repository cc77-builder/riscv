# prefix feature1 ABC-D800 两命令实验有限静态审查

## 结论

最终 `map800.py` **11,997 B / SHA-256 `f854197eb5b3291d927d8cdbb88d6d1192f0411542c5a0d95ca88dfc64d8421c`** 与合同一致；未发现影响本次有界两命令对照实验的剩余静态缺陷。可以继续按既有授权和合同进行这一个 D800 点的实际映射/STA，结果出来后再决定是否保留。

本结论不表示已执行计划或工程入口，也不表示 D800 已改善面积、时序或应用性能。审查仅使用云端文件的读取、SHA、JSON/AST 检查以及独立文字替换核对，没有访问 PC/Pro/网络，没有执行被审 `run`、helper、Yosys、ABC、STA 或仿真，没有改动执行源或实际输入。

主端预告的 selfpins/快照比对补改已纳入最终版本。我另指出了正常退出时未复查单阶段截止的窄边界，主端用两行检查闭合；未为此引入新框架或额外实验。

## 1. 核实的身份与原始证据

| 对象 | 字节数 | SHA-256 |
| --- | ---: | --- |
| 最终 `map800.py` | 11,997 | `f854197eb5b3291d927d8cdbb88d6d1192f0411542c5a0d95ca88dfc64d8421c` |
| `CONTRACT.md` | 2,475 | `62cb59ac9172e0a16dff6cf2690ec2158650177825dbf027538288c277016f73` |
| 原 prefix 实际 result | 205,865 | `a0c4dd60fddc001f368b71ec283327f2d7fe0874080ac35304e3debe783116d0` |
| 原 prefix inputs manifest | 131,374 | `1afacb22c143705355ffed93b62824b2a02153e799b003bcc7f92dba1b10c219` |
| 原 prefix final artifact pins | 18,231 | `07d4a614ba2b7fd06652290d266023ae405881578cc370fa86d368086baa3451` |
| 原 process helper | 12,865 | `db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3` |
| 原 cost helper | 3,199 | `bee29ddcfb0b1b6281dd8e05637bd9a032587a7b5ec18abaf85e08dda26be209` |

前三个原始实验文件的副本位于 `source-review/prefix-candidate-v1/actual-result.json` 与 `actual-manifests/`。helper 本地证据分别为 `source-review/production-cost-review/process_helper.py`、`dot16-cost-helpers.py`；后者虽本地文件名不同，完整 SHA 与控制器引用的 `cost_helpers.py` 相同。

实际原映射/STA 文本来自 `verification/prefix-critical-path-review-01/mapping-constraints.json`，该捕获记录 SHA 为 `bbcbc32f380bc0b5b4a7254e7debdc449d4c29d1be97423a5a9405e45fab3c87`。独立核对其中 feature1 的三段完整 text，其 UTF-8 字节长度与 SHA 均等于记录值，并且与原 final pins 一致：

- `map.ys`：1,531 B / `cef763ad586c74c252125d4a19c4e7949364494105eb364578e3d13e9a3bde2c`。
- `timing.tcl`：2,625 B / `fd7b68d1a9b7a4981b627b7194b89a7ce25c4b65a9cf1e0bdb402b1e053934a2`。
- `abc.constr`：37 B / `6710077f5f66e43fcb9993d501d605c2a9a99549566ad74fa987bc839a803c89`。

因此读取顺序、字符串匹配和原约束的判断基于实际冻结文本，没有根据旧报告概述猜测脚本内容。

## 2. 固定输入与输出路径

原实验固定为：

`/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-20261107-main/local-01`

唯一允许的新输出为：

`/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-map800-20261108-main/local-01`

入口要求输出是绝对、已规范化的路径，父目录和末级名称精确相等，且输出不存在、不是 symlink。原 map/STA 输入和四个 SV 始终从旧冻结目录只读；新 mapped.v、mapped.json、报告、日志、tmp 与快照写入新输出。未发现仍指向旧 mapped 输出的写入路径。

原 result、inputs、final manifest、两个 helper、Yosys/ABC/STA 和库固定 SHA。四 SV、原 map.ys/timing.tcl/abc.constr 的预期身份来自自身 SHA 已固定的旧 final manifest；工具与库身份还与旧 inputs 的原 recipe 核对。这样复用的是本次实际需要的闭合输入，不要求重新核验与两命令无关的整个 Scala/Verilator 开发环境。

最终版本先建立自身控制器及合同 pins，再复制每个快照并核对复制物 SHA 是否等于该原输入 pin；同名冲突会失败。生成脚本、约束副本与所有快照形成 `generated_pins`，与 originals 一起写入新 inputs。两个工程命令结束后重新核对全部原输入和生成 pins，最后又检查 pending signal 与总 deadline，然后才写完成状态。

`-B` 是入口的明确要求，确保导入旧冻结 helper 时不产生 pycache。helper 导入前已经比对 SHA，module 注册 `sys.modules` 后执行定义；读到的两个 helper 没有此次导入会启动工程任务的顶层调用，process helper 的 CLI 仍受 `__main__` guard 控制。

## 3. 实际读取顺序与完整逆变换

原 feature1 map 的四条 `read_verilog` 顺序确为：

1. `VDotCarrySaveRows.sv`
2. `VDotPrefixFinish20.sv`
3. `VDotElastic.sv`
4. `CommonFuCostTop.sv`

它们均带 `-sv -DSYNTHESIS`，对应控制器 `required[3:]`，不是从文件名排序推断的顺序。映射执行直接读取这些原冻结 SV；本次不引入 Pgroup，也不生成新 RTL。

我以原捕获文本独立进行同样的文字替换，没有调用候选函数：原 map 中 ` -D 1000 -constr ` 恰好一次，新 map 中对应 ` -D 800 -constr ` 恰好一次；只替换旧 mapped 输出前缀与这个 ABC 参数后，反向替换可以恢复整个原 map。STA 只改旧 mapped 输出前缀，反向替换也能恢复整个原 STA。

固定原文及完整逆变换共同限制了变更范围：原四 SV 读取路径不变、CommonFuCostTop 边界不变、综合与检查命令不变、库与 ABC 可执行文件不变；ABC 的约束仍为 BUF_X1 driving cell 与 5.0 load。STA 仍读取本次新 mapped.v，保留：

- 1.0 ns 时钟周期。
- 0.05 ns clock uncertainty、clock/input transition。
- 0.1 ns input/output delay。
- 5 fF 输出负载。
- 原 `5K_hvratio_1_1` wire-load model。
- 原五类 r2r、i2r、r2o、i2o、ready 路径及 setup warning 检查。

所以 ABC 映射目标的改变没有暗中放宽 STA 条件；ABC 内部 delay 也没有被直接转成实际芯片频率。

## 4. 两命令预算、停止与回收

默认 plan 路径不创建输出、不启动工程子进程；显式 `--execute` 后只有两处工程 `command()` 调用：Yosys map 上限 300 秒，OpenSTA 上限 60 秒。总 deadline 从前置核验之前开始计，固定为 420 秒；固定 CPU affinity `{2}`、nice 5，使用独立 TMPDIR、C locale 和单线程环境。没有扫描多个 delay 值、重试、续时或后台再启动行为。

每条命令在新输出 cwd 以独立 session/进程组运行，stdout/stderr 合并为独立日志，记录 PID、起止与预算。等待间检查中断、总时间和该阶段剩余时间；成功要求退出 0 且进程组消失。异常路径沿用精确原 process helper 的有限 TERM/等待/KILL/等待回收，记录 reaped/group_absent；失败会保留日志、部分产物和 `FAILED` 状态。合同已要求外层保护覆盖回收，不在本审查中重新设计该机制。

### 已闭合的窄边界

中间版 11,900 B / SHA `88352ed345ad38144a37d7aa5c66ecdb915179ced2b0a1a4532895e3b9601e5b` 已有等待中的阶段超时判断，但 `poll`/`wait` 正常返回后只核退出码与进程组。恰在阶段截止附近结束时，可能尚未超出 420 秒总预算而未再次检查自己的 300/60 秒边界。

最终版在正常退出后增加 `check()` 和 `need(time.monotonic() <= until, ...)`，之后才检查 rc/group。独立回读确认该顺序与最终 SHA 一致。这两行闭合了指出的具体正常退出路径，没有改变原 helper 或扩大测试范围。

最终全部输入哈希和 mapped 输出 SHA 计算后仍调用 `check()`，再更新 `PREFIX_FEATURE1_MAP800_COST_COMPLETE`；未发现先给成功状态再检查中断/总预算的路径。

## 5. 结果核验与资格边界

原 feature1 result 的 1,678 DFF、cell area 17,965.374 与完整接口身份被固定。独立读取实际原结果确认接口为 **220 个端口、2,888 bit**。

新映射结果按完整 cell type histogram 和固定 Liberty 面积表独立求和，与 Yosys 打印面积对照；任何未知 cell 会失败。完整端口 direction/width/offset 必须与原接口相等，DFF 数必须维持 1,678。STA 要求退出 0、无 Error/not-found、恰好一个完成标记；原 `parse_path` 检查有限数值、arrival/slack 一致性和单一路径，五类报告都必须存在。原 `constant_warnings` 从本次 mapped JSON 的真实常量位判定可接受端点，不是单纯忽略所有 warning。

结果保留面积、DFF、各路径 arrival/slack、nominal_setup_met、相对 D1000 的全部差值、mapped.v/mapped.json SHA 和输入/回收状态。nominal setup 是否满足与实验流程是否完成分开记录；即使 1 ns 仍违例，也不会伪写成时序达标。

`unchanged_rtl` 和 `rtl_functional_evidence_reused` 的依据是此次精确相同的冻结 RTL。结果明确 `mapped_netlist_equivalence_tested=false`，没有用旧 RTL/FU PASS 声称对新映射网表执行了门级等价检查。合同限制于独立 FU 的映射和 pre-layout setup 观察；不产生新 parent、整核、应用、功耗、hold 或版图后资格，不自动修改 production default，也不改正在使用的 prefix 整核输入。

## 后续边界

可以按本合同执行这一个点并审读实际面积和全部路径，尤其是最差 setup slack 的变化。最终是否保留 D800 必须依据实际记录及面积代价；本静态审查没有预测收益。没有需要为本次准备追加的形式化、整核、应用或参数扫描门槛。

审查开始：2026-11-08 02:46:06 UTC。最终源码、合同与阶段退出补改回读：2026-11-08 02:48:45 UTC。仅新增本 `REVIEW.md`。
