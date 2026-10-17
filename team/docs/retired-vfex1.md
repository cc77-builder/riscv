# 旧 VFEX1 实现已退役

2026-10-17 按用户要求从当前工作树删除旧实现，生产只保留 VFEX4 的
`VDotDatapath`、`VDot`、`VDotCfg`。T14 可选模式与 T15 独立参数实验保留。

删除范围：

- `team/legacy/james-vfex1/`：旧执行器、适配器、译码/陷阱辅助类、测试和旧脚本。
- `team/hardware/vdot/`：只构建旧执行器的 sbt 工程。
- `team/scripts/vdot-hardware-tests.sh`、`vdot-fu-tests.sh`、`vdot-decode-tests.sh`。
- `team/tests/generate_vdot_hardware_vectors.py` 及四个仅服务旧入口的诊断/失败门禁脚本。

当前验证入口为 `team/scripts/check-vdot-datapath.sh`、`check-vdot-fu.sh`、
`check-vdot-decode.sh`，全核使用源码绑定的构建与 T12/T13 入口。
共享独立模型、NEMU/RVV工作负载、VFEX4来源检查器与原始证据未删除。

## 历史恢复

完整旧生产接入固定于提交 `9bb544812df9b424e399ae3ca91899a904f583bd`；
删除前的归档布局固定于 `75e0e13b9b9fbef39b46e2555c90d3b1d91844fa`。
例如只读查看旧源码：

```sh
git show 9bb544812df9b424e399ae3ca91899a904f583bd:src/main/scala/xiangshan/backend/fu/vector/VdotExec.scala
```

若复验旧构建，另建对应提交的独立工作区，按当时依赖和记录执行；不要把
旧源码片段复制回当前生产树。`team/evidence/` 中的原始日志、源码摘要和
源快照按原字节保留，可能仍包含旧类名或路径。这些是历史证据，不是当前
可编译的第二套实现。旧验收工具要求旧源码时，应回到固定提交，不能删掉
来源门禁让新树冒充旧树。
