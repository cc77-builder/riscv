# 三阶段LaTeX与PDF报告

本目录发布2026年11月4日补图版。正文材料日期为2026年11月2日，组合为0f＋firstdot V2＋原C8；工程身份和资格边界见[最终版本确认](最终版本确认.md)。本次仅发布文档，不包含RTL、模型、NEMU或工作负载等项目实现代码。

| 文档 | 页数 | 待补图片位置 |
| --- | ---: | ---: |
| [三阶段技术文档合订本](output/三阶段技术文档_合订本.pdf) | 82 | 9 |
| [第一阶段执行日志与过程文档](output/第一阶段_执行日志与过程文档.pdf) | 26 | 2 |
| [第二阶段设计与基础测试文档](output/第二阶段_设计与基础测试文档.pdf) | 28 | 4 |
| [第三阶段协同仿真与性能分析](output/第三阶段_协同仿真与性能分析.pdf) | 26 | 3 |

13张命名图片已加入原位置；26个原位置中17处有图、9处待补，另保留5组补充截图。图题按阶段编号并在图下居中，已补图附正式说明及来源。结构示意图、事件重绘图和实测截图分别标明，缺少的原始波形不由日志截图替代。原截图中的团队占位标识、历史日期及已知限制继续保留。

## 文件与重编译

main.tex为合订本入口，stage1.tex、stage2.tex、stage3.tex为独立报告入口。sections保存当前完整正文，preamble.tex保存排版及图注宏。figures保存插图PDF/PNG、位置配置和页码映射；figures/source-diagrams保存本轮13张原名图片，figures/source-screenshots保存已有截图原图。

安装XeLaTeX和合法授权的宋体SimSun、Times New Roman字体后运行：

```bash
python -X utf8 build.py
```

build.py可通过--compiler指定XeLaTeX路径，通过--output-dir指定输出目录。默认每份编译三遍，并生成四份中文文件名PDF。仓库不分发Windows字体文件；默认加载系统字体，也支持本地fonts目录。

只替换图片时，将文件按编号放入figures后重新编译即可；优先级为PDF、PNG、JPG。调整图题或位置时，修改figures/placement.json，再执行：

```bash
python -X utf8 expand_reports.py
python -X utf8 build.py
```

content保存叙述、选用材料、来源SHA及重新生成正文所需的baseline文本；evidence保存引用的历史日志、状态和事件CSV。报告中的代码片段及历史材料属于文档内容，不表示本次改动或发布项目实现。

## 验证与边界

四份PDF与Windows已检查补图版逐字节一致，主报告逐页渲染无越界文字；图像与图注同页。独立报告与合订本对应页面除页码外像素一致。详细检查见[交付校验](交付校验.json)，逐文件SHA见publication-manifest.json。完整渲染预览和历史备份留本地。

插图内容、待采信号及本次页码见[插图清单](插图清单与替换说明.md)。本轮未运行EMU/NEMU、RTL构建、综合、STA或性能实验，也未修改稳定工程组合。
