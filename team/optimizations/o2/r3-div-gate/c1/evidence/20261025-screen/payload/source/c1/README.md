# C1 DIV busy／owner 候选

本轮筛选完成，不采用。当前修复版保持 0f12df6；独立候选 3be0e3d 及原始证据保留，未推送。

- [结果、面积时序与取舍](RESULT.md)
- [预设筛选合同](CONTRACT.md)
- [状态等价关系及边界](STATE_EQUIVALENCE.md)
- [封存清单](evidence/20261025-screen/manifest.json)

state_model.py / replay_states.py 为抽象与实际轨迹检查；run.py / resume.py 保存初次失败与成功运行；screen.py / screen_after_ppa.py 执行条件筛选；audit.py 复核原始报告；review_dffs.py 保存映射计数检查（额外映射差异的解释见结果）；archive.py / verify_archive.py 用于封存及字节核验。脚本中的绝对路径是本次运行定位，移机重跑应另建输出并保持合同。
