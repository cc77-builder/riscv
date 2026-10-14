# 2026-10-14 当前任务审查证据

这里记录审查时发现问题的隔离负控及轻量复测；不替换T04/T06/T10原始验收。

- optimized-validator-repro.json：从实际vdot-core-smoke.sh提取最终Python验收段。将真实日志的20个T10_CASE和总T10_CORE_SMOKE_PASS行全部删除，其余日志保留；普通模式拒绝，PYTHONOPTIMIZE=1错误生成PASS。optimized-generated-false-pass.json仅为故障复现产物，不能当作任何任务通过记录。
- relocated-image-repro.json：复制镜像/flash/清单到隔离目录，只在复制的BIN尾部追加字节；实际清单摘要仍核对原目录镜像并退出0。未启动仿真器，未修改原通过镜像，不声称整次故障程序已运行。
- actual-positive-normal.log：正常开启断言重新验证T10实际原始日志，20项通过仍成立。
- review-tests.json：23项Python回归、25项C判定器通过；C诊断定位v10字节15的注入高位错误。原三份归档的105/25/255文件摘要全部一致。

审查范围/问题/优化建议见[报告](../../docs/current-tasks-audit-20261014.md)。完整源码与重型运行沿用已有归档，本轮未重新构建全核或重跑完整NEMU/RTL矩阵。源码未修复；只新增审查报告和证据。
