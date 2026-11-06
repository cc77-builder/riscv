# G/GQ 完整消费者参考结果

合同：`r2-s3-first-forward-gsq-v1`。验证日期：2026-11-06 UTC。

**在既有合成模型、规定共同 prepare 后，G 与 GQ 的新同镜像均通过固定 p0/token1 的首次完整 forward 参考验证；GQ 的窗口退休指令比 G 少 391,067 条，减少 8.09865%。本组合尚无新目标 EMU、香山周期或完整应用加速比结论。**

本记录的机器可读入口为 [REFERENCE.json](REFERENCE.json)，规格与边界见 [CONTRACT.md](CONTRACT.md)，量化函数自身的独立资格见 [上一级 RESULT](../RESULT.md)。源码、完整原始状态、进程回执、失败记录及来源清单在 [紧凑证据包](evidence/g-gq-consumer-reference-01.zip) 与 [完整原始文件清单](evidence/manifest.json)。

## 实际结果与比较口径

| 本次同镜像方法 | 完整 forward 的 NEMU instret | 整个参考程序 retired | 完整 state | 末端 flags |
|---|---:|---:|---|---:|
| 原 G：GS32 GEMV＋原 scalar quantize | 4,828,794 | 8,522,188 | 3,691,424B 独立 golden 全等 | 1 |
| GQ：同 G GEMV＋新 GS32 quantize | 4,437,727 | 8,131,121 | 3,691,424B 独立 golden 全等 | 1 |
| GQ 指定末 logit 负控 | 4,437,727 | 4,592,220 | 原完整比较器在 byte 152476 拒绝 | 1 |

完整 forward 窗口包含 method 读取、分派、全部量化和模型运算，四个 CSR 读取沿原合同保留，未添加快路命中计数器。窗口不含模型生成、packing、启动/init 及窗口前的共同 prepare；本次不是生产模型的整程应用测量。两个正常参考镜像逐块核对，除 offset 73,424,408 起的四字节 selector 外全部相同；UART 均为 0，共同 prepare、模型和零初态一致。两臂完整 guarded-state 的 SHA256 均为 `027e4200fcbbd6453806591c355b616df27acbd219d4008d24893ac685bd814a`。

391,067 / 4,828,794 = 8.0986474%。整个参考程序还包括 prepare 与验证扫描，其 retired 减少 4.58881%，这个数不是应用收益。NEMU 的 cycle CSR 也不是香山微架构周期。旧 G 基线和其已有证据仍保留；本次分母使用新共同镜像实测 G，不用历史计数替代。实际快路命中比例没有单独测量。

三个新原 NEMU 进程分别是 PID 19584、19585、19586，退出码 2、0、0；负控真拒绝，两个正常案例通过。全部进程均 direct-child-reaped、process-group-absent，无超时或残留。完整 guards、模型与 gold、TLS/errno=12345、FRM/flags、控制字、初末寄存器/CSR 和真实 trap 均按原比较器检查。旧量化原型的四进程不混入本次三进程计数。

## 改动及真实执行身份

新增 GQ cached clone 和薄公开入口；仅替换该 clone 的五处量化调用，整段可逆恢复到 G。七处 K288 GEMV 仍走 GS32，唯一 W2 矩阵乘仍走 FR。W2 的 hq 激活量化属于本次改动。原 G、原 quantize、FP32 组间顺序、模型布局、公开枚举和稳定默认保持原样。

实际重新编译 consumer-core，并把已独立合格的量化对象链接进新共同 CORE，未靠修改标签或替换结果取得通过。最终 ELF 检查确认：

- dispatcher、GQ 公开入口和 GQ clone 的实际调用关系；
- 原 G 五处实际调用均到原 quantize，新 GQ 五处均到 `r2_quantize_gs32_rvv`；
- 完整 248B 新量化体仅 GS 与 scalar fallback 的两个 AUIPC 对发生重定位，其余机器字与合格原型相同；
- 共享 GS 实际地址 `0x8498bb3c`，fallback 实到原 quantize `0x80003a6c`；原 quantize/fabs/round 指令及常量身份保持；
- 八个 GEMV 路由、七个 consumer 的 21 处 norm 调用、独立 gold 与初始存储身份通过。

新 ELF SHA256：`737d2eeb080363114419431b2543329e37588d5d708daccb5ea8ad12b937c2dd`。新 BIN SHA256：`80b6934994bd329d33bdce3d052ab234ce528fe6dad4d4a4ec2062a8eeb9cedc`；镜像 77,118,304B。

## 实际执行、失败与恢复

11:38:39–45 UTC 的首个作业完成 GNU 和全部静态 ELF 检查，但 reference 输入检查报 `S3 runtime module roots differ`，尚未启动 NEMU。该失败保留在证据包内。

准备阶段曾在同一 Python 解释器中加载 live repository 的辅助闭包，随后参考阶段要求冻结 snapshot 根。11:41:44–56 UTC 改为在新解释器中只加载同一 reference controller，原 root 检查与所有源码不变，三个参考进程全部通过。没有通过清空全局模块、放宽判据或修改官方程序解决问题。

本批 CPU1、GNU -j1；每个参考最多 100M API/600 秒，owner 630 秒；全批原截止 12:13:40 UTC 未延长。实际工程操作和各子进程终态见证据包 `readback/external-tool-receipts.json`。复现时把 prepare、build、reference 作为三个独立 Python 进程启动，避免再次混用辅助模块来源。

## 复现与回退

先准备合同指向的已冻结父输入，核对 `prepare.py` 中五份 base 文件、八份已合格 quantize 输入的固定 SHA。证据包 `raw/consumer-source-01/` 保留实际 base 副本、配置、四个新源文件及 SHA 清单。配置是本次运行的实际位置记录，不是新的团队工作区规则。

每一步使用新输出路径，并遵循当前 CPU 与运行协调预算。以下为已有接口的顺序，三个命令须分别启动进程：

```sh
taskset -c 1 python3 -B prepare.py --base BASE --config CONFIG_JSON \
  --quantize QUALIFIED_QUANTIZE_BUILD --output NEW_CONTROLLER
taskset -c 1 python3 -B NEW_CONTROLLER/build.py --output NEW_BUILD
taskset -c 1 python3 -B NEW_CONTROLLER/reference.py \
  --build NEW_BUILD --adapter ORIGINAL_ADAPTER \
  --identity ORIGINAL_IDENTITY_JSON --output NEW_REFERENCE
```

这里的大写参数须指向核验过的实际输入和全新输出，不重新使用本次冻结目录。新 controller 只保留参考入口；目标运行须按获准的目标合同另行绑定与排程。实验回退可选原 G selector `0x47533332`，无须更改原应用默认或重写量化函数。

## 指令支持与成本边界

对 T17 来源提交 `34bae6d4acceac939f958199dae53c14bc1f6183` 的只读源码核对确认，相关向量除法、动态 FRM 转换及整数窄化有活动实现入口。[FuConfig.scala](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/fu/FuConfig.scala) 将 Vfdiv 配置为 128 位、非流水且时延不确定；[VCVT.scala](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/fu/wrapper/VCVT.scala) 的普通转换接入动态舍入模式。[CSR 解码](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/decode/DecodeUnit.scala) 还包含非推测与向后阻塞控制。每组保留的除法及 CSR 操作都有实际成本，不能按参考退休指令减量估算目标周期。这项源码检查没有授予新 GQ 镜像的目标运行资格，也不新增本参考合同的验收门槛。

## 证据保留与后续判断

证据包 2,729,694B、330 个成员，SHA256 `12b850647af1997c2acc8af00a820573f12457175b788faa17650866b7a20f44`；已逐成员回读验证。完整原始清单覆盖 345 文件、781,063,245B，SHA256 `fd184cd71cedb26a5553d96abb93276e29239f657b4004f82c7af8342a34dc00`。

包内保留全部新源码/controller、构建元数据和对象、golden state、三个完整 guarded-state、寄存器/CSR/report、进程及失败回执。32 份大型 ELF/BIN/模型/fixture 副本仍留在原 WSL 输出，清单记录每个尺寸与完整 SHA；紧凑包依赖这些冻结父输入，不冒称脱离父输入可独立重建。原目录未删除或修改。

下一步值得结合原 FR/G/P 的真实目标结果，评估是否排程同一新镜像的 G/GQ 目标比较。参考指令减少已经实测；具体周期收益、更多 token/position、实际快路比例及完整应用收益仍未验证。本次资格限定于上述固定 p0 合同。
