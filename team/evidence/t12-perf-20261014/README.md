> 历史早期证据入口：本目录空样本/NOT_RUN保留原状；后继实际190/199运行、全部63窗口见[最终原始证据](../t12-r2-20261014/README.md)，本次复核见[整合报告](../../docs/t12-zufan-integration-20261014.md)。

# T12 本轮证据

当前只有真实 host 检查、环境拒绝回执与源文件摘要。没有新 EMU 日志或处理器性能样本，T12 Architectural 全核验收 NOT_RUN，微架构事件 NOT_OBSERVED。

`host/` 保存实际测试日志与 exit code；测试内的合成日志仅用于拒错，未归档成 DUT 结果。`performance.json` 的 samples 为空，`raw.csv` 只有表头。`environment.json` 记录本会话 WSL/Git 拒绝及未核实项。最终源码快照摘要另见 Windows implement/overlay-sha256.json；尚无实现 commit。

重跑入口见 [工作负载README](../../workloads/t12-perf/README.md)，分析及边界见 [报告](../../docs/t12-perf-20261014.md)。接续运行产物先留指定Linux runs独立目录，再归档少量压缩日志/raw/来源/反汇编，不提交binary或waveform。
