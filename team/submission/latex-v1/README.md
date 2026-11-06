# 三阶段 LaTeX 与 PDF 报告

2026年11月6日更新：第一阶段按环境、操作日志和vadd加法过程归属；第二阶段补齐正数、负数及边界点积三类测试截图，以及22项定向＋10000项随机算术RTL测试汇总；第三阶段补充真实vdot输入、响应、提交观察波形及bit100拒错／正常恢复日志截图。性能与PPA结论保持原测试范围。

| 文档 | 页数 |
| --- | ---: |
| [第一阶段](output/第一阶段_执行日志与过程文档.pdf) | 26 |
| [第二阶段](output/第二阶段_设计与基础测试文档.pdf) | 30 |
| [第三阶段](output/第三阶段_协同仿真与性能分析.pdf) | 30 |
| [合订本](output/三阶段技术文档_合订本.pdf) | 88 |

第二阶段三类案例位于第10—11页，算术汇总位于第11页。第三阶段拒错／恢复截图位于第3页，真实vdot波形位于第5—7页。合订本对应算术汇总第39页、拒错／恢复第61页。以figures/page-map.json为准。

## 编译当前交付源码

main.tex、stage1.tex、stage2.tex、stage3.tex通过sections中的最终正文直接编译。安装XeLaTeX、合法授权的SimSun及Times New Roman字体后执行：

```bash
python -X utf8 build.py
```

本次所有既有Python脚本保持原状。旧expand_reports.py属于上轮再生流程，会覆盖本轮直接交付的正文；请直接编译当前.tex文件，不运行旧再生脚本。字体、FST/VCD大波形、编译缓存及渲染预览不随本次更新发布。

## 证据范围

原始截图保存在figures/source-screenshots；图下注明历史记录与本次波形的身份。10022项统计属于算术数据通路；历史negative-vdot及functional-0日志用于拒错／恢复；真实vdot波形补采仅证明所示正数事务，不新增性能或PPA测量。阶段一vadd不作为点积测试。

当前PDF经过本地排版检查；本发布副本的LaTeX源码独立编译后核对全部页面文本。更新范围和文件SHA见publication-manifest.json、交付校验.json。源码、图片、PDF以外的项目实现及既有辅助代码均保持不变。
