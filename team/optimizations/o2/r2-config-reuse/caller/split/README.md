# 8×32 分离输入接口

可选的 GNU C11 接口：A 与 x 分开存放，直接计算八个完整128位结果槽，
`split_full()` 再提取连续的八个 INT32。它省去旧普通 C 消费者每次288B的
A||x 打包。R5 默认映射和原 packed 接口保持原样。

实际资格、周期及决定见 [RESULT.md](RESULT.md)；验收门槛在首轮构建前固定于
[CONTRACT.md](CONTRACT.md)。不能仅凭少了复制或指令，就推断应用性能。
配对基线是已合格的hoisted普通C打包包装，使用冻结的编译选项；本实验没有
证明它比所有优化过的memcpy/向量化打包都快。若输入本来已经是A||x，应用也
没有逐次打包成本，不能套用本轮省复制的收益。

本轮分别报告完整验收状态、接口采用资格与算法选择。接口资格来自同一种计算
实现的新旧完整调用配对；算法选择还需通过锚点和较快RVV对照的筛选。
接口合格不等于vdot获选；`HOLD_CONTEXT_VARIATION` 表示本计划暂不作算法推荐，
各入口由调用者显式选择。若实际消费者能够缓存或摊销打包，或固定A后只更新x，
应按其实际复制成本重新比较。R5默认映射不变。

## 使用合同

| 对象 | 必须满足的条件 |
|---|---|
| A | 256个有符号INT8，行优先8×32；允许任意字节对齐 |
| x | 32个有符号INT8；允许任意字节对齐，不要求紧邻A |
| slots | 八个连续 `struct caller_slot`，共128B；**首地址16B对齐** |
| y | 八个连续INT32，共32B，满足INT32自然对齐 |
| context | 有效且正常对齐的 `struct split_context`，调用期间字段稳定 |
| 关系 | A、x、slots、y、context互不重叠，存储和生命周期覆盖整个调用 |

每个slot低32位为精确有符号累加，高96位为零。`caller_slot` 类型本身并不
保证16B对齐；必须用 `_Alignas(16)` 或满足条件的workspace。
不要将紧密的 `int32_t y[8]` 直接当作slots传给leaf。

平台资格为 RV64/lp64d、VLEN128、VS已启用；vdot入口还需要本项目匹配的
自定义指令硬件及参考模型。函数自己建立向量状态，返回
`vl=8,vtype=0,vstart=0,vcsr=7`，破坏向量寄存器及配置，不恢复调用前状态。
后续代码需要其他向量配置时应重新建立。函数不分配内存、不检查长度或空指针、
不自动选择算法，也没有标量返回值。头文件当前承诺GNU C11，不声明C++/其他FFI支持。

## 明确选择实现

| 新符号 | 保持的计算实现 |
|---|---|
| `split_gemv_8x32_vdot` | config-reuse / reuse vdot |
| `split_gemv_8x32_rvv0` | S0 / basic RVV |
| `split_gemv_8x32_rvv1` | S0 / reuse RVV |
| `split_gemv_8x32_rvv2` | config-reuse / basic RVV |
| `split_gemv_8x32_rvv3` | firstdot / reuse RVV |
| `split_gemv_8x32_rvv4` | config-reuse / reuse RVV |

编号表示实现身份，不代表速度排名。三参数 `split_leaf` 不能与旧两参数
`caller_leaf` 互换，也不能强制转换后使用。

```c
#include "split.h"

/* 在匹配平台启用VS，并由调用方填写A/x。此处的入口选择仅演示ABI。 */
void example(const int8_t *a, const int8_t *x, int32_t *y) {
    _Alignas(16) struct caller_slot slots[8];
    struct split_context context = {
        .a = a, .x = x, .y = y, .slots = slots,
        .entry = split_gemv_8x32_vdot,
    };
    split_full(&context);
}
```

只需要完整slots时，也可直接调用相应三参数leaf；它的周期不能套用包含
INT32提取的完整调用测量。上述自动存储示例另经GNU编译和可重定位链接检查；
实际整核实验的84次功能调用使用独立全局context/workspace，二者验证范围不同。

## 构建与复算

在仓库根目录，使用Linux/WSL原生文件系统和固定T17运行环境；所有输出选仓库外
的新目录。命令中的绝对路径由运行者填写，不能指向已冻结实验或现存输出。

```bash
python3 -B team/optimizations/o2/r2-config-reuse/caller/split/run.py \
  --repo "$PWD" --action build --output /absolute/new/build

python3 -B team/optimizations/o2/r2-config-reuse/caller/split/run.py \
  --repo "$PWD" --action run --build /absolute/new/build \
  --output /absolute/new/run --operation-id unique-coordinated-operation

python3 -B team/optimizations/o2/r2-config-reuse/caller/split/archive.py \
  --action audit --build /absolute/new/build --run /absolute/new/run \
  --output /absolute/new/audit.json
```

`run`执行三次独立EMU：实际vd0 bit100负控、同BIN正常恢复、同BIN正常重放；
运行前按协作约定认领资源。全程最多4核，性能EMU串行。
完整campaign审计同时检查实参/输入清单/进程回执/时间顺序和原始日志。
单独调用Python的 `normal()` 仅负责内容分析，不能替代完整来源审计。

检查新增框架及验收器的拒错能力（不启动EMU）：

```bash
python3 -B team/optimizations/o2/r2-config-reuse/caller/split/harness_check.py \
  --build /absolute/accepted/build --output /absolute/new/host-check

python3 -B team/optimizations/o2/r2-config-reuse/caller/split/mutations.py \
  --build /absolute/accepted/build --run /absolute/accepted/run \
  --output /absolute/new/mutation-check.json
```

主机检查明确模拟三个ISA语句，只验证实际C初始化/判定逻辑；不调用候选叶函数，
不产生真实CSR或性能资格。拒错检查使用内存中的ELF变体和临时日志副本，原输入不改。

不启动EMU的证据复算：

```bash
python3 -B team/optimizations/o2/r2-config-reuse/caller/split/archive.py \
  --action audit-archive \
  --archive team/optimizations/o2/r2-config-reuse/caller/split/evidence/split-input-v2 \
  --output /absolute/new/archive-audit.json
```

它解包到临时目录，重新生成源、验证ELF与机器字、回放原RETIRE/CSR/O2/UART，
重算所有窗口和门槛。它验证封存证据，不重新证明旧机器外部输入现时仍存在。

从已验证构建生成独立库及完整使用文件：

```bash
python3 -B team/optimizations/o2/r2-config-reuse/caller/split/library.py \
  --qualified-build /absolute/accepted/build --output /absolute/new/library
```

输出包括 `libxs_split_8x32.a`、`split.h`、依赖的 `caller.h`、`split.c`、
`kernels.S`、`example.c` 和命令/身份回执。工具重新GNU编译和归档，检查实际
archive成员，并要求七个公共函数的完整机器字与所选已验证构建ELF相同；示例编译
并链接后不得有未解析符号。库工具本身不授予运行资格；本次交付由RESULT中相同
镜像SHA与完整campaign绑定，库的位置也见RESULT。

C包装使用GNU11.4、`-O2`、RV64GV/lp64d，禁止relax、自动向量化、LTO、IPA特化
及尾调用；准确命令在 `library.json` 和构建记录中。调用方应遵守ABI。
不同编译器/选项/链接布局或新的调用计划不能直接继承已测周期。
不要同时链接独立 `kernels.o` 与已包含它的静态库。

## 回退

新接口内改用RVV，只需将 `split_context.entry` 换为已验证的某个
`split_gemv_8x32_rvvN`，重新编译调用端。A/x/slots/y合同保持一致。

回到旧packed接口，应恢复原 `caller_context`、`caller_workspace` 与
`caller_full()`，或按R5说明使用既有稳定入口，并准备A||x和完整输出槽。
旧leaf是两参数函数，不能只把它塞进新context的函数指针。

本模块只覆盖固定8×32和上述平台。本轮不改变RTL、FU时延/吞吐、ASIC PPA，
不代表完整LLM性能、所有矩阵形状或新机器安装复现。
