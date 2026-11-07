# CSA 后 P 级 prefix finish 的有限验证合同 v1

合同身份：`dot16-csa-prefix-local-v1`。这是隔离候选的生成、组合证明、FU 行为及匹配成本实验。当前文件和控制器仅已准备、静态审查；未据此运行 Scala、Verilator、Yosys、STA 或 guest，尚无新候选 PASS。

## 固定输入与修改边界

直接基线为已闭合 CSA `local-03/result.json`：109822B，SHA256 `21510c330817f12c03426ac0ca262331c4ff088d90e33b2be1fefae0c605707a`，状态 `CSA_REUSED_GENERATION_ARITHMETIC_FU_AND_COST_COMPLETE`。该结果是新参数 `--csa-local` 的固定入口；其真实四套生成物、源码快照、完整结构证明和原乘法 miter 日志均只读。

基线 datapath 为6454B/`62ace0342070bc2a40f57b999c8aa94d376543a4cc79d455cf69e6083742488c`，wrapper 为8789B/`4a525d2e8ead5cc10a193d9724342162af4ffebd130c58ad7c606093849ac1c8`。候选由首席实现，位于控制器目录的同级 `../source`：datapath `1d02d8a34772e7d9b9947f997f32465f3e946f4b24cacc66159eef7ee10ab3bb`，wrapper `912c1a038ef8e9a1ac56cfa349161ae1c582d763acfce5352b08ebde2a227f92`。固定 source-derivation SHA 为 `2c1fd758ba8ebb22537ee1ab776c3e9418331b16d5aa2064ff84163674d61caa`。

控制器必须核对候选 datapath 等于完整基线加唯一声明的 append；wrapper 的两处替换反向还原全部基线字节。控制条件、时钟、复位、接口、P/R 状态、模式捕获和观察接口因此保持源级一致。生产目录、既有 runs 和缓存只读。控制器由冻结 CSA v3 `csa.py`（34059B，SHA `07d93e73072304a64b7bc415820b2856a27b2d74a01e649a2e141f78e8adf0f7`）作完整可逆文字派生；`controller-derivation.json` 在运行时再次还原并核其完整 SHA。

## 数据通路与实际生成绑定

保留128位架构输入/输出、低/高64位各8组 signed8、原 P/R 两槽与 ready/valid、redirect/kill 和同步高有效 valid reset。P 内保存每 half 两行19位；feature0 的结果状态为19位，feature1 为20位。数据与 metadata 不增加复位。原上升沿 E0 接收、E1 P→R、E2 最早响应和连续无阻塞 II=1 约定保持；仍由本次实际 FU 检查核实。

四次真实生成分别覆盖 cost/FU × feature0/1。每套完整 SV 集合为原 `VDotCarrySaveRows.sv`、`VDotElastic.sv`、对应公共 top、`extern_modules.sv` 加 `VDotPrefixFinish19.sv` 或 `VDotPrefixFinish20.sv`。完整 filelist 必须恰好覆盖五文件；blackbox resource manifest 必须恰好覆盖 CSA 和对应 prefix 两模块。公共 top 与原固定生成物逐字节相同。external 文件仅接受旧实际 firtool header 加两个完整固定 external-module 注释，两个注释可交换顺序，其余字节不放宽。

全部四个 CSA 模块与 `--csa-local` 对应文件及彼此逐字节相同。新 wrapper 逐个核对原 CSA 实例、实际输入切片、P 的完整19位捕获以及 dot8 接收时高 half 置零；新 `prefixSum` 只能为本 feature 的唯一 prefix 实例：

| Feature | 模块 | rows 输入顺序 | R 写入 |
|---|---|---|---|
| 0 | `VDotPrefixFinish19` | `pRows_0_0`, `pRows_0_1` | `pCtrl_exceptionVec_2 ? 19'h0 : _prefixSum_result` |
| 1 | `VDotPrefixFinish20` | low0、low1、high0、high1，各由 `{pRows...[18],pRows...}` 符号扩至20位 | `pCtrl_exceptionVec_2 ? 20'h0 : _prefixSum_result` |

核对全部非数据顺序赋值、架构输出符号扩展、prefix 输出线宽和 R 数据线宽。原普通加法 R 表达式不用于检查新候选。未知 emitted 形态拒绝并保留原件，不能为取得 PASS 宽泛删除/规范化表达式。

## 两类组合证据分别记录

复用的 CSA 结构报告必须是完整原件，SHA `9483d70f24876e7c89281e559d3d062355c0787e38a7f3fd7ab9cf36d3cd8ad6`，并与固定 local03 result 内完整对象一致。要求 `all_inputs_equivalent=true`、完整解析、相同实际 CSA SHA、`discarded_carries=[]`、row0 MSB=1 和 row1 MSB=0。这组更强整数不变量支撑直接解释保存行的有符号值。八项真实和范围为[-130048,131072]；两 half 的16项范围为[-260096,262144]，均适合对应最终 signed19/signed20 解释。

旧乘法 independent miter 仍为 `UNKNOWN_EXTERNAL_TIMEOUT`；原日志 SHA `a9175ff5e52888f37d8cf8eeeb1673f6975e32cc8e08687be91f3db2cc845b2b` 完整保存，`solver_equivalence_proved=false`、`retried=false`。本次不调用旧 checker、不重试或延长该乘法 miter，亦不把新 prefix SAT 写成乘法 solver PASS。

新证明只读取实际生成的 `VDotPrefixFinish19/20.sv`。两个小 miter 将其与同宽普通模加法比较：19位两个独立任意输入，20位四个独立任意输入。DUT 算术不由控制器重造；实际完整模块头绑定名称、端口数和位宽，Gold 仅实现普通同宽求和。每个 Yosys 求解器30s、单命令60s；一次尝试，无自动重试。两次命令均 exit0 且各明确出现一次 SAT SUCCESS、无反例/ERROR，才允许后续 FU/cost；超时、错误、反例或缺成功标志一律 FAILED。结果使用独立的 `prefix_miters` 字段，证明范围仅实际组合 prefix 模块。

## FU 与匹配成本

沿用原完整、已固定的两套 C++、vectors、coverage/completion 检查器以及 identity/wen/high/cancel 观察负控。本次必须真实 lint/build/运行/分类，旧 FU PASS 不转移。完整 FU 流程与原 v3 控制器逐字节一致。

成本使用原完整 `CommonFuCostTop` 边界、Nangate45 库、nominal 1ns、ABC driving/load（BUF_X1/5.0）以及原五类 STA 模板。相对原映射模板，只允许精准替换模块 read 列表并更换隔离路径；相对 CSA 映射列表仅新增 prefix 模块，read_liberty、其他算法和约束顺序不变。对映射及 STA 模板作完整逆向文本检查。记录实际 cell/library area、DFF、完整端口、r2r/i2r/r2o/i2o/ready、常量端点和时序是否满足。

新增 `delta_from_csa` 的面积、DFF、各类 arrival/slack，直接使用实际 CSA local03 baseline。其 DFF 为 feature0=1639、feature1=1678；记录实测差值，避免旧1637/1675估计形成错误拒绝。DFF 相等不是本合同新增的 PASS 门槛；任何差异由首席结合实际网表判断。保留旧 rwidth、signed8 和最初相同边界面积差值作历史参照，不能把它们混为本次新增收益。面积20000只作目标记录，不以目标内面积或单条时序 PASS 代替完整路径说明。

## 资源、运行与闭合

固定 CPU1、absolute nice5、单 worker；所有子进程继承同一 affinity/priority，构建 `-j1`，原线程环境限制不变。总工程预算精确1200s，每命令还受剩余总预算约束。完整路径的计划命令数为33：编译1、生成4、新 SAT 2、FU22、map/STA4。未到后续阶段不得补列为已执行。

沿用原 `command()`、TERM/INT 单次 latch、安全点、独立进程组、有限 cleanup、reaped/group_absent 记录。1200s 是工程 deadline；外层执行应留出成熟 stop_group 的有限回收及最终回执余量，不能恰好1200s强杀。任何失败保留源、日志、部分输出和回执；不更改旧 runs、不自动续跑。

只读范围包括 `--repo` 的已固定源/辅助脚本、`--cost-root` 的 generation-01/nominal-01、`--fu-root` 的 flag0-02/flag1-01、三处 signed8/rwidth/CSA baseline、本 controller 与同级 source、配置列出的完整 classpath/cache/tool/library 和 Verilator/clang/make 系统依赖。唯一可写树为 fresh `--output`（含 tmp、快照、classes、生成物、日志、FU obj/bin、mapped 输出），且不能与任何输入根包含或重叠。调用方必须据实际路径完整声明资源，源码目录存在不构成新执行授权。

所有 pin、快照、完整 classpath、缺省不存在资源以及新生成输入前后审计；实际 FU 二进制、生成文件、证明脚本、结果和 map/STA 关键身份保存。`inputs.json`、`final-artifact-pins.json` 与 `result.json` 沿原格式，新增证据通过完整快照和 manifest 纳入闭合。

完成状态为 `PREFIX_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE`；新算术/FU 成立且 local cost 已记录后，parent/fullcore/application/corecost 仍为 false。未进行全 FU 顺序 SAT、真实 parent、整核、应用性能或 core cost 资格验证；不替换生产源码、不发布默认、不启动新 EMU。

## 运行入口形态

保持源目录与控制器目录为同级，不把根实现的源码移入控制器目录。首席核实际路径与资源声明、冻结完整输入后，入口形态为：

```text
python3 -B <candidate-root>/controller/prefix.py \
  --repo <resident-source> --cost-root <closed-production-cost-root> \
  --fu-root <closed-original-fu-root> --signed8-local <closed-signed8-local03> \
  --rwidth-local <closed-rwidth-local01> --csa-local <closed-csa-local03> \
  --output <fresh-prefix-local01> --cpu 1 --budget-seconds 1200
```

以上占位符必须由已核闭合路径替换，不可据示例猜目录。该入口未在本辅助开发任务中执行。
