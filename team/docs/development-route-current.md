# 香山 vdot 工程开发路线：满足赛题技术要求，持续提高性能

更新：2026-10-27（UTC+08:00）。硬件比较基点：6d2abe403b07c297b8830a7d4f06e370b0a8e070；当前T17新构建源码：34bae6d4acceac939f958199dae53c14bc1f6183；当前推荐采用的稳定 C 源包为[firstdot V2](../optimizations/o2/r2-select/FIRSTDOT_STABLE.md)，冻结[V1与回退](../optimizations/o2/r2-select/STABLE.md)保留；底层资格分别见[firstdot运行结果](../optimizations/o2/r2-vector-accum/FIRSTDOT_RESULT.md)及[R4结果](../optimizations/o2/r2-select/ENTRY_RESULT.md)，后续config-reuse选择性优化见[当前S3结果](../optimizations/o2/r2-config-reuse/RUNTIME_RESULT.md)。团队集成分支 cc77-builder/riscv:zufan。实时活动见[协作入口](collaboration-current.md)，每轮成果及路线变化见[开发计分板](../../开发计分板.md)。

本路线只安排工程实现、验证、复现和性能优化。比赛报告、PPT、视频、答辩、平台提交及赛事事务由成员另行安排，不属于 Agent 的工程任务，也不作为工程推进的前置条件。开发只维护必要的运行说明、结果证据和简短计分板记录。

赛题技术目标、完整评分表及官方／内部合同边界统一见根目录[赛题要求与评分总览](../../赛题要求与评分总览.md)。每轮先读计分板的近期“路线影响／接续”，结合 Issue 和真实运行恢复工作，再使用本路线选包；上轮聊天不是接续依据。

## 1. 当前从哪里出发

沿 O2 两槽弹性 FU＋H1 低 32 位结果保存继续开发，O1、原 O2 B0 保留为固定对照与回退。已有实现先复用，缺什么补什么，不从头重做全部阶段。

| 对象 | 已知事实 | 当前边界 |
| --- | --- | --- |
| 合并 6d2abe403 | [MERGE-REG 新夹具回归](../optimizations/o2/fullcore/MERGED_REGRESSION_RESULT.md)完成12 core＋2 supplement，13完整正常轨迹、1预期拒错及六项O2覆盖；原实物与封存原文复算均PASS | 绑定6d2/1a23和新6e8b夹具；旧9b3、B0/H1合同缺项保留，不转移到新构建 |
| O2 吞吐 | 历史 batch128 相对 O1 周期少 39.03%，相对当轮 RVV 为 3.068×；无停顿 II=1、首响应 2 拍 | 不能推广为应用或 LLM 端到端收益 |
| GEMV | 历史 O2 相对 O1 端到端少 0.62%～1.50%；4×13 对较快 RVV 为 0.907× | 当前先解决尾部、搬运和配置开销，比较完整应用周期 |
| H1 | 历史 96 对正式窗口周期相同；FU 面积少 2.33386%、父级少 0.137349%，部分 STA 路径回退 | 32 位保存已完成，不重做；没有整核频率／功耗改善结论 |
| S2 | [固定完整布局重测](../optimizations/o2/r2-safe-tail/FIXED_RESULT.md)完成31次整核进程/384正式窗口；K13 reuse/endtoend 210→187周期（−10.952%），basic退化21.117%，16×64整BIN及窗口不变。另5次强RVV探针/32窗口正确性和重放PASS | 同镜像dataset0/endtoend下S2 reuse187对较快RVV175.25，慢6.705%；按停止条件不扩大S2采用矩阵，不冒称强RVV完整12样本资格。保留S1 RVV与S0 vdot回退，旧B0/H1仍BLOCKED |
| S1 | [独立实现及固定布局主批](../optimizations/o2/r2-vector-accum/VALIDATION.md)完成57次整核进程、768正式窗口，另4次小尺寸进程重放及两项原文重算均PASS；4×8／8×32／16×64的reuse vdot端到端周期下降5.7751%／12.5%／17.1589%，保留同步优化后的更快RVV | K13的S1 vdot退化1.3095%，不采用；保留S0 vdot回退和更快的S1 RVV。单项资格及原镜像选择/导出已闭合；不代表新caller、默认入口、T17或完整应用收益 |
| R4 调用入口 | [普通RV64 C ABI GEMV入口](../optimizations/o2/r2-select/ENTRY_RESULT.md)完成33次性能进程／384正式窗口／192全窗口重放比较；另3次普通C进程覆盖16公共函数、48个不同case和96正常调用 | 新调用窗中4×8／8×32／16×64选S1 reuse vdot，较最快同入口RVV少9.4667%／2.7431%／7.9859%周期；K13选S1 reuse RVV。只闭合调用入口影响，完整MERGE-REG、T17和默认切换分别验收 |
| T17 新构建复现 | [同主机干净源码与新身份结果](../optimizations/o2/repro/CLEAN_RESULT.md)通过：145仓库来源、新EMU ff840528/正常参考8af118e5、50次新执行（47正常＋3预期负控）；三类最终归档独立检出原文复算通过 | Agent同机复现，工具/缓存保留；未代签人工ACK或新机器安装。384正式窗口及全部768跨构建对应窗口一致，原始PASS不转移；已作为R5/G5稳定入口的运行资格依据 |
| R5/G5 稳定入口 | [firstdot V2源包](../optimizations/o2/r2-select/FIRSTDOT_STABLE.md)已闭合：四形状8别名、单完整对象库和可独立搬移的两头文件；原文矩阵/C资格重算、实际GNU三模式/8别名/完整对象等价及错选择/错别名/错对象拒错通过，冻结V1回退实跑通过 | V2默认前三形状firstdot vdot、K13 firstdot RVV；公平比较仍保留同轮最快合格RVV。现有V1不自动迁移，变版本/开关须完整重编译；新增EMU为0，无新应用周期或PPA资格 |
| R2-S1 firstdot | [首块直接初始化实跑](../optimizations/o2/r2-vector-accum/FIRSTDOT_RESULT.md)完成33次性能进程／384正式窗口／192重放比较；另3次普通C进程及独立静态库闭合 | 三个整块reuse vdot较原S1少7.0692%／3.5043%／1.4291%周期，K13仍保留更快RVV；已由R5 V2提供版本明确的推荐源入口，原V1保留；这些仍是历史固定调用窗数据，不是完整应用收益 |
| R2-S3 重复向量配置 | [GNU与整核结果](../optimizations/o2/r2-config-reuse/RUNTIME_RESULT.md)完成33次性能进程、384正式窗口、192全窗口重放比较；三个整块reuse/vdot较本轮firstdot少3.0111%／3.2772%／0.6011%周期，另3次普通C进程、独立静态库及另一源码检出原文复算均PASS | 固定调用计划下可选，K13 S3 vdot反而慢0.4890%，保留本轮更快firstdot reuse/RVV；部分相同RVV槽有小幅可重放但未归因差异，不宣称全矩阵无退化。R5默认、完整应用与新PPA边界保持 |
| R2-S3 caller | [基础8×32普通C完整调用](../optimizations/o2/r2-config-reuse/caller/RESULT.md)的144/96窗口已闭合；[hoisted/强RVV筛选](../optimizations/o2/r2-config-reuse/caller/hoisted/RESULT.md)完成新匹配基线和五类RVV、18次新EMU及整组原文复算 | 指针缓存对匹配vdot/RVV完整调用分别少9.9838%/9.6943%周期；共同vdot跨镜像锚点超过事前1%门槛，HOLD_CONTEXT_VARIATION；[原文诊断](../optimizations/o2/r2-config-reuse/caller/hoisted/CONTEXT_RESULT.md)已补充退休与共同间接调用重定向的连续性关联，不发布最优内核或更改R5默认。仅新caller_full在固定8×32范围有运行资格，不扩展为LLM收益 |
| R2-S3 前序干预 | [单镜像固定目标干预](../optimizations/o2/r2-config-reuse/caller/hoisted/intervention/RESULT.md)完成3次EMU、每正常进程40窗/640提交、20项检查及隔离检出原文复算；正式A/B均0/8连续origin、总周期9611/9613 | 按事前规则为MIXED，未重现旧正式连续origin模式；1拍间隙随块内位置出现且不增加对应目标周期。本计划收束，旧HOLD和R5保持，不选核、不扩大矩阵；下一步仍需实际消费者输入。 |
| R2-S3 split-input | [8×32分离输入完整C调用](../optimizations/o2/r2-config-reuse/caller/split/RESULT.md)完成同镜像六对接口、v2三次EMU、84功能与252窗重放，以及独立GNU库和原文解包复算；v1预算失败原文保留 | 六对周期减少63.009076%～74.495350%，取得可选接口资格；split vdot均值308.5拍，较最低split RVV少7.703815%，三组锚点及六格门槛通过。仅在本计划内推荐vdot，R5与旧hoisted HOLD保持，不是完整应用收益 |
| R2-S3 fixed-weight | [固定A、N1/N4完整消费者](../optimizations/o2/r2-config-reuse/caller/fixed-weight/RESULT.md)完成原3次EMU、每正常进程168功能/8控制/504窗/15104提交及重放；27函数可选库、391原归档成员恢复和新进程原文复算通过 | packed每stream只准备一次A；六对接口检查通过，但N1/N4锚点最大6.677019%/2.237354%，均HOLD_CONTEXT_VARIATION、无性能优选。可显式使用，R5/旧split与全部RVV回退保持；仅有界工程示例，未接入实际LLM。主ZIP以原字节分片发布，先重组再按冻结审计器复算 |
| R2-S3 Q288 / acc8 / fused | [acc8 第二步](../optimizations/o2/r2-config-reuse/caller/runq-q288/acc8/target/RESULT.md)已完成真实负控、正常恢复、独立重放与隔离原文复算；[完整 Q 融合](../optimizations/o2/r2-config-reuse/caller/runq-q288/fused/target/RESULT.md)在同一目标 ELF 的共同 selfwarm、反序两块和全部四锚点下完成公平比较 | fused-vdot / fused-RVV4 相对各自 acc8 保守少23.797253% / 23.852889%周期；fused-vdot对本次最快RVV保守少6.844186%，可按本固定计划显式选用，保留强RVV与旧接口回退。[宿主完整forward](../optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/RESULT.md)已取得72个真实调用输入并完成两融合ELF模型接续，尚无目标token/模型质量资格；R5默认保持。 |
| R2-S3 Q288 phased / TA | [phased目标结果](../optimizations/o2/r2-config-reuse/caller/runq-q288/fused/phased/target/RESULT.md)已闭合三进程、同ELF反序计划和原文/新源复算；[TA结果](../optimizations/o2/r2-config-reuse/caller/runq-q288/fused/phased/tail/target/RESULT.md)及[普通C入口/真实链接](../optimizations/o2/r2-config-reuse/caller/runq-q288/fused/phased/README.md)已交付 | 原phased计划中PV对FV/FR保守少3.7948849%/10.3370386%周期；本批显式选择TA入口 `q288_tail_vdot`。资格限固定合成、已量化/预打包Q及同方法完整Q selfwarm；不含pack、量化、token、模型质量或新ASIC结论，R5稳定默认保持。 |
| R2-S3 活动 forward / FP32→QKV | [活动状态接续](../optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/active/RESULT.md)以原样参考与独立TA/FR状态完成3位置完整logits/KV逐位一致、消费前K/V污染和漏写拒错；[目标QKV结果](../optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/active/target/RESULT.md)已按新ELF完成真实负控、恢复、独立重放与封存新源复算 | 含共同FP32量化的完整QKV边界，TA对本批强FR保守少3.4731903%周期，FR锚点跨度0.2261795%，按事前规则显式选TA并保留FR回退；普通C两变体实际GNU链接闭合。资格限层0/位置0的计时输入与位置1功能覆盖、预打包权重和固定T17；不是目标完整forward/token、训练模型质量、最优RVV量化或新ASIC资格，R5默认保持。 |
| R2-S3 完整 forward 阶段 | [完整消费者与阶段结果](../optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages/RESULT.md)建立宿主256位置、实际数学/TLS、两组各4进程的完整参考执行；37张K288矩阵经172Q及13尾块接入强FR/TA，6张K768 W2保留scalar；RoPE与真实W1/classifier尾部各有独立目标边界 | 每种资格按各自最终输入与原文复算限定；完整参考不等于完整香山DiffTest，MAC覆盖和局部热窗口均不外推token。scalar/cache与scalar/FR/TA没有合并验证，R5默认、强FR及旧失败保持。 |
| R3 | [perfDebugInfo子项](../optimizations/o4/perf/RESULT.md)已闭合并保留577位；[carry-save归约筛选](../optimizations/o4/reduce/RESULT.md)完成真实RTL证书/G1/完整FU新AB及封存复算 | 归约候选r2r仅改善0.8849%、面积增加0.5459%、i2r退化1.9166%，未达事前门槛，STOP_SCREEN；不采用、不扩大父级/整核、不继续枚举。生产RTL与稳定默认不变，两个子项均不产生新应用周期/ASIC成绩 |

依据：[历史项目状态](project-status-20261020.md)、[H1 成本与时序](../optimizations/o2/result-width/h1/H1_RESULT.md)、[H1 周期](../optimizations/o2/result-width/h1/performance/B0_H1_RESULT.md)、[R2 入口](../../R2_STATUS.md)。结果绑定各自源码、配置和输入；运行是否结束须读实际 state、日志和进程。

## 2. Agent 按当前任务包执行与证据调整

在当前用户已授权的工程范围内，**沿当前规划的 14 个工程包及默认次序推进，Agent 无需每一轮重新搜索和规划全部可能方向**。工作包界定做什么、完成条件；Agent 在包内自主决定实现方法、试验和验证顺序。数量不是约束：新证据优先形成现有包的子项，确有独立目标或验收边界时按第 6 节调整工作包。

1. **先接续。** 核实当前 SHA、工作树、真实运行、最新结论和 Issue 有效认领；合格历史结果复用，仍在运行的任务继续观察，不重复启动。进程已结束时先读对应入口的恢复能力；S2 当前不能断点续跑，处理方式见[筛选合同的中断与重复构建限制](../optimizations/o2/r2-safe-tail/FULLCORE_VALIDATION.md#中断与重复构建限制)。
2. **按序选空闲包并 WORK。** `MERGE-REG` 的[新夹具拒错／正常恢复及相容旧日志复核](../optimizations/o2/fullcore/MERGED_REGRESSION_RESULT.md)已闭合，绑定与R4相同的6d2/1a23硬件。`R2-S2` 已完成固定布局主批和强 RVV 有界取舍：reuse 相对 S0 的收益真实，但未胜过同镜像较快 RVV，当前停止扩大采用。`R2-SELECT` 的[原镜像选择/查询/导出](../optimizations/o2/r2-select/RESULT.md)已完成，`R4/O5` 的[普通调用入口子项](../optimizations/o2/r2-select/ENTRY_RESULT.md)已闭合新路径的性能及普通C使用验证。T17已按独立新构建身份完成实际复现和50次新运行，R5/G5已形成可使用的稳定C源入口、默认库构建及回退。后续以此版本保底，只有明确的新瓶颈假设才开展有界试验；R2-S1首块初始化已按独立合同完成同入口强RVV矩阵、普通C及独立库交付；R2-S3重复向量配置已完成独立状态证明、GNU、完整固定调用窗矩阵与普通C可选库；三个整块reuse/vdot有实测收益，K13不采用S3 vdot，保留本轮更快firstdot/RVV。零删除RVV的部分窗口仍有未归因上下文差异，不概括为全矩阵无退化。当前子项不重复仿真，后续优先寻找真实应用的打包、搬运和调用成本证据，再决定是否值得开展新有界试验；不按静态删指令数或单个FU指标继续开题。未来若再改整数叶或旧8×32 caller/调度布局，仍先在8×32/dataset0/endtoend与最快同入口RVV配对验证。仅修改完整Q包装且六叶完整机器码不变时，按Q288新合同先完成有界完整Q正确性与成本判别；不复跑未变叶，也不转借其旧PASS。原 B0/H1 固定实物未变化时不重复预检；这不是固定人员分工。若本包已有认领或冲突，按现有表选择下一输入就绪、未占用的**准确叶级包**。按[协作约定](collaboration-current.md)发布 WORK 后回读；不允许同包重复开发，也要检查公共生成器、接口和重型资源。
3. **包内连续自主工作。** 实现、主机检查、真实验证、定位问题、修订与提交不逐步征求确认。正确性失败优先修复受影响层级；无收益和退化依据第 4 节明确采用、再试一次有依据的修订或关闭。
4. **仅有理由才换包。** 被认领、依赖缺失、实际资源冲突或技术证据要求调整时，用 PAUSE/UPDATE 记录原因、是否释放及残留保护，改选已规划的独立包。缺什么补 `R0` 的对应子项，不为了填表反复预检，也不转去制作比赛材料。
5. **区分 R0 / S2 / 新硬件候选。** S2 的 `preflight` 分别报告 `build_ready` 和 `runtime_ready`。仅前者满足，可先 `--action build` 构建并静态检查 26 份 ELF，仍不得声称 EMU 或 DiffTest PASS；只有运行来源和所有固定回执齐备才能 `--action all`。历史 B0 使用其 `repro.py` 与旧版本锁；当前 H1／新 RTL 使用匹配的源码、硬件 pins 与新构建身份，不能拿 B0 锁拒绝新合法构建。
6. **阶段交付。** 候选进入 READY 等待按短窗口集成；完成采用/否决和相应验证后 DONE 并记一条计分板成果。获选组合走 `R4/O5 → T17 → R5/G5`，留下可用稳定版本及回退。条件探索不是必须逐项做完。

S1/S2 是不同叶级包，但 `candidate.py` 被 S2 的完整 Git blob 合同冻结：**S1 默认以独立候选模块实现**，只读引用原 O3 生成器/模型。确需修改相同文件时先协调版本和输出边界；旧 S2 在冻结提交复现，新候选明确新源码身份与检查条件，不静默放宽旧验证。

## 3. 工程工作包全表


沿用现有编号，以下为**当前规划的 14 个工程包**；默认次序见第 2 节，条件探索可以不开展，同一父包不构成对所有子项的排他认领。表格维护当前入口和决定，执行者及运行中／暂停等实时状态只放协调 Issue。

### A. 只补实际缺失的工程能力

| 工作包 | 当前从哪里开始／前置 | 完成条件与入口 |
| --- | --- | --- |
| MERGE-REG 合并基线回归 | [新夹具合同与原始证据交付](../optimizations/o2/fullcore/MERGED_REGRESSION_RESULT.md)完成；12旧正常任务复用来源逐字节复核，新matrix0负控→新正常恢复2次实际执行；本轮接续新增EMU为0 | 原实物审计与558载荷归档的完整架构／异常／控制／dense／O2离线复算PASS。与R4固定6d2/1a23相容；旧9b3缺项、B0/H1旧合同与新构建身份分别保留 |
| R0 运行输入与复现缺项 | 只对当前实验缺的工具、依赖、正常／故障 NEMU、AM、flash、镜像和构建身份做预检与恢复 | 输入有来源或构建命令及校验方式；新机器能取得所需输入，配置不依赖个人目录，见[复现入口](../optimizations/o2/repro/README.md)。环境已满足时直接跳过 |
| T03 技术要求与语义缺项 | 对照[规格](../spec/vdot.md)及已有实现／验收，定位真正未覆盖的技术要求；Q01～Q07 区分现行内部合同、已获答复与未答复项 | 缺项补实现或对应测试；语义变化同步 RTL/NEMU/封装/测试。沿现行合同可继续工程开发，未答复不伪写官方认可，也不无条件阻塞所有优化 |
| T04 hello/vadd 与调试链路 | [当前输出与两相波形结果](../evidence/stage1-current-20261025/RESULT.md)已闭合：新BIN在生产T17与独立FST模型各通过3组/24元素普通DiffTest；两FU/八提交槽的三条事件链、24项工具检查及独立目录离线重放通过 | [运行/提取入口](stage1.md)可复用；输入不变时无需重跑。程序、模型或调试接口变化才按影响补验；不是新vdot全核/应用性能/PPA或人工验收，不包括报告、录屏和赛事提交 |

negative-reference.so 是故障注入夹具，不是正常黄金 NEMU；不能把新哈希填进旧锁冒充原文件。无法恢复旧二进制时保留旧验收缺项，以新身份重建夹具并验证预期拒错和同镜像正常恢复。不得修改任何仍在运行的物理输入。

### B. 持续优化：先测现有候选，再按瓶颈扩展

| 工作包 | 当前从哪里开始／前置 | 完成条件与入口 |
| --- | --- | --- |
| R2-S2 安全尾部筛选 | [新固定布局合同与结果](../optimizations/o2/r2-safe-tail/FIXED_RESULT.md)闭合S0→S2单项因果比较；两形状/三数据集/basic-reuse/core-endtoend、负控恢复及重放PASS。另以仅RVV两槽改变的同镜像K13/endtoend探针比较已合格S1 RVV | 当前reuse相对S0少10.952%，却在dataset0探针比强RVV慢6.705%；basic退化，不扩大采用矩阵。该探针为4窗口单元格，不是强RVV全矩阵资格。保留完整原始数据、旧合同/哈希/归档；只有新可检验假设才重开。原[固定B0/H1合同](../optimizations/o2/r2-safe-tail/FULLCORE_VALIDATION.md)仍BLOCKED，不重跑未变缺项，也不以合并EMU替代旧对照或MERGE-REG |
| R2-S1 向量累加与对等 RVV | 原[S1完整主批](../optimizations/o2/r2-vector-accum/README.md)与新增[firstdot运行子项](../optimizations/o2/r2-vector-accum/FIRSTDOT_RESULT.md)均已闭合；新独立C库保留16函数和全部原始证据 | firstdot三个整块reuse vdot胜过原S1及本轮最快RVV，K13继续用RVV；R5默认不变，可使用独立firstdot入口及明确回退。新caller/布局/应用仍按影响验证，旧静态原型与冻结批次原样保留 |
| R2-S3 后续应用瓶颈优化 | 原caller/split/fixed-weight/Q/phased/TA合同与失败证据保留；[实际FP32→QKV](../optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/active/target/RESULT.md)沿用自身资格；新[完整forward阶段](../optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages/RESULT.md)已建立数学运行时与完整参考消费者，具名目标边界和复算入口独立列明 | 下一步先评估完整调用链的目标正确性与测量成本，给验证/性能镜像分别固定身份，避免把逐矩阵重算、大转储或局部selfwarm带入应用收益。这属于长期应用性能工程，当前赛题没有完整LLM token/s硬门槛，按实际收益决定投入。再按目标阶段数据选择K768 W2、量化、norm或非线性；W2仍scalar，不能因其MAC占比低就忽略。严格数值[研究](../optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages/RESEARCH.md)中的RMSNorm只是可选低改动起点，不自动开全RVV round/近似exp；旧百分比不迁移或串乘。真实checkpoint/tokenizer/模型质量、完整token和新ASIC仍各自缺证据；R5与强RVV回退保持。 |
| R3 硬件成本／关键路径优化 | [perf消费者与覆盖](../optimizations/o4/perf/RESULT.md)及[carry-save归约筛选](../optimizations/o4/reduce/RESULT.md)已闭合，保留生产实现；归约候选真实RTL/G1通过，但完整FU时序/面积未达事前门槛 | 关闭直接裁剪perf与本次CSA假设。后续须有新的真实存活逻辑/路径或应用瓶颈证据，再按影响完成FU／父级／整核／公平周期与同条件STA；不复跑已完成子项，不因抽象树深自动枚举或强改RTL |
| R1-H1b 19 位保存备选 | 默认不开展；32 位 H1 已完成，只有新增映射证据表明继续收窄值得才开启 | 19→32 符号扩展、高 96 位清零及边界正确，并有实际收益；否则关闭，见[H1 合同](../optimizations/o2/result-width/h1/CONTRACT.md) |
| T15-REPRO 参数扩展复核 | 已有[参数合同](../spec/t15-parameters.md)及[结果](t15-parameter-extension.md)先复用；只在相关实现变化、扩展验收缺项或有优化依据时重开 | 独立 INT16×8／64 位结果扩展在其范围内可复现；不扩大为生产整核支持，不作为默认 INT8 优化的前置 |
| R2-SELECT 应用与组合取舍 | [原镜像选择、查询与导出](../optimizations/o2/r2-select/RESULT.md)已完成：复算S1 v2完整768窗口/64候选格，每格12窗口；三个整块形状选S1 reuse vdot，K13选较快S1 reuse RVV并保留S0 vdot回退。48份完整原镜像精确导出，Linux/Windows各21项测试通过 | 本次只闭合原镜像数据层，未新增运行时或默认入口；实际export/verify/resolve见[入口](../optimizations/o2/r2-select/README.md)。新caller/dispatcher/合并ELF由R4/O5验证实际新增影响，先测8×32/dataset0/endtoend且强RVV走相同新调用路径；原10.75周期余量只作筛选依据。T17新身份与R5/G5稳定入口资格独立列明，不拼接不相容PASS |

S2 保持 dot8 合法域，安全读取剩余 5 项、显式补零、恢复 VL=8，全部成本计入窗口；16×64 是不应变化的控制形状。新合并 EMU 不能冒充合同中的 B0/H1。S1 先独立验证，组合收益不能代替单项归因。R3 保留 ROB、pdest、异常、写使能、两槽独立身份、必要观测、II=1、首响应 2 拍、反压／取消与 DIV 互斥；577 位额外信息不是可以直接删除的数量。

### C. 将获选方案闭合为稳定、可复现的工程

| 工作包 | 当前从哪里开始／前置 | 完成条件与入口 |
| --- | --- | --- |
| R4/O5 获选组合回归 | [新普通调用入口](../optimizations/o2/r2-select/ENTRY_RESULT.md)已完成24个性能ELF和1个普通C ELF的影响验证、原始证据复算及公共源码交付；硬件仍为固定6d2/1a23身份 | 调用入口与[MERGE-REG](../optimizations/o2/fullcore/MERGED_REGRESSION_RESULT.md)的功能／异常／控制证据均绑定相同6d2/1a23身份，新构建已由T17另行验证；完整全宽结果、差分拒错／恢复、性能及必要成本证据一致，无未解释失败。只复测变化影响，不拼接不相容PASS |
| T17 干净环境复现 | [合同范围已完成](../optimizations/o2/repro/CLEAN_RESULT.md)：同主机独立源码/产物、145仓库来源、实际构建、14整核＋3C＋33矩阵新执行；传输层修正后最终M03/C02与整核包独立原文复算通过 | 源码／依赖／镜像／命令及差异可追溯。执行者为Agent，未取得人工ACK或新机器安装资格；三类归档跨系统字节/索引另核验。R5/G5使用该固定身份，不重复旧运行或改判旧B0/H1 |
| R5/G5 稳定版本与默认入口 | [firstdot V2范围已闭合](../optimizations/o2/r2-select/FIRSTDOT_STABLE.md)：固定firstdot普通C资格、四形状C别名、可搬移静态库/双头文件及完整迁移说明；原firstdot源码和V1执行输入保持原字节 | GNU完整库对象与合格firstdot相等，三模式/八别名caller及可重定位link逐字节相等，搬移SDK与V1回退实跑通过；新增EMU为0。新caller/布局/应用仍按影响验证，未冒称全赛题、人工ACK或新增ASIC PPA通过 |

## 4. 每轮实验怎样决定下一步

开始前在已有结果文件或实验记录写清：假设、固定输入／修改范围、主要指标与可接受代价、最小实验和资源预算。已有合同足够时直接引用，不重复建文件。默认先用主机／静态检查和冒烟排除无效候选，再扩大验证。

| 结果 | 下一动作 |
| --- | --- |
| 正确性、身份、异常或边界安全失败 | 停止该候选的性能判断，修复最小失败并重测受影响层级；其他独立工作继续 |
| 环境／固定输入缺失 | 补 R0 的具体缺项，保留 BLOCKED 与已尝试动作；另一条线做独立原型／分析，不换不明二进制或改旧锁凑通过 |
| S2 或 S1 有可重放端到端收益，控制样本无未解释变化 | 进入 R2-SELECT 和组合回归；保持单项归因，再决定是否组合 |
| 无收益、退化，或更强 RVV 消除了优势 | 保留较好基线；依据完整数据选择一次有针对性的修订、转下一个瓶颈或关闭。只有 core 改善不能写成端到端收益 |
| R3 字段必要、路径不属于 VDot、收益不足或破坏观测 | 关闭该假设，记录依据，不为完成工作包强改 RTL |
| 面积更小但时序变差，或一个形状改善而其他形状退化 | 按事先指标衡量整体取舍，可保留分场景候选；不只取最佳样本、不事后换约束或降低门槛 |
| 新数据推翻当前瓶颈判断 | 更新相应工作包的下一动作，将新假设放入 R2-S3／R3 子项，先做最小实验；ISA 或公平合同变化单独定义身份和验证 |
| 当前候选均无采用价值，或达到用户预算／本轮停止条件 | 完成已获选组合的工程闭环，报告稳定版本、排除的方向和尚未验证的假设；不声称已达理论最优，不为保持忙碌无限开题 |

每个最小实验必须有能作决定的终点。达到约定预算或重复得到同类失败而无新证据时，先作取舍，不自动续开相同尝试；新证据才能重开已否决候选。软件以选定场景的 endtoend 周期和较快合格 RVV 为主，同时保留 core 与其余尺寸；硬件同时检查功能、接口、周期、面积和相关 STA，不把宿主耗时当处理器周期。

## 5. 工程完成与继续优化的边界

工程达标要有以下可定位的实现和验证；适用的历史证据可复用，有变化才按影响补测：

- 环境与 hello/vadd 可运行，必要调试和波形链路可用；vdot 的算术、编码、接入和向量状态符合当前明确标识的技术合同。
- 正数、负数、边界、全 128 位结果、别名、异常和流水控制有对应测试；NEMU 扩展与真实 DiffTest 有正常通过、故障捕获及同镜像恢复证据。
- 有正确且公平的 RVV 等价实现，以及延迟、吞吐和应用端到端的可重放比较；性能结论明确实现、尺寸、数据、配置和覆盖边界。
- 选中源码、依赖／补丁、构建与运行入口可在干净目录复现；未解决项如实记录，必要技术缺项未闭合就不能宣称全部达标。

达标后以稳定版本为保底持续优化；一个候选失败不影响已有成果，一个候选成功也不意味着不再优化。条件探索不要求全部做完，停止依据是用户目标／预算和当前证据，而非把工作包逐行打勾。比赛材料和人工事务不纳入上述工程闭环。

## 6. 只维护当前决定

普通工作更新相关结果并追加一条计分板记录；只有当前选择、前置或下一动作改变才更新本路线。结论及理由写计分板，详细数据留原处，本文件不累积逐日进度。已关闭工作包只留一行采用／不采用／完成结论和证据。

新增工作优先作为已有包的子项；只有新目标、独立验收或明确依赖边界才增包。旧计划、旧排期和 T16／T18 等材料事务只供历史追溯，不驱动当前 Agent 队列；已完成的 H1、T05～T15 等工作不因路线整理重新启动。技术要求来源和未确认项沿[vdot 规格](../spec/vdot.md)读取；获得新的真实要求时更新受影响的工程包，不把未确认内容写成事实。

