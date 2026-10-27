# 固定 A、连续 x 的 8×32 可选 C 消费者

本模块把同一块 8×32 INT8 权重与 N 个连续输入向量组成一次完整调用。`fixed_packed` 在该调用内只准备一次 A，再逐步复制 x；`fixed_split` 直接使用独立 A/X。两者均调用既有叶函数，保存每一步的完整 128 位槽并提取 INT32 输出。

采用结论、全部五种 RVV 的比较和验证状态见 [RESULT.md](RESULT.md)；预先固定的范围与门槛见 [CONTRACT.md](CONTRACT.md)。这是固定 A 生命周期的有界工程示例，没有接入真实 LLM，也没有改变 R5 默认或生产 RTL。

## 接口与生命周期

`fixed.h` 定义两个普通 C 函数：

```c
void fixed_packed(struct fixed_context *context);
void fixed_split(struct fixed_context *context);
```

| 字段 | 调用方提供的有效空间与含义 |
| --- | --- |
| `a` | 行优先 `int8_t A[8][32]`，256 字节，整个 stream 内固定 |
| `x` | 连续 N 个 `int8_t[32]`，步长 32 字节 |
| `y` | 连续 N×8 个 `int32_t`，自然对齐 |
| `slots` | 连续 N×8 个 `caller_slot`；每槽 16 字节，首地址 16 字节对齐 |
| `packed` | 288 字节临时空间；packed 使用，split 保持不变 |
| `packed_entry` | 一次消费 `[A 256B][x 32B]` 的两参数叶函数 |
| `split_entry` | 一次消费独立 A、x、slots 的三参数叶函数 |
| `count` | 取得资格的有效值严格为 1 或 4；其他值不在合同内 |

A/X 允许任意字节对齐。五个缓冲区和 64 字节 context 必须互不重叠，调用期间输入、count、函数指针保持稳定。没有参数检查、动态分配或跨调用缓存。每个 slot 的低32位为有符号点积结果，高96位为零。每次新 stream 的 packed 路径仍准备一次 A；这不等于跨 stream 永久缓存权重。

平台为已固定的 GNU C11 / RV64 `lp64d` / VLEN128，调用者先启用 VS。调用会破坏向量寄存器及配置，返回时 `VL=8,VTYPE=0,VSTART=0,VCSR=7`。时钟、复位和 FU 接口不变；本模块没有新的硬件频率、面积或功耗结论。

### 显式选择叶函数

`public/fixed_entries.h` 提供 packed 声明，并通过 `fixed.h` / `split.h` 提供 split 声明。

| 算法身份 | packed 符号 | split 符号 |
| --- | --- | --- |
| S3/reuse vdot | `config_reuse_gemv_8x32_reuse_vdot` | `split_gemv_8x32_vdot` |
| S0/basic RVV | `r4_gemv_8x32_basic_rvv` | `split_gemv_8x32_rvv0` |
| S0/reuse RVV | `r4_gemv_8x32_reuse_rvv` | `split_gemv_8x32_rvv1` |
| S3/basic RVV | `config_reuse_gemv_8x32_basic_rvv` | `split_gemv_8x32_rvv2` |
| firstdot/reuse RVV | `firstdot_gemv_8x32_reuse_rvv` | `split_gemv_8x32_rvv3` |
| S3/reuse RVV | `config_reuse_gemv_8x32_reuse_rvv` | `split_gemv_8x32_rvv4` |

调用示例由调用者传入已选择的 split 叶函数：

```c
#include "fixed_entries.h"

void consume_four(const int8_t *a, const int8_t *x, int32_t *y,
                  split_leaf selected_entry) {
    _Alignas(16) struct caller_slot full_slots[32];
    int8_t packed[288];
    struct fixed_context context = {
        .a = a, .x = x, .y = y, .slots = full_slots, .packed = packed,
        .packed_entry = config_reuse_gemv_8x32_reuse_vdot,
        .split_entry = selected_entry, .count = 4
    };
    fixed_split(&context);
}
```

完整可编译示例、全部函数的链接检查和静态库由 [library.py](library.py) 生成。`libxs_fixed_weight_8x32.a` 是独立可选库，包含 `fixed.o / gemv.o / strong.o / kernels.o`。**不要与定义相同 packed、config-reuse、r4、firstdot 或 split 符号的其他库混链**；特别是旧 R5/S1 中存在同名 `r4_*` 实现，静态库链接顺序可能选择错误对象。保留 `-march=rv64gv -mabi=lp64d -mno-relax`，最终链接禁用 relaxation。

公开库的 27 个函数均从实际 archive 成员抽取，并在最终完成重定位的 ELF 中与被验证程序逐字节比较。链接验收不额外授予 ISA 运行资格；库回执通过同一 BIN SHA 与本模块的实际运行证据关联。

## 测量范围与结果解读

计时覆盖一次完整 stream：包装/上下文读取、packed 的一次 A 复制、全部 x 更新、N 次叶调用、循环控制、完整槽写入及紧凑 INT32 提取。输入、context、guard 和独立 golden 的准备在两边计时外。每个完整 stream 前只有一次匹配 N 的 RVV conditioning；序列内部不插入检查、UART 或逐步预热。

N=4 是主组，N=1 是初始化对照。每组分别在五种 RVV 中选择最快者，不能跨 N 共用赢家。每 N/普通方法有12个正式样本，覆盖三个数据集和正反两种调用次序；锚点按数据集检查上下文稳定性。总周期/N 是**包含初始化的摊销均值**，不能通过 N1/N4 相减推导纯稳态成本。

结果只适用于本合同的普通 C 包装、标量复制方式、输入形状、预热与调用计划。接口收益与同接口中的 vdot/RVV 算法差异分别报告；局部周期、指令数和 FU 指标不代表完整应用性能。

## 构建与新运行

使用 Linux/WSL 原生目录。NTFS 发布树只用于编辑、Windows 原生 Git 暂存和发布。先核实协调 Issue、四核总预算及受保护输入；所有输出必须是新目录，下面命令不用于覆盖或续跑旧实验。

```bash
export FW_REPO=/absolute/published/checkout
export FW_OUT=/absolute/new/fixed-weight-attempt
export FW_MODULE="$FW_REPO/team/optimizations/o2/r2-config-reuse/caller/fixed-weight"

taskset -c 0-3 python3 -B "$FW_MODULE/run.py" \
  --repo "$FW_REPO" --action build --output "$FW_OUT/build"

taskset -c 0-3 python3 -B "$FW_MODULE/harness_check.py" \
  --build "$FW_OUT/build" --output "$FW_OUT/host"

taskset -c 0-3 python3 -B "$FW_MODULE/run.py" \
  --repo "$FW_REPO" --action run --build "$FW_OUT/build" \
  --output "$FW_OUT/run" --operation-id 'unique-fixed-weight-operation'
```

CPU 0～3 只是本机例子；实际 cpuset 不同或不足四核时使用实际获准集合。运行器内部三次 EMU 串行：真实 vd0 bit100 负控、正常恢复、独立重放；每次上限 8,000,000 模拟周期和 7200 宿主秒。预算到达、进程消失或单项 PASS 都不代表整体完成。未知交付只查询原 operation、PID、state 和日志。

本入口固定复用 T17 `identity-02.json`、EMU、正常 NEMU、AM 和 flash。它们的实际路径及 SHA 在父 identity 中；需要按记录恢复相同身份。这里提供新软件构建/运行入口，尚未取得任意新机器安装或历史输入任意路径迁移资格。旧官方程序、冻结输入、失败证据及历史合同保持原样。

## 完整验收与离线复算

正常运行必须同时满足 168 个功能 stream、8 个运行中判定负控、504 个计时窗口、15,104 条 vdot 提交、完整退休/计数 CSR/O2 轨迹和恢复/重放一致；具体状态以封存原文审计为准。

```bash
python3 -B "$FW_MODULE/mutations.py" --build "$FW_OUT/build" \
  --run "$FW_OUT/run" --output "$FW_OUT/mutations.json"
python3 -B "$FW_MODULE/statistics_check.py" --build "$FW_OUT/build" \
  --run "$FW_OUT/run" --output "$FW_OUT/statistics.json"
python3 -B "$FW_MODULE/library.py" --qualified-build "$FW_OUT/build" \
  --output "$FW_OUT/library"
python3 -B "$FW_MODULE/archive.py" --action pack \
  --build "$FW_OUT/build" --run "$FW_OUT/run" --output "$FW_OUT/archive"
python3 -B "$FW_MODULE/archive.py" --action audit-snapshot \
  --archive "$FW_OUT/archive" --output "$FW_OUT/snapshot-audit"
```

这些后处理放在性能 EMU 全部结束后执行，不再启动 EMU。`mutations.py` 不传 `--run` 时只检查实际 ELF 和合成门槛反例，不代表原始运行资格。

`audit-snapshot` 解包完整原文，复制归档源码闭包、原运行的固定父 identity 和发布树中已绑定的三个审计器，在新 Python 进程复算。旧 gate 的六次 `git show BASE:path` 保持不变：归档额外保留原 BASE commit、路径上的 tree 和六个 checker blob，共19个原始对象。子进程临时仓库只导入这些对象，禁用全局/系统 Git 配置和模板，并检查没有 alternates；它不借用原 Git 对象缓存，也不代表完整开发仓库。临时 HEAD 指向原 BASE 只用于旧 provenance 检查，当前软件身份仍由构建回执的逐文件 SHA 确认。

冻结的 T17 探针检查 Python 文件/目录访问和显式子进程路径，拒绝原软件、原运行及相关外部物理目录；它不是 OS 沙箱或新机器安装测试。启动该命令仍需要本提交的源码 checkout，内层复算不需要完整 Git 历史。离线审计不重新验证当前外部 EMU/NEMU 实物。

发布的主 ZIP 采用 `fixed-weight-archive-parts-v1` 传输：原始 17,287,829 字节 ZIP 分为三段，原 `archive-manifest.json`、ZIP SHA256 和冻结 `archive.py` 均不变。这是为适配连接器的单次请求大小限制；它没有改变实验执行方式或资格合同。先在 checkout 外重组，再运行原审计器：

```bash
python3 -B "$FW_MODULE/restore_archive.py" --output "$FW_OUT/published-archive"
python3 -B "$FW_MODULE/archive.py" --action audit-snapshot \
  --archive "$FW_OUT/published-archive" --output "$FW_OUT/published-audit"
```

`restore_archive.py` 检查每段大小/哈希、顺序、完整 ZIP 哈希及五份原始元数据，拒绝覆盖已有输出；损坏时不会生成已完成的 `payload.zip`，保留未完成目录用于检查。重组本身只证明传输身份，完整证据资格仍由原审计器判断。三段和 `transport.json` 必须一起取得。

需要 Python、Git 以及原父审计器要求的已安装工具；不需要原 EMU。启动器也会调用冻结 checker 的六次 `git show`，因此普通源码 checkout 须具有原 BASE 对象。对仅含文件的快照或缺少该历史的浅检出，可在**独立检出**中先导入包内的原始对象，不改变分支或 index：

```bash
git -C "$FW_REPO" index-pack --stdin < "$FW_OUT/published-archive/history/objects.pack"
```

该对象包只含原 commit、路径 tree 和六个 checker blob，共 19 个对象；它不是完整仓库备份。本次交付的分片正向恢复、损坏字节、错误顺序和已有输出拒绝记录见 `evidence/qualified-v1/recovery-1432/`。

主机检查针对实际 C 包装和 judge：504 个场景使用 scalar leaf/CSR 替身；其中84个场景对每个受检字节翻转 bit0，共177,408次，另有336次替身 CSR 故障。它不执行六种 RVV/vdot 机器实现，也不运行 guest 的计时/UART main；不要与目标程序的504计时窗口混为同一覆盖。

## 回退和接续

本模块是独立可选入口，没有注册 dispatcher 或覆盖现有库。调用方恢复原 API 调用、原头文件和库链接，并按已有 R5/旧 packed/split 的相应合同准备输入与输出后，可移除本模块链接。单独移除库不会自动改写 `fixed_packed` / `fixed_split` 调用。已有提交和冻结证据不需要 reset、改写或删除。

源码、原运行、独立检查和发布树位置见 `evidence/qualified-v1/locations.json`。运行结束不等于可删除供体或输入目录；原生 source 使用只读 Git 对象供体，具体依赖在位置清单中保留。旧 R3 未知回执及旧锁继续按原交接保护，本模块的完成不解除它们。
