# 香山昆明湖 V2 自定义向量点积指令技术报告

本文件夹是比赛提交版报告的 LaTeX 工程，2026 年 11 月 8 日定稿。报告分三个阶段：环境部署与向量执行过程、指令设计与基础测试、协同仿真与性能评估。

编好的 PDF 在 `output/`：

| 文件 | 内容 |
| --- | --- |
| `第一阶段_执行日志与过程文档.pdf` | 第一阶段 |
| `第二阶段_设计与基础测试文档.pdf` | 第二阶段 |
| `第三阶段_协同仿真与性能分析.pdf` | 第三阶段 |
| `三阶段技术文档_合订本.pdf` | 三个阶段合订，供自己查看 |

## 编译

**环境**

- Python 3.9 或更新版本，只用标准库。
- 完整的 TeX Live（推荐 2026），需要包含 `xelatex`、ctex、Fandol 和 TeX Gyre 字体，以及 fvextra、needspace、seqsplit、placeins 等常用宏包。安装 scheme-full 即可。
- 所用字体都随 TeX Live 提供，不依赖 Windows 字体，Windows、Linux、macOS 都能编译。
- 全部图片都是预先生成好的 PDF 或 PNG，编译时不需要 Inkscape，也不需要联网。

**命令**（在本文件夹中执行）

```
python -X utf8 build.py                          # 编译全部 4 份 PDF
python -X utf8 build.py --documents stage2       # 只编译某一份：main、stage1、stage2、stage3
python -X utf8 build.py --compiler "C:\texlive\2026\bin\windows\xelatex.exe"   # xelatex 不在 PATH 中时指定路径
```

每份文档排版三轮：前两轮更新目录和交叉引用，第三轮生成 PDF。结果写到 `output/`，同时生成 `build-receipt.json`，记录各文件的 SHA-256。各轮日志和中间文件（`*.aux`、`*.log`、`*-pass*.txt` 等）也会留在 `output/`，提交前可以删掉，只保留 4 份 PDF。

`-X utf8` 用于避免 Windows 中文控制台的编码错误；在 Linux 和 macOS 上可以省略。

**检查编译是否正常**：`output/` 下各 `*.log` 中不应出现 `Missing character`、`Overfull`、`undefined`，也不应出现 `multiply defined`。

## 文件组织

| 路径 | 内容 |
| --- | --- |
| `main.tex`、`stage1.tex`～`stage3.tex` | 合订本与三份分阶段文档的入口 |
| `preamble.tex` | 版式、字体、图表宏 `\reportfigure` 与浮动参数 |
| `sections/` | 正文 |
| `report-figure-overrides.tex` | 每个图号实际使用的图片文件 |
| `figures/unified-20261107/` | 统一风格的技术图与截图组图，报告实际使用 |
| `figures/unified-20261107-src/` | 上述图片的生成脚本、SVG 和截图原图，说明见其中的 README |
| `figures/S2-TEST-*.png`、`figures/S3-WAVE-*.png`、`figures/source-screenshots/` | 直接引用的测试截图和波形截图 |
| `evidence/` | 正文中摘录的日志 |

以下文件保留备查，不参与编译：

- `figures/tu/`：早期候选图
- `figures/updated-20261106/`：上一版重绘图
- `figures/` 根目录下的 `S1-03.pdf`～`S1-05.pdf`、`SUP-*.pdf`：英文子标题的旧截图组图
- `sections/overview.tex`：内部用的结果总览
- `sections/screenshots-stage2.tex`、`sections/screenshots-stage3.tex`：原来集中摆放截图的章节

## 修改时的注意事项

- **正文**：在 `sections/` 中修改，然后重新编译。图表都写成“图\ref{fig:…}”“表\ref{tab:…}”的形式，编号由 LaTeX 自动生成，不要手写编号。
- **插图**：用 `\reportfigure{图号}{图题}{最大高度}{备注}{来源}` 插入。第 4、5 个参数只留在源码里供自己查看，不会排版到图下；图的解释写在正文中。
- **图片文件**：在 `report-figure-overrides.tex` 中修改图号对应的文件。如需重画统一风格的图，见 `figures/unified-20261107-src/README.md`。
- **排版方式**：图和带表题的表格是浮动体，当前页放不下时会移到下一页顶部，由后续正文填满本页，因此图可能出现在引用它的段落之后一页。不要在图前加强制换页。
