# T15 独立参数模型与数据

本目录服务于 [T15 合同](../../spec/t15-parameters.md)，不改变原 vdot 指令或旧 T05 模型。新增配置为 8 对 int16、128 位源、低 64 位结果补码、高 64 位零；基本配置为原 8 对 int8/低 32 位结果。

oracle.py 用 Python 精确整数和按字节有符号解码，独立于 RTL 归约树。参数校验由数学正负极值推导结果所需位宽。测试还用逐位移位/符号修正求和交叉检查全部数据，并有手工极值、字节顺序、高半参与和窄位宽错误反例。

```bash
python3 -B -m unittest discover -s team/models/vdot-param/tests -v
python3 -B team/models/vdot-param/generate.py --check
```

新数据建立原因：原 int8 数据不能验证 int16 的 35 位结果、高半源 lane 以及跨字节元素。s8x8.jsonl/tsv 从原 22+10000 数据只读转换，并逐条比较旧 golden；s16x8 为 94 定向+10000 随机，种子命名空间 20261017-t15-s16x8-v1。随机源由 SHA256(seed:index) 直接生成两个 128 位整数，不依赖随机库版本。原 team/models/vdot/data 的所有文件保持不变。

manifest 固定新模型/生成器源码、数据摘要和两份原始数据摘要。数据不按硬件结果改写；generate.py 默认只允许创建不存在的输出目录，--check 不写文件。

模型仅验证算术、位布局和参数约束，没有实现新机器编码、CSR、非法指令异常或 NEMU 执行。

2026-10-17 可移植性修复：原始生成器使用操作系统相关的路径字符串，导致 Windows 重生成 manifest 的 original 路径键不同；现统一为 POSIX 分隔符。四份数值向量/TSV 字节不变，Linux manifest 只更新生成器来源 SHA。保留 unit-01/Windows 初次失败记录，正式验收以修复后的 unit-02 为准。
