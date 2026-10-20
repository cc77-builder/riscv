# 当前任务：O3中断恢复进行中（2026-10-20，本地）

原campaign-01在46项通过后中断；两项只有部分日志、无真实完成退出，不能宣称仍在跑或已完成。
当前由resume.py在campaign-02导入46项字节相同证据，仅补跑剩余10项，另2中断尝试保留。
原始campaign-01、镜像和运行源码不修改。恢复编排99f04b9，原execute源码7a642b6，恢复交付工具8aab2ed。
当前进度查/home/riscv/riscv-lab/o3-gemv-20261019/campaign-02/state.json；
恢复启动回执recovery-launch-state.json；新监督根/home/riscv/riscv-lab/o3-gemv-recovery-delivery-20261020。
finish-recovery.py负责通过后的严格复核、封存、Windows复算和本地交付。不要再启动旧launch.py/finish.py或重跑全部测试。
本轮不push，不自动O4/O5/G5/默认切换，正式T16后置。以下状态为历史记录。

# O3 INT8 GEMV应用评估

2026-10-19开始，本地分支local/o3-gemv-20261019，未推送GitHub。26份镜像已编译及ELF审计，22项主机检查、4项真实O1/O2冒烟通过；正式应用campaign进行中，尚无完整O3性能结论。不要以模型通过代替RTL通过。

[测试合同](CONTRACT.md)规定四尺寸、三数据集、两计时口径、基础/复用两种软件和公平RVV对照。复用G4固定O1/O2，不修改硬件或旧基准。

模型及生成器检查：

    python3 -B -m unittest discover -s team/workloads/o3-gemv -p 'test_*.py' -v

在完整香山检出中编译新镜像，输出目录必须不存在：

    python3 -B team/workloads/o3-gemv/build.py --output /absolute/new/images

所有实际运行和结果随后以新的campaign目录记录；本轮不自动O4/O5/G5，不改变默认模式，正式T16报告后置。

当前运行状态：/home/riscv/riscv-lab/o3-gemv-20261019/campaign-01/state.json；交付监督状态：/home/riscv/riscv-lab/o3-gemv-delivery-20261019/state.json。不要重复启动campaign。通过后监督程序自动严格复核、封存、原生Windows复算并本地提交；失败会保留日志并停止，不自动重跑EMU。
