# P3-0f 探针适配与预算准入

当前决定见 [RESULT.md](RESULT.md)。这是离线检查器包，生产版本仍为 **0f＋firstdot V2＋原 C8**。本包没有 EMU/NEMU 启动入口。

| 入口 | 用途 |
| --- | --- |
| identity.py | 核对固定 0f 的 EMU/NEMU、生成物、构建元数据及冻结 P3 镜像 |
| paths.py | 从已验证 GNU ELF 的宿主模型导出完整动态路径证书，不重建镜像 |
| adapter.py | 退休/CSR/O2/完整 UART/实际首故障/进程回执/3% selector/失败即停及重放门禁 |
| synthetic.py | 生成明确标为合成的完整规模检查器夹具，禁止用其周期作性能结果 |
| test_adapter.py | 针对性损坏、状态机门禁、旧真实 0f 日志复核；只启动隔离的宿主 Python |
| historical_check.py | 在独立 Python 模块空间复核旧 C8 退休/CSR，避免重名模块相互污染 |
| budget.py | 旧实测单调耗时、完整应用计划和日志开销的离线预算审查 |
| INPUT_FREEZE.json / READY_PLAN.json | 输入身份及被预算门禁阻断的未来计划，不是运行授权 |
| evidence/manifest.json | 本轮源码和精简证据清单；失败尝试保留 |

工作目录和既有 ELF/BIN 路径集中在 common.py。依赖固定的 ../p3-qkv-v1 包及原 clean-02 物理产物；本轮未制作可在任意新机器独立运行的分发包。

离线复核入口（原 WSL 环境，均不执行目标程序）：

~~~bash
python3 -B identity.py
python3 -B paths.py
python3 -B budget.py
python3 -B test_adapter.py
~~~

这些脚本会在独立本轮输出目录写入派生文件；归档证据是执行时保存的版本，复核输出不得覆盖归档。完整合成轨迹的生成和审计命令另见 evidence/commands.json；其 155521 笔提交只能证明检查器能处理该规模。现有真实 C8 日志兼容也不等于 P3 已通过差分。

下一轮建议及边界见 [NEXT_STEP.md](NEXT_STEP.md)。必须先获得新的明确授权，不能凭下一轮建议自动试跑。
