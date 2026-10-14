# T06真实功能单元接口验证

2026-10-13（北京时间），`dev`，基准 `5389bde799f5ce1e7939e4eeed5fe9bcdc2325a3` 加本轮工作区。源码/子模块/生成结果按 `source-manifest.json` 与 `check.json` 绑定；不是仅用基准提交号代表新增源码。

使用根 Mill0.12.3 项目及真实 XiangShan FuncUnit/FuConfig/RobPtr/Redirect。Java21.0.12.1、Verilator5.020、firtool1.62.1、g++13.3.0，工具记录和实际命令在本目录；生成 SV 和编译产物仍在忽略的 `team/out/t06-interface-20261013`。

最终实际检查：

- 根/测试 Scala 编译、适配层生成、Verilator lint通过；ScalaTest三项成功、零失败。
- 36个配置/目的接口请求：8合法、28拒绝；检查完整128位数据、异常、vec/v0使能、ROB/物理目的/调试身份以及变化输入下的保持。
- pending和incoming分别18432次真实RobPtr年龄比较，覆盖48项非二次幂ROB、回绕、两种redirect level；每类检查的事件含义见 [T06说明](../../docs/t06-interface.md)。
- 4000周期scoreboard：2079接受＝1959返回＋120取消；1236阻塞计数、1424次同时替换、3次occupied reset。只报告真实握手数量。

初次 `policy-layout-failure.log` 是实际失败记录：合法vta=1被误判，两项失败、一项年龄检查通过；`policy-layout-failure-source.json` 保存当时两个变动源码的摘要。修复是将真实2位SEW显式扩展为架构3位后再拼接；同时将测试的SEW拒绝值限定为实际snapshot能表达的e16/e32/e64，reserved SEW由T10上游vset/vill验证。最终日志不能覆盖或重新标记初次失败。

对应两个 `policy-layout-failure-*.scala.txt` 保留失败版本的完整源文本，已逐一核对与当时运行摘要相同；使用txt扩展名，避免参与当前工程编译。

`failure-gate.json` 记录真实入口在成功后以故障launcher重跑：退出17、旧PASS失效、原成功目录保留。负控用于证明交付门禁，不能计作功能成功。

`prepare-compile.log` 只记录本机首次准备缓存时的根Scala编译；两个改动文件随后规范为LF，最终源码、增量编译和仿真以emit/test及check绑定为准。Windows共享目录的make时钟偏差警告原样保留，最终实际编译/全部测试完成。

独立VdotExec字节仍与前一轮交付摘要相同；前轮12022数学向量不在本轮重跑或重复计数。本轮不验证EXU调度/门控、真实v0/RF读写、VL生产者唤醒/旁路、精确异常PC、CSR完整路径、退休/回滚、完整香山仿真或guest DiffTest；不能据此关闭T04/T06整体/T10/T11或报告性能。

`archive.sha256` 仅覆盖本目录交付的文件。后续修改源码需重新运行入口，不能直接复用这里的PASS。
