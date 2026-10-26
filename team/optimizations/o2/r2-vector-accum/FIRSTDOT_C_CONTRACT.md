# Firstdot 普通 C 调用与独立库合同

合同 `r2-s1-firstdot-c-application-v1`。性能资格沿用 [firstdot 配对合同](FIRSTDOT_CONTRACT.md) 的完整矩阵；本合同仅证明普通 C 使用路径与库字节身份，不把功能程序的运行时间当成性能样本。

## 修改范围与接口

`firstdot_c_api.py` 通过私有模块复用原 `r2-select/entry_c_api.py`。原 C `main.c`、Makefile 模板、48用例、标量点积参考、完整128位输出检查、输入/输出 canary、五种软件自检负控、CSR 检查和 O2 事务门禁保持原样。新生成器只选择已测 firstdot 函数并将16个公开符号从 `r4_gemv_*` 改为 `firstdot_gemv_*`。原 R5 默认库及 `r4_gemv_*` 符号不变。

公开源位于 `firstdot/public/gemv.S`、`firstdot/public/gemv.h`。每个函数使用普通 RV64 lp64d 双指针 C ABI：

```c
void firstdot_gemv_8x32_reuse_vdot(const int8_t *packed_ax, void *output_slots);
```

四种形状为4×8、8×32、16×64、4×13，各有basic/reuse与vdot/RVV四个函数。`packed_ax`为行优先有符号INT8矩阵A紧接向量x；输出每行占16字节，低4字节为有符号INT32结果，高12字节清零。输入与输出必须互不重叠，提供完整缓冲；调用环境需要VLEN128、启用VS和本项目vdot硬件。向量配置与调用者保存寄存器可被覆盖，不能假设调用前的向量内容/配置保留。具体容量和状态约束继承原 [C调用合同](../r2-select/ENTRY_CONTRACT.md)。

## 验收顺序

1. 先从原文审计出完整24图/33进程的firstdot矩阵资格。新普通C函数的每一段机器码必须等于三个dataset对应的已测公共leaf，共16函数×3=48次比较。符号改名不改变函数机器码。
2. 使用原AM与GNU工具链实际编译新C程序，保留构建命令、原始输出、独立公共对象、ELF/BIN和源码快照。原门禁检查真实函数指针调用表、实际输入、16个leaf的机器码与有限模型。
3. 在完全相同的T17身份上运行三个串行进程：新C程序bit100负控、同BIN正常恢复、正常重放。负控必须发生在新C ELF的真实公开函数范围内，vd0、word `0x0388000b`、bit100；不能照搬性能探针PC。现场和离线都通过同一个私有负控包装要求这些字段。
4. 每个正常进程执行48用例，合计96次，覆盖4形状×4函数×3数据集；完整输出、边界、CSR和全部架构提交/O2事务都要通过。前后现场硬件profile必须等于冻结T17身份，不能只证明前后相同。
5. `firstdot_c_evidence.py` 复用原C证据器主体并锚定本轮完整firstdot矩阵；新公共源必须与真实C构建源逐字节一致。离线审计重算完整矩阵和C日志。大型外部输入仍只以已核实哈希表示。

旧验证器内部的 `R4C_*` UART标签、`r4-c-api-s1`记录名和`R4_C_*`状态名保留，以避免修改冻结解析器。新身份由外层合同、firstdot源码快照、改名符号、`matrix-anchor.json`和`firstdot-qualification.json`共同确定；不得把旧标签解释为旧S1实现被重新执行。

## 独立静态库

若交付预编译`.a`，使用已通过上述C执行的`gemv-reference.o`创建新库，原C构建回执仍保留其三个artifact和两条命令。独立库回执应记录对象/库/header、工具链、命令及矩阵/C资格身份，并验证归档成员的完整对象字节一致。

另编译一个通过新header引用全部16函数的真实C consumer，以新`.a`完成GNU链接，验证所有公开函数解析到已合格对象的原始leaf。打包与链接不改变已运行机器码，因此不要求为此额外启动EMU。库调用语义和适用范围由本合同限定，不构成任意应用、不同工具链或不同硬件的全面验收。

## 复现入口

```bash
python3 -B "$REPO/team/optimizations/o2/r2-vector-accum/firstdot_c_api.py" \
  --repo "$REPO" --identity "$IDENTITY" --matrix "$MATRIX_ARCHIVE" \
  --action build --output "$OUT/c-build"

taskset -c 0-3 python3 -B "$REPO/team/optimizations/o2/r2-vector-accum/firstdot_c_api.py" \
  --repo "$REPO" --identity "$IDENTITY" --matrix "$MATRIX_ARCHIVE" \
  --action run --build "$OUT/c-build" --output "$OUT/c-run" \
  --operation-id unique-operation-id

python3 -B "$REPO/team/optimizations/o2/r2-vector-accum/firstdot_c_api.py" \
  --repo "$REPO" --identity "$IDENTITY" --matrix "$MATRIX_ARCHIVE" \
  --action export --build "$OUT/c-build" --run "$OUT/c-run" \
  --output "$OUT/qualified-public-source"

python3 -B "$REPO/team/optimizations/o2/r2-vector-accum/firstdot_library.py" \
  --repo "$REPO" --identity "$IDENTITY" --matrix "$MATRIX_ARCHIVE" \
  --c-archive "$C_ARCHIVE" --build "$OUT/c-build" --run "$OUT/c-run" \
  --action build --output "$OUT/qualified-library"
```

所有输出使用新的原生绝对目录，不覆盖已有尝试。本合同不自动修改稳定默认选择；性能选择必须引用完整矩阵中更快的合格RVV和S1，而不是按函数名称或静态指令数决定。

库的`bytes`动作只复查现有包装对象、库成员和已链接consumer，不重新执行matrix/C原文审计。完整来源资格在库`build`阶段验证并写入独立`library.json`；不能把之后的字节检查当成新功能或性能实跑。
