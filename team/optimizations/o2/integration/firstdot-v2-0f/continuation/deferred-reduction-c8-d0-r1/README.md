# C8 dataset0探针R1

状态：**HOLD_ANCHOR_AND_GAIN_SCREEN**。本目录是独立软件试验；当前正式版本仍为0f＋firstdot V2＋原C8。

从[RESULT.md](RESULT.md)查看采用决定、原门槛、周期和未测项；[RESULT.json](RESULT.json)保存完整数据；[R1_CONTRACT.md](R1_CONTRACT.md)约束本轮改动；[evidence/manifest.json](evidence/manifest.json)绑定全部原始证据。

执行顺序为：build_probe.py构建A/B → verify_probe.py静态审计 → test_probe.py负控 → audit_overhead.py开销与宿主审计 → run_probe.py freeze冻结 → run_probe.py run最多5串行进程。实际只启动2个目标进程；A门槛失败后停止。本轮已结束，禁止在此证据目录重跑、覆盖或继续后3项。新的目标运行须另轮授权并使用新目录/新冻结身份。

四个算术叶和计时包装来自原合同。R1只从目标端移出重复校验器自检，并补实际线程亲和性审计。所有目标命令、环境、GNU依赖、原输出及封存源码可由归档清单定位。大文件使用gzip；先核对stored_sha256，再解压核对sha256。

[下一轮指令](NEXT_STEP.md)仅为只读归因建议，本轮未开始下一项。
