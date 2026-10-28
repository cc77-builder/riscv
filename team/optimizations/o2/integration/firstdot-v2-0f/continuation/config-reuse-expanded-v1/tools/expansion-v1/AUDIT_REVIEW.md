# 扩展配置复用矩阵：只读原文审计复核

本文件记录扩展审计工具的实现与主机验证，不代表新的 33 次目标运行已完成。新矩阵真实运行与审计结论由主控制器另行封存。

## 固定对象与边界

- 4 个尺寸：4×8、8×32、16×64、4×13；3 个数据集：0、1、2；firstdot/config-reuse 两种软件变体，共 24 个镜像。
- 计划实际目标进程：1 次 bit100 负控、24 次正常运行、8 次 dataset0 重放，共 33 次。
- 32 个正常/重放进程必须各有 24 个原文窗口，共 768 窗；正式计分窗口为 24×16=384。
- 8 个 dataset0 重放逐窗比较完整 sample 字典，共 192 对；12 个 firstdot 镜像对 qualified clean 基线逐窗比较完整 sample 字典，共 288 对。
- 本工具不启动 EMU/NEMU、不修改 RTL、不切换默认硬件、不上传代码。只有原文重解析过程使用临时目录，最终审计输出必须为 build/campaign 之外的新文件。
- 旧 V3 数据只作为主机测试夹具；旧探针目标进程不能计入新的 33 次运行。

## 证据门禁

1. 校验 Matrix 生成器的完整输入闭包、当前干净身份、硬件 profile、固定来源以及真实构建与 GNU 静态检查。
2. 共享比较 BIN 的准确集合为 12 个；完整共享映射在外层前后均校验。每进程只移除这 12 个比较角色，再加入该进程实际加载的 BIN、私有 AUX 和参考模型。实际命令、cwd、参考模型与故障环境必须逐项匹配。
3. 33 个 result 必须与 run-plan 的镜像、label、phase、replay、negative 和 canonical 顺序一致，不能缺漏、重用 PID、增添进程或保留活动 PID。
4. 逐进程重新读取 stdout/stderr，校验原文摘要和 runtime banner；调用既有协议验证器重新解析 windows/CSR、结果高 128 位、O2 观察器。原始 checker 的写入限定在临时副本，重新计算的数据必须与原窗口、观察器和缓存 sample 完全一致。
5. bit100 负控必须对应候选真实 ELF 指令 PC、vd=0、word=0x0388000b；后续恢复必须同 BIN、清理故障环境、绑定正确 golden reference，并用单调时钟证明负控先结束、恢复才开始。
6. 各实际 PID 绑定同一 boot_id、正整数 monotonic start/end 与 Popen/wait 包络；独立扫描所有包络重算峰值，要求不超过 workers（1—4），且处于总 campaign 包络中。恢复完成后才允许正式池，全部 23 个正式池任务结束后才允许 8 个重放任务。
7. UTC 字段只校验时区与格式，用作诊断；不使用 UTC 顺序或历史串行假设证明并发数。Popen/wait 包络提供保守的进程并发上界，不声称证明 OS 瞬时调度或 CPU 利用率。
8. 完整重算嵌套 results.summary、各尺寸 decisions、all_window_replay；验证 results/state 的 monotonic_proof 一致。4×13 可以没有收益，控制不一致可保留为 INCONCLUSIVE，不能改写成性能通过。
9. 审计开始和结束分别计算整个 campaign 文件树摘要，要求没有新旧文件变化并拒绝符号链接；使用 physical_before 保留原物理身份元组，避免旧审计器循环变量遮蔽该元组的错误。

## 主机验证

命令：

    python3 -B /home/riscv/riscv-lab/software-import-20261026/reviews/config-reuse/expansion-v1/test_raw_audit.py

最终结果：37 tests，6.889 秒，OK，exit code 0。

覆盖包含：

- 22 项时序与身份边界：4 并发正例、预算超额、boot/PID/label/phase 不匹配、缺项、布尔假整数、无效/反向/越界时钟、阶段屏障、未收尾进程、UTC 回拨可诊断而不影响单调证据。
- 6 项输入闭包与只读树封存：精确映射、缺项、多项、真实字节篡改、增添文件、符号链接。
- 4 项真实 results 构造 schema 检查：直接解析当前 Matrix.run 中 result=dict 的 AST，构造真实嵌套 summary 形状，拒绝旧扁平结构、统计篡改、多余字段。
- 5 项冻结 V3 原文夹具检查：实际 24 窗重解析、bit100 负控重解析、实际 BIN 摘要篡改、缓存 sample 篡改、原文篡改。正例同时证明临时夹具文件树未变化。

首次开发测试的一个拒错用例因新增 label/phase 前置门禁提前触发而失败；随后把该用例的 record/spec 同步改成错误 phase，以专门测试 phase 数量门禁。最终全量重跑通过。该调整只影响新测试夹具，未修改历史原始结果或摘要。

其他代理补充的完整 Matrix.run→audit_matrix 主机双替身组合检查发现了 results 决策中 dataset_decisions 的整数键经 JSON 变成字符串的问题；控制器已在生产者端统一为字符串键。此类组合测试仍是主机流程证据，不替代真实新矩阵的 UART/CSR 证据。

## 冻结摘要

| 文件 | SHA-256 |
| --- | --- |
| raw_audit.py | 9aeca96415e1d6153ae398fa653c949196426bf57caaea5692ee34c204de13cf |
| test_raw_audit.py | 7dc5510fa27f74942722e6fbcf48a10b76b8a70ecc80ef976c3f4da2772c23f7 |
| matrix.py（对接版本） | 0eecb8aaee9093b43030658eb75c30dbceb05a8156729922ce321fe0635839c9 |
| ../adapter-v3/probe.py（冻结参考） | 5c29a1a681e77c13e7342197993d4cc73e4f47b6457a3ea9efff972ee2c01cda |
| ../audit-scope-fix-v1/raw_audit_fixed.py（冻结参考） | 220dc6ae52de5d42a87cce09dde8dd23e789c075cc75b8bdb869f42efc6dade5 |

## 真实运行完成后的审计命令

    python3 -B raw_audit.py \
      --repo /home/riscv/riscv-lab/software-import-20261026/clean-02/checkout/source \
      --identity /home/riscv/riscv-lab/software-import-20261026/clean-02/identity/current.json \
      --matrix /home/riscv/riscv-lab/software-import-20261026/clean-02/matrix-build-01 \
      --matrix-run /home/riscv/riscv-lab/software-import-20261026/clean-02/matrix-run-01 \
      --build 新矩阵构建绝对路径 \
      --campaign 新矩阵运行绝对路径 \
      --output 原build与campaign目录外的全新审计JSON

真实结论只应在上述命令成功并生成 EXPANDED_MATRIX_LOCAL_RAW_AUDIT_PASS 后登记。工具输出明确保留 source_hardware_remeasured=false 和 portable_archive_audited=false：这是当前身份下的软件筛选矩阵审计，不是新 RTL PPA 测量，也未声称已验证独立可迁移归档。
