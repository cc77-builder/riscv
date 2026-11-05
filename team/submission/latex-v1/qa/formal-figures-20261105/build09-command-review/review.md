# Build09 独立增量复核

完成时间：2026-11-05T19:05:35.000336+00:00。范围：两份现成 PDF 的三处命令排版，以及 Build08 → Build09 的其余页面渲染一致性。

## 结论

本次范围内通过。三组命令的选项前缀均提取为 ASCII `--`（U+002D U+002D）；六个受影响页面已分别以 Poppler 125 dpi 整页渲染并实际查看，未发现新增截断、重叠或孤立标题。Build08 的 F01 已解决。

## 当前 PDF 身份

| PDF | 页数 | SHA-256 |
|---|---:|---|
| main.pdf | 102 | `9e0399d869a9ca86e1a08a5cbdb512ab44930af6fccf096e4077b1bebd2c8cf5` |
| stage3.pdf | 38 | `df1f02348e7279116ab35117e055f3552e9fd0bb4f3ec22db509e0b4cc0cac7b` |

## 命令与实际页面

下表页码均为从 1 开始的物理页；括号内为印刷页码。字体为本次 PDF span 提取结果，三处均是 `TimesNewRomanPSMT`，不将代码标记误述为已使用等宽字体。

| 核对项 | stage3 | main | 字号 | 观察 |
|---|---|---|---:|---|
| `objcopy --strip-debug` | 20（17） | 84（78） | 10.909 pt | 表 3-6 命令与中文完整，未越界；下方 3.4.5 标题后有正文。 |
| `portable.py --archive … --campaign … --output …` | 32（29） | 96（90） | 9.963 pt | 完整排为两行，在 `--campaign` 后换行；下一行从其值 `campaign-01` 开始。下一段、3.7.5 标题与表格页内部分完整。 |
| `package_evaluation.py --verify ARCHIVE --receipt NEW_JSON` | 36（33） | 100（94） | 11.955 pt | 命令与段落完整；3.7.10、表 3-15、3.7.11 及其后正文未发生新增截断。 |

portable.py 的实际提取为以下两行；转成单行命令时用空格连接视觉换行：

```text
python -X utf8 -B performance/portable.py --archive evidence/20261019-performance-ab --campaign
campaign-01 --output /absolute/new/portable-verification.json
```

## 其余页面与公式复核复用

用 PyMuPDF 对两版本全部页面按相同 72 dpi RGB 设置渲染，比较原始像素的 SHA-256：

- main：仅物理页 **84、96、100** 改变，其余 **99 页** 像素相同。
- stage3：仅物理页 **20、32、36** 改变，其余 **35 页** 像素相同。

因此，原公式审查所涉及的 main 38、40、76、77、95、97、98，以及 stage3 12、13、31、33、34 均有本次渲染一致性证据，可保留 Build08 审查的原范围与结论。main/stage3 目录页也一致，页数仍为 102/38。此处不把 dormant overview 源文件中的公式宣称为活动 PDF 中已显示的公式。

## 证据与边界

逐页像素哈希保存在 `build08-build09-render-comparison.json`，提取文字与字体坐标分别在 `identity-and-command-locations.json`、`command-font-extraction.json`；本次实际查看的六张整页图在 `pages/`。前次审查位置为 `../../build08-fetch/independent-review/review.md`。

本次未重审单独 stage1/stage2 PDF；未修改源码或 PDF，未重建、未执行报告中的命令或工程测试。像素一致只指上述 72 dpi 设置，不表示 PDF 原字节相同。本次结论仅覆盖指定增量和既有审查页保持情况。没有新增问题；可停止可选测试。
