# 香山昆明湖 V2 自定义向量点积指令技术报告

2026 年 11 月 6 日整合修订。报告以环境与运行、指令与硬件设计、差分验证与性能评估三个阶段组织，整合 zjhwork 的新增测试截图、真实波形与此前制作的 22 张概念插图。技术正文按已有源码和原始结果更新，图表中的测试范围与测量条件在相应章节说明。

## 阅读与编译

`output/三阶段技术文档_合订本.pdf` 为完整报告；同目录另有三份分阶段 PDF。主文由 `sections/` 中的正文直接编译，全部必需图片和被引用的日志摘录均包含在包内。

需要 Python 3.9 或更新版本，以及包含 XeLaTeX、ctex、Fandol 和 TeX Gyre 的完整 TeX Live。字体采用 TeX Live 所附开放字体，无需安装 Windows 专有字体。推荐 TeX Live 2026。

在解压目录执行：

```bash
python -X utf8 build.py
```

若 XeLaTeX 未加入 PATH，可指定编译器：

```bash
python -X utf8 build.py --compiler /path/to/xelatex
```

只编译合订本可使用：

```bash
python -X utf8 build.py --documents main
```

脚本对每份文档执行三轮排版，前两轮更新目录和交叉引用，第三轮生成 PDF；记录位于 `output/build-receipt.json`，各轮日志保留在同目录。运行过程无需访问 GitHub 或网络。Windows PowerShell 可使用 `py -3 -X utf8 build.py`；带空格的编译器路径应使用引号。

## 文件组织

| 路径 | 内容 |
| --- | --- |
| `main.tex`、`stage1.tex`、`stage2.tex`、`stage3.tex` | 合订本及三份分阶段入口 |
| `preamble.tex`、`report-concepts.tex` | 版式、开放字体与概念插图映射 |
| `sections/` | 本次整合后的最终正文 |
| `figures/` | 技术图、测试截图、真实波形及 22 张概念插图 |
| `figures/updated-20261106/` | 按当前正文术语更新的覆盖范围图及来源说明 |
| `evidence/` | 编译时使用的日志与关键数据摘要 |
| `output/` | 四份 PDF 及编译记录 |
| `qa/build11-20261106/` | 本次发布核验及编译元数据 |

图片中的概念示意用于帮助理解，编号技术图及实测表保留可核对的接口、位宽、数值和条件。合订本与分阶段文档共享同一份正文和图件。仓库中的历史生成脚本不属于本整合包的构建流程；编译只需运行 `build.py`。

## 数据与版本

文档整合基于 `zufan` 与 `zjhwork` 合并提交 `cfb0010f379f13ac7732dfb98ae600cc7ee1d44b`；最新完整 forward 独立参考摘要对应提交 `6fc3972158daec30bad37b97b72c4653155e1260`。各测量使用的硬件和软件版本在正文证据索引中单独列出。

`evidence/application-current-20261106/` 保留旧 FR/TA 目标单窗口结果、FR/G/P 独立参考摘要，以及 2026 年 11 月 6 日闭合的 FR/G/P 三臂目标原始结果。第三阶段源码已补入同 ELF 的完整 forward 周期与退休指令观测，并保留目标正确性、正式性能资格和测量边界的区别；新增结果来自提交 `75b832d0d3ce82fc09c217e20a226676c7c33ba7`，来源成员、原始字节数与 SHA256 见 `provenance.json`。

本次新增目标结果目前已进入正文源码，现存 PDF 与发布元数据仍对应 Build11；新增内容将在下一次统一编译时纳入。

`figures/ai-concepts/layout-map.json` 与 `selected-assets.json` 保留了沿用图片的 Build10 选择记录和内容校验，仅作为资产来源；当前文档的编译、页码和视觉检查以 Build11 发布元数据为准。

文件清单、SHA256、实际编译环境和页面核验结果见发布元数据。完整工程、全部原始运行证据及实现源码见团队仓库 `cc77-builder/riscv` 的 `zufan` 分支。
