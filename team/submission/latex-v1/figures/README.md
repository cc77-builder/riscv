# Build10 报告图片

本版保留 31 个原技术图位：13 张精确 SVG 结构图、9 张精确数据／事件图、9 个原截图组；新增 22 张无编号概念伴图，三阶段分别为 4／9／9 张，封面另计。

原图继续优先读取 `figures/<ID>.pdf`。伴图由 `report-concepts.tex` 读取 `figures/ai-concepts/<ID>.png`，完整画布按原比例显示，伴图块与精确图块可自然分页。新增伴图的内容与版面审查各自记账，原数据、位宽、时序和结果仍以原图与正文为依据。

`ai-concepts/selected-assets.json` 保存相对路径、原 PNG SHA、尺寸和逐图审查引用；`page-map.json` 使用本次实际 PDF 页码。原始选图 manifest、完整审查 Markdown、像素身份／次数／几何核验和主端视觉记录保存在 `../qa/concept-figures-20261106/`，未复制图片管理器、claim 或私有请求。

风格参考与表达决策见 `evidence-20261105/图形表达参考.md`。原图、旧候选、历史截图和失败证据继续保留。S2-09仍是合法算术截图，非法配置异常码与目的寄存器不更新的专门截图未新增；SQRT不因静态路径图增加动态覆盖。 历史UTC容量审计FAIL、负时序裕量和墙钟稳定性未证实继续保留；整核Fmax、布线后时序及功耗未新增验证。

常规重编使用原 `build.py` 与已记录的 XeLaTeX、SimSun、Times New Roman 环境，无需运行正文展开器、绘图器或生图工具。精确恢复本次构建输入时，在全新目录按 `qa/concept-figures-20261106/build10-native/frozen-sources.json` 逐项复制：描述性更新的文件取 `qa/concept-figures-20261106/build10-input-documents/` 中的原字节，其余取当前 source。469 项全部核验后再编译。字体和系统库没有因编译器 exe 的 SHA 而自动冻结，不承诺跨环境重编 PDF 字节必然相同。
