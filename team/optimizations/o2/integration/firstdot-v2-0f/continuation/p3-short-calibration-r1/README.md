# P3校准运行器R1

[结果](RESULT.md) · [合同](CONTRACT.md) · [下一轮](NEXT_STEP.md)

本轮只提供经宿主验证的显式路径/冻结模块、进程组监督器、纯失败即停状态机和候选命令描述；没有目标启动CLI。
pc_context.CAL_HERE是本叶唯一根，freeze.REQUIRED强制新源码集合，bounded.py持久化触发进程和线程身份。
test_freeze.py、test_supervisor.py为宿主测试；host_fixture.cpp只使用原始宿主运行时对象。

本轮证据已封存，重做宿主测试须换输出目录，不覆盖现有host-tests及INPUT_FREEZE。旧V1代码、freeze与失败不修改。
