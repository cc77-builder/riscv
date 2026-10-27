# 普通C适配器主机验证

17项标准库unittest测试通过；真实GNU/AM构建、ELF/BIN、公共对象和48次矩阵机器码比较通过，8×32有12次跨数据集比较。48个case完整字典多重集合不变，仅将8×32组及其dataset0/reuse/vdot首例前移。gemv.S/h、main.c和Makefile与冻结生成器逐字节相同。

覆盖：目标首例、缺用例、重复用例、缺目标数据集、目标符号错误、调用表篡改、外层输入漂移、混合身份、单调时钟、串行、PID唯一和重放顺序。主机测试新EMU为0；不能代替真实C运行。

实际命令和退出码：../c8-preflight-01/host-tests-01.command.json。
真实构建：../c8-preflight-01/host-build-01/。
此构建用于静态测试，实际运行将使用独立新构建并保存其身份。
