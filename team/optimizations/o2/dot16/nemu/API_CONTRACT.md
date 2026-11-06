# dot16 实际 NEMU 构建与 API 验证合同

合同：`dot16-nemu-reference-api-v1`。本阶段是独立团队 ISA 候选的真实构建／接口验证，不授予新 RTL、整核 DiffTest、平台 xTVAL 或应用性能资格。

## 目标与固定输入

在固定 NEMU `a48a11f208ff81ad765591d83271d1b339fb3861` 上，依次应用旧团队 dot8 1.1.0 补丁（SHA-256 `6c165bf5f94ef0bfb4f894a5f06eb6d620d4a7e0e12f3b1400fa72811f5d24db`）和本叶 dot16 候选补丁（`d803d7bd6c6c89ae759e76477b63e50e680dc6ce56e9e3898259f4e428b91966`）。每个阶段按已有 manifest 核对全部接入文件，旧 dot8 helper 两份逐字保持。

源来自现有只读基线的独立 Git 对象克隆；五个外部依赖沿用 `team/scripts/lock-nemu-extra-deps.sh` 中的固定提交。新工作目录与输出位于常驻开发区的独立 `runs/dot16-nemu-reference-20261106-0105/`。不修改旧 base/reference/standalone、旧共享库、官方判定程序、旧测试或任何冻结实验；不改变 XiangShan superproject 分支、Git index 或他人工作树。

官方原题第 3.1.1 项明确要求参赛者扩展 NEMU 指令；原题仍是八项 dot8。此候选保留其编码和语义，dot16 使用独立新编码，并不声称已替代官方要求或获赛事采纳。

## 两个独立构建身份

固定源码相同，只切换 `CUSTOM_VDOT16`；以原 `riscv64-xs-ref_defconfig` 生成配置，保留既有 RVV、dot8、旧 dot8 xTVAL、TVAL_EX_II、NMIE_INIT，MDT_INIT 关闭。两个构建均关闭 LIGHTQS 和 `CUSTOM_VDOT16_XS_TVAL`。后者的候选硬件策略尚未资格化，不因 ISS 自测通过而开启。

feature0 与 feature1 按上游默认 source/build 路径顺序构建；每次完成且子进程退出后，将本候选刚生成的完整 build 目录保存在独立 feature 输出中，再冻结配置、生成头、共享库与日志。下一配置从空的默认 build 目录开始，不复用前一配置对象；不向递归 make 传播全局 BUILD_DIR 覆盖。配置切换前封存上一身份，运行时两库分别在独立进程加载。只以实际配置、实际导出符号、库哈希与执行回执授予对应结论。

复用已有 `artifact_guard.audit_repo` 的逐文件检查，不改旧工具的 manifest 或判定。新入口为新候选绑定独立 manifest，记录固定依赖和实际编译输入。源/配置不符即停止，不将旧库身份用于新模型。

## 真实 API 与 ABI

复用 `team/tests/nemu_reference_traps.cpp` 的加载、生成 `diffstate.h` 布局和单步检查骨架。固定生成头来自已存在 T17 构建，SHA-256 `6a2ce3ab51893908f74452522ab03c553cf7fa7e8aa25f74ea84d79aa45f044d`；其来源和新 NEMU 配置分别核验，`difftest_init_v2(sizeof(ReferenceState))` 与导出的 `DIFFTEST_REG_SIZE` 同时检查。

函数签名以固定 NEMU 实际导出代码为准：LIGHTQS 关闭时 `difftest_regcpy(void *, bool)` 为**两参**。不照搬旧 C++ 调用者的三参声明，也不把状态尺寸检查当作函数 ABI 检查。

每个不同机器字使用独立固定 PC，避免已解码 tcache 被原地改写污染；恢复干净初始寄存器状态后再单步。所有源注入完成后才计算独立 int64 oracle，覆盖目的／源重叠。测试状态可通过 API 注入；保留位、vill、超出正常 VLMAX 的 VL 等测试不声称是程序级 CSR 可达状态。

## 必要验证

- 两配置：实际加载、ABI、NMIE=1、MDT=0、VLEN=128；单步 ebreak 的精确 cause/PC；标准标量和 RVV 冒烟。
- feature0：其他状态合法时，新 dot16 编码真实进入非法指令陷阱，全部向量寄存器不发生部分写入。
- feature1：全零、全部 −128、最大正值、负极值、混合符号、固定随机值、逐通道单点与高八项扰动；全部寄存器编号及别名、四种 vta/vma。结果低32位补码、高96位清零，其他向量/GPR/FPR保持，VS 变 Dirty，运算相关 CSR 保持。
- 非法状态：VS-Off、vill、SEW/LMUL错误、vstart非零、VL边界、保留位及少量复合非法；只对仍属于 custom-0 的 vm/funct3/funct6 固定位邻居断言拒绝，不把可能成为其他合法 opcode 或 RVC 的邻居强判非法。
- 两配置：旧 dot8 合法／非法、完整128位、别名及高八项忽略回归，保留旧平台行为。

非法请求的无部分写入针对 vreg、GPR/FPR、运算相关 CSR 和 VS。正常 trap 对 pc/mepc/mcause/mtval/mstatus 的修改单独判断，不要求整个 CPU 状态不变。dot16 新平台开关关闭时，非法请求的 mtval 是完整指令字；旧 dot8 的仅 VL 非法情况仍按旧 profile 为零。两者分开判定。

## 资源、失败与验收

总体预算最多四核；本阶段获协调后单 CPU，make -j1，不与他人占用同一配额。构建输出、API 正常/负控输出独立；长作业在十五分钟检查点查看真实进度。超时或环境失败仅记录为构建/运行未完成，不自动判硬件功能失败。所有未知操作先查原回执，不重放。

API 检查器先用真实旧库执行 feature0 场景以验证旧路径和新编码拒绝，再对新 feature0/feature1 库分别执行。另以只改变预期结果或指定错误 feature 身份的检查器负控证明判定能拒绝错误，不修改任何参考模型的比较行为。测试源码、实际库和配置身份均入证。

完成标准：两身份构建、导出/链接检查、相应真实 API 矩阵、必要负控与原始回执可追溯。尚未完成的项明确标为 NOT_TESTED/BLOCKED，不借历史 PASS 补齐。通过后的结论只属于此 ISS 状态注入与 M-mode API 范围。
