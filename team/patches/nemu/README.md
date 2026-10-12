# NEMU vdot 候选扩展交付

合同 `vdot-s8x8-r32-v0.1`，补丁版本 `1.0.0`。采用固定基线加补丁交付，NEMU 基线仍是 [versions.env](../../versions.env) 的 `a48a11f208ff81ad765591d83271d1b339fb3861`；不需要团队成员依赖作者机器上的私有提交。

[vdot 补丁](vdot-s8x8-r32-v0.1.patch) 修改 5 个文件：[manifest.json](manifest.json) 保存基线、补丁 SHA256 和应用后各源文件 SHA256。`.gitattributes` 保留补丁原始字节。实现概要：

- Kconfig 增加默认关闭、依赖 RVV 的 `CUSTOM_VDOT`，保留普通 NEMU 配置的选择权。
- 主译码精确识别 `MATCH=0x0200000b` / `MASK=0xfe00707f`，独立分派到 vdot，复用 R 字段编号解析，不进入普通 OP-V 子表。
- 注册执行入口并包含专用 helper；先核查向量启用、vill/保留位、e8/m1/vl8/vstart0。
- 缓存两个源的低 64 位，以数学整数规则解释 signed int8，求八项精确和；低 32 位补码零扩展到完整 128 位目的，支持全部单寄存器别名及 v0/v31。
- 合法执行沿用 VP Dirty；保持向量 CSR。配置非法走现有 EX_II，不写目的、不置脏、不生成部分结果；相邻编码不匹配本指令。

Linux/WSL 在团队仓库根执行：

```bash
bash team/scripts/prepare-nemu-vdot.sh standalone
bash team/scripts/prepare-nemu-vdot.sh reference
```

默认检出到 `$HOME/riscv-lab/vdot-nemu/{base,standalone,reference}`。两种构建使用独立目录与配置；`TEAM_NEMU_VDOT_ROOT` 可调整根目录，`TEAM_NEMU_BASE_ROOT` 可复用已有固定提交的 Git 对象。脚本只从提交克隆，不复制其他检出的未提交源码；不会丢弃已有源码修改。

脚本先核对补丁及应用后源码摘要，再固定配套依赖，选择 riscv64-xs 或 riscv64-xs-ref 配置并显式启用 CUSTOM_VDOT。共享来源检查核对固定提交的实际跟踪文件字节、manifest 允许的补丁文件、源码目录中包括 Git 忽略文件在内的未知输入，以及编译依赖文件实际消费的头文件；固定依赖执行相同检查。明确生成的配置头允许构建，但实际字节仍进入快照。关键校验不受 PYTHONOPTIMIZE 影响。构建产物附带 schema 2 的 `build/vdot-provenance.json`，绑定基线、补丁、角色、实际源码/头文件快照、配置和二进制摘要；运行入口强制校验这些记录。旧 schema 1 产物须重新构建。重复运行复核实际文件，部分应用或源码漂移会失败。早期检查见 [T08 复核](../../docs/t08-review.md)；当前完整来源门禁、优化模式负控与重新构建见 [审查修复](../../docs/audit-fixes.md)。

构建要求包括原有 C/C++ 编译工具、bison/flex、readline、SDL2、zlib/zstd 开发库和 RISC-V GNU 工具链；本次还准备了 Python protobuf。所有依赖的实际提交由锁定脚本记录。原 NEMU makefile 的 `__NOT_DEFINED` 变量非空时会启用自动 Git 快照宏，团队脚本显式置空，避免继承该开关。

运行时使用 [异常 workload 入口](../../workloads/vdot-exceptions/README.md)，将 NEMU_HOME 与 VDOT_NEMU_BIN 指向 standalone 检出和可执行文件。reference 产物为 `riscv64-nemu-interpreter-so`，供后续香山 DiffTest 加载，不能当解释器直接运行。

本次已在原开发检出和新补丁检出分别通过验收；结果与边界见 [T08 记录](../../docs/t08-nemu.md)。原始 ISA 仍是内部候选草案；该补丁没有增加 RTL，也不代表全核差分已经通过。
