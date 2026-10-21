# O1/O2 同镜像公平周期对比

当前整合后的 live 入口要求完整源码/依赖库存及相同原生构建合同。先以 `fullcore/build_fullcore.py` 生成新的 O2 回执，再用 `build_o1.py --o2-build /absolute/new/o2-build --output /absolute/new/o1-build` 重建配对参考；`compare.py` 用 `--o1-pins`、`--o2-pins` 显式选择新回执。旧回执使用封存检查器复算，不能补写合同后交给当前 live 入口。归档校验在 Python 优化模式下仍生效。

以下性能数字仍属于原固定实验；[James 整合与修复记录](../../../docs/o2-o3-integration-20261020.md)另行绑定当前验证范围。

**G4公平测量、Linux原始日志严格重审及Windows全量离线复算完成，本地保存，未推送GitHub。** 完成时间：2026-10-19T11:34:55.879421+00:00。正式T16报告继续后置。

| 场景 | O1 vdot均值cycles | O2 vdot均值cycles | O2周期降低 | O2相对实测RVV |
| --- | ---: | ---: | ---: | ---: |
| 单次点积 | 71.000 | 71.000 | 0.00% | 1.201× |
| 依赖链256 | 1857.000 | 1857.000 | 0.00% | 2.930× |
| 四路独立点积128 | 362.500 | 221.000 | 39.03% | 3.068× |
| 加载/计算/存储64 | 1127.500 | 1127.500 | 0.00% | 1.005× |

独立batch相对本次新测O1降低39.03%，至少10%的预定工程目标达到。超过2%的场景均值退化调查项：无。

## 本次实测范围

两模式使用原16份冻结镜像，实际新跑36项（32次首次镜像运行＋4次代表batch镜像重放），478个校验窗口，192条正式性能窗口。每场景每模式每方法为3数据集×4measured＝12条样本；first/warmup和重放完整保留，重放不增加独立样本数。

周期降低按1-sum(O2 custom)/sum(O1 custom)，加速比按该模式本次实测sum(RVV)/sum(custom)。每组逐dataset/repeat/seq/镜像配对，机器码、工作量及退休指令一致；未扣循环/屏障或空窗开销。历史362.50/678没有作为本次统计输入。single不是FU固有延迟，batch四路同输入独立目的不代表任意GEMV收益。

每个作业通过真实DiffTest、约定输出/128位高位/非scratch寄存器/CSR/哨兵、计数器与全局周期窗口核验，以及各自O1/O2完整协议和有限排空门禁；致命错误文本显式拒绝。冻结manifest明确允许各内核的scratch寄存器范围，scratch_control也须通过；不把允许破坏的scratch当成全部32寄存器逐位相同。额外4次batch重放逐seq周期与退休数一致。30项主机测试通过；全部原始stdout/stderr、真实退出码、版本、输入和检查器摘要保留。

## 可复算材料

[测量合同](CONTRACT.md) · [封存证据](../evidence/20261019-performance-ab/README.md)

原始工作根：/home/riscv/riscv-lab/o2-performance-20261019。results-01下有逐窗口samples.csv、各模式summary.csv、配对comparison.csv和性能结果与工程记录.md；verification.json为严格原流重审。Windows交付目录为D:/yanyi/riscv大赛/doc/O1_O2同镜像性能对比_20261019。

## 硬件与工具身份

| 项目 | O1 | O2 |
| --- | --- | --- |
| 实测EMU SHA-256 | 6699225b76ceae479060741026683bb03de069c1e10a4a94e463304ba1e322d0 | ac0123280bf6c742d27a7650505bc1d91db350d1519806edfd0be9c7ea208a57 |
| 构建源码提交 | a239dace720b32216e83fb5a514930d334c69a26 | b218cbc6e6b135e4ff219a902a9284a59d3c82c9 |
| 来源 | 本轮从相同硬件输入重建 | 复用G3已验收固定EMU |
| O1_HANDOFF/O2_ELASTIC | 1/0 | 0/1 |
| O1_TRACE/O2_TRACE | 1/0 | 0/1 |

429项硬件源码与21236项依赖逐字节相同，MinimalConfig/单核/VLEN128/单线程EMU；共同FUSED_INPUT1、T12_TRACE0、T13_TRACE1。各自合法协议观察器只提供只读观察，共同T13提供全局周期/退休计数。

路径归一化后的实际Verilator/C++命令、七类工具版本日志一致；实际LLVM19.1.7编译器由构建过程/proc记录并核对。j2、12G JVM、O3/O0；最多两个单线程EMU。新O1采用外置产品目录，原G3的1687份非对象生成文件已恢复并验证原始SHA，旧O2 EMU不覆盖。硬件构建身份、运行工具身份与后续文档/封存提交分别记录，不以文档提交冒称重构建。

## 复跑

在完整checkout中使用全新输出目录：

    python3 -B team/optimizations/o2/fullcore/build_fullcore.py --output /absolute/new/o2-build
    python3 -B team/optimizations/o2/performance/build_o1.py --o2-build /absolute/new/o2-build --output /absolute/new/o1-build
    python3 -B team/optimizations/o2/performance/compare.py --o1-pins /absolute/new/o1-build/hardware-inputs.json --o2-pins /absolute/new/o2-build/hardware-inputs.json --images /absolute/restored/performance-images --reference /absolute/restored/reference.so --flash /absolute/restored/boot-flash.bin --output /absolute/new/campaign
    python3 -B team/optimizations/o2/performance/results.py --campaign /absolute/completed/campaign --output /absolute/new/results

第一步要求当前 checkout 的 build/ 不存在；使用新的完整 checkout，保留已有构建和证据。后两步使用第一步同一源码、依赖和工具环境；compare 的 images/reference/flash 必须恢复完整已核验输入，不能只复制或重命名 bin。默认路径绑定原机器固定输入，以上显式参数须按实际恢复目录填写。不要重启已完成campaign或覆盖封存输出。本轮不是T17新机器完整构建复现。

## 取舍边界

本次确认同镜像的RTL周期收益；没有Fmax/面积/功耗/PPA、官方计分或最终采用结论。O2默认关闭。后续按G5结合O3应用、O4时序/结构与O5/T17独立复现、成员人工ACK决定是否采用，再集中编写T16/T18材料。本任务未自动执行这些后续工作。

## 交付复核

Windows原生Python 3.13.2全量离线复算通过，覆盖36项作业、478个窗口、192条正式性能窗口及4项重放。见[原生复算回执](../evidence/20261019-performance-ab/delivery/windows-portable-audit.json)。它复核封存记录，不另跑EMU，也不替代Linux构建来源审核。

交付时补齐了原冻结功能生成器依赖的两份模型语料，逐字节取自运行工具提交63b95a5并绑定Git blob及SHA-256；原镜像、测量日志和646份主封存payload均未改变。原30项主机测试及新增3项语料绑定检查共33项通过；首次封装复算失败和修复后成功记录均保留。Windows请用Python UTF-8模式执行：

    python -X utf8 -B performance/portable.py --archive evidence/20261019-performance-ab --campaign campaign-01 --output /absolute/new/portable-verification.json

上述相对路径适用于Windows交付目录；仓库内对应team/optimizations/o2下的路径。
