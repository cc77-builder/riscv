# 报告插图源文件（2026-11-08 提交版）

本目录保存报告中统一风格插图的生成脚本。报告实际引用的 PDF 在 `../unified-20261107/`，由工程根目录的 `report-figure-overrides.tex` 接入。

**只编译报告时不需要运行这里的脚本。** 只有修改插图时才需要。

## 目录

| 位置 | 内容 |
| --- | --- |
| `tukit.py` | 公共绘图工具：画布单位 mm，字号单位 pt；中文 Noto Serif SC（字重 400），西文 Times New Roman；配色、线宽、箭头 |
| `s1_01.py` … `s3_09_sup.py` | 23 张技术图，每个脚本对应一张，文件头注明图中数值的来源 |
| `build_figs.py` | 运行上述脚本，用 Inkscape 导出文字转曲线的 PDF |
| `svg/` | 各技术图的可编辑 SVG（由 `build_figs.py` 生成） |
| `screenshot_figs.py` | 8 张截图组图（S1-03、S1-04、S1-05、SUP-S2-*、SUP-S3-SUMMARY）：只重排版并加中文子标题，截图像素不变 |
| `shots/` | 截图原图，从原组图 PDF 无损提取 |

`S3-09-SUP` 和 `SUP-S3-SUMMARY` 两张图已不在正文中使用，脚本与 PDF 保留备查。

## 统一规格

- 画布宽 160 mm，高度不超过正文中 `\reportfigure` 给出的上限，插入后约 1:1 印刷。
- 印刷字号：分区标题 9 pt，框标题 8.5～9 pt，正文和标签 7～7.5 pt，最小 6.5 pt。整体调整改 `tukit.py` 的 `SIZE_DELTA`（默认 −1）。
- 连线 0.2 mm、箭头 1.55 mm；S2-02 单独用 0.16 mm、1.2 mm。
- 配色：蓝 #2B6189 主体，青 #13827F 结果与通过，橙 #AD641F 异常与取消，紫 #6A4C93 控制与身份通路；S3-05、S3-07 的柱条用浅色填充加细描边。

## 依赖

- Python 3，以及 `pip install pymupdf pillow`
- Inkscape 1.4（命令 `inkscape` 在 PATH 中）
- 字体 Noto Serif SC、Times New Roman。其他系统缺少这两个字体时，字形宽度会变化，可能导致文字溢出。
- 截图组图另需 TeX Live 的 `xelatex`，与编译报告用的是同一套。

## 用法

在本目录执行：

```
python -X utf8 build_figs.py                  # 重新生成全部 23 张技术图
python -X utf8 build_figs.py S2-03 S2-10      # 只生成指定的图
python -X utf8 screenshot_figs.py             # 重新生成 8 张截图组图
```

两个脚本默认直接覆盖 `../unified-20261107/` 中的 PDF。想先比对，可加 `--out 其他目录`；加 `--png 目录` 可另存预览图。

`build_figs.py` 会报告每张图在正文中的印刷缩放比例；脚本检测到文字超出框体时会输出 `WARN`。重新生成后，回到工程根目录运行 `python -X utf8 build.py` 重新编译报告。即使图的内容没变，重新导出的 PDF 字节也可能不同，这是导出时间等元数据造成的。
