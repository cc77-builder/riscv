# O2 R0：基线固定与复现入口

本目录完成 R0 的输入身份固定、配置准备和主机预检。工程主线仍为 O2，两种配置由 profiles.json 明确区分。R0 不产生新的 RTL 性能、综合结果或独立成员复现结论。

## 文件与身份

- baseline-lock.json：B0 的文件散列、依赖提交、工具身份和唯一已知源码差异。
- config.example.json：通过环境变量指定机器路径；没有隐式搜索旧镜像或替换版本的逻辑。
- profiles.json：observe 用于已有全核观察/性能验证，cost 关闭四类 trace。
- repro.py：统一预检、生成命令及按显式请求构建。
- test_repro.py：错误配置、坏文件、路径迁移约束与构建保护的主机检查。
- R0_STATUS.md：本次完成情况和限制。
- evidence/20261021：本次预检、负控及主机检查的精简证据。

B0 发布源码基点是 9b6cf074951dbd51e1670c5fbc7111a97c362b3f，实际受测 O2 EMU 构建源码是 b218cbc6e6b135e4ff219a902a9284a59d3c82c9。O2 EMU 的 SHA-256 为 ac0123280bf6c742d27a7650505bc1d91db350d1519806edfd0be9c7ea208a57。

主仓库的 429 项原构建输入中，build.sc 已增加 O4 vdotCost 目标；其精确差异及当前 Git blob 单独固定。生产 src 树和 21,236 项依赖文件保持原身份。入口不会对其他 build.sc 修改放行，也不会改写旧硬件 pins。旧 G3 hardware_guard 对当前 build.sc 会拒绝，这是预期的版本保护。需要真正复跑时使用新构建生成的新 pins。

## 1. 恢复依赖与设置路径

必须在完整香山 checkout 的 Linux/WSL 环境中操作。新成员先恢复相同提交与递归依赖；126 个依赖仓库的完整提交在 baseline-lock.json 中。GitHub 仓库不含本机历史构建目录和大二进制。

从仓库根目录执行，路径按实际机器设置：

~~~bash
export REPO_ROOT="$PWD"
export LAB_ROOT=/path/to/restored/riscv-lab
export XS_ENV_ROOT="$LAB_ROOT/xs-env"
export JAVA_HOME=/path/to/graalvm-jdk-21
export FIRTOOL_DIR=/path/to/llvm-firtool/1.62.1/bin

python3 -B team/optimizations/o2/repro/repro.py preflight \
  --config team/optimizations/o2/repro/config.example.json \
  --profile observe --output /absolute/new/r0-observe
~~~

模板的 locations 使用固定的历史目录布局，根路径可配置。需要采用不同布局时，先明确制定新的输入锁及来源记录，不能只改一个路径绕过身份检查。相对路径按配置文件所在目录解析；未设置变量、越界路径、未知配置字段和缺失文件均拒绝。

本机已解析配置在 /home/riscv/riscv-lab/o2-r0-repro-20261021/config.local.json。日常只需运行：

~~~bash
python3 -B team/optimizations/o2/repro/repro.py preflight \
  --config /home/riscv/riscv-lab/o2-r0-repro-20261021/config.local.json \
  --profile observe --output /absolute/new/r0-preflight
~~~

每次输出必须是新的、checkout 外的目录。旧失败和旧证据不能覆盖。

## 2. 需要恢复的输入

| 输入 | 固定来源或检查方法 |
| --- | --- |
| 生产源码与 126 个递归依赖 | 原 O2 hardware-inputs.json 与 dependencies.json；全部内容和提交核对 |
| 正常 NEMU、故障参考库 | T12 的 reference 与 build-evidence；正常库使用 artifact_guard 检查配置、补丁和源码来源 |
| hello/vadd、flash | T12 阶段一构建目录中的原镜像 |
| 功能/异常矩阵 | T12 runs/t11-matrix-canonical；117 唯一用例、124 次分片执行清单 |
| 控制镜像 | T14 runs/control-sweep-02，保留原 build.json 和关联文件 |
| G4 性能镜像 | 四项目统一测试 runs/ours-images-02 的原 16 份镜像（12 performance、3 functional、1 smoke） |
| O2 补充覆盖输入 | G3 diagnostic-build-03、control-diagnostic-build-04 |
| O3 应用输入 | o3-gemv-20261019/images-02，26 份原镜像及源码、数据、构建记录 |
| O1/O2 固定二进制 | R0 工作根的 baseline-binaries；与原 pins 完全相同，放在 checkout 外 |
| O4 参考工具及库 | 原 tools/root、共享库、Nangate45 Liberty；还需原 toolchain-lock.json 中的版本 |
| 封存结果入口 | G3/G4/O3/O4 的封存 manifest；R0 锁定索引，不冒称再次复算所有封存日志 |

已将 O1/O2 原二进制逐字节复制到 checkout 外的只读基线缓存，原 build/emu 保留。缓存只供已验证基准对照；它不进入日常 Git 提交。新机器须从团队保存的材料恢复并核验，或另行构建并保存新的构建身份。源代码检出本身不包含这些历史产物。

工具核验：GraalVM JDK 21.0.12、Mill 0.12.3、Verilator 5.052、Clang 19.1.7、GNU Make 4.3、Python 3.10.12、RISC-V GCC 11.4.0、firtool 1.62.1、Yosys 0.9、ABC 1.01、OpenSTA 2.0.17。Mill 版本从仓库 .mill-version 选择，因此版本探针固定在仓库根目录运行。可执行文件和版本标识均检查，O4 共享库亦锁定。这里没有声称 Maven/下载缓存及整个操作系统已经成为完全离线的封闭构建环境。

## 3. 两种配置与命令准备

~~~bash
python3 -B team/optimizations/o2/repro/repro.py commands \
  --config /path/to/config.json --profile cost \
  --output /absolute/new/r0-cost-commands
~~~

commands 会先完成预检，然后输出 commands.json；它不会执行其中的构建、EMU 或 RTL 生成命令。

| 配置 | FUSED_INPUT | O1_HANDOFF | O2_ELASTIC | O2_TRACE | T13_TRACE | O1_TRACE/T12_TRACE |
| --- | --- | --- | --- | --- | --- | --- |
| observe | 1 | 0 | 1 | 1 | 1 | 0/0 |
| cost | 1 | 0 | 1 | 0 | 0 | 0/0 |

入口会清除继承的 VDOT_* 开关，再显式设置对应配置。配置文件不接受任意 flags 字段；选择 cost 也不能把它用于已有 G3 观察器验收。设置变量不会改变已经编译好的 EMU。

需要后续真正构建时，使用有完整依赖、尚无 build/ 的新 checkout：

~~~bash
python3 -B team/optimizations/o2/repro/repro.py build \
  --config /path/to/config-for-new-checkout.json --profile observe \
  --output /absolute/new/o2-build
~~~

此命令先执行 R0 预检，再调用 build_fullcore.py。配套构建工具新增 --profile 和 --firtool-dir，原默认 observe 行为保留。实际 make 仍为 MinimalConfig、单核、单线程 EMU、-j2、12G JVM。成功后产生新的 hardware-inputs.json，而不是覆盖 B0 身份。

当前 checkout 已有 build/，该构建命令会拒绝执行，不删除或移动原产物。本次 R0 仅实际检验了拒绝覆盖和配置等行为；没有在新 checkout 进行完整构建。完整构建仍由 R4/T17 验收。

cost_rtl 命令使用真实 O4 父级 harness 和已配置的 firtool 路径。后续的映射、STA 继续按 O4 RUNBOOK 和相同参考约束执行；R0 不重新跑 O4。此 build 入口用于 B0 固定版本复现；后续 RTL 候选应建立新的源码/构建身份，不能冒用 B0 预检通过。core_run 使用新的 observe 构建 pins，并显式传入 T12/T14/dense 路径。补充测试与离线 recheck 仍按 fullcore/REPRODUCE.md 执行，涉及旧绝对路径的工具不自动迁移。

## 4. 旧负向参考库的迁移边界

冻结 negative-reference.so 的 ELF 依赖绑定：

~~~
/home/riscv/riscv-lab/t12-regression-20261013/nemu/reference/build/riscv64-nemu-interpreter-so
~~~

文件 SHA 相同也不能让这个编译进二进制的路径自动变化。预检使用 readelf 检查真实依赖，并核对正常库实际路径。

新机器可以恢复该原始位置及相同来源；若要放在其他位置，需要在 R4 单独重建负向库，保存新源码/路径/散列，并对原 frozen-input 合同明确升级，再重做负向注入与正常恢复。R0 没有修改旧库、旧 FROZEN 常量，也没有关闭差分检查。配置入口可移植不表示全部历史二进制已可任意迁移。

## 5. 检查命令与结论

~~~bash
python3 -B -m unittest discover -s team/optimizations/o2/repro -p 'test_*.py' -v
python3 -B -m unittest discover -s team/optimizations/o2/fullcore -p 'test_*.py' -v
~~~

预检成功标识为 O2_R0_PREFLIGHT_PASS。此标识只表示锁定输入、工具、配置和旧输入来源通过本机主机检查；emulators_executed=0，independent_member_reproduction=false。

四类真实命令负控会保留失败回执：错误配置字段/模式混用、缺失输入、错误 B0 镜像身份、已有 build/。它们应返回非零，并由外部验收确认拒绝原因符合预期。

后续入口：先完成 R1 的映射寄存器审查，再决定是否实施低 32 位保存候选；R2 可以由另一位成员独立开展应用分析。正式报告仍在工程冻结后编写。
