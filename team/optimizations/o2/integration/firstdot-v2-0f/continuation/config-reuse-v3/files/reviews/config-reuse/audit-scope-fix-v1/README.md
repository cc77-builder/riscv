# 只读审计变量遮蔽修复

原raw_audit.py在审计开头用before保存物理身份三元组，随后for before,after遍历相邻进程回执，覆盖为dict；末尾用物理身份三元组与进程dict比较必然失败。只将循环局部变量改为previous/following，原物理身份、时间线比较和原文验收条件完全不变。

冻结V3运行源码及其输入哈希不修改；此次作为单独绑定的只读审计器验证已有5个新进程，不新增目标仿真、不改原始state/result/log。旧audit-01和pipeline失败保留，新审计使用audit-02及独立完成回执。
