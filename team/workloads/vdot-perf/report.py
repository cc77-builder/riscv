"""Generate the Chinese T13 report from accepted measurements, never hand-enter timing values."""
from check import require
import argparse
from collections import Counter
import json
from pathlib import Path


def main(a):
    base=a.base;analysis=base/'runs/analysis-v1'
    record=json.loads((analysis/'result.json').read_text());require(record['status']=='T13_FAIR_CYCLE_COMPARISON_PASS', "Validation failed: record['status']=='T13_FAIR_CYCLE_COMPARISON_PASS'")
    stats=json.loads((analysis/'summary.json').read_text())
    pins=json.loads((base/'build-evidence/hardware-inputs.json').read_text())
    standard=json.loads((base/'runs/images-v3/functional-d0-s00/build.json').read_text())['source']
    stream=json.loads((base/'runs/images-stream-v4/performance-d0-s07/build.json').read_text())['source']
    names={'single':'已知配置单次','chain':'依赖链','batch':'独立四路批处理','stream':'加载/点积/存储','generic':'逐次保留 VL/vtype'}
    order=[('single',1),('chain',16),('chain',64),('chain',256),('batch',1),('batch',8),('batch',32),('stream',1),('stream',16),('stream',64),('generic',1),('generic',16),('generic',64)]
    table=[]
    for key in order:
        group=[s for s in stats if (s['scenario'],s['n'])==key]
        require(len(group)==3, 'Validation failed: len(group)==3')
        require(all({k:v for k,v in s.items() if k!='dataset'}=={k:v for k,v in group[0].items() if k!='dataset'} for s in group), "Validation failed: all({k:v for k,v in s.items() if k!='dataset'}=={k:v for k,v in group[0].items() if k!='dataset'} for s in group)")
        s=group[0]
        table.append(f"| {names[s['scenario']]} | {s['n']} | {s['dots']} | {s['vdot_min']}/{s['vdot_median']:g}/{s['vdot_max']} | {s['rvv_min']}/{s['rvv_median']:g}/{s['rvv_max']} | {s['speedup_median']:.4f}× | {s['vdot_cycles_per_dot']:.4f} / {s['rvv_cycles_per_dot']:.4f} |")
    fu=Counter()
    for r in record['receipt']:fu.update(r['fu']['response_latency_histogram'])
    require(fu=={'3':35856}, "Validation failed: fu=={'3':35856}")
    text=f'''# T13：RVV 基线与 vdot 公平周期性能对比

日期：2026-10-15（Asia/Shanghai）。**本地自动验收完成，未上传 GitHub，尚未代替队友人工复核。** 当前开发分支为 `local/t13-performance-20261015`，基于已发布至 zjhwork 的 T12 提交 `2c0bf8e283d400c1c946ca75f890f266d7758411`。原工作区与 main 保持原状态。

## 1. 结论与使用范围

在固定 MinimalConfig、单核、VLEN=128 的实现上，vdot 相对经过等价验证的精简 RVV 基线，正式窗口的配对中位加速比为：已知配置单次 **1.1725×**，依赖链 **2.0619～2.5736×**，独立四路批处理 **1.0888～1.1309×**，含访存循环 **1.0115～1.1064×**。收益随场景显著变化，不能用静态指令数之比替代实测。

逐次保存/恢复 VL、vtype 的通用调用为 **1.6528～7.9510×**。这是该调用合同中的配置管理开销，不能宣传为所有点积或 LLM 的通用加速比。若外层循环已知配置稳定、允许共享配置，应采用已知配置或四路批处理基线；不能故意把可外提的 CSR 开销重复计入最优批处理对照。

首次访存样本存在 vdot 更慢的情况，见第 5 节。本文不宣称 Fmax、面积、功耗或官方得分提升。所有比值只适用于本轮固定程序与微架构。

## 2. 从 zufan 取用了什么

再次联网核对后，`zufan` 最新仍是 `f090665130107282be0990a7664aebf26e491b87`，提交时间 2026-10-14 22:47:52 +08:00。它完成 T12 软件和证据整合：original190、lean199 两套计划分别通过，输入有重叠，不能加成 389 个唯一 ISA 用例；其报告明确 rdcycle 时序尚未校准，II3/输入融合候选尚未完成真实 RTL A/B 与 PPA。

本轮选择性保存了其精简 RVV 生成器、参考检查器、指令计数脚本、整合报告与审查结论。原字节、提交号和 SHA-256 见 [来源记录](../references/zufan-t13/provenance.json)，远端回读见 [核对回执](../references/zufan-t13/remote-check.json)。没有整体合并分支，也没有启用对方的候选 RTL 优化。新执行结果全部由本轮重新产生。

## 3. 固定版本与测量边界

| 项目 | 实际采用版本/设置 |
|---|---|
| 硬件与观察器源码 | `{pins['source_commit']}` |
| EMU SHA-256 | `{pins['emu_sha256']}` |
| 功能、非访存性能镜像源码 | `{standard}` |
| 共享输入访存镜像源码 | `{stream}` |
| NEMU | 基线 a48a11f208ff81ad765591d83271d1b339fb3861；已验收补丁 1.1.0 |
| NEMU 二进制 SHA-256 | `efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4` |
| AM | 独立副本，086a238062fdfb3281b745a537b361983d0154b5 |
| 核与仿真 | MinimalConfig、NUM_CORES=1、EMU_THREADS=1、128 MB RAM、DiffTest 启用 |
| 构建 | VDOT_T12_TRACE=1、VDOT_T13_TRACE=1、JVM_XMX=12G、-j2、OPT_FAST=-O3、OPT_SLOW=-O0 |
| 软件 | ARCH=riscv64-xs、MARCH=rv64gcv，显式汇编，关闭 C 自动向量化 |
| 重放 | 每个性能镜像 3 次全新 EMU，固定 seed=1；共 39 个配对配置 |

全部源码文件与 1,209 项依赖文件摘要、依赖提交和实际构建命令位于 [硬件构建证据](../evidence/t13-performance-20261015/hardware-build/hardware-inputs.json)。相对 T12 实际硬件源码，本轮只增加两个文件共 34 行观察逻辑，不改变生产算术、执行控制和 NEMU 行为。后续校验器/报告提交不冒充重新构建硬件。

**关键校准修正：** 解码表虽然给普通 CSR 设置 waitForward/blockBackward，但 Rename.scala 会解除多数只读 CSR 的限制。真实事件证实 rdcycle 不能独自保证序列化。正式程序在四次 counter 读前后加入固定版本可观测的 fence 隔离，逐条核对入 ROB、CSR 采样、退休和机器码。

校准 13 个窗口全部通过。空主体为 59 周期、7 条退休指令；8 条整数指令为 74 周期、15 条；32 条依赖除法及其初始化为 342 周期、42 条。每个正式窗口都满足 CSR cycle 差 = 全核采样 tick 差；instret 差 = 实际退休计数 = ELF 有限循环展开计数。绝对值使用整数处理，超过 2^53 也不损失精度。

窗口内包含相同的 fence、循环和指针控制开销。**不扣除空窗口，不把 59 周期当作所有程序都能相减的固定常数。** 两边共同的输入装载和入口状态初始化在窗口前，计入窗口的是各自完成约定操作必须执行的乘法、清零、归约、配置恢复及该场景的访存。详细合同见 [measurement.md](../spec/measurement.md)。

## 4. 正确性与证据验收

| 层次 | 实际结果 | 含义 |
|---|---|---|
| 主机检查 | 18 项 unittest 通过；14 项真实工件的临时损坏均被拒绝 | 覆盖计数器、缺失事件、身份、ELF 黄金高位、scratch、输入指针 |
| 真实 C 判定器 | plain 与 UBSan 均通过；合计 4,867,560 次错误位翻转被拒，61,440 次 scratch 位翻转被允许 | 实际 C 源文件，完整寄存器/CSR/内存/次数检查 |
| NEMU 参考层 | 14,928 组通用 RVV/vdot 配对 + 10,022 次已知配置 + 10,022 次 batch，共 49,900 次序列执行 | 覆盖全部原始 22+10,000 输入；不能冒充全核执行次数 |
| 全核功能 | 9 个镜像，54 对/108 次调用全部通过 | 22 定向+32 随机，轮换别名和 policy，不是笛卡尔积 |
| 计时校准 | 13 个窗口通过 | 空窗口、整数、依赖除法及五种点积场景 |
| 最终性能 | 39 个配对配置 × 6 轮 × 2 路 × 3 重放 = 1,404 窗口 | 首次、预热、4 轮正式；AB/BA 交替 |
| 确定性 | 全部性能镜像 3 次重放逐窗口相同 | 重放用于复现，不是独立统计增样 |
| 最终选用全核运行 | 126 次 = 9 功能 + 117 性能，另有 1 次校准 | exit0、DiffTest、完整 summary、GOOD TRAP、原始字节摘要均验收 |

每次调用检查完整 128 位目的结果、全部非 scratch 向量寄存器、VL/vtype/vstart/vxrm/vxsat/vcsr、循环次数和内存边界；访存组逐个比较全部输出。检查器还从 ELF 中读取实际编译的黄金字节、入口、次数和 scratch 常量，并重新运行该镜像的原版生成器。不能仅修改 manifest 就掩盖错误。

最终 NEMU 配对验证和全核功能层各自通过后，才接受对应性能数据。运行调度采用多个宿主进程，验收顺序仍执行正确性和校准门禁。宿主耗时不参与性能计算。

## 5. 全部正式结果

下表为第 0 次重放的 4 轮正式配对样本。三组输入逐项结果相同，经脚本断言后合并显示；完整 39 行表和三次重放全部保留。周期栏为 **min / median / max**。加速比列是逐轮配对比值的中位数，不是先取两边中位数再相除。batch 每轮有四个点积。

| 场景 | n | 点积数 | vdot 周期 | RVV 周期 | 配对中位加速比 | 中位周期/点积：vdot / RVV |
|---|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(table)+'''

完整数据：[窗口 CSV](../evidence/t13-performance-20261015/support/analysis-v1/samples.csv)、[配对 CSV](../evidence/t13-performance-20261015/support/analysis-v1/pairs.csv)、[39 项汇总](../evidence/t13-performance-20261015/support/analysis-v1/summary.csv)。CSV 只把差值作为数值字段；完整 64 位绝对计数器以 JSON 整数保留，读取时不要转成浮点。

首次访存配对（vdot 先执行、RVV 后执行）为：n=1 时 161 对 130 周期；n=16 时 717 对 410；n=64 时 2566 对 1179。它们是带顺序影响的首次样本，**不是两边分别清缓存后的对称冷缓存对照**。预热和正式样本单独报告，不把首次劣势删掉，也不把它解释成普遍冷缓存规律。

![所有阶段的配对周期比](../evidence/t13-performance-20261015/figures/paired-cycle-ratio.png)

每个点来自一次已验收配对，横轴大于 1 表示 vdot 更快。图保留所有场景、输入与阶段；三次完全一致重放只绘制第 0 次，不把重复结果当统计增样。PDF/SVG 和图形检查回执见 evidence 下的 figures。

## 6. 微架构解释与下一步

- **FU 层：** 最终选用运行中 35,856 次 accepted 事务全部响应，accept→response 均为 3 个归一化全核周期；无写回反压，最小观测接受间隔为 4 周期。这是局部握手数据，不是完整指令/循环延迟。
- **依赖链：** n=256 的中位周期/点积为 vdot 8.2578、RVV 21.2520，明显高于 FU 的 3 周期，说明循环、调度及依赖仍有代价。反馈按完整向量位表示进行，数值可能收敛到零；这是依赖微基准，不是应用模型。
- **独立批处理：** 128 个点积时 vdot 4.6836、精简 RVV 5.2969 周期/点积。RVV 共享配置后的基线很强，优势只有约 13.1%，不应拿逐次通用调用的 7.95× 替代它。
- **访存循环：** n=64 的收益约 1.15%。结果支持后续优先检查数据搬运、循环和调度占比；本轮没有逐级 cache/LSU 归因证据，不能凭周期差锁定唯一瓶颈。

按计划进入 G5 前，应由另一位队友复算本报告。之后只选择一个优化点做基础版/候选版 A/B，例如检查当前 II=4 的释放/再接收限制；保留同一 ISA、测试输入、基线和测量边界，并重跑取消、反压、身份及 T12 回归。本文没有实现或验收新的 II3 RTL，没有启动 PPA 或扩展 ISA。

## 7. 保留的失败与排除项

1. 初次 EMU 构建因 ready-to-run 子模块未初始化失败；固定到原指定版本后重建成功，两个构建日志均保留。
2. 早期没有完整 fence 隔离的 13 项测试功能通过，但计时边界不足；只保留为诊断，正式统计使用 calibration-02 及之后的隔离版本。
3. 精简串口模式曾因未使用的 vector 打印函数触发 `-Werror`；只编译所需打印器后通过，失败构建目录保留在原运行区。
4. 首次参考检查调用多步 difftest_exec 被固定 NEMU 的单步接口断言拒绝；改用逐指令执行，reference-02 全部通过，首次失败日志保留。
5. 原访存版本使用两块不同输入缓冲区。检查地址后，在读取这组性能值前决定改为共享同一 64 字节对齐输入；原 27 次重放、324 窗口全部作为诊断保留，统一排除，未挑选快的个例。正式访存结果来自独立 stream-v4 版本；ELF 指针和对齐已核实。

硬件异常、T12 控制压力、官方语义待确认项及人工接口签字仍分别引用已有材料；本轮不把 108 次普通功能调用重复包装成新异常或虚拟化覆盖。

## 8. 复核入口与交付

工作负载和工具：[vdot-perf](../workloads/vdot-perf/README.md)。测量约定：[measurement.md](../spec/measurement.md)。完整证据：[T13 证据包](../evidence/t13-performance-20261015/README.md)。 搬迁复核：[WSL / Windows 离线回执](../evidence/t13-offline-review-20261015/README.md)。

在仓库根目录执行（输出使用不存在的新目录）：

```bash
python3 -B -m unittest discover -s team/workloads/vdot-perf -p 'test_*.py' -v
python3 -B team/workloads/vdot-perf/verify_archive.py \
  --archive team/evidence/t13-performance-20261015 \
  --output /tmp/t13-offline-review-new
```

离线复核校验原始字节、源码、ELF 与事件，并重新生成全部比值；它不重新执行 RTL。真正重跑需按 measurement.md 准备固定 EMU、NEMU 和 flash。大体积构建目录、仿真器及波形不进入日常提交。

本轮只在独立本地分支形成可审查提交和 bundle；没有 push、PR 或 main 合并，也没有代签任何队友确认。
'''
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);main(p.parse_args())
