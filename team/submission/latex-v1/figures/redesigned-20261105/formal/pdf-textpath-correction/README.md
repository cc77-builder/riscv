# S1-01 / S3-01 排版 PDF 文字转路径修正

这份补充用于替代前次交付中带有错误 ToUnicode 映射的两张排版 PDF。原 SVG、原 PDF 与其旧包均保留，不覆盖。

## 已确认的问题

原 PDF 的可见图面正确，但 `fitz` 与 `pdftotext` 对关键数字提取出错。例如 S1-01 的 `WSL2 · Ubuntu 22.04.5`、S3-01 的 `8 对 signed8`、`i = 0 … 7` 和两处 `vd[127:0]` 含控制字符或 U+FFFD。对应 SVG 标签正确。原样复制 `--diff` 还可能取得兼容连字 `--diﬀ`。具体提取结果和原文件 SHA 保存在 original-text-mapping-check.json。

## 本次处理

直接使用已安装 Inkscape 的 `--export-text-to-path`，由完全相同的文字 SVG 导出新 PDF；没有开发字体转换器，没有更改标签、连线、图意或源 SVG。

- S1-01-environment-textpath.pdf：原生 160 × 120 mm。
- S3-01-structural-textpath.pdf：原生 160 × 122 mm。
- 两张 PDF 的字体列表均为空、文字提取为空，所有可见文字已成为矢量路径。这绕开了错误文本层，**并非修复了 ToUnicode；图中文字不再可直接搜索或复制**。
- sources/ 内保存同字节的可编辑 SVG。报告图注和来源记录继续提供可读文字。
- 两张 PDF 均实际经 Poppler 渲染并由本轮 Agent 查看；关键数字与标识正确，无新增遮挡或连线变化。与旧渲染的像素不完全相同，平均绝对通道差约 1.52–2.43/255，未宣称像素同一。

render-qa.json 和 render-comparison.json 保存本次实际命令、摘要、尺寸及比较记录。export_textpath.py 可从 sources/ 重新导出两张 PDF/PNG。本次仅处理图形文档，没有工程构建、仿真、报告工作树或 Git index 写入；人工是否最终选用另行判断。
