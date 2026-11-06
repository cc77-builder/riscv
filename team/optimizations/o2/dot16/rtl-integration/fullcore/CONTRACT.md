# dot16 首次整核差分冒烟合同 v1

准备状态：本目录是一个新的整核构建及六例合法指令镜像入口。源码准备不表示已经构建或运行；每次实际结果须由对应新输出目录的回执给出。

## 1. 目标和输入

本轮检查六路径生产候选能否经过整核取指、译码、重命名、向量寄存器数据通路、执行、写回及提交，与固定 feature1 NEMU 在一个合法 AM 镜像上正常完成 DiffTest。
保持官方 Makefile、DiffTest、NEMU 权威代码和旧验证器原样；不转移旧 T17/G3 的资格。

生产 patch SHA256 为 `5b5824bac200c2a775598686e550854f8276d5db007b72f4b7be92437b4d3416`。
构建前校验相邻 `source-manifest.json` 的六个结果文件及两个未改依赖，捕获实际完整 HEAD、硬件文件、递归依赖、脚本、工具及环境。
HEAD 由 `--expected-head` 显式传入；源码实际字节还必须满足候选守卫。未提交候选允许构建，并保存其 patch、新文件及源码快照；不把脏树描述成已提交版本。

feature1 reference 固定为实际已验证的库：

`/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-nemu-reference-20261106-0105/feature1-01/build/riscv64-nemu-interpreter-so`

SHA256：`cc768488944941d59442727a96e0a19206e24872dcefed0052cf6cb3694a3fae`。
它的 API 资格使用 1400 字节寄存器复制布局、LIGHTQS 关闭和两参数 regcpy；新 EMU 的实际接口头与编译配置必须匹配后才能运行。本镜像不覆盖尚未取得硬件资格的 dot16 非法指令 xTVAL 策略。

## 2. 新 EMU 的构建边界

只用常驻 WSL checkout，默认 `ROOT/build` 必须事先不存在，并作为本次独占生成目录；不清理或覆盖旧 build。
该路径由官方 `SimTop.scala` 和 DiffTest 的生成器使用。日志、命令、回执、薄 Mill 启动器及快照放仓外新 run 目录。
复用现有且已被 Git 忽略的 `out/dot16-fu-20261106-pro2` Scala 缓存及下载依赖；本次是复用缓存的新整核构建，不是纯 C++ 增量构建或新机器无缓存复现。

固定环境：

| 项目 | 值 |
| --- | --- |
| VDOT_DOT16 / VDOT_O2_ELASTIC / VDOT_T14_FUSED_INPUT | 1 / 1 / 1 |
| VDOT_O1_HANDOFF | 0 |
| VDOT_O1_TRACE / VDOT_O2_TRACE / VDOT_T12_TRACE / VDOT_T13_TRACE | 全部 0 |
| 核心配置 | MinimalConfig，NUM_CORES=1 |
| EMU_THREADS / EMU_TRACE / NO_DIFF | 1 / 0 / 0 |
| WITH_CHISELDB / WITH_CONSTANTIN / WITH_ROLLINGDB | 全部 0 |
| 原生编译 | 已绑定的 GNU gcc/g++，OPT_FAST=-O3，OPT_SLOW=-O0 |
| 本轮拟用 CPU | 1,2,3；make -j3；以实际团队资源窗口为准 |
| Mill 调度并发 | -j1，--no-server |
| Scala 预编译控制 JVM | -Xmx3G，-Xss8m |
| make 内 Mill 控制 JVM | -Xmx1G，-Xss8m |
| elaboration fork JVM | -Xmx8G，-Xss16m |

先运行官方 `xiangshan.test.compile` 并等待其进程退出，再执行官方 `make emu`。缓存保留同一源码身份，避免编译控制 JVM 的较高堆和生成 JVM 同时驻留。
新薄 Mill 启动器只把官方 make 的首个 `-i` 替换为已使用过的 `--no-server -j1`，其余参数原样转发；不修改官方文件或旧 builder。
Java、Mill 和 Verilator 由入口的三个显式路径参数选择，再逐工具核实际路径与 SHA；本次进程环境不依赖登录 shell，也不改变用户或系统配置。
构建源与工具身份前后复核；原运行日志、GNU time 阶段记录和每 30 秒的 WSL 进程组/内存采样保留。
墙钟保护上限默认 3600 秒；失败或超时停止本次进程组并保留全部中间件，禁止自动清理、换源或重试。

命令入口示例（必须先获得团队相应资源窗口）：

```sh
python3 -B team/optimizations/o2/dot16/rtl-integration/fullcore/build.py \
  --repo /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/checkout/source \
  --output /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-fullcore-20261106-pro2/build-01 \
  --expected-head c981529dc6e493fb7deee8429b9ce05fd197497b \
  --cpus 1,2,3 --jobs 3 --budget-seconds 3600 \
  --firtool-dir /home/lizufan/riscv-tools/firtool-1.62.1/bin \
  --java-home /home/lizufan/.local/share/graalvm-jdk-21.0.12 \
  --mill /home/lizufan/riscv-tools/bin/mill \
  --verilator /home/lizufan/riscv-tools/verilator-5.052/bin/verilator
```

旧 T17 的四核构建曾实际用时约 17 分钟；本候选源、缓存和 trace 配置不同，此值只用于排期。
3 核构建可先按 20–35 分钟估算，不作通过要求。Windows Available、commit、WSL swap/PSI 和全部构建进程需结合观察；单个空闲内存数字不作为额外验收门槛。

## 3. 六例合法 AM 镜像

每个汇编入口只执行一条 custom 指令，顺序固定为 dot8、四条 dot16、dot8。每例先按 e8/m1/VL16 加载完整两路 128 位，再选择本条 VL。
非别名目的预置为全 1，输出内存也预置非零；别名目的保留源数据。记录指令前实际 VL、vtype、vstart，要求分别为表中 VL、`0xc0`（e8/m1、ta/ma）、0。
执行后以 e32/m1/VL4 存下全部四个 32 位字。C 用独立 int64 标量逐项乘加，核对低 32 位及高 96 位零。

| 例 | 指令与寄存器关系 | A / B 的 16 个 signed8 值 | VL | 低32位期望 |
| --- | --- | --- | ---: | --- |
| 0 | dot8，vd=v10，vs1=v8，vs2=v9 | 两源低8全0、高8全-128 | 8 | `00000000` |
| 1 | dot16，vd=vs1=v8，vs2=v9 | 同例0 | 16 | `00020000` |
| 2 | dot16，vd=v0，vs1=v8，vs2=v9 | 两源全部-128 | 16 | `00040000` |
| 3 | dot16，vd=vs2=v9，vs1=v8 | A全部-128 / B全部127 | 16 | `fffc0800` |
| 4 | dot16，vd=vs1=vs2=v0 | 两源均为[-128,127,-1,0,1,2,-2,3]重复两次 | 16 | `0000fe28` |
| 5 | dot8，vd=v10，vs1=v8，vs2=v9 | A全部-128 / B全部127 | 8 | `fffe0400` |

AM 源码使用固定 `086a238062fdfb3281b745a537b361983d0154b5` 的既有 T17 目录。
已有 `am-riscv64-xs.a`（`57501f59d55d1b15116d9022ffc2d5efcc74bcde8c5674d7f31db0714e04b933`）与
`klib-riscv64-xs.a`（`f45d8c2049384123642b8c5d4a86f46be285d785ac5d16438eee510347eafda1`）只读复用。
通过 GNU make 的 `-o am -o klib` 使用这两个已固定库；所有新对象和 ELF/BIN/反汇编在新输出目录。原 AM 文件、库及源码身份须前后不变。
新 C 禁用自动向量化；ELF 要核对六函数内实际自定义编码恰好为两条旧编码和四条新编码。保留 boot flash 的来源、字节、编译命令和 SHA。

独立镜像准备命令（单 CPU1，不包含 EMU）：

```sh
python3 -B team/optimizations/o2/dot16/rtl-integration/fullcore/smoke.py image \
  --repo /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/checkout/source \
  --output /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-fullcore-20261106-pro2/image-01 \
  --am /home/lizufan/riscv-lab/t17-clean-20261024-0854/clean-02/xs-env/nexus-am --cpu 1
```

## 4. 一次实际差分的通过要求

新 EMU 与新 AM 镜像绑定固定 reference、flash、单线程、128 MB RAM、seed=1，最多 300000 cycle、10 分钟墙钟；上限只是运行保护。
完整保留 stdout、stderr、命令、输入 SHA、起止时间、退出码及清理状态。

运行前，使用新 EMU 的实际编译器和新生成头构建一个无 reference 初始化副作用的布局探针。它测量相对 `RefProxy::regs_int` 的各块偏移和末端，要求跨度1400字节；另将八个架构状态 typedef 的完整字段类型、顺序、数组长度与 API 固定头逐项比较。固定头 SHA 为 `6a2ce3ab51893908f74452522ab03c553cf7fa7e8aa25f74ea84d79aa45f044d`，API 来源为 `23056586264f8aacff65ba7ab5ceca6f8e5fddf680da8dd3e731c2a5673a7012`。
官方 `RefProxy` 仍按其现有三参数声明调用两参数 NEMU 导出；不修改任何一方。布局检查不等于动态调用资格，实际可用性由本机 ABI 下随后唯一的真实 EMU 差分限定。

单次差分命令：

```sh
python3 -B team/optimizations/o2/dot16/rtl-integration/fullcore/smoke.py run \
  --repo /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/checkout/source \
  --output /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-fullcore-20261106-pro2/smoke-01 \
  --build-record /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-fullcore-20261106-pro2/build-01 \
  --image-build /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-fullcore-20261106-pro2/image-01 \
  --reference /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-nemu-reference-20261106-0105/feature1-01/build/riscv64-nemu-interpreter-so \
  --reference-inputs /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-nemu-reference-20261106-0105/inputs --cpu 1
```

同一次运行必须全部满足：

1. 真实退出0、`HIT GOOD TRAP`，六条用例记录按顺序出现，且唯一末尾汇总为 `DOT16_CORE_SMOKE_PASS cases=6 dot8=2 dot16=4 failures=0`。
2. 实际出现 `The first instruction of core 0 has commited. Difftest enabled.`，唯一加载 reference 路径等于固定新库。
3. 运行不包含差分不一致、ABORT、坏 trap、断言、周期超限、`CRITICAL ERROR`、double trap 或 PMA 错误。复用旧通用失败检查并在新合同内补足后面这些已知失败信号；不修改旧检查器。
4. 进程组清理完成，源、镜像、参考及启动输入身份未变。

结果仅说明这一固定候选与固定合法镜像的整核差分冒烟。它不覆盖非法 trap、完整 G3、随机/取消/竞争矩阵、应用性能、功耗或 ASIC 时序。
