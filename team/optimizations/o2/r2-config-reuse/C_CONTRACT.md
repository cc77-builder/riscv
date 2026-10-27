# Config-reuse 普通 C 与独立静态库合同 v1

合同为 `r2-s3-config-reuse-c-application-v1`。本合同验证重复配置删除候选的普通 C 调用路径和可用库，性能选择依据[当前运行合同](RUNTIME_CONTRACT.md)的完整配对矩阵。普通 C 功能程序本身不提供新的性能样本。原 R5、firstdot 库与官方程序保持原字节。

## 接口与候选身份

公开源为 `public/gemv.S` 和 `public/gemv.h`，独立命名空间为 `config_reuse_gemv_*`：

```c
void config_reuse_gemv_8x32_reuse_vdot(const int8_t *packed_ax,
                                    void *output_slots);
```

四种形状是 4×8、8×32、16×64、4×13，每种包含 basic/reuse × vdot/RVV，共16个函数。普通 RV64 lp64d 双指针 ABI、前8字节参数搬运和末尾返回保持。输入是行优先有符号 INT8 矩阵 A 紧接向量 x；每行输出占16字节，低4字节为有符号 INT32 点积，高12字节为零。输入/输出需各自16字节对齐、完整且互不重叠；环境需 VLEN128、VS启用，以及调用 vdot 时相应自定义硬件。向量寄存器、向量配置和调用者保存寄存器允许被覆盖。其余容量和状态边界继承[原调用合同](../r2-select/ENTRY_CONTRACT.md)。

`c_api.py` 私有加载冻结的 `entry_c_api.py`，保留其 C main、Makefile、48个用例、标量参考、完整128位/输入不变性/边界检查、五种软件自检负控、CSR和O2检查。生成器明确调用本轮 `runtime_candidate.generate(..., "config-reuse", ...)`，只将公共符号改名，不改变已测 leaf 机器码。

外层合同、manifest变体、源码快照、当前矩阵锚、公开符号和 `config-reuse-qualification.json` 共同标识本候选。冻结解析器中的 `R4C_*`、`r4-c-api-s1` 和 `R4_C_*` 保留原样，不能用这些内部标签或一个摘要JSON转移旧资格。

## 验收顺序与拒绝条件

1. 本轮 firstdot/config-reuse 完整矩阵的原文审计通过后才构建普通 C 候选。8×32 两图探针不足以提供16函数资格。
2. 普通 C 独立对象的16个公共 leaf，必须逐字节等于当前 config-reuse 矩阵中全部12个形状/数据集单元对应函数，共48次比较。原 firstdot 矩阵合同、漏单元、重复单元和不同字节均拒绝。
3. 实际 GNU/AM 构建需保持官方依赖只读，封存真实命令、退出码、工具链、源码快照、ELF/BIN与独立对象。复用冻结门禁检查实际函数指针表、实际输入、ABI、机器码解码/数学模型和精确再生。
4. 同一固定T17身份上串行执行新普通C程序的bit100负控、同BIN正常恢复、正常功能重放，共3个新EMU。负控PC必须位于本次C ELF实际公共函数内，vd0、指令字 `0x0388000b`、bit100及唯一mismatch满足合同；不复制性能探针PC。
5. 两个正常进程各覆盖48个不同用例，合计96次正常调用。完整128位、标量参考、canary、CSR、实际架构提交和O2事务全部重算；点积数量从本轮manifest/模型推导。物理硬件profile在前后均须等于固定T17身份，不只检查前后相同。
6. `c_evidence.py` 原文审计同时重新核验本轮完整矩阵和普通C记录；公开源需等于真实构建源。精确输入闭包、负控恢复顺序、运行个数和所有原文摘要一致性保持。离线审计不再启动EMU，外部物理输入只报告已封存的哈希边界。

所有输出必须使用新目录；不覆盖失败，不隐式续跑。完整矩阵与C运行结果不因符号改名自动成立，`qualification()`只形成摘要，不能替代源码、构建、原文和跨阶段字节验证。

## 可选静态库与使用范围

`library.py` 用已通过本轮C运行的完整 `gemv-reference.o` 生成 `libconfig_reuse_gemv.a`，验证唯一 `gemv.o` 成员的完整字节相同。真实 C consumer 引用全部16函数，经 GNU 可重定位链接后验证精确函数表重定位和每个leaf字节；拒绝R4或firstdot旧命名空间混入。库构建同时审计本轮矩阵和C归档，记录各manifest、工具链和对象身份。

库包装保持已验证对象字节，新增EMU为0；其 `bytes` 动作只复查现有包装对象和consumer自洽性，不能提供新运行资格。新caller、布局、工具链或完整应用仍按变化影响验证。本合同不修改稳定默认，不授予完整应用、完整赛题、人工验收或新ASIC PPA资格。

## 命令入口

```bash
python3 -B "$REPO/team/optimizations/o2/r2-config-reuse/c_api.py" \
  --repo "$REPO" --identity "$IDENTITY" --matrix "$MATRIX_ARCHIVE" \
  --action build --output "$OUT/c-build"

taskset -c 0-3 python3 -B "$REPO/team/optimizations/o2/r2-config-reuse/c_api.py" \
  --repo "$REPO" --identity "$IDENTITY" --matrix "$MATRIX_ARCHIVE" \
  --action run --build "$OUT/c-build" --output "$OUT/c-run" \
  --operation-id unique-operation-id

python3 -B "$REPO/team/optimizations/o2/r2-config-reuse/c_api.py" \
  --repo "$REPO" --identity "$IDENTITY" --matrix "$MATRIX_ARCHIVE" \
  --action export --build "$OUT/c-build" --run "$OUT/c-run" \
  --output "$OUT/qualified-public-source"

python3 -B "$REPO/team/optimizations/o2/r2-config-reuse/library.py" \
  --repo "$REPO" --identity "$IDENTITY" --matrix "$MATRIX_ARCHIVE" \
  --c-archive "$C_ARCHIVE" --build "$OUT/c-build" --run "$OUT/c-run" \
  --action build --output "$OUT/qualified-library"
```

生成的函数同时保留vdot与RVV，不按名称统一选择vdot；四形状采用决定以本轮完整矩阵实测为准。使用及回退说明在实际资格通过后与交付对象一同发布。
