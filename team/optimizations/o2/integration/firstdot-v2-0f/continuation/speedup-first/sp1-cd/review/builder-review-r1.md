# SP1-C 新构建器独立复核（执行前）

结论：**GO_BUILD_ONLY。** 这仅准入新 EMU 构建，不代表目标程序验证或性能门槛通过。实际 freeze 必须成功，构建器身份必须与 JSON 中 SHA 一致。

初审发现的两项缺口均已修正：

1. 新增 Verilator include/runtime 源码与 `verilated.mk` 冻结，并补 LLVM/GCC 内建头文件、系统头文件及启动对象/标准库。
2. make 根进程正常或异常结束后都扫描并清理整个进程组，记录清理结果，拒绝活后代残留。独立宿主夹具特意让根先以 0 退出、留一个 sleep 子进程；本轮检查确认仍能发现并清理该后代。该夹具没有运行构建或 EMU/NEMU。

原已通过项继续成立：显式候选 cwd 与 NOOP_HOME/DESIGN_DIR/MILL_WORKSPACE_ROOT；环境白名单；有效的 PGO/trace/coverage/snapshot/DRAMsim3/ResetGen 关闭；CPU4/5、-j2、12G JVM；输出只落候选 build/out；旧稳定 EMU 与主仓库两份未采用 RTL 前后受保护。

额外补录了 126 依赖 HEAD 和候选私有 Git 版本元数据。构建后仍需核验生成 HDL、SP1 观察器 schema、新 EMU 与实际运行库身份，按新附录另行准入五角色目标探针。目标阶段不能沿用本 GO 代替完整运行合同。

`builder-review.json` 包含最终 SHA 与宿主检查结果。`builder-review-initial-hold.json` 保留初审失败项，未覆盖历史结论。
