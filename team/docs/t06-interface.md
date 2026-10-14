# T06：香山功能单元适配层

2026-10-13（北京时间），`dev` 分支，基准 `5389bde799f5ce1e7939e4eeed5fe9bcdc2325a3`。

本轮把已经验证的独立 `VdotExec` 包装为真实香山 `FuncUnit`，落实 T06 的执行接口部分。选择独立 `FuType.vdot` 与 `VdotCfg`，避免占用 YunSuan 既有操作编码或改变普通乘加/Mgu 语义。合同仍为 `vdot-s8x8-r32-v0.1`，未替成员签字或冻结 ISA。

新类型保留原35类的 one-hot 数值，但总类型宽度从35增至36，不能复用旧全核生成物或仿真器；现有指令的全核回归仍需重新构建。wrapper 测试也没有实例化 EXU 时钟门控，T10须核验固定延迟预留/always-ready假设及 redirect 时钟使能；有真实反压时不能沿用只按固定延迟保持的门控策略。

## 已实现的边界

| 接口 | 当前实现与理由 |
| --- | --- |
| 运算 | [VdotFu.scala](../../src/main/scala/xiangshan/backend/fu/wrapper/VdotFu.scala) 实例化原独立模块；完整128位结果直接输出，不经过 Mgu，不读取旧目的参与运算 |
| 类型/配置 | 新类型追加在枚举末尾，原 one-hot 数值保持；纳入 vecOPI/vecAll、needVecCtrl、配置索引；尚未启用译码或 EXU |
| 源槽 | 沿用五槽：两个128位源、保留的旧目的、128位 v0、8位物理 VL；`maskWakeUp` 保留以支持 vm=1 时的普通 v0 源 |
| 配置 | 实际 VL 只来自槽4，合法性使用本次输入的 vpu.vill/vsew/vlmul/vstart/vm；vta/vma 均接受，不把 vpu.vl 当实际物理 VL |
| 身份 | 请求握手时同步保存 robIdx、pdest、vpu 和 PerfDebugInfo；注册结果与 metadata tag 一致性断言；反压时不采样较新输入 |
| 写回 | vecWen/v0Wen 来自已保存的目的选择，与合法写使能相与；断言不得同时写两类 RF；无整数/浮点/VL/vxsat/fflags 输出 |
| 异常 | 非法配置或未知内部操作产生有身份的 illegalInstr 完成，完整数据为零，两个写使能为零；不通过丢弃 out.valid 隐藏异常 |
| 取消 | pendingTag 的实际 RobPtr 使用现有 needFlush 比较，区分较老/较年轻、回绕与 flushItself；同周期已被取消的输入禁止握手；被取消 pending 槽清空时保守暂停新接受一周期 |
| 时序 | 单注册响应槽；无阻塞时一拍输出、每拍可替换；`CertainLatency(1)`，无额外延迟。该声明不代表全核端口竞争或目标频率已验收 |

`FuncUnit` 没有原始指令字、逻辑 vd/vs 编号和 VS 输入。wrapper 将已经译出的内部操作转换为独立模块的规范请求编码，目的由 pdest/写使能携带；**精确 mask/match、v0 实际读源、VS Off 拒绝仍是上游义务**。当前 wrapper 在非Off域使用代表值 VS=Initial，它不承担真实 VS 状态读取或更新。架构 VS Dirty 仍由成功退休负责。

vtype 控制只有 vill、策略、SEW、LMUL；保留位与64位原始 vstart 的 WARL/非法处理须在 CSR/译码链路验证，不能用 adapter 已接收的窄字段证明这些链路。

当前 VPU snapshot 的 SEW 只有2位，而架构 vtype 的 SEW 字段为3位。wrapper 显式扩展为3位后再拼接64位配置，并断言总宽度；保留 SEW 的第三位由上游 vset/vill 合法性处理。初次真实测试在合法 `vta=1` 下失败，暴露了缺少补零导致的策略位错位；本轮保留实际失败日志，并通过四种策略及 e16/e32/e64 拒绝检查复验修复。

当前 [Unprivileged.scala](../../src/main/scala/xiangshan/backend/fu/NewCSR/Unprivileged.scala) 的 Vstart 实际保存低7位（0～127），而 vpu.vstart/适配层输入为8位。接口测试中的255用于窄接口拒绝压力，不证明 CSR 可构造255；全核测试必须使用已读回确认的实际状态，不能直接把写入的64位值当作硬件保存值。

## 构建与测试入口

初始化当前锁定的子模块后，在 WSL/Linux 项目根执行：

```bash
git submodule update --init --recursive --jobs 2
export VDOT_MILL=/path/to/mill-0.12.3
export TEAM_EVIDENCE_DIR="$PWD/team/out/t06-interface"
bash team/scripts/vdot-fu-tests.sh
```

Windows Git 以 CRLF 检出根源码、WSL Git 全局设置不同的共享目录，可额外设置 `VDOT_GIT_AUTOCRLF=true`。它只调整本次 Git 状态比较的换行解释，不修改工作文件或用户配置；编译来源仍按文件实际字节计算摘要。入口按子模块提交与真实源文件摘要记录依赖，避免对子模块反复做慢速 dirty 扫描。

入口使用根 `build.sc` 编译真实香山和子模块，通过 `EmitVdotFu` 生成适配层，先做 Verilator lint，再仅运行 `VdotFuSpec`。这与 T07 的独立 sbt 工程不同，不使用 mock RobPtr/Redirect/FuConfig。

测试观察内容：

- 合法四种策略与两类目的，非法 VL/vill/SEW/LMUL/vstart/vm/操作均检查完整结果、exceptionVec、目的写使能及身份；故意使 shadow vpu.vl 与真实 VL 不同。
- 48-entry 非二次幂 ROB 的96种 flag/value，对每种 redirect 指针和两类 level 分别检查 pending 与 incoming；每类18432个接口比较。距离48的比较边界按既有比较器约定检查，不声称该边界的两条指令可同时存活于全核。
- 4000周期 scoreboard 按真实握手追踪接受、返回、取消，涵盖输入/输出反压、同时替换、选择取消及 occupied reset；不把这些周期计作新增数学随机用例。

入口在开始时移除旧 PASS，绑定当前根/测试与依赖 Scala 源码、子模块和生成 RTL 摘要。最终结论来自完整 ScalaTest 成功和实际计数；生成 SV、编译缓存与模拟器留在忽略目录。

本轮实际结果见 [证据](../evidence/t06-interface-20261013/README.md)：36请求（8合法/28拒绝）、pending/incoming各18432检查、4000周期中2079接受＝1959返回＋120取消，另有1236阻塞计数、1424同时替换及3次occupied reset。三项测试成功，root Scala/lint与源码集合/摘要复核通过；属于执行接口部分，T06整体仍待团队确认及全核映射。

## 本机准备与资源范围

当前项目已初始化原锁定的全部递归子模块，没有升级 SHA；Mill0.12.3 下载至本机 WSL 的 `/home/amesotten/.cache/codex-rvinno/t06/tools/`，没有更改全局 PATH、WSL 配额或 Java 安装。使用已有 Ubuntu Java21.0.12.1 和 Verilator5.020；这些不同于原主机阶段一记录，不能复用其全核工具验收结论。

本机 WSL 检查约11GiB内存、3GiB swap；本轮限制并行数和 JVM 内存，执行 Scala 编译/适配层验证。没有启动完整香山 C++ 仿真器构建，不将资源检查或 Scala 编译当作 T04 全核运行。

## T10 接入前必须落实

1. 当前主机构建/复现未修改指令路径的 hello/vadd 全核调试基线，补齐 T04；原开发机历史记录不能替代本机记录。
2. 新增精确 `0xfe00707f / 0x0200000b` 译码；只匹配本编码，邻近 custom-0 保持原处理。只生成一条 uop，即使输入 LMUL 非法也不拆成多个目的写回。
3. 接入独立 FU 的调度资源并验证同批次 VL 重命名旁路、配置快照/恢复与 v0 数据选择；保留旧目的源槽时记录额外依赖成本。
4. 候选位置为 VFEX1 的一拍向量路径；落成前检查其固定延迟写回预留，证明与其它 FU 不会同时输出。不能直接把可反压的局部协议当作全核仲裁已安全。
5. 核对 WbDataPath 的无数据完成路径向 ROB 报告异常，成功退休才置 VS Dirty；全核 cause/PC、全宽状态导出、年轻 squash 仍按 V/W/E/C 矩阵验收。

T06 的执行适配层可以先验证，但人工接口确认、精确译码/资源映射、当前全核基线和 T10/T11 验收仍开放。下一步是完成这些入口条件，再接通现有 workload 与真实 NEMU DiffTest；本轮不开展性能优化。
