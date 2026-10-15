# NEMU vdot 候选扩展：固定补丁与平台配置

当前补丁 **1.1.0**，合同 `vdot-s8x8-r32-v0.1`，平台 profile `xs-16ae9dd-vdot-runtime-tval-v1`。基线仍为 `a48a11f208ff81ad765591d83271d1b339fb3861`；[manifest](manifest.json) 与 [补丁](vdot-s8x8-r32-v0.1.patch)绑定七个变化文件，补丁SHA256为 `6c165bf5f94ef0bfb4f894a5f06eb6d620d4a7e0e12f3b1400fa72811f5d24db`。1.0.0原始补丁、manifest和此前README保留于 [history](history/README-before-t10-closure-20261013.md)，不可拿旧库替代当前reference。

1.0.0算术仍为独立数学实现：精确custom-0分派、先读取两源快照、signed8点积从零求和、完整128位目的写回、状态不合法不产生部分写入。1.1.0没有复制硬件归约树，也没有改测试期望；仅增加显式平台xTVAL配置。固定香山中仅VL不等于8而其他decode状态合法时，非法性由FU发现，TrapInstMod未捕获该机器字，故xTVAL为0；decode已知非法保留机器字。适配谓词只读架构指令/配置，不读DUT结果、PC或用例ID。所有xTVAL比较继续启用，不跳过vdot。

RISC-V privileged规范允许非法指令xTVAL选择零或机器字，具体平台应保持一致；参见 [Machine-level ISA](https://docs.riscv.org/reference/isa/v20260120/priv/machine.html)。该选择只支持已验证的固定香山平台口径，不代表任何CPU都应这样实现。本次真实验证为M模式，S/HS/VS/嵌套虚拟化和推测陷阱竞争不在已完成范围。

构建脚本显式要求 `CUSTOM_VDOT=y`、`CUSTOM_VDOT_XS_TVAL=y`、`TVAL_EX_II=y`、`NMIE_INIT=y`、`MDT_INIT=n`，与固定RTL的复位及异常入口匹配。普通NEMU配置中自定义选项默认关闭。reference与standalone使用独立检出、配置和二进制角色，schema2来源记录绑定补丁、全部实际源码/头文件、配置和binary SHA256。

```bash
# 先准备版本匹配的依赖；脚本不会升级源码到远端最新
bash team/scripts/prepare-nemu-vdot.sh reference
bash team/scripts/prepare-nemu-vdot.sh standalone
```

`TEAM_NEMU_VDOT_ROOT`设置独立构建根，`TEAM_NEMU_BASE_ROOT`可复用固定基线对象。运行前 `artifact_guard.py nemu-runtime` 必须通过；来源异常时不得修改权限或放宽白名单来假装验收。当前本机reference已实际构建、加载并通过117项全核DiffTest及bit100负控；reference API另有10054合法/22非法检查，但后者是状态注入式ISS检查，不是117项全核运行数量。

本机新standalone构建的来源检查仍拒绝用户目录下解包的readline头文件，因此**本轮不宣称新standalone已通过来源验收**。可以在有正常系统开发包的环境独立复现；不要求为此修改Windows或sudo越权，不使用该未验收standalone作为最终证据。共享reference没有这一阻塞，实际全核证据见 [验收报告](../../docs/t10-t11-acceptance-20261013.md)。
