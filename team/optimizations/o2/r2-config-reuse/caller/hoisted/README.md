# 8×32 普通 C caller：指针缓存与强 RVV 筛选

本目录保留早期 v1 草稿，并通过 [SCREEN_CONTRACT.md](SCREEN_CONTRACT.md) 定义本轮 v2 实验。实际结果为 `HOLD_CONTEXT_VARIATION`：匹配基线下包装改善已测得，但共同 vdot 的跨镜像上下文门槛未通过，未授予最优内核采用资格。完整数据与边界见 [RESULT.md](RESULT.md)。

## 修改了什么

[caller.c](caller.c) 在完整调用函数内缓存 context 中的 A、x、workspace、y、entry 指针，再按原语义逐字节打包、调用已合格 leaf、提取八个 INT32。接口类型继续使用 [父目录 caller.h](../caller.h)，原源码和既有证据不变。

这项优化不增加 `restrict`、字宽搬运、向量打包或对齐前置。A[256]、x[32]、y[8] 和464字节 workspace 必须有效且互不重叠；context 也必须与写区分离，指针字段在一次调用中保持稳定。workspace 的16字节对齐由类型属性规定。向量状态与公共 leaf 的现有调用要求继续适用。

`caller_full` 的指针捕获、栈保存/恢复、打包、实际间接调用和提取都包含在 full 测量内。内核选择与 context 初始化位于计时窗外，对所有方法采用相同规则。独立诊断阶段不与 full 相加；本轮仅测决定取舍所需的 full。

本轮新运行资格只覆盖 `caller_full`。源码中保留的 `caller_pack/core/extract` 是分阶段诊断入口，本轮没有为它们建立新的独立运行或周期资格；基础版本的历史诊断结果仍只属于基础版本。

## 工具分工

| 文件 | 用途 |
| --- | --- |
| `candidate.py`、`CONTRACT.md` | 原 v1 草稿，字节保持原样；不能单独表达 v2 的强 RVV 筛选范围 |
| [screen.py](screen.py) | v2 入口，复用冻结的团队 caller 引擎，生成完整36窗计划和五类 RVV 集合，按实际 ELF 选择数据绑定路径 |
| [checks.py](checks.py) | 跨镜像 ALLOC/BIN 白名单、匹配基线、针对性拒错、事前门槛计算；是外部分析身份，不事后加入旧构建快照 |
| [recheck.py](recheck.py) | 从封存载荷恢复到新临时目录，复算全部已执行案例、跨镜像门禁及最终决策；不启动 EMU |
| [SCREEN_CONTRACT.md](SCREEN_CONTRACT.md) | 固定输入、样本、资源和采用门槛 |
| [RESULT.md](RESULT.md) | 实际执行、取舍、限制与交付身份 |

没有修改官方程序或父目录判定器。私有适配仍调用原始路径、counter/ROB、完整输出、负控、输入身份与原文审计检查；仅将选中叶绑定到真实 ELF，并把旧摘要的144/96窗口描述修正为实际36/24。

## 优先复算已交付证据

在本提交完整仓库检出中运行，`SCREEN_REPO` 为该检出的绝对路径。优先复算整组证据；输出文件必须尚不存在：

```sh
python3 -B "$SCREEN_REPO/team/optimizations/o2/r2-config-reuse/caller/hoisted/recheck.py" \
  audit "$SCREEN_REPO/team/optimizations/o2/r2-config-reuse/caller/hoisted/evidence/screen-v2" \
  --output /tmp/hoisted-matrix-recheck-new.json
```

期望 `HOISTED_MATRIX_RECHECK_PASS`，但这表示证据和决策可复算，采用结论仍须看 `decision`：`STOP_SCREEN`、`HOLD_CONTEXT_VARIATION` 也可以得到审计 PASS。复算检查已封存的输入身份，不重新读取当时本机的 EMU、AM 或参考模型；新硬件或新机器的运行资格须另验。在 Linux/WSL 原生目录中，离线复算只需 Python 标准库和完整、字节匹配的仓库检出；检出须包含已跟踪的参考对象、冻结脚本和证据归档，不必安装 GNU RISC-V 工具链或启动 EMU。

需要只检查一个已执行案例时，以 h4 为例：

```sh
python3 -B "$SCREEN_REPO/team/optimizations/o2/r2-config-reuse/caller/hoisted/screen.py" \
  --caller hoisted --rvv 4 --repo "$SCREEN_REPO" \
  --action audit-archive \
  --archive "$SCREEN_REPO/team/optimizations/o2/r2-config-reuse/caller/hoisted/evidence/screen-v2/h4" \
  --output /tmp/hoisted-h4-recheck-new.json
```

其他标签 h0/h1/h2/h3 相应改变 `--rvv`；b4 使用 `--caller baseline --rvv 4`。只能审计实际交付的已完成案例；第一阶段停止时，未执行候选保留构建资格但没有运行归档。完整清单见 [证据索引](evidence/screen-v2/index.json)。

期望 `CALLER_ARCHIVE_RAW_AUDIT_PASS`，每正常进程36窗、24正式窗、重放36窗。重放用于确认一致性，不额外增加统计样本。解包逐项验证 ZIP/文件哈希并重新分析原文，不依赖旧运行目录的文件。

整组复算还可附加事后时序观察：将32条真实退休 vdot 按完整 ROB 分配代关联到 FU 接受/响应，再使用已验证的采样 tick 表示相对位置。`CONTEXT_OBSERVATIONS_AVAILABLE` 只表示该有限形态可明确提取；不支持时返回 `UNAVAILABLE`，不会改变筛选门槛。无越界时的三个区间也不是独立 pack/core/extract 计时，不能单凭它们认定缓存或预测器原因。

## 新建实验

使用 Linux 原生独立检出及仓库外的新输出根。现有 T17 运行身份、工具链、AM、参考模型和 flash 必须满足项目复现入口；不要修改旧锁或以另一个硬件镜像冒充固定输入。所有输出参数要求新路径。

先按 b4、h4、h0、h1、h2、h3 六个标签分别构建，例如：

```sh
python3 -B "$SCREEN_REPO/team/optimizations/o2/r2-config-reuse/caller/hoisted/screen.py" \
  --caller baseline --rvv 4 --repo "$SCREEN_REPO" --action build \
  --output "$SCREEN_RUN/build-b4-01"
```

其余镜像用 `--caller hoisted` 及对应索引、独立 `build-hN-01`。完成六个构建后执行：

```sh
python3 -B "$SCREEN_REPO/team/optimizations/o2/r2-config-reuse/caller/hoisted/checks.py" \
  preflight --root "$SCREEN_RUN" --output "$SCREEN_RUN/preflight-01.json"
python3 -B "$SCREEN_REPO/team/optimizations/o2/r2-config-reuse/caller/hoisted/checks.py" \
  rejections --root "$SCREEN_RUN" --output "$SCREEN_RUN/rejections-01.json"
```

全 ALLOC（含 BSS 布局）及 BIN 白名单必须通过。五个 hoisted 镜像只有唯一4字节选择字段与等长合同标识允许不同，不能忽略整个数据段或字符串段。新 baseline 与 hoisted 的有意 C/布局差异单独保留。

之后只运行 b4、h4 的 `--action run --build ... --operation-id ... --output ...`，各自完成负控→恢复→重放；再用 `--action audit` 和带 `--run` 的 `--action selftest` 完成原文审计及日志拒错。运行输出命名 `run-b4-01`、`run-h4-01`，与 `checks.py` 的矩阵入口一致。

`checks.py stage1 --root ... --output ...` 返回 `CONTINUE_RVV_SCREEN` 时，才串行执行 h0/h1/h2/h3，同样先 audit 再进入 `selection`。若返回 `STOP_SCREEN`，保留已完成结果并关闭本次试验。运行器和汇总器不会把历史 PASS 或未运行镜像算作合格样本。

实际启动脚本、回执、固定输入清单与本机定位随证据保存。封存时，将 `$SCREEN_RUN` 根目录的 JSON/log 映射为 `support.zip` 中的 `runtime/<原文件名>`；整组复算读取这个恢复后的映射。该次封存脚本保存在 support 的 `runtime/transport/seal-delivery.py`，不属于固定运行输入。脚本中个人绝对路径是原执行事实，复建须明确替换为新配置和新目录。驱动不支持盲目续跑未闭合的单个 campaign；发生中断先核实 state、日志、PID 和已有成果，不覆盖或重复副作用未知的操作。

## 使用与回退边界

本轮不修改 R5 默认。可选消费者通过同一个 `caller_context.entry` 调用已验证的8×32 leaf；公共汇编与返回的全128位槽语义原样保留。实际推荐方法及其覆盖范围以 RESULT 为准。

集成时编译本目录的 `caller.c`，并把父目录加入头文件搜索路径，以复用 `caller.h`；只链接一份 `caller_full` 等包装实现，不能同时编译父目录的原版 `caller.c`。[父入口的接口组装示例](../README.md#接口与编译)仍适用，叶函数声明、汇编或静态库使用对应的原公开交付，`caller_context.entry` 由调用端明确设置。若使用本轮观测总周期最低的 `firstdot_gemv_8x32_reuse_rvv`，须按 [firstdot 公共交付](../../../r2-vector-accum/FIRSTDOT_README.md)提供其声明和实现，不能误以为 config-reuse 库导出该符号；这仍是调用方的显式选择，不是本合同的自动采用结果。父目录的 `demo.c` 是独立的栈打包示例，其中 `gemv8` 直接选择 config-reuse/vdot，完全不调用 `caller_full`；它不会自动跟随本轮筛选结果。三个 demo 的正确性结果不能作为新包装或任何 RVV 的应用性能证据。

调用者须满足 [公共库平台前置](../../RUNTIME_README.md)：RV64/lp64d、VLEN128、VS 已启用，使用 vdot 时具有匹配扩展，并接受 leaf 对向量寄存器/配置的既有破坏约定。context、workspace、输入、输出须使用互不重叠的有效存储，生命周期覆盖整个调用。按验证时的 GNU/nexus-AM 编译入口重建最容易保持资格；改变优化、向量化、LTO 或其他编译条件时，旧 ELF/路径和性能 PASS 不会自动转移。

恢复父目录原 [caller.c](../caller.c) 并重新编译，即回到基础包装；稳定应用继续使用项目既有 [R5/G5 入口](../../../r2-select/STABLE.md)。新 caller、不同编译选项、输入布局或硬件均须按变化影响验证。结果不自动扩展到完整 LLM、其他尺寸、全局最优或 ASIC PPA。
