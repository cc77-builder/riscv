# 当前0f＋firstdot V2组合与干净复现记录

当前节点：2026-10-27，@cc77-builder / Agent，本地执行。硬件仍为0f（O2＋H1＋DIV取消修复）；软件/工具源码c823a，生产RTL未改，未上传GitHub。

| 步骤 | 实际状态 | 结论与证据 |
| --- | --- | --- |
| zufan T17与firstdot V2选择性引入 | 完成 | 固定fcf4a11；45文件，43新增/2相同；没有整分支合并 |
| 原当前组合 | 功能/周期通过，宿主墙钟受限 | 38次实际启动，36合格、2中断保留；384正式/768全部窗口、96C调用 |
| 同机独立干净构建 | 完成 | clean-02独立源码/生成物，重新构建EMU/NEMU/AM/klib及25应用；保留已装工具与下载缓存 |
| 干净组合运行与原文审计 | 完成，明确全核宿主时间限制 | 53实际运行，50选用：全核14＋矩阵33＋新C3。旧C3严格时间失败排除，新C使用原检查器PASS |
| 新旧构建比较 | 完成 | 25应用BIN/PT_LOAD、768完整窗口、96C调用输出逐项一致；没有新增性能收益 |
| 配置复用筛选 | 功能/原文审计PASS；PERFORMANCE_CANDIDATE | 8×32/d0：reuse vdot 282.25→273.00 cycles（−3.2772%）；最快同场RVV 299.00。V3五进程/96窗、48对重放通过；旧V2两进程工具失败保留 |

[比较合同](CONTRACT.md)、[选择性来源](import-manifest.json)、[干净复现完成快照](continuation/clean02-final/README.md)、[版本档案第23条](../../../../docs/version-data-ledger.md)。
原始根：/home/riscv/riscv-lab/software-import-20261026。已完成干净证据见clean-02/full-reproduction-comparison-03.json、combination-audit-03、c-run-02。配置复用config-reuse-clean02-02已完成，目标运行退出0；首次只读审计因循环变量遮蔽失败并保留，新audit-02/完成回执退出0，原文审计和前后物理身份复核PASS；当前无本轮在途目标。

全核UTC时间曾推导出80.119ms重叠，仍记墙钟容量FAIL；固定源码容量上限3的证据PASS，不声称OS单调时钟并发已实测。旧C外层结束早于内部2.455386秒的失败保留，仅新增3个严格C补测。宿主耗时不用于DUT性能计算。前三整块形状firstdot优于S1；4×13继续RVV回退。公共stable默认入口未切换；新面积/STA、功耗和成员人工复现未测。

本轮新增的26个配置复用源文件已按上游固定提交逐字节引入，39个原有依赖不变，作为非默认候选保留。上游目录中的历史成绩不转借给0f；本机资格见[配置复用V3结果](continuation/config-reuse-v3/RESULT.md)与[工具/证据说明](continuation/config-reuse-v3/README.md)。版本档案追加第24条，先前23条不变。

下一步：将配置复用保留为候选；下一工程包先扩展多数据集/其他尺寸，并补普通公共C调用验证，再决定默认入口。 本轮限定筛选已收尾，不自动扩大测试。生产RTL及公共stable默认入口未切换，所有新增源码和记录仅在本地，未提交或推送本轮改动。

以下为历史接续记录，保留当时状态；判断当前进度以上表及真实state为准。

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

## 干净复现首次实际尝试

软件源码固定为本地提交 c823a8786e052c6e26f6915563c42b6d730dd8e3，仅84项新增软件/工具文件；
生产硬件仍为0f，提交后25869项物理输入复核通过。未推送。

clean-01 于2026-10-27 00:08:52 UTC+08开始：133仓库独立恢复PASS，
NEMU/AM/klib实际新构建PASS；00:10:01硬件构建退出1，未生成合格EMU。
原因已定位：MAIN为linked worktree，其common Git目录有真实shallow边界16ae9dd…；
本地clone未复制此边界，新仓被误认完整历史，Mill版本信息遍历缺失父e524…时失败。
原源码/RTL未变，失败clean-01和全部日志保留。下一次新clean-02在构建前恢复真实浅克隆元数据、
核验所有来源/目标的可达历史，独立留回执；不改冻结clean_prepare源码或旧失败数据。

2026-10-27 00:20（UTC+08），clean-02的133仓库恢复、精确shallow计划/恢复、新support和145仓库复核均exit0；开始EMU编译。只补新主仓缺失的Git边界记录，未覆写既有边界、未改原缓存/源码。新EMU/身份/运行资格仍待实际完成。

## 2026-10-27 clean-02 新构建及程序检查

新构建于03:30:46 UTC（11:30:46 UTC+08）完成，exit0：
429硬件源、21236依赖文件、126硬件依赖及2723个实际生成文件均校验。
期间观察到长墙钟跳跃，不能把全部起止时差作为连续CPU编译耗时；现场记录保留。
新EMU SHA-256：acf672eb39f836da4000b253849e3214089e9c8e5198060a57d2cc6bbd393da9。
identity/current.json SHA-256：3b9d9332720b6d21a52c979d84c3398bf9c3070812094da29431575a4e7a7451。

重新构建24矩阵程序和1普通C程序全部exit0。BIN和全部ELF PT_LOAD字节、入口、地址、flags、
文件/内存长度逐项等同当前原批；全ELF中的调试信息可因路径不同而变化。
见clean-02/program-byte-comparison-01.json；这是程序同一性通过，不是运行成绩转授。

全核14项以3CPU运行，普通C negative/recovery/replay以CPU1运行，输出相互独立。
hello/vadd已PASS；C高位故障已真实被捕获，正常恢复在途。
matrix-waiter-01.json只在全核外进程exit0和最终PASS后启动33项矩阵，避免重启已完成工作。
随后仍须全核/矩阵/C原文审计、归档与768窗口/96C输出完整对照；配置复用尚未开始。

新正常NEMU SHA-256：62b1707c52a4c323468481e0c1863b79f244d9a3fd54aeb7b7d2ecb5f01a35ca。

## 2026-10-27 配置复用首筛的离线复核（目标尚未执行）

等待clean全核期间，独立审查发现首筛v1在主候选落败时漏记其他格的未解释退化，
以及本地raw audit未逐项复验私有cwd/AUX实物。旧v1、反例和旧54项证据均保留。
新adapter-v2修复分类、按实际运行规则重建完整输入闭包，并核验共享与每进程实物；
52项针对性检查通过，候选指令、8×32/d0范围、5进程顺序和严格双基线阈值不变。

外部execute_clean02_stage.py另经29项准入/拒绝检查，要求实际clean证据与主任务复核回执绑定；
当前真实check因全核尚未完成而拒绝，未创建候选目录或运行目标。
原始位置：reviews/config-reuse/adapter-v2、clean02-launch-plan-v2.json、
execute_clean02_stage.py。配置复用目标资格仍NOT_TESTED，未修改生产RTL或推送。

准备阶段617份已结束文件已单独封存，原始28664439字节，压缩7034880字节；
manifest为bc7567257bbc38a4c33c516b1e3f21cb4e4c096bba97d2f34ac1030ceade6bf1，
见reviews/clean-preparation-archive-01。包含首次构建失败、修复、新构建与25程序字节比较，
不包含尚在写入的运行日志；运行结束后须补运行编排证据。

## 2026-10-27 13:31（UTC+08）全核运行完成，原文审计出现限制

全核14个实际进程均完成，最终CURRENT_CLEAN_FULLCORE_PASS、外层exit0；八功能分片原文
共117个不同案例、124次执行均PASS，最后控制诊断16组全部PASS。普通C3个实际进程已
R4_C_APPLICATION_CALLS_PASS、exit0，16函数/48不同案例/96正常调用。尚待联合原文审计。

33进程矩阵已由等待器合法启动，保持原目录运行。postprocess-01在首个fullcore_physical
失败：旧严格时间审计从墙钟推算唯一4路重叠，超过jobs=3。记录中o2-control-diagnostic
开始05:05:46.666837UTC，functional-7结束05:05:46.746956UTC，重叠0.080119秒。
失败与原始时间不改；正在独立核对固定ThreadPool/阻塞spawn的因果资源边界，不以宽容差消除失败。
另有C外层结束比子状态时间早2.455386秒，原值快照见reviews/clean-clock-observation-02。

原文/归档/跨窗口最终复现尚未合格；配置复用准入仍未释放。新证据会以新合同和独立输出保存，
不得把v1时间审计失败改写为PASS。生产RTL保持0f，未推送。

## 2026-10-27 13:51（UTC+08）全核原文与归档完成

新合同zjh-current-clean-fullcore-archive-v2-wall-clock-limited的physical、pack、bytes、
archive live四命令均exit0，结果均带WALL_CLOCK_LIMITED。原fc.audit完整重算：
14新目标进程、13正常/1预期拒错、117不同案例/124执行、六类O2覆盖全部通过；
同镜像负例与正常恢复绑定、全128位结果、输入/生成物/参考模型检查不放宽。

原v1墙钟峰4超过jobs3仍FAIL；仅对原14记录、71份证据与唯一80119微秒异常精确绑定，
从固定同步hello、ThreadPool(max_workers=3)、每worker阻塞spawn/wait证明source-bound容量3。
未记录OS单调并发，原因UNCONFIRMED，不把推断峰值改成实测3，也不修改时间/日志。
外部v2工具通过76项主机检查，原源码与01失败保留，未重复目标运行。

归档fullcore-archive-02共22141载荷，原始407009430字节、保存112906538字节；
manifest SHA-256：a80a1063aacd3baa524377710f280830f860d91071661636d6c493b407cebc91。
语义复核仍需要原物理输入，bytes核验与live原文复算分别记录，不是新机器脱离原输入的完整复现。
新postprocess-02正在等matrix-run-01，随后finalize C、combined-audit-02和full-reproduction-comparison-02。
配置复用尚未释放；须使用新executor-v2/plan-v3，不使用旧待审方案。

## 2026-10-27 中断后接续：审计工具与归档准备

根执行器只读核对配置复用 V2 的 8 项结果门禁、10 份实际命令完成回执、单次导入与物理身份前后相等约束，源审查通过；这不是尚未完成的运行放行。记录：reviews/config-reuse/executor-v2-root-review-01.json。新版留档草稿位于 reviews/clean-ledger-draft-02，保留全核宿主 UTC 容量失败及 C 外层回执时间异常，矩阵与最终比对保持待完成。

已将 30 份全核 V2 审计与编排工具逐字节保存到 [continuation/clean02-review-tools](continuation/clean02-review-tools/README.md)，不修改冻结 clean 源码或生产 RTL。新增编排补充归档器只允许指定运行全部结束后封存，不能代替原文审计。

截至此次只读抽查，干净矩阵 14 组正常进程的 336 个窗口与原构建逐项相同；这只是部分结果，不代替最终 768 窗口比较。原矩阵和后处理进程继续，尚未启动配置复用目标仿真。

### clean-02 正式测量阶段检查（2026-10-27T08:05:23.985181+00:00）

24 个正式运行完成，384 正式窗与 192 首轮/预热窗，共 576 窗与旧构建逐项相同。当前仍待 8 个独立重放、联合原文审计及最终 768 窗/96 次 C 输出比对，不宣称整体完成。

新运行重算的 firstdot/reuse/vdot 平均周期依次为：4×8 157.75、8×32 282.25、16×64 707.00、4×13 204.50；均与旧构建相同。此检查保存于 reviews/clean-formal-checkpoint-01/checkpoint.json，完整度和限定条件见文件状态。

## clean-02 矩阵完成与 C 严格回执补测

矩阵状态 CURRENT_FIRSTDOT_PAIRED_C_ABI_PASS，33 个实际进程全部完成，外层退出码 0。原 C run01 的功能状态通过，但 finalize-c-02 因外层结束时间比内部结束时间早 2.455386 秒而退出 1，postprocess-02 原样保留为 FAILED；未修改时间戳或 C 验收规则。

为得到符合原严格合同的新 C 回执，仅补跑 c-run-02 的 3 个进程。已完成的全核 14 个和矩阵 33 个进程继续复用；C 旧 3 个进程完整保留，不重复计入最终合格组合。补测实际进程总数待结束统计，不预先算作通过。

新后处理计划 clean-02-postbuild-plan-v3.json 和驱动 finish_clean_validation_v3.py 复用原四项全核审计，仅等待并执行 C 验收、联合审计和完整比较；三个新回执使用 -03，输出 combination-audit-03 与 full-reproduction-comparison-03.json。新后处理状态在 clean-02/postprocess-03/state.json。已校验四份语义验收源码与 c823a 源提交逐字节一致，并验证既有状态目录不可覆盖。

配置复用仍未启动。原 config-reuse 计划 v3、执行器 v2 和准备好的流水线当前不适用新 C 输出，需更新路径及完成证据绑定后再审查放行；不能用旧前置状态绕过这次失败。


## 配置复用范围扩展

4尺寸×3数据集扩展已完成，详见[本轮结果](continuation/config-reuse-expanded-v1/RESULT.md)。24新图、33新进程；逐尺寸判定：4x8=INCONCLUSIVE；8x32=PERFORMANCE_CANDIDATE；16x64=INCONCLUSIVE；4x13=INCONCLUSIVE。默认未切换，下一步补普通公共C调用路径验证。


## 8×32普通C调用补齐

配置复用的普通C路径已完成新3进程验证，详见[结果](continuation/config-reuse-c8-v2/RESULT.md)。16函数/48用例/96调用通过，其中8×32为4函数/12例/24调用；目标高位拒错与重放通过。上一轮1.095238×仍为独立性能矩阵数据，本次未新测周期；默认和RTL未改，未上传。


## 8×32稳定入口设计完成

[设计评审](package/C8_DESIGN.md)选择独立显式C8包、两个编译期别名和完整单对象静态库。当前尚未实现或验收新包；下一步做GNU等价、语义负控和搬移验证。符合完整等价条件可0新EMU；新运行控制流/最终映像须另按影响验证。本轮无新实测，不追加版本数据，旧第26条和默认保持，未上传。
