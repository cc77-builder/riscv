# Guarded paired16：目标功能与计数路径通过，性能 HOLD_CONTEXT_VARIATION

2026-11-06 UTC；工作包 `20261106-LiZufan001-paired16-rvv-pro6`，Issue #2 WORK [6672431323](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6672431323)。主机筛选合同为 `r2-s3-runq-paired16-rvv-screen-v1`，实际目标合同为 `r2-s3-runq-paired16-rvv-target-v1`。

**当前结论：唯一实际campaign `fa966` 已完成预期负控拒绝、正常恢复与确定性回放，目标功能、DiffTest及计数路径通过；性能选择为 `HOLD_CONTEXT_VARIATION`。P对G/TA/FR的原始周期分离均通过0.5%门槛，但四个FR锚点未通过1%上下文门槛，因此 `candidate_qualified=false`。保留既有冻结的更快合格RVV，不改变稳定默认入口；完整应用没有获得性能资格。**

以下保留主机筛选和目标构建预检的先前证据，并明确它们各自当时的边界。先前“尚无目标运行或周期资格”的结论仅适用于那些历史阶段；当前目标结论以文末实际campaign结果为准。本工作包新增源码仅在本叶；生产RTL、NEMU、官方程序、旧生成器/验证器和其他工作包没有修改。

## 为什么尝试，以及为什么保留回退

每个 GS32 中，将前后16项的乘积先按相同 lane 两两相加，再做一次 s16→s32 宽归约，可把每行归约输入从32项变成16项。实现用标准 RVV `vwmul.vv`、`vwmacc.vv` 和 `vwredsum.vs`，保持原 packed W、尺度、八行 tile 和逐组 FP32 消费顺序；没有新 ISA、硬件或数据转置。

这个变换对任意 s8 输入不能无条件使用：两项乘积和范围是 [−32512,32768]；唯一正溢出来自两项都为 (−128)×(−128)。因此函数入口完整扫描288字节 X；只要出现 −128，就执行保留的 FR 完整函数主体。X 不含 −128 时，任意 s8 W 的成对和属于 [−32512,32512]，快路可精确执行。原输入只读/非别名要求确保一次检测覆盖后续所有行。检测、分支和重复初始化均在完整函数内，不能从计时区排除。

完整 signed-int8 域的判断依赖上述范围推导和安全回退；下面的19组筛选是实际机器码证据，不是全输入穷举。FP证据沿用有限 binary32 输入/结果、RNE 边界，没有 `fflags` 模型；不外推到 NaN、Inf、非RNE或中断恢复。

## 历史阶段一：实际主机筛选与身份

实际 GNU 构建及筛选在常驻 WSL 原生目录执行，CPU affinity 为 `[2]`，没有新 EMU、EDA 或 Git 操作。主机控制回执为 `succeeded / exit_code=0 / cleanup_complete=true`，未取消、未超时。Windows 控制器记录启动 `2026-11-06T00:01:29.8971797Z`，持续13,913毫秒；WSL 驱动自身记录 `00:01:32.683651–00:01:44.884169Z`。两套时钟原样保留，不混算持续时间。

操作 ID：`bee1ca65369429068a98a24c112ef728.ae68de0c66f5a77e477d0ae3d219c37a`。

GNU GCC 为 Ubuntu 11.4.0，编译器 SHA-256 `0c54895c55568be5b5fee49e2426abcc8fb05ca2c121ca5685dea2cbc24a1c13`。实际使用 RV64GCV、LP64D、禁链接 relaxation，静态无运行库 ELF。生成、汇编、链接、反汇编、screen 五阶段退出码均为0。13个输入在运行前冻结，并在运行后核对未变；完整命令和所有日志保存在 `run.json` 与同目录阶段日志中。

| 证据 | SHA-256 |
| --- | --- |
| CONTRACT.md | `523bb74834eaa2a2c8a59530c24f011aa8ed743157b6f0fa585c234f73851553` |
| generate.py | `ac3b61a164e948f2f3518407fb9fd3d07582649038786afb707fa660ae00823b` |
| screen.py | `fe2168eab295f3a232e1905192dbaeeeba37d5c96f94487ccb5180637b2c1d29` |
| 生成 paired16.S | `7b1bf0ba021a69aeab466c8e6bce6a1a88072d40d3f18adfe47555df5dcd3c56` |
| paired16.elf | `fb3c030efa7aa347029a69f6aabe82c912cbbb85294b27cf407a01ea58a314f3` |
| screen/result.json | `6a9e418223ad9b44235f5b4216419288e0d9f6302dfdfed0295e1d26130b5fa0` |
| run.json | `c3309e8db47cc734a71a231d5b0e7437c765db489f3a0c847d588be8d406a14f` |

原始输出目录：`/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/paired16-rvv-20261106-0740/host-01`。其中保留13个冻结输入、执行驱动、GNU对象/ELF/反汇编、C oracle、全部正向结果和六个损坏后的实际 ELF；没有覆写原筛选证据。

本叶的 [host-01-evidence.zip](host-01-evidence.zip) 已封存46个原始文件及一份清单，81,041字节，SHA-256为 `86419540600d09a489de6b94f150e2a1ae112576f1007fe8cad58efa560cf453`。归档逐文件回读比对成功，清单包含每文件长度/SHA及原ChatPC运行回执。曾有一次归档请求被另一工作包的项目锁拒绝，回执明确未开始；确认占用结束、旧请求过期且目标不存在后，另行封存成功，未重放实际构建或筛选。

### 从冻结输入复现

解压证据包后，在Linux原生目录执行下列命令。输出使用新临时目录；使用当前协调分配的单核，示例CPU2对应本次实际运行。此过程不修改原输入或既有输出。完整原始命令仍以包内 `run.json` 为准。

```bash
paired_snapshot="$PWD/host-01/inputs/source"
paired_source="$paired_snapshot/team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/paired16-rvv"
paired_out=$(mktemp -d /tmp/paired16-reproduce.XXXXXX)
paired_cpu=2
taskset -c "$paired_cpu" python3 -B "$paired_source/generate.py" \
  --repo "$paired_snapshot" --output "$paired_out/generated"
taskset -c "$paired_cpu" riscv64-linux-gnu-gcc -march=rv64gcv -mabi=lp64d -mno-relax \
  -c "$paired_out/generated/paired16.S" -o "$paired_out/paired16.o"
taskset -c "$paired_cpu" riscv64-linux-gnu-gcc -march=rv64gcv -mabi=lp64d -mno-relax \
  -static -no-pie -nostdlib -nostartfiles \
  -Wl,--build-id=none,--no-relax,-Ttext=0x80000000,-e,q288_paired16_rvv \
  "$paired_out/paired16.o" -o "$paired_out/paired16.elf"
taskset -c "$paired_cpu" python3 -B "$paired_source/screen.py" \
  --repo "$paired_snapshot" --elf "$paired_out/paired16.elf" --output "$paired_out/screen"
```

## 历史阶段一：数值、路径和边界检查

19组全部通过；候选与独立 row-major C/Python golden 的288个 FP32 输出逐位一致，八个最终完整128位 slots 也一致。8组走快路，11组走回退。

| 用例组 | 数量 | 实际路径 |
| --- | ---: | --- |
| 原 x0→x1→x0→x2，后续调用继承脏向量状态 | 4 | 快路 |
| W/X=max/max、min/max、min/−127、零权重 | 4 | 快路 |
| W/X=min/min、max/min | 2 | 回退 |
| 单个 X=−128 在0、15、16、31、32、255、256、287位置 | 8 | 回退 |
| 最后组危险 pair：X[271]=X[287]=−128、W全−128 | 1 | 回退 |

所有用例均核对324个完整整数核心、九次完整guard扫描、一次分派、未选路径不执行、输入只读、精确逐字节读写足迹、整数/FP ABI、CSR、零栈使用和普通返回。后15组包含量化输入字节非对齐情况。候选每个 X 字节读37次，包含新增的一次扫描；没有沿用旧36次读取计数。所有合格执行的 `wrapped_lanes=0`。

FP逐元素操作次数保持转换2592、乘法5184、加法2592；共享原 FP 模型通过4337个加法、3798个乘法、4108个整数转换原语检查，有限结果域外的3个加法与542个乘法结果明确排除。不存在改变运算顺序或 FMA 的隐含许可。

实际机器码证书确认候选内部的592字节回退主体与同 ELF 保留的 `q288_fused_rvv4` 全函数字节相同，SHA为 `66a12c0ec3cb7c0d1cdceadf04e4c658607438d83a2a958892100422343117ab`。快路核心180字节，即45条固定宽指令。核心之后的原 FP 消费及出口只允许相对分支位移变化，其他机器字保持一致。

## 历史阶段一：六个实际 ELF 负向变体

所有负控都执行至普通返回，再被预期数值或完整槽检查拒绝。不是靠不支持某条指令、路径白名单或禁止模型溢出来获得拒绝。

| 损坏 | 拒绝依据 | 已观察到的关键现象 |
| --- | --- | --- |
| 关闭 guard，输入全 min | 完整Q逐位输出 | 41,472个 s16 lane 回绕；row0从应有 `0x4538ab2e` 变为 `0xc538ab2e` |
| guard 只扫前8组 | 完整Q逐位输出 | 最后危险pair引发288个 lane 回绕 |
| 删除共享零种子清零 | 完整Q逐位输出 | 原应为0的row0变为 `0xba800000` |
| 第二半乘数误用第一半 X | 完整Q逐位输出 | row8首次出现错误 |
| 删除入口结果高96位清零 | 八个完整最终槽 | 全部Y仍正确，slots错误被单独识别 |
| 交换 Ws/Xs 乘法次序 | 完整Q逐位输出 | row1发生1 ulp差异，明确拒绝FP重排 |

各负控的 ELF SHA、完整输出 SHA、首次差异和动态指令数均在原始 `controls[]` 中。

## 历史阶段一：指令计数与当时的目标验证计划

| 完整函数实际 ELF 模型路径 | 动态架构指令 |
| --- | ---: |
| 保留 FR | 35,670 |
| paired16 快路，包含guard | 22,138 |
| paired16 回退，包含guard | 35,742 |

快路相比 FR 少13,532条指令；回退多72条，恰为完整检测及分派代价。这些不是周期。更强的 GS32v2 已有更少的架构指令，因此不能用这张表判断候选排名。

固定 T17 源码的静态核心账本显示：GS32v2每八行/每组为39条架构指令、142个声明微操作；paired16为45条、106个声明微操作。后者多出MAC的旧目的依赖，却减少宽归约工作量。该账本包含 rd=x0 的向量配置 nop 微操作，不模拟RF仲裁、加载拆流、实际发射或停顿；因此不能把25.35%的声明微操作减少转成周期收益。

该阶段确定的目标验证计划，是在同一新 ELF 内固定 paired16、GS32v2、既有TA与FR，比较包含guard的完整Q函数，保留反向执行次序、全部锚点与较快合格对照。目标行为、DiffTest、真实输出、计时路径及失败控制通过后，才按预先固定的保守周期规则判断；对照或锚点不稳定则保持HOLD，不挑较慢样本。本计划后续已经实际执行，结果见下文；本稿不再将它列为待执行实验。

上述主机筛选阶段明确为 `new_emu_runs=0`、`target_runtime_qualified=false`、`performance_qualified=false`。本阶段无RTL改动，无新的时钟、复位、FU时延、吞吐率或ASIC PPA承诺。

## 历史阶段二：四臂目标 ELF 构建预检（当时尚未执行 EMU）

新目标合同见 `TARGET_CONTRACT.md`，身份为 `r2-s3-runq-paired16-rvv-target-v1`。同一 ELF 的 arm 0/1/2/3 固定为 P/GS32v2/TA/FR，计时顺序固定为 `(3,0,1,2,3, 3,2,1,0,3)`。原三组数据、FP尺度、完整函数、guest判定和五项故障控制保留；全 −128 的 W/X 使用额外独立缓冲区，调用 P 一次，仅作为功能证据。八次标准功能调用、一次 fullmin、十次 selfwarm 和十次计时合计29次完整Q、8352个输出判定；TA仍调用六次，连同probe预期62209条custom提交。

实际构建/预检操作 `bee1ca65369429068a98a24c112ef728.857573547d6ba5fa147255bb402fa12e` 成功，控制回执 `exit_code=0 / cleanup_complete=true`，未取消/未超时。Windows记录启动 `2026-11-06T00:45:35.5816533Z`、持续7016毫秒；WSL驱动记录 `00:45:36.048849–00:45:42.444513Z`，其中串行GNU构建0.623秒、ELF检查5.741秒。只使用CPU2的一个worker，无新EMU或硬件构建。

常驻WSL快进前的37个实际读取输入已在 `5c7cd127b12a46d4927ddb6f0ef359fde0ba4c91` 冻结，随后仅附加本叶7个控制文件及5个真实参考文件；没有新Git检出。原counter checker仍是 `084bebc22e2f4665e5c7a7797e5cd2a6c73220719b4cf228ce3075ae2446bc66`，没有借用快进后的版本。源码、固定AM输入和参考字节在构建前后核对，源码再生成一致，完整ELF/BIN相符。

| 目标证据 | SHA-256 |
| --- | --- |
| paired16-target.elf | `889aedd64a1a80ed5e3bfdfe5530ca2f8b4105d40b3ffb0559e6a64201746b1e` |
| paired16-target.bin | `7a7dea70e60fa2c8a138a081f3e272c35ac977c9fc32149e6ffeba8a1ea3f960` |
| target-check-01.json | `b91401cbb4ac7275010ef767dd2d75414d39c487d0146f81df0374202888343f` |
| manifest.json | `08bfb2fff685aaf0f13b139bbe26a3157620b6ae340d8ba1e788852810020198` |
| producer-inputs.json | `0570985758d5701984b4bed5c72f89423a5ef75814ba373ba913d5fae29344fe` |

P完整函数（包含内嵌回退）SHA `a06e377e88a230929cc971acf91b0adf3ac27e52fd17ec72956ae7890ed7e73c` 与上述host ELF逐字节相同；GS32v2完整函数SHA `2d95481faa1c79f7a8a06ef65fc02154e30cf731e6ba5c990a7209c2e90c32ab` 与其筛选ELF `8316e32939385653c1c4f7e257443529c19dc71df8b5991552a2ab1453069daa` 一致。TA、FR完整函数保留各自既定SHA。完整 `split_measure` 与先前 `610c499f46f1fe73074f626d8990bdcbdbc5f78c30ce8fc4a835495b0e392faa` 参考ELF一致，函数SHA `11de9048976be8af31e6bd6ac48a63e8aad22e1194e63cac809659a4e956860b`。

13条链接后实际ELF的主机模型路径通过：四臂各三组原数据，另加P的fullmin。完整Y/slots、ABI及精确足迹均保持。fullmin模型执行35742条指令、走fallback且 `wrapped_lanes=0`，独立C/Python golden与既有host输出/槽SHA相同。它的返回环境是显式合成的ABI上下文，不声称已经观察到untimed guest退休路径。六个编译数组的内存ELF字节变体均被对应数组检查拒绝：wrapper、计时次序、原golden、原packed W、新X和新golden。

| 原dataset0的计时区 | 预检时的预期CSR指令数，当时尚非实测 |
| --- | ---: |
| P，包含完整guard | 22149 |
| GS32v2 | 20134 |
| TA | 49613 |
| FR | 35681 |

预先固定的选择规则未放宽：四个FR锚点满足 `100×max ≤ 101×min`；P的较慢观测须对GS32、TA、FR各自的最快观测都满足 `200×max(P) ≤ 199×min(reference)`。replay只是确定性复核，不增加统计样本。运行器只并行EMU进程，所有动态模块导入和分析均在主线程串行执行；producer/controller重复路径必须保持原pin，Popen后的可捕获异常也会回收本次进程。

原始证据位于上述runs根下 `target-inputs-01/`、`target-build-01/`、`target-01-logs/`、`target-01-run.json` 和 `target-check-01.json`。`target-01-evidence.zip` 已封存120个原文件及清单，730654字节，SHA `ade9abcd36b904cd84847b6246b4057edc5d88cfebbb612c534952b0206e7aff`，逐文件回读与原始证据相同。包内保留37文件薄快照、7控制文件、5参考、生成源、GNU对象/ELF/BIN、日志、完整命令及原ChatPC回执。该预检阶段当时明确 `target_runtime_qualified=false / performance_qualified=false`；这是构建与主机预检的历史边界。随后冻结的negative、recovery、replay三次EMU实际执行结果记录在下节，不能把上述历史false误读为当前目标功能失败。

## 实际目标campaign：功能与计数通过，性能保持HOLD

### 唯一campaign与三次EMU

唯一实际campaign操作为 `bee1ca65369429068a98a24c112ef728.fa966c66acdf751c5598749ef2acf072`。控制器记录开始 `2026-11-06T01:19:22.1280334Z`、结束 `2026-11-06T01:49:21.5271835Z`，回执耗时 `1799.361 s`，`exit_code=0 / cleanup_complete=true`。起止时间与回执耗时分别原样保留，不混算或相互替代。该墙钟只表示执行成本，不是目标周期。

原始运行目录为 `/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/paired16-rvv-20261106-0740/campaign-01`。本轮使用上述已冻结的同一目标ELF/BIN、既有T17 EMU、flash、seed1、128MB RAM及12M目标周期上限，没有新硬件构建。负控完成并验收后，两个正常进程在独立CWD/输出目录、获配CPU2/3上各用单线程并行执行；进程结束后的分析按合同串行完成。

| 实际运行 | CPU | 进程开始（UTC） | 进程结束（UTC） | 退出码 | 实际判定 |
| --- | ---: | --- | --- | ---: | --- |
| negative | 2 | 01:19:22.843339 | 01:19:33.139667 | 1 | `PAIRED16_EXPECTED_BIT100_REJECTION` |
| recovery | 2 | 01:19:33.231263 | 01:47:33.965772 | 0 | `PAIRED16_TARGET_DIFFTEST_COUNTER_PATH_PASS` |
| replay | 3 | 01:19:33.230346 | 01:47:32.712417 | 0 | `PAIRED16_TARGET_DIFFTEST_COUNTER_PATH_PASS` |

三个进程均实际启动且未超时。负控在 `0x80001c04` 对bit100故障得到预期拒绝，`reference_unchanged=true`；其退出码1是预期结果，不能把三次执行概括为“三次exit0”。两次正常运行均使用既有正常reference。

恢复与回放各自记录 `windows=10`、`full_q_calls=29`、`judge_fault_controls=5`、`outputs_checked=8352`、`committed_vdot=62209`。调用计划为8次标准功能、1次P fullmin、10次同方法selfwarm与10次计时；P/G/TA/FR调用数分别为7/6/6/10。完整custom PC序列SHA-256为 `0a24e77d1a0c7c8d2c1fabf04a306b1b783572deead689ffa5d526a0669fc843`，恢复与回放一致。

`fullmin_functional_pass=true` 说明计时外全−128 W/X的完整P调用通过目标功能检查；它不增加计时窗口，也不形成fallback周期或计时外退休trace结论：`fullmin_performance_sample=false`、`fullmin_retirement_trace_claim=false`。两次正常运行均为 `runtime_qualified=true`，同时 `full_application_performance_qualified=false`。

### 十个完整Q计时窗口

下表为recovery的完整十窗；replay的全部samples逐项相同。原顺序 `FR,P,G,TA,FR / FR,TA,G,P,FR` 保留，四个FR锚点全部纳入。各窗均为标准dataset0的一次完整Q调用，包含共同timer开销，P额外包含完整入口guard与分派；每窗前按原合同执行一次同方法selfwarm。

| 窗口 | 方法 | cycles | instret |
| ---: | --- | ---: | ---: |
| 0 | FR | 67,770 | 35,681 |
| 1 | P | 43,971 | 22,149 |
| 2 | G（GS32v2） | 54,054 | 20,134 |
| 3 | TA | 55,459 | 49,613 |
| 4 | FR | 62,772 | 35,681 |
| 5 | FR | 62,786 | 35,681 |
| 6 | TA | 55,414 | 49,613 |
| 7 | G（GS32v2） | 53,920 | 20,134 |
| 8 | P | 43,076 | 22,149 |
| 9 | FR | 62,751 | 35,681 |

独立只读复核使用Python整数。每窗四个 `counter_values` 均超过2^53、仍在uint64范围内，窗口内没有回绕；十窗全部满足 `counter_values[2]-counter_values[1] = cycles = sample_ticks[2]-sample_ticks[1]` 和 `counter_values[3]-counter_values[0] = instructions`。计数器采样两端的对应间隔均为34 ticks。没有通过JavaScript浮点解析这些大整数后计算差值。

### 冻结门槛与选择结果

四个FR锚点为67,770 / 62,772 / 62,786 / 62,751。最大与最小相差5,019 cycles，相对最小值的变化为 `5019/62751 = 7.9982789119%`。冻结门槛要求 `100×max(FR) ≤ 101×min(FR)`；实际 `6,777,000 > 6,337,851`，因此 `anchor_gate=false`。

P最慢窗口为43,971 cycles。分离门槛要求对每个B∈{G,TA,FR}都满足 `200×max(P) ≤ 199×min(B)`，三项整数比较全部通过：

| 对照B | 最快对照cycles | 对照最快比P最慢多出的cycles | 原始周期降幅 | 0.5%分离整数比较 |
| --- | ---: | ---: | ---: | --- |
| G（GS32v2） | 53,920 | 9,949 | 18.451409% | 8,794,200 ≤ 10,730,080，通过 |
| TA | 55,414 | 11,443 | 20.650016% | 8,794,200 ≤ 11,027,386，通过 |
| FR | 62,751 | 18,780 | 29.927810% | 8,794,200 ≤ 12,487,449，通过 |

这些百分比描述本次原始记录，不是已合格的性能收益。上下文门槛失败使三项 `qualified` 均为false，最终 `decision=HOLD_CONTEXT_VARIATION`、`candidate_qualified=false`；`stable_default_changed=false`、`hardware_changed=false`。不能删除首个FR锚点，不能改变已冻结次序、对照或阈值，也不能用剩余三锚点重新赋予本轮资格。

恢复与回放的完整samples、选择结果和custom PC序列一致，只提供确定性复核，不增加独立统计样本，也不修复上下文门槛失败。FR的7.998%变化不是P/G比较偏差的上界，不能用18.451%减去7.998%构造“保底收益”。本轮没有证据把变化归因于cache、内存瓶颈或宿主机争用。

### 原始结果与归档身份

原始results文件为 **88,457,550字节**，SHA-256 **`2a2feb6cb093a4377116f62c19e6b97ba1ec50cddc4d0cc7eb6e8dc2cf82f89a`**，已在归档时重新计算。上述数值复核使用从实际原结果提取的精确JSON投影；本叶 [campaign-summary.json](campaign-summary.json) 保存同一来源的 `records[].receipt`、`records[].result.samples` 与 `records[].result.selection`，支持上述表格和结论。选择公式对应 [check_target.py](check_target.py) 的 `selection`，范围和调用计划对应 [TARGET_CONTRACT.md](TARGET_CONTRACT.md)。数值复核与归档未重新启动EMU，也没有把一次重算门槛说成新增目标样本或完整协议重验。

本次campaign归档已实际完成；以下归档身份依据实际归档回执，与前文host及预检归档分别记录。

| 归档证据 | 字节数 | SHA-256 |
| --- | ---: | --- |
| [campaign-01-evidence.zip](campaign-01-evidence.zip) | 35,373,888 | `ac62d6977ba6504334d2c948e3192335fe1fb41ec523a4960548f8fe8ef361fd` |
| [campaign-summary.json](campaign-summary.json) | 29,714 | `343887c902cbe48f8c6ccc87e98dacd145ef774d97bb1c20716078dcda68e9e7` |

归档操作为 `d9b025210fdcd3c1fd06c2f645cfad75.ae15efe351b982c197b82948fb1fb53a`，2026-11-06 UTC `02:06:20.786–02:06:26.489`，回执耗时5653毫秒，`exit_code=0 / cleanup_complete=true`，CPU2。22个原始文件共508,402,285字节，全部ZIP成员SHA及原始源文件再次hash核对通过；另含manifest、campaign-summary和操作回执。小summary保留原始uint64整数，读取计数器仍须使用精确整数解析。

此前一次归档尝试 `71e3…` 在任何输出写入前，因脚本将真实字段 `instructions` 误写为 `instret` 而失败。随后经 `file_info` 确认两个目标文件均不存在，修正脚本后完成上述归档；失败回执也保留在ZIP内。此过程未重跑EMU，不增加目标运行或性能样本。

### 当前决策、保留依赖与结论范围

目标功能及计数路径资格保留；候选性能优先资格未成立。保留既有冻结的更快合格RVV及稳定默认入口，不用旧FR替换更强对照，也不把本轮G的观测自动转换为新的历史资格。原始P对G的18.451409%周期分离可以记录为后续判断的信号，不能发布为已通过冻结合同的收益。

`/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/paired16-rvv-20261106-0740/target-inputs-01/source` 已被Pro3 postprocessing引用，仍是有效依赖，**必须保留，不能退役**；本次campaign及归档完成不解除该依赖。

全部计时仅覆盖synthetic、prepacked Q288、dataset0、同方法selfwarm及P快路；不包含quantize、packing、K768、完整token或模型运行，fullmin仅提供计时外功能证据。完整应用没有获得性能资格。本次未获得合格的完整Q性能选择，不据此扩展P到完整forward，不安排新EMU或放宽验收。
