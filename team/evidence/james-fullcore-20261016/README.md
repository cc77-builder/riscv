# James 当前源码全核复验（2026-10-17）

执行硬件固定 d3706f0b86ecfdfbb24cb34cbcf2c18a0314f7f9，报告见
[全核复验](../../docs/james-fullcore-20261016.md)。源码、工具与镜像摘要随包保存。

- `hardware*`、`source-pack`、`nemu-build`：完整构建来源与依赖审计。
- `workloads`：构建镜像、ELF、生成数据及来源；含未执行的原 stream 镜像。
- `runs`：143次实际启动（141次接受、2次排除），包含原始流、失败回执、重判与派生汇总。
- `reviewer-source`：本轮修复检查器/压力序列的源码快照；不冒充硬件重建来源。
- `file-manifest.json`、`bundle-files.json`：容器与每个成员的字节长度/摘要。

软件计划为original190和lean199，两个计划有重叠。T13为126运行、108功能调用、
1404性能窗口，39配对配置；固定seed的三次重放不是独立统计样本。
原负控装载中止与原控制覆盖不足均排除，原stream布局27次未执行。
未代替人工签字、STA/PPA、虚拟化或官方规格验收。

在仓库根目录用Python 3.10+离线复核（仅标准库，直接解析ELF）：

```sh
python3 -B team/evidence/james-fullcore-20261016/verify-current.py \
  --archive team/evidence/james-fullcore-20261016 \
  --repo . --output /tmp/james-fullcore-fresh-recheck
```

输出目录必须尚不存在；命令不启动DUT。完整EMU/NEMU可执行文件仅留本机缓存，
归档保存其摘要、构建配方、来源和实际命令，镜像与原始日志可独立复算。
