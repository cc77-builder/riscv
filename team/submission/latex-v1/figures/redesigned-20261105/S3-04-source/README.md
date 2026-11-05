# S3-04 精确事件图

本图由固定数据与 SVG 排版代码生成，不是生图或新增仿真。显示版采用 `S3-04-dual-window.png` 的原始字节，以 160 mm 宽嵌入；可编辑 SVG、数据和脚本一并保留。

数据来源见 `../../evidence-20261105/csr-window-source.json`。根端已按固定 Git 提交取回原始 gzip、window-result 与 runtime，核对 Git blob、gzip/raw SHA256，并直接按整数计数复算 71 cycles、12 instret 和 11 条退休记录。运行身份为 after/dataset0/replay0/seq4，正式样本 repeat=2；数据中的 rob 字段是 ROB 入队相对 tick，不是 ROB 编号。图内集中展示 CSR 采样与退休两行。

画布为 160 × 151.694444 mm，SVG 最小文字 11 pt；Noto Sans CJK SC Regular/Bold。暖色实线 cycle 与橙色虚线 instret 同时通过文字和线型区分。将脚本复制到安装 Inkscape、fontconfig 和该字体的环境后运行 `python3 render.py` 可输出 SVG/PNG/PDF。脚本没有仿真调用。

PNG 与实际 PDF 栅格预览均已目视核验。该 Inkscape PDF 的部分字形 ToUnicode 映射不正确，因此正式展示选用 240 dpi PNG，避免复制出错误数字；SVG 文本与 JSON 数据是精确可编辑源。此选择不改变图形位置、数值或字号。

`independent-visual-review.json` 记录根端添加固定来源注释之前的视觉审查；后续仅替换来源路径和字段释义，事件数据与选定 SVG/PNG 字节没有改变。

`S3-04-dual-window.pdf` 随附为原始字体映射诊断副本；其可见画面已核对，但 ToUnicode 文字映射异常，因此正文选择同源 PNG，不能将该诊断 PDF 当作当前显示资产。
