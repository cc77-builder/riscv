# 8×32 普通 C 消费者：构建、运行、复算与回退

本目录把独立 `int8_t A[8][32]`、`int8_t x[32]` 与紧密 `int32_t y[8]` 接到已经合格的 config-reuse 公共内核，记录打包、完整内核调用、结果提取的实际成本。工程结论与全部数据见 [RESULT.md](RESULT.md)；基础合同见 [CONTRACT.md](CONTRACT.md)，指针缓存候选见 [hoisted/CONTRACT.md](hoisted/CONTRACT.md)。

**当前资格：基础 caller-v2 已完成实际负控、正常恢复和独立重放。`hoisted/` 只保留上轮未完成的候选源码与合同，未构建、未运行、无性能或采用资格；本次没有补跑该候选。**

## 接口与编译

`caller.h` 定义固定8×32上下文、464字节且16字节对齐的workspace、8个完整128位输出槽。消费者只提供标量C包装，最终调用哪个内核由 `context.entry` 明确选择：

```c
#include "caller.h"
#include "gemv.h"

/* A, x, y, workspace and context use distinct valid storage. */
struct caller_context context = {
    .a = &a[0][0],
    .x = x,
    .y = y,
    .workspace = &workspace,
    .entry = config_reuse_gemv_8x32_reuse_vdot,
};
caller_full(&context);
```

`workspace` 的类型为 `struct caller_workspace`，其类型自带16字节对齐要求。`a`、`x`、`y` 由调用方分配；context本身不与写区重叠、调用期间字段稳定。切到RVV只需把入口设为 `config_reuse_gemv_8x32_reuse_rvv`。不允许输入、输出、工作区相互重叠，也不允许把任意其他函数当成同一输出合同的leaf。

正常使用编译已验证的 `caller.c`。`hoisted/caller.c` 是尚未验证的局部缓存指针候选，只有另行认领、构建和实际运行后才能评估采用。它们导出相同的 `caller_full/pack/core/extract` 名称，因此不能同时链接。把本目录加入头文件搜索路径，另链接上一级 [公共库](../evidence/runtime-v1/library/libconfig_reuse_gemv.a)或未改动的 [public/gemv.S](../public/gemv.S)。公共函数的完整平台/向量状态前置条件继续见 [RUNTIME_README.md](../RUNTIME_README.md)。

`caller_full` 完成整个调用。其余三个入口只供分阶段诊断：`caller_pack` 只填充 packed；`caller_core` 要求 packed 已含完整 A/x 数据；`caller_extract` 要求 slots 中已有符合公共内核合同的八个完整结果槽。它们不独立替代 full。

上述片段说明接口组装，不另授予新布局的周期资格。每个ELF内，两种方法使用 `main.c` 中同一组全局guarded缓冲区和相同地址；不同ELF的布局可能变化。原README的栈版 `gemv8()` 由 `demo.c` 单独真实执行并检查结果，两者的周期范围不能混称。

## 固定 T17 上重新构建与运行

在Linux/WSL原生检出根执行。以下输出均须使用不存在的新路径，并位于源码、固定硬件、AM、原构建及原证据目录之外。旧失败输出保留，不隐式续跑。先按仓库协作规则确认任务与同机资源。

```sh
PPA_CALLER=team/optimizations/o2/r2-config-reuse/caller
PPA_IDENTITY=team/optimizations/o2/repro/evidence/clean-reproduction-v1/reports/identity-02.json
PPA_OUTPUT=/home/lizufan/riscv-lab/caller-new-round
```

基础消费者：

```sh
taskset -c 0-3 python3 "$PPA_CALLER/experiment.py" \
  --repo "$PWD" --identity "$PPA_IDENTITY" --action build \
  --output "$PPA_OUTPUT/build"

taskset -c 0-3 python3 "$PPA_CALLER/experiment.py" \
  --repo "$PWD" --identity "$PPA_IDENTITY" --action run \
  --build "$PPA_OUTPUT/build" --output "$PPA_OUTPUT/run" \
  --operation-id YOUR_UNIQUE_COORDINATED_OPERATION_ID
```

局部缓存候选使用同样的参数，把程序换成 `"$PPA_CALLER/hoisted/candidate.py"`，并使用另一组新输出目录。候选装配器会验证冻结的基础源码；它只在当前Python进程中选择候选生成规则，不改写基础程序或既有证据。

构建实际使用GNU `make -j4 --trace --output-sync=target`，逐个核对三份C编译命令、完整参考对象、最终ELF的16个公共leaf、编译后有限路径和ELF/BIN映射。正常运行始终启用真实DiffTest。`run` 自动顺序执行负控、同BIN正常恢复和独立正常重放，`state.json` 记录阶段与实际PID。性能EMU串行，禁止与同机重构建竞争；四核预算是总预算。

身份入口固定到已核验的T17来源。离线复算不要求这些原机器路径仍然存在；重新运行EMU则必须按实际身份配置核验物理输入。新机器安装、另一硬件身份或人工复现不能仅凭本目录的历史PASS自动获得资格。

## 原始证据审计与拒错

基础消费者的完整原始审计：

```sh
python3 "$PPA_CALLER/evidence.py" --action audit \
  --build "$PPA_OUTPUT/build" --run "$PPA_OUTPUT/run" \
  --output "$PPA_OUTPUT/audit.json"

python3 "$PPA_CALLER/selftest.py" \
  --build "$PPA_OUTPUT/build" --run "$PPA_OUTPUT/run" \
  --output "$PPA_OUTPUT/rejection-tests.json"
```

候选使用 `hoisted/candidate.py --repo "$PWD" --action audit` 或 `--action selftest`，其余对应参数相同。省略selftest的 `--run` 只做构建/路径拒错；完整测试还变异真实计数器ROB身份和调用退休压缩，要求触达具体语义门禁。所有变异写独立临时副本，不启动EMU。

每个合格版本的归档仅用一个 `payload.zip`、一个 `archive-manifest.json` 和原文审计摘要，保存源码快照、必要GNU产物/命令、输入闭包、三个进程回执、原始日志和结果；临时对象、缓存及重复反汇编不入包。失败的caller-v1另存冻结失败包和事实摘要，保留已产生的负控、未完成恢复的完整原始日志、实际命令/输入/产物与失败记录；没有重放回执或正常链PASS，也不进入正式性能统计。原生失败目录保持原样，具体位置与归档入口见结果页。基础归档的复算命令为：

```sh
python3 "$PPA_CALLER/evidence.py" --action audit-archive \
  --archive "$PPA_CALLER/evidence/baseline-v2/archive" \
  --output /tmp/caller-baseline-audit-new.json
```

本次没有 hoisted 归档或审计通过记录。未来完成该候选后，才可使用 `hoisted/candidate.py --repo "$PWD" --action audit-archive` 审计其独立归档。输出路径也必须为新路径。审计重新解包、校验载荷、从原始日志复算全部窗口、核对负控/正常恢复/独立重放和完整输入/命令/时间线；**不会新增EMU，也不声称当前外部物理文件已重新验证**。

## 范围与回退

full 是实际完整workspace调用窗；pack/core/extract是分别准备的独立诊断，不能相加冒称full或相减得到精确归因。pack/extract的两种方法标签执行相同代码，其差异只作为上下文对照。每方法主指标为三数据集各四次正式窗口；首次与预热另存，独立重放不重复计入均值。

软件候选是否采用由完整窗口和正确性决定，不能从指令数或单个阶段直接推导。本次比较分母是同轮同路径的 config-reuse/reuse RVV；没有在新 caller 下重选全部 basic/firstdot/RVV，因此不声称它是所有可能入口的全局最快者。基础消费者和未验证候选源码均保留；未来候选未获资格或发生退化时继续链接 `caller.c`，公共内核、头和库无需变动。R5稳定默认、已有公共库、RTL与官方权威代码均未修改。
