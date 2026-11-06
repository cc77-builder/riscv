# P3 最小运行源包

固定供体 ffd668bf1bc80850d382f514d13bb00316c85582，D=288、GS=32、RV64/lp64d、VLEN=128。
boundary.S 与 q288-kernels.S 各编译一次，配套头文件来自同一固定源；不要同时链接旧 fused/phased/tail 筛选对象。

- 主入口 qkv_boundary：一次 FP32 量化，按 Q/K/V 顺序调用明确选择的 q288_tail_vdot 或 q288_fused_rvv4。
- q288.c 为可选的打包及旧完整 Q 入口；本轮融合路径不调用它。q288_full 另需有效 entry 叶指针。
- 数据域、别名、对齐、返回 CSR 和 ABI 以本轮 ../../CONTRACT.json 为准。调用函数不分配、不检查数据域。
- 编译使用 GNU -march=rv64gv -mabi=lp64d -mcmodel=medany -mno-relax -fno-pic -fno-pie -fno-lto；
  C 另用 -O2 -ffreestanding -fno-builtin -fno-tree-vectorize -fno-tree-slp-vectorize -fno-fast-math -ffp-contract=off。
- manifest.json 保留逐文件来源及 SHA256。生成/构建/链接复验入口为上级 build_check.py；整个搬移验证见 audit_extra.py。

本轮仅宿主构建与有限机器字模型。没有执行 EMU/NEMU，没有取得本地目标周期或加速比资格。
