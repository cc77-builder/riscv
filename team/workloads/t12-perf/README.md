> 当前入口：最终构建/运行源码与`1ba275411d41b6454b14ecfc537be10cd7202739`一致；original190和lean199分别已有完整DiffTest运行。见[复现命令与原始证据](../../evidence/t12-r2-20261014/README.md)及[整合报告](../../docs/t12-zufan-integration-20261014.md)。以下是早期190计划的历史说明，“待编译/待运行”和缺少RAW链的描述不代表后继lean版本；不得直接照旧文覆盖输出目录。

# T12 压力与配对性能实验

2026-10-14；内部合同 `vdot-s8x8-r32-v0.1`。当前是待交叉编译、待全核运行的增量实现，不是整核 PASS。

## 入口

新增 `team/tests/generate_t12.py`、本目录 C/汇编/Makefile、`team/scripts/t12-tests.py` 和严格检查器。复用原 `vdot-exceptions/harness.S` 与 `judge.c`，不修改黄金语义或生产硬件。生成器要求全新数据目录；构建/运行要求独立、已提交、干净且父提交匹配的 Git checkout。

单镜像计划 190 条记录：13 个压力/异常恢复场景、11 边界 + 64 固定随机输入各执行 vdot/RVV、3 个测量场景各 1 次空窗口和 4 对 AB/BA 交替样本。所有点积源用低八个 signed int8，完整目的低32补码、高96零。初始化/输出在既有汇编边界外完成；压力区没有 printf。非法 VL 取 0/1/7/9/16；捕获故障 CSR/PC/mtval 后返回同一 stub 紧邻合法 vsetvl/vdot，独立核验恢复 CSR 和未写的非法目的 v16。

原 baseline 采用 `vwmul.vv` 的16位乘积与 `vwredsum.vs` 的32位归约，支持正极值131072；禁止16位累加溢出或8位结果。功能调用恢复实际入口 vl/vtype。比较所有32个向量寄存器，RVV 只排除明确声明的 caller scratch；vdot 不排除任何 scratch。比较六项向量 CSR、入口全32状态、guard、VS、精确陷阱协议；不弱化原 judge。

## 运行（已获准的 Linux 会话）

先将本增量放入以固定父 SHA 为起点的新 clone 并正常本地提交。`S` 是真实实现提交，不填父提交来冒充新代码。以下依赖路径必须由接续者实读确认；当前受限会话未确认 Linux 路径。

```bash
# 仓库根；不 Push。先运行 host 检查。
python3 -B -m unittest discover -s team/tests -p test_t12.py -v

# 按用户指定布局；S 取该实现 checkout 的完整 commit，AM 取已核对的固定库。
python3 -B team/scripts/t12-tests.py build --expected-source "$S" \
  --am "$AM_HOME" --output /home/lizufan/xiangshan-t12-perf-20261014/runs/implement-build

python3 -B team/scripts/t12-tests.py run --expected-source "$S" \
  --build /home/lizufan/xiangshan-t12-perf-20261014/runs/implement-build \
  --output /home/lizufan/xiangshan-t12-perf-20261014/runs/implement-run \
  --emu /home/lizufan/xiangshan-t10-t11-supervisor-20261013/repo/build/emu \
  --nemu "$NEMU_HOME" --reference "$VDOT_NEMU_REF" --flash "$COMMON_FLASH"
```

AM 使用既有来源审计及固定 revision，`make -j1`，发现 AM 已有活动构建则拒绝启动。本实现自己的构建串行；不提供跨会话永久锁，不保证别人在检查后的竞争，因此接续者仍需协调共享 AM 构建时段。make 最多300秒；EMU 最多1200秒、500万处理器周期、128MB内存。EMU 必须严格匹配已验收 hash，并证明新提交 src/build.sc 与实际 EMU 来源相同；NEMU 使用现有1.1.0来源门禁且 hash 固定；flash 同旧验收 hash。所有长子进程有 PID、命令、日志、start/end/实际 exit；超时回收本次进程组，不终止其他任务。驱动运行门禁不会启动 WSL、修改 safe.directory 或绕过拒绝。

成功输出包括 `checked/raw.csv`、`checked/analysis.json`、反汇编、来源回执、独立 runtime/process JSON 和压缩原日志。检查器强制完整有序 case、目标负控、唯一 summary、开启 DiffTest、summary 后 GOOD TRAP、实际 exit0。失败不能由 wrapper exit0 掩盖。

## 性能解释边界

- `complete`：每次独立调用具备一般合法入口恢复功能，与成熟 baseline 相同；vdot 已有配置在共同 harness 中准备。
- `known-config`：单独消融固定 e8/m1/VL8 下省去每点积两次 CSR 保存读的 baseline。它不能替代任意入口配置恢复的完整接口。
- `independent-batch`：每轮四个独立目的，baseline 将相同阶段配置合并，不为美化比例反复插入不必要 vset；16轮共64点积。
- 空窗口包含相同次数的 loop 控制和同等结果存储/fence，不含算术。报告原始窗口，不减空窗口，也不将其当作精确可加减的常数。
- 计数器顺序为 `fence; rdcycle; rdinstret; kernel; 全宽结果store; fence; rdinstret; rdcycle`。结果存储依赖所有目的，减少测量终点脱离计算的风险；fence 只承诺内存排序，不是经校准的全指令退休屏障。两个计数器窗口也不完全同边界。
- 输出所有4对样本及中位比例，允许 RVV 更快。首次样本在前面的功能测试之后；重复样本继承真实缓存/预测器状态，无 cache flush，不声称严格冷启动。
- 这些是未校准的处理器计数器窗口，含控制、配置、读计数器和结果存储成本。不能称为 FU 精确 latency、纯 II，不能用 Verilator host 秒数替代。
- 依赖链和含 load/store 小内核的配对测量本批未实现/未运行；长 RAW 压力属于功能场景，不是这两类性能结果。

## 微架构观测

当前没有新 RTL 观察点，复用旧 EMU 的收益大于在不能运行时盲目重编的成本。即使190条架构记录全过，也只能关闭相应功能项。年轻 vdot 已发射后 kill、共享端口竞争、实际 ROB/FTQ 回绕全部仍未观察。详见报告的信号方案；不得用循环次数代替事件。
