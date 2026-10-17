# 试水项目统一基准接入审计

## 固定来源与实际准备结果

- 公开仓库：https://github.com/vienna-0FFH/cie2026-shishui-vdot
- 实际 Git commit：`4421d88beb39f8e95e23e25c78eaaaf1a7de4b52`（本地 clone 后 `git rev-parse HEAD` 核实）。
- 硬件目录：`variants/shishui`；香山统一上游：`16ae9ddcda54fc9a2fddffad73174cf793ac7814`。
- YunSuan：`cadd3c2f43096e253d61296b33ac697be8354e29`；其他 13 个已初始化 Git 子模块及嵌套子模块与固定平台一致，详见 `shishui.json`。
- NEMU 目录：`variants/shishui/.benchmark/nemu`；统一上游：`a48a11f208ff81ad765591d83271d1b339fb3861`。

公开的 `xiangshan-vdot.patch` 已经包含平衡树；不重复应用 `xiangshan-vdot-balanced-tree.patch`。原完整补丁用 `git apply --exclude=yunsuan` 直接应用，只排除补丁中 `cadd3c2...-dirty` 的伪 gitlink；真正的 YunSuan 修改以 `yunsuan-vdot.patch` 独立应用。三个语义补丁均通过 `git apply --check`，无需算术、译码或调度移植。之后应用根代理提供的 `common-observers.patch`，只加入统一 T13 CSR/ROB 计数观察点。

## 统一程序接入方式

编码基值 `0xfa000057`，掩码 `0xfe00707f`。寄存器字段仍用标准 RVV 布局：

```python
word = 0xfa000057 | (vs2 << 20) | (vs1 << 15) | (vd << 7)
```

`vd=3, vs1=1, vs2=2` 得到 `0xfa2081d7`。合法公共配置采用 `SEW=8, LMUL=1, VL=8, vstart=0, vm=1`。原实现的固定八元素运算不由 VL 限定。读两源低 64 位中的八个有符号字节，求和后写低 32 位，高 96 位全部清零。NEMU 在写入之前读完源，支持 `vd==vs1/vs2`。

全核实现沿用 `VimacCfg` 的 `piped=true`、`CertainLatency(2)` 与 128 位向量回写路径。八个乘法和三级平衡加法树位于延迟后 `outData` 的组合路径。公开独立模块中的四级流水 RTL **不是本次全核执行路径**。统一周期结果可比较相同处理器配置下的执行效率；没有综合或时序收敛证据，不应将周期差异转换为频率/PPA结论。

## 已完成验证

1. 公开 Python 数学模型通过本项目原有 22 组定向和 10,000 组随机输入，比较完整 128 位结果；数据未更改。见 `shishui-model-conformance.py/json`。
2. 独立 NEMU 参考库编译成功，最终命令 `NEMU_HOME=<nemu路径> make -j1`；见 `shishui-nemu-build.json/log`。
3. NEMU 参考库 SHA256：`6117e9f5ec76685efabc4e6d3223a1b685f871e965ba86911608b42badcc2268`。
4. 统一 reference 测试通过：`runs/shishui-reference-01`，`generic_vdot_pairs=10154`、`known=10022`、`batch=10022`，包含寄存器别名与 full128 比较。状态是 `PASS_REFERENCE_ONLY`，尚不是全核性能结果。

配置沿用 T12 的 `.config`，仅去掉该公开实现没有的 `CUSTOM_VDOT` 与 `CUSTOM_VDOT_XS_TVAL` 两行，保留 MDT/NMIE 等启动设置相同。完整配置归档为 `shishui-nemu.config`。NEMU 依赖资源使用本机已固定的独立共享对象克隆，SHA 记录在 JSON。

## 尚待根代理完成

统一 `MinimalConfig NUM_CORES=1 EMU_THREADS=1 JVM_XMX=12G` 的 EMU 构建、真实 RTL/NEMU DiffTest、统一计时窗口与公平 RVV 对照。当前审计不宣称 RTL 已通过或给出硬件加速比。所有硬件源码已就绪；未推送 GitHub，也未改原 T15 仓库。

## 环境尝试记录

系统没有 pytest，且 `python3 -m venv` 缺少 ensurepip，故未运行原公开 pytest 集；没有为此改系统安装。改用标准库加载原模型并执行上述 10,022 组完整结果比对。初次 `make olddefconfig` 失败后使用 NEMU 自带 `tools/kconfig/build/conf --syncconfig Kconfig`。初次构建误传 `__NOT_DEFINED=1`，激活了上游脚本里的 compile_git 宏，但 Git 路径越界和无身份导致该宏失败，未产生提交或暂存；改用不带变量的正常 `make -j1` 后编译通过。首次和最终日志分别保留，最终 `.so` 哈希一致。
