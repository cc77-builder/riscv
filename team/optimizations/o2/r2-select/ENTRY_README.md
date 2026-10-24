# R4：可调用 GEMV 候选入口

本入口把既有 S0/S1 GEMV body 导出为普通 RV64 C ABI 叶函数，并对真实调用成本重新测量。性能路径合同见 [ENTRY_CONTRACT.md](ENTRY_CONTRACT.md)，普通C应用功能补充见 [C_API_CONTRACT.md](C_API_CONTRACT.md)，实测采用结果、证据和遗留资格见 [ENTRY_RESULT.md](ENTRY_RESULT.md)。原 [R2-SELECT](README.md) 的原镜像查询/导出仍保持原来的语义。

本交付包含公共汇编及头文件的确定性生成器、实际 C 调用程序、整核运行器和离线证据审计器。此段记录 R4 冻结批次，当时未切换默认入口；当前推荐的稳定 C 源别名、默认库构建、T17 新身份运行及回退见 [STABLE.md](STABLE.md)。下文继续保留原 R4 实验合同与命令，公共函数不包含运行时 dispatcher。

## 1. 调用接口

```c
#include <stdint.h>
#include "gemv.h"

/* A 按行存放，x 紧接 A；两个存储区域不重叠。 */
int8_t packed_ax[8 * 32 + 32] __attribute__((aligned(16)));
unsigned char output_slots[8][16] __attribute__((aligned(16)));

void run_8x32(void) {
  /* 先填写 packed_ax，再在 VS 已启用的 VLEN128 环境调用。 */
  r4_gemv_8x32_reuse_vdot(packed_ax, output_slots);
}
```

输出每行一个16字节槽，低32位为INT8点积的有符号结果，高96位清零。尺寸由符号固定，支持4×8、8×32、16×64、4×13；每种形状提供basic/reuse与vdot/RVV。调用者负责足够的有效存储和互不重叠的输入输出；性能和功能证据使用16字节对齐的存储。

使用标准整数调用约定：a0为紧密A||x指针，a1为输出槽指针，无标量返回值。函数不改变栈及被调用者保存的整数寄存器；向量配置和调用者保存寄存器被改变。返回时VL=8、vtype=0（e8/m1/tu/mu）、vstart=0、vcsr=7。不得把该接口当作任意尺寸、任意别名或保留向量CSR的通用BLAS。

已交付的 [public/gemv.S](public/gemv.S) 和 [public/gemv.h](public/gemv.h) 可直接加入构建；它们必须与实际C验证镜像的生成源码逐字节一致，C档案审计会重新检查这一点。以下命令可在新目录确定性再生成全部16个S1公共函数：

```bash
REPO=$(git rev-parse --show-toplevel)
MOD="$REPO/team/optimizations/o2/r2-select"
OUT=/absolute/path/to/new-r4-output
mkdir -p "$OUT"

python3 -B "$MOD/entry_c_api.py" --repo "$REPO" \
  --action generate --output "$OUT/public-s1"
```

将生成的 `gemv.S` 和 `gemv.h` 加入自己的构建；该目录还包含本合同的普通C功能程序及其数据。链接后仍需按实际应用影响验证，不能转借本合同的周期。

## 2. 固定硬件上的真实再构建与运行

以下命令针对本次固定合并O2/H1硬件身份；不会重建或替换硬件。需要Linux/WSL、完整Git历史、GNU RISC-V工具链、固定AM源码及预构建库、EMU构建回执、正常NEMU及flash。运行参数示例见 [runtime.entry.example.json](runtime.entry.example.json)，其中所有绝对路径须替换为实际存在的输入；来源和哈希由运行器核验。此入口不适用于把其他EMU伪装成既定硬件身份。

先在新的输出目录构建最小8×32/dataset0探针并检查实际产物：

```bash
CFG=/absolute/path/to/runtime.entry.json

python3 -B "$MOD/entry_experiment.py" --repo "$REPO" --config "$CFG" \
  --action build --output "$OUT/build-probe" \
  --shards 3 --datasets 0 --jobs 2

R4_ENTRY_BUILD="$OUT/build-probe" python3 -B -m unittest discover \
  -s "$MOD" -p test_entry.py -v

python3 -B "$MOD/entry_experiment.py" --repo "$REPO" --config "$CFG" \
  --action run --output "$OUT/run-probe" --build "$OUT/build-probe" \
  --operation-id YOUR_REGISTERED_OPERATION --negative --replay
```

以上为5个真实EMU进程：负控、同BIN恢复、另一变体正常运行及两个变体重放。先确认完整正确性、拒错/恢复和重放，再判断新入口的S1 reuse vdot是否胜过同条件下最快合格RVV。探针不胜出时保留证据并停止扩大。

对已经合格的本版本进行完整再现，可在一个新批次建立24个镜像：

```bash
python3 -B "$MOD/entry_experiment.py" --repo "$REPO" --config "$CFG" \
  --action build --output "$OUT/build-matrix" \
  --shards 1 3 5 7 --datasets 0 1 2 --jobs 4

python3 -B "$MOD/entry_experiment.py" --repo "$REPO" --config "$CFG" \
  --action run --output "$OUT/run-matrix" --build "$OUT/build-matrix" \
  --operation-id YOUR_REGISTERED_OPERATION --negative --replay
```

完整批次为24个正常正式镜像、8个dataset0重放、1个负控，共33个EMU；384个正式窗口，每个候选格12样本。first/warmup不进入正式统计。EMU顺序执行，构建至多4个独立单核任务，仍受团队四核总预算和实时协作约束。每个输出必须是新路径，运行器不隐式恢复或覆盖已有批次。

普通C程序单独构建与运行：

```bash
python3 -B "$MOD/entry_c_api.py" --repo "$REPO" --config "$CFG" \
  --action build --output "$OUT/build-c-api"

R4_C_API_BUILD="$OUT/build-c-api" python3 -B -m unittest discover \
  -s "$MOD" -p test_entry_c_api.py -v

python3 -B "$MOD/entry_c_api.py" --repo "$REPO" --config "$CFG" \
  --action run --build "$OUT/build-c-api" --output "$OUT/run-c-api" \
  --operation-id YOUR_REGISTERED_OPERATION
```

C程序采用普通AM默认链接流程。三个进程依次完成真实负控、48case正常恢复和48case功能重放；C独立标量判定、全部128位输出、输入与边界保护、CSR及每个正常进程1008条vdot提交均受检查。它不产生性能窗口。

运行中以 `active_pid`、`active_result` 及逐次 `result.json` 判断真实执行阶段；本版C控制器在最终收束前的顶层 `status` 保留 `PREFLIGHT`，不能据此认定EMU尚未启动。新进程数与实际PID会持续更新，最终状态另作明确判定。

## 3. 封存与无需启动EMU的复核

已交付档案位置为本目录下 `evidence/entry-v1` 与 `evidence/c-api-v1`。两份完整档案和对应源码必须共同保留；C档案以性能档案manifest哈希锚定共享硬件来源。

另保留最小探针档案 `evidence/entry-probe-v1`，用于快速重跑下面的语义拒绝测试。它是完整矩阵中probe部分的原始封存副本，不增加性能样本或EMU执行数。

```bash
python3 -B "$MOD/entry_evidence.py" --repo "$REPO" \
  --action audit --archive "$MOD/evidence/entry-v1" \
  --output "$OUT/matrix-offline-audit.json"

python3 -B "$MOD/entry_c_evidence.py" --repo "$REPO" \
  --action audit --archive "$MOD/evidence/c-api-v1" \
  --matrix "$MOD/evidence/entry-v1" \
  --output "$OUT/c-api-offline-audit.json"
```

离线审计从档案重新生成源码、检查实际ELF/独立对象、逐项复算完整输出/CSR/退休窗口/O2轨迹、负控恢复、重放和统计。它没有新的EMU或NEMU执行，不重新证明档案之外的硬件、参考库、AM与工具链当前仍存在；这些外部大输入以原实跑哈希与来源回执保存。

要封存自己刚完成的批次，须先结束所有进程并保持物理输入不变：

```bash
python3 -B "$MOD/entry_evidence.py" --repo "$REPO" --action pack \
  --scope matrix --run "$OUT/run-matrix" --archive "$OUT/archive-matrix"

python3 -B "$MOD/entry_c_evidence.py" --repo "$REPO" --action pack \
  --build "$OUT/build-c-api" --run "$OUT/run-c-api" \
  --matrix "$OUT/archive-matrix" --archive "$OUT/archive-c-api"
```

本次性能批次由最小probe与后续extension组成，封存时提供两个 `--run`，审计器要求其合计恰为完整矩阵且没有重复样本。extension单独的PARTIAL状态会原样保存。`pack`只封存并核验字节及实物输入，最终资格以`audit`从原始记录复算为准。

探针归档的语义拒绝测试：

```bash
python3 -B "$MOD/entry_evidence.py" --repo "$REPO" --action pack \
  --scope probe --run "$OUT/run-probe" --archive "$OUT/archive-probe"

R4_ENTRY_ARCHIVE="$OUT/archive-probe" python3 -B -m unittest discover \
  -s "$MOD" -p test_entry_evidence.py -v
```

测试在临时副本中重新封存篡改后的记录，验证缺少审计器、冒称完整矩阵、重放顺序颠倒、硬件事实改写和操作身份丢失均被语义层拒绝。不能只凭文件哈希自洽宣布实验资格。

直接复核随交付提供的最小探针，无需启动EMU：

```bash
R4_ENTRY_ARCHIVE="$MOD/evidence/entry-probe-v1" python3 -B -m unittest discover \
  -s "$MOD" -p test_entry_evidence.py -v
```

## 4. 回退和后续资格

不使用新接口时继续使用原R2-SELECT导出的完整原镜像。要生成新调用合同下的8×32 S0回退：

```bash
python3 -B "$MOD/entry_candidate.py" --repo "$REPO" \
  --variant s0 --shard 3 --dataset 0 --output "$OUT/public-s0-8x32"
```

shard的1、3、5、7分别对应4×8、8×32、16×64、4×13。S0与S1导出相同符号名，因此应选择其中一个版本链接，不能在同一程序中重复定义。所有较快RVV对照及S0回退都保留在完整矩阵中。

固定硬件的整体MERGE-REG相容资格、另一执行者的T17完整复现、R5/G5默认切换分别按现行路线处理。本软件入口通过不自动完成上述项目，也不产生新的ASIC面积、STA、功耗或完整应用性能结论。
