# T05 独立模型与数据

合同：`vdot-s8x8-r32-v0.1`。模型版本 `1.0.0`，生成器版本 `1.1.0`。Python 3.10+，仅使用标准库；可在 Windows 或 Linux 执行。

[vdot_model.py](vdot_model.py) 将数学 oracle、编码识别和候选指令状态模型分开。数学整数求八项 signed int8 点积，输出完整 128 位值；合法指令只替换一个目的并置 VS Dirty，非法配置返回 cause=2/fault_pc 且保持输入状态。它不实现特权陷阱入口、内存、调度、物理寄存器或 NEMU ABI。非匹配机器字报告 `NotVdot`，不能凭此认定整台处理器的非法指令。

运行模型、日志判定和编码/数据检查：

```text
python -m unittest discover -s team/tests -p "test_*.py" -v
python team/tests/generate_vdot_cases.py --output team/out/t05 --random-count 10000 --seed 0x20261011
```

Linux/WSL 另可执行 `bash team/scripts/vdot-tests.sh host`，增加 C 判定器的 18 项检查。测试方法表示分组验证，不等于硬件用例数量。

产物由 [generate_vdot_cases.py](generate_vdot_cases.py) 统一生成：

| 文件 | 内容与用途 |
| --- | --- |
| [data/vdot-directed.jsonl](data/vdot-directed.jsonl) | 已纳入仓库的 48 个定向用例；测试会核对其是否与生成器一致 |
| `team/out/t05/cases.jsonl` | 48 个定向 + 默认 10,000 个随机用例，保存实际源、旧目的、寄存器编号、编码及完整期望 |
| `manifest.json` | 合同、版本、种子、算法、数量、生成器/模型源码 SHA256，以及所有生成文件的 SHA256 |
| `cases.h` | 48 个定向 + 前 32 个随机用例的裸机输入及期望，并包含 35 个异常子例 |
| `exceptions.json` | X01～X10 的 35 个异常子例；合法 D00/D03 等承担 X00 正反数对照 |
| `word-sites.S` / `stubs.h` | 根据使用的机器字生成固定 32 位 fault/resume 标签和分派，避免自修改代码及未知汇编助记符 |

定向集合覆盖 D00～D10、8 个单 lane、不参与的高半部分、别名/v0/v31、四种策略与两种旧目的预填、vxrm/vxsat。别名时旧目的值就是对应的源初值，不能同时要求同一个寄存器既保存源又预填另一份哨兵。两个源编号相同时，数据文件中两份源也相同。

随机算法为 `xorshift32-v1-low-byte`：非零 uint32 状态依次执行左移 13 XOR、右移 17 XOR、左移 5 XOR，各次左移按 uint32 截断，最后取低字节。每例依次取 16 字节源 A、16 字节源 B、16 字节旧目的；字节按小端装入寄存器。寄存器十六进制字段按高字节在前显示；机器字另存小端字节。已固定具体输入与算法，不依赖 Python 自带随机序列的版本行为。

数据重生成应逐字相同。生成器源码改变时 manifest 的源码摘要会改变，即使数学输入相同；更新版本和受影响的定向 fixture 后再比较。`team/out/` 为临时产物，正式实现运行记录放入 evidence，不把数学模型通过当作 RTL/NEMU 通过。

生成器 `--smoke-random-count` 默认 32，可增加裸机随机规模。运行脚本的 `VDOT_DATA`、`VDOT_RANDOM_COUNT` 和 `VDOT_SMOKE_RANDOM_COUNT` 控制数据位置/数量；构建和运行必须使用相同设置。T08 已用独立目录运行 1,000 随机输入，见 [NEMU 验收](../docs/t08-nemu.md)。

相邻编码的额外静态检查：

```text
python team/tests/review_vdot_encodings.py --rocket <固定rocket的Instructions.scala> --custom <固定rocket的CustomInstructions.scala> --nemu <固定NEMU的decode.c> --output team/out/encoding-review/review.json
```

[review_vdot_encodings.py](review_vdot_encodings.py) 解析香山命名的 literal BitPat 表项及 NEMU 32 位主分派；未解析名称、候选冲突均失败。这不执行处理器译码；新增扩展或接入 vdot 后必须重新检查。固定源码与本次检查结果见 [T05/T05-E 评审](../docs/t05-t05e-review.md)。
