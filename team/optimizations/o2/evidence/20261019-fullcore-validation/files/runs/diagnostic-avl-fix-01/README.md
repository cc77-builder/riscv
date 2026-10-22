# 补充诊断 case9 的 AVL 依赖链修复候选

状态：候选主机检查通过，**尚未编译，尚未运行修复后的 EMU**。冻结仓库源码、原镜像及原始失败日志均未修改。candidate.patch 供主任务在当前冻结任务结束后复核应用；不能把本目录主机 PASS 算作 G3 全核 PASS。

## 已绑定的实际失败

diagnostic-build-02/o2-diag.bin 在 supplements-01/o2-diagnostic 中完成了前 9 个病例；第 10 个 vfex4-all-pairs 没有 PASS，也没有汇总。exit code 虽为 0，但存在 PMA address0、CRITICAL ERROR double trap 和 pc=0xe 的伪 GOOD TRAP，严格检查正确地拒绝了该结果。

- 第一条转换 dot：PC=0x80002be8、seq=1152、ROB=1:11；cycle111675 接受 VL8，111677 返回完整128位 0x000000000000000000000000ffffe421。
- 后续 vmv.x.s@0x80002bec 在仍为 SEW8 的配置下得到 0x21（33），并非 signed32 的 -7135。
- 冻结生成器用 signed32(-7135)^8 得到常数 0xffffffffffffe429。实际 0x21 xor 此常数 = 0xffffffffffffe408，作为无符号 AVL 输入 vsetvli 后得到 e8/VLEN128/LMUL1 的 VL16。
- 第二条 dot：PC=0x80002c00、seq=1153、ROB=1:16；cycle111696 真实 ACCEPT 显示 vl=16、illegal=1；111698 正常输出 exception=4、vecwen=0；111718 ROB self-flush，111719 父级 flush。
- 所以本次故障链指向软件生成器的 SEW 提取假设；已有证据没有显示该请求违反 FU 处理协议。完整根因身份及摘录见 failure-evidence.json、trace-excerpt.txt。

## 最小修复

只改变 generate.py 对转换序列常数的提取宽度：vdot 后当前 SEW8，使用最低1字节有符号值；VIDiv/VFDiv 后当前 SEW32，使用最低4字节有符号值。保持原有数据依赖结构，不增加 vset 或改变指令规范/RTL/NEMU。首条转换常数变为 0x29，实际 0x21 xor 0x29=8。

独立测试解释执行生成器输出的 vsetivli/vsetvli、vmv.x.s、li、xor 和全部18个操作。SEW从实际发出的配置指令读取，抽取用位掩码和符号位独立计算，不调用生成器的 dot 函数或复制修复行。每个 vset 的 AVL 必须精确为4/8，不能靠 clamp 恰好落在 VLMAX 掩盖错误。

新增6项测试覆盖：
1. 默认18操作完整依赖链及最终 SEW8/VL8、全32向量寄存器结果。
2. 原32位常数精确复现观察到的错误 AVL 0xffffffffffffe408。
3. dot结果+128、-130、-128、+127，包含低8位符号与32位结果符号不同的情况。
4. 错误“无符号8位提取”常数必须被拒绝。
5. 32位 0x7fffffff、0x80000000、0xffffffff 的符号扩展及最终 e8 配置恢复。
6. 错误最终 AVL、缺失依赖链必须被拒绝。

原10项测试加新6项测试，共16项通过，见 host-tests.log / host-tests-exit-code.txt。该解释器只覆盖本生成程序使用的指令子集，不是完整 ISA 模拟器，也不取代后续 NEMU/全核运行。

## 生成物差异与后续边界

generated-comparison.json 证明：10个病例的操作列表和全部黄金向量保持不变；前9病例的指令体逐项不变；cases.h 字节完全一致；第10病例仅6条 dot 后的 li 常数改变。预期提交总数仍为1158。kernels.S 和 manifest 身份发生预期变化，因此必须生成新的独立 build receipt/镜像并保留原失败批次，不能覆盖 diagnostic-build-02。

候选文件在 source/，候选生成文本在 candidate-data/。此目录没有调用 Makefile、交叉编译器或 EMU。冻结两个补充作业仍按原计划结束；后续修复运行由主任务调度，且只在正常完整通过后方可贡献覆盖。
