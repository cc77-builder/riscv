# P2 依赖链只读归因

[结论与分段](RESULT.md) · [结构化记录](RESULT.json) · [范围](CONTRACT.md) · [下一轮指令](NEXT_STEP.md)

本轮复用现有日志与398份同版生产源码，未新增目标运行或RTL改动。
实测7拍依赖间隔拆为FU2拍与响应后5拍；五拍逐阶段解释是带前提的静态模型。
下一步只进入P4-G0可行性评审，不代表允许实现，也不把条件1601 cycles填为实测。

[输入锁](input-lock.json)及[归档](evidence/20261028-p2-dependency/manifest.json)保留原文/派生/失败身份；
reviews为阅读副本，原目录结构在逐文件gzip载荷中。仅需本机离线复算时按归档中trace/analyze_dependency.py和jade/analyze_history.py入口使用fresh输出目录。
