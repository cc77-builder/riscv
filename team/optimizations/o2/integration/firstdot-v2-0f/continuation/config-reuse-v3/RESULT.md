# 配置复用限定筛选结果

## 14. 配置复用有界筛选：CONFIG-REUSE-DIVFIX0F-CLEAN02-20261027-01

第24条。结果：**PERFORMANCE_CANDIDATE**；功能与原文复算PASS。限定8×32/dataset0/C ABI完整调用窗，每格4正式样本。候选BIN不同，硬件、数据、布局和调用计划相同；不称同完整镜像比较。

| 方法 | firstdot平均cycles | 配置复用平均cycles | 退休指令(firstdot→配置复用) |
| --- | ---: | ---: | --- |
| basic vdot | 645.50 | 643.75 | [276] → [267] |
| reuse vdot | 282.25 | 273.00 | [182] → [175] |
| basic rvv | 356.00 | 356.00 | [180] → [180] |
| reuse rvv | 300.75 | 299.00 | [124] → [123] |

reuse vdot相对firstdot减少3.277236%；相对本次最快RVV减少8.695652%，RVV/vdot=1.095238×。
未解释对照项：[]。功能与性能结论分开；决策：KEEP_FOR_EXPANDED_VALIDATION_ONLY，本次不扩大矩阵、不切stable默认、不推送。

实际7个目标进程：V2的2个保留并排除，V3新5个功能通过；5次正常exit0、2次预期负控exit1。选用V3的32正式窗口、含重放96窗口、48对全窗口重放（一致=True）；firstdot24窗口与原干净合格对照一致=True。高位bit100拒错及正常恢复、NEMU完整128位结果、CSR与O2生命周期均PASS。

V2停止原因是对照BIN被工具误作实际加载BIN，正常目标exit0且UART failures=0，不能因此把原失败验收改为PASS。V3只修复测试适配层，保留共享对照哈希校验；61项主机检查PASS，含真实旧日志失败复现及错误镜像/篡改拒绝。原失败原样封存。

V3首次独立审计又因循环变量遮蔽物理身份而误报；原失败保留。独立新审计器仅重命名两个循环变量，真实完整批次成功及模拟最终身份漂移仍拒绝两项检查PASS。新audit-02及completion-02通过，全程不新增EMU；冻结运行源码和旧日志不改。

候选来源zufan fcf4a11的26文件＋39相同依赖；新适配器V3及执行器独立绑定。生产RTL仍0f；全核默认选择未变。新多形状/多数据集矩阵、普通公共C应用、面积/STA/功耗、成员人工复现均NOT_TESTED。4×13继续RVV回退。

本地原始输出：/home/riscv/riscv-lab/software-import-20261026/config-reuse-clean02-02。封存manifest：d5cbde2b37239214c6632b891dd61d94f9483cb45b51b7cacedd293e6a898bd5；原文审计及所有版本/镜像/配置/命令/实测数值见配套JSON。档案验证仅为字节封存，原文复算仍依赖本地物理输入。
