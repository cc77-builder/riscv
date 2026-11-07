# 未完成 P/PQ 目标作业的原始证据

本包仅保留超时与未闭合事实，不授目标正确性或性能资格。解释入口为[REFERENCE.md第8节](../../REFERENCE.md#pq-interrupted-01)和[结构化索引](../../PQ_TARGET_INTERRUPTED.json)。

- 原作业：`0844a5921b2fa4d9e47903bfc930fdee.ed242368865ac5da0771e8e56eae7564`，外层30000秒超时；两臂原状态仍RUNNING。
- `raw.zip`：136个原始/回读成员，1,916,252B；SHA `e3c39cbc5b4369f67377522b1d46433b131fc6194ed38123b5bf9c38a5e2251e`。
- `manifest.json`：每份原文件的路径、大小、SHA与收录状态；2个大镜像留在原路径且未改动。清单SHA `8a7ffa59c53e4f8f30ba47b7ab9e52ea81e818882794a96528e4c3ad9bd7b515`。
- `external-operation.json`：本轮查询到的原ChatPC回执；Windows清理字段不等于历史WSL reap证明。
- `current-readback.json`：主端独立读取原日志/状态及本轮进程观察的实际回执。
- `clock-observations.json`：本轮另一次时钟区间观测；不能倒推旧超时根因，也不证明稳定频率误差。

归档操作 `49cbde030e5643f0cccfca5cec8a79c1.9b0ab533a4d8ae169302761413e473a7` 于2026-11-07 09:24:51–09:24:52 UTC退出0、清理完成。所有ZIP成员读回CRC/大小/SHA，原来源再次核SHA未变。没有新guest、构建或官方程序修改。
