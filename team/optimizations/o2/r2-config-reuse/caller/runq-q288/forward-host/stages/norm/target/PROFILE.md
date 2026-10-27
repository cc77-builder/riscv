# 完整首 token 的参考退休 PC 分布诊断

身份 `r2-s3-first-token-reference-pc-profile-v1`。目的为后续瓶颈选题建立实际指令分布，不重复开展 norm 枚举，不提供香山性能资格。

只从已合格的团队 reference adapter 源码派生一个外部宿主观察器，四处有限插入可完整逆回原字节。原 NEMU shared library、官方头文件、原 adapter、首 token ELF/BIN、消费者与目标四例均不修改。仍逐次 `difftest_exec(1)`，观察器只读取已有执行前 PC、退休计数和执行后的寄存器副本，没有 TO_REF、异常抑制或跳过执行。

固定最终 build-03 的 FR-cache、TA-cache 正常案例各一次，单核顺序运行，总共两个 NEMU 进程，无新增 EMU。每例100M API calls、内部600秒、适配器子进程外部等待630秒、128MiB单文件。运行CPU限制在本轮现有四核预算内。

窗口为实际初始 instret 指令起至末尾 instret 指令前，即计入起始读取、排除结束读取，包含两者间实际 fence 和 dispatch。四条 CSR 每条必须恰好退休一次、顺序一致。每步退休增量0或1，窗口内必须为1；PC按半字槽统计，全部计数之和必须同时等于观察到的全局退休数差和寄存器中的 instret 差。四个实际 CSR 值须等于完整 report，不能用程序运行次数或静态指令条数推算。

每例重新运行现有完整 reference validator，且所有 image、内存 dump、初末寄存器及 CSR 文件须逐字等于最终合格参考。PC映射使用实际 ELF 与固定 readelf 符号表；同范围别名合并，不同范围不能重叠，无法分配的PC单列并纳入总数，不以猜测消除。每PC的原始计数、完整 guest 状态、派生 adapter 源/编译命令/依赖、原始父源码及历史源码闭包均保存。

这些是原参考的动态退休指令计数。不同指令延迟、访存、预测、向量工作量和定制指令吞吐没有被换算成目标周期；不能把占比叫作目标耗时占比，不能据此发布性能优选、token/s 或新的目标正确性。失败保留，不自动重复采样或续预算。

`profile.py run` 接收 `--build --reference --adapter --identity --output`，所有路径必须匹配实际合格记录，输出新建于冻结输入外。离线恢复后，从 `profile/closure/repo/.../norm/target/profile.py` 执行 `recheck --build RESTORED_BUILD --reference RESTORED_REFERENCE --profile RESTORED_PROFILE --output NEW_AUDIT`，只读取原始 histogram 和 dump，核对历史输入、精确派生和计数守恒，不重新运行 NEMU。
