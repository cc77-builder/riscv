# O3 INT8 GEMV应用评估

2026-10-19开始，本地分支local/o3-gemv-20261019，未推送GitHub。当前处于软件/镜像准备，尚无O3全核性能结果；不要以模型通过代替RTL通过。

[测试合同](CONTRACT.md)规定四尺寸、三数据集、两计时口径、基础/复用两种软件和公平RVV对照。复用G4固定O1/O2，不修改硬件或旧基准。

模型及生成器检查：

    python3 -B -m unittest discover -s team/workloads/o3-gemv -p 'test_*.py' -v

在完整香山检出中编译新镜像，输出目录必须不存在：

    python3 -B team/workloads/o3-gemv/build.py --output /absolute/new/images

所有实际运行和结果随后以新的campaign目录记录；本轮不自动O4/O5/G5，不改变默认模式，正式T16报告后置。
