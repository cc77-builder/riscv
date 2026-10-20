# O2 G3 全核验证封存证据

最终合格集合：core-02＋supplements-02，严格离线结果 **O2_G3_OFFLINE_RECHECK_PASS**。14项作业满足预期，正常程序5378条vdot提交；六项覆盖齐全，95项主机测试通过。修正前supplements-01/recheck-01失败记录保留，不并入最终合格覆盖。本轮本地保存，未推送GitHub，不是G4公平性能或T16正式报告。

## 入口

- [精简最终结果](files/runs/final-summary.json)
- [Linux严格离线重审](files/runs/recheck-02/result.json.gz)
- [最终两项补充测试](files/runs/supplements-02/result.json)
- [最终主机测试与源码摘要](files/runs/host-verification-final-01/verification.json)
- [实际9种FU类型切换审计](files/runs/transition-live-review-01/README.md)
- [最终部分取消与幸存者独立审计](files/runs/live-observer-check-10/README.md)
- [完整工程说明](../../fullcore/README.md) · [复跑步骤](../../fullcore/REPRODUCE.md)

## 内容和字节身份

共1037份封存文件，原始字节379277883，存储字节39611598（约39.6MB，不含manifest等入口文件）。每项记录原路径、原始SHA-256、存储SHA-256和压缩方式；gzip用固定mtime，恢复后须校验原始SHA。大于16KiB的日志/JSON等使用gzip，链接到.gz文件时可用gzip解压，原始字节校验见archive.py/portable.py。

[manifest](archive-manifest.json) · [manifest摘要](archive-manifest.sha256) · [封存字节回执](archive-check.json)。

导出时源码提交：2a8c4a4b7cf9ec3fa9f28d22585a83ced97d977f。真实硬件与运行工具提交另见最终结果，不以导出提交冒称重新构建。保留构建失败/中断、初轮软件诊断失败、源码副本、精确命令、正常/负控原始流及修复审计。生成RTL、编译对象、缓存、保留的旧EMU和大型硬件二进制不进入本包；小型测试镜像/ELF与其源码身份保留。原始WSL工作根仍完整保留。

## 跨平台复核

在checkout根目录执行：

    python3 -B team/optimizations/o2/fullcore/portable.py --archive team/optimizations/o2/evidence/20261019-fullcore-validation --core-campaign core-02 --supplement-campaign supplements-02 --output /absolute/new/portable-result.json

该工具使用Python标准库，复算全部存储/原始字节、13份完整轨迹及1份故障部分轨迹；它不重新运行EMU/NEMU，不替代Linux的Git/输入来源与全部架构用例审计。Windows交付目录保存单独实际复核回执；人工ACK、T17新机器构建、PPA与G4未由本包证明。
