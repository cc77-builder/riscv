# Build10 概念伴图排版副本：尚未编译

此目录是当前报告的局部副本，不是完整工程代码仓。它只实现 22 张概念伴图的 LaTeX 接入；最终 PNG、对应 SHA 与审查身份尚由主端交付。当前没有概念 PNG、占位 PNG 或 Build10 成品 PDF，也没有新增技术结论、仿真或性能验收。

## 改动与保留

- `preamble.tex` 仅新增 `report-concepts.tex` 的加载和 `reportfigure` 开头的一次调用。原精确图的整个绘制、caption、label、技术说明与 PDF→PNG→JPG 优先级保持原样。
- `report-concepts.tex` 包含最小伴图宏与 22 条显式映射。每张概念图使用完整画布、正文宽度 `\linewidth`（现有几何设置为 160 mm）和原长宽比；图片与短说明在一个小块内。概念块与后面的原精确图是两个独立块，之间可以自然分页，没有逐图 `clearpage`。
- 伴图说明为“概念示意：主题。技术依据见图 `\ref{fig:ID}`。”，不使用编号 caption、不增加图号、不新增测量或 PASS 声明。22 项由第一／二／三阶段的 4／9／9 项组成；9 个原截图组没有伴图入口。
- `figures/ai-concepts/layout-map.json` 记录原图、锚点、文字、输入 SHA 和目标 PNG 路径。`selected_asset=null` 表示本任务没有选择或批准最终图片。
- 原 448 项正式文件中，4 个 Build09 `output/` 成品未复制到此目录，其余 444 项逐字节复制后仅修改上述前导文件。全部原 31 个显示 PDF、三份正文、其他入口、原构建器与检查器保持字节一致。缓存不带入。原目录未写入、删除或改名。

原 README、发布 manifest、页码索引、交付校验和 `qa/` 历史记录随副本保留，仍只说明 Build09 或更早版本。它们不是 Build10 的页数、输入清单或 QA PASS；主端完成实际编译和视觉检查后再更新本次发布元数据。

## 主端落入最终图片

将 22 个最终原字节 PNG 放到 `figures/ai-concepts/<ID>.png`，ID 集合严格按 `layout-map.json`。在独立的最终选图 manifest 记录每项 SHA-256、bytes、像素尺寸、实际 imagegen 请求／版本／回执及适用于这些字节的审查记录。封面和原精确图不计入这 22 张。

宏只检查被调用的映射 PNG 是否存在；缺失会触发 `PackageError`，现有 `build.py` 的 `-halt-on-error` 会终止编译。宏不回退到原精确 PDF，也不生成空白框。文件 SHA 与选图资格需由主端在编译前核验，不能仅凭 LaTeX 成功读取就认定绑定正确。

## 编译与检查建议（本任务未执行）

沿用已核实的 Windows XeLaTeX、SimSun 与 Times New Roman，保留字体和编译器实际身份。四份文档都需重编，每份由原 `build.py` 执行三遍；不要沿用 Build09 复用 stage1/stage2 的驱动，也不要运行旧绘图器或正文展开器。

每份可使用如下同一个原入口，分别令 `DOCUMENT` 为 `main`、`stage1`、`stage2`、`stage3`，输出到本次新建的各文档目录：

```text
python build.py --compiler "<已核实的 xelatex.exe 绝对路径>" --output-dir "<本次独立输出根>/DOCUMENT" --documents DOCUMENT
```

原检查器要求 `--logs-dir/<document>/<document>.log`，而 `build.py` 会把一次调用的日志直接写进指定输出目录。按上面的四个目录保存日志即可与原接口一致；另把四份正式中文文件名 PDF 原字节汇总到单独的 `--compiled-dir`。不需要修改构建器或原检查器。

原 QA 继续核 A4、31 个技术图题、页码、引用、诊断和占位。新增伴图要补充实际包含与视觉检查：合订本 22 张、三分册 4／9／9 张，原技术图位分别 31／7／14／10 个。以实际 PDF 页码重建映射；PNG 可能被 PDF 重新编码，不能只用提取容器 SHA 判断同图。查看所有页面缩略图及伴图、精确图、图注和相邻分页的大图，核完整画布、可读性和实际空白。特别检查 S3-08、S3-02 等原精确图较高的相邻区域；先看实际排版，再决定是否局部移动，不预设新页数或强制两块同页。

## 静态证据与交接

本任务的差异、输入保护和静态检查位于相邻 `build10-layout-work/`。本目录当前是“布局实现待图片、编译与视觉验收”，不作为最终报告交付或发布。
