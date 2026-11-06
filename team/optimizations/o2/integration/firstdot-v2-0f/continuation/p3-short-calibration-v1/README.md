# P3独立短校准

当前结论见[RESULT.md](RESULT.md)，冻结边界见[CONTRACT.md](CONTRACT.md)，下一轮见[NEXT_STEP.md](NEXT_STEP.md)。

context.py绑定上一轮冻结镜像/适配器；bounded.py负责自有进程组限额与原始日志，calibrate.py负责最多两项串行及前置门禁。test_supervisor.py为8项宿主进程机制，test_gates.py为8项宿主门禁。

本轮campaign已终止，不可重启或复用输出目录；只读复核已有证据。镜像和既有输入已核验；本轮运行器预冻结漏6项，保留失败，不在原位置修订。新正常吞吐与正式性能仍未测。
