# O3 INT8 GEMV应用评估

真实O1/O2应用测量及Linux原始日志重审完成，Windows交付复算另见delivery回执；本地保存未push，正式T16报告后置。

四尺寸、三数据集、core/endtoend、basic/reuse、vdot/RVV；56项合格EMU作业（46项原通过复用、10项恢复补跑，另2项中断尝试保留），1280校验窗口，768正式性能窗口，4项代表重放逐seq一致。全部规定尺寸和有利/不利结果保留。

[合同](CONTRACT.md) · [封存结果与证据](evidence/20261020-application/README.md)

core包含所有A/x加载、乘法/归约、累加及输出寄存器形成，endtoend再包括kernel初始配置和结果存储；测试框架和VS启用在窗外。K=13的vdot标量尾部成本计入；RVV使用最多16项宽向量及动态尾部，不能称为已证明全局最优。

硬件O1/O2使用G4相同429硬件文件/21236依赖及固定EMU；未重构建、未改ISA/NEMU/旧基准。原测量execute冻结7a642b6，构建软件5fdeba3；恢复编排99f04b9、后处理恢复审核8aab2ed、顺序修复8b6163b；不同提交角色分别记录，文档提交不是重构建。

    python3 -B -m unittest discover -s team/workloads/o3-gemv -p 'test_*.py' -v
    python3 -B team/workloads/o3-gemv/build.py --output /absolute/new/images
    python3 -B team/workloads/o3-gemv/campaign.py --images /absolute/completed/images --output /absolute/new/campaign
    python3 -B team/workloads/o3-gemv/results.py --campaign /absolute/completed/campaign --output /absolute/new/results

不要重启已完成campaign或改写旧证据。新的完整复跑必须用新目录；不以离线复算冒称T17干净构建。O4/O5/G5、默认模式采用和人工ACK仍待后续。
