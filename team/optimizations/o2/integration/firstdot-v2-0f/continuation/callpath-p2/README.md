# P2：首条 vdot 接受前的调用路径归因

已完成本次调用路径叶的只读归因，见[结果](RESULT.md)、[结构化结果](RESULT.json)及[下一轮单次修订设计](REVISION_PLAN.md)。P1原HOLD和稳定默认保持；没有实现或运行修订候选。

本轮只读分析 P1 已完成的 steady-d0 原始日志、最终 ELF、冻结源码和观察器；不改生产 RTL、P0/P1 输入、默认入口或旧证据，不新增 EMU/NEMU/综合/STA，不提交或上传 GitHub。

叶级范围：R3/R4 → P2/callpath/0f-P1-steady-d0。主 Agent 负责输入绑定、综合判断、档案/计分板/路线；独立子任务仅写本轮隔离输出的 trace、static、semantics 子目录。Git index 和仓库文档由主 Agent 单独维护。

先核验正常/重放同身份和完整84窗，再将周期窗口、完整退休路径、ROB分配代次、vdot入队/接受/响应与重定向相互绑定。退休时间不是执行/取指时间；缺少直接信号时不得把相关性升级为缓存/分支预测表的确定因果。仅支持旧观测范围的结论，不补造逐指令成本。

结果必须回答：差值在哪一段、对应哪条实际指令/事件、哪些机制可排除、哪些仍未知、是否值得一次对称且有界的 P1 修订。旧1%锚点/3%收益门槛及HOLD保持；不把修订设计当新结果。

## 本机离线复算

原始P1输入在 /home/riscv/riscv-lab/software-import-20261026/p1-split-input-20261028-01；对应源码/镜像/日志锁与归档在P1包。以下只读取旧输入，输出目录必须是新目录。

~~~bash
python3 -B tools/trace.py --p1-root "$P1_OUTPUT" --archive-manifest "$P1_ARCHIVE/manifest.json" --output "$FRESH_TRACE_OUT"
python3 -B tools/static.py --out "$FRESH_STATIC_OUT"
mkdir "$FRESH_OBSERVER_OUT"
cp tools/observer.py "$FRESH_OBSERVER_OUT/observer.py"
python3 -B "$FRESH_OBSERVER_OUT/observer.py"
~~~

从本包目录执行；设置变量为实际原始输入/归档及独立输出。static/observer脚本绑定本机冻结来源绝对路径，路径迁移尚未验证；不要修改旧锁去宣称任意位置可复现。observer在脚本自身目录生成结果，须如上先复制到新输出目录，禁止在已封存工具目录直接运行。tools/archive.py只用于归档/逐文件解压回读，不启动目标。

证据中的root-recheck-*记录主Agent已实际独立执行三个分析器，逐项结果相等。原01/02分析拒绝和观察器格式检查失败均保留。归档生成之后追加的ledger、计分板、路线与finalization回执不声称属于此前已归档载荷。
