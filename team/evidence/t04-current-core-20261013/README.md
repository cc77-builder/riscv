# T04 当前主机全核基线证据

日期：2026-10-13（北京时间）。dev基准`5389bde799f5ce1e7939e4eeed5fe9bcdc2325a3`及未提交T06接口；源码包摘要`e8bd8d763650fc4fe8b8a389f643032db4f582aa2388915750635250bacc05d6`。本目录保留实际成功、失败、诊断、采样及来源材料；不覆盖旧开发机证据。

结论：当前源码的MinimalConfig hello/vadd全核运行通过，3组/24项、DiffTest开启、GOOD TRAP、退出0；普通vadd执行单元与ROB侧提交路径核对通过。vdot没有启用全核译码/执行资源，不能据此关闭T10/T11或正式团队交付。

| 材料 | 作用 |
| --- | --- |
| [check.json](check.json)、[final-source-check.log](final-source-check.log) | 实际根输入/依赖/AM/参考库角色与源码、编译器/profile、RTL、镜像及运行验收；human_acceptance_complete=false、vdot_full_core=false |
| [source-pack.json](source-pack.json)、[source-binding.json](source-binding.json)、[source-changes.patch](source-changes.patch) | 当前工作区叠加与Linux规范/物理字节；436根输入、126锁定子模块 |
| [dependency-sources.json](dependency-sources.json) | 21,236个子模块文件；另拒绝编译目录中的未知/忽略文件 |
| [compile-profile.json](compile-profile.json)、[build-command.txt](build-command.txt)、[build.log](build.log) | Clang19.1.1、双任务、FAST=O1/SLOW=O0、固定配置；全部旧GCC对象另行移走后构建 |
| [build-compiler-version.txt](build-compiler-version.txt)、[clang-install.log](clang-install.log) | 实际编译器及WSL新增9个软件包；通用run脚本另外打印的compiler-version.txt是宿主GCC版本，不能当作本次仿真器编译器 |
| [lower-fir.log](lower-fir.log)、[fir-input.sha256](fir-input.sha256)、[rtl.sha256](rtl.sha256) | 完整FIR解析/独立转换及编译前后RTL一致性；转换5:54.26、最大RSS约6.58GiB |
| [workload.sha256](workload.sha256)、[am-libraries.sha256](am-libraries.sha256)、[nemu-verification.json](nemu-verification.json) | 实际ELF/bin/共同flash、AM库、候选reference来源/角色/配置摘要 |
| [emulator-output.log](emulator-output.log)、[run-summary.log](run-summary.log)、[run.status](run.status) | 真实输出；16518条/42415周期，宿主235.919秒，退出0 |
| [disassembly.txt](disassembly.txt)、[vadd-commit-events.csv](vadd-commit-events.csv)、[vector-fix-alu-events.csv](vector-fix-alu-events.csv) | 当前机器字、三次执行及ROB提交；PC80000138，vecwen=1、v3 |
| [wave-summary.json](wave-summary.json)、[wave-signals.csv](wave-signals.csv)、[wave-artifacts.sha256](wave-artifacts.sha256) | 本次真实采样位置/位宽和外部大文件摘要；保留128位结果 |
| [negative-gates.log](negative-gates.log)、[negative-cache-profile.log](negative-cache-profile.log) | 真实构建失败移除旧receipt、忽略资源拒绝/恢复、缓存优化profile变化拒绝且原二进制不变 |
| build-attempt-1/2/3/4/5/6材料、kernel与memory记录 | Mill启动参数、OOM/缺少完整退出、受控中断、GCC高内存；保留原过程，不以最终PASS覆盖失败 |
| [validator-first-error.log](validator-first-error.log)、[wave-extract-first-error.log](wave-extract-first-error.log) | 验收工具初次根/子模块归属及波形总线名问题，随后按实际层级与位宽修正 |

本次波形的ROB提交观测使用`rob.difftest_delayer*.i_*`，是DiffTest内部三周期延迟之前的ROB侧输入；默认FST时间戳为`DiffTrapEvent.cycleCnt`、上升沿eval后采样。三组FU输入/输出/ROB提交为19719/19720/19722、25366/25367/25369、32698/32699/32701。历史DPIC侧时间戳不能直接混用；这些间隔不独立定义FU固有延迟。

完整FST（236,538,469字节，摘要55fa40b0…）、原始wave-events.csv、FIR/RTL、仿真器、DSO及ELF/bin仍在当前本机缓存或`team/out/`，不放入Git。`check.json`中的绝对路径及摘要覆盖实际本机产物，可能指向未归档的大文件；`archive.sha256`只覆盖本目录实际交付文件。波形提取源码与构建/采样脚本在本目录，使用当前机器已有Verilator5.020的FST库源，不需要安装GTKWave。

两份派生事件CSV按Git约定归档为LF；本机原始CSV为Python csv默认CRLF。`check.json.evidence_sha256`对应本机运行目录的原始字节，`archive.sha256`对应提交材料的字节，列值和事件不变。实际编译与采样使用的旧脚本字节另存，旧摘要与保存副本已核验；源码包里的其他文档不要求与后续进度更新相同。

临时8GiB交换文件在最后构建包装器退出时停用并删除；永久WSL配置未改。成功路径为绑定FIR恢复→独立转换→Clang全量编译→真实运行。正常FIR-only冷入口还未在第二个干净副本完整复现；真实团队标识、成员/非作者/全队复现及视频待完成。

完整边界及复现入口见 [本机记录](../../docs/t04-current-core.md)。本目录没有性能优化、加速比或vdot全核通过结论。
