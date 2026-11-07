# whole8+narrow：同镜像完整 Q288 有限筛选 v1

合同：`r3-dot16-whole8-narrow-q288-v1`。本合同在首次 GNU 构建和目标运行前冻结；结果另行记录，不把源码推导、旧 PASS 或指令减少当作新性能结论。

## 目的、边界及来源

人工于 2026-11-07 11:30 UTC 要求在四核 forward 仿真期间继续有较大改进可能的优化。本小试直接比较新 N 与当前已通过 whole2 的 W，保留较快合格 RVV P 及 FR。只派生团队已有源码和运行器，不修改官方程序、RTL、NEMU、DiffTest、GNU 工具或 AM 库，不重建 EMU，不改变在途四臂 forward 的输入、profile、CPU affinity 或预算。

新源码为 `narrow.py` 和 `narrow_q288.py`；前者复用固定 `whole8.py`，后者对现有 `q288-consumer/image.py`、`run.py` 做可逆且限定数量的文本派生。冻结实验源和所有失败证据保留。只在本账户已有 whole2/consumer 范围和独立运行目录写入，不建新检出，不触碰共享 index 或正式报告。

基底 builder SHA 为 `211e35d232bc941950e20dee1633a1bea90148ba3b02e90ae3e540e0cf4e4d0d`，runner SHA 为 `ed585cfa849358b4ee28eae0cd46afeb56ca089a77c09acdc359b36e765fb55e`。plain-D 基底 ZIP、whole2 ZIP、fixture/golden、原编译工具和 AM 输入继续由基底 builder 的固定 SHA 约束。whole2 实际 412B 函数 SHA 为 `b2b5b7fa44ecf9646a7c07fdaf971df8fad6430aec58161ffc3e2c3332d934a6`。

## 规格与微架构适用范围

接口沿用固定 Q288：M=K=288、GS32、VLEN=128、RV64/lp64d 的 56B context、36 个八行 tile、每行九组。权重、X、scale 布局、288 个逐位 FP 输出、最终八个完整 128 位 slots、guards、CSR 和五项故障控制均沿用原合同。返回 VL8/e8/m1、vstart0、vcsr7、FRM0；不重新定义 fflags 规则。只改变软件调度，没有新时钟、复位、FU 端口、流水时延或吞吐承诺；沿用现有 dot16/O2/T14 硬件。

N=`q288_dot16_whole8_narrow` 在 whole2 的两段 W 加载各用一次 `vl8re8.v` 取代四次 `vl2re8.v`，同样覆盖 256B，X 仍一次 `vl2re8.v` 取 32B。随后用以下六条替换原 18 条整数合并与打包：

```asm
vsetvli  t6, zero, e32, m8, tu, mu
vadd.vv  v0, v0, v24
vsetivli zero, 16, e32, m4, tu, mu
vnsrl.wi v16, v0, 0
vsetivli zero, 8, e32, m2, tu, mu
vnsrl.wi v10, v16, 0
```

第一条 rd 非零使 VL=VLMAX=32。m8 加法与原八条 m1 加法对全部 32 个 e32 lanes 执行相同的模 2^32 加法。两级 64→32、逻辑右移零依次选择 lane 0,2,…30 和原 lane 0,4,…28，与旧打包完全相同；证明允许任意高 lanes，不依赖高 96 位为零。v0…v7 完整结果保留，v8/v9 累加器及随后 FP 转换、乘法、加法次序不变。t6 在后续读取前重写。源/目的不重叠且组对齐，最大 EMUL=8，无饱和或舍入。

固定函数预期 78 条/312B、每 Q 12,990 条动态架构指令（whole2 为 21,090）；16 个静态 dot16 点不变。独立从旧完整机器字重建新 load、六字替换和两条分支后，预期完整机器 SHA 为 `050bc3db3e2a70bd6e5409cbf9c139868008e8ccb18776b7e0e7104e6a554b75`。实际 GNU 必须逐字节相等。上述数量不等于微操作数、周期或应用收益。

## 同镜像调用计划与真实性

| 槽 | 臂 | kind | 完整 Q 调用数 |
| --- | --- | ---: | ---: |
| 0 | P：原 paired16 RVV | 5 | 6 |
| 1 | W：原 whole2 | 0 | 6 |
| 2 | N：whole8+narrow | 0 | 7 |
| 3 | FR：原 fused RVV4 | 5 | 10 |

顺序保持 `(3,0,1,2,3,3,2,1,0,3)`，即 FR/P/W/N/FR、FR/N/W/P/FR。八次普通功能调用逐臂覆盖 datasets1/2；第九次对 N 做 all−128 满幅检查（每组 524288，288 输出和八个完整 slots）。十个窗口各一次同臂 warmup 和一次计时，仍为 29Q、8352 输出、10 窗口、五项共享故障控制。dot16 计划数量仍为 67,392，另一次 dot8 probe；没有声称验证全部退休数量。

基底 main.c 原本在 arm2 做满幅，直接保留它；保留全部 judge、guards、故障控制、timer 和循环。data.h 只改合同、W/N 声明、wrapper 和原 W methods。fused.S 保留全部原基底，追加固定 W 和 N，逐段可逆。实际 ELF 校验 P/W/FR 完整函数 SHA、N 完整期望机器字、wrapper 地址、控制数组、fixture/golden、timer/probe；保留新 ELF/BIN 身份和八条原 GNU 命令的真实回收结果。调用计划和满幅归属同步到 manifest、runner 和 profile。

## 四核内有限并发

当前四臂 CPU0–3 各单线程，已核合同为 shared total 最多四个 CPU，无主机或 CPU 排他要求。新编译及准备依次固定 CPU0、单线程、低优先级，输出隔离。准备结束后最多启动一个新 Q EMU，固定 CPU0、实际 nice=4；不使用 CPU4–19，不改变旧作业。在新 Q 运行期间不同时向 CPU0 追加编译/参考队列。

新 Q 限额：max_cycles=4,000,000；EMU 墙钟 9,000 秒；每 stdout/stderr 16MiB；外层工具 9,600 秒，给原 helper 清理与输入核验留余量。RAM=128MB、seed=1、单线程及原 TRACE0 配置。无自动延期、重启或重试。旧 Q 实际约 1.55M guest cycles、21.03 分钟主机耗时只用于排程估计，不保证新任务完成时间。记录新 PID、affinity、nice、RSS 和新旧 CPU0 推进情况；超时保留失败证据。

主机调度只影响仿真完成耗时，计分比较使用同一新 ELF/EMU 内的模拟 cycle/instret；主机 elapsed 不作应用性能指标。保留全部 FR 锚及正反序，不从历史 ELF 补样本，不删不利窗口，不额外套用其他实验的波动阈值，也不因此要求当前四臂重跑。

## 验证、选择与回退

必须满足原有限 Q 合同的实际正常 exit、指定 reference、真实 DiffTest、GOOD TRAP、完整 43 行协议、全部输出与 CSR/guards、输入前后 SHA 不变、进程回收。固定 EMU/NEMU/flash 和 1400B ABI 继续由旧硬件证据及新 profile 绑定；不重新探测 ABI。源码与实际 GNU 先核实，再启动唯一新 EMU。

比较 N/W 的两次同次观察、均值与保守范围，并保留 P。若有清楚一致的优势，再决定是否值得新完整 forward；若优势小、反转、失败或资源成本失衡，停止扩大该候选并记录原因，不自动堆叠优化或加测。完整应用超过 10% 的目标仍需完整应用证据，本 Q 筛选本身不授予正式 performance、完整退休窗口或 ASIC PPA 资格。

回退只需不选择 N；旧 P、whole2、旧 plain-D 和所有证据均保留。无部署。
