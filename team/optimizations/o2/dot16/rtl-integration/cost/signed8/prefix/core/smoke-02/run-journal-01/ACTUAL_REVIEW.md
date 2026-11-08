# prefix core02：ABI 与六例 smoke 实际结果复核

**结论：原始证据支持 `PREFIX_FULLCORE_SIX_CASE_SMOKE_PASS`，未发现影响这一个固定六例合法镜像结论的冲突。** 这不是完整整核资格、G3、非法指令/trap 矩阵、应用性能或 PPA 结论。

本次只读云端原始归档、源码快照与已有固定 gate 源码；没有访问 PC/Pro，没有执行 gate 函数、ABI 探针、EMU、EDA 或重新运行测试，没有修改执行源或实际结果。

## 1. 归档、执行身份与回收

- `raw.zip`：288,894 B，SHA-256 `d1f11eec2208bdf829d28830ad28c3eb23c09b9405ed8f286a195c784b3f90fe`。独立读取验证 CRC、唯一 member、逐文件长度/SHA 及落盘字节，均一致。原始 payload 为 **28 文件 / 6,259,039 B**；另含 4,603 B manifest，所以 zip 共 29 成员、解压总字节 6,263,642。没有数量口径冲突。
- `actual/core-smoke-02/result.json`：6,553 B，SHA-256 `2ec969938a8c4f790e10ba7067befe22f890946b58f2a533276d3051c0cc6eda`。
- `runtime-inputs.json` SHA 为 `9df6be73b603e5b47f6f4bfc6bc9d84af75899f310bb8fbbdec71c8730fab4a2`，与结果一致。三个 raw log SHA 也都与结果和归档一致；`run.log` 逐字节等于 **emulator.stderr 后接 emulator.log**，符合冻结入口构造方式，未漏掉 stderr。

运行记录绑定的是新 `core-build-02/cwd/build/emu`：71,489,976 B / SHA `6387d998c3f715a9ced1f44c4410f0f29f76780a96ec15c1830c8828ded6f887`，对应 core result SHA `06b38d232feda7ea93e3b34d806888163a5abf89de916e63af185d383773a5e2`。EMU 命令 argv、runtime inputs 和结果指向同一新产物，未指向旧 resident EMU。冻结入口的 `build_record` 在执行前要求该 core 真实完成、七阶段退出 0 并回收、EMU 大小/SHA 与生成清单一致。本审查复核该身份链，没有另行读取未包含在本归档内的 71 MB EMU 本体。

五条实际命令依次为输入检查、ABI 编译、ABI 运行、EMU、输入检查；均退出 0，`reaped` 和 `group_absent` 均为 true，时间先后与预算一致。两次输入检查原始输出均为 `INPUTS_UNCHANGED`，stderr 为空。状态起止为 **2026-11-08 03:20:25.020517–03:21:22.353701 UTC**，共 57.333184 秒；EMU 命令区间 45.261665 秒。记录 CPU1、nice5，未发生重跑。

## 2. 原门禁与实际 ABI

实际 source-02 wrapper SHA 为 `cdd3dcd9e58ea0f16587884cc63226655c489f8536a0c4ca4a8f0bd2a758970b`。仅将 builder/lock 两项 SHA 逆替换后，可逐字节还原已审 source-01 的 `5044a433…`。归档 staging 源、运行快照和 runtime input SHA 相互一致。

`legacy-smoke.py` 是 18,293 B / SHA `363725f7a54ed367c7302108bc73f70266c68674a25a72587aaa04bc80e9e755` 的原样文件；`abi_probe.cpp` 保持 `709fd1d0…`。通用 runtime gate 固定为 `172551fb537e93f33937819b1a7625e39986726c039266750adadb73e8ccc05c`；本次读取匹配该 SHA 的 `source-review/packed-ws-20261107/target-inputs/runtime_gate.py`，没有拿其他版本代替。

ABI 编译命令首先包含新 `core-build-02/cwd/build/generated-src`，使用固定 Clang 和 `NUM_CORES=1`。运行输入记录中新生成的 diffstate.h 与固定 reference diffstate.h 均为 SHA `6a2ce3ab…`；八类架构块记录存在。原始 `abi-run.log`、`abi-layout.json` 和 result 内布局三者完全相等，符合旧 `EXPECTED_ABI`：

| 布局字段 | 值（字节） |
| --- | ---: |
| 总复制长度 | 1,400 |
| regs_int / regs_fp | 0 / 256 |
| csr / pc / hcsr | 512 / 656 / 664 |
| regs_vec / vcsr | 800 / 1,312 |
| fcsr / triggercsr | 1,368 / 1,376 |

probe 编译和运行均实际成功，stderr 为空；没有用预先填好的 EXPECTED_ABI 代替探针原始输出。

## 3. 原始日志对应同一六例

EMU argv 使用原固定 BIN `6f800620…`、flash `a3360212…`、128 MB RAM、seed 1、300,000 cycle 上限和固定 feature1 NEMU。runtime inputs 中 reference SO SHA 为 `cc768488944941d59442727a96e0a19206e24872dcefed0052cf6cb3694a3fae`。原始日志只声明一次正确 reference 路径，并确实包含 `The first instruction of core 0 has commited. Difftest enabled.`。

`run.log` 中的所有 smoke marker 恰好是一次 BEGIN、下列六例和一次最终 PASS，顺序、VL、低 32 位与原 legacy 常量逐项相符，没有重复或额外 case：

| case | VL | 实际 low（hex） | 高 96 位 | 结果 |
| --- | ---: | --- | --- | --- |
| 0 | 8 | `00000000` | zero | PASS |
| 1 | 16 | `00020000` | zero | PASS |
| 2 | 16 | `00040000` | zero | PASS |
| 3 | 16 | `fffc0800` | zero | PASS |
| 4 | 16 | `0000fe28` | zero | PASS |
| 5 | 8 | `fffe0400` | zero | PASS |

开头为 `DOT16_CORE_SMOKE_BEGIN schema=1 cases=6 vlenb=16`；唯一最终行为 `DOT16_CORE_SMOKE_PASS cases=6 dot8=2 dot16=4 failures=0`。之后出现一次 `HIT GOOD TRAP at pc = 0x80000442`。实际 guest cycle 57,336，低于此次保护上限；该值只用于确认运行完成，没有当作应用性能证据。

对照精确原 gate 源码只读检索完整原始日志，未见 assertion failed、BAD TRAP、DIFFTEST FAIL、ABORT、different at pc、cycle/instruction limit、signal stop、unknown trap、segfault/terminate 等通用失败文本，也未见额外 smoke 的 CRITICAL ERROR、double trap、PMA check failed、`DOT16_CORE_SMOKE_FAIL`。ANSI 控制去除后的文字没有残留或不支持的控制字符。未调用原门禁来重跑或改写状态。

## 4. 可交付的限定结论

可记录为：**新 prefix core02 EMU 的实际 ABI 对齐，并在固定 feature1 reference 下通过同一六例合法整核差分 smoke（dot8×2、dot16×4），所有进程回收、记录输入保持不变。**

结果只将 `fullcore_smoke_qualified=true`；`fullcore_qualified`、`application_performance_qualified`、`ppa_qualified` 均为 false，范围说明也明确排除 G3/illegal/performance 转授。这个边界与原始证据相符，无需为此次六例结果增加其他验收阻塞。

审查开始：2026-11-08 03:26:02 UTC；原始证据核对完成：03:28:59 UTC。仅新增本报告。
