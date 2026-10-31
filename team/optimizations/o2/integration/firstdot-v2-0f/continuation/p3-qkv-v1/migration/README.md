# P3 最小迁入与 GNU 门禁

本目录只包含独立软件包和宿主验证工具；保留当前 0f + firstdot V2 + C8 默认。
固定供体 ffd668bf1bc80850d382f514d13bb00316c85582；143 项源闭包另加 2 项普通 C 审计源，历史 19 个 Git 对象在独立清单中保存。

## 本轮入口

- build_check.py：核对冻结合同/源清单/0f AM 静态库，生成原样 QKV 测试源，执行 GNU 编译链接，完整数组/只读属性/路由/六函数机器字审计；另编译链接 TA/FR 普通 C 示例。
- audit_extra.py：验证真实对象重定位、fs0–fs11 写集、源码/对象/最终 ELF 负控；把源码复制到新位置重新生成、编译和链接，要求主 ELF/BIN 及两普通 C ELF 逐字节一致。
- package_check.py：编译 runtime 下 8 文件最小运行源包，要求三个对象和完整主 ELF/BIN 全相等。
- static_negative.py：把实际 ELF 的输入、packed 权重及函数指针各破坏一位，交给原生产 image_audit，分别按明确原因拒绝。
- runtime/：boundary、一次去重投影汇编、头文件及可选 pack/legacy full-Q 源。实际布局/别名/数值/CSR/ABI 以 ../CONTRACT.json 为准。

复验时为各脚本指定新的绝对输出目录，使用 taskset -c 4 python3 -B；无任何 target run 子命令。build_check.py 的 --output 为新目录；其余两个另以 --image 指向已生成 image 目录。可移动源码仅通过 audit_extra 的 --output 内部搬移复验。

## 本轮判定边界

GNU 编译/链接、源搬移、完整数组及机器字通过不等于目标全核通过。
迁入后的 target main 与 manifest 保留供体字节，仅用于 HOST_BUILD_SOURCE_EQUIVALENCE_ONLY。
其中供体的 0.5% 收益条件、18M 周期预算和合同名不能作为本地目标准入；
后续只能按本项目 P3 目标合同（1% 锚点、3% 保守收益）另外绑定检查器及预算。

普通 C 两变体示例用于指针路由及真实链接审计，数据为零初始化，不是合法可运行输入。
真实生成的主镜像使用固定 fixture，并由独立 host-numeric 门禁核查完整数值。
本目录脚本未执行 EMU、NEMU、QEMU，也没有修改 RTL、构建新核或上传。

结果入口：../evidence/migration/result.json。原始命令/日志/ELF/变异负控留在 WSL 的
/home/riscv/riscv-lab/software-import-20261026/p3-qkv-host-20261030-01/migration；
精简证据和完整文件 SHA 清单已保存至仓库。
