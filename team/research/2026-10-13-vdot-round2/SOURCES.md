# 第二轮来源索引与适用边界

检索与阅读日期：2026-10-13，Asia/Shanghai。这里的 27 个编号是**来源记录，不是 27 篇全部精读的论文**。区分正文/指定章节、代码片段、摘要筛选和第一轮继承；未下载保存整篇论文，不把检索命中当成复现。优先级表示对当前八项 signed-int8、低32位结果的候选合同的帮助，不表示论文总体优劣。

## A. 最直接的规格、实现和应用证据

### S01 — 命题方入口与仍待确认的规则

[OpenXiangShan/XiangShanLab 比赛 README](https://github.com/OpenXiangShan/XiangShanLab/blob/master/2026-CIE-RISC-V-Contest-Application-Track/README.md)。本轮读取全文，返回 blob `ac95bc15ec16ee806a1c2c6cbad613ca1e1c1df4`。确认昆明湖V2题目与官方资料入口；官网细则和语义图片本轮未成功重新抓取。具体评分、截止日期、发布可见性及候选语义是否获官方认可，不能由本次调研宣布已核实。沿用第一轮待确认项，不用推测关闭它们。

### S02 — 团队候选合同与独立执行单元【P0】

固定 Fork 快照 `a978b3b8fe731dd9422a41f80d9d53e40c775656`：
[vdot.md](https://github.com/LiZufan001/riscv/blob/a978b3b8fe731dd9422a41f80d9d53e40c775656/team/spec/vdot.md)、[rtl-interface.md](https://github.com/LiZufan001/riscv/blob/a978b3b8fe731dd9422a41f80d9d53e40c775656/team/spec/rtl-interface.md)、[VdotExec.scala](https://github.com/LiZufan001/riscv/blob/a978b3b8fe731dd9422a41f80d9d53e40c775656/src/main/scala/xiangshan/backend/fu/vector/VdotExec.scala)。读取合同核心条款、接口主要章节及执行单元全文。单元 blob `6b6d7ba336674e9f4fa5635afab1534f84bb2cdc`。已有平衡树和单响应槽，不是空白项目；扩流水时须重新处理多在途身份与按年龄取消。合同仍是 draft，不能冒充官方定案。

### S03 — ggml 的真实 RISC-V 量化点积【P1】

[ggml RISC-V quants.c 固定提交](https://github.com/ggml-org/ggml/blob/3612c0af93f2cfc8f048295300a61187723b12ae/src/ggml-cpu/arch/riscv/quants.c)，blob `47e9180bf9bb4aa9efc59541b72f6246208c4936`。读取1–180、240–510行，重点 `ggml_vec_dot_q8_0_q8_0`。它按量化块完成宽乘、宽归约、整数取数，再应用该块缩放。可借鉴 block32 工作负载与端到端对照；**不能把不同缩放块的整数和直接合并后只乘一次缩放**。本轮没有编译整个 ggml，也没有复制其源码进项目；实际复用前仍需检查对应文件许可证及依赖。

### S04 — RVV 1.0 官方规范【P0】

[20260120 规范库 V 章节](https://docs.riscv.org/reference/isa/v20260120/unpriv/v-st-ext.html)。本轮阅读配置、LMUL/EMUL、尾部策略、宽化、归约和标量移动相关条款。用途：限定B5/B6/B7与长点积候选的合法域，核对EEW/SEW区别。规范不是目标实现已正确执行的证明；需要目标ISS/RTL验收。

### S05 — 正在演进的标准向量点积提案【P1/边界】

[riscv-dot-product/header.adoc](https://github.com/riscv/riscv-dot-product/blob/main/header.adoc)，本轮全文读取，blob `801674d98d1b71f8c90826fb049aef69f2eb7516`。读取版本自称 `Vector Dot-Product Extension (Zvqdotq)`、v0.0.2、Development。只据该快照描述，不断言所有后续提案的最终命名/批准状态。第一轮已讨论其分组/累加语义与本题差别；**不能因同名dot就换成本题编码或增加旧vd累加**。

### S26 — 固定版本的香山向量包装器【P0】

固定 `355756ed30bab01a6a31f48fad3cdda2be513211` 的 [VIMacU.scala](https://github.com/LiZufan001/riscv/blob/355756ed30bab01a6a31f48fad3cdda2be513211/src/main/scala/xiangshan/backend/fu/wrapper/VIMacU.scala) 与 [VecPipedFuncUnit.scala](https://github.com/LiZufan001/riscv/blob/355756ed30bab01a6a31f48fad3cdda2be513211/src/main/scala/xiangshan/backend/fu/vector/VecPipedFuncUnit.scala)，本轮全文读取；blob分别 `27eb8012e59683d61849e4d94b45a22d7673261a`、`1ff7a8c03eb829d8bec1d0c12b3d989036fb94da`。现有包装器把数据送到64位子单元，宽化时重组源，并经过Mgu；流水控制取cfg声明延迟。复用控制体系有价值，**直接拼接一个独立Decoupled模块不是已证明正确的接入方案**。

## B. 新增重点论文与开源路线

### S06 — Ten-Four【P1：算术候选；非整核模板】

Rout、Tine：[arXiv:2512.00053v2](https://arxiv.org/html/2512.00053v2)，2026-04-05版本。[PDF](https://arxiv.org/pdf/2512.00053v2)。读取微架构、整数通路与评价章节，实际查看PDF第4页结构图和第6页评价/表格。可迁移：多操作数压缩、短位宽乘法结构的实测取舍。作者在其4–11位目标中不采用Booth，不能据此宣布本项目Booth永远差。其浮点对齐、规格化、旧累加值和GPU调度不能整体照搬。第6页把一项吞吐指标按操作数/延迟计算，不能不核对II就当作稳态流水吞吐。论文链接的Vortex分支本轮未做完整源码构建。

### S07 — Saturn【P1：短向量调度】

Zhao等：[arXiv:2412.00997v1](https://arxiv.org/html/2412.00997v1)。本轮阅读短向量瓶颈、调度、依赖与流水组织相关正文。帮助把发射空泡、配置、链式执行、存储供给纳入实验。Saturn与本题香山的主核/提交边界不同，**不能搬用其提交后向量执行模式来规避香山精确异常**。本轮未构建Saturn；其独立站点访问失败，记录为资料缺口，不将其当成已检验的工具链。

### S08 — Spatz【P1：数据复用与供给】

[arXiv:2309.10137v2](https://arxiv.org/html/2309.10137v2)，阅读VRF、数据复用及dotp/矩阵算子分析；[项目README](https://github.com/pulp-platform/spatz/blob/main/README.md) 读取1–160行，blob `fc486a6f880b19d39b8a514ea958ea27caf45fc4`。点积低复用与矩阵高复用对存储端口的需求不同，不能用一种纯计算测试决定所有场景。该平台的L1 scratchpad、VLEN及Snitch宿主不同。本项目不照搬其配置。README明确软硬件目录许可证不同，不能只看仓库顶部Apache徽章就复制所有RTL。

### S09 — MXDOTP【P1/P2：操作数接口代价】

[arXiv:2505.13159v1](https://arxiv.org/html/2505.13159v1)，阅读数据通路与操作数供给章节。可迁移的是把运算、缩放和操作数端口一起优化的思考方式；它处理微缩放FP8并借助Snitch/SSR，非本题signed-int8等价实现。不要为复用它引入新SSR、浮点缩放或额外架构操作数。

### S10 — Structured-sparse RVV / vindexmac【P1：软件展开】

Titopoulos等：[arXiv:2501.10189v1](https://arxiv.org/html/2501.10189v1)。阅读软件展开与优化对比章节（II-C、IV-B）。可迁移：分别探索归约维与输出维展开，复用地址计算与操作数，观察寄存器压力；不照搬稀疏收益、新索引指令或特定最优展开倍数到密集八项点积。

### S11 — Portable RVV Performance【P1：计数器校准】

[Closer in the Gap: Towards Portable Performance on RISC-V Vector Processors, arXiv:2605.10860v2](https://arxiv.org/html/2605.10860v2)。读取测量校准章节。用途：先用已知指令/事件的微测试证明计数器含义，再解释性能。其Banana Pi/Linux计数器及容差不是香山仿真的默认标准；本项目应自行给出事件定义、采样边界与可重算记录。

### S12 — CORE-V CV32E40P packed-SIMD【P2：语义与实现筛选】

[官方手册v1.8.3扩展指令](https://docs.openhwgroup.org/projects/cv32e40p-user-manual/en/latest/instruction_set_extensions.html)。阅读SIMD点积相关条目与编码范围。专用dot和累加dot的区分值得借鉴；GPR打包、编码、宿主流水不同。尝试读取旧地址RTL未成功，故本轮**没有声称精读/验证其乘法RTL**。

### S13 — Cascade【P1：定向随机与失败缩减】

Solt、Ceesay-Seitz、Razavi：[USENIX Security 2024](https://www.usenix.org/conference/usenixsecurity24/presentation/solt)，[论文](https://www.usenix.org/system/files/usenixsecurity24-solt.pdf)。本轮阅读会议摘要并核实论文入口，未完整复现工具。可迁移的是把数据/控制依赖缠绕起来、保留可缩减失败样本；不直接宣称支持你们的自定义向量语义。先在既有测试环境生成小规模依赖程序，没必要第一天换整套fuzzer。

### S14 — RISCV-DV【P1：复用刺激组织，不盲接框架】

[CHIPS Alliance README](https://github.com/chipsalliance/riscv-dv/blob/master/README.md)，读取全文，blob `569289a9e6a90d3d73598a9ffd4b7b28d3445188`。关注随机流中插入定向指令、非法指令、CSR/异常、覆盖和多ISS比较。README列出的基础支持集不是“现成支持本题RVV custom指令”的证据；适配成本必须先评估。

### S15 — 团队锁定版本的 DiffTest【P0】

[README @62e4540](https://github.com/OpenXiangShan/difftest/blob/62e4540c03c03aa947bdb67f4b6bf66f1a29c5d0/README.md)，读取1–160行，blob `829408a4b8e9a79491d606950fd60f3f7b6393f0`。向量状态和向量CSR接口是可选项；**框架存在这些接口，不证明你们的构建已启用且完整比较**。继续做高位负控和真实退休观测。新主线依赖版本变化不能直接混入旧昆明湖基线。

### S16 — Snitch / SSR / FREP【筛选】

[arXiv:2002.10143](https://arxiv.org/abs/2002.10143)。本轮摘要筛选。控制与数据搬运开销值得研究，但tiny in-order/流寄存器/FPU组合不是香山可直接采用的接口；不为单条vdot添加完整SSR/FREP子系统。

### S17 — Sparq【筛选，不进入首版】

[arXiv:2306.09905](https://arxiv.org/abs/2306.09905)。本轮摘要筛选：子字节量化、自定义运算和Ara背景有参考价值；额外精度/格式会扩大语义、软件和验证矩阵，不放入当前signed-int8正确性闭环。

### S18 — ExSdotp / MiniFloat-NN【筛选】

[arXiv:2207.03192](https://arxiv.org/abs/2207.03192)。本轮摘要筛选。借鉴融合思想，不能把浮点中间舍入误差的收益套到本题精确整数求和上。

## C. 第一轮继承，不重复算作新增精读

### S19 — Nanhu-vdot / Ara2 / XpulpNN

见[第一轮来源记录](../2026-10-12-vdot-review/SOURCES.md)：[Nanhu-vdot](https://arxiv.org/abs/2409.00661)、[Ara2](https://arxiv.org/abs/2311.07493)、[XpulpNN DATE论文](https://past.date-conference.com/proceedings-archive/2020/pdf/0650.pdf)。本轮继承已记录的阅读边界和问题，不声称重新完整阅读。Nanhu寄存器合同不同；Ara2提示短向量供给瓶颈；XpulpNN的共享选择逻辑代价与本轮“先测后选”一致。

### S20 — 量化正确性背景

[Jacob等整数推理](https://arxiv.org/abs/1712.05877)、[SmoothQuant](https://proceedings.mlr.press/v202/xiao23c.html)。继承第一轮资料范围。本轮新增加的应用证据是S03的真实代码，而非宣称已完成LLM准确率测试。

## D. 协作工具的真实能力边界

### S21 — Git push【机制】

[官方文档](https://git-scm.com/docs/git-push)。阅读快进、non-fast-forward及force相关规则。普通push保护提交祖先关系，不理解任务负责人/模块锁；本轮临时仓库实验实际演示这种区别。共享分支禁止以force解决并发冲突。

### S22 — Git worktree【隔离】

[官方文档](https://git-scm.com/docs/git-worktree)。阅读独立工作树、分支签出限制与detach。独立检出固定SHA适合评审/构建；**worktree lock不是远端多人分支互斥锁**。涉及子模块与构建目录时仍要检验实际工具兼容性。

### S23 — GitHub assignees【责任展示】

[官方文档](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/assigning-issues-and-pull-requests-to-other-github-users)。负责人字段适合表达责任，不代表“现在正在执行”，也没有提供跨fork互斥保证。

### S24 — GitHub Projects【可选看板】

[官方文档](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)。读取字段/视图及与Issues、PR的同步说明。可用作同一任务记录的视图；不要再独立维护一份冲突的进度表。三人小队初期可不启用Projects。

### S25 — CODEOWNERS【评审路由】

[官方文档](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)。读取分支、PR base、fork及保护条件。它路由评审，不阻止两个人开始改同一模块；私有仓库/保护功能还受方案和权限限制。本轮只给建议，不修改实际权限策略。

### S27 — 本轮 Git 对照实验【自有证据】

[check_git_handoff.py](experiments/check_git_handoff.py) 与 [git-handoff.json](evidence/git-handoff.json)。在临时bare仓库和独立clone中验证并发push、显式交接、固定SHA评审及双fork独立授权。它证明/反驳的是这些协议假设，不是团队已经采用的实际工作流程，也不构成生产级分布式锁。

## 检索结论与未覆盖项

新增重点放在短向量调度、整数算术组织、操作数供给、真实量化内核、测量校准和协作机制。GPU混合精度、SSR、稀疏化和子字节扩展是筛选面，不等于建议一起实现。没有声称穷尽全部文献；官网细则抓取、部分项目源码、各论文完整构建/PPA复现仍有缺口。下一次检索应由目标测量暴露的瓶颈驱动，避免继续堆积与当前关键路径无关的文献。
