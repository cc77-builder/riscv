# vdot 独立数学模型与测试数据（T05）

本目录实现 [vdot 第一版规格](../../spec/vdot.md) 中的内部原型 `vdot-s8x8-r32-v0.1`：两个源各取低 8 个 signed int8，精确相乘求和，写目的低 32 位补码，高 96 位清零。模型使用 Python 精确整数，不依赖 RTL 的加法树、NEMU 或第三方数值库。

T05 最初在 `zjhwork` 开发（历史）。2026-10-13 本地合并候选已通过模型、组合 RTL 和真实 FU 复验，见 [最新报告](../../merge/2026-10-13-zjhwork-into-zufan.codex-review.md)。**尚未远端发布，成员交接待完成；发布并接收后在共享 `zufan` 独立工作区错峰推进**，暂不合入 `main`。规格中的未确认事项继续有效；模型通过不等于命题方认可原型选择，也不代表 vdot 已在香山/NEMU 上实现。

## 1. 取得代码并检查

以下为候选已发布到团队 zufan 且完成接收后的用法。发布前按最新报告从候选 bundle 检出固定 C，不能假定远端 zufan 已有本目录：

```bash
git clone --branch zufan https://github.com/cc77-builder/riscv.git
cd riscv
bash team/scripts/check-vdot-model.sh
```

此主机模型检查只需要 Python 3.10 或更高版本，不需要初始化硬件子模块、安装 Python 包或构建香山。已有完整仿真环境继续使用原目录；需核对已接收的 `zufan` 完整 SHA 和工作树状态，再执行检查命令。

脚本执行单元测试与数据重生成一致性检查，成功输出 `VDOT_MODEL_CHECK_PASS`，失败返回非零。`--check` 不覆盖已有数据；输出必须保留错误信息，不能通过重新生成来掩盖尚未解释的预期值变化。

## 2. 文件与接口

| 文件 | 用途 |
| --- | --- |
| [model.py](model.py) | 精确数学运算、位布局、候选机器码和纯函数状态适配层 |
| [generate.py](generate.py) | 可复现的数据生成器与只读一致性检查 |
| [tests](tests/) | 手工期望值、独立算法交叉检查、编码/配置/别名和生成器测试 |
| [data/manifest.json](data/manifest.json) | 合同、生成器版本、种子、数据数量及 SHA-256 |
| [data/directed.jsonl](data/directed.jsonl) | 手算用例、单 lane 与高半干扰输入 |
| [data/random.jsonl](data/random.jsonl) | 10,000 组固定种子的算术输入与完整期望结果 |
| [data/smoke.jsonl](data/smoke.jsonl) | 全部定向输入及前 32 组随机输入，供后续全核程序使用 |
| [data/state.jsonl](data/state.jsonl) | 寄存器重叠、策略位、CSR、非法配置及编码拒绝用例 |
| [check-vdot-model.sh](../../scripts/check-vdot-model.sh) | 从任意目录运行的检查入口 |
| [T05 验证记录](../../evidence/model-20261012/README.md) | 35 项测试、数据检查结果、运行日志及适用边界 |

核心 Python API：

```python
from model import VectorConfig, dot_s8, encode, execute, pack_lanes, vdot

assert dot_s8([-128] * 8, [-128] * 8) == 131072
a = pack_lanes([-1] * 8)
b = pack_lanes([1] * 8, high64=0xffffffffffffffff)
assert vdot(a, b) == 0xfffffff8

regs = [0] * 32
regs[9], regs[8] = a, b
regs[10] = (1 << 128) - 1
result = execute(encode(10, 8, 9), regs, VectorConfig(vs=1))
assert result.registers[10] == 0xfffffff8
assert result.config.vs == 3
assert regs[10] == (1 << 128) - 1  # 调用者初态不被修改
```

从本目录执行示例；在其他 Python 程序中调用时，把本目录加入导入路径。`encode(vd, vs2, vs1)` 使用汇编操作数顺序，而 `vdot(vs1, vs2)` 接收寄存器值；字段顺序不可混淆。

数学 API 接收整数列表/元组，拒绝错误长度、bool、float、越界 int8 或越界寄存器值，不会静默截断无效输入。`pack_lanes` 的 high64 是 64 位无符号数；`vdot` 的返回值按完整 128 位目的寄存器解释，负数只在低 32 位编码。

`execute` 不是完整 CPU 仿真器。它接受 32 个向量寄存器值和 `VectorConfig`，返回新的不可变结果，不修改初态。配置中的 `vtype` 是 RV64 原始 64 位 CSR 值：本原型只允许 bits 6/7（vta/vma）变化，其他位须为零；VS 使用 0/1/2/3 表示 Off/Initial/Clean/Dirty，`vcsr` 由 `vxrm/vxsat` 派生。

- `ValueError`：调用数据的类型、长度或数值范围错误。
- `UnsupportedConfiguration`：VLEN 不等于 128，属于模型适用范围拒绝。
- `IllegalInstruction`（cause=2）：在 vdot 入口中遇到不匹配的编码或不支持的架构配置。

最后一项不意味着任意非 vdot 指令在真实处理器中都非法；接入时须先由完整译码器分派。此处没有实现 PC、陷阱入口、特权 CSR 更新、内存、提交计数、时钟或 flush，不能用 Python 异常证明硬件精确异常已实现。

## 3. 数据格式与重生成

JSONL 每行是一个独立用例，UTF-8、LF 换行。算术文件中的字段为：

| 字段 | 含义 |
| --- | --- |
| `id` | 稳定用例编号，用于日志定位 |
| `vs1`、`vs2` | `0x` 加 32 位十六进制字符，表示完整 128 位源值 |
| `expected_sum` | 精确数学结果，有符号十进制整数 |
| `expected_vd` | `0x` 加 32 位十六进制字符，表示完整目的值，包含高 96 位零 |

十六进制文本按通常的高位在左打印；lane 0 始终是最低字节。转换成目标小端内存字节时使用 `int(hex_value, 16).to_bytes(16, 'little')`，不要直接把从左往右的十六进制对当作 lane 顺序。

state 文件在用例中另外记录机器字、初态的稀疏寄存器映射（`registers`，键为 `v0`～`v31`）、配置及期望结果。未列出的寄存器初值为零；重叠寄存器只有一份真实初值，禁止在消费数据时依次加载两个不同源值到同一个寄存器，悄悄改变用例。成功时除目的外的寄存器保持初态，VS 变为 3，其余已建模配置不变。

`expected.outcome` 分为四类：`ok` 表示模型成功；`illegal_instruction` 表示匹配 vdot 但不支持其配置；`unsupported_configuration` 表示模型不支持该 VLEN；`decoder_reject` 只表示 vdot 专用解码入口拒绝了不匹配的机器字。后三类的 `unchanged` 仅表示本模型未修改调用者初态。**`decoder_reject` 不预测全 CPU 陷阱**：翻转 opcode 位可能得到合法的 LB 或 ADDIW，不能拿该类数据要求 NEMU/香山报非法指令。

state 数据中部分非法配置是为直接调用模型而构造的状态，例如原始 vtype 保留位或 vl 超过该 vtype 的 VLMAX；它们不一定能通过标准配置指令原样建立。全核消费端须自行构造架构可达状态并记录实际 CSR，再按原型规定测试；不能将 JSON 配置字典视作可直接回放的裸机准备程序。

随机算术输入采用以下确定算法，不依赖 Python `random` 的版本行为：

```text
seed = 0x20261011
i = 0 ... 9999
message = ASCII(f"{seed:08x}:{i}")
digest = SHA256(message)                         # 32 bytes
vs1 = unsigned_little_endian(digest[0:16])
vs2 = unsigned_little_endian(digest[16:32])
```

生成器把实际输入与期望值全部保存。固定种子用于重生成，不能代替数据文件与源码版本。下面的生成命令会更新目标目录的标准数据文件，先理解规格或生成器变化再运行：

```bash
python3 -B team/models/vdot/generate.py
python3 -B team/models/vdot/generate.py --check
```

试验其他种子时写入忽略的 `team/out/`，避免覆盖已评审的数据：

```bash
python3 -B team/models/vdot/generate.py --seed 0x1234 --random-count 100 --output team/out/vdot-example
python3 -B team/models/vdot/generate.py --seed 0x1234 --random-count 100 --output team/out/vdot-example --check
```

manifest 包括模型/生成器源码的 SHA-256，便于识别生成数据对应的代码。源码变更后即使数学结果相同，来源校验也可能需要更新；应在同一提交中检查并解释数据与 manifest 的变化。

## 4. T05 历史验证范围与后续交接

以下表格和 A/B/C 安排描述 T05 首次交付时点。当前组合算术和独立 FU 已通过本机复验；仍待译码/VFEX4、NEMU 和全核验证，角色以真实认领为准。

模型测试包含人工算出的 D00～D10、19 位边界、候选编码字段、高半干扰、别名、v0/v31、CSR 保持和域外拒绝。随机交叉检查使用不同的字节解码路径求和，避免仅把函数调用结果再作为自己的断言期望。生成器测试验证确定性，以及篡改/丢失数据后检查会失败。

`state.jsonl` 的非法状态是原型约定的测试向量，后续硬件程序还需正确构造：例如 vill=1 会与 vl=0 联动；非零 vstart 必须在配置、加载之后最后设置。数据文件不包含已运行的 NEMU/RTL 结果。

| 已在本轮交付 | 留待后续任务 |
| --- | --- |
| 精确数学结果与完整目的格式 | NEMU 自定义指令执行实现 |
| 编码检查、纯函数状态适配与数据 | Chisel 算术单元及向量通路接入 |
| 主机单元测试和重生成检查 | 真实异常、反压、依赖和 flush 验证 |
| 可供共享的 smoke 输入集合 | 裸机 vdot 工作负载、DiffTest、RVV 基线及性能测量 |

A 可用算术 JSONL 驱动单元测试；B 将同一组数据接入 NEMU 验证；C 记录完整 128 位实际结果并与期望比较。消费端应核对 manifest 合同版本与校验和。下一步按原计划先完成 RTL 接口设计和 NEMU/单元实现，最后才进入全核性能比较。
