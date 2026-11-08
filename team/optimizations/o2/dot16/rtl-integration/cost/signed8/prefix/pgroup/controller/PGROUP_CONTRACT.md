# prefix P 压缩分组候选：有限局部验证合同 v1

身份：`dot16-prefix-pgroup-local-v1`。本文件定义一个新实验；准备和静态审查不是实际生成、证明、FU 或成本结果。仅在根端核实资源和冻结输入后执行一次，失败保留原件，不续跑或扩矩阵。

## 目标与修改范围

原 prefix 局部实测的 feature0/1 输入到 P 寄存器路径 arrival 分别为 1.172514/1.163662 ns，名义 1 ns 下均有负 slack。本候选检验一个具体假设：每层旧输入先按压缩器依赖深度、单位门深度和稳定原顺序分组，再把选中 FA 的较晚输入放在 z 支路，能否改善真实映射的 P 路径。

只修改 `VDotCarrySaveRows` 对象。仍为8组 signed8 乘积的512个 partial-product bit，修正常量仍在18、11位，限高仍为63/42/28/19/13/9/6/4/3/2；每次只消费旧层位，输出仍为两条19位 row。metadata 只在 Scala elaboration 中排序，不生成状态。符号交叉项的 AND+NOT 在启发式中记2级，其余 AND记1级；FA/HA按原二输入表达式递推，不做常量折叠。9层/22单位只是可检查的结构估计，不是库时序、PPA或加速比例。

直接源基线为已闭合 prefix datapath 8780 B/SHA `1d02d8a34772e7d9b9947f997f32465f3e946f4b24cacc66159eef7ee10ab3bb`；候选9850 B/SHA `1f9a4c807b30b8aa769e65595ce6b54619b190a5f2b5af1d531413de9970b90c`。source-derivation记录唯一完整对象替换，可逆还原全部原源码。`VDotPrefixFinish19/20`、其他类与整个wrapper保持字节不变；wrapper 8999 B/SHA `912c1a038ef8e9a1ac56cfa349161ae1c582d763acfce5352b08ebde2a227f92`。

架构输入/输出仍128位，dot8使用低64位、dot16使用两半；P每半区两条19位行，R为feature0 signed19/feature1 signed20。仍为原单时钟、同步高有效valid reset、P/R两槽、ready/valid、redirect/kill及metadata协议；数据不新增reset。E0接收、E1转入R、E2最早响应，无阻塞II=1，必须在本次真实FU执行中核验。没有新流水级、时钟频率或吞吐率参数。

## 输入身份与基线

直接测量基线为 `--prefix-local/result.json`：205865 B/SHA `a0c4dd60fddc001f368b71ec283327f2d7fe0874080ac35304e3debe783116d0`，状态 `PREFIX_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE`。其四套生成物、全部prefix SAT gold/gate/script/log及源快照均固定读入；已闭合源码、生成、classpath与清理条件必须成立。

团队控制器由原prefix.py 43201 B/SHA `8f33f550c9b7e74e8190cb5f5a2cfdcc693a783d86ae905ec3e60c7ad10d148c`精确文字派生。derivation必须反向还原全文件；wrapper_binding、command、interrupt、check函数和完整FU执行段逐字节不变。原CSA、rwidth、signed8及初始同边界cost记录仍用于来源与历史差值，不取代直接prefix基线。

源码、合同、控制器、未改的结构校验器、完整原classpath/cache、工具和库均按原固定流程在运行前后核验。新overlay全目录rglob捕获所有class，包含新HeapBit辅助class；不得把原23类清单转授。所有运行产物写fresh output，生产仓、旧runs、输入和缓存只读。

## 真实生成与算术证明

真实编译一次，生成cost/FU×feature0/1四套。每套恰为 `VDotCarrySaveRows.sv`、`VDotElastic.sv`、对应公共top、`extern_modules.sv`及对应 `VDotPrefixFinish19/20.sv`。完整filelist/resource manifest和原firtool注释边界不放宽。公共top与原固定基线逐字节相同，新生成wrapper还须逐字节等于对应旧prefix wrapper，并执行原完整端口、P捕获、高半模式清零、R表达式及符号扩展绑定。

四份新CSA模块须彼此全字节相同，再用原样团队 `verify_csa.py`（14051 B/SHA `e6924e406792fe9e2b82f27be5a591b37466fb7b3ee23ec93935698934e397de`）检查实际生成的SV：完整语法解析、512项lane/bit/sign、每个FA/HA真值表、完整无环DAG、仅前层输入、列权重、每位唯一算术去向及18/11修正恒等式。该证明覆盖全部2^128二值输入，不声称X/Z行为。

必须有477FA、17HA、无被丢弃carry、row0[18]恒1且row1[18]恒0。仅模2^19相等不够：无丢弃的整数heap恒等式和固定行符号才支撑feature1分别符号扩展再作20位和。旧CSA结构PASS不转授新字节。

R级未改变；新实际cost/FU中的完整Finish19/20 SV必须同时匹配旧prefix实际SV及对应既有SAT记录SHA。原两份SAT为19位两任意输入和20位四任意输入的普通模加法，适用域包含新P行；完整gold/gate/script/log复制并核原SUCCESS、exit0和无反例。仅此条件成立时标记精确复用，不重复启动两次求解器，不把它写为新运行。

旧CSA乘法miter的 `UNKNOWN_EXTERNAL_TIMEOUT` 保留在 `historical_multiplication_miter`，注明旧输入来源。新候选自己的乘法solver为 `NOT_RUN`；新算术资格来自实际结构证明与精确复用R模加法证明，不能把旧UNKNOWN写成本候选已经运行。

## FU、综合与时序

新候选真实运行原两态完整C++/vectors、coverage/completion门槛及identity/wen/high/cancel观察负控；不转授旧FU PASS。不改官方或原权威程序及判定行为。

成本仍为完整 `CommonFuCostTop`、原Nangate45库角、1ns约束、BUF_X1 driving/5.0 load、原map和五类STA模板。只改变隔离路径及已声明模块read列表，并以完整逆向检查证明其余模板字节不变；不改ABC目标、库、窗口或端点。记录area、DFF、全部端口、r2r/i2r/r2o/i2o/ready、常量端点及完整raw。

直接报告 `delta_from_prefix`，原feature0 area14171.948/DFF1639、feature1 area17965.374/DFF1678。R与控制路径仍可能失败；P改进不保证1ns闭合。面积≤20000是偏好目标，不是功能或整体时序PASS替代品。结构估计不是验收阻塞；采用决定根据同边界实际结果，不扫描多树或追加整核/长forward。

## 资源与结束

本新实验固定CPU2、absolute nice5、单worker、Java ActiveProcessorCount=1、原4G heap、构建j1和原线程环境。它与Pro2的CPU1整核入口分离，总体不超过用户四核预算；启动前查实际内存和其他任务，内存不足时排队而不扩大堆。

总工程预算精确1200s，单命令仍受剩余总预算约束。完整路径共32个子命令：compile1、generate4、实际结构checker1、FU22、map/STA4。成熟command/进程组/TERM与INT latch/有限回收函数不变；最终完整hash/classpath核验及manifest保存之后、写PASS之前，再检查一次pending signal与deadline，避免末端核验期间收到停止请求仍报成功。外层留60s清理余量。失败保留源、输入、日志、部分输出和终态，不自动续时或重启。

只读资源：resident源码及Git元数据（如工具实际访问）、cost根、原FU根、signed8/rwidth/CSA/prefix闭合目录、本候选source/controller、所列完整coursier/classpath、Java/firtool/Verilator/Clang/make/Yosys/STA及库。唯一可写树是新的 `dot16-prefix-pgroup-20261108-main/local-01`；与任何输入不得重叠。Windows源码拷贝、WSL输出及主仓Git发布分别按实际访问声明，不改现有作业归属或资源锁。

成功状态：`PGROUP_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE`。只有新的局部算术/FU及同边界成本资格；parent、fullcore、application performance和core cost仍false。不替换生产默认，不启动EMU，不操作视频原件或PDF/LaTeX。

入口为新controller/pgroup.py，使用现有八个已核路径参数，其中新增 `--prefix-local`；固定 `--cpu 2 --budget-seconds 1200`，`--output`必须不存在。准备期不执行该入口。
