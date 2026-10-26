# 当前0f＋firstdot V2组合与干净复现记录

2026-10-26，执行者 @cc77-builder / Agent。本轮仅本地工作。
硬件保持0f12df675378556670afd0dd2153f47fcb330610；新模拟器干净重建尚未开始。
[合同](CONTRACT.md)、[选择性来源清单](import-manifest.json)。

| 步骤 | 当前状态 | 证据/限制 |
| --- | --- | --- |
| 选择性引入 | PASS | zufan fcf4a11；45源文件，43新增、2原有相同；不整体merge |
| 生成器/公开C源码 | PASS | 原firstdot CLI、48次生成，16函数/48case；真实GNU构建4项产物破坏拒绝 |
| 当前身份 | PASS | 429源、126依赖仓库、21236依赖文件、1672生成物/NEMU真实来源；18项身份负控 |
| 新组合门禁 | PASS | 22项测试，包含错误合同、缺失/伪造重放、镜像身份、源漂移；前两次测试失败记录保留 |
| 24软件镜像 | PASS | combination-build-02；源码/全128位数学模型/实际ELF/固定布局/RVV完整代码槽检查 |
| 干净复现适配器 | 工具测试PASS，实际重建未开始 | 32项 clean/35项归档检查；已修正新NEMU身份下负例检查器的私有绑定，旧模块保持原样 |
| 跨构建对照工具 | 工具测试PASS，实际对照未开始 | 55项检查；24矩阵+C镜像加载字节、768全部窗口及96次C输出 |
| 当前33逻辑目标进程 | 功能/周期原文审计PASS，墙钟顺序受限 | combination-resume-01退出0；384正式窗口、192重放窗口；34实际启动含1次中断 |
| 普通C目标3逻辑进程/V2包 | 目标调用PASS / 包静态检查PASS | 16函数、48不同案例、96正常调用；续跑退出0，联合原文复算PASS |
| 新身份干净重建/运行 | NOT_TESTED | 必须当前组合通过后启动 |
| 配置复用筛选 | NOT_TESTED | 必须上述干净复现通过后启动 |

原始根：/home/riscv/riscv-lab/software-import-20261026。
当前运行命令/退出码保存在combination-run-01.command.json，实时阶段见combination-run-01/state.json。
外层Windows/WSL前台会话保持任务存活；矩阵内部串行。15:18起独立普通C正确性以另一单线程并行；两个EMU独立cwd/输出、合计不超过4CPU。C完成后仍待矩阵资格联合验收，宿主耗时不进入性能统计。同机未发现队友进程。

初次通用unittest发现firstdot 0项、T17 17项全跳过，不计作测试PASS；已按实际CLI补firstdot检查，
T17真实fixture测试待新构建。combination-build-01因适配器门禁继续修订而保留为早期编译结果，
正式目标使用修订后独立的build-02。不把编译或旧upstream PASS当作本轮全核运行通过。
本轮不修改RTL、不推送GitHub、不代签人工验收。

## 2026-10-26 21:52（UTC+08）中断恢复核查

确认两组旧进程均已不存在，退出码和停止时刻未知，不伪造FAIL退出码或完成状态。旧state/raw全部保留。
中断证据见原始根interruption-01/receipt.json，当前硬件25869项物理输入重新验证通过。
续跑采用新合同与目录，矩阵将累计34次实际启动（33项完成资格＋1次中断），C累计4次（3项完成资格＋1次中断）。
新工具只执行未完成项，不修改冻结的4个组合运行文件，不复用未完成的窗口作为正式结果。

22:02（UTC+08）已从固定续跑工具启动combination-resume-01与c-run-02；两路各1个EMU，原目录不变。
矩阵续跑前12项完成记录已原文复算，13项控制器检查通过；C旧负例复核与5项控制器检查通过。
续跑原文审计工具20项测试通过，完整38次实际启动的联合验收等待目标运行完成。
Windows独立隐藏启动器保存job/receipt，并持有WSL进程；20秒跨工具存活检查通过，退出0。

22:59（UTC+08）普通C续跑完成：recovery/replay均DiffTest与O2协议PASS，实际输出一致，续跑控制器退出0；continuation-proof.json完成前后输入封存。累计4次启动含1中断，3项逻辑运行有效。未签发完整组合资格。

## 当前组合运行完成与审计接续

矩阵续跑状态为CURRENT_FIRSTDOT_RESUMED_PAIRED_C_ABI_PASS，普通C为CURRENT_FIRSTDOT_C_CONTINUATION_PASS；控制器均退出0。合计38次实际启动、36项完整逻辑运行、2次中断，旧部分输出保留。

首次联合审计combination-audit-resumed-01在读取矩阵qualify依赖时失败：脚本引用了不存在的r2-vector-accum/merged_screen.py，真实冻结文件位于r2-safe-tail/merged_screen.py。该审计未新增EMU，也未修改旧日志；正在以单独审计适配修正，不把此次工具失败写成目标测试失败或审计PASS。

干净复现与配置复用仍为NOT_TESTED。后续依次完成联合原文审计、固定软件源提交、独立依赖/EMU/NEMU/AM重建、真实运行对照、配置复用有界筛选；生产RTL保持0f，本轮未推送。

## 2026-10-27 00:05（UTC+08）当前组合验收

正式审计位于原始根 reviews/resume-audit-fix-01/full-raw-audit-02/，控制器退出0。
合同为 zjhwork-0f-firstdot-continuation-raw-audit-v2-wall-clock-limited：
functional_validation=PASS、target_cycle_validation=PASS、causal_serial_order=PASS；
wall_clock_chronology=FAIL。原两记录出现唯一0.543481秒倒置，原因未确认，无单调时间记录；
按固定阻塞控制器、实际回执和完成日志验证串行因果顺序，没有修改时间戳、重排记录或应用通用容差。
早期路径错误及原严格墙钟审计失败完整保留；审计本身新增EMU为0。

38次实际启动、36完整逻辑运行、2中断；384正式窗口、192重放窗口，连同first/warmup共768正常窗口。
普通C的16函数、48不同case、96次正常调用输出全部原文复核。1756载荷封存，
原始966485449字节、保存176446013字节；manifest SHA-256：
b4f255c6cb81c02536f1797ee8938ab784888b4a65f90cf6b5fb5024f274d06c。

| 形状 | S1 reuse vdot cycles | firstdot reuse vdot cycles | 最快纳入RVV cycles | 相对S1周期减少 | RVV/firstdot | 当前选择 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 4×8 | 169.75 | 157.75 | 187.50 | 7.0692% | 1.1886× | firstdot reuse vdot |
| 8×32 | 292.50 | 282.25 | 300.75 | 3.5043% | 1.0655× | firstdot reuse vdot |
| 16×64 | 717.25 | 707.00 | 778.75 | 1.4291% | 1.1015× | firstdot reuse vdot |
| 4×13 | 219.75 | 204.50 | 187.00 | 6.9397% | 0.9144× | reuse RVV |

每项12正式窗口，含C ABI调用/返回，不扣计时成本。K13的S1/firstdot reuse RVV均为187周期；
选择V2所带RVV回退，不能把firstdot对旧vdot的改善描述为胜过RVV。
以上仅为当前硬件与软件组合资格。干净重建/运行及配置复用仍NOT_TESTED，后续按合同继续。
