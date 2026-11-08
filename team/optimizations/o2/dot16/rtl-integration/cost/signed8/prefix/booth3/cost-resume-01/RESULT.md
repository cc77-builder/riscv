# Booth3 一次成本续接：完整图通过，STA超时后停止

## 结论

**FAILED / STOP，未采用该候选。** 本次以独立合同 `dot16-booth3-one-shot-cost-continuation-v1` 补查同一Booth3候选的未完成成本阶段。feature0的原映射经既有序列化及同库回读后，完整连接图在明确的一一对应单元改名下相等；随后OpenSTA在固定30秒内未完成，只留下启动banner，没有形成五类时序报告。feature1首次映射没有启动。

本次 `local_cost_recorded=false`、`cost_results=[]`；不补授parent、整核、应用或物理PPA资格。旧[local-01](../failed-local-01/RESULT.md)和[balanced-Gold02](../balanced-local-02/RESULT.md)保持原FAILED及原始证据。后者的新算术和两feature FU阶段已完成，但这与整体候选资格不同。本次不修改RTL、Gold、FU、工具版本或约束，现有prefix及稳定默认不切换。

**本轮到此停止Booth3成本适配，不加时、不更换第二格式、不做进一步映射或参数扫描。** 不能将缺失的成本结果解释为Booth3时序改善，也不能由超时推断电路功能错误。

## 实际运行和回收

| 项目 | 实际记录 |
|---|---|
| ChatPC operation | `0250d6044ba18f5fd71831ae3131d2ce.34f43c7fb29a8bce9cf04a25956c818e` |
| 主机起止 | 2026-11-08T06:55:55.2315827Z–06:56:28.5902577Z |
| 主机耗时/状态 | 33.319秒，exit1，cleanup_complete=true；无外层timeout/cancel |
| 控制器起止 | 06:55:56.024593Z–06:56:28.359967Z |
| 控制器总预算 | 从预检起300秒；实际32.479272秒，未超过总预算 |
| CPU/内存 | CPU2单核、nice5；启动时MemAvailable 15,196,212 KiB，无其他重任务 |
| 子命令 | serialize-0 rc0；reparse-0 rc0；sta-0触发30秒时限后TERM，rc−15 |
| 回收 | 根组37118及子组37119/37120/37121均不存在；全部子进程reaped/group_absent |
| 新mapping次数 | feature0=0，feature1=0；f0成本不完整，f1分支未进入 |

原控制器记录见[实际结果](evidence/result.json)及[主机最终回执](run-journal-01/run-host-final.json)。原STA日志只有351字节的OpenSTA 2.0.17 banner；没有完成标记、路径报告或可用slack。本记录不把“日志没有语法报错”解释为OpenSTA解析、时序分析或约束检查通过。

## 通过的范围：映射网表序列化保持连接

固定f0原件 `mapped.json` SHA256为 `a0625a8f7d9f79d69e6118cfa84ec787c02e4dbb3c951c2bd2eb5a340d057a5d`。复用原 `splitnets`（无`-ports`）与 `write_verilog -noattr -norename`，无新优化、ABC或手改网表；随后按相同Liberty回读并执行hierarchy/check。

[完整图审计](evidence/feature0/serialized/graph-audit.json)记录：

| 范围 | 数量或摘要 |
|---|---:|
| cells / ports | 6236 / 220 |
| nets / terminals | 9840 / 25655 |
| 明确改名 | 6236个原美元开头cell名各增加一个字面反斜杠 |
| 完整双射 | 无碰撞，完整覆盖回读cell集合 |
| 原图与逆改名后图SHA256 | `7da4f77fab87cbab3f057b7b8462515ee5a2990d0530c80906081fdb2eee6a6f` |
| 新序列化Verilog SHA256 | `adaa99efa26eb453a73e9ea299d1f00660ccc9c1a4f2ae012cdad11233a6f3a4` |

未改的 `circuit()` 保留全部端口几何、cell类型/参数、逐位终端连接和0/1/x/z常量，并拒绝memory/process/init。先比较原图与split图，再逆向改回cell字典键比较回读图；不是仅比较单元数量。本项仅证明该已映射网表的序列化保持电路，不声称RTL-to-mapped等价或时序闭合。

STA完整TCL只替换网表/输出目录，反向恢复原文本；相同Nangate45典型库、1ns时钟、uncertainty、I/O边界、输出负载和线负载模型保持。由于STA未完成，本次没有可发布的面积/五类时序成本点，不与prefix数值拼接或推算频率。

## 冻结身份与归档

- 控制器：[cost_resume.py](source/cost_resume.py)，21,597 B，SHA256 `317f1919138e0c2e69c9d48514667fe82a871a0ec4caf8d6cc5fb206390f594a`。
- 运行前[控制器审查](source/REVIEW-controller.md)及[图/约束审查](source/REVIEW-graph.md)完成；末端保存期间pending信号的检查缺口已在本次冻结版本修复。审查不代替实际运行。
- 新输入8文件共79,644 B；WSL SOURCE_STAGING SHA256 `9d874b240e85db056d0aed0bcd6162beca73b11909a60ac4b7cae9e34044a6bf`。
- 最终结果2,782 B，SHA256 `0bf4fc5a537394179bd347518c2adfe6d9631e3fda34b0ef2b0635a673a1b8d2`；850原输入pin、8冻结输入和21产物pin核验未变。
- [raw.zip](raw.zip)：871,985 B，SHA256 `437a83c57165a701c356017eea8cd45046a6c778d349b44374ee4ae294a5f27b`。本次input-cost-01/cost-resume-01共32 payload、18,021,977 B，另含一个归档清单，共33 ZIP members，0遗漏，全部成员SHA与CRC核验。
- [summary.zip](summary.zip)：50,565 B，SHA256 `b7dec2caf68cdf0aae1d7c1bfab21973557e24b42ccd183d58dabdccd9de3d91`；[audit.json](audit.json)为运输核验，不是工程PASS。
- 归档operation `0250d6044ba18f5fd71831ae3131d2ce.f6ced38669417e2d6fff0f09b7f53cd1`，06:57:23.6914002Z–06:57:24.7857128Z，exit0/cleanup=true，无新EDA或guest运行。

本归档完整保存本次新输入和输出；继承的原网表、阶段证据和工具身份仍引用已冻结父档案，不是独立环境安装包。`artifact-pins.json`包含部分失败产物，不能当作成功标记。Windows权威入口为 `runs/dot16-prefix-booth3-20261108-main/cost-resume-01`，WSL同名目录下原结果、日志和网表继续保留。已核对实际进程和保护范围后释放运行保护；协调回执见[coordination-close.json](run-journal-01/coordination-close.json)。
