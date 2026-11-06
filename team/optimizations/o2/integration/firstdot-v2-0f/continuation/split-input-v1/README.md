# P1：0f 上的 split-input 8×32 最小软件试验

合同沿用 [P0](../split-input-p0/CONTRACT.md)，contract ID 为
`zjhwork-0f-c8-split-fixed-a-8x32-v1`。仅增加本目录；生产 RTL、C8 库和公共默认入口不变。

## 组成

| 文件 | 用途 |
| --- | --- |
| `source/vendor/` | 供体 ffd668 的四份原字节运行源；来源哈希受 P0 锁约束 |
| `source/`、`workload.py` | 三种 profile、三数据集、六算法新旧接口的 C 测试及统一计时窗口 |
| `identity.py` | 当前 0f/clean-02 的实物、工具、依赖、生成物身份核查；不改历史资格字段 |
| `build.py` | 先冻结九份源码，再 GNU 构建并检查完整对象、最终 ELF 与装载内容 |
| `verify.py` | 六对完整叶函数机器码、实际地址/复制范围、ABI、退休路径和 CSR 窗口证书 |
| `runtime.py` | 串行负控→正常→重放，单调时钟/原始流限额，UART与退休计数绑定，P0门槛 |
| `test_*.py` | 正确性与拒错测试；宿主测试不等于目标 ISA 或全核通过 |

稳态 packed 只在每次调用复制 32B x；A 在 stream 开头只准备一次。first 将 A/x 两部分复制计入窗口，native 已有连续输入不增加复制。三个 profile 的结果分别解释。

## 本地使用

先在完整源码根目录设置 `REPO=$PWD`，指定已固定的 `SOFTWARE_IMPORT_ROOT`、`FLASH` 与新的输出目录。不是执行供体旧 runner，也不接受不明二进制。

```bash
P="$REPO/team/optimizations/o2/integration/firstdot-v2-0f/continuation/split-input-v1"
python3 -B -m unittest discover -s "$P" -p 'test_*.py' -v
python3 -B "$P/build.py" --help
python3 -B "$P/runtime.py" --help
```

构建入口为 `build_all(repo, out, software_import_root, flash_file)`；具体命令与 GNU 选项以新输出中的执行回执为准。运行入口：

```bash
python3 -B "$P/runtime.py" \
  --repo "$REPO" --software-import-root "$SOFTWARE_IMPORT_ROOT" \
  --flash "$FLASH" --build "$BUILD_OUT" --out "$FRESH_RUN_OUT"
```

运行前九份镜像必须完成最终 ELF 证书。首先只运行 steady-d0 三进程；正确性、路径、重放、锚点和两个顺序格的至少 3% 收益全部通过后，才会自动扩大其余八镜像。所有重放只查一致性，不增加统计样本；最快 RVV 按同 profile 固定实现的正式总周期选择。

任何超时、原始流限额、身份变化或校验失败都会停止并留档，输出目录不可续用。只有 steady 三数据集决定稳态采用；first/native 用于报告边界，不要求它们满足稳态 3% 采用条件。普通 C ABI 的合法输入责任仍见 P0。

本轮实际结论与未测范围将写入本目录 RESULT.md；没有该结果时不能从源码或构建成功推导全核通过。
