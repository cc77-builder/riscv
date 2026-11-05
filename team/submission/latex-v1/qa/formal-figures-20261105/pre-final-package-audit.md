# Build09 最终包与说明一致性审查

范围：只读核对 `report-work/source/team/submission/latex-v1`（下称源目录）、`build09-fetch`、`delivery` 和既有导出脚本。未修改正式源、未构建、未开展新视觉或硬件验收。主端正在同步说明，以下区分已核实事实和交付前待同步事项。

## 已核实的交付身份

实际读取四份 PDF 的页数、字节及 SHA256，与 `build09-fetch/metadata/build-receipt.json`、自动检查和下载清单一致：

| 文档 | 页数 | 实际构建来源 | SHA256 |
| --- | ---: | --- | --- |
| 合订本 | 102 | Build09 | `9e0399d869a9ca86e1a08a5cbdb512ab44930af6fccf096e4077b1bebd2c8cf5` |
| 第一阶段 | 34 | Build08 原字节复用 | `a3e10ab20f654ac6541c5c08a1013b47a759cf31360b0d02c4185945b0fe3502` |
| 第二阶段 | 33 | Build07 原字节复用 | `ac8f4731418b730350d9f7afe73247fd04aa4424970c2aef5c44373b43b0ec71` |
| 第三阶段 | 38 | Build09 | `df1f02348e7279116ab35117e055f3552e9fd0bb4f3ec22db509e0b4cc0cac7b` |

源目录 `output/` 四份文件已经一致；31 张顶层图 PDF 与 metadata 内对应文件逐字节一致。`diagram-layout.json`、`screenshot-layout.json`、`generated-figures.json` 也一致。

`frozen-sources.json` 的340项在当前源均存在；本次比对仅两个 README 因构建后说明更新而变化，未发现正文、生成代码、图源或数据偏移。13图选图清单共278条哈希引用、126个不同文件，全部存在、摘要吻合并已纳入冻结清单；9张数据/事件图的记录摘要全部吻合。未发现需要重新构建才能解决的包身份问题。

## 最少必要同步事项

1. **替换旧“当前校验”，保留历史记录。** 源目录 `交付校验.json` 仍以 `DOCUMENT_DELIVERY_PASS_WITH_DISCLOSED_EVIDENCE_LIMITS` 声明 Build05、113/34/42/40页和旧字体结论；`delivery/04_交付校验.json` 对应 Build06 的94/33/30/34页及旧视觉PASS。这些记录作为历史有效，但不能配新PDF充当当前结论。源 `publication-manifest.json` 仍为旧172文件清单，实算44项不匹配，scope仍称“三概念部件和九张重绘图”。归档既有版本后，根据当前文件重建发布清单、交付校验和对外04；不能只替换顶层状态字符串。`qa/pdf-inspection.json` 已同步为本次102/34/33/38页，六类自动检查均无异常，其原始状态为 `AUTOMATED_INSPECTION_COMPLETE_VISUAL_REVIEW_PENDING`。最终视觉结论只绑定实际已查看的本轮证据，单独保留人工审美尚未确认。

2. **更新两个相同的图件索引及制作分类。** 源 `插图清单与替换说明.md` 与 `delivery/01_报告缺图清单.md` 仍明确指向 build-06 和旧页码。按当前 generated sections、placement及 `build09-fetch/metadata/qa/page-map.json` 重写一次，再复制为相同内容；不要机械给全表加固定页差。例：S1-04为合订本20/分册17，S2-10为47/13，S3-05为78/14，S3-06为82/18，SUP-S3-SUMMARY为102/38。图题也按当前正文取值。`delivery/00_图片来源分类.md` 仍称“B版9张整图imagegen＋13张确定性精确图”，应改为13结构图＋9数据/事件图＋9原截图；封面独列。保留S2-09合法完整128位结果已具备、非法配置专门截图尚未提供的区别。

3. **收齐相互对应的说明。** 本次审查期间主端已更新源 README 与 figures/README，正确记录Build07失败、Build08修复、Build09只重编main/stage3，且保留S3-05横向B版及整套审美未确认。不要再把这里列为未修。仍需将 `figures/evidence-20261105/图形表达参考.md` 与 `delivery/03_厂商图形风格与制图决策.md` 同步成逐字节一致；最新读取时前者仍写“Build07尚未启动”，两文件已不相同。保留最新生图技能实际尝试、概念图技术错误不采用和失败记录，不将新精确图的制作决定写成人工审美接受。

4. **使用参数化导出脚本，并绑定本轮页码。** 禁用 `report-work/finalize_delivery.py`：它硬编码 `build-03`，会写入固定视觉PASS与旧页码。可用 `phase3-drafts/export-review-images.py`，给当前源目录、Build09 page-map和一个不存在的新输出目录。其31唯一ID、图号、单页PDF、复制哈希检查有效，PNG确由导出的同一PDF渲染；但图号未变时旧page-map也可能通过，脚本本身不验证四份报告SHA。因此明确传本轮映射，保持已核对的31图PDF不变。输出后随附新 `images.csv`、`export-manifest.json`、README和HTML，不沿用旧导出文件名/页码。该目录是图片浏览包，不是完整可编辑源码包。

5. **交付完整源快照，不能把metadata.zip称为复现源码。** `build09-fetch/metadata.zip` 只有50个条目，含日志、回执、冻结摘要、QA和图PDF，未包含Python代码或正文JSON。源码包须保留现行 `content/overview/narrative/technical/structure`、模板/生成器/编译器脚本、31展示PDF、26正式图配置与截图定义，以及 `selected-diagrams.json` 引用的SVG/支持源、S3-05的 `selection.json`、SVG/PDF/renderer、冻结数据/CSV和必要原日志。现行源中这些输入已存在，不必重新制作。以完整源快照和README重建即可；若还声称能重放Build07–09的原生增量恢复流程，则额外附driver、原delta和两个fix输入、回执/失败日志。仅附 `original_delta_sha256` 或 `frozen-sources.json` 不能代替文件本体。现有尝试与失败材料应在源码历史目录或独立证据包有可定位入口，不应为缩包删除独有记录。发布manifest在说明、输出与索引全部同步后生成；构建冻结清单保留原义，不改成发布清单。

6. **保护用户和队员的润色成果。** 此次审查未读取Windows实时工作树，不能判断其当前改动归属。交付使用新的明确版本目录；不要用本云端目录或旧整包覆盖既有润色版、主仓或其他工作树。需要Git集成时以实际差异、文件归属和当时工作树为准，正文内容与图片/说明分别核对。交付说明可称“基于e2c2e8d的本轮配图与正文修订稿”，不能声称包含之后未核对的队员润色或替代其版本。

## 结论

PDF与31图的当前文件身份一致，源码中的选图及支持输入齐全。剩余实质事项是更新旧校验/manifest、索引/制作分类、成对说明，并将当前源码和可编辑资产随交付保存。当前自动检查通过是事实；人工审美接受仍未发生。上述同步不要求新RTL、仿真、EDA或重复编译。
