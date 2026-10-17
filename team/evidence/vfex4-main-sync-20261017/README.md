# 旧VFEX1清理验证（2026-10-17）

本轮新执行309个测试方法，全部通过：团队186、T13测量23、T15模型11、
O0诊断79、统一测试10。实际日志、Python优化模式与计数见result.json。
全部在Ubuntu-HDL运行：`python3 -OO -B -m unittest discover -s <目录>`，
目录依次为team/tests、team/workloads/vdot-perf、team/models/vdot-param/tests、
team/optimizations/o0、team/workloads/unified-vdot。

cleanup-check.json记录删除的24文件及源码/构建/原归档不变检查。
清理没有更改生产RTL，因此没有重新构建EMU或运行全核；这些检查验证
当前工具与依赖未因删除旧实现而破坏，不能替代新硬件验收。

main独有历史归档将在普通合并时按其原Git blob保留；发布后的远端SHA另行
回读，不把本目录测试结果当成发布回执。详见../../docs/vfex4-main-sync-20261017.md。
