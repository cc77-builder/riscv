# Config-reuse 数据集与尺寸扩展合同 v1

合同 ID：zjhwork-clean-config-reuse-4shape-3dataset-matrix-v1。

## 范围与输入身份

只扩展软件配置复用的测试范围，使用 clean-02 的 c823a8786e052c6e26f6915563c42b6d730dd8e3 源码组合，以及 0f12df675378556670afd0dd2153f47fcb330610 硬件。身份以 clean-02/identity/current.json 和物理检查为准。沿用冻结 adapter-v3 的 26 个新增源码及 39 个已有依赖的原字节锁，禁止改旧生成器、旧门禁、旧结果和生产 RTL。冻结 probe.py 等四件工具另有硬编码 SHA-256 校验；新控制器、审计器及本合同进入本轮构建和运行的源文件闭包。

四个尺寸是 4×8、8×32、16×64、4×13（shard 1、3、5、7）。每个尺寸使用 dataset 0、1、2，每组分别构建 firstdot 和 config-reuse，总计 24 个新镜像。固定调用计划、C ABI、seed、RAM、最大周期、输入生成及 full128/NEMU/CSR/O2 门禁均复用原工具。没有额外普通公共 C 应用测试，不更改稳定默认方案。

## 新运行清单与并发

每轮严格创建 33 个新的 EMU 进程，旧 5 进程探针不能充当本轮样本：

1. 8×32/dataset0/config-reuse 的 bit100 负控，要求实际首条 custom PC、word=0x0388000b、vd=0，故障能使差分检查失败。
2. 同一 BIN 使用正常 NEMU 的恢复运行，负控环境必须清除。恢复算入 24 次正式正常运行。
3. 恢复通过后运行剩余 23 个正式镜像。
4. 全部正式运行及其语义检查通过后，运行 dataset0 下四个尺寸、两个变体的 8 次独立重放。

CLI 的 --workers 为整数 1..4，且不得超过当前 CPU affinity 数量；允许 CPU affinity 数量最多为 4。负控与恢复串行。正式阶段和重放阶段分别使用有界线程池，并有完整阶段屏障。每项使用私有运行目录和私有运行模块/计时闭包。失败后停止提交新任务，已经启动的任务完成后保留证据，再以 FAILED 结束。不支持覆写或原地恢复部分轮次；修复后创建新的输出目录并重跑完整 33 项，旧轮次保留。

每个进程记录真实 PID、boot_id、从冻结 spawn 的 Popen/wait 入口之前到返回/等待之后的 monotonic_ns 包络。该包络是保守的执行容量证明，包含极少启动与落盘开销，不声称为精确操作系统运行重叠时间。UTC 仅供诊断，不参与阶段顺序或并发上限判断。记录必须处于整个 campaign 的同一 boot_id/单调边界内，PID 唯一，包络峰值不超过 workers。负控完成早于恢复，恢复完成早于剩余正式阶段，全部正式完成早于任何重放。

## 镜像闭包与加载角色

12 个干净合格 firstdot 对照 BIN 的路径/哈希都保存在完整 runtime-inputs.json，并在每个新进程前后校验完整映射。旧检查器把任何 /vdot-perf.bin 文件项视为“当前实际加载镜像”；因此 process_inputs 只从单进程映射去掉明确列出的这 12 个对照路径，不能宽泛忽略未知 BIN。execute 会加入当前实际加载的唯一 BIN；它仍必须与运行命令、镜像清单、GNU、ELF、输入、全核日志绑定。独立审计重新构建完整外层映射与单进程角色映射。

每个新 firstdot 镜像必须与相应 clean 合格镜像的完整 ELF ALLOC、入口、BIN、机器对象、数据、固定槽位、构建工具链和 AM 身份一致；S1 的两个 RVV 8 KiB 槽位也必须一致。旧历史性能数字不移植为新样本。

## 功能与性能判定

32 个正常/重放进程各有 24 个完整窗口，共 768 窗。24 个正式进程包含 384 个 measured 窗和 192 个 first/warmup 窗；8 个重放包含 192 窗。对 12 个新 firstdot 的全部 288 窗与对应 clean 正常进程的完整 sample 字典比较；8 个重放的全部 192 窗与本轮对应正式进程的完整 sample 字典比较。不能只比较均值或 cycles。

未改动 RVV 控制单元的全部六窗按 seq/cycles/instructions 比较；优化前面调用可能平移后续绝对计数器和 tick，因此跨变体不要求绝对计数器值相同，各自仍受原始 CSR 与精确退休门禁约束。

每种尺寸分别形成八个 variant/software/method 单元，每单元有 12 个 measured 样本；同时按三个 dataset 各自四个样本判定，聚合总数必须等于三个 dataset 总数。主候选为 config-reuse/reuse/vdot，必须在聚合及每个 dataset 上均严格小于 firstdot/reuse/vdot 和同条件四个 RVV 单元中最快者，才标 PERFORMANCE_CANDIDATE。没有人为百分比阈值，少量确定性样本只描述当前条件，不宣称统计显著性。

任一其他配对单元退化、未改变的 RVV 控制异常、firstdot 干净对照异常或重放不一致，都标 INCONCLUSIVE；任何 dataset 主项持平或落后且无独立异常，则标 REJECT。不能用全局平均掩盖某个数据集或单元格退化。四个尺寸允许不同结论，4×13 不必获益才算完成范围测试。

CURRENT_CONFIG_REUSE_MATRIX_SCREEN_COMPLETE 只说明完整测试流程结束、原功能门禁完成；收益由各尺寸 decisions 明确给出。不能据该状态单独声称方案全面变快、普通 C 应用通过、默认已切换、RTL/PPA/功耗改善。最终原始日志独立审计通过后，才归档为可信结果。

## 接口与产物

matrix.py 提供 inventory、run_specs、process_inputs、assess、decide_shape、validate_records、validate_timing、validate_recovery 纯函数，以及 Matrix 的 build、selected、runtime、common_inputs、evaluate 和 run。raw_audit.py 独立重读进程原始日志及同条件比较，不接受缓存状态替代。

构建目录包含 images.json、pairs.json、baseline-current.json、matrix-build.json 和 state.json。运行目录包含原始 runs、负控夹具、run-plan.json、runtime-inputs.json、parent-identity.json、configuration.json、hardware-profile.json、completed-runs.json、results.json、state.json。最终 completed-runs 按固定清单排序，不按并发完成顺序排序。每个 result.json 持有 label、phase、PID、monotonic 包络及原工具的日志/输入哈希。

本轮工具只支持新目录 build/run，不发布、不推送、不修改 MAIN 的既有文件。用户看过结果后再决定后续复用范围。
