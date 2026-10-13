# VDot hardware A/B 工件与状态

2026-10-14；基线 `6bf3c2c3be0c88ff3a020786ff10cbec9aa126d3`。

这是审查与待运行实验包，**不是已通过的硬件优化**。生产源码未应用patch，默认行为保留；真实Chisel/C++编译、FU A/B/负控、综合、STA、全核DiffTest均NOT_RUN。WSL枚举E_ACCESSDENIED、Git引用写入被拒绝；没有绕过。

- [审查报告](../../docs/vdot-hardware-ab-20261014.md)：真实协议、候选收益/风险、计划矩阵、未运行项和晋升条件。
- `experiments/fuse-input-stage.patch`：仅修改VDot构造参数/输入阶段与原真实FU适配器；默认关闭。
- `experiments/*.candidate.scala`：patch后的阅读副本，未编译，不在生产source路径。
- `experiments/fu_ab_test.cpp`：原真实FU checker的局部延伸；双延迟、逐拍trace与drop/identity/cancel-leak负控，未编译/运行。
- `experiments/run_ab.py`：仅允许用户指定的Linux hardware-repo与新hardware-runs目录；jobs1/4G堆；保留命令/版本/资源/原始日志/trace/哈希；不构建CPU。
- `local-checks.json`：本次实际命令、elapsed、exit与明确NOT_RUN。Python syntax/CLI检查仅验证runner本身。
- `logs/`：完整模型/向量/工具日志及工具拒绝转录。工件比较曾因CRLF/LF失败，两次原始失败转录保留，校验方法修正后通过；生产逻辑/黄金期望未改。
- `vectors.tsv`：按原manifest验证后的原算术输入/期望导出，10022组；不是运行trace。
- `source.sha256`：Windows独立clone的本地字节快照。Git clone有CRLF检出；Git/发布内容另按LF归一比较，不能将跨平台byte差异称为逻辑改动。

不修改主worker的T12报告/证据、不Push、不写旧树、不使用后台任务。当前commit=null，不能提供cherry-pick SHA。
