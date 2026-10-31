> 最新追加：2026-10-27，第26条为8×32配置复用普通C调用验证；无新性能窗口，旧25条全部保留。详见文末第16节。

> 最新追加：2026-10-27，第25条为4尺寸×3数据集的新配置复用矩阵；第24条仍是历史8×32/d0探针，全部旧数据保留。详见文末第15节。

> 最新追加：当前 JSON 已有 **24 条记录**。第 13 节为同机干净复现（25 应用装载字节、768 窗口、96 C 输出一致，保留全核宿主时间限制）；第 14 节为配置复用 8×32/d0 筛选（273 cycles，候选保留，未切默认）。以下原导言中的“22条”“干净复现未完成”等措辞是第22条写入时的历史状态，原文保留。

# 香山 vdot 各版本运行数据档案

更新：2026-10-27（UTC+08:00）。本文件保存版本身份、测量口径、实测数据和采用依据；后续每版继续追加。原始实验合同和封存证据是最终依据。它不维护待办顺序；当前开发安排仍看 [开发路线](development-route-current.md)，执行过程仍记 [开发计分板](../../开发计分板.md)。

历史部分只读取已有成果，未重跑旧版本或补授资格。当前保留的生产实现是 **O2＋H1＋DIV 取消关钟修复 0f12df6**。C1、C2 已否决。C3-G0 的只读建议保留在第 10 节；随后实施的 **C3-HF 单次最小试验也已否决**：局部验证通过，面积 +0.184115% 超限，五档路径 20/45 通过、25/45 失败。三控制 D 最差虽下降 16.617459%，仍未通过完整合同。第 11 节追加本轮真实结果，旧记录保留各自当时状态。C3-HF 的新全核/NEMU、周期、功耗和整核 Fmax 均 NOT_TESTED；当前门控试验关闭，0f 与原 EMU 不变。

配套机器可读索引：[version-data-ledger.json](version-data-ledger.json)。索引含完整硬件/EMU 身份、22 条工程记录（第20条为评审/抽象控制，第21条为 C3-HF 真实局部及成本试验，第22条为当前 0f＋firstdot V2 的功能/周期组合资格）、原表文本、指定原 CSV/JSON 和输入 SHA-256。只列出历史执行实际支持的结果；未执行的层级写 NOT_TESTED，而不是 0。

第 12 节追加 firstdot V2 的当前组合实测：功能与 DUT 周期原文审计通过，严格墙钟时间线 FAIL 单独保留。硬件仍是 0f；源码已本地固定为 c823a878，干净复现尚未完成，配置复用与新面积/STA 仍为 NOT_TESTED。

## 1. 如何比较这些数字

- **同一 comparison/run ID 内才按原合同比较。** T14 原消融的 batch128 为 464 cycles；后续统一镜像中的 T14 为 453.25 cycles。两者镜像、观察器/构建及统计合同不同，不可拼接成连续硬件收益。
- **FU 拍数、全核窗口 cycles、面积和 STA 分开。** II=1 不等于应用每点积 1 cycle；同镜像周期不退化不意味着频率不退化。
- 加速比保留分母。微基准通常使用同版实测 RVV/vdot；硬件消融使用旧 vdot/新 vdot。S1/R4 使用同合同中最快合格 RVV，不拿较慢基线抬高比值。
- 确定性重放证明可复现，不增加独立样本。正式窗口之外的 first/warmup、失败、中断、负控和恢复仍保留。
- 综合面积是参考库单元 area 之和；STA 为布局前参考约束。所有硬件版本的实际整核 Fmax、布局布线和活动率功耗均 NOT_TESTED。本档案不推算比赛得分。

## 2. 版本与证据层级

PASS 仅适用于表中原合同和身份。“周期”指该版是否有已完成的相关真实测量，不表示任何工作负载均获益。

| 版本/工作 | 主要变化或用途 | 真实 FU/父级 | 全核/NEMU | 周期 | 面积/STA | 已有决定 |
| --- | --- | --- | --- | --- | --- | --- |
| T13 原基线 | 单请求、3 拍响应、II4 | 原阶段资格 | PASS | PASS | NOT_TESTED | 冻结对照 |
| T14 | 输入拍保存乘积，2 拍响应、II3 | PASS | PASS | PASS | 本轮 NOT_TESTED | 后续基础 |
| T15 | 独立 INT16×8、64 位结果 | 独立算术/实验包装 PASS；父级 NOT_TESTED | INT16 NOT_TESTED | 全核 NOT_TESTED | NOT_TESTED | 参数扩展证据 |
| O1 | vdot 同拍响应/再接受，II2 | PASS | PASS | PASS | O4 有限定结果 | 冻结对照/回退 |
| O2/B0 | 两槽弹性 FU，II1 | PASS | PASS | PASS | O4 有限定结果 | 后续主线基点 |
| O3 | O1/O2 GEMV 测量，非新 RTL 版 | 复用固定硬件 | 应用 PASS | PASS | 本轮 NOT_TESTED | 识别应用收益有限 |
| O4 | O1/O2 成本评估，非新 RTL 版 | 不重新仿真 | 不重新运行 | 只引用既有值 | 报告有效，1 ns 未收敛 | 保留取舍 |
| H1 | R 槽结果 128→32 位 | 原合同 PASS | PASS | 96 对窗口不变 | FU 少 2.33386% | 保留；后来发现 DIV 关钟缺项 |
| 合并 H1 | 6d2/1a23 硬件，新夹具回归 | 不转授新局部资格 | MERGE-REG PASS | S1/S2/R4 各自测量 | 本身份 NOT_TESTED | 软件实验固定硬件 |
| S1 软件 | 向量累加及对等 RVV 优化 | 无新硬件 | 应用 PASS | 固定布局 v2 PASS | NOT_TESTED | 三种整块尺寸采用；K13 vdot 不采用 |
| S2 软件 | 安全尾部 | 无新硬件 | 应用 PASS | 固定布局和强 RVV 探针 PASS | NOT_TESTED | 未胜较快 RVV，不扩大采用 |
| R4 入口 | 普通 RV64 C ABI GEMV 函数 | 无新硬件 | 普通 C/应用 PASS | 新调用窗 PASS | NOT_TESTED | 按形状选择 vdot/RVV |
| DIV-fix0f | 取消后停止多余 DIV 时钟 | 新严格门禁 PASS | PASS | 96 对窗口不变 | 父级面积小降，部分时序退化 | 当前保留 |
| C1 | busy＋owner 替代双 hold | PASS | NOT_TESTED | NOT_TESTED | 15/45 筛选失败 | REJECT，不采用 |
| C2 只读归因 | 固定端点/缓冲扇出分析 | 未运行新仿真 | NOT_TESTED | NOT_TESTED | 2 次补充 STA | 支持先证明新假设 |
| C2-G0 | 空闲必 ready 的控制证明 | 控制抽象 PASS；非 RTL 仿真 | NOT_TESTED | NOT_TESTED | NOT_TESTED | 可进入 C2 设计 |
| C2 本轮 | busy/owner＋门控启动去 ready 依赖，真实接收协议保留 | PASS（含 SQRT/双 lane 增补） | NOT_TESTED | NOT_TESTED | NOT_TESTED | 局部通过，未采用；下一步成本筛选 |
| C2-cost 新轮 | 相同 C2 的独立成本筛选，旧局部记录保持 | 引用旧局部资格，本轮未重跑 | NOT_TESTED | NOT_TESTED | 20/45 通过，25/45 超限 | REJECT，保留 0f |
| C3-G0 评审 | 提出只改 FP DIV/SQRT hold 置位的 C3-HF；尚无新 RTL | 抽象控制 PASS；真实 FU/父级 NOT_TESTED | NOT_TESTED | NOT_TESTED | 仅引用历史值 | 建议至多一次试验，未实施/未采用 |
| C3-HF 实测 | 仅 FP DIV/SQRT hold 置位去 ready 依赖；保留双 hold 和原 ICG 公式 | PASS（本轮新 FU、父级、补充及观察） | NOT_TESTED | NOT_TESTED | 面积超限；20/45 通过、25/45 失败 | REJECT，保留 0f，关闭当前门控试验 |

O0 是吞吐观察/分析工具及证据入口，R0 是固定输入/复现前提，R1/R3 只读审查不是新的跑分硬件。它们按所支持的具体实验记录归档，不另造“优化后的数字”。H1 的原 PASS 不掩盖后续新严格关钟门禁 FAIL；修复和失败证据均见 DIV-fix0f。

## 3. 同镜像微基准数据

### 3.1 T14 原消融合同

[原结果及全部 13 场景](t14-optimization.md)；[合同](../spec/t14-ablation.md)。逐 dataset 先取正式轮次中位数，配对比值另行取中位数。以下是几个代表值，完整表保留在 JSON 的 t14/source_tables 中。

| 场景 | 基础 vdot cycles | T14 vdot cycles | 配对硬件加速比 |
| --- | ---: | ---: | ---: |
| 单次 | 72.5 | 71 | 1.0211× |
| chain256 | 2114 | 1857 | 1.1384× |
| batch128 | 599.5 | 464 | 1.2906× |
| stream64 | 1126 | 1125.5 | 1.0009× |
| generic64（含 CSR 管理） | 428.5 | 274.5 | 1.5701× |

这组是旧硬件/新硬件消融，不是后面各轮 RVV/vdot 比值。generic64 较大比值不能推广成纯算术或应用收益。

### 3.2 T14/O1：2026-10-18 新同镜像比较

[结果和身份](../optimizations/o1/performance/README.md)。36 次主运行、478 校验窗、192 正式窗；16 份 ELF/BIN 相同。正式均值 cycles：

| 场景 | T14 | O1 | O1 周期减少 | O1 实测 RVV/vdot |
| --- | ---: | ---: | ---: | ---: |
| single | 71 | 71 | 0% | 1.201× |
| chain256 | 1857 | 1857 | 0% | 2.930× |
| batch128 | 453.25 | 362.5 | 20.02% | 1.870× |
| stream64 | 1127.5 | 1127.5 | 0% | 1.005× |

### 3.3 O1/O2：2026-10-19 新同镜像比较

[结果和身份](../optimizations/o2/performance/README.md)。O1 在相同硬件输入下重新构建，O2 复用已验收 G3 固定 EMU，工作负载两版实际新跑。36 次、478 校验窗、192 正式窗。

| 场景 | 本轮 O1 | 本轮 O2 | O2 周期减少 | O2 实测 RVV/vdot |
| --- | ---: | ---: | ---: | ---: |
| single | 71 | 71 | 0% | 1.201× |
| chain256 | 1857 | 1857 | 0% | 2.930× |
| batch128 | 362.5 | 221 | 39.03% | 3.068× |
| stream64 | 1127.5 | 1127.5 | 0% | 1.005× |

### 3.4 B0/H1 与 H1/DIV-fix0f：两轮独立不退化检查

[B0/H1](../optimizations/o2/result-width/h1/performance/B0_H1_RESULT.md) 与 [H1/DIV-fix0f](../optimizations/o2/r3-div-gate/PERFORMANCE_COST_RESULT.md) 分属两轮新运行，各有 36 次 EMU、478 校验窗、192 正式窗、96 对逐窗比较。两轮均为逐对差值 0，不能合成一次四版本同步实验。

| 场景 | B0/H1 各自 vdot 均值 | H1/fix0f 各自 vdot 均值 | 每轮各版实测 RVV 均值 | fix0f RVV/vdot |
| --- | ---: | ---: | ---: | ---: |
| single | 71 | 71 | 85.25 | 1.200704× |
| chain256 | 1857 | 1857 | 5440.5 | 2.929725× |
| batch128 | 221 | 221 | 678 | 3.067873× |
| stream64 | 1127.5 | 1127.5 | 1133 | 1.004878× |

H1 减少存储，DIV 修复取消后的多余时钟；这两轮没有新增 cycles 加速收益。C1 和 C2-G0 没有全核周期成绩。

### 3.5 四项目统一测试：同一旧合同，单独存档

[完整比较与限制](unified-vdot-comparison-20261017.md)；[固定条件与公开源码身份](../workloads/unified-vdot/README.md)。本机实际运行64个全核镜像，384个正式窗口。每格为“自定义窗口平均 cycles / 该实现实测 RVV÷自定义”。这里只比较当时的 T14、Jade、试水、Redoop dot8 适配，不把后来 O2/C2 插入此表作为当前排名。

| 实现 | single1 | chain256 | batch128（四路×32） | stream64 |
| --- | ---: | ---: | ---: | ---: |
| 本项目 T14 | 71 / 1.201× | 1857 / 2.930× | 453.25 / 1.496× | 1127.5 / 1.005× |
| Jade | 70 / 1.218× | 1601.25 / 3.398× | 260.25 / 2.605× | 1126.25 / 1.006× |
| 试水 | 71 / 1.201× | 1857 / 2.930× | 292 / 2.322× | 1127.5 / 1.005× |
| Redoop（dot8 适配） | 90.25 / 0.953× | 3673 / 1.481× | 744.75 / 0.929× | 1155.5 / 0.981× |

Redoop 原生工作不同，表中已计入完成共同 dot8/full128 的软件适配；窗口外辅助代码并非逐字节相同。这里没有统一 PPA、真实频率或官方排名结论。

## 4. 应用数据按合同保存

### 4.1 O3：O1/O2，reuse/endtoend

[O3 合同和原始比较](../workloads/o3-gemv/README.md)。四尺寸、三数据集、basic/reuse、core/endtoend 全矩阵 768 正式窗；下表只是明确标注的 reuse/endtoend 切片，全部 comparison.csv 已纳入机器索引。

| GEMV | O1 vdot cycles | O2 vdot cycles | O2 周期减少 | O2 对较快 RVV |
| --- | ---: | ---: | ---: | ---: |
| 4×8 | 166.5 | 164 | 1.50% | 1.160× |
| 8×32 | 323.5 | 321.5 | 0.62% | 1.035× |
| 16×64 | 856.75 | 847.75 | 1.05% | 1.054× |
| 4×13 | 212 | 209.5 | 1.18% | 0.907× |

### 4.2 S1：合并 H1 硬件、固定布局 v2

[S1 全表](../optimizations/o2/r2-vector-accum/VALIDATION.md)。57 次主批、768 正式窗；另 4 次小尺寸重放不新增正式样本。下表均为 reuse/endtoend。

| GEMV | S0 vdot | S1 vdot | S1 周期减少 | 同合同最快 RVV | RVV/S1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4×8 | 164.5 | 155 | 5.7751% | 175 | 1.129032× |
| 8×32 | 318 | 278.25 | 12.5000% | 289 | 1.038634× |
| 16×64 | 846.5 | 701.25 | 17.1589% | 768.25 | 1.095544× |
| 4×13 | 210 | 212.75 | −1.3095% | 175 | 0.822562× |

S1 v1 布局改变 caller/加载地址，性能不进入采用统计，历史输出保留。禁止拿 v1 或旧 O3 均值替代 v2 的实际 S0 分母。

### 4.3 S2：固定布局主批与强 RVV 探针分别记录

[S2 结果](../optimizations/o2/r2-safe-tail/FIXED_RESULT.md)。主批 31 进程/384 正式窗；探针 5 进程/32 正式窗，探针仅 dataset0，不能冒称全 12 样本强 RVV 资格。

| 比较范围 | S0 vdot | S2 vdot | RVV / 解释 |
| --- | ---: | ---: | --- |
| K13 basic/endtoend，主批 | 246.25 | 298.25 | vdot 退化 21.117% |
| K13 reuse/endtoend，主批 | 210 | 187 | vdot 减少 10.952%；原 RVV 190/190.25 |
| K13 reuse/endtoend，dataset0 强 RVV 探针 | 不混入主批 | 187 | 较快 RVV 175.25；S2 慢 6.705% |
| 16×64 reuse/endtoend，主批 | 845.25 | 845.25 | 整 BIN 和窗口不变 |

旧 S2 K13 −10.621% 有布局混杂，仅保留为历史观察；固定布局重测的 −10.952% 是另一合同。当前未扩大 S2 采用。

### 4.4 R4：真实函数调用窗

[R4 原表及普通 C 验证](../optimizations/o2/r2-select/ENTRY_RESULT.md)。窗口包括参数传递、jal、完整叶函数和 ret。性能 33 进程/384 正式窗；另 3 个普通 C 进程验证 16 公共函数、48 不同 case、96 次正常调用。

| GEMV | S0 reuse vdot | S1 reuse vdot | 最快合格 RVV | 本合同选择 |
| --- | ---: | ---: | ---: | --- |
| 4×8 | 178.5 | 169.75 | 187.5 | S1 vdot |
| 8×32 | 335.5 | 292.5 | 300.75 | S1 vdot |
| 16×64 | 860 | 717.25 | 779.5 | S1 vdot |
| 4×13 | 219.25 | 219.75 | 187 | S1 RVV |

旧直线内核与新调用窗不能相减后宣称“纯 ABI 开销”；它们没有构成只改变调用的独立实验。S1/S2/R4 软件资格也不能直接转授到后来 C1/C2 新硬件。

## 5. 成本档案

下表每个值均有原独立实验，比较边界保持完整生产 FU/真实 VFEX4。O4→H1→fix0f→C1 的相邻配对按对应合同核验；没有把所有版本在本次重新综合。

| 版本 | FU 单元面积和 μm² | VFEX4 父级单元面积和 μm² | FU DFF | 父级 DFF | 数据来源 |
| --- | ---: | ---: | ---: | ---: | --- |
| O1 | 12525.142 | 281750.392 | 1048 | 16675 | O4 |
| O2/B0 | 17711.610 | 285271.700 | 1838 | 17267 | O4 |
| H1 | 17298.246 | 284879.882 | 1742 | 17171 | H1 实测 |
| DIV-fix0f | 17298.246 | 284614.946 | 1742 | 17172 | 修复后实测 |
| C1 | 复用固定相同 FU，未重测 | 284587.548 | 复用 1742 | 17171 | C1 父级实测，筛选否决 |
| C2 | NOT_TESTED | NOT_TESTED | NOT_TESTED | NOT_TESTED | 待独立成本任务 |
| C2-cost 新轮 | 复用固定相同 FU，未重测 | 284496.310 | 复用 1742 | 17170 | 新父级实测，25/45 筛选失败；见第 9 节 |

H1 实际净减少 FU 2.33386%、父级 0.137349%；并非此前局部估计的 3.0277%/0.1879%。fix0f 父级面积少 0.092999%，但映射 DFF 多 1，来自原整数 DIV 保留/裁剪差异。C1 少 1 个 DFF，父级面积只少 0.009626%，不能把面积收益完全归因于单个 DFF。

共同参考条件：Yosys0.9/ABC1.01/OpenSTA2.0.17；Nangate45 typical 25°C/1.1V；库 SHA-256 为 8d540a4d4cf6d09d27c87ad067857a9c0c2eeb023ab7a56e058cd3113db4e9b1；ABC 1000ps、BUF_X1、5fF；STA ideal clock、5K wire-load、uncertainty/transition 0.05ns、IO delay 0.1ns、父级 TE=0。五档为 nominal 1ns/5fF、0.5ns/5fF、2ns/5fF、1ns/1fF、1ns/20fF，均非布局后签核。

### 5.1 nominal 路径到达时间（ns）

这是每类查询最坏路径，起止点可能改变；完整端点/slack/五档原表在各来源文件及 JSON 中。不得把 arrival 倒数当整核 Fmax。

| 路径 | O1/O4 | O2/O4 | H1 | DIV-fix0f | C1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| FU r2r | 1.154101 | 1.152729 | 1.163404 | 1.163404 | 复用 FU，未重测 |
| FU i2r | 1.186674 | 1.219926 | 1.190323 | 1.190323 | 复用 FU，未重测 |
| 父级 r2r | 3.219300 | 3.191926 | 3.166914 | 3.261218 | 3.235859 |
| 父级 i2r | 3.298250 | 3.245332 | 3.194971 | 3.314103 | 3.301439 |
| 父级 ready | 0.339943 | 0.274544 | 0.295424 | 0.247821 | 0.266115 |
| VDot r2r | 1.337530 | 1.321661 | 1.345889 | 1.356106 | 1.402385 |
| VDot i2r | 1.516260 | 1.540559 | 1.511395 | 1.474949 | 1.479503 |
| VDot r2o | 3.174139 | 2.807015 | 2.832115 | 2.776701 | 2.677773 |
| 父级全部 gate-enable 最坏 | 1.785938 | 1.915197 | 1.855397 | 1.888362 | 见各 ICG，不混查询 |

H1 在 20fF 的 ready 为 0.413792ns，对照 B0 0.324555ns，退化 89.237ps；不能只保留 nominal 或有利档位。两版 ready 仍有正 slack，但整体参考 1ns 均未收敛。

来源：[O4](../optimizations/o4/O4结构与时序评估.md)、[H1](../optimizations/o2/result-width/h1/H1_RESULT.md)、[fix0f](../optimizations/o2/r3-div-gate/PERFORMANCE_COST_RESULT.md)、[C1](../optimizations/o2/r3-div-gate/c1/RESULT.md)。

### 5.2 C1 及只读归因的专项数据

| nominal 查询 | fix0f | C1 | 结论 |
| --- | ---: | ---: | --- |
| 控制状态最差 D | 1.930584 | 0.798315 | 改善 58.649% |
| 整数 DIV ICG.E | 1.128021 | 1.727299 | 退化 53.126% |
| 浮点 DIV ICG.E | 1.888362 | 1.901547 | 退化 0.698% |
| VDot ICG.E | 0.873228 | 0.808116 | 改善 |
| 固定 lane4→同结果位 | 1.356106 | 1.401305 | 退化 45.199ps |
| 固定 lane6→同结果位 | 1.355025 | 1.402385 | 退化 47.360ps |

C1 五档的 VDot r2r、ready、整数 DIV ICG 共 15/45 项超容限，因此否决。只读归因新增两次 STA、20 查询：19 个有效路径，1 个 owner/Q 无路径；实际整数门控分支从 QN 出发，不能把无路径记 0ns。整数最坏门控路径 BUF 从 8→19 个，缓冲弧延迟合计 0.595722→1.366627ns。见 [归因报告](../optimizations/o2/r3-div-gate/c2-attribution/RESULT.md)。

## 6. 功能和扩展数据不能冒充跑分

| 版本/层级 | 已有数据 | 解释边界 |
| --- | --- | --- |
| T05/生产 INT8 数学与算术 | 22 定向＋10000 固定随机，完整 128 位结果 | 同一集合多层重跑不能累加唯一 case |
| T15 s8x8/r32 | 10022 数值；65572 协议拍；2 拍响应/II3 | 独立 ParamPipe |
| T15 s16x8/r64 | 94＋10000=10094 数值；65968 协议拍；2 拍响应/II3 | 35 位精确累加、低64位结果；生产全核 INT16 未接入 |
| H1 父级 | 34356 拍；9类切换；FU4＋父级16负控 | 原合同；不能替代后加严格关钟门禁 |
| DIV-fix0f 父级 | 35075 拍13组；48取消空闲窗/144采样0多余脉冲；28ROB定向；12DIV复位 | 真实 VIDiv/VFDiv/ClockGate；旧 H1 在新严格门禁实际拒绝 |
| fix0f 全核 | 13正常＋1bit100负控；117唯一case/124执行；5378 vdot提交 | 未新增运行期全核 reset |
| C1 | 状态4可达/1920转移；真实父级与 fix0f 日志字节相同 | 原浮点动态刺激为 DIV，没有 SQRT 动态资格 |
| C2-G0 | 主抽象48状态/33600转移；ROB65536项；5变异检出 | 有效初始化/正常接口下控制证明，不是新 RTL 数值仿真 |

C2-G0 的真实异步 reset 与同步测试夹具 bootstrap 条件分别记录，涵盖取消、浮点双 lane、SQRT 控制。详见 [G0 原结论](../optimizations/o2/r3-div-gate/c2-g0/RESULT.md)。无有效初始化的环境反例、所有故意破坏控制关系的反例均保留。

### 6.1 C2-local-20261025-01：本轮真实局部验证

候选提交 **6704ce3502a7235cdb81697638c01ed23f6914f6**，生产修改仅 ExeUnit.scala，文件 SHA256 为 febbce48c4865ac5e1c7909f8494599a01ae2fee643ee53396635a0f403323a6。候选在独立检出中组合 busy/owner 保持与不依赖 ready 的门控启动；对照仍为获保留的 fix0f。真实 parent.ready、child.valid、实际接收、ROB 捕获和响应协议保留。

| 本轮层级 | 实际数据/状态 |
| --- | --- |
| FU 完整结果与控制 | PASS；10022 向量、31499 拍；23311 接受、22460 响应、739 取消、112 复位丢弃；4 项观测故障负控全部检出 |
| 原真实父级矩阵 | PASS；35075 拍、13 组；13611 接受、13122 响应、426 取消、63 复位丢弃；16 项观测故障负控检出 |
| 原严格取消关钟 | 48 空闲窗口/144 采样，额外时钟脉冲 0；原父级日志与 fix0f/C1 固定日志 SHA 相同 |
| 新真实父级增补 | PASS；2959 拍、6 组，实际 SQRT、取消、ROB、切换、TE=0 动态复位 |
| SQRT 定向与控制 | 15 正常 SQRT、48 取消、14 ROB 定向、18 切换；这些覆盖标签有交集，不求和成唯一 case |
| 双 lane 实际不同步 | 两种方向分别 56/27 拍；不同步时取消各 6 例，均来自真实内部观测 |
| 空闲/复位增补 | 620 次空闲 ready 检查；20 个 TE=0 复位场景；162 次取消后即时空闲采样 |
| 增补负控 | 7 项离线观测变异全部检出；不是 RTL 故障注入 |
| 源码及生成控制结构 | 独立审查 PASS；两处 DIV 门控启动的生成控制锥去除 ready 依赖；旧 C1 被同检查器按预期拒绝 |
| 新全核/NEMU、同镜像 cycles、面积/STA、功耗、Fmax | NOT_TESTED |

本轮只能作 **LOCAL_VALIDATION_PASS_NOT_ADOPTED**：尚未采用 C2，也没有新的加速比或时序改善结论。下一步相对 fix0f 做同约束父级面积与五档 STA 筛选，通过后再进入新全核回归。完整结果见 [C2 结果](../optimizations/o2/r3-div-gate/c2/RESULT.md)，不可变证据入口为 [C2 manifest](../optimizations/o2/r3-div-gate/c2/evidence/20261025-local/manifest.json)。manifest 的最终 SHA 由本轮封存后补入配套 JSON；实际本地来源已逐项固定。

## 7. 完整身份索引

构建提交不等于后来文档提交；未提交候选必须同时记基点、patch 和逐源 SHA。完整身份见配套 JSON hardware_identities；下表便于定位。

| 记录 | 硬件/实际源码身份 | EMU SHA-256 前缀 |
| --- | --- | --- |
| T13 | 4460300e9557ad20ac152fa67b1827c5d62802dd | 9903d6d8b3d59bed |
| T14 原构建 | 2443fb1c101dfc5974ac208275a8b86d68a11e0f | 60521f406816846f |
| T14/O1 的 T14 | 72fc206a417e5781dded45433eae0de45f181458；继续编译2dee53fc | 081247df2c8220a3 |
| 原 O1 | 18c0ce08a40e889654bfe76d5435f272854ad7d0 | b13b05a3b03d2dd1 |
| G4 新 O1 | a239dace720b32216e83fb5a514930d334c69a26 | 6699225b76ceae47 |
| O2/B0 | b218cbc6e6b135e4ff219a902a9284a59d3c82c9 | ac0123280bf6c742 |
| H1 全核 | 8b5024fcbd96986871cc40ce8c9fb71a67c495eb | e37b3c267cae2903 |
| 合并 H1（S1/S2/R4） | 6d2abe403b07c297b8830a7d4f06e370b0a8e070 | 1a23dbab5f919da0 |
| DIV-fix0f | 0f12df675378556670afd0dd2153f47fcb330610 | 2d1db77cc407486a |
| C1 | 3be0e3d9e500bd1aa772bcc8d4f8b023a2877c66 | NOT_TESTED |
| T15 独立 | 65f6159e305adc10b4f8bd67812f3a6460ccf360 | NOT_TESTED |
| C2-G0 | 审查 fix0f，未生成新硬件 | NOT_TESTED |
| C2 | 6704ce3502a7235cdb81697638c01ed23f6914f6 | NOT_TESTED |
| C3-HF | 77d0a1228f0da7d584d5c7375b404dcda9763cf3 | NOT_TESTED |

H1 成本轮实际身份是 9b6cf074 基点＋h1-production.patch＋candidate-inputs.json 的逐文件 SHA；不能把后来 H1 全核提交冒充较早未提交局部试验的构建来源。运行工具、参考 NEMU、flash、镜像、依赖、库及工具链另在每轮 manifest 中绑定。本档案固定这些来源文档/清单的 SHA，未声称已再次检查全部外置大二进制。

## 8. 后续每一版如何追加

1. **实验启动前**给新候选和比较分配永久 ID，例如 C2-local-20261025-01、C2-cost-日期-01、C2-core-日期-01；先存合同、基线身份、源码/patch哈希、配置和门槛。只完成局部验证就只记局部资格。
2. **每次真实运行**用新输出目录，保存命令、开始结束时间和时区、真实退出码、输入/工具/构建身份、原始 stdout/stderr、生成物清单；长期大二进制可以外置，但必须存大小、SHA及恢复来源。
3. **每次结论形成**新增 JSON record，不覆盖旧 record；本 Markdown 新增对应小节或表行，指向合同和不可变 evidence/manifest。相同候选的后续层级可以新增子 run 记录，并保留前一轮“当时未测”的时间边界。
4. **所有周期结果**保存逐窗口 CSV/JSON，包含 dataset、repeat、seq、phase、method、实际工作量、cycles、退休指令、镜像 SHA 和硬件身份。清楚写均值/中位数/配对比值，first/warmup/replay 不悄悄删掉。
5. **所有成本结果**保存完整层级边界、生成源/网表、工具/库 SHA、综合命令和 STA 约束；五档和所有原规定路径都保留。NO_PATH、FAIL、REJECT、NOT_TESTED 不能换成 0 或空格；保留起止点/slack。
6. **失败/否决照样存档。** 源码改了、检查器修了、布局改了，必须新身份/新 run；原错误记录不能覆盖成 PASS。取舍由既定合同判断，不能只挑最优一轮。
7. **发布前**核验 manifest、原始数据到汇总的复算和文档链接；跨 Windows/WSL 复制要逐文件比哈希。用户未授权推送时仅本地保存。计分板只加工程摘要和档案链接，不复制整套数据表。

新记录模板（也在 JSON 的 record_template 中保留）：

~~~json
{
  "record_id": "C2-cost-YYYYMMDD-01",
  "candidate": "C2",
  "baseline": "DIV-fix0f",
  "scope": "real-parent / FU / fullcore / application",
  "source_commit": "40 hex or NOT_TESTED",
  "source_snapshot_manifest_sha256": "64 hex or NOT_TESTED",
  "contract_path": "team/optimizations/.../CONTRACT.md",
  "contract_sha256": "64 hex",
  "configuration": {},
  "input_identities": {
    "emu_sha256": "NOT_TESTED",
    "nemu_sha256": "NOT_TESTED",
    "images_manifest_sha256": "NOT_TESTED",
    "toolchain_manifest_sha256": "NOT_TESTED",
    "library_sha256": "NOT_TESTED"
  },
  "execution": {
    "started_at": "ISO8601 with UTC offset",
    "finished_at": "ISO8601 with UTC offset",
    "commands_path": "evidence/.../commands.json",
    "exit_codes": [],
    "new_runs": 0,
    "reused_runs": 0
  },
  "verification": {
    "fu": "NOT_TESTED",
    "real_parent": "NOT_TESTED",
    "fullcore_difftest": "NOT_TESTED",
    "cycles": "NOT_TESTED",
    "area_sta": "NOT_TESTED",
    "power": "NOT_TESTED"
  },
  "statistics": {
    "aggregation": "mean / median / paired median / raw",
    "measured_windows": 0,
    "replay_windows": 0,
    "samples_path": "NOT_TESTED"
  },
  "metrics": [],
  "decision": "NOT_TESTED",
  "limitations": [],
  "evidence_manifest": "path + SHA256"
}
~~~

上述 0 是空模板中的计数占位，不是候选测量值；实际数据记录中的未测指标一律使用 NOT_TESTED。不要为了“填满每版”重复启动已完成的实验，也不要将旧版 PASS 自动继承给新候选。

## 9. C2-cost-20261025-01：同约束真实父级成本筛选

这是 C2-local 后新增的独立成本记录；旧轮当时的面积/STA、全核和周期 NOT_TESTED 保留。

候选 6704ce3502a7235cdb81697638c01ed23f6914f6；对照 0f12df675378556670afd0dd2153f47fcb330610。完整生产 CommonParentCostTop / VFEX4，O2 弹性和融合输入开启，O1/trace 关闭，TE=0。沿用第 5 节同一参考库、工具、综合及五档约束。

新执行 1 次父级综合、5 次标准 STA、两边共 10 次控制专项 STA；结果 **C2_SCREEN_REJECT**，45 项中 20 项通过、25 项失败。

| 指标 | fix0f | C2 | 变化 / 门槛 |
| --- | ---: | ---: | --- |
| 父级单元面积和 | 284614.946 | 284496.310 | -0.041683%；上限 284899.560946 |
| 父级 DFF | 17172 | 17170 | 实际映射 |
| nominal 控制 D 最差 ns | 1.930584 | 0.977028 | -49.392101%；上限 1.737526 |
| 未知单元 / ICG 数 | 0 / 3 | 0 / 3 | 完整生产边界 |

五档完整筛选如下。数值为 arrival / slack（ns）；arrival 上限为对照的 101%，原有正 slack 的 ICG 保持非负。icg0/1/2 是原报告查询标识，语义和起止点在 JSON 与原报告中保留。

| 档位 | 路径 | fix0f arrival / slack | C2 arrival / slack | arrival 变化 | 筛选 |
| --- | --- | ---: | ---: | ---: | --- |
| nominal | r2r | 3.261218 / -2.341112 | 3.296141 / -2.373648 | +1.070858% | FAIL |
| nominal | i2r | 3.314103 / -2.393998 | 3.338666 / -2.416173 | +0.741166% | PASS |
| nominal | vdot_r2r | 1.356106 / -0.433760 | 1.378167 / -0.455822 | +1.626790% | FAIL |
| nominal | vdot_i2r | 1.474949 / -0.549064 | 1.469347 / -0.547006 | -0.379810% | PASS |
| nominal | vdot_r2o | 2.776701 / -1.926701 | 2.959080 / -2.109080 | +6.568190% | FAIL |
| nominal | ready | 0.247821 / 0.602179 | 0.349254 / 0.500746 | +40.929945% | FAIL |
| nominal | icg0 | 1.888362 / -1.010883 | 0.505818 / 0.372885 | -73.213928% | PASS |
| nominal | icg1 | 1.128021 / -0.249725 | 0.488211 / 0.387873 | -56.719689% | PASS |
| nominal | icg2 | 0.873228 / 0.003779 | 0.945313 / -0.061260 | +8.255003% | FAIL |
| period050 | r2r | 3.261218 / -2.841112 | 3.296141 / -2.873648 | +1.070858% | FAIL |
| period050 | i2r | 3.314103 / -2.893998 | 3.338666 / -2.916173 | +0.741166% | PASS |
| period050 | vdot_r2r | 1.356106 / -0.933760 | 1.378167 / -0.955822 | +1.626790% | FAIL |
| period050 | vdot_i2r | 1.474949 / -1.049064 | 1.469347 / -1.047006 | -0.379810% | PASS |
| period050 | vdot_r2o | 2.776701 / -2.426701 | 2.959080 / -2.609080 | +6.568190% | FAIL |
| period050 | ready | 0.247821 / 0.102179 | 0.349254 / 0.000746 | +40.929945% | FAIL |
| period050 | icg0 | 1.888362 / -1.510883 | 0.505818 / -0.127115 | -73.213928% | PASS |
| period050 | icg1 | 1.128021 / -0.749725 | 0.488211 / -0.112127 | -56.719689% | PASS |
| period050 | icg2 | 0.873228 / -0.496221 | 0.945313 / -0.561261 | +8.255003% | FAIL |
| period200 | r2r | 3.261218 / -1.341112 | 3.296141 / -1.373648 | +1.070858% | FAIL |
| period200 | i2r | 3.314103 / -1.393998 | 3.338666 / -1.416173 | +0.741166% | PASS |
| period200 | vdot_r2r | 1.356106 / 0.566240 | 1.378167 / 0.544178 | +1.626790% | FAIL |
| period200 | vdot_i2r | 1.474949 / 0.450936 | 1.469347 / 0.452994 | -0.379810% | PASS |
| period200 | vdot_r2o | 2.776701 / -0.926701 | 2.959080 / -1.109080 | +6.568190% | FAIL |
| period200 | ready | 0.247821 / 1.602179 | 0.349254 / 1.500746 | +40.929945% | FAIL |
| period200 | icg0 | 1.888362 / -0.010883 | 0.505818 / 1.372885 | -73.213928% | PASS |
| period200 | icg1 | 1.128021 / 0.750275 | 0.488211 / 1.387873 | -56.719689% | PASS |
| period200 | icg2 | 0.873228 / 1.003779 | 0.945313 / 0.938739 | +8.255003% | FAIL |
| load001 | r2r | 3.261218 / -2.341112 | 3.296141 / -2.373648 | +1.070858% | FAIL |
| load001 | i2r | 3.314103 / -2.393998 | 3.338666 / -2.416173 | +0.741166% | PASS |
| load001 | vdot_r2r | 1.356106 / -0.433760 | 1.378167 / -0.455822 | +1.626790% | FAIL |
| load001 | vdot_i2r | 1.474949 / -0.549064 | 1.469347 / -0.547006 | -0.379810% | PASS |
| load001 | vdot_r2o | 2.756125 / -1.906126 | 2.938536 / -2.088536 | +6.618386% | FAIL |
| load001 | ready | 0.238594 / 0.611406 | 0.337792 / 0.512208 | +41.576066% | FAIL |
| load001 | icg0 | 1.888362 / -1.010883 | 0.505818 / 0.372885 | -73.213928% | PASS |
| load001 | icg1 | 1.128021 / -0.249725 | 0.488211 / 0.387873 | -56.719689% | PASS |
| load001 | icg2 | 0.873228 / 0.003779 | 0.945313 / -0.061260 | +8.255003% | FAIL |
| load020 | r2r | 3.261218 / -2.341112 | 3.296141 / -2.373648 | +1.070858% | FAIL |
| load020 | i2r | 3.314103 / -2.393998 | 3.338666 / -2.416173 | +0.741166% | PASS |
| load020 | vdot_r2r | 1.356106 / -0.433760 | 1.378167 / -0.455822 | +1.626790% | FAIL |
| load020 | vdot_i2r | 1.474949 / -0.549064 | 1.469347 / -0.547006 | -0.379810% | PASS |
| load020 | vdot_r2o | 2.852842 / -2.002842 | 3.035195 / -2.185195 | +6.391977% | FAIL |
| load020 | ready | 0.308999 / 0.541001 | 0.376593 / 0.473407 | +21.875152% | FAIL |
| load020 | icg0 | 1.888362 / -1.010883 | 0.505818 / 0.372885 | -73.213928% | PASS |
| load020 | icg1 | 1.128021 / -0.249725 | 0.488211 / 0.387873 | -56.719689% | PASS |
| load020 | icg2 | 0.873228 / 0.003779 | 0.945313 / -0.061260 | +8.255003% | FAIL |

全部筛选失败原因：

- nominal/r2r exceeds +1% (1.070858%)
- nominal/vdot_r2r exceeds +1% (1.626790%)
- nominal/vdot_r2o exceeds +1% (6.568190%)
- nominal/ready exceeds +1% (40.929945%)
- nominal/icg2 violates +1%/positive-slack gate
- period050/r2r exceeds +1% (1.070858%)
- period050/vdot_r2r exceeds +1% (1.626790%)
- period050/vdot_r2o exceeds +1% (6.568190%)
- period050/ready exceeds +1% (40.929945%)
- period050/icg2 violates +1%/positive-slack gate
- period200/r2r exceeds +1% (1.070858%)
- period200/vdot_r2r exceeds +1% (1.626790%)
- period200/vdot_r2o exceeds +1% (6.568190%)
- period200/ready exceeds +1% (40.929945%)
- period200/icg2 violates +1%/positive-slack gate
- load001/r2r exceeds +1% (1.070858%)
- load001/vdot_r2r exceeds +1% (1.626790%)
- load001/vdot_r2o exceeds +1% (6.618386%)
- load001/ready exceeds +1% (41.576066%)
- load001/icg2 violates +1%/positive-slack gate
- load020/r2r exceeds +1% (1.070858%)
- load020/vdot_r2r exceeds +1% (1.626790%)
- load020/vdot_r2o exceeds +1% (6.391977%)
- load020/ready exceeds +1% (21.875152%)
- load020/icg2 violates +1%/positive-slack gate

本候选未通过冻结成本合同，保留 fix0f，本候选全核与周期入口关闭。
本成本记录的新全核/NEMU、新同镜像 cycles、功耗和整核 Fmax 均为 **NOT_TESTED**。此前 C2-local 的 FU/父级资格按固定来源复用，本轮未重跑局部仿真。

这是布局前工程筛选，不是官方赛题门槛；不能把负 slack 忽略、将 arrival 倒数当整核 Fmax，或将相对改善当作已经完成 1ns 时序收敛。

[合同](../optimizations/o2/r3-div-gate/c2/cost/CONTRACT.md) · [完整结果](../optimizations/o2/r3-div-gate/c2/cost/RESULT.md) · [证据 manifest](../optimizations/o2/r3-div-gate/c2/cost/evidence/20261025-cost/manifest.json)。全部标准与专项路径、起止点和 slack 保留在 JSON 与原始报告中。

独立原文复算 C2_COST_INDEPENDENT_AUDIT_PASS、便携审计 C2_PORTABLE_COST_AUDIT_PASS、生产生成物审计 C2_COST_PRODUCTION_MODULES_PASS；审计通过确认数据与拒绝结论一致，不代表候选通过筛选。审计来源及 SHA 已追加至 JSON。

封存 manifest SHA256：d81ff41e4ae745a56172d2b75c6d85ceaa9e8f4c2fca7effc9a5e8bc4bf5d8c6。旧 18 条 JSON 记录逐字段保持，新增为第 19 条。

封存副本的 Linux 与 Windows 原生 Python 校验、数值复算均通过，均重现 20/45 通过及 C2 拒绝；没有新增全核或周期运行。完整回执见 [成本结果](../optimizations/o2/r3-div-gate/c2/cost/RESULT.md)。


## 10. C3-G0：最小改法可行性评审（2026-10-25）

记录 **C3-G0-20261025-01** 是只读设计评审与纯 Python 控制抽象运行，不是新硬件版本。建议至多一次 C3-HF 试验：从 0f 出发，只替换 FP DIV/SQRT hold 的置位条件，保持原门控公式、实际握手及全部其他状态；本轮没有实施。

新控制抽象有四组（两种概念方案×两种复位合同），每组48状态、38,400状态/输入组合、48,960后继，8种ROB初始历史；六项坏变体被拒绝，域外无有效初始化反例保留。只推荐 hold-only，未选择 gate+hold。重叠状态不相加为 RTL 覆盖率；模型 PASS 不转授新 RTL/FU/父级资格。

旧0f/C1/C2路径数字仅作为设计依据，不生成C3面积或周期数值。新RTL、真实FU/父级、面积/STA、全核/NEMU、同镜像周期和功耗均为 **NOT_TESTED**。当前保留0f，C1/C2否决保持。后续先局部正确性，再一次原约束成本筛选；失败则结束当前门控试验，成本全部通过才进入新全核/周期。

[完整评审](../optimizations/o2/r3-div-gate/c3-g0/RESULT.md) · [控制数据](../optimizations/o2/r3-div-gate/c3-g0/evidence/candidate-review/control-variants-01.json) · [证据manifest](../optimizations/o2/r3-div-gate/c3-g0/evidence/manifest.json)。

本次仅追加第20条，旧19条JSON记录与既有来源固定值逐字段保持。54份评审载荷封存，manifest SHA256：66ae381f1e2aafbed3d19a63b4b59bb7ce85c6f849279ac49d593a37e440cb8c。

## 11. C3-HF 单次最小试验：局部通过、成本否决（2026-10-25）

记录 ID：C3-HF-20261025-01。实际开始 2026-10-25T22:05:32.367527+08:00，完成 2026-10-25T22:41:41.712685+08:00。
[结果](../optimizations/o2/r3-div-gate/c3-hf/RESULT.md)、
[生产合同](../optimizations/o2/r3-div-gate/c3-hf/CONTRACT.md)、
[成本合同](../optimizations/o2/r3-div-gate/c3-hf/cost/CONTRACT.md)。
**REJECT，不采用，保留 0f，关闭当前门控试验。** 此结论不改变任何历史版本加速比。

唯一候选 77d0a1228f0da7d584d5c7375b404dcda9763cf3，ExeUnit SHA-256 150baa7c78aa8948ff0f4fb771912f7d2058aaa802a0853ee99ea3a2dc0bb9b7。
基线 0f12df675378556670afd0dd2153f47fcb330610。仅 FP DIV/SQRT hold SET 从真实 fire 改为 P_F；
两个 hold、divBusy、ROB、原 ICG.E 公式、实际接受协议、整数和 VDot 保持。
该单点试验不构成 C1/C2 完整两因素归因，亦未实施 gate＋hold 更大改法。

### 11.1 本轮实际局部验证

| 层级 | 实际结果 |
| --- | --- |
| 主机检查 | 49 父级＋2 FU，共 51 项通过 |
| FU | 22 定向＋10,000 随机，完整 128 位结果；31,499 拍，4 个坏观察被拒绝 |
| 原真实父级 | 13 组、35,075 拍；16 个坏观察被拒绝；本轮严格轨迹重放通过 |
| 补充父级 | 115 场景、6 组、2,959 拍；7 个坏观察被拒绝；实际完成 attempt 为 supplement-02 |
| C3 hold 观察 | 2,958 拍有效初始化域内 P_F＝实际 FP fire；FP/INT hold 符合原 fire 递推；9 个坏观察被拒绝 |
| 实际观察覆盖 | 143 次 FP 接受、15 次普通 SQRT、54 次取消、291 拍 FP 反压、20 个 TE0 复位场景／40 拍复位 |
| 取消后关钟 | 54 窗口、162 个立即空闲采样；0 多余时钟 |
| 独立局部审计 | C3_HF_LOCAL_INDEPENDENT_AUDIT_PASS，1103 个输入、126 依赖 |
| 全核/NEMU、周期、功耗、整核 Fmax | NOT_TESTED |

4＋16＋7＋9 是运行时/离线坏观察拒错，非 RTL 变异；观察覆盖存在重叠，不能累计为唯一覆盖率。
旧 C3-G0 抽象论证只复用，没有重复计入本轮 RTL 验证。
supplement-01 的测试观察器编译宽度告警失败保留，修正测试表达式后新 supplement-02 通过；
未把基础设施失败伪装成候选通过，也未修改生产 RTL 以绕过门禁。
保持位观察结论限定于测试顶层实际采样的有效同步 bootstrap 域，不是异步物理复位签核。

### 11.2 同约束成本和三状态 D

采用相同 CommonParentCostTop/MinimalConfig(1)、Nangate45 typical 25°C/1.1V、
Yosys 0.9／ABC 1.01／OpenSTA 2.0.17。ABC -D 1000 ps；BUF_X1 输入驱动、
理想时钟、5K_hvratio_1_1 wireload、uncertainty/transition 各 0.05 ns、I/O delay 0.1 ns、TE=0。
五档为 nominal(1 ns,5 fF)、period050(0.5 ns,5 fF)、period200(2 ns,5 fF)、
load001(1 ns,1 fF)、load020(1 ns,20 fF)。
实际一次新生产生成、一次综合、五档常规 STA、两边各五档定向 STA；
无第二候选、映射挑选或阈值放宽。

| 指标 | 0f | C3-HF | 冻结门槛与判定 |
| --- | --- | --- | --- |
| 父级参考库单元面积和 | 284614.946 | 285138.966 | +0.184115%；上限 284899.560946，FAIL |
| 父级 DFF | 17172 | 17171 | 实际映射，非预设数量 |
| 最差控制 D / ns | 1.930584 | 1.609770 | -16.617459%；上限 1.737526，PASS |
| ICG / 未知单元 | 3 / 0 | 3 / 0 | 完整生产边界 |
| 五档全部路径 | 45 项 | 20 PASS / 25 FAIL | 任一失败即否决 |

| 控制 D 端 | 0f (ns) | C3-HF (ns) | 变化 |
| --- | --- | --- | --- |
| divBusy | 0.870094 | 0.859954 | -1.165391% |
| FP hold | 1.930584 | 0.557445 | -71.125577% |
| INT hold | 1.506153 | 1.609770 | +6.879580% |

两边均绑定 divBusy、FP hold、INT hold 三个不同 DFF 的 D。FP hold 显著缩短至 0.557445 ns，
但当前最差已转为 INT hold 1.609770 ns；不能只展示有利的 FP 单点。
配套 JSON 保留三状态全部五档 arrival、slack、实际起止点与语义到 D 引脚映射。

### 11.3 五档 45 项完整比较

每项 arrival 最多比同档 0f 增加 1%；基线非负的 ICG slack 仍须非负。
这是本项目冻结筛选合同，并非官方比赛阈值；相对 PASS 不表示绝对时序收敛。

| 档位 | 路径 | 0f arrival / slack (ns) | C3-HF arrival / slack (ns) | arrival 变化 | 筛选 |
| --- | --- | --- | --- | --- | --- |
| nominal | r2r | 3.261218 / -2.341112 | 3.229321 / -2.305008 | -0.978070% | PASS |
| nominal | i2r | 3.314103 / -2.393998 | 3.283447 / -2.360285 | -0.925017% | PASS |
| nominal | vdot_r2r | 1.356106 / -0.433760 | 1.318106 / -0.395290 | -2.802141% | PASS |
| nominal | vdot_i2r | 1.474949 / -0.549064 | 1.566019 / -0.643681 | +6.174451% | FAIL |
| nominal | vdot_r2o | 2.776701 / -1.926701 | 2.852312 / -2.002312 | +2.723052% | FAIL |
| nominal | ready | 0.247821 / 0.602179 | 0.268650 / 0.581350 | +8.404857% | FAIL |
| nominal | icg0 | 1.888362 / -1.010883 | 1.975078 / -1.096782 | +4.592128% | FAIL |
| nominal | icg1 | 1.128021 / -0.249725 | 1.262832 / -0.384536 | +11.951107% | FAIL |
| nominal | icg2 | 0.873228 / 0.003779 | 0.874722 / 0.002292 | +0.171089% | PASS |
| period050 | r2r | 3.261218 / -2.841112 | 3.229321 / -2.805008 | -0.978070% | PASS |
| period050 | i2r | 3.314103 / -2.893998 | 3.283447 / -2.860285 | -0.925017% | PASS |
| period050 | vdot_r2r | 1.356106 / -0.933760 | 1.318106 / -0.895290 | -2.802141% | PASS |
| period050 | vdot_i2r | 1.474949 / -1.049064 | 1.566019 / -1.143681 | +6.174451% | FAIL |
| period050 | vdot_r2o | 2.776701 / -2.426701 | 2.852312 / -2.502312 | +2.723052% | FAIL |
| period050 | ready | 0.247821 / 0.102179 | 0.268650 / 0.081350 | +8.404857% | FAIL |
| period050 | icg0 | 1.888362 / -1.510883 | 1.975078 / -1.596782 | +4.592128% | FAIL |
| period050 | icg1 | 1.128021 / -0.749725 | 1.262832 / -0.884536 | +11.951107% | FAIL |
| period050 | icg2 | 0.873228 / -0.496221 | 0.874722 / -0.497708 | +0.171089% | PASS |
| period200 | r2r | 3.261218 / -1.341112 | 3.229321 / -1.305008 | -0.978070% | PASS |
| period200 | i2r | 3.314103 / -1.393998 | 3.283447 / -1.360285 | -0.925017% | PASS |
| period200 | vdot_r2r | 1.356106 / 0.566240 | 1.318106 / 0.604711 | -2.802141% | PASS |
| period200 | vdot_i2r | 1.474949 / 0.450936 | 1.566019 / 0.356319 | +6.174451% | FAIL |
| period200 | vdot_r2o | 2.776701 / -0.926701 | 2.852312 / -1.002312 | +2.723052% | FAIL |
| period200 | ready | 0.247821 / 1.602179 | 0.268650 / 1.581350 | +8.404857% | FAIL |
| period200 | icg0 | 1.888362 / -0.010883 | 1.975078 / -0.096782 | +4.592128% | FAIL |
| period200 | icg1 | 1.128021 / 0.750275 | 1.262832 / 0.615464 | +11.951107% | FAIL |
| period200 | icg2 | 0.873228 / 1.003779 | 0.874722 / 1.002292 | +0.171089% | PASS |
| load001 | r2r | 3.261218 / -2.341112 | 3.229321 / -2.305008 | -0.978070% | PASS |
| load001 | i2r | 3.314103 / -2.393998 | 3.283447 / -2.360285 | -0.925017% | PASS |
| load001 | vdot_r2r | 1.356106 / -0.433760 | 1.318106 / -0.395290 | -2.802141% | PASS |
| load001 | vdot_i2r | 1.474949 / -0.549064 | 1.566019 / -0.643681 | +6.174451% | FAIL |
| load001 | vdot_r2o | 2.756125 / -1.906126 | 2.831839 / -1.981839 | +2.747118% | FAIL |
| load001 | ready | 0.238594 / 0.611406 | 0.259698 / 0.590302 | +8.845151% | FAIL |
| load001 | icg0 | 1.888362 / -1.010883 | 1.975078 / -1.096782 | +4.592128% | FAIL |
| load001 | icg1 | 1.128021 / -0.249725 | 1.262832 / -0.384536 | +11.951107% | FAIL |
| load001 | icg2 | 0.873228 / 0.003779 | 0.874722 / 0.002292 | +0.171089% | PASS |
| load020 | r2r | 3.261218 / -2.341112 | 3.229321 / -2.305008 | -0.978070% | PASS |
| load020 | i2r | 3.314103 / -2.393998 | 3.283447 / -2.360285 | -0.925017% | PASS |
| load020 | vdot_r2r | 1.356106 / -0.433760 | 1.318106 / -0.395290 | -2.802141% | PASS |
| load020 | vdot_i2r | 1.474949 / -0.549064 | 1.566019 / -0.643681 | +6.174451% | FAIL |
| load020 | vdot_r2o | 2.852842 / -2.002842 | 2.928424 / -2.078424 | +2.649358% | FAIL |
| load020 | ready | 0.308999 / 0.541001 | 0.339873 / 0.510127 | +9.991618% | FAIL |
| load020 | icg0 | 1.888362 / -1.010883 | 1.975078 / -1.096782 | +4.592128% | FAIL |
| load020 | icg1 | 1.128021 / -0.249725 | 1.262832 / -0.384536 | +11.951107% | FAIL |
| load020 | icg2 | 0.873228 / 0.003779 | 0.874722 / 0.002292 | +0.171089% | PASS |

失败为面积 1 项，以及 VDot i2r、VDot r2o、ready、FP ICG.E、INT ICG.E
五类路径在五档中的 25 项；完整失败文本和实际起止点见配套 JSON。
原文独立成本审计 C3_HF_COST_INDEPENDENT_AUDIT_PASS，857 输入不变，
表明数据有效，**不表示候选通过成本筛选**。
父级 r2r 虽下降至 3.229321 ns，仍有负 slack；不得以其倒数冒充整核 Fmax。
完整父级 ABC 重映射可影响源码未改模块的路径；此数据不证明某一个布尔项是全部变化的唯一原因。

### 11.4 身份、原文与停止边界

[封存 manifest](../optimizations/o2/r3-div-gate/c3-hf/evidence/20261025-trial/manifest.json)
SHA-256：d59cb0ebaec8209a8683ce3b3f97fafabc4daedbd50e0a2e0f36caf948d3ce31。载荷 1131 份，包含实际新结果、局部/成本审计、
冻结输入、工具与二进制身份、原文路径和失败记录；压缩文件按 manifest 的 raw/stored 双 SHA 读取。
本台账将新来源仅追加到 c3_hf_source_pins／c3_hf_sources，旧 20 条及旧来源保持。

C3-HF 新 EMU、NEMU 差分、性能镜像及同镜像周期均 NOT_TESTED。保留 0f EMU
2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8，不能把它授予新候选。
本轮不产生新的加速比、功耗或比赛分数结论；当前门控支线结束，回到保留主线的稳定集成与 T17 干净复现。

## 12. 固定 0f 硬件上的 firstdot V2 组合验证（2026-10-26～27）

记录 ID：`FIRSTDOT-V2-DIVFIX0F-20261026-01`。本轮选择性引入 zufan 的 T17 工具与 firstdot V2，使用当前 O2＋H1＋DIV 取消关钟修复 0f 硬件实测。联合原文审计实际返回 0，状态为 **CURRENT_FIRSTDOT_CONTINUATION_FUNCTIONAL_CYCLES_AUDIT_PASS_WALL_CLOCK_LIMITED**。功能与 DUT 周期通过；**墙钟时间线 FAIL 单独保留**，不将其改写为完整无条件 PASS。干净复现、配置复用及新面积/时序仍为 NOT_TESTED。

### 12.1 公平比较口径及全部形状结果

相同 0f 模拟器、输入和观察器；S1/firstdot 两个软件版本使用成对固定布局与完整 RVV 代码槽。BIN 随软件变化，不能称为同镜像硬件消融。比较覆盖 4 形状 × 3 数据集 × S1/firstdot × basic/reuse × vdot/RVV。下表为包含 C ABI 调用/返回的 reuse 窗口算术均值，每项 12 个正式窗口（3 数据集 × repeat 2～5）；不扣除计时成本。最快 RVV 从全部四种 RVV 组合中选择，未采用较慢分母。JSON 保留每种形状的全部 8 个候选及精确值。

| 形状 | S1 reuse vdot cycles | firstdot reuse vdot cycles | 最快纳入 RVV cycles | 相比 S1 周期减少 | 相比最快 RVV 周期减少 | RVV/firstdot 加速比 | 当前组合选择 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 4×8 | 169.75 | 157.75 | 187.50 | 7.0692% | 15.8667% | 1.1886× | firstdot reuse vdot |
| 8×32 | 292.50 | 282.25 | 300.75 | 3.5043% | 6.1513% | 1.0655× | firstdot reuse vdot |
| 16×64 | 717.25 | 707.00 | 778.75 | 1.4291% | 9.2135% | 1.1015× | firstdot reuse vdot |
| 4×13 | 219.75 | 204.50 | 187.00 | 6.9397% | -9.3583% | 0.9144× | firstdot reuse RVV |

4×8、8×32、16×64 的 reuse vdot 分别减少 12、10.25、10.25 cycles；窗口退休指令分别为 54→44、202→182、672→632。4×13 的 firstdot vdot 虽比 S1 vdot 减少 15.25 cycles，仍比最快 RVV 多 17.5 cycles，即慢 9.3583%，因此保留 firstdot reuse RVV 回退。此形状 S1/firstdot reuse RVV 同为 187 cycles，并列最快。以上为本合同的应用窗口收益，不产生新的 RTL、整核 Fmax、功耗或比赛分数结论。

这四项选择已获得当前软硬件组合的原文资格；公共 stable 默认入口未切换，仍需干净复现完成后再决定默认集成。

### 12.2 运行数量与功能证据

| 项目 | 实测记录及本轮审计 |
| --- | --- |
| EMU 实际启动 | **38 次**：矩阵 34、普通 C 4 |
| 合格完成 / 中断 | **36 / 2**：矩阵 33 / 1，普通 C 3 / 1 |
| 续跑关系 | 新增 23 次；保留同轮已合格 13 次；原先实际启动 15 次中含 2 次中断 |
| 正式 / 重放窗口 | **384 / 192**；连同 first/warmup 共 768 个正常窗口 |
| 普通 C ABI | **16 个公共函数、48 个不同 case、96 次完整正常调用** |
| 全 128 位结果、NEMU 差分 | PASS |
| CSR 窗口与 O2 生命周期 | PASS |
| 高位负控及恢复 | PASS；firstdot 目的 v0 的 bit100 故障被拒绝，正常版本恢复 |
| 原文周期复算 | PASS；384 个正式样本身份、cycles/instructions 与留档逐条一致，32 个候选聚合重新核对 |
| 审计本身新增 EMU / NEMU | **0 / 0** |

两个中断记录和 null 退出码原样保留，不计入合格窗口与 96 次调用。已完成的负控没有重跑；同轮续跑不借用队友历史硬件 PASS。计数不能只写 36 而隐藏两次中断启动。

### 12.3 墙钟时间线失败与证据边界

| 验收维度 | 结果 |
| --- | --- |
| 功能与 DUT 周期原文检查 | PASS |
| 冻结同步控制流与回执支持的因果串行顺序 | PASS |
| 严格 UTC 墙钟时间线 | **FAIL** |
| 直接单调时钟记录 | NOT_RECORDED |
| 墙钟回退原因 | UNCONFIRMED |

旧矩阵 `formal-performance-s1-d0-s01` 的 finished 为 `2026-10-26T07:07:55.796377+00:00`，
随后 `formal-performance-s1-d1-s01` 的 started 为 `2026-10-26T07:07:55.252896+00:00`，
出现 **0.543481 秒**回退。两条原始 result 哈希、完整时间值和源码/回执绑定见配套 JSON 的 chronology。

冻结路径按同步 `Popen → wait → 校验 → finished/写盘 → 下一次 launch` 执行，控制器完成日志也保持该顺序；started/finished 来自 `datetime.now(timezone.utc)`，没有 monotonic 时间线。故此证据支持串行生命周期，不能独立证明精确主机时间间隔；不推测 NTP 或 WSL 时钟调整原因。并行的独立 C 运行也不能用来解释时钟回退。

DUT/CSR cycles 不由主机 UTC 相减得到，故功能/周期原文资格与此墙钟失败分开记录。原时间值未改、记录未重排、未设置容差。第一次审计工具导入失败及随后 v1 严格 chronology 检查失败均保留；v2 显式使用墙钟受限合同，没有将旧合同的 FAIL 改成 PASS。

### 12.4 硬件、软件、配置与证据身份

- 实际硬件构建源：`0f12df675378556670afd0dd2153f47fcb330610`。
- EMU SHA-256：`2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8`。
- NEMU SHA-256：`efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4`。
- firstdot/T17 选择性来源：zufan `fcf4a11fc569cb2a8fcb4e18d96ec2764b228557`，45 个文件（43 新增、2 原有相同）。
- 本地软件及工具源码提交：`c823a8786e052c6e26f6915563c42b6d730dd8e3`。这是运行后的源码提交，不是新 EMU 构建身份；提交后 25,869 项物理硬件输入复核 PASS，原 EMU 不变。
- 配置：MinimalConfig / 1 核，O2 elastic、T14 fused input 启用，O2/T13 观察开启，EMU_THREADS=1，seed=1，128MB RAM，max-cycles=2,000,000。
- JSON 内嵌 24 个矩阵镜像、普通 C 镜像、工具链、AM/klib、源清单、命令与实际进程记录的身份目录，并绑定 base、矩阵续跑、C 续跑及 v2 审计合同。

实际原文审计：
`/home/riscv/riscv-lab/software-import-20261026/reviews/resume-audit-fix-01/full-raw-audit-02/`。
封存 [manifest](/home/riscv/riscv-lab/software-import-20261026/reviews/resume-audit-fix-01/full-raw-audit-02/archive/manifest.json)
SHA-256：`b4f255c6cb81c02536f1797ee8938ab784888b4a65f90cf6b5fb5024f274d06c`。
共 1,756 份载荷，原文 966,485,449 bytes、存储 176,446,013 bytes，raw/stored 双 SHA 校验通过。
此封存仍依赖原外部构建输入才能重新进行原文审计；**不宣称独立可移植复算或干净复现完成**。

### 12.5 未测事项及干净复现尝试

本条的独立干净复现、配置复用、FU/父级重跑、新面积/STA、功耗和成员人工复现均 **NOT_TESTED**。生产 RTL 和公共 stable 默认入口不变；本轮未推送 GitHub。

单独的 `clean-01` 已尝试新构建，但返回 2、未生成新 EMU。其 Mill Git 历史查询报 `Could not read e524aeedab50586b2dbc86a2180380085c43a4cd`；linked worktree 本地克隆未保留真实浅克隆边界的构建准备问题另行修复。失败状态保留于
[clean-01/build/build-state.json](/home/riscv/riscv-lab/software-import-20261026/clean-01/build/build-state.json)，
不把构建失败算作当前已完成组合的功能/性能失败，也不给予干净复现资格。后续使用新的干净目录继续，完成后追加新的实测记录；再开展配置复用筛选。

本节与配套 JSON 为追加第 22 条记录，原 21 条历史记录及原来源内容保留。

## 13. 同机干净复现完成：CLEAN-FIRSTDOT-V2-DIVFIX0F-20261027-01

第23条记录。沿用0f硬件（O2＋H1＋DIV取消修复），软件/工具源码c823a；独立检出并重新构建NEMU、EMU、AM/klib和应用。保留本机已装工具及下载缓存，不等同新机器人工复现。

- 实际启动并结束53个目标进程，选用50个：全核14、矩阵33、新C3。原C3个功能通过但外层时间校验失败，保留并排除；无中断。49次exit0、4次预期负控exit1。
- 新旧25个应用镜像BIN/ELF装载段一致；768个完整窗口逐项一致；16公共函数、48case、96次C调用输出一致。联合原文审计通过。
- 全核117个不同功能case/124次执行及O2覆盖通过。宿主UTC曾推导出80.119ms重叠，墙钟容量仍FAIL；源码线程池上限3的证据PASS，未实测OS单调时钟并发。不能据此宣称宿主运行耗时或频率改善。
- 原C回执2.455386s时间异常及clean-01构建失败均留档；仅另跑3个C进程，未放宽C检查器，run02严格验收PASS。

| 形状 | S1 reuse vdot | firstdot reuse vdot | 最快同口径RVV | firstdot较S1减少 | RVV/firstdot |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4×8 | 169.75 | 157.75 | 187.50 | 7.0692% | 1.1886× |
| 8×32 | 292.50 | 282.25 | 300.75 | 3.5043% | 1.0655× |
| 16×64 | 717.25 | 707.00 | 778.75 | 1.4291% | 1.1015× |
| 4×13 | 219.75 | 204.50 | 187.00 | 6.9397% | 0.9144× |

单位cycles，包含C ABI调用/返回，3数据集每格12个正式样本。4×13继续RVV回退。公共stable默认入口未切换；配置复用另项筛选。新面积/STA/功耗、单独FU/父级重跑、成员人工验收均NOT_TESTED。

新EMU SHA-256: acf672eb39f836da4000b253849e3214089e9c8e5198060a57d2cc6bbd393da9。

新NEMU SHA-256: 62b1707c52a4c323468481e0c1863b79f244d9a3fd54aeb7b7d2ecb5f01a35ca。

本地根：/home/riscv/riscv-lab/software-import-20261026/clean-02。完整结果full-reproduction-comparison-03.json，联合审计combination-audit-03。全部版本、命令、镜像、失败和manifest哈希见配套JSON本条。全核封存manifest为a80a1063…，联合封存eba6744d…，编排补充封存5798eb25…；后者包含152文件且已双SHA回读，不替代原文资格。原始档案依赖本地外部物理输入，不声称单独档案即可重建。

## 14. 配置复用有界筛选：CONFIG-REUSE-DIVFIX0F-CLEAN02-20261027-01

第24条。结果：**PERFORMANCE_CANDIDATE**；功能与原文复算PASS。限定8×32/dataset0/C ABI完整调用窗，每格4正式样本。候选BIN不同，硬件、数据、布局和调用计划相同；不称同完整镜像比较。

| 方法 | firstdot平均cycles | 配置复用平均cycles | 退休指令(firstdot→配置复用) |
| --- | ---: | ---: | --- |
| basic vdot | 645.50 | 643.75 | [276] → [267] |
| reuse vdot | 282.25 | 273.00 | [182] → [175] |
| basic rvv | 356.00 | 356.00 | [180] → [180] |
| reuse rvv | 300.75 | 299.00 | [124] → [123] |

reuse vdot相对firstdot减少3.277236%；相对本次最快RVV减少8.695652%，RVV/vdot=1.095238×。
未解释对照项：[]。功能与性能结论分开；决策：KEEP_FOR_EXPANDED_VALIDATION_ONLY，本次不扩大矩阵、不切stable默认、不推送。

实际7个目标进程：V2的2个保留并排除，V3新5个功能通过；5次正常exit0、2次预期负控exit1。选用V3的32正式窗口、含重放96窗口、48对全窗口重放（一致=True）；firstdot24窗口与原干净合格对照一致=True。高位bit100拒错及正常恢复、NEMU完整128位结果、CSR与O2生命周期均PASS。

V2停止原因是对照BIN被工具误作实际加载BIN，正常目标exit0且UART failures=0，不能因此把原失败验收改为PASS。V3只修复测试适配层，保留共享对照哈希校验；61项主机检查PASS，含真实旧日志失败复现及错误镜像/篡改拒绝。原失败原样封存。

V3首次独立审计又因循环变量遮蔽物理身份而误报；原失败保留。独立新审计器仅重命名两个循环变量，真实完整批次成功及模拟最终身份漂移仍拒绝两项检查PASS。新audit-02及completion-02通过，全程不新增EMU；冻结运行源码和旧日志不改。

候选来源zufan fcf4a11的26文件＋39相同依赖；新适配器V3及执行器独立绑定。生产RTL仍0f；全核默认选择未变。新多形状/多数据集矩阵、普通公共C应用、面积/STA/功耗、成员人工复现均NOT_TESTED。4×13继续RVV回退。

本地原始输出：/home/riscv/riscv-lab/software-import-20261026/config-reuse-clean02-02。封存manifest：d5cbde2b37239214c6632b891dd61d94f9483cb45b51b7cacedd293e6a898bd5；原文审计及所有版本/镜像/配置/命令/实测数值见配套JSON。档案验证仅为字节封存，原文复算仍依赖本地物理输入。


## 15. 配置复用四尺寸、三数据集扩展（第25条）


本轮在当前 O2 + H1 + DIV 取消保持修复（0f）硬件上，比较 firstdot 与配置复用软件。24 个新镜像、33 个新目标进程已完成；功能、全128位结果、NEMU差分及原文审计通过。各尺寸的性能采用结论见下表，稳定入口尚未切换。

### 比较口径

- 尺寸为矩阵 M×K，分别为4×8、8×32、16×64、4×13；输入为有符号INT8，K=13保留真实尾部处理成本。
- dataset0覆盖INT8极值、正负和零；dataset1为固定模运算序列；dataset2为固定种子的随机数据。
- 完整C ABI调用窗口包含调用/返回、配置、装载、计算和存储，不扣空测开销。相同硬件、数据、布局和计划，软件BIN不同。
- 每个尺寸的每个比较格含12个正式样本（3组数据各4次）。同时保留首次/预热以及dataset0独立重放。
- 比较对象包含firstdot/config-reuse × basic/reuse × vdot/RVV八格；RVV分母使用本轮最快的合格格。

### 各尺寸结果

| 尺寸 | firstdot reuse vdot cycles | 配置复用 reuse vdot cycles | 最快RVV cycles | 比firstdot减少 | RVV/vdot | 判定 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 4x8 | 157.7500 | 153.0000 | 185.0000 | 3.0111% | 1.209150x | INCONCLUSIVE |
| 8x32 | 282.2500 | 273.0000 | 299.0000 | 3.2772% | 1.095238x | PERFORMANCE_CANDIDATE |
| 16x64 | 707.0000 | 702.7500 | 773.0000 | 0.6011% | 1.099964x | INCONCLUSIVE |
| 4x13 | 204.5000 | 205.5000 | 187.0000 | -0.4890% | 0.909976x | INCONCLUSIVE |

cycles为完整调用窗口的正式均值。PERFORMANCE_CANDIDATE要求聚合及每组数据均严格快于firstdot和最快RVV，同时无未解释控制漂移或其他格退化；REJECT与INCONCLUSIVE均保留原始数据。

### 逐数据集

下表只列逐组的局部指标判定；最终采用还受完整控制窗口与重放门禁约束，以上表总体判定为准。

| 尺寸 | 数据集 | firstdot cycles | 配置复用 cycles | 最快RVV cycles | RVV/vdot | 局部指标判定 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 4x8 | 0 | 157.7500 | 153.0000 | 185.0000 | 1.209150x | PERFORMANCE_CANDIDATE |
| 4x8 | 1 | 157.7500 | 153.0000 | 185.0000 | 1.209150x | PERFORMANCE_CANDIDATE |
| 4x8 | 2 | 157.7500 | 153.0000 | 185.0000 | 1.209150x | PERFORMANCE_CANDIDATE |
| 8x32 | 0 | 282.2500 | 273.0000 | 299.0000 | 1.095238x | PERFORMANCE_CANDIDATE |
| 8x32 | 1 | 282.2500 | 273.0000 | 299.0000 | 1.095238x | PERFORMANCE_CANDIDATE |
| 8x32 | 2 | 282.2500 | 273.0000 | 299.0000 | 1.095238x | PERFORMANCE_CANDIDATE |
| 16x64 | 0 | 707.0000 | 702.7500 | 773.0000 | 1.099964x | INCONCLUSIVE |
| 16x64 | 1 | 707.0000 | 702.7500 | 773.0000 | 1.099964x | INCONCLUSIVE |
| 16x64 | 2 | 707.0000 | 702.7500 | 773.0000 | 1.099964x | INCONCLUSIVE |
| 4x13 | 0 | 204.5000 | 205.5000 | 187.0000 | 0.909976x | INCONCLUSIVE |
| 4x13 | 1 | 204.5000 | 205.5000 | 187.0000 | 0.909976x | INCONCLUSIVE |
| 4x13 | 2 | 204.5000 | 205.5000 | 187.0000 | 0.909976x | INCONCLUSIVE |

### 控制差异与采用判断

- **8×32：保留性能候选。** 三组数据均为282.25→273 cycles，较firstdot少3.2772%，相对本轮最快RVV为1.095238×；控制窗口、同版本重放均一致。
- **4×8：保留收益信号，暂待归因。** 主项157.75→153 cycles；未改动basic RVV的正式均值仍为225.25，但部分首轮/正式窗口有±1周期变化。总体判定为INCONCLUSIVE，不能以平均相同替代逐窗门禁。
- **16×64：暂待归因。** 主项707→702.75 cycles，仅少0.6011%；未改动basic RVV的均值990→991，六窗记录也变化。总体判定为INCONCLUSIVE。
- **4×13：本轮不采用该候选，保留较优RVV。** 主项204.5→205.5 cycles，慢0.4890%，且慢于最快RVV的187 cycles；basic vdot与reuse RVV也有配对退化、未改RVV窗口存在差异。合同总体标记为INCONCLUSIVE，完整原因列表保存在record.json。

这些差异出现在已通过功能和NEMU差分的运行中。12个firstdot同BIN对照的288个完整样本与干净基线一致，8次同版本独立重放也一致；跨软件变体的控制周期变化因此仍需单独归因。本轮不修改门禁、不补跑到出现更好的结果，也不把静态少指令直接等同于性能收益。

### 验证与留档

24个镜像GNU/布局/再生检查通过，12个firstdot对照BIN及ELF装载内容与干净版本一致。实际启动33次：32次正常退出、1次预期bit100负控失败，随后同BIN恢复正常。新轮次未借用旧探针运行。
原文审计复核768个正常窗口，其中384个正式窗口；192个重放窗口对、288个firstdot历史同BIN对照窗口分别核对完整sample字典。重放一致性：True。
并发使用4个CPU，按同boot的单调时钟Popen/wait包络与阶段屏障检查；峰值：4。该包络不表示精确操作系统调度重叠。

92项主机测试通过。此前JSON键类型问题在主机组合测试中发现并修复；第一次启动因测试文件仍更新被源码锁拒绝，未构建或启动EMU，该失败回执保留。
原始证据归档逐文件回读通过：1841项，manifest SHA256：be8e45af31040e5a96c9b947587a02b1ef854aa2a0cf1014f4f7d6d05f4394c6。这不是新的便携环境重建。
固定版本、配置、24个镜像哈希、33个进程身份、全部32个比较格和逐数据集判定保存在record.json。

### 当前选择与下一步

本轮只完成数据集与尺寸扩展；生产RTL、默认入口和GitHub未改动。普通公共C应用路径尚未为配置复用版新增验证，面积/STA/功耗也没有新测量。
8×32优先补普通公共C调用路径验证；4×8和16×64先做只读控制差异归因，4×13保留既有较优RVV路径。相关门禁闭合后再考虑稳定入口。
只读复核确认12个firstdot镜像的288个完整样本与干净基线一致；15个未改动RVV控制格的完整8 KiB槽位逐字节相等。4×8、16×64、4×13的部分控制窗仍有周期差异，其微架构原因尚未确认，不能把它们当作噪声删除或放宽门禁。

原始工作目录：/home/riscv/riscv-lab/software-import-20261026/config-reuse-expanded-01

完整数据档案记录ID：CONFIG-REUSE-MATRIX-DIVFIX0F-CLEAN02-20261027-01


## 16. 8×32配置复用普通C调用（第26条）


当前 O2＋H1＋DIV 取消保持修复（0f）硬件上，**8×32 配置复用普通 C 调用验证通过**。本轮补齐实际 C ABI 调用的正确性、拒错、恢复和重放证据，未修改生产 RTL或稳定默认入口，未上传 GitHub。

### 本轮验证了什么

| 项目 | 实测结果 |
| --- | --- |
| 8×32 范围 | 4 个公共函数（basic/reuse × vdot/RVV）× 3 数据集，12 个不同用例；两轮正常运行共 24 次调用 |
| 完整夹具 | 保留 16 函数、48 不同用例；两轮共 96 次正常调用，全部通过 |
| 全宽结果 | 每行低 32 位 INT32 点积与标量模型一致，高 96 位清零；逐字节检查 |
| 边界与状态 | 输入不变、前后 canary、未用输出行及向量 CSR 检查通过；5 种软件错误自检全部检出 |
| 差分拒错 | 在8×32 reuse vdot内注入 vd0 的bit100错误，唯一mismatch被拒绝；同BIN恢复与独立重放通过 |
| O2 观察器 | 两轮均完整闭合；每轮1008次自定义提交，其中8×32为192次，无残留事务 |
| 机器码对应 | 16公共函数与此前12个配置复用矩阵单元逐字节匹配，共48次比较；8×32占12次 |
| 主机与原文审计 | 20项主机检查通过；GNU/ELF、原始UART/O2日志、版本/镜像/工具身份复核通过 |

### 真实运行与输入身份

- 新目标进程共3个，严格串行：1个预期拒错exit1、2个正常exit0；无中断。命令起止：2026-10-27T20:05:30.496475+08:00 至 2026-10-27T20:49:03.394487+08:00。
- 同一个C程序BIN：56805506eb98b68269c73a3645d8f75dff73b697e30dec5f93ccc4716089ad34。
- 实际注入PC：0x80000d64，指令字0x0388000b；不是复用性能探针的PC。
- 软件源码基点：c823a8786e052c6e26f6915563c42b6d730dd8e3；硬件：0f12df675378556670afd0dd2153f47fcb330610。
- EMU SHA256：acf672eb39f836da4000b253849e3214089e9c8e5198060a57d2cc6bbd393da9；NEMU SHA256：62b1707c52a4c323468481e0c1863b79f244d9a3fd54aeb7b7d2ecb5f01a35ca。
- MinimalConfig、单核、EMU_THREADS=1、VLEN128；guest上限2,000,000 cycles、seed1、128MB RAM；每个进程外部超时7200秒，CPU亲和0–3。
- 保留原C检查器的严格UTC顺序验收，另用同boot单调Popen/wait包络与真实PID核对串行。包络不等于精确OS调度时刻。
- 普通C主程序和Makefile保持冻结原文。仅将48条调用表稳定排序，把8×32/dataset0/reuse/vdot放首项；输入数据及完整case多重集合不变，以保证负控命中目标函数。

### 如何使用这个公共函数

本次使用Nexus-AM裸机C程序，接口为普通RV64 lp64d双指针ABI；实际测试经C函数指针调用。该资格不扩展为Linux用户态运行或完整LLM推理验收。

~~~c
void config_reuse_gemv_8x32_reuse_vdot(const int8_t *packed_ax, void *output_slots);
~~~

输入为行优先8×32有符号INT8矩阵A，紧接32项向量x，共288字节。输入和输出各自16字节对齐、互不重叠。输出为8个16字节槽，共128字节；每槽低4字节是INT32结果，高12字节为零，不能按连续8个int32_t读取。环境须启用向量状态，并支持VLEN128及当前自定义vdot编码；函数会覆盖允许的向量/调用者状态。
实际构建源、头文件和C调用程序保存在qualified-public及仓库精简材料public目录。静态库、dispatcher和默认入口未在本轮新增。

### 性能结论的边界

两次正确性程序的整程序计数（含启动、标量检查、UART，不是点积性能窗口）：recovery: 871322 cycles / 1062247 retired instructions；replay: 871322 cycles / 1062247 retired instructions。

本C正确性程序未采集新的性能窗口。上一轮4尺寸×3数据集矩阵中，8×32为firstdot 282.25 → 配置复用273.00 cycles，比firstdot少3.2772%；同场最快RVV为299.00 cycles，加速比1.095238×，每格12个正式样本。这些是上一轮完整调用窗口的数据，不能写成本C程序新跑出的加速比。
本次确认这些已测函数可以经普通C调用并正确工作；性能采用候选具体为8×32 reuse vdot，basic等函数只分别保留各自已有数据。4×8、16×64和4×13的性能资格不随功能通过升级；此前控制差异与K13较慢的结论继续保留。

### 失败记录与后续

首次V1运行在EMU启动前因进程包装器未接收位置参数env/timeout而失败，新增EMU为0。原源码、构建、回执保留；V2修复参数透传并补真实主机子进程测试，再在新目录完成本轮。未改内层冻结验证器或放宽门禁。
归档首次因固定系统编译器为符号链接而拒绝，未生成档案；新版仅对构建回执中已固定的工具链路径保存链接文本、实际目标与相同SHA，其他链接仍拒绝。原失败回执保留，无新增EMU。
下一步可评审8×32候选的稳定入口范围；4×8/16×64仍先只读归因未改RVV控制窗差异，4×13保留较优RVV。若改调用/调度/布局，须验证相应新路径，不能直接继承旧周期数。

### 留档

- 记录ID：CONFIG-REUSE-C8-DIVFIX0F-CLEAN02-20261027-02；统一数据档案第26条。
- 原始输出：/home/riscv/riscv-lab/software-import-20261026/config-reuse-c8-02
- 工具：/home/riscv/riscv-lab/software-import-20261026/reviews/config-reuse/c8-v2/c8.py
- 原文审计：/home/riscv/riscv-lab/software-import-20261026/config-reuse-c8-02/audit-01.json
- 本地归档：/home/riscv/riscv-lab/software-import-20261026/reviews/config-reuse-c8-final-archive-03/manifest.json
- 归档包含589项，manifest SHA256：0e2285d8f8b95f9126f8d1d5014de62620be242522aba1486aae515912ca2144。逐文件压缩前后SHA及回读通过；这是本地字节封存，不是独立机器复现。
- 完整版本、配置、镜像、命令、PID、退出码和失败记录保存在配套JSON。新周期、面积、STA、功耗、成员人工复现均为NOT_TESTED。


## 17. 独立8×32 C8最小软件包（第27条）

**结果：PASS，可作为独立、显式选用的 C8 静态软件包使用。** 当前软件源码基点 c823a8786e052c6e26f6915563c42b6d730dd8e3，硬件保持 0f12df675378556670afd0dd2153f47fcb330610（O2＋H1＋DIV取消保持修复）。

本轮实现 `selected_gemv_c8.h`、完整单对象库构建、调用示例、当前身份验证器和主机测试。未切换旧四尺寸默认入口，未修改生产 RTL，未提交或上传 GitHub。执行者 @cc77-builder / Agent；本地包验收不是成员人工验收。

### 实际结果

| 验收项 | 本轮结果 |
| --- | --- |
| GNU 构建 | 固定 rv64gcv/lp64d/mno-relax，独立重建完整对象与原 C8 已验证对象全字节相同 |
| 完整对象 | 27,160 bytes；SHA256 f8bc13daeead98a414f313600a5778c96ac95a66b5bcb5c714ea3b98e0d25ab3 |
| 静态库 | libxs_gemv_c8.a，仅一个完整 gemv.o；ar t/p、独立归档、确定性字节一致 |
| 符号与节 | 16 个原公共函数；单一16字节对齐.text；原对象无重定位；新增运行时别名/包装函数为0 |
| 别名与链接 | 缺省、0、1及宏展开为1共4模式；两个别名的 caller.o/linked.o 与直接调用逐字节相同 |
| 实际引用 | 每模式核对2个有序指针重定位、2个调用重定位；GNU可重定位链接后未解析符号为空 |
| 错误配置拒绝 | 17项集成负控：10种非法宏、4种错误别名、错误对象、错误库、缺失头文件 |
| 旧入口共存 | V1/V2分别与C8，两个包含顺序×旧新开关0/1，共16组，选择与版本保持 |
| 搬移 | SDK移到仓库外含空格目录；默认vdot及强制RVV示例均按文档flags编译/链接通过 |
| 主机检查 | 22项unittest通过，包括错误硬件/NEMU、混合配置、缺失数据集、伪造历史C资格及改哈希后错选择拒绝 |
| 构建门禁 | 额外3项Python优化模式负控通过：旧输出、仓库内输出、错误源码仍被拒绝 |
| 原始资格 | 当前0f身份及完整输入闭包复核；原33个矩阵进程＋3个C进程重审，48次叶函数锚点通过 |
| 新目标运行 | 0 EMU、0 NEMU；新示例运行、新最终ELF、新周期、面积/STA/功耗均为NOT_TESTED |

完整验收流水线：2026-10-27T21:36:30.342114+08:00 至 2026-10-27T21:38:56.981151+08:00，exit0；115份命令回执。新包首次集成验收即通过，原始输出与预期失败负控全部保留。

### 如何选用

使用 [构建与调用说明](../optimizations/o2/integration/firstdot-v2-0f/package/c8/README.md) 和 [完整 ABI 合同](../optimizations/o2/integration/firstdot-v2-0f/package/c8/CONTRACT.md)。头文件提供：

~~~c
#include "selected_gemv_c8.h"
xs_c8_gemv_8x32(packed_ax, slots);      /* configuration reuse vdot */
xs_c8_gemv_8x32_rvv(packed_ax, slots);  /* explicit reuse RVV */
~~~

`XS_C8_GEMV_FORCE_RVV=1` 将默认入口也选为 RVV；缺省或0为vdot。仅接受最终展开为字面量0或1，切换后重编相关翻译单元。

必须是 **VLEN恰好128**、VS已启用和已验证的RV64/lp64d平台。输入为16字节对齐的288字节有符号INT8 A[8][32]||x[32]；输出是16字节对齐的8×16字节槽，共128字节，输入输出不重叠。每槽低32位为结果、高96位清零。输出不能当作紧密的 int32_t[8]。原向量状态/CSR效果保持，详见合同。

完整库仍有16个函数及未调用vdot代码；显式RVV不等于纯RVV镜像或跨平台自动检测。旧 firstdot 包与四尺寸默认均保持。

### 性能含义与下一步

本轮证明新编译期入口在被测试的调用对象和可重定位链接中没有新增包装代码，并正确复用了已验证的同一完整对象。它不是新的性能测试，也不证明任意最终应用的布局或周期都相同。

此前第25条矩阵数据继续有效：8×32配置复用273.00 cycles，firstdot282.25，最快同场RVV299.00，加速比1.095238×；每格12正式样本。本轮没有把这些数值重新标成新实测。

最小包目标已完成。下一步若接入实际应用或产生新的最终ELF，先固定新调用布局/窗口合同，再做受影响路径的全128位正确性、差分拒错/恢复与重放；性能比较须用同路径firstdot/RVV对照。纯宏别名不需要新增wrapper。如果新增wrapper、dispatcher或CSR保护，需新的控制流检查，不能借用旧唯一jal/ret门禁。其他尺寸的4×8/16×64控制漂移仍可独立只读归因，4×13保留RVV。

### 证据与工程记录

- [机器可读记录](../optimizations/o2/integration/firstdot-v2-0f/package/c8/record.json)；[GNU与静态结果](../optimizations/o2/integration/firstdot-v2-0f/package/c8/evidence/report.json)；[当前资格绑定](../optimizations/o2/integration/firstdot-v2-0f/package/c8/evidence/qualification.json)。
- [固定输入](../optimizations/o2/integration/firstdot-v2-0f/package/c8/INPUTS.json)；[原文审计/构建工具](../optimizations/o2/integration/firstdot-v2-0f/package/c8/verify_c8_package.py)；[主机测试](../optimizations/o2/integration/firstdot-v2-0f/package/c8/test_c8_package.py)。
- [矩阵原文重审](../optimizations/o2/integration/firstdot-v2-0f/package/c8/evidence/matrix-raw-audit.json)；[C调用原文重审](../optimizations/o2/integration/firstdot-v2-0f/package/c8/evidence/c8-raw-audit.json)。
- [归档索引](../optimizations/o2/integration/firstdot-v2-0f/package/c8/evidence/archive-reference.json)；`evidence/commands/`保留115份命令及文本日志，ar提取的二进制stdout保留在完整外部归档。
- 原始输出：/home/riscv/riscv-lab/software-import-20261026/c8-package-01。
- 外部完整归档：/home/riscv/riscv-lab/software-import-20261026/reviews/c8-package-final-archive-01。
- 记录ID：C8-PACKAGE-DIVFIX0F-CLEAN02-20261027-01，统一版本档案第27条。

初版Makefile烟雾测试通过后，审查发现assert可能被Python优化模式跳过，改为显式退出并验证三项门禁；修正前后材料均保留。没有降低旧运行门禁、更新旧对象哈希或覆盖历史失败。


## 18. C8接回普通C最终镜像等价（第28条）

**PASS：C8 软件包已真实接入原普通 C 夹具，最终可执行内容完全等价。** 依照事先约定，复用第26条同镜像的功能、NEMU/O2、bit100拒错、恢复与重放证据；本轮无需新增全核仿真。

执行者 @cc77-builder / Agent；操作ID 20261027-cc77-builder-c8-relink。生产RTL保持0f，旧四尺寸默认不变；未提交或上传GitHub。

### 接入内容

- 原主程序只把底层头的包含改为 `selected_gemv_c8.h`。
- 8×32 reuse vdot/RVV × 三数据集，共6个函数表项改用 `xs_c8_gemv_8x32` / `xs_c8_gemv_8x32_rvv`。其余42项、数据、期望值、顺序和校验不变，没有重新生成测试向量。
- 真正从 `libxs_gemv_c8.a(gemv.o)` 链入完整合格对象；SDK程序源目录没有gemv.S，对象目录没有绕过库的gemv.o。GNU依赖文件和link map确认实际包含SDK头、实际抽取库成员。
- 在全新输出中分别构建原源码复制对照和SDK接入程序，保留原AM/klib和链接次序；只有输出路径和记录链接来源的选项不同。

源码见 [source](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/source/)，重建和完整核验见 [README](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/README.md)。

### 三方等价结果

比较对象：原已通过全核的C8镜像 → 本轮原源码复制对照 → 本轮SDK接入版。

| 项目 | 结果 |
| --- | --- |
| 完整BIN | 三者全字节一致，均31,440字节 |
| BIN SHA256 | 56805506eb98b68269c73a3645d8f75dff73b697e30dec5f93ccc4716089ad34 |
| 入口 | 均0x80000000；ABI flags及ISA属性一致 |
| PT_LOAD | 同地址、权限、对齐及完整内容；file30,024B，memory31,440B，零填充1,416B |
| 装载节 | 所有SHF_ALLOC节的位置、大小、权限、对齐及内容一致，包括BSS |
| 函数 | 16个公共函数及启动/主程序等5个函数的地址、大小和机器码一致 |
| 测试表与数据 | 48条64字节调用记录与原计划逐项匹配；12组输入数组地址及内容一致 |
| GNU链接 | 无未解析符号；map与实际子命令证明使用SDK库成员 |
| 完整ELF原字节 | 不同；差异仅在.debug_info、.debug_line、.debug_line_str |
| 独立GNU复核 | 分别objcopy --strip-debug后，三份完整ELF全字节一致 |
| 去调试ELF SHA256 | 7e26e295fb020a63334026f768ed4825372266465b4e6008973de966fefc04ab |

调试节保存源文件/头文件路径及行号等信息，构建目录与头文件发生变化会改变这些记录。保留原ELF，没有通过删除调试信息来掩盖装载差异：主检查器已先完整比较装载内容和计划，去调试检查是独立补充证据。

原ELF SHA256：02159c7ef78cb31eb24cf706bf2974eadea313710563f235f2b11a7bb922de56。  
复制对照ELF SHA256：cfad14278ee4a3590de9bcbe7589b808fd91959156cef93ba92a78a90db0d99b。  
SDK接入ELF SHA256：f0ddf1167c961101e70f58cfd012ae788d2965324ad057aa4ade5af1de5bc42e。

### 检查器拒错与输入保护

7项负控全部被拒绝：实际ELF代码字节改坏、调用表改坏、启动入口改变、BSS大小改变、ISA属性改变、输入计划改变，以及真实GNU链接错误空库。另有只改调试字节的正控，确认不会将纯调试变化判为行为改变。错误镜像只用于主机检查，没有送入全核。

627项完整输入与封存运行证据绑定当前0f、EMU/NEMU及GNU工具。原33个矩阵进程和3个C进程的审计关系及全部封存输出树保持；本轮没有重复解析相同原始日志或伪造新PASS。当前操作保存了真实新GNU构建和最终镜像等价证据。

成功流水线：2026-10-27T21:59:40.771873+08:00 至 2026-10-27T21:59:43.182911+08:00，exit0。两次GNU构建，8份主流水线命令回执，另3份去调试GNU检查回执。流程首次通过，负控和原始文件全部保留。

### 已完成与未新增的结论

当前C8包已从“对象/可重定位链接合格”推进到“接回原可运行C程序、完整镜像等价”。原16函数、48例/两轮96正常调用（8×32占12例/24调用）的功能资格可明确复用；不是本轮重新执行这些调用。

新增EMU/NEMU/全核运行均为0。当前验证的是原测试夹具的包化接入，不是新的实际应用或LLM推理。没有新的周期、面积、STA或功耗测量。原273 cycles与1.095238×属于第25条性能矩阵，不是本C程序新测数据。

最小软件包接入闭环已完成。后续选择具体应用后再固定新的输入/调用路径/最终镜像合同；需要新性能结论时使用同路径firstdot/RVV及必要的集成前对照。另可继续4×8、16×64控制差异只读归因；4×13保留RVV。生产RTL和旧默认均不因本次接入改变。

### 证据

- [完整数据记录](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/record.json)，统一版本档案第28条：C8-RELINK-DIVFIX0F-CLEAN02-20261027-01。
- [比较与负控结果](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/evidence/report.json)、[实际接入link map](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/evidence/integrated/link.map)、[GNU独立复核](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/evidence/postcheck/result.json)。
- [原图/新图比较](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/evidence/integrated/equivalence.json)、[输入身份](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/evidence/qualification/report.json)、[执行回执](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/evidence/pipeline.command.json)。
- 原始输出：/home/riscv/riscv-lab/software-import-20261026/c8-relink-01。
- 完整本地归档：/home/riscv/riscv-lab/software-import-20261026/reviews/c8-relink-final-archive-01。
- 软件基点c823a8786e052c6e26f6915563c42b6d730dd8e3；硬件0f12df675378556670afd0dd2153f47fcb330610。当前状态为本地未提交材料，不能把基点SHA当作已包含本次修改的提交。


## 29. R5/G5 冻结与工程总验收（2026-10-27T22:58:45.908838+08:00）

状态：R5_G5_ENGINEERING_ACCEPTED_WITH_DECLARED_LIMITS。0f＋firstdot V2＋显式C8候选冻结；生产RTL与默认未改，未上传。

仅新执行o2-control-diagnostic 1次，原13项原文重验；组合功能/差分/O2覆盖及独立原文复算PASS。原clean-02全14项UTC容量FAIL保留；新选择集合严格UTC峰值3、新单进程单调包络峰值1。不是fresh14。

398生产源码、627个C8输入、31,440字节最终BIN和24,157冻结文件校验；35模型测试、11时钟门禁测试、FU/父级与T15旧归档复算通过。PPA证据审计不等于时序收敛；新性能/PPA/功耗/Fmax均NOT_TESTED。

[结果](../optimizations/o2/integration/firstdot-v2-0f/acceptance/RESULT.md) · [完整记录](../optimizations/o2/integration/firstdot-v2-0f/acceptance/record.json)。证据manifest SHA256：e5122e1c3eb5a4f25ca608ee87ed2e432b16758775d76ccb132599434e23137c。旧28条保留。



## 30. P1 split-input 最小迁入与 steady-d0 探针（2026-10-28T17:13:31.013620+08:00）

**P1_PROBE_HOLD**：9镜像静态与63主机检查通过；steady-d0负控/正常/独立重放及完整validation通过。各轮7组功能数据/312调用/8控制/2432退休vdot。两次共168计时窗，统计仅正常48正式普通窗；其余8镜像runtime NOT_TESTED。

同新窗口S-V **308.5**、最快观测S-R4 **340.5**、P-V **408.75 cycles**，观测比 **1.103727715×**。两顺序3%收益过线，但锚点605/605/626/606、跨度 **3.471074% > 1%**，停止扩大、不采用为升级。不能与旧273/299比较。

PPA沿用0f：FU17,298.246 / 父级284,614.946 μm²；nominal FU i2r1.190323、r2r1.163404、slack−0.268520ns；父级全局r2r3.261218、VDot r2r1.356106、最差已报告slack−2.393998ns。无新综合/STA/功耗/Fmax。

实际5个EMU进程（run01负控完成＋正常中断；run02负控/正常/重放），旧中断closure闭合、原文不改。只读分段21cycles锚点差主要为首个退休vdot接受前+19，不指定分支预测/缓存原因。完整原4窗、全部84窗、整数门槛与原始UTC/单调差在结果JSON及归档。

[完整结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/split-input-v1/RESULT.md) · [结构化结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/split-input-v1/RESULT.json)。
manifest：team/optimizations/o2/integration/firstdot-v2-0f/continuation/split-input-v1/evidence/20261028-p1/manifest.json，SHA256 **b4713776247348ed7c8c4745e5c1f5b46254272af307cdee11a2048011e687b2**，2622载荷；原29条保持。

P0 SOURCE_LOCK.current_sources 中两份 ledger 标记 historical_snapshot_reference，但冻结 identity.check 实际将其当作当前路径 live pins。此次在全部运行和最终完整身份复核结束后才追加第30条；原 ledger 字节保存在本归档的 *.before。追加后旧完整 identity 对当前工作树拒绝属于预期复现边界，旧资格应在独立历史快照中用归档的旧 ledger 与原冻结输入复核，不能恢复当前文件凑 PASS，也不修改 identity.py 或回写旧 SOURCE_LOCK。新增 RESULT/证据后重建完整源码清单也须另立新身份。

本轮未改RTL/默认、未commit/push。后续不自动新增实验。


## 31. P2 首vdot调用路径归因（2026-10-28T17:57:12.483077+08:00）

**只读派生分析完成，不是新性能测量。** 基于P1相同steady-d0原文，正常/重放84窗归因一致、7变异拒绝及独立复算通过。4个正式慢窗41/48/69/76额外redirect绑定0x800015ac的正常退休JALR；快/慢leaf首退休45–47/55拍，随后到首vdot接受均51拍，首vdot入队到接受均19拍。差值已在入队前，支持间接调用控制流预测纠正所在到达区间归因，不能称特定BTB或固定9拍纯恢复。

20个正式split RVV普通窗也发生同调用纠正，必须重新测对照。决定值得一次P1-R1窗外conditioning调用点隔离；设计已写、未实现/未构建/未目标测试。原1%/3%门槛、P1 HOLD、稳定0f+C8保持。P2其他依赖链/Jade未开展。

三指标沿用旧值：P1观察308.5/340.5 cycles、1.103727715×仍HOLD；FU/父级面积17,298.246/284,614.946 μm²；参考nominal父级全局r2r3.261218ns、VDot r2r1.356106ns、已报告最差slack−2.393998ns（全字段见JSON）。新性能/综合/STA均NOT_TESTED。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/callpath-p2/RESULT.md) · [修订设计](../optimizations/o2/integration/firstdot-v2-0f/continuation/callpath-p2/REVISION_PLAN.md)。manifest SHA256 c70c41682b00ace838031406e691d416fcbbe491eb8fa7f33fece61d0c671011；59个归档载荷。原30条JSON和Markdown前缀保持；无commit/push。


## 32. P1-R1 准备调用隔离（2026-10-28T20:57:21.546706+08:00）

**P1_R1_PROBE_HOLD**；新候选正确性 PASS_STEADY_D0_ONLY；性能探针 HOLD。实际EMU 4 个，后处理新增目标0。

candidate S-V 310.00、最快观测RVV S-R4，同场RVV/S-V 1.099193548×；1%锚点=False，正反3%收益=True。

仅steady-d0；其余8镜像NOT_TESTED，重放不追加统计样本，默认/RTL未改。PPA继承0f：FU/父级17,298.246/284,614.946 μm²；nominal父级全局r2r3.261218、vdot r2r1.356106 ns、最差已报告slack−2.393998 ns；本轮无新面积/STA/功耗/Fmax。

[完整结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/split-input-r1/RESULT.md)。manifest SHA256 4604a8c369617fe3ac0d55bd4bf3d78deba568fb0777a5213ff2d21768796a32。原31条逐条深等值、旧Markdown前缀保留；全部失败/partial原文封存。未commit/push。

保留0f＋firstdot V2＋显式C8稳定版；停止该候选扩大，先复核本轮完整失败/未过门槛原因，不自动重试。


## 33. P2 依赖链只读归因（2026-10-28T23:53:08.308949+08:00）

**P2_DEPENDENCY_READONLY_COMPLETE**。复用0f三数据/12正式chain256窗、3072条vdot/3060依赖边；ACCEPT→MOVE1、MOVE→RESPONSE1、RESPONSE→下一ACCEPT5，合计7拍。每窗1857=37+255×7+2+33。ROB提前分配不证明IQ驻留；COMMIT非WB，后五拍逐段为静态模型。

398生产源码/原EMU身份一致；15主机检查、Jade2个ROI拒错通过；根分别fresh复算最终派生逐字相等。无新增EMU/NEMU/综合/STA。旧chain256加速比2.929725×与0f面积/时序沿用，1601/1602只是条件模型，不纳入实测成绩。

决定仅GO_FOR_P4_G0_READONLY_REVIEW：研究VDot内部2→1且保留两槽/全部协议，先评审组合锥和同约束成本门槛。没有允许改功能RTL；不先重建观察器或改共享后端。稳定0f+C8保持、P1-R1 HOLD保持。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/dependency-p2/RESULT.md) · [下一步](../optimizations/o2/integration/firstdot-v2-0f/continuation/dependency-p2/NEXT_STEP.md)。manifest SHA256 a8366da492856270e0eecbed6ede4a6c672618f2516b69578967aeaaf08add01。原32条保留；未commit/push。

## 34. P4-G0 一拍算术／两槽弹性只读评审（2026-10-29T00:31:40.273005+08:00）

**P4_G0_READONLY_REVIEW_COMPLETE_CONDITIONAL_GO**。唯一候选为组合乘加、无旧P且R可接收则新包直写R，否则存P低32结果；两槽身份/异常/取消/反压与DIV协议保持。默认0f＋firstdot V2＋显式C8不变。

320组抽象状态、连续8笔一拍/II1、4类错误拒绝通过；根独立复算协议/PPA提取逐字节相等。不是RTL/父级/全核PASS。新加速比、面积、STA均NOT_TESTED，无构建/综合/目标运行。

历史0f chain256=1857拍、RVV/VDot=2.929725×，FU/父级面积17298.246/284614.946 μm²；nominal父级最差setup slack−2.393998ns。1601拍、13.7857%下降仅条件模型；少96数据保存位、裸DFF理想差434.112μm²不等于净面积节约。

预声明G2：FU＋5%、父级＋1%面积上限，五档局部Q增长≤5%，输出/控制保护、全路径覆盖；全部为工程筛选而非官网门槛。GO只指值得下轮启动G1，未实施/采用，未进全核。G1先说明RTL改法；完成FU/真实父级/DIV/SQRT后再决定G2。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g0/RESULT.md) · [合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g0/CONTRACT.md)。manifest SHA256 2b5b55cda9411a64dc7a294c169d0a16380b666509154d12a93f00d9be4c003e。原33条保持，无commit/push。


## 35. P4-G1 一拍算术／两槽弹性局部验证（2026-10-29T01:14:23.782861+08:00）

**P4_G1_LOCAL_VALIDATION_PASS**。候选默认关闭，仅VDotO2.scala/VDotElastic.scala两处生产改动，改前已说明。当前HEAD加未提交patch构成候选，不能用HEAD单独代表源码。

10022完整128位向量全部通过，无反压10022响应均1拍、10021个II1间隔；FU24215接受守恒，9负控；真实父级14组13468接受守恒，20负控；SQRT115场景、54取消后162立即空闲钟样本全部关闭、7离线负控。关闭模式原FU/父级及功能生成物对照通过，默认未设置及8种错误配置已验证。

新程序加速比、面积、STA均NOT_TESTED。0f历史参考2.929725×（chain256）、FU/父级17298.246/284614.946μm²、nominal父级最差setup slack−2.393998ns不能转授候选。一拍是局部协议延迟，非程序2倍提速。

首次parent-01因identity注入先命中stability而被严格门禁拒绝，保留FAIL；只修注入窗口、不放宽检查，重建parent-02全部通过。无生产功能修复，完整正向日志修前后逐字一致。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g1/RESULT.md)；manifest SHA256 48ebb60bcf92745577cc3b80bdeeb0109a04fd9b460f883e23ffacdbddd19033；patch SHA256 86b34d6117d8f36609e152847a0cda763b3aeb5411908194489e5be882a47243。旧34条保持。

下一步仅P4-G2同约束综合和五档STA，继续按G0门槛筛选；本轮未执行G2、未构建全核、未NEMU/应用性能运行、未commit/push。


## 36. P4-G2 同约束综合与五档STA（2026-10-30T12:31:24.863291+08:00）

**P4_G2_NO_GO**。47项冻结门槛中41通过、6未通过；不进入G3，不采用，稳定0f行为＋firstdot V2＋C8保持。G1候选源码445份不变，本轮RTL修改0；HEAD加原未提交patch，不能用HEAD单独代表候选。

| 三指标 | 0f基线 | P4候选 |
| --- | ---: | ---: |
| chain256加速比 | 历史2.929725× | NOT_TESTED |
| FU面积μm² | 17298.246 | 18322.878（+5.923329%） |
| 含FU父级面积μm² | 284614.946 | 285241.642（+0.220191%） |
| nominal FU最差setup裕量ns | -0.268520 | -0.790381 |
| nominal父级最差setup裕量ns | -2.393998 | -2.337809 |

FU少96 DFF但多737 MUX，净面积+1024.632μm²；完整身份保留，主要新增选择位于R控制/perf写入锥。两模式4次映射、40档STA执行（20原组＋20覆盖），旧14×5组和候选70补充报告完整。两边界旧成本数值精确复现；全部失败门槛及五档Q见结果，未用改善项冲抵失败。

首次off-fu-coverage-01分析别名错误被严格断言拒绝，保留旧源与失败；仅改工具，新02通过。无全核/NEMU/性能或功耗测量；局部Q非整核Fmax，1ns负裕量不冒充时序闭合。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2/RESULT.md) · [完整逐项](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2/screening.json)。manifest SHA256 ff4224cfcd193e78b9c221864220c005d9f99f0dc818698e9a0491f27644754c。旧35条保持，无commit/push。

下一轮仅建议P4-G2R0只读成本复核，按全部失败项判断一次最小修订价值；不自动改RTL或进入G3。

## 37. P4-G2R0 R元数据／父级ready只读评审（2026-10-30T13:03:20.575600+08:00）

**P4_G2R0_GO_ONE_BOUNDED_REVISION**：只表示值得下一轮做一次元数据选择的最小修订。当前P4-G2仍NO-GO，47项41通过／6失败原样保留，不进入G3、不采用。稳定0f＋firstdot V2＋C8保持。

FU的790位R元数据中，784位各有两级MUX（1568个不同实例）；真实父级595位中593位相同。建议仅在一拍分支中把ctrl/perf写入改为完整的hold/move/directR三路互斥表达，其他数据、状态、ready与DIV均保持。

两个手工等价单元构型的毛面积节省208.544／625.632μm²，未包含控制/缓冲/映射，不是新综合成绩或上下界。父级ready仍需五档分别恢复5.243／5.243／5.243／5.535／6.844ps；共享负载分析不能保证改善。2048项主机位逻辑检查与4类错误反例、独立重放通过，仅为二值选择逻辑，不代替RTL验证。

| 三指标 | 本轮新修订 |
| --- | --- |
| 程序加速比 | NOT_TESTED |
| FU／父级面积 | NOT_TESTED |
| STA／时序 | NOT_TESTED |

旧G2实测仅作为归因参考：FU18322.878、父级285241.642μm²，nominal父级slack−2.337809ns／ready0.303064ns，候选加速比未测。0f历史chain256为2.929725×，不能转授新修订。

41项输入与445份候选源码未变，原patch SHA256 86b34d6117d8f36609e152847a0cda763b3aeb5411908194489e5be882a47243；生产RTL修改0、新EDA/全核/NEMU运行0、无commit/push。旧36条保持。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2r0/RESULT.md) · [最小修订合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2r0/REVISION_CONTRACT.md)。manifest SHA256 2c09801af8eeb90e6f17060300f82a47b2f23e1c1d29150e36b39cfc8bb3c053。下一轮仅建议P4-G2R1局部实现与验证，另轮再做原G2成本筛选；任一原门槛失败停止该次修订，不自动扩大。

## 38. P4-G2R1 R槽元数据最小修订局部验证（2026-10-30T13:29:29.086733+08:00）

**P4_G2R1_LOCAL_VALIDATION_PASS**。相对G1仅改VDotElastic.scala一拍分支的R ctrl/perf为完整hold/move/directR三路互斥选择，加恰一断言；数据、状态、ready、DIV和默认关分支不变。改前已说明；默认关闭、不采用、未进入全核。

| 本轮资格 | 实测 |
| --- | --- |
| 完整128位 | 22定向＋10000随机全部通过；10022一拍响应、10021个II1间隔 |
| FU | 24215接受守恒；9观察负控拒绝 |
| 真实VFEX4 | 14组、13468接受守恒；完整VPU/perf/异常，DIV切换/反压/取消/身份，20观察负控拒绝 |
| SQRT/双lane | 115场景；54取消后162立即真空闲钟样本全部关闭；7离线负控拒绝 |
| 默认关/拒错 | FU/父级重新通过，4/16负控；4/56模块严格诊断规范化后逻辑一致；默认未设置成功及8种错误配置拒绝 |
| 程序加速比、面积、STA | **全部NOT_TESTED**；不转授旧G2数值 |

五份新正向日志与G1逐字一致，非性能测量。生成夹具中常量元数据保留变化：FU的reg声明40/1354位→98/1994位，父级102/2580位→129/2607位；不是映射DFF/面积，成本轮需核查。

首轮汇总因“非VDot生成HDL都应相同”的过宽假设FAIL，完整留档；仅修分析方法，生产源/原checker不变。确认传播差异仅VDotElastic/ExeUnit/测试顶层，ready/busy/状态/断言片段经3个输入探针重命名一致，三个ClockGate连接一致；不声称整个候选父级生成图等价。

HEAD 10b71ad4bff25cd2070e775c74a4717b01602f75＋完整补丁SHA256 9327fa6f472f1869a41d04ceb515a7f8b76bae338279719568512571f88610d5；本轮增量SHA256 fb85300a4600318c36964bc77518be3560a6c7ce50909272343744b17e602023。源码/配置/实际新二进制/日志均绑定；313冻结输入和444其他源码未变。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2r1/RESULT.md) · [完整数据](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2r1/aggregate.json)。manifest SHA256 75351b6eef5cedf28e976e592b9610ad0c0aecf3466e847cefc99a866c0ca412（938条，776去重gzip）。旧37条及原G2六项失败保留。

下一轮先FU同约束综合＋五档STA并核查常量元数据实际映射，合格后才做真实父级；原47项门槛不变。本轮无综合/STA/全核/NEMU/commit/push，稳定0f行为＋firstdot V2＋C8保持。

## 39. P4-G2R1 成本筛选（2026-10-30T14:41:16.082152+08:00）

**P4_G2R1_COST_NO_GO**；原47项 37 PASS / 10 FAIL。FU通过后才运行父级；默认0f＋firstdot V2＋C8保持，未采用。R1程序加速比NOT_TESTED。

| 本轮三指标 | R1实测 | 说明 |
| --- | ---: | --- |
| 程序加速比 | NOT_TESTED | 不借用0f历史成绩 |
| FU面积 μm² | 18086.936 | 相对0f +4.559364% |
| 含FU父级面积 μm² | 285473.062 | 相对0f +0.301501% |
| nominal FU最差slack ns | -0.776319 | 布局前局部参考 |
| nominal父级最差slack ns | -2.235609 | 负裕量保留；非整核Fmax |

[全部47项、五档及历版对照](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2r1-cost/RESULT.md)。源码补丁 9327fa6f472f1869a41d04ceb515a7f8b76bae338279719568512571f88610d5；证据manifest 4ad0eba39ad487f15e7b4dfa8c8dfaae5331b57bd05921d4f9bfc1a5509d3b9d。常量位实际保留逐位归因，全部计入面积与STA；原数值门槛未改，分析工具两次失败和旧G2六项FAIL保留。旧38条不变；RTL修改0，全核/NEMU/性能0，无commit/push。

下一轮：开始 P4 收口后的只读路线评审：保持 0f＋firstdot V2＋C8，依据 P4/R1 的完整成本结果和现有应用瓶颈，判断还有没有值得启动的最小优化。不继续试改 P4、不修改 RTL、不构建全核、不上传 GitHub，给出 GO/NO-GO 和下一轮指令。


## 40. C8 8×32分段归约：GNU与宿主资格（2026-10-30）

记录C8-DEFERRED-HOST-20261030-01，状态**C8_DEFERRED_HOST_PASS_GO_D0_PROBE**。只到dataset0公平探针，不采用候选；当前0f＋firstdot V2＋C8保持。
新加速比/面积/STA均**NOT_TESTED**，目标EMU/NEMU为0。不得把本条称为全核验证通过。
GNU实际叶：vdot 164→156指令、13→5配置、656→624B；RVV112→108、13→9、448→432B。架构向量寄存器使用20→28、22→30；无spill/额外move。
最终attempt-03：310输入×3入口状态×4实现＝3720有限模型执行；29760完整128位输出槽、59520逐dot独立完整128位oracle核对，4原语、39负控、9对象/ELF/BIN重复构建字节一致。
三次宿主尝试原样保留；只统计最后一次独立覆盖，不把重复用例倍增。真实C引用与静态链接通过，夹具不是AM运行程序。
候选汇编SHA256 bdd86ba4552cca7f48865fa5740dc9c855152b4649407ef6e497d64d70691807；对象2a5b5dc774f3acc343eea2ec69fd08fa2ffe9093be9bfbd03dbf3095760b4157。
完整版本/工具/合同/负控/证据见[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-v1/RESULT.md)及配套JSON；下一轮按[冻结探针合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-v1/PROBE_CONTRACT.md)，先构建实际AM及observer适配，再最多5串行目标进程；本轮未启动、未改RTL、未上传。

## 41. C8 分段归约 dataset0 公平探针（2026-10-30）

**HOLD_TEST_HARNESS_BUDGET_REVIEW，不采用候选。** 真实AM A/B、静态及宿主负控、首条NV的bit100实际拒错通过。正常恢复没有完成，没有合格性能窗口。

| 新三指标 | 结论 |
| --- | --- |
| 加速比 | NOT_TESTED |
| 面积 | NOT_TESTED，RTL未变 |
| 时序 | NOT_TESTED，未做STA |

A/B各53,572B，所有ALLOC布局相同，仅NV/NR叶代码不同。静态窗口instret OV/NV/OR/NR＝175/167/123/119；不能当作实测cycles。实际C校验函数84组、177,408次宿主扰动；退休/跳转/计数及阈值负控通过。

2/5个目标进程：A拒错24.906965秒PASS，PC0x80004854、word0x0388000b、vd0、bit100；A正常534.868194秒后主动SIGTERM（−15），后三项NOT_TESTED。原因是本Agent把15项校验器负控重复放进84次目标功能调用，额外1,260项自检导致明显前序开销、预算预检不足。80,794是前两条不同调用首dot提交间隔，**不是叶延迟或加速比**。主动停止未触发硬上限，不写成超时，也不据此判断候选性能失败；原campaign NO_GO退出门禁保留，候选决定HOLD。

1%锚点、逐窗控制精确相等和正反3%收益均未实际验证，原门槛不变。下一轮仅先修框架重复自检与预算审计，保留84功能调用及完整检查、原四叶和计时窗口；新镜像/新预算重新开始，不能续借本轮部分资格。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-d0/RESULT.md)及配套JSON；manifest SHA256 c94290a60dcf121420ab0e59cd2b9b67ddf561c6ecf7012a5625ab9f009db834，119条归档。5298运行输入、926保护文件、src补丁9327fa6f472f1869a41d04ceb515a7f8b76bae338279719568512571f88610d5复核未变。旧40记录保持，无RTL/新核/EDA/commit/push。

## 42. C8 分段归约 dataset0 公平探针 R1（2026-10-30）

**HOLD_ANCHOR_AND_GAIN_SCREEN，不采用、不扩围。** 测试框架修复后，84次功能调用、32个计时窗口、完整128位/CSR/寄存器/范围检查、NEMU差分、退休与O2身份审计通过；原1%锚点及正反3%收益门槛失败，实际2/5串行进程后自动停止。

| 实现 | 正向均值 cycles | 反向均值 cycles | 全部正式均值 cycles | 每窗instret |
| --- | ---: | ---: | ---: | ---: |
| 原C8 vdot OV | 273.50 | 274.00 | 273.75 | 175 |
| 分段归约vdot NV | 273.00 | 273.00 | 273.00 | 167 |
| 原C8 RVV OR | 301.00 | 301.00 | 301.00 | 123 |
| 分段归约RVV NR | 278.00 | 278.00 | 278.00 | 119 |

**以上仅A图诊断观察，不是公平资格已通过的性能成绩。** OV四锚点273/274/274/268，跨度2.238806%>1%；OR四锚点301，跨度0%。NV正反分别仅比OV少0.183%/0.365%，均未达3%。原始最快RVV/NV＝278/273＝1.018315×，不得排除更快NR改用OR分母。B校准、A/B重放、跨镜像逐窗控制精确相等均NOT_TESTED，保留原门槛。

| 新三指标 | 资格 |
| --- | --- |
| 合格加速比 | NOT_QUALIFIED；1.018315×仅诊断观察 |
| 面积 | NOT_TESTED；硬件保持0f |
| 时序 | NOT_TESTED；未做STA/新核构建 |

R1仅移出目标端1260重复校验器自检及84恢复复检，validate调用1460→116；84功能与32性能调用不变，宿主177408扰动和1260自检保留。新旧A/B共24项叶/计时/功能入口的机器码、地址、长度逐项相同。新A/B各52868B，仅NV/NR叶666字节不同；原53572B镜像和主动停止失败记录不覆盖。

bit100拒错PASS（PC0x80004854、word0x0388000b、vd0），单调耗时32.307366s；A正常exit0，3065.826606s，O2接受/移动/响应/入队/提交各1856。实际4线程CPU4–7；未超硬限、未人工停止、未重试。正常单调时间与UTC显示差211.463253s，原因NOT_ATTRIBUTED，两者保留；7200s预算只按冻结单调时钟判断。新增DIV/STALL/KILL覆盖为0，不借本次扩张硬件资格。

HEAD 10b71ad4bff25cd2070e775c74a4717b01602f75、原src补丁9327fa6f472f1869a41d04ceb515a7f8b76bae338279719568512571f88610d5保持；固定5583输入、1179保护文件复核未变。完整镜像/工具/合同/轨迹/时钟及已知显示路径说明见[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-d0-r1/RESULT.md)和[JSON](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-d0-r1/RESULT.json)。归档manifest SHA256 bed28543a868b72af5fccc69f51055274a5ca7ebafab4081cc9f637beb247230，141载荷；旧41记录及失败保持。

下一轮只读归因：解释末OV锚点6周期差异与NV/OV、NR/OR等待和依赖；不自动新开EMU、修代码、改RTL、构建新核或上传。当前仍0f＋firstdot V2＋原C8。


## 43. P3 FP32→QKV最小迁入与宿主门禁（2026-10-30）

**P3_HOST_PASS_GO_0F_ADAPTATION_AND_BUDGET_ADMISSION；HOST_ONLY。** 供体固定ffd668bf1bc80850d382f514d13bb00316c85582；生产保持0f＋firstdot V2＋原C8，不采用P3为默认。

| 项目 | 实际值／资格 |
| --- | --- |
| 源闭包 | 143项＋2项API；19历史Git对象；最小运行包8文件25140B |
| GNU最终镜像 | ELF 50004cbc4436c8bd52edfae198527be48c224fb1baffc1e9986038e8bc3109f1；BIN fc43caac20b07a6241b20d88fc37e1acc530cb1e1eea89d0b6bef70e4c76c459 |
| 构建/对象/链接/搬移 | PASS；6函数实际字/重定位、完整只读数组和路由、字段布局、去重、两个普通C链接入口、独立路径及包替换重链相等 |
| 完整数值 | 864量化元素/27尺度；2真实位置×2方法×3投影＝3456直接输出比较，1728唯一参考；另4 wrapper完整路径 |
| 完整128位 | 124416笔dot写入、192次slotstore逐笔独立检查，低32/高96均验证 |
| CSR/ABI/负控 | 宿主静态和模型PASS；5迁入负控、11机器字变异、14值/CSR/ABI负控、5类非法域；14策略合成测试 |
| 新加速比 /面积 /STA | NOT_TESTED /NOT_TESTED /NOT_TESTED |
| 当前硬件、旧成绩 | 没有改变0f；供体3.473%不转授；没有把新host指令数当cycles |
| 目标执行 /全核构建 | 0 /0；真实fflags/异常/DiffTest和新应用周期NOT_TESTED |
| 下一步 | GO仅进入0f身份/观察器/3%selector适配和预算准入；最多3进程合同已给出，NOT_READY_TO_RUN |

有效数值轮为attempt05；attempt01挂钩/变异定位失败、attempt04身份NUL构造失败保留。算法与GNU镜像未变，02/03早期PASS不替代最终身份门禁，不累计重复覆盖。两项FP机器字负控有提前拒绝限制，FP ABI敏感性由fs0/fs11值负控单独证明。

当前源码HEAD 10b71ad4bff25cd2070e775c74a4717b01602f75，local/zjhwork-integration-20261024，原src补丁9327fa6f472f1869a41d04ceb515a7f8b76bae338279719568512571f88610d5；639保护文件与7运行时身份不变。记录人为@cc77-builder / Agent，operation 20261030-cc77-builder-p3-qkv-host。本轮未提交、未上传。

证据：[P3结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-qkv-v1/RESULT.md)、[JSON](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-qkv-v1/RESULT.json)、[manifest](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-qkv-v1/evidence/manifest.json)、[下一轮合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-qkv-v1/PROBE_CONTRACT.md)。原始输出software-import-20261026/p3-qkv-host-20261030-01。预算18M/7200只为硬上限，缺可完成性证据不能开跑；旧42记录及失败保持。

## 44. P3-0f探针适配与预算准入（2026-10-30）

**HOST_ADAPTER_PASS / HOLD_BUDGET_NOT_DEMONSTRATED；HOST_ADAPTER_ONLY。** 保持0f＋firstdot V2＋原C8；P3不切默认。复用上轮冻结ELF/BIN，0个目标进程、0次核构建、0项RTL修改、0次GitHub写入。

| 项目 | 结果 |
| --- | --- |
| 0f身份 | 3519项物理运行/构建pins、2723生成物；另核对429实际硬件源；本轮冻结4303项 |
| 真实配置 | EMU_THREADS=1，O2两槽、T13/O2开启；CPU4–7/4个OS线程不是四模型线程 |
| 离线整规模观察器 | 155521笔合成提交，62208笔计时退休与O2 cycle/ROB/PC绑定；24CSR＋24计数入队 |
| 真实旧日志兼容 | C8原32窗、1856提交、512计时绑定重新解析PASS；不是新P3运行 |
| 门禁与负控 | 最终tests-05共22组通过；包含14个1%/3%整数策略用例，失败即停、回执、首bit100绑定及重放拒绝 |
| 解析器开销实测 | 合成293661026B stderr＋802B stdout，183.473969宿主秒，峰值6664052736B（6.206GiB） |
| 目标预算 | HOLD。旧C8吞吐498.287guest cycles/s仅用于情景估算；缺完整P3周期、吞吐/资源上界 |
| 新加速比 / 面积 / 时序 | **NOT_TESTED / NOT_TESTED / NOT_TESTED** |

冻结ELF 50004cbc4436c8bd52edfae198527be48c224fb1baffc1e9986038e8bc3109f1；
BIN fc43caac20b07a6241b20d88fc37e1acc530cb1e1eea89d0b6bef70e4c76c459。
14边界/42投影/17量化/5049标量除法、主机审计14977比较等成本全部保留。正式FR/TA/FR/FR/TA/FR顺序、1%锚点和最慢TA相对最快FR少3%不变。合成cycles不记作硬件性能，供体3.473%不转授。

7200秒只是正常单进程硬限；按旧吞吐350万guest cycles约7024秒、400万约8027秒，均是条件情景，不能据此宣称P3必超时或必完成。日志点估计约761MB不是上界，真实解析峰值也未确定。budget_admitted=false，next_role=null，正式三项全NOT_STARTED，不自动校准/加时/重试。

保留identity-01误读模型线程数、tests-01模块重名、tests-02语法、tests-03负控末行截断、tests-04错误流无效变异及source-map定位失败；最终通过没有改原合同或输入。
3615保护文件、HEAD 10b71ad4bff25cd2070e775c74a4717b01602f75和原src补丁不变，前43记录保持。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-0f-adapter-v1/RESULT.md)、
[JSON](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-0f-adapter-v1/RESULT.json)、
[manifest](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-0f-adapter-v1/evidence/manifest.json)：
3673e11b8aa2504f3d858417c025d233bae1bfe8360ba2104c6630b6a3fd6c6b，102载荷。
下一轮建议另立独立短校准合同，仅在用户另行指令后最多2串行/2700秒获取吞吐和日志进度；不能自动进入正式探针，详见[NEXT_STEP](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-0f-adapter-v1/NEXT_STEP.md)。

## 45. P3独立短校准（2026-10-30）

**HOLD_THREAD_LIMIT_NO_NORMAL_CALIBRATION。** 1/2个目标进程，负控24.422046秒后整组线程峰值5>4，SIGKILL/exit−9；正常2400秒未启动。不是300秒超时，也不是候选数学失败；无自动重试、加时或正式探针。

| 项目 | 实测或资格 |
| --- | --- |
| 首指令及注入 | PC0x80001d44/word0x0388000b/vd0，O2 cycle12580；bit100标记已出现 |
| 完整拒错 | 未取得规范mismatch/ABORT/exit1，NOT_PASSED |
| RSS / 原始日志 | 77725696B；stdout961B＋stderr38039B |
| 线程 / 清理 | 5>4；检测到清理0.116474秒，存活组成员0 |
| 正常吞吐、完整QKV周期 | NOT_MEASURED |
| 7200秒预算 | HOLD_NOT_DEMONSTRATED |
| 新加速比 / 面积 / 时序 | NOT_TESTED / NOT_TESTED / NOT_TESTED |

另保留 **FAIL_NEW_RUNNER_SOURCE_FREEZE_INCOMPLETE**：context通配导入覆盖HERE，导致新运行器/测试/合同6项未入预冻结；镜像和EMU/NEMU原哈希不变，但不能授完整运行资格。原freeze不改，事后源码清单不替代预冻结。

10秒、20秒快照只有EMU自身4线程；触发瞬间缺PID/TID明细。固定DiffTest源码错误打印含system/popen辅助进程，是候选机制，尚未证明第5个的实际身份。原有界门禁保持，不排除辅助进程或回填PASS。8真实宿主机制＋8门禁用例通过，但未覆盖源路径遮蔽缺陷。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-v1/RESULT.md) · [完整JSON](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-v1/RESULT.json) · [证据manifest](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-v1/evidence/manifest.json)。
保持0f＋firstdot V2＋原C8，前44条不变。下一轮先修源冻结和触发观测，仅宿主验证，按[NEXT_STEP](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-v1/NEXT_STEP.md)；本轮不再运行EMU/NEMU、未改RTL/构建核/上传。

## 46. P3校准运行器R1宿主修订（2026-10-31）

**HOST_GO_SINGLE_CPU_CALIBRATION_CANDIDATE，HOST_TOOLS_ONLY。** 生产0f＋firstdot V2＋原C8不变，本轮0次EMU/NEMU。

| 项目 | 实际结果 |
| --- | --- |
| 路径/源冻结 | 显式pc_context.CAL_HERE，8必需源码/合同，4324项测试前冻结；旧V1错误清单及缺项/漂移均拒绝 |
| 触发快照 | 保存当次PID/PPID/PGID/SID、进程/TID出生ticks、命令/亲和；先持久化再回收，首原因保留 |
| 宿主测试 | 14组PASS，13实际宿主进程，目标0 |
| 四核运行时基线 | 主运行时4线程，峰值4 |
| 四核诊断夹具 | 主运行时4＋子sh1＝5，THREAD_LIMIT正确停止，触发PID/TID明细完整 |
| 单核CPU4诊断 | 两次正常结束，整组峰值均3，不超过原4线程上限 |
| 新加速比 / 面积 / 时序 | NOT_TESTED / NOT_TESTED / NOT_TESTED |
| 7200秒预算 | HOLD，尚无正常QKV吞吐 |

夹具仅链接原始冻结verilated.o/verilated_threads.o/spikedasm.o，不含VSimTop或NEMU；诊断占位程序仅用于宿主可控采样。已证明这一宿主机制，未追溯证明旧目标第5个线程身份。模型threads()=1与运行时按亲和建立的宿主池分开记录。

预算仍CPU允许4–7、整组4线程（含助手）、RSS12GiB、日志合计2GiB、300/2400/2700秒和各100万guest。建议launch_cpus=[4]，属于原允许子集；不增加预算、不豁免shell。新运行wrapper和授权须列入下一次预冻结，当前没有目标启动CLI。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-r1/RESULT.md) · [JSON](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-r1/RESULT.json) · [manifest](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-r1/evidence/manifest.json) · [下一轮](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-r1/NEXT_STEP.md)。
4540既有保护输入及原RTL补丁不变，前45条/上轮两项失败保留，无commit/push。

## 47. P3单核亲和有界校准（2026-10-31）

**TARGET_PREFIX_ONLY / HOLD正式预算**；稳定0f＋firstdot V2＋原C8不变。HEAD 10b71ad4bff25cd2070e775c74a4717b01602f75，记录ID P3-SINGLE-CPU-CALIBRATION-20261031-01。

| 项目 | 实测 |
| --- | --- |
| bit100拒错 | PASS，23.401695秒，12586 guest，exit1，首PC/word/vd/高位mismatch绑定 |
| 正常校准 | INCOMPLETE，1599.320037秒，999988 guest，原生guest限额，exit0不等于GOOD TRAP |
| 正常前缀吞吐 | 625.258220 guest cycles/秒 |
| 覆盖 | 31105条vdot；首RVV窗开始855738周期，1窗启动/0窗完成，2次CSR起始采样 |
| 冻结ELF前缀 | 65288退休记录、67782/110580条首窗动态指令吻合；仅进度资格 |
| 资源 | CPU4，两项线程观测峰值1；正常RSS81133568字节，日志73290448字节；组清理完成 |
| 两项目标墙钟 | 1622.721732秒，最多2串行，无重试/正式探针 |
| 7200秒预算 | HOLD；按前缀速率约容纳4501859周期，完整14调用无可信耗时上界 |
| 新加速比/面积/时序 | NOT_QUALIFIED_NO_COMPLETE_PAIR / NOT_TESTED / NOT_TESTED |

4502项预冻结、5项本轮必需源、10组宿主门禁通过；4487旧保护文件与RTL补丁保持。事后前缀核对的list/tuple实现失败已保留并修正，0次目标重跑。旧46条及全部失败不覆盖。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-single-cpu-calibration-v1/RESULT.md) · [合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-single-cpu-calibration-v1/CONTRACT.md) · [证据manifest](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-single-cpu-calibration-v1/evidence/manifest.json)，SHA 695b2db238836b7089839e20c1b55269d0e9a3993c0bcdb38041623c84be0ea3。
