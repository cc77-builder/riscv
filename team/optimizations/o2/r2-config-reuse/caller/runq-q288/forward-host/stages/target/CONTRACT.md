# 完整 forward 的目标数学运行时入口 v1

身份 `r2-s3-forward-math-closure-v1`。这是团队新建的依赖探针，原样 upstream、AM/klib、官方验证器和旧目标运行输入不变。

先使用本机实际 `riscv64-linux-gnu-` 工具链定位并固定 `libm.a`，对显式 volatile 外部调用进行 RV64/lp64d 编译，再用普通 archive 成员选择规则做 `ld -r` 部分链接。不使用 `--whole-archive`，不拉入整份 libc，也不为消除未解析符号填写成功返回的空桩。

入口覆盖源码中的 `powf/sinf/cosf/expf/sqrtf/round/fabs`、实际宿主编译出现的 `sincosf/roundf`，以及域检查的 `fabsf`。本探针关闭 builtin，不能把常见编译器会内联 fabs 当作链接前提。保存完整命令终态、工具/输入 SHA、链接 map、所选成员原字节、所有未解析符号、ELF 属性/符号/重定位和反汇编。检查 TLS、IFUNC、stack protector 必须来自本次实际对象，不能将某个 glibc 版本的可能实现当作本机事实。

本入口只给出 `STATIC_CLOSURE_INSPECTED`；即使部分链接退出 0，也不代表目标可启动或数学数值正确。`target_runtime_ready=false`、`target_emu_runs=0`、`performance_qualified=false` 保留。后继目标数值探针须另行固定实际适配及输入，保留 original round 语义、RNE 和原样 DiffTest；遇到宿主/目标数值差异须保存反例，不改 golden 或降低旧验收标准。

使用既有常驻 WSL source，输出在仓库外新目录；单进程单核，保持总体最多四核。所有失败记录保留，原目录不可复用覆盖。读取静态库不修改该库；结束时重新核对工具、脚本和 archive 身份。
