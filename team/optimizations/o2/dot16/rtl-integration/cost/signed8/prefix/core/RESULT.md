# Prefix core-build-02 与 smoke-02 工程结果

日期：2026-11-08 UTC。**外置 prefix 整核构建已完成；新 EMU 的 ABI 与原固定 reference 对齐，并实际通过同一六例合法差分 smoke。** 本记录不授予完整整核、G3、非法指令/trap 矩阵、应用性能或 PPA 资格。

> 同一prefix EMU已分别完成[K288](k288/RESULT.md)与[K768](k768/RESULT.md)固定完整调用。K768本次N／packedN均值为125509.5／108648.5（周期少13.4340%）；同次较快RVV packedP均值162987，与packedN比较为1.500131×（周期少33.33916%，prepare窗外）。K288八样本与旧f149相同，仅支持该固定例周期保持，没有新增硬件周期收益。两项各自只增加固定调用target_runtime资格和局部CSR观察；本页构建与原六例smoke的范围保持，不转授旧完整forward或新增G3、完整退休、正式性能及整核PPA资格。

## 范围与最小修订

沿用已闭合 prefix 候选及 `MinimalConfig` 单核、DiffTest 启用配置。source-02 仅在 Java generation 环境补回官方 `forkEnv` 已有的仓库 Espresso 资源 PATH，并固定该原工具身份；native PATH 未改，官方代码和工具未改。

时钟、复位、接口与延迟/吞吐沿冻结 `local-01/source-snapshot/PREFIX_CONTRACT.md`，SHA `22a4b7b6319f8c97a2f20a02e3c25237bce48d4fd77258ed54172547c493bf40`：128 位架构接口、同步高有效 valid reset、P/R 两槽、E0 接收/E1 推进/E2 最早响应、无阻塞 II=1。它们是原 FU 契约；本轮没有测定 core 物理频率或证明整核时序达标。

固定 builder SHA：`77f0d609f732a54c6376759ea2db1ed4b988945c93d8255bf1221774b8c81081`；输入锁 SHA：`01ebfe385c649d14e02f0f1a880dd60f5971cbb92c8219bc4a3a211b198d8ce4`。构建与 smoke 分别使用独立 `core-build-02`、`core-smoke-02`，同属：

`/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-20261107-main`

## 构建回执与关键身份

构建事实来自已核验 host 回执及 core result：operation `0250d6044ba18f5fd71831ae3131d2ce.90c1744b6b558fc1157d65c1e3c742eb`，host 起止 `2026-11-08T02:43:41.8722648Z`–`2026-11-08T03:08:23.4152327Z`，host 报告执行时长 1481.505 秒，exit 0、cleanup 完成。七个内部阶段均 exit 0、reaped/group_absent=true，终态 `PREFIX_CORE_BUILD_COMPLETE`。

| 产物 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `core-build-02/result.json` | 25,446 | `06b38d232feda7ea93e3b34d806888163a5abf89de916e63af185d383773a5e2` |
| `core-build-02/cwd/build/emu` | 71,489,976 | `6387d998c3f715a9ced1f44c4410f0f29f76780a96ec15c1830c8828ded6f887` |
| `core-build-02/cwd/build/generated-src/diffstate.h` | 8,446 | `6a2ce3ab51893908f74452522ab03c553cf7fa7e8aa25f74ea84d79aa45f044d` |
| `core-build-02/generated-files.json` | 444,907 | `2bf579a661d390d7c8d734580487c0ccb352e63b684471aa622498bddb102bc3` |
| `core-smoke-02/result.json` | 6,553 | `2ec969938a8c4f790e10ba7067befe22f890946b58f2a533276d3051c0cc6eda` |

## 实际 ABI 与六例结果

smoke 状态区间为 `03:20:25.020517`–`03:21:22.353701 UTC`，共 57.333184 秒。五命令均 exit 0 并回收；前后输入检查均输出 `INPUTS_UNCHANGED`。EMU argv、runtime inputs 和结果绑定上表新 EMU，没有复用旧运行 PASS。

原始 ABI 探针输出、布局记录与结果中的布局一致：复制长度 1400 B，全部字段偏移符合原固定 ABI。以下两份文件位于 smoke 原始包的 `core-smoke-02/` 内，须分别绑定身份：

| 文件 | 用途 | 字节数 | SHA-256 |
| --- | --- | ---: | --- |
| `abi-run.log` | 实际 ABI 探针的原始 stdout | 129 | `5d6e133fb80be4c75e3453364f6515b2a33ede5db81f4294f441fedb1238151e` |
| `abi-layout.json` | 同一布局对象的排版记录 | 170 | `6a4ec3322731720f73f878c2211620a17fffb4b7e0a1c454ebae642261e39137` |

两者解析后的 JSON 对象相等，字节数与 SHA 不相同；1400 B 是 ABI 复制长度，不是任一记录文件的大小。实际探针成功编译并运行，没有用预填布局代替原始输出。

使用原六例 BIN、flash、固定 feature1 NEMU、128 MB RAM、seed=1、300000 cycle 保护。日志有唯一 BEGIN、六例逐项 PASS、最终 `cases=6 dot8=2 dot16=4 failures=0`、正确 reference、实际 DiffTest 启用标记及 GOOD TRAP；未见原门禁覆盖的失败标记。原始 guest cycle 57336 只说明此次运行在保护上限内，不作为应用性能指标。

smoke 完整归档 [smoke-02/raw.zip](smoke-02/raw.zip) 为 **288,894 B**，SHA `d1f11eec2208bdf829d28830ad28c3eb23c09b9405ed8f286a195c784b3f90fe`。包内为 **28 原始文件 / 6,259,039 B**，加一份 manifest 共29成员；CRC、逐成员 SHA 与落盘字节已核对。归档审计见 [smoke-02/audit.json](smoke-02/audit.json)，实质复核见 [ACTUAL_REVIEW.md](smoke-02/run-journal-01/ACTUAL_REVIEW.md)。原始依据包括包内 `runtime-inputs.json`、`abi-run.log`、`abi-layout.json`、`run.log` 和五命令日志；[运行与收集记录](smoke-02/run-journal-01/) 保存 `launch.py`、`launch.ps1`、`collect.py`、`collect.ps1` 及 [host-receipts.json](smoke-02/run-journal-01/host-receipts.json)。

新增结论仅为 `fullcore_smoke_qualified=true`；`fullcore_qualified`、`application_performance_qualified`、`ppa_qualified` 保持 false。

## 构建选择归档、失败证据与恢复边界

构建选择归档已完成，原 Windows 工程 runs 根中的位置为 `dot16-prefix-20261107-main/core-build-02-archive-01/raw.zip`。发布入口及已核验身份如下：

| 文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| [build-02/raw.zip](build-02/raw.zip) | 31,214,736 | `2349b27a4f5ef7ad8cba3dd451e6fb49adcb7c1a5733b43f7b1810a9043829f8` |
| [build-02/audit.json](build-02/audit.json) | 2,569 | `79c61ca85a6b667458e279b03c258af961860d798c6ef98c95c2a0650fe77c5e` |

包内包含 **1711 个 payload 文件 / 208,239,924 B**，再加两份 manifest，共 **1713 成员**。其中生成文件1687个（包含本次 EMU 与所选 RTL 等，FIR 等未选项除外），另有13个构建控制文件、7个旧构建失败文件及4个审查文件。入包成员的 SHA、CRC 及源未变核对已经闭合；归档行为本身不新增功能、性能或 PPA 资格。

这是**选择归档**，没有装入全部约2.6 GB构建原件。[archive-selection.json](build-02/archive-selection.json) 逐项列出另 **1035 个生成文件 / 2,415,811,194 B** 的未入包范围；本次归档未重新计算这些文件的内容 SHA，不能把它们算进入包成员的内容核验结论。实际成员见 [archive-members.json](build-02/archive-members.json)，归档前库存见 [source-inventory-before.json](build-02/source-inventory-before.json)；归档实现、选择说明与原回执分别见 [archive.py](build-02/archive.py)、[PREPARATION.json](build-02/PREPARATION.json) 和 [host-receipts.json](build-02/host-receipts.json)。

**原 native 构建树及原件全部保留**，包括未入包文件和必要路径依赖。该包用于证据保存与追溯，恢复仍依赖冻结源码、工具、classpath/资源和实际构建路径；它不是可脱离原环境独立重建或运行的 standalone 包，不能据此删除原构建树。

`core-build-01` 的实际失败、输入与原始日志完整保留。原日志显示 Espresso 缺失后进入 QMC 展开并发生 Java heap OOM；这是当次生成环境/运行失败，不是 prefix 算法或事务逻辑失败的证据。source-02 的成功不改写旧失败记录。

本结果的功能范围限定于上述原六例合法 smoke。后继 K288 完整调用及更广整核覆盖由各自独立证据记录，本节不预赋予其 PASS、应用收益或其他候选资格。稳定生产默认及旧 f149 上的 NQ/PQ 观察边界保持；赛事提交仍由人工负责。
