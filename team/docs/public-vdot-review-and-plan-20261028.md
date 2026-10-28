# 公开 vdot 项目、分支进度与 zjhwork 后续优化计划

核查日期：2026-10-28（日期级记录）。执行身份：已认证 `@cc77-builder / Agent`。操作 ID：`20261028-cc77-public-vdot-review`。

**比较基线：`zjhwork@4653fd51a1195c8e370e11f564acbc6613f4bbd0`。** 本次用户明确要求把计划放入 zjhwork；仅新增研究文档与导航，不合并其他分支、不修改 RTL、ISA/NEMU、默认入口或封存证据，不启动仿真。本报告是用户指定的后续研究建议，不替代[当前开发路线](development-route-current.md)的实际任务状态，也不领取或接管其他成员正在运行的任务。

## 1. 结论：不要再按 10 月 21 日的旧进度规划

当前 zjhwork 已发布 **0f 硬件＋firstdot V2 四形状＋显式 C8 8×32 包的 R5/G5 工程验收**。S1、S2、首块初始化、部分配置复用和 DIV 取消后门控保持修复均已有后续成果；“S2 只有主机验证、整个项目等待首次实测”不再是本分支的当前状态。[A1][A2]

建议保留这个已验收版本，下一轮先做两件事：

1. **选择性评估 zufan 已验证的应用接口与消费者，而不是重复实现 S1/S2。** 先从 8×32 split-input 完整 C 调用开始，再按证据决定是否迁入 FP32→QKV；所有迁入结果须在当前 0f 组合版重新取得资格。
2. **补一个版本明确、口径一致的外部实现对照。** 当前 O2 吞吐已有优势线索，Jade 的依赖链较短值得研究，但不能拿不同项目 README 的倍数直接排名，更不能只压缩仿真周期而忽略实际时序。

RTL 新实验放在路径归因之后。平衡树、低32位保存、II=1 已经具备；577位性能元数据保留、carry-save 归约及 C3-HF 门控候选的既有否决结论也应复用，不因换一个计划名称就重新枚举。[A2][B1]

## 2. 证据等级与比较规则

本次联网搜索公开 GitHub 仓库，并通过连接器读取仓库文档、Git 分支关系及关键 RTL。不是对所有开源项目的穷尽检索，也不是本次重新运行了这些项目。

| 等级 | 本文如何使用 | 不能据此声称什么 |
| --- | --- | --- |
| 作者公开报告 | 转述作者报告的配置、结果和限制，保留“作者报告”标识 | 不能当成本次独立复测或同场排名 |
| 本仓库历史统一复测 | 使用固定提交、统一基础硬件/负载下的既有数据 | 不等于今天重新构建的所有项目成绩 |
| 当前分支验收记录 | 说明指定源码、二进制和合同下已有资格 | 不能跨硬件、跨 ELF、跨调用边界转借 PASS |
| 本次源码审查与推断 | 指出实际代码结构、风险和可检验假设 | 不把静态指令数、结构推断写成新性能、功耗或 PPA |

统一公式：`加速比 = 同口径合格 RVV cycles / vdot cycles`；周期降低率与加速倍数分别报告。gross cycles、扣循环回归斜率、单元 II、NEMU 指令数、应用周期和 tokens/s 是不同指标。结果还须区分 dot8 单结果和 dot4 分组累加、是否读取 oldVd、是否包括量化/打包/配置/存储、RVV 是否获得对等优化。

## 3. 找到的公开项目及指标

### 3.1 值得重点阅读的五个项目

| 项目 | 实际可见进度及作者报告 | 与本项目比较的限制 | 优先阅读 |
| --- | --- | --- | --- |
| [Jade](https://github.com/Jade0x13157A6/cie2026-xiangshan-vdot) | 昆明湖 V2 全核差分与76个定向/随机用例；1000次调用的最小样本为标量C 24862、vdot 8203 cycles，即3.030× | 基线是禁止自动向量化的标量C，不是最快RVV；作者平台为KunminghuV2Config，本仓库统一复测另用MinimalConfig | `docs/RESULTS.md`、`patches/03-xiangshan-vdot.patch` |
| [试水 / Shishui](https://github.com/vienna-0FFH/cie2026-shishui-vdot) | 报告香山/NEMU全核运行；依赖链净5.983对27.980 cycles/dot，4.677×；八路独立净0.917对6.500，7.086× | N=0/64/256/1024回归并减去循环控制斜率，不是本项目四路gross batch；0.917不能解读为单发射FU突破II=1 | `vdot/docs/performance-results.md`、`vdot/integration/patches/xiangshan-vdot.patch` |
| [Redoop](https://github.com/redoop/xiangshan-vdot) | 报告GEMM指令6797对86554、净周期约8.2×；独立1.78/依赖7.02 cycles/条；TinyGPT 13615 instructions/token；有RTL、NEMU、Spike和软件栈 | 原生是每INT32 lane的dot4＋oldVd累加，不是本项目dot8输出高96位零；TinyGPT数字是NEMU指令数，不是香山tokens/s；0.014%面积为其作者口径，不能与本项目FU/父级Nangate参考面积混比 | `rtl/yunsuan/.../Vdot64b.scala`、`software/`、`docs/` |
| [Qixuan](https://github.com/qixuan-cn/cie2026-qxriscv-xiangshan-vdot) | 模块RTL 1518/1518，RTL↔NEMU导出结果1513/1513一致，模块延迟3拍、吞吐1条/拍 | README明确香山平台集成未完成，Chisel集成骨架未编译；不是整核DiffTest或实际应用加速 | `rtl/verilog/VDot.v`、`docs/phase2/test_report.md`、`docs/phase3/cosim_report.md` |
| [AsyncSys](https://github.com/Sun-Yingjie/cie2026-AsyncSys-xiangshan-vdot) | hello全核差分通过；INT8/INT16、signed/unsigned/mixed局部运算核6项测试、2500+随机；wrapper/译码/自定义指令NEMU/全核尚待接入 | 64位切片形成两个dot4或dot2累加结果，语义不同；没有可直接比较的vdot整核加速比 | `rtl/yunsuan/VDot64b.scala`及对应Spec |

上述数值均有对应公开原文，未由本轮重新仿真。[P1]—[P7]

还核查到：`mmm-arch/cie2026-01-xiangshan-vdot` 当前树主要为阶段一日志和截图；`juese12/cie2026-skito-SKIProject` README列出hello/vadd和波形已完成、vdot实现待开始；`Sleepless9/cie2026-try1try-xiangshan-vdot` 根README仍为xs-env部署说明；GEMwhu仓库README勾选三阶段完成，但本轮未从其详细材料独立核实可比数值。不能把缺少根README指标等同于项目必然没有成果，也不将未核实指标填成0。[P8]

**公开可读不等于任意复制许可。** 移植前单独核对仓库及上游文件许可、固定原始提交和归属；本轮只借鉴结构与验证思路，没有复制第三方 RTL 进生产代码。

### 3.2 本仓库已经做过的统一复测更有参考价值

2026-10-17四项目复测采用同一香山基础版本 `16ae9ddcda54fc9a2fddffad73174cf793ac7814`、MinimalConfig、单核/VLEN128、统一工具和固定负载。共64镜像、860校验窗口、384正式窗口，每格12个正式样本。外部实现固定为 Jade `a17e381...`、试水 `4421d88...`、Redoop `fba90f8...`；本次读取的三者分支头仍分别对应这些提交。[A3]

| 实现及测量批次 | 单次 gross cycles | 依赖链256 | 四路独立batch128 | load/compute/store64 | batch 对各自同轮 RVV |
| --- | ---: | ---: | ---: | ---: | ---: |
| 本项目历史T14，10月17统一批 | 71.00 | 1857.00 | 453.25 | 1127.50 | 1.496× |
| Jade，10月17统一批 | 70.00 | 1601.25 | 260.25 | 1126.25 | 2.605× |
| 试水，10月17统一批 | 71.00 | 1857.00 | 292.00 | 1127.50 | 2.322× |
| Redoop＋dot8适配，10月17统一批 | 90.25 | 3673.00 | 744.75 | 1155.50 | 0.929× |
| 本项目O2/0f后续已验微基准，**不同批次** | 71.00 | 1857.00 | 221.00 | 1127.50 | 678/221＝3.067873× |

最后一行用于展示本项目演进，不与前四行拼成“本轮统一重测排名”。方向上，本项目已不再处于旧T14的吞吐落后状态；仍值得研究的是 Jade 的依赖链路径，而不是重复追求本FU已实现的无停顿II=1。Redoop的dot8适配含额外指令，0.929×不能否定其原生dot4 GEMM价值。[A2][A3]

## 4. 仓库各分支：先看资格，不能按提交数排性能

以下都是本轮写文档前的固定快照。“对方独有/本基线独有”是Git历史差异，不是已验证功能数量。

| 分支 | 核查完整提交 | 相对zjhwork基线 | 实际定位与判断 |
| --- | --- | --- | --- |
| zjhwork | `4653fd51a1195c8e370e11f564acbc6613f4bbd0` | 本次基线 | 0f＋firstdot V2＋显式C8，R5/G5工程验收完成；保底主线 |
| zjhwork2 | `79ce5643e225437000c3b5a3f2c97e888c47596c` | ahead 0 / behind 29 | 原S2候选与严格ELF入口，历史停在预检；已全部包含于zjhwork，无需再次整体合并 |
| zufan | `ffd668bf1bc80850d382f514d13bb00316c85582` | 已分叉，独有53 / 基线独有4 | firstdot/config-reuse后继续推进split输入、Q288、FP32→QKV及forward分段；应用拓展更多，但HOLD/NOT_TESTED边界仍在 |
| James_Hotten | `e611eafb1af2730d8d86c768ee98f1b80f5fe0b2` | 已分叉，独有125 / 基线独有4 | 包含自身门控/观察器/严格验证历史，并已同步zufan至431938271的50个提交；不是只停在旧PARTIAL_KILL缺项时点 |
| main | `e9c70db384ca71c494ef197aba598ed4bc08fa9b` | 已分叉，独有22 / 基线独有97 | README仍说明10月17统一VFEX4及T12/T13/T14阶段；不是最新R5稳定组合，不能因为叫main就视为最新 |
| zufan-t12-review-20261014 | `f188f6f7588270714d94d970fe36f2f2cdda15b9` | 历史审查快照，本轮未另算提交差 | 入口仍是早期T10/T11与T12审查时期，不作为新性能基线 |

zufan、James与当前zjhwork的共同祖先为 `c9132b8d7f284ad7e76550315214b5b2ca431f79`。不能强推或整树覆盖来“同步最新”；本次不合并这两个分支。[B1][B2][B3]

### 值得吸收的分支成果及数值边界

- **zufan split-input：** 固定8×32完整C调用中，split vdot均值308.5 cycles，比同计划最低split RVV少7.703815%；接口对比中63.009076%—74.495350%的周期减少主要涉及打包/搬运边界，不能写成RTL提速。适合作为当前0f组合的首个移植候选。[B1]
- **zufan FP32→QKV：** 含共同FP32量化的完整QKV边界，TA相对本批强FR保守少3.4731903%，FR锚点跨度0.2261795%；普通C两变体链接闭合。仅层0/位置0计时、位置1功能、预打包权重和固定T17硬件；不是完整forward/token或模型质量结果。[B1]
- **zufan尚未闭合项：** fixed-weight N1/N4、部分caller上下文、K768 W2、RMSNorm存在锚点超1%的HOLD；完整香山forward/token没有已确认资格。不能把局部PASS拼接为整个LLM通过。[B1]
- **James历史firstdot探针：** bc9/e66硬件、8×32/dataset0/endtoend下，reuse vdot为268.5 cycles，S1为278.25，最快合格RVV为289；仅有界探针，不与当前zjhwork C8的273/299直接横比，也不把后来同步的团队完整矩阵重新算成James独立实测。[B2]

## 5. 当前 zjhwork 的真实优势和短板

| 维度 | 已有事实 | 后续应解决的问题 |
| --- | --- | --- |
| FU协议 | O2两槽，首响应2拍、无停顿II=1；全宽数据、身份、反压、取消/排空和共享DIV验证 | 不以丢失异常、元数据或反压能力换取表面低开销 |
| 数据通路 | 8个signed INT8乘法，16→17→18→19位平衡归约；H1只保存低32位，接口补高96位零 | 平衡树和低32位不是待实现的新优化；进一步位宽裁剪先查实际映射成本 |
| 微基准 | batch128 221对RVV678，3.067873× | 依赖链1857、数据流1127.5仍提示不同瓶颈，不能推广成所有应用3倍 |
| C8显式软件包 | 8×32固定完整调用窗273对最快RVV299，1.095238×；对firstdot282.25少3.2772% | 普通调用边界收益有限；K13继续选择合格RVV，不强行用vdot |
| 参考PPA | 0f完整FU面积17298.246、完整VFEX4父级284614.946（同参考库报告单位）；1ns参考目标仍未闭合 | 不能称整核面积、后布局Fmax或功耗；时序优化需同库/同边界/同约束 |
| 验收 | R5/G5组合完成；clean02原墙钟FAIL保留，13旧＋1新组合验收有明确来源 | 同主机Agent干净构建不等于独立成员或新机器安装，不代签ACK |

依据当前最终验收及生产源码。[A2][R1][R2]

## 6. RTL 具体学习建议

### 6.1 Jade：学习执行路径选择，不直接搬“一拍点积”

实际补丁把vdot接入 `VIAluFix` / `FuType.vialuF`，结果和isVdot通过相应寄存器对齐。八路乘法及4/2/1归约组合计算，正常框架的短延迟路径能解释其依赖链优势的研究价值。[P2]

可研究：在当前硬件上分离“请求到FU响应”“写回/旁路”“下一条依赖指令发射”的周期，判断差距来自算术级数还是外层调度。仅当真实临界路径、共享端口冲突和完整元数据合同允许时，才立一个独立短延迟候选。

不能直接照搬：一拍中容纳乘法＋三级归约可能降低可达频率；外部合法域与本项目 `vill/SEW/LMUL/vm/vstart/VL=8` 严格合同不完全相同。必须保留v0目的、异常、取消、反压与共享FU行为。较少仿真cycles不自动代表实际时间更短。

### 6.2 试水：学习现有流水框架与输出控制对齐

`VIMacU` 复用 `VecPipedFuncUnit`，从延迟后的 `outData.src` 构造乘积和平衡树，将结果、饱和位和非法条件一起选择。要注意：名义两拍接口不等于乘法/归约被均匀切成两个物理算术级；仍须看寄存器位置和STA。[P4]

对本项目的意义是研究现有向量执行端口与旁路，而不是再加一棵平衡树。本项目已使用 `+&` 的17/18/19位逐级扩展；不能将既有结构再次登记为优化成果。[R1]

### 6.3 Redoop：学习数据、oldVd 与控制的同事务流水

`Vdot64b.scala` 在fire时同步寄存vs1/vs2/oldVd，通过 `GatedValidRegNext` 对齐第二级，再对每个32位lane做符号扩展和回绕累加。这个例子很适合学习“算术结果正确，但输入/旧目的/控制错拍仍会出错”的集成风险。[P6]

当前O2两槽已经分别保存每个请求的ctrl/perf身份，不应退化成一份共享元数据。Redoop的oldVd累加是另一种ISA语义；可学习其软件intrinsic、打包和实际消费者接口，但不能用它替换生产dot8合同。dot4-accumulate只能作为另立编码、完整验证的远期研究，不是本计划默认改动。

### 6.4 Qixuan / AsyncSys：适合参数化与分层验证学习

Qixuan明确模块级验证和整核集成的边界；AsyncSys区分signed/unsigned/mixed扩展和lane内回绕。可用于检查参数化设计的位宽、符号和测试组织。当前生产全核仍是INT8 dot8，已存在的独立INT16扩展不因这些示例而自动获得生产全核资格。[P7]

### 6.5 当前代码自身应保留的模式

`VDotElastic.scala` 的P/R独立live/kill、旧R输出＋旧P搬移＋新接收同拍、停顿输出整包稳定，以及非法指令关闭写使能，是当前工程的重要资产。任何短延迟或门控候选都应复用其测试合同，不能只保留数学点积测试。[R2]

## 7. 后续优化计划：按现有工作包挂子项，不推倒重来

下面是建议执行次序及准入条件。未自动实施、未排占他人资源；实际执行前按协调Issue核查准确叶级包和冻结输入。现有R5验收不因文档新增而失效，默认入口不自动切换。

| 建议顺序 / 关联包 | 具体工作 | 交付物 | 进入下一步的条件 |
| --- | --- | --- | --- |
| 1 / R0＋R2-SELECT：当前资格与可移植差异 | 固定4653fd5、0f/参考模型/firstdot V2/C8身份；列出zufan split/QKV源闭包及与当前接口的差异，记录HOLD/STOP项；只选一个最小移植对象 | `compatibility-matrix`、输入/工具锁、可读差异，不做整分支覆盖 | 无重复领取；语义/输出/调用范围清楚，旧证据字节保持 |
| 2 / R2-S3：8×32 split-input迁入 | 先移植可选接口和最强RVV对照，在当前0f上同ELF测试packed与split；准备A/x、布局变换、调用与存储计时边界对称 | 新独立C接口、反汇编、真实DiffTest、配对原始窗口和重放 | 数学/完整128位/保护状态通过；共同锚点稳定；收益不来自计时外打包或更弱RVV |
| 3 / R4：外部实现复测与依赖路径归因 | 优先复用10月17固定外部源码；当前0f加入同一批控制，保持dot8输出合同，记录适配成本；重点测chain256及当前消费者 | 同基线gross表、允许的净斜率诊断表、发射→响应→写回→消费轨迹 | 外部合法域差异明确；新数据与历史分开；能判断短延迟是否值得RTL实验 |
| 4 / R2-S3：FP32→QKV有界消费者 | 若split移植有价值，选择性迁入zufan已验TA/强FR消费者；量化＋计算纳入同窗，预打包权重边界单独记录 | 当前0f的新QKV资格、普通C库、完整结果及回退；不声称token | 在当前硬件闭合正确性与同口径性能；上下文不稳则HOLD，不扩到完整forward |
| 5 / R3：条件性短延迟/时序审查 | 仅当第3步发现可解决的真实瓶颈，审查VIAlu/VIMac路径、旁路及算术级边界，最多一个候选；先局部STA和真实父级，再决定全核 | 路径归因、单一差异、原候选/0f同约束FU与父级成本表 | II、吞吐、取消、身份及共享FU不退化；面积与最差相关路径满足事前门槛，否则停止 |
| 6 / R4→T17→R5：组合验收 | 仅对获选软件/RTL组合重新绑定版本、功能/异常/性能/成本；独立成员或机器复现单独记录，保留原0f+V2+C8 | 可复现可选包、资格清单、采用/否决说明、回退入口 | 新组合真实通过才讨论默认变更；无收益可明确关闭，不为完成编号强改 |

**第一项实际开发建议：先做第1项差异清单，并以8×32 split-input作为第2项唯一候选。** 不先重跑全部旧S2，不先整体合并zufan/James，也不先开始一拍RTL重构。

### 7.1 公平测量与停止条件

沿用既有冻结合同优先；新增消费者在运行前写清样本和阈值。以下为本计划建议，不是官方赛题门槛，也不追溯修改旧实验：

- 同硬件同ELF内保留A/B和共同控制路径；输入、数据/代码布局、预热、反向执行顺序、seed和资源上限固定。旧四形状回归采用三数据集、每格12正式样本及确定性重放；新QKV另立适配输入合同。
- 报告全部样本、均值和离散度，以同口径最快合格RVV为对照；准备/量化/打包不可只替某一方移出窗口。硬件比较必须同ELF，软件比较必须同硬件。
- 建议共同锚点跨度超过1%即HOLD并定位上下文，不挑最好样本。新应用优选可预设至少3%的稳定端到端周期改善目标；未达目标但具备其他明确价值时单列取舍，不自动采用。
- 正确性、异常、身份、反压或输出高96位任一失败立即停止。固定完整调用中的回退与受保护寄存器不得弱化；不修改checker把失败变成PASS。
- RTL先明确实际关键路径、PDK/库、边界、负载、约束及工具。仿真cycles改善但STA恶化时必须同时报告；不能用arrival倒数当整核Fmax，也不能无活动率/功耗工具宣称节能。
- 同一假设只允许一次有依据的修订；无收益、控制漂移或来源不完整就归档关闭，避免无界扫参数。

### 7.2 明确不重复和不建议直接采用的方向

1. **S2强行覆盖K13：不建议。** 已有187对175.25的较强RVV探针和basic退化记录，优先保留RVV选择；需要新的真实消费者证据才能重开。
2. **再次把平衡树或低32位保存列为新优化：不成立。** 当前已经实现。
3. **删除577位perf元数据：不建议直接做。** zufan已有消费者审查并保留；两槽不同请求身份不能合并或整包清零。
4. **重跑同一carry-save或C1/C2/C3门控搜索：不建议。** carry-save在已有筛选中r2r仅改善0.8849%、面积增0.5459%、i2r退化1.9166%，STOP；C3-HF局部路径改善但未过整体成本门槛。只有新的路径/约束依据才能另立候选。[A1][B1]
5. **用Redoop dot4累加替代本题dot8或直接宣称LLM 8.2×：不允许这样比较。** 保持当前生产语义，扩展需独立编码和验证。
6. **把zufan的完整参考forward当成香山完整forward：不成立。** norm、W2、首token目标仍有HOLD或未取得目标资格；本轮不接管其活动任务。[B1]

## 8. 实施边界与本次交付

本次仅研究、阅读和制定计划。新增RTL构建、EMU/NEMU运行、综合、STA、周期样本均为0；没有复验全部封存原始日志，也没有代签人工ACK。指标来自相应固定版本的文档和已公开代码，适用边界逐项列出。本文建议的移植与新测试全部尚未执行。

变更目标仅 `zjhwork`；`zjhwork2`、`zufan`、`James_Hotten`、`main`及历史审查分支不由本次修改。推送以正常快进和预期HEAD校验进行；承载本报告的提交由Git历史和远端回读确定，不把文档提交SHA冒充受测硬件SHA。

研究记录：`20261028-cc77-public-vdot-review`，日期级；源码/文档审查完成，硬件测试NOT_RUN。路线建议是复用已验应用接口→当前0f资格→公平外部对照/依赖归因→条件RTL→组合验收；不撤销当前R5完成状态，不自动切换默认。

## 9. 来源与可追溯快照

以下是实际读取的主要材料；公开项目报告为作者陈述，本仓库数据为既有项目记录。未在本轮重跑性能。

[A1] [当前zjhwork路线，4653fd5](https://github.com/cc77-builder/riscv/blob/4653fd51a1195c8e370e11f564acbc6613f4bbd0/team/docs/development-route-current.md)。

[A2] [0f＋firstdot V2＋C8最终验收，4653fd5](https://github.com/cc77-builder/riscv/blob/4653fd51a1195c8e370e11f564acbc6613f4bbd0/team/optimizations/o2/integration/firstdot-v2-0f/acceptance/RESULT.md)。

[A3] [四项目统一复测，4653fd5](https://github.com/cc77-builder/riscv/blob/4653fd51a1195c8e370e11f564acbc6613f4bbd0/team/docs/unified-vdot-comparison-20261017.md)。

[B1] [zufan完整当前路线，ffd668b](https://github.com/cc77-builder/riscv/blob/ffd668bf1bc80850d382f514d13bb00316c85582/team/docs/development-route-current.md)，包含各split/QKV/W2/norm/carry-save原始RESULT链接。本次依据这些明确边界，不声称已对所有归档逐字节复算。

[B2] [James当前路线，e611eaf](https://github.com/cc77-builder/riscv/blob/e611eafb1af2730d8d86c768ee98f1b80f5fe0b2/team/docs/development-route-current.md)；[James同步与独立探针记录](https://github.com/cc77-builder/riscv/blob/e611eafb1af2730d8d86c768ee98f1b80f5fe0b2/team/docs/latest-integration-20261023.md)。

[B3] [10月24整合边界及旧合同问题](https://github.com/cc77-builder/riscv/blob/4653fd51a1195c8e370e11f564acbc6613f4bbd0/team/docs/branch-integration-20261024.md)；分支提交差由本轮GitHub compare接口读取，不用旧整合表代替当前SHA。

[R1] [本项目平衡归约源码](https://github.com/cc77-builder/riscv/blob/4653fd51a1195c8e370e11f564acbc6613f4bbd0/src/main/scala/xiangshan/backend/fu/vector/VDotDatapath.scala)，blob `e0703191ed2b626179e36fb40eb9741cdb843151`。

[R2] [本项目两槽源码](https://github.com/cc77-builder/riscv/blob/4653fd51a1195c8e370e11f564acbc6613f4bbd0/src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala)，blob `72d23e224bbfea13245865cc5a506ac87aed877b`。

[P1] [Jade作者结果](https://github.com/Jade0x13157A6/cie2026-xiangshan-vdot/blob/a17e38128e589d745152f3ef4b595b4572b22b3d/docs/RESULTS.md)。

[P2] [Jade实际RTL补丁](https://github.com/Jade0x13157A6/cie2026-xiangshan-vdot/blob/a17e38128e589d745152f3ef4b595b4572b22b3d/patches/03-xiangshan-vdot.patch)。

[P3] [试水作者性能口径](https://github.com/vienna-0FFH/cie2026-shishui-vdot/blob/4421d88beb39f8e95e23e25c78eaaaf1a7de4b52/vdot/docs/performance-results.md)。

[P4] [试水实际RTL补丁](https://github.com/vienna-0FFH/cie2026-shishui-vdot/blob/4421d88beb39f8e95e23e25c78eaaaf1a7de4b52/vdot/integration/patches/xiangshan-vdot.patch)。

[P5] [Redoop作者README](https://github.com/redoop/xiangshan-vdot/blob/fba90f8eb0818ed9539aa097691b371fd852f7a1/README.md)。

[P6] [Redoop流水数据通路](https://github.com/redoop/xiangshan-vdot/blob/fba90f8eb0818ed9539aa097691b371fd852f7a1/rtl/yunsuan/src/main/scala/yunsuan/vector/vectorIMAC/Vdot64b.scala)，blob `d51deb23f83a11beb0d850a3424e5ccca1032788`。

[P7] [Qixuan README](https://github.com/qixuan-cn/cie2026-qxriscv-xiangshan-vdot/blob/main/README.md)，本次blob `2c9427c14b459d62817454bc826246730f8e99b9`；[AsyncSys README](https://github.com/Sun-Yingjie/cie2026-AsyncSys-xiangshan-vdot/blob/master/README.md)，blob `62027946cdec793fce78ced1012e9cca3a1dbfbb`。这两条为活动分支链接，内容以记录blob和核查日期为准。

[P8] [mmm-arch](https://github.com/mmm-arch/cie2026-01-xiangshan-vdot/tree/b9e8a5ec103fd9e139ea2ebb9b3d5b7e5926ae25)；[SKIProject](https://github.com/juese12/cie2026-skito-SKIProject)；[try1try](https://github.com/Sleepless9/cie2026-try1try-xiangshan-vdot)；[GEMwhu](https://github.com/Gloria-Deng/cie2026-GEMwhu-XiangShan-Vector-Dot-Product-Acceleration-Engine)。扩展发现项，不用于未经核验的数值排名。
