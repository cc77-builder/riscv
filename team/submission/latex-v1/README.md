# 三阶段LaTeX与PDF技术文档

本目录保存用户确认的参赛工程V1.0技术初稿，采用0f＋firstdot V2＋原C8以及已有Nangate45数据。团队名称、成员和学校信息待填写。

## PDF阅读入口

- [第一阶段执行日志与过程文档](output/第一阶段_执行日志与过程文档.pdf)，5页。
- [第二阶段设计与基础测试文档](output/第二阶段_设计与基础测试文档.pdf)，3页。
- [第三阶段协同仿真与性能分析](output/第三阶段_协同仿真与性能分析.pdf)，4页。
- [三阶段合订本](output/三阶段技术文档_合订本.pdf)，13页。

## 源码与附件

main.tex为合订本入口，stage1.tex、stage2.tex、stage3.tex为各报告入口。sections保存正文，preamble.tex保存格式，evidence保存报告引用的真实日志和事件数据。[版本确认](最终版本确认.md)与[原PDF校验](交付校验.json)记录既有身份。[发布清单](publication-manifest.json)绑定本次实际上传文件。

## 字体及复编

使用XeLaTeX，中文字体为宋体SimSun，英文和数字为Times New Roman。字体属于机器环境依赖，由使用者安装合法取得的相应字体。仓库不分发Windows字体文件。

preamble.tex优先读取使用者自行准备的fonts目录内simsun.ttc和Times系列文件，缺少该目录时按系统字体名加载同一字体。此适配保留原本地工程的字体文件模式，支持安装了对应字体的机器直接复编。

在本目录执行python3 build.py，或分别对main.tex及stage1.tex至stage3.tex执行两遍xelatex。LaTeX包需包含ctex、fontspec、fvextra、longtable、seqsplit、tikz和hyperref。编译产生的aux/log/out/toc和渲染预览保留在本地。

## 阅读范围与发布

PDF为用户本轮要求的技术初稿，提交前填写团队信息并完成成员复核。第一阶段图按原FST事件CSV重绘。真实原始日志和既有测试资格按正文范围引用。既有PDF原文件逐字节发布，本次仅为源码增加系统字体回退及可移植构建入口。

本次发布到zjhwork的范围是本目录、团队导航和一条发布计分板记录。未采用P4源码继续保留在本地研究工作树，生产src按原0f树校验。
