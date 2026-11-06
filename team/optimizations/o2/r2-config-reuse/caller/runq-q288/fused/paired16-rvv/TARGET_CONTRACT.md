# paired16 四臂完整 Q 目标合同 v1

合同 `r2-s3-runq-paired16-rvv-target-v1`，属于既有 `20261106-LiZufan001-paired16-rvv-pro6` 叶级包。主 Pro 已协调本阶段的单核目标构建和实际 ELF 检查；EMU 启动仍按当时资源安排另行登记。本合同冻结在新目标运行之前，旧 host 合同、已筛选源码及证据保持原样。

## 比较对象与边界

同一 ELF、同一既有 T17 硬件、正常 reference、flash、seed1、128MB guest RAM、12M周期上限；无硬件或NEMU构建。四臂如下：

| arm | 名称 | 实际入口 | 原方法 kind |
| --- | --- | --- | ---: |
| 0 | P，guarded paired16 | `q288_paired16_rvv` | 5 |
| 1 | G，GS32v2 | `q288_gs32_rvv` | 5 |
| 2 | TA，原 tail-vdot | `q288_tail_vdot` | 0 |
| 3 | FR，原 fused RVV4 | `q288_fused_rvv4` | 5 |

P完整函数字节必须等于host ELF `fb3c030efa7aa347029a69f6aabe82c912cbbb85294b27cf407a01ea58a314f3`；G完整函数字节必须等于v2筛选ELF `8316e32939385653c1c4f7e257443529c19dc71df8b5991552a2ab1453069daa`。TA/FR全函数SHA分别固定为 `b318b99344d0ceabb2a5cab6ce671ab2bfcb189e4aacc9ffccb18488165971f3`、`66a12c0ec3cb7c0d1cdceadf04e4c658607438d83a2a958892100422343117ab`。完整共同计时器逐字等于既有 `610c499f46f1fe73074f626d8990bdcbdbc5f78c30ce8fc4a835495b0e392faa` ELF中的 `split_measure`。

计时边界是原预打包288×288、GS32、八行tile的完整 Q 函数及固定共同timer开销。P的完整入口guard和分派包括在内。原W/Ws/X/Xs布局、标准三组fixture、golden、FP消费顺序、ABI/CSR与末组完整slots合同不变。结果不包含quantize、packing、K768、完整token或模型运行；既有更快合格RVV对照不能被旧FR替代。G是否已有历史目标资格由其原始运行及串行复核判断，本合同始终单独绑定实际筛选v2字节。

## 固定调用计划

先按P/G/TA/FR分别执行标准dataset1，再分别执行dataset2，共8个功能调用；第一次标准dataset1调用之后保留原guest判定器的五项故障控制。随后增加一个计时外P完整调用，逻辑dataset3表示独立fullmin fixture：82944字节packed W和288字节X全为−128，使用原row-major Ws和标准dataset0的Xs。

fullmin每行每组精确点积为524288，仍按g0→g8执行原两次FP32乘法及累加。其288个golden由独立C/Python oracle一致生成，并绑定host min-min输出SHA `66c4c3af41f5c15c3228ce31c1bfc1be67e438e566d1def9499e6daa6b96e525`。最终slots应为八份低32位 `0x00080000`、高96位全零。新输入有独立前后guards，不复用原 `q_packed` 的guard检查；派生min_judge检查全部输出、槽、guards、七个context字段及原CSR，读取CSR前不重置状态。原三组数据、原judge/prepare/五故控不修改，只在新生成副本添加这一功能分支。

之后计时顺序固定为：

```text
FR, P, G, TA, FR / FR, TA, G, P, FR
```

每窗前保持原同方法selfwarm，warm和timed调用分别执行相同prepare，各自完成后判定全部输出/槽/guards/context/CSR。总共29次完整调用：P7、G6、TA6、FR10，即9功能、10selfwarm、10timed；总完整输出判定数8352。TA仍为6次，custom协议总数仍为62209=6×10368+1独立probe。fullmin不是性能样本，不增加第11个计时窗口，也不形成fallback周期结论。

## 实际 ELF 和目标证据

生成后实际GNU编译，旧官方程序与AM库只读。检查ELF/BIN对应、四个全函数、共同timer、原全部输入及golden、四臂指针/kind/顺序数组、新fullmin数组与golden、29调用计划。保留原四个编译数组负控，并覆盖新增fullmin X/golden的绑定。固定上游 `.gz` pin按其既有解压payload语义检查，同时记录压缩文件物理SHA，二者不混用。

基于实际链接地址，分别解释四臂的原三数据集，以及P的fullmin函数路径，检查完整输出、精确footprint、ABI/CSR、slots及正常返回。用于计时解析的每臂PC/word流明确选标准dataset0；不假设数据相关guard的所有输入都走同一路径。fullmin的host fallback路径与目标功能PASS分开报告，不冒充已取得其计时外退休trace。

运行先使用既有团队bit100故障reference wrapper，对独立probe要求精确PC→高半bit100差异→ABORT→exit1拒绝链；该wrapper仅损坏返回DiffTest的状态副本，不改变原NEMU或执行状态。负控完成并串行验收后，才允许两个隔离正常reference进程。正常运行必须有实际DiffTest enabled banner、正确reference身份、完整guest功能/调用证据及GOOD TRAP；十窗完整退休PC/word、四次CSR采样、fence与计数器须相互一致；全程custom接受/完成/提交及62209个PC顺序匹配实际ELF。

两正常EMU可在各自单线程构建、各自CWD/输出、不同获配CPU上并行；主机墙钟只作执行成本。worker仅负责进程与终态回执，不调用动态模型/解析器。两个进程都结束后，在主线程依次分析recovery和replay，避免 `sys.modules` 竞态。replay要求十窗样本和完整custom PC序列一致，不作为新统计样本。所有源码、ELF/BIN、manifest、验证报告、工具、硬件/reference/flash身份均在运行前后核对；失败原证据保留，不能靠改合同重解释通过。

## 预先固定的选择规则

保留全部十窗与四个FR锚；若 `100×max(FR)>101×min(FR)`，结论为HOLD_CONTEXT_VARIATION。否则仅当对于B∈{G,TA,FR}均满足 `200×max(P)≤199×min(B)`，P才获得本固定计划的优先资格，即最慢P对最快的每一对照至少快0.5%。不根据新结果调整次序、对照、阈值或删样本。

若正确性/目标证据未闭合，不形成性能结论；若未取得有意义的完整Q收益，不扩展P到完整forward。通过也仅表示标准dataset0、同方法selfwarm、固定Q快路径的条件性结果，后续真实消费者、K768路由、量化/packing成本、真实输入guard命中率另行评估。稳定入口不会自动改变。
