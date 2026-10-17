# T15 独立参数单元证据

本包保存基本 s8x8/r32 与扩展 s16x8/r64 的真实 Chisel RTL、Verilator 全宽读回、逐周期握手、错误注入、参数拒绝及模型检查。原始日志/TSV 超过 1 KiB 时无损 gzip；run/file-manifest.json 校验解压后的原字节，file-manifest.json 校验存储字节。

从仓库根执行（输出文件必须不存在）：

```bash
python3 -B team/scripts/verify-t15.py --run team/evidence/t15-parameters-20261017/run --output /tmp/t15-offline-new.json
```

通过标志 T15_OFFLINE_RECHECK_PASS。只需 Python 3.10+ 标准库；脚本与数据源码必须与 run/source.json 固定摘要相同。大型 Verilator 生成 C++、对象及可执行文件不进入证据包；原二进制摘要和完整构建命令已保存。

这不是新 ISA 或全核 SEW=16 验收，也不是重新执行硬件仿真或物理时序/PPA 验证。旧生产硬件与 NEMU 未被修改。最终报告见 ../../docs/t15-parameter-extension.md。
