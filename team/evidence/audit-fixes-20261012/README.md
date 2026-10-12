# 综合审查修复实际证据

2026-10-12（北京时间），James_Hotten，源码基准7cd588a8f加本轮工作区。当前源码、输入、配置及镜像由各来源记录的实际摘要识别；Git提交包括本轮源码。新记录独立归档，此前六份归档223项摘要均验证，不改写旧运行结果。

| 原始记录 | 用途 |
| --- | --- |
| [model-tests.txt](model-tests.txt) / [judge-tests.txt](judge-tests.txt) | 23个Python方法及25项生产C判定检查 |
| [qemu-selftest/run.log](qemu-selftest/run.log) | 7项harness自测及3项负控，仅验证harness |
| [qemu-unextended/run.log](qemu-unextended/run.log) | 未扩展合法vdot被拒绝，退出3，非扩展通过 |
| [vdot-nemu/run.log](vdot-nemu/run.log) / [check.json](vdot-nemu/check.json) | 1304合法+37异常，1341/1341，退出0/GOOD TRAP；含实际VS负控 |
| [baseline-qemu/run.log](baseline-qemu/run.log) / [check.json](baseline-qemu/check.json) | 普通RVV1304项及判定负控 |
| [baseline-nemu/run.log](baseline-nemu/run.log) / [check.json](baseline-nemu/check.json) | 同一oracle集合1304项及判定负控 |
| [runtime-coverage.json](runtime-coverage.json) | 直接从原始结果行统计32寄存器、1147三元组、96交叉；preVS直方图478/429/397，18种scratch mask |
| [sequence-check.json](sequence-check.json) | 两份实际反汇编各1147个stub，完整13条、算术3条，无custom-0 |
| [diagnostic.log](diagnostic.log) | 实际C诊断输出，受控v10 byte15错误及pre-source快照 |
| [source-guards/summary.json](source-guards/summary.json) | 外层PYTHONOPTIMIZE=1的六项真实源码/头文件注入拒绝 |
| [vdot-gates/summary.json](vdot-gates/summary.json) / [baseline-gates/summary.json](baseline-gates/summary.json) | 各三项来源拒绝，guest未执行，源码/配置复原且镜像不变 |
| [nemu-standalone/provenance.json](nemu-standalone/provenance.json) / [nemu-reference/provenance.json](nemu-reference/provenance.json) | schema2固定候选NEMU来源、角色、配置、源码/生成输入与二进制 |
| [nemu-reference/load-check.json](nemu-reference/load-check.json) | 共享库加载及四个接口导出，guest_difftest_run=false |
| [vdot-build/workload-provenance.json](vdot-build/workload-provenance.json) / [baseline-build/workload-provenance.json](baseline-build/workload-provenance.json) | 编译镜像绑定实际源码/模型/生成器/AM/数据/模式 |
| [delivery-check.json](delivery-check.json) / [verification-script.py](verification-script.py) | 历史摘要、原48 fixture/补丁不变、ISA2～4节不变及实际覆盖/反汇编诊断核验 |
| [review.md](review.md) | 修复后的Standards/Spec两轴只读结论及验收边界 |

构建/运行原始记录保留当时team.sha（构建时HEAD）和working-tree；未提交源码用source.sha256及provenance绑定。摘要内绝对路径是原执行位置，不能把重新clone位置直接代入旧输入校验。复现时重新生成、构建、捕获来源，再验证新产物。归档不含ELF/bin/对象文件及全量生成输入；它们可按当前源码与固定seed复现。本地实际镜像留在忽略的team/out。

执行入口和规模见 [修复报告](../../docs/audit-fixes.md)；NEMU来源须先通过prepare-nemu-vdot.sh的两个角色构建，再使用各自HOME/binary。vdot build-xs与run-nemu使用同一VDOT_DATA和VDOT_IMAGE，默认expanded/1000随机；baseline两平台使用独立数据目录避免并发覆盖。来源探针使用本仓库check_nemu_source_guards.py、check_workload_gates.py，均在PYTHONOPTIMIZE=1下运行，必须与guest运行分开，避免共享配置临时修改。

verification-script.py是本次主执行者的交付检查原件，路径按team/out布局解析；归档副本仅保留检查过程，需放回team/out并具有本地运行产物后执行。所有关键判断为显式require，不依赖assert。

运行参数记录在各平台runtime-parameters.txt；NEMU vdot最终默认600s，baseline实测显式600s（脚本默认300s）。主机耗时不用于硬件性能。T03冻结、成员复核、非作者复现、RTL/真实DiffTest与T13测量仍未完成。

archive.sha256校验本目录原始字节；源目录.gitattributes防止Git转换归档换行。
