# 三阶段技术报告：图像修订版

本版基于 James_Hotten 的 `e2c2e8d5fa9a92c5d99c3c3e3f5399d60a115c63`。按用户要求，先将该分支正常快进合并到 `zufan`，再进行本轮文档修订。新增修改只涉及报告及工程交接；原实验结论仍绑定各自冻结的 0f、firstdot V2、原 C8 与 R5 运行身份，不自动转移到当前 Git HEAD。

## 图片与证据

原 26 个图位现均有图：沿用 17 处、补齐 9 处，并保留原 5 组补充截图。新增九图包括历史 vadd 事件与启动恢复、P/R 重叠、反压保持、取消/复位、DIV 切换/关钟、bit100 拒错恢复、四类微基准和 Nangate45 面积/STA。

技术图以固定日志和 CSV 为输入生成矢量 PDF；每张均有运行身份、字段含义及范围说明。图源与 SHA256 见 `figures/evidence-20261105/`，完整清单见[插图清单与替换说明](插图清单与替换说明.md)。封面概念图通过图像生成工具创建并注明用途，不承担工程证据作用。图形表达参考见[厂商风格与制图决策](figures/evidence-20261105/图形表达参考.md)。

仍需保留的补证限制：S1-04/05 原截图的时钟显示尚未确认；S2-09 缺少非法配置异常码与目的不更新的专门截图。SQRT 仅保留静态取消路径检查范围。本轮没有新增 RTL 仿真、性能运行或 EDA，也未修改官方程序、验证器、原始日志和失败证据。

## 版式与编译

A4，四边 25 mm，正文 12 pt；中文宋体、英文 Times New Roman，代码/日志沿用 Times New Roman。四份报告均有封面与目录：封面无页码，目录罗马编号，正文从 1 开始；章节、图表按阶段编号，图片与图注同页，跨页表重复表头。保留尚待人工确认的队伍、成员、学校等身份信息。

入口为 `main.tex`、`stage1.tex`、`stage2.tex`、`stage3.tex`，公共模板为 `preamble.tex`。交付 PDF 位于 `output/`。当前页数、正文汉字数、字体、编译诊断和 PDF SHA256 统一见 `qa/pdf-inspection.json` 与 `交付校验.json`；当前物理页码映射见 `figures/page-map.json`。

安装 XeLaTeX 与有权使用的 SimSun、Times New Roman 后：

```bash
python -X utf8 expand_reports.py
python -X utf8 build.py --output-dir <独立输出目录>
```

`build.py` 支持 `--compiler` 指定 XeLaTeX、`--documents` 选择文档，每份编译三遍。仓库不分发字体。重绘九图另需 Matplotlib、NumPy（PDF 预览还需 PyMuPDF）和 Noto Sans CJK / 微软雅黑 / 宋体，可运行：

```bash
python figures/build_evidence_figures.py --preview-dir <图片预览目录>
```

正文由 `content/`、`expand_reports.py`、`report_layout.py` 与 `figures/placement.json` 生成。修改源材料或配置后重新生成，不只改生成的 `sections/stage*.tex`。图片按同名 PDF、PNG、JPG 顺序加载。

## 版本与核验

原发布元数据分别保留于 `qa/upstream-402706f/`、`qa/upstream-e2c2e8d/`，适用其原版 PDF。当前发布清单在最终编译和视觉复核后生成，不能用历史 PASS 或旧页数代替本版检查。原报告中的“本轮”工程状态按 `最终版本确认.md` 所列历史语境阅读；本次仅补图、核对图注与重编译。
