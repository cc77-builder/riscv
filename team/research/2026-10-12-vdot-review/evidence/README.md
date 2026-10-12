# 本次实验的证据边界与复现

这不是团队原有硬件/NEMU 验收记录的副本。这里保存的是本次评审在**会话 Linux 容器**中对 B6/B7 新候选执行的 host 与汇编检查；没有调用本机 Codex，没有在用户 Windows 上运行硬件仿真。

## 实际执行

`candidate-check.json` 对应最终脚本一次成功运行：Python 3.13.5，Clang 17.0.0，固定 seed `0x20261012`。内部时间字段采用 UTC，对应北京时间 2026-10-12 晚间。完整 corpus、程序和代码段摘要在 JSON 中。

```bash
python3 experiments/check_candidates.py --assemble --output evidence/candidate-check.json
```

在目录外运行时按实际路径补全参数。`--assemble` 要求 PATH 中有支持 `--target=riscv64 -march=rv64gcv -mabi=lp64d` 的 Clang；只做 host 检查可以不加此参数，但汇编状态会标为 NOT_RUN。

脚本在临时目录生成全部编号组合的 .S/.o，结束后清理；仓库没有提交这些大量可再生对象。它读取 ELF64 little-endian 的 `.text`，检查每种候选的总指令长度并保存摘要。显式要求汇编但找不到 Clang 会失败，不悄悄降级。新运行先将输出标为 RUNNING，异常标为 FAIL，防止上一次 PASS 被误用。

代表性 B6 另外执行了：

```bash
clang --target=riscv64 -march=rv64gcv -mabi=lp64d \
  -c experiments/baseline6.S -o /tmp/baseline6.o
llvm-objdump -d /tmp/baseline6.o
```

归档反汇编中的路径是当时容器路径，与这里演示的 /tmp 不同，不影响机器码；代码核心区 24 字节，ret 位于其后。

## 如何解释 PASS

全部 32³ 寄存器编号组合中，每一组使用一份一致的 32 个寄存器随机快照，两种候选各检查四策略、两种尾部设置，并测试四组额外边界输入。它不是全部数据位模式穷举；B7 的某些策略/尾部组合在这个模型中效果相同，也不应被描述为同样数量的独立硬件覆盖点。

模型手工实现有效乘积的布局和归约，并用另一种 Python 字节解包表达计算 oracle；CSR 恢复只作为数据与前提推导处理。它不包含真实译码、CSR 权限、vstart/vill 处理、ROB、取消、pipeline 或 cache。汇编器接受语法也不代表目标 CPU 已执行全部组合。

四个 negative_counterexamples 是数值反例，不是向真实被测 RTL 注入错误后的检出日志。BK 长点积候选没有纳入本次已运行探针。

**下一步真实接收条件**：把 B6/B7 接入现有 T09 harness，先运行 NEMU/QEMU 的完整状态与别名检查，再运行香山全核，最后记录真实周期；在此之前只能称“候选已通过 host/汇编检查”。

## 与提交内容的一致性

上传到 GitHub 的四个实验/结果 blob 与容器中已执行文件的 Git blob SHA 完全一致：

```text
experiments/check_candidates.py    d845051671cf5906f77f185fb63c1dba420f2aa7
experiments/baseline6.S            92b119cfc41390550538d5c2f92efd317fb85732
evidence/candidate-check.json      4970c5c730b1e358f148c400c3df4f865aca7609
evidence/baseline6-disassembly.txt 7c761b68fa161026c3b751646b24318abeac7599
```

用 `git hash-object <file>` 可比较 Git blob SHA；JSON 中 `script_sha256` 是文件原始字节的 SHA-256，不要把两种摘要直接比较。若 Windows 检出进行了换行转换，先区分工作区文件与 Git 中的原始 LF 内容；未说明的新换行/脚本修改会改变原始字节摘要。
