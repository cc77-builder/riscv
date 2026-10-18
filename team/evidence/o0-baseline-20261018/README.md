# O0 固定256点积矩阵：II4基线全核执行

54次实际运行、648个窗口全部通过；18个镜像分别执行3次固定seed重放，结果完全一致。唯一计划为216窗口，性能汇总只使用replay 0的144个measured窗口。

执行硬件固定 `d3706f0b86ecfdfbb24cb34cbcf2c18a0314f7f9`，EMU/参考库/flash摘要见 `selection.json`；硬件未重新构建。此前来源审计及13窗口校准的证据绑定保存在 `source-binding.json`。这里是新执行的O0软件矩阵，不是当前整合源码或T14的全核复验。

构建镜像与冻结源数据来自 [上一阶段](../o0-progress-20261017/README.md)。

- `runs.tar.gz`：54次运行的原始stdout/stderr、运行与验收回执、启动前预选清单、检查器源快照及完整campaign结果。
- `summary.json`：独立复算的逐窗口观察、计数及按1/2/4路、same/different、vdot/RVV分组的统计。
- `campaign.json`、`selection.json`：与压缩包内一致的便捷查看副本，不替代原始流验收。
- `pilot-run.tar.gz`：首个真实运行的小型测试夹具，来自上述54次运行之一；用于日志篡改负控，不是额外第55次运行。
- `host-o0.log`、`host-unified.log`、`host-validation.json`：108+10项主机测试，包含完整64个旧镜像生成兼容性、真实ELF和真实日志突变检查，使用 `-OO`。
- `artifacts.json`：载荷字节长度及SHA256；`verify.py`另固定该清单摘要。
- `independent-recheck.json`：Windows 11/Python 3.13.9在全新目录独立解包复算的回执，54次/648窗口通过，重算汇总SHA256与封存文件完全一致。

用本次Git版本的检查器从全新目录独立解包复算，无需原EMU/NEMU路径、编译器或网络：

```sh
python3 -OO -B team/evidence/o0-baseline-20261018/verify.py \
  --output /tmp/o0-baseline-independent-new
```

Windows使用 `python -X utf8 -OO -B`。输出目录必须不存在。验证器先认证两个阶段的归档与编译回执，再逐一重新生成矩阵、检查ELF完整状态数据、完整退休工作量、CSR采样边界、UART负控及FU生命周期，并与封存汇总逐字段比较。检查器源摘要发生变化时拒绝，不能用放宽门禁替代历史复算。

1/2/4路固定算术工作量，却改变循环次数与退休指令数；busy/响应重合不证明O1同拍交接合法。T14对照须来自同一统一源码和工具链的成对构建，O0尚未全部关闭。结果与限制详见 [工作记录](../../docs/o0-progress-20261018.md)。
