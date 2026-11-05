# 报告图片与重建

26个正式图位及5组补充截图对应31份PDF展示资产。当前候选按**22张精确重绘＋9组原截图**整合，封面另行记录。正式图题由报告放在图下；多面板截图的分图标题放在相应面板下方。`placement.json`管理正式图题、说明、高度、来源和范围，`page-map.json`记录实际编译后的图号与物理页码。

13张SVG已全部完成，并通过原图存档、所选PDF及支持源的哈希核验；S1-07已改为实际12字节、三条启动指令和共同输入的精确图。数学表达源已修复，**Build07尚未启动，新合订本和三个分册尚未完成实际PDF检查，整套审美尚未确认；人工已暂时接受S3-01与S3-06，S3-05新横向周期版已作为候选入稿，仍待人工评价**。既有Build06与候选图的记录分别保留。

## 展示资产的三个入口

| 入口 | 图件数 | 处理方式 | 身份与输出记录 |
| --- | ---: | --- | --- |
| `build_evidence_figures.py` | 9 | 八张从冻结输入重绘；S3-05核对固定数据并采用已审阅轮廓PDF | `evidence-20261105/figure-data.json`、原CSV/日志、`generated-figures.json` |
| `build_diagram_layouts.py` | 13 | 保留原PNG存档，集成可编辑SVG制作的精确工程结构图 | `redesigned-20261105/selected-diagrams.json`、`diagram-layout.json` |
| `build_report_panels.py` | 9 | 从原日志、波形及代码截图选择显示区域并编排 | `source-screenshots/`、`screenshot-insertion-manifest.json`、`screenshot-layout.json` |

当前方法以每张实际源文件和显示资产为准。代码/SVG是22张候选图的制作源，PDF是报告展示入口；PDF优先于同名PNG加载。此前概念生图与精确图混合制作的分工已停止使用。

## 精确图与原截图

九张源数据、事件与启动指令图为S1-06、S1-07、S2-05/06/07/08、S3-03、S3-05、S3-07，保留固定输入、代码与SHA256。S1-07依据实际三条启动指令展示共同输入；S3-05按各场景自身RVV=100%采用统一线性周期占比轴，条内列出实际平均窗口周期；S3-07使用名义档14项正负裕量条形，完整五档70项数据继续保存在附件。

十三张SVG工程结构图为S1-01/02、S2-01/02/03/04/10、S3-01/02/04/06/08/09，按内容采用数据通路、位段、状态、控制流、时序窗口或内存布局。S3-01展示RTL与NEMU独立求值及对应架构状态比较；S3-06展示公共接口的编译时选择、288字节连续输入与八个完整16字节结果槽。较长条件和证据出处保留在图注、正文与附件。

当前候选使用原创白底、蓝青细线：文字`#24384A`、强调`#287F84`、次要文字`#637487`、结构线`#CED9E2`。颜色不代替方向、位宽、状态和结果标签，也不宣称采用厂商品牌色。

九组截图保留原始像素与来源。`screenshot-layout.json`记录源像素区域、PDF位置与原图摘要。S1-04/05是历史vadd事件定位，S2-09是合法算术用例的完整128位结果；未提供的异常专门截图仍按材料索引记录。

## 字体与实际尺寸

除S3-05外，八张源数据、事件与启动指令图由原生Windows中的Microsoft YaHei排版；生成器同时核查Microsoft YaHei与SimSun可用。S3-05使用已审阅的Noto Sans CJK SC轮廓PDF，11.5–12 pt，构建时交叉核对冻结数据与文件哈希后原字节采用。可见文字按至少11 pt、完整宽约160 mm绘制，按信息量增加高度。相关中文PDF使用Type3字形轮廓嵌入，预览从实际PDF渲染。

SVG保留可编辑文字，实际字体、字号和物理尺寸随独立源记录；已有SVG源使用Noto Sans CJK SC等实际字体。凡遇Inkscape CFF数字的ToUnicode映射错误，展示PDF均导出文字轮廓，再渲染该PDF检查画面；可编辑文字继续保留在SVG。轮廓字PDF可以没有可提取文字span，不能将其误判为缺字，也不能声称它具有正确的文本复制映射。

S3-04已有保持精确事件位置与双窗口几何、采用当前候选配色的文字轮廓PDF。原SVG、固定数据、240 dpi PNG及旧PDF仍用于追溯，旧PNG不再是唯一显示方案。

报告插图高度上限应容纳原比例，避免160 mm图件在正文中再次缩字。源字号、画布比例和最终正文显示尺寸分别记录；实际页面尚未检查前不预报通过。字体文件不随工程分发。

## 重建与验证

候选资产、选图清单和加载器整合完成后，在Windows Python环境重建展示图：

```text
python figures/build_evidence_figures.py --preview-dir <技术图预览目录> --preview-dpi 300
python figures/build_diagram_layouts.py --preview-dir <工程图预览目录> --preview-dpi 300
```

九组原截图保持不变；需要复现其已有排版时再运行`python figures/build_report_panels.py --preview-dir <截图预览目录> --preview-dpi 300`。

集成依赖Matplotlib、NumPy、PyMuPDF、Pillow及上述Windows字体。`build_evidence_figures.py --only S1-07 S2-07 S3-03`可限制预览范围。精确SVG需修改时，按其源目录说明使用相应脚本、Inkscape和实际字体；普通图件集成使用固定展示资产，不重新调用生图。

S3-04的`evidence-20261105/csr-window-source.json`绑定固定Git提交、after路径、原gzip及解压SHA、window-result和runtime；71 cycle、12 instret及11条退休记录已从原件独立复算。`r0`是运行replay编号，`seq4`的正式样本repeat=2。原gzip保存在同目录，图源不再依赖临时交接路径。

随后执行`python -X utf8 expand_reports.py`与`build.py`。最终检查实际PDF中的数学公式、图题唯一性、字号、页边界、图文同页及显示内容；输入断言与制图核验不构成新的RTL、全核、性能或EDA实验。

## 原图、生成尝试与历史版本

本轮已实际使用最新生图技能尝试整图概念和结构表达。完整生成图、提示词、请求与返回记录、版本、审查结论和失败材料继续保留；B概念图遭人工否定、S3-01结构生图的运算/连线错误均不改写为已接受。结构、数值和字符精确性要求使当前22张候选最终选择代码或SVG矢量绘制。

原13张示意图PNG、原截图和源插入清单继续保留；`diagram-layout-plan.json`用于核对原件身份，选图身份由`selected-diagrams.json`记录。`generated-assets-20261105/`中的启动文件、空槽及芯片/程序小图是早期制作记录，不是当前候选图的拼接部件。封面概念图单独记录，不表示实际芯片版图。

发布清单在编译和视觉复核后更新；历史失败版、字体问题与原始实验失败证据各自保留，不将单图事实/字号检查视为人工审美认可或新版整套PDF验收。
