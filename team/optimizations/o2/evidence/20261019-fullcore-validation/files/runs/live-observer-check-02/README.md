# core-02 的独立 hello 观察审查

冻结检查器 e2d9c06 复读新 core-02 的完整 hello 原流，退出码 0、O2_TRACE_PASS；正式 runner 自身记录 HELLO_VADD_PASS。324 个 STATE、165 个 ROB redirect / VFEX4 redirect，已满足按全局 cycle 的下一拍匹配。实际 schema 仍为 ROB48、FTQ8、VLEN128、vpu195、perf577。

同一冻结新版检查器重新读 live-observer-check-01 的旧不可变安全前缀，require_complete=False：正常完成，状态明确是 O2_PARTIAL_TRACE_AUDIT。旧冻结检查器的原 rc=1 反例仍保留在 01 目录。未修改旧日志来通过检查。

hello 无 VDOT/DIV 请求，不构成两槽功能、反压、取消、覆盖完成或 G3 通过证据。negative-vdot 与 functional-1 正在运行，快照时尚未出现第一笔 VDOT；旧 O1 同镜像首 ENQUEUE 约 cycle311080，仅供等待估计。所有命令、源 SHA、源提交及日志 SHA 见 diagnostic.json；本次没有启动 EMU，没有修改运行工具或源日志。
