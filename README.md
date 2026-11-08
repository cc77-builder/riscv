# 香山昆明湖 V2 自定义向量点积指令 vdot

2026 CIE RISC-V 应用赛道 · 面向边缘 AI 大语言模型推理的 RISC-V 自定义 vdot 指令设计

参赛队伍：**啊对对对对**

本仓库在香山昆明湖 V2（MinimalConfig，VLEN=128）中加入自定义指令 `vdot.vv`：对两个向量寄存器的低 8 个 signed int8 元素求点积，32 位结果写入目的寄存器低位，高 96 位清零。仓库同时包含 NEMU 参考模型扩展、DiffTest 协同验证、等价 RVV 基线，以及 firstdot V2 和 C8 两套软件库。

## 评审导航

### 提交材料

| 材料 | 位置 |
| --- | --- |
| 三阶段技术文档 | [提交/技术文档/](提交/技术文档/)：[第一阶段](提交/技术文档/第一阶段_执行日志与过程文档.pdf)、[第二阶段](提交/技术文档/第二阶段_设计与基础测试文档.pdf)、[第三阶段](提交/技术文档/第三阶段_协同仿真与性能分析.pdf) |
| 演示视频 | [提交/项目演示视频/](提交/项目演示视频/)：阶段一环境部署与向量加法、阶段二解题思路、阶段三波形仿真与性能分析（Git LFS，克隆后 `git lfs pull`） |
| 证明材料 | [submission/logs/](submission/logs/README.md)：全部原始运行日志（含失败记录）、命令、配置与版本；[submission/VALIDATION.md](submission/VALIDATION.md)：本分支上执行的检查与结果 |
| 复现操作步骤 | [提交/复现操作步骤.pdf](提交/复现操作步骤.pdf)（[Markdown 版](提交/复现操作步骤.md)） |

### 赛题要求与对应位置

| 赛题要求 | 报告章节 | 代码与记录 |
| --- | --- | --- |
| 1.1 环境部署验证 | 第一阶段 1.1～1.2 | 依赖与环境脚本 [prepare-dependencies.sh](team/scripts/prepare-dependencies.sh)、[activate.sh](team/scripts/activate.sh)、[check-environment.sh](team/scripts/check-environment.sh)；版本锁 [versions.env](team/versions.env)；[环境说明](submission/docs/ENVIRONMENT.md) |
| 1.2 操作日志 | 第一阶段 1.4、1.7 | [submission/logs/stage1/](submission/logs/stage1/)：工具版本、hello/vadd 运行摘要、验收记录 |
| 1.3 向量加法执行过程 | 第一阶段 1.4～1.5 | 程序 [hello-vadd/](team/workloads/hello-vadd/)；提交事件 [vadd-commit-events.csv](submission/logs/stage1/vadd-commit-events.csv)；运行脚本 [stage1.sh](team/scripts/stage1.sh) |
| 2.1 指令设计 | 第二阶段 2.1～2.2 | 指令规格 [team/spec/vdot.md](team/spec/vdot.md) |
| 2.2 RTL 实现 | 第二阶段 2.3～2.4 | 见下方“vdot 源码” |
| 2.3 正数、负数、边界测试 | 第二阶段 2.5 | 参考模型与数据 [team/models/vdot/](team/models/vdot/)；单元测试顶层 [team/rtl/vdot/](team/rtl/vdot/)；整核测试程序 [vdot-exceptions/](team/workloads/vdot-exceptions/)；入口 [vdot-tests.sh](team/scripts/vdot-tests.sh) |
| 3 NEMU 扩展 | 第三阶段 3.2 | 补丁 [team/patches/nemu/](team/patches/nemu/)；构建脚本 [prepare-nemu-vdot.sh](team/scripts/prepare-nemu-vdot.sh) |
| 3 协同仿真与波形 | 第三阶段 3.3～3.4 | DiffTest 运行 `vdot-tests.sh run-rtl`；波形截图 [S3-WAVE-01～03](submission/reports/figures/) |
| 3 性能分析 | 第三阶段 3.5～3.8 | 微基准 [vdot-perf/](team/workloads/vdot-perf/)；RVV 基线 [rvv-baseline/](team/workloads/rvv-baseline/)；GEMV 与软件库见下方 |
| 3 面积与时序 | 第三阶段 3.9 | 综合与 STA 原始报告 [submission/reports/evidence/](submission/reports/evidence/) |

### vdot 源码

| 内容 | 文件 |
| --- | --- |
| 乘积与归约模块 | [VDotDatapath.scala](src/main/scala/xiangshan/backend/fu/vector/VDotDatapath.scala) |
| 最终两槽弹性 FU | [VDotElastic.scala](src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala) |
| 基础单槽 FU | [VDot.scala](src/main/scala/xiangshan/backend/fu/wrapper/VDot.scala) |
| 配置开关 | [VDotO2.scala](src/main/scala/xiangshan/backend/fu/wrapper/VDotO2.scala)、[VDotHandoff.scala](src/main/scala/xiangshan/backend/fu/wrapper/VDotHandoff.scala) |
| FU 注册与选择 | [FuConfig.scala](src/main/scala/xiangshan/backend/fu/FuConfig.scala)、[FuType.scala](src/main/scala/xiangshan/backend/fu/FuType.scala) |
| 译码与异常 | [Instructions.scala](src/main/scala/xiangshan/backend/decode/Instructions.scala)、[DecodeUnit.scala](src/main/scala/xiangshan/backend/decode/DecodeUnit.scala)、[VecDecoder.scala](src/main/scala/xiangshan/backend/decode/VecDecoder.scala)、[VecExceptionGen.scala](src/main/scala/xiangshan/backend/decode/VecExceptionGen.scala) |
| VFEX4 父级与 DIV 取消关钟 | [ExeUnit.scala](src/main/scala/xiangshan/backend/exu/ExeUnit.scala) |
| 最终 FU / 父级测试顶层 | [team/optimizations/o2/fu/](team/optimizations/o2/fu/)、[team/optimizations/o2/parent/](team/optimizations/o2/parent/) |
| firstdot V2 库 | [team/optimizations/o2/r2-select/public/firstdot/](team/optimizations/o2/r2-select/public/firstdot/) |
| C8 GEMV 库 | [package/c8/public/](team/optimizations/o2/integration/firstdot-v2-0f/package/c8/public/)、汇编与数据接口 [config-reuse-c8-v2/public/](team/optimizations/o2/integration/firstdot-v2-0f/continuation/config-reuse-c8-v2/public/) |

### 目录结构

```text
README.md                本页
提交/                    比赛提交材料：技术文档、演示视频、复现操作步骤
src/                     香山源码，含 vdot 数据通路、FU、译码与执行单元接入
team/
  spec/                  vdot 指令规格
  models/                Python 参考模型与确定性测试数据
  rtl/                   数据通路、译码、FU 单元测试顶层
  patches/nemu/          NEMU vdot 扩展补丁
  workloads/             hello/vadd、vdot 整核测试、微基准、RVV 基线、GEMV
  optimizations/         最终两槽 FU/父级测试、EMU 构建器、firstdot 与 C8 软件库
  scripts/               环境、构建、测试与运行脚本
  tests/                 宿主检查器
submission/
  reports/               报告 LaTeX 源码、图片、证据与 PDF（含合订本）
  logs/                  原始运行日志归档、索引与读取工具
  REPRODUCE.md           复现命令速查；reproduce.sh 为统一入口
  VALIDATION.md          本分支上执行的检查
  FINAL_VERSION.json     最终代码与配置身份
  MANIFEST.json          交付文件哈希清单，verify.py 校验
build.sc、Makefile        香山原构建入口；子模块固定在 .gitmodules
```

## 设计要点

- **指令**：custom-0 编码，`MATCH=0x0200000b`、`MASK=0xfe00707f`；固定 SEW=8、LMUL=1、VL=8、vstart=0，非法配置走异常路径。
- **两槽弹性 FU**：乘法与归约分两拍，两个结果槽交替使用，连续独立点积每拍发起一笔，最早 2 拍响应；支持背压和按 ROB 身份精确取消。
- **结果保存**：利用高 96 位恒为零，结果寄存器只存 32 位，写回时补零为 128 位。
- **与 DIV/SQRT 共用执行单元**：DIV 请求被取消后不再保持时钟，VFEX4 可以完全关钟，测量周期不变。
- **协同验证**：NEMU 独立实现同一语义，与 RTL 在提交边界比较完整 128 位结果和 CSR。
- **软件**：firstdot V2 用首段点积初始化累加；C8 为 8×32 GEMV 复用向量配置，提供普通 C 接口。

## 主要结果

数据均来自技术文档，受测硬件为提交 `0f12df6753`（与本分支 `src/` 相同）。

| 指标 | 数值 | 测量范围 | 报告出处 |
| --- | --- | --- | --- |
| 基础测试 | 正数 204、负数 −8、边界 131072，完整 128 位结果均正确 | 赛题 2.3.1～2.3.3 定向用例 | 第二阶段 |
| 算术 RTL | 10022 组输入全部通过 | 乘积与归约模块，定向＋随机 | 第二阶段 |
| 独立批量加速比 | 3.0679×（221 vs 678 周期） | 32 轮四路点积，对比等价 RVV | 表 3-3 |
| 依赖链加速比 | 2.9297×（1857 vs 5440.5 周期） | 256 次串行点积 | 表 3-3 |
| 单次点积加速比 | 1.2007×（71 vs 85.25 周期） | 单条点积完整窗口 | 表 3-3 |
| 加载-计算-存储流 | 1.0049×（1127.5 vs 1133 周期） | 64 次，含访存与循环 | 表 3-3 |
| C8 GEMV 调用 | 273 周期，比较快的 RVV 实现快 1.095× | 8×32 INT8 GEMV 完整函数调用 | 表 3-4 |
| 独立 FU 面积 | 17112.578 µm² | Nangate45，4 ns 综合 | 表 3-9 |
| VFEX4 父级面积 | 284562.278 µm² | 含 VDot、DIV、FDIV/SQRT | 表 3-9 |
| 时序 | FU 最差裕量 +2.601 ns，父级 +0.422 ns，全部路径满足 | 4 ns／5 fF 布局前 STA | 表 3-9 |

每个场景、每种实现取三个数据集、各四个正式窗口；加速比为同场景 RVV 平均周期除以 VDot 平均周期。另外实现并验收了一拍运算方案 SP1（依赖链加速比 3.40×，FU 面积 +6.1%），综合权衡后保留两拍方案，对比见第三阶段 3.9.1 节。

## 快速开始

```bash
git clone --recurse-submodules -b release/cie2026-v1 https://github.com/cc77-builder/riscv.git
cd riscv
python3 -B submission/verify.py          # 交付文件、源码树与子模块校验
bash submission/reproduce.sh check       # 参考模型、编码与静态接入
bash submission/reproduce.sh logs-check  # 原始日志归档校验
```

完整的环境准备、阶段一至阶段三运行步骤见[复现操作步骤](提交/复现操作步骤.pdf)。

上游香山源码、子模块和许可证沿用原工程，见 [LICENSE](LICENSE)、[.gitmodules](.gitmodules)。
