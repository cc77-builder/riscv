# C3-HF 第21条数据档案增量计划

此文件只规划台账字段；成本运行尚未结束，不写候选采用或否决结论，不修改固定成本脚本、pins、共享台账、路线或计分板。后续由root通知实际成本和独立审计结果、最终manifest位置后，再写三份台账文件。没有推送。

## 1. 已核对的现有结构

MAIN/team/docs/version-data-ledger.json 使用 schema_version=1，records准确20条；第18条C2-local、第19条C2-cost、第20条C3-G0。第20条仍是只读评审与抽象模型，candidate_commit=null、真实RTL/FU/父级/成本/全核/cycles为NOT_TESTED；不得回填新C3-HF资格。

机器台账的相关容器：
- hardware_identities当前13项，新增C3-HF，不修改已有身份。
- source_tables当前25项，新增c3_hf来源，不重建旧表。
- source_pins最早58项原字典；archive_pin_refs当前11项，只追加新manifest路径。
- c2_local_source_pins 32项、c2_cost_source_pins 20项、c2_cost_post_archive_pins 5项，以及c3_g0_source_pins 7项，全部原样保留。
- historical_document_snapshots 2项保存AGENTS/route旧内容；不能把当前文件新hash覆盖历史pin。

配套sources.json最早files为58条列表，另有c2_local_sources、c2_cost_sources、c2_cost_post_archive_pins、c3_g0_sources及各manifest字段。不能为“统一格式”重写旧列表/字典混合结构，只新增c3_hf_sources及新manifest字段。

检查时三文件身份：
- version-data-ledger.json：ead9a206c8e2d8f4a8971e9b5e615cc9e9e286b621a201ba9f74da6a928200d7，4700676字节。
- version-data-ledger-sources.json：8cef7ad08b0e73f4d58b94037f96d28fc66ac66cb1425df9cbd67dedb79375f2，33850字节。
- version-data-ledger.md：3ba85586f294c842decabd0c748f7a0828049efef659a77778e17ba7d241a638，34441字节。

实际修改前重新读取、与这些身份核对；若被其他工作正常更新，先恢复合并上下文，不覆盖。真正保存前备份三文件到本轮独立台账审计输出，后续差异核验以该快照为准。

## 2. 建议第21条唯一记录

永久record_id建议C3-HF-20261025-01，label为“C3-HF 单点浮点DIV保持位置位候选：局部验证与同约束成本筛选”。一条记录内分别保存local和cost子对象/执行阶段，不把FU拍数当全核窗口。

固定身份：
- candidate_commit/source_commit：77d0a1228f0da7d584d5c7375b404dcda9763cf3。
- ExeUnit SHA：150baa7c78aa8948ff0f4fb771912f7d2058aaa802a0853ee99ea3a2dc0bb9b7。
- baseline_commit：0f12df675378556670afd0dd2153f47fcb330610。
- identity_ids包含DIV-fix0f与新增C3-HF；source_ids包含新增c3_hf。
- source_snapshot_manifest_sha256指实际新源码pins，不沿用C2旧值。
- contract_refs绑定c3-hf/CONTRACT.md与c3-hf/cost/CONTRACT.md，分别存SHA。
- 新EMU/NEMU/性能镜像本轮未使用则NOT_TESTED；不能将0f EMU SHA填作C3-HF。
- 局部仿真二进制、生成RTL、编译器及测试数据的身份按实际runner/artifacts记录，明确它们不是全核EMU。

verification分别记录numeric_rtl、fu、real_parent、supplement、source_scope、control_monitor、negative_controls、independent_local_audit、area_sta、independent_cost_audit；全核/NEMU、cycles、power、fullcore_fmax、成员人工复现未执行则NOT_TESTED。area_sta用“报告有效且筛选通过”或“报告有效但筛选拒绝”，不要只写PASS掩盖拒绝。

局部数值只从本轮新输出读取：
- 独立FU10022向量、完整128位、实际拍数/接受/响应/取消/复位丢弃及4负控。
- 原父级13组的实际拍数、接受/响应/取消/复位、严格取消空闲窗/采样/多余脉冲及16负控。
- supplement本轮真正完成的attempt（当前root称supplement-02），6组/115场景、实际SQRT/双lane偏斜/TE0动态复位与控制观察数、7离线负控。
- C3新增P_F=fire、hold建立/释放、原E保持的实际监视回执。
- 测试计数有交集，不相加为唯一RTL覆盖率；Python抽象状态数与RTL拍数分开。
- 首轮测试/脚本基础设施失败、补充失败attempt及修复后的新attempt均保留，不填旧C2 PASS作为新数据。

成本值只从最终screen和独立原文复算读取：
- area_before/after/delta及≤284899.560946门槛和判定。
- control_before/after/delta及≤1.737526ns门槛和判定。
- before/after三状态busy、FP hold、INT hold的语义→本版DFF D映射，以及五档全部arrival/slack/真实起止点；没有owner查询，不只列最大值。
- DFF总数、cell_count、unknown_cells、ICG数；表明总DFF变化是实际映射结果，不能强行预填17172。
- 五档45条唯一比较，完整before/after arrival/slack/startpoint/endpoint、delta、pass；path总计/通过/失败和所有失败原因。
- 原非负ICG slack是否保持、numeric cost gate是否打开；该字段与最终采用、实际全核运行分开。
- 工具/Liberty/源/生成RTL/网表SHA、端口/约束及baseline manifest SHA。
- cost campaign、standard STA、定向STA的实际命令/退出码/起止时间。预期1次新综合、5常规、10定向，但记录必须按实际receipt计数；不把planned写成executed。

决策：
- 若任何冻结实质门槛失败：C3_HF_SCREEN_REJECT_NOT_ADOPTED_KEEP_DIV_FIX0F；全核/cycles保持NOT_TESTED，关钟试验结束。
- 若成本全过但未跑后继：C3_HF_COST_PASS_AWAIT_FULLCORE_NOT_ADOPTED；不能提前写全核PASS或最终采用。
- 后续确有新全核/周期结论时另追加第22条等，不回填本条当时NOT_TESTED。

## 3. 证据引用与源pin新增

新增c3_hf_source_pins和sources.json.c3_hf_sources，与旧容器分开；内容至少包含：
- candidate.json、local-result.json、cost-qualification.json与合同；
- fu/parent/supplement真实runner.status、source/artifacts/run.env、result.log及最终checker/monitor/replay/negative回执；
- 独立source review、局部总audit；成本脚本freeze与实际qualified输入；
- cost-01的preflight/inputs/dependencies/campaign、生成/综合/STA summary；
- screen-01/result、state、before/after-state-registers、各profile paths/queries；
- 独立成本audit及原文复算，最终RESULT和证据manifest。

每个pin保存来源路径、SHA、字节数；归档后同时记录archive_manifest与对应raw/stored路径，避免只有个人绝对路径。record.evidence_manifest_path/raw_evidence_location与manifest SHA必须实际存在并校验后填写，未知时不要写假64位或永久PENDING_SEAL。最终result_path/result_sha也需等root报告冻结。

root最终证据archive若包含台账增量草稿，不再把manifest自身或最终台账文件纳入自引用哈希循环。可先封存原始运行证据，再追加最终台账；台账自检回执放post_archive范围，不能为增加台账回执修改已封存manifest。

## 4. Markdown如何更新而不改历史结论

- 顶部概述准确更新到C3-HF本轮实际结论；“C3-G0仅建议尚未实施”明确为第20条当时状态，不让总述继续误导当前事实。
- 总记录数20改21；第2节追加C3-HF新行，第7节追加新硬件身份；旧行和旧章节保留。
- 末尾新增第11节，区分真实局部资格、成本筛选与NOT_TESTED层级；列关键结果及45条完整比较或指向JSON的完整数据，不把拒绝藏起来。
- C3-G0章节仍保留candidate_commit=null/未实施的历史描述，不将旧C2-local的PPA NOT_TESTED改为通过。
- 只改台账3文件。路线/计分板由root负责，避免并发覆盖。

## 5. 保存后的可机械核对

1. 新records长度21、ID唯一、new.records[:20]逐字段等于旧records。
2. 除generated_at及许可的新增容器/append外，每个旧顶层键内容逐字段不变；hardware_identities和source_tables旧键值保留；archive_pin_refs旧11项保持原前缀。
3. sources.json所有旧键值（58+32+20+5+7来源和两个历史快照）逐字段不变。
4. 每个新pin与实际原文/归档raw SHA一致；旧pin若当前活动文档变化，只按旧历史快照核验，不更新旧值。
5. 第21条所有实测数值与本轮原始JSON一致；45项集合精确、三状态/五档完整、失败数与独立audit一致、报告exit0≠筛选PASS。
6. 新全核/cycles/功耗/Fmax为NOT_TESTED时，MD和JSON均不得出现新加速比、已采用或全核已完成措辞。
7. JSON可读、MD链接目标存在，记录实际SHA及保存时间；没有GitHub写入。

最主要的遗漏风险是：照搬C2两态/owner结构；把source review或成本工具执行成功当候选通过；用旧C2的115场景/负控数据代替本轮实际日志；把有重叠的监视计数相加；只更新MD遗漏JSON/source pins；更新当前路线后覆盖58条历史pin；以及manifest与台账互相引用造成封存循环。
