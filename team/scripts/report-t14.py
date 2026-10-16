"""Generate T14 result tables after the offline gate, preserving all regressions."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(path):
    return json.loads(path.read_text())


def span(values, suffix=""):
    low, high = min(values), max(values)
    def number(value):
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    return number(low) + ("" if low == high else "–" + number(high)) + suffix


def report(base, offline, output):
    run = base / "runs/fullcore-02"
    state = load(run / "campaign-state.json")
    ab = load(base / "runs/ablation-01/result.json")
    receipt = load(offline / "offline-receipt.json")
    assert state["status"] == "T14_CANDIDATE_FULLCORE_PASS"
    assert ab["status"] == "T14_IDENTICAL_IMAGE_ABLATION_PASS"
    assert receipt["status"] == "T14_OFFLINE_REPLAY_PASS"
    old = load(ROOT / "team/evidence/t13-performance-20261015/support/analysis-v1/result.json")
    new = load(run / "analysis/result.json")
    pins = load(base / "build-evidence/hardware-inputs.json")
    structure = load(base / "runs/structure-01.json")
    tables = [defaultdict(list) for _ in range(3)]
    for table, source in zip(tables, (old["summary"], new["summary"], ab["summary"])):
        for row in source:
            table[(row["scenario"], row["n"])].append(row)
    lines = [
        "# T14：输入拍乘积锁存优化与消融",
        "",
        "2026-10-16。本地自动验收完成；尚未上传 GitHub，B/C 人工复核待完成。默认基础模式仍保留。",
        "",
        "## 实测结果",
        "",
        "独立 FU 最早响应从 3 拍降至 2 拍，无反压最小接受间隔从 4 拍降至 3 拍。全核收益以下表为准，不能用 3/2 或 4/3 代替应用加速比。",
        "",
        "正式 vdot 窗口的中位硬件加速比范围为 " + span(ab["vdot_median_speedup_range"], "×") +
        "。这里比较相同镜像在基础硬件与候选硬件的周期。三次确定性重放不是独立统计样本。",
        "",
        "表中区间覆盖 3 组输入数据，每组先取 4 个正式轮次的中位数。各列分别汇总，不能将区间端点拼成新样本；节省为负表示变慢。",
        "",
        "| 场景 / 数量参数 | 基础 vdot 周期 | 候选 vdot 周期 | 同方法硬件加速比 | RVV 节省周期 | 原 RVV/vdot | 候选 RVV/vdot |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for key in sorted(tables[2]):
        v = [r for r in tables[2][key] if r["method"] == "vdot"]
        rvv = [r for r in tables[2][key] if r["method"] == "rvv"]
        values = [f"{key[0]} / {key[1]}",
                  span([r["baseline_cycles_median"] for r in v]),
                  span([r["candidate_cycles_median"] for r in v]),
                  span([r["hardware_speedup_median"] for r in v], "×"),
                  span([r["cycles_saved_median"] for r in rvv]),
                  span([r["speedup_median"] for r in tables[0][key]], "×"),
                  span([r["speedup_median"] for r in tables[1][key]], "×")]
        lines.append("| " + " | ".join(values) + " |")
    lines += [
        "",
        "single 是单次调用；chain 是 RAW 依赖链；batch 是独立寄存器批量；stream 包含访存；generic 包含通用接口的 CSR 管理。generic 的较大 RVV/vdot 比值不能推广到纯算术或所有应用。",
        "",
        "## 首次、预热与退化样本",
        "",
        "下表只取 replay=0，避免对相同重放重复计数。所有阶段和全部三次重放均保存在 paired-windows.json/csv，未按收益筛选。",
        "",
        "| 方法 | 阶段 | 窗口数 | 变快 | 不变 | 变慢 | 节省周期范围 |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    windows = load(base / "runs/ablation-01/paired-windows.json")
    for method in ("vdot", "rvv"):
        for phase in ("first", "warmup", "measured"):
            vals = [r["cycles_saved"] for r in windows if r["replay"] == 0 and r["method"] == method and r["phase"] == phase]
            if vals:
                lines.append(f"| {method} | {phase} | {len(vals)} | {sum(v>0 for v in vals)} | {sum(v==0 for v in vals)} | {sum(v<0 for v in vals)} | {span(vals)} |")
    lines += [
        "",
        "首次 stream 沿用原合同的 vdot 后 RVV 顺序，共享输入会受前一次执行影响；这不是对称冷缓存实验。没有缓存事件证据，不能把差值全归因于缓存。RVV 指令未改，也可能因前序 vdot、预测器、缓存和排队状态而变化。",
        "",
        "## 唯一硬件变化和代价",
        "",
        "| 边沿 | 基础版 | 候选版 |",
        "|---|---|---|",
        "| E0 | 接受并保存源操作数 | 接受并保存 8 个 int8 乘积 |",
        "| E1 | 保存乘积 | 保存归约结果 |",
        "| E2 | 保存归约结果 | 最早响应 |",
        "| E3 | 最早响应 | 可接受下一请求 |",
        "| E4 | 可接受下一请求 | 后续事务推进 |",
        "",
        "VDOT_T14_FUSED_INPUT=0 或不设置为基础版，=1 为候选版，其他值拒绝构建。开关在 elaboration 阶段选择结构，不生成运行时选择器。ISA、编码、NEMU、算术算法、FuConfig 和单请求协议保持一致。",
        "",
        f"生成 RTL 的 VDot 寄存器声明从 {structure['baseline_declared_register_bits']} 位变成 {structure['candidate_declared_register_bits']} 位，去掉两个 128 位源寄存器声明；8 个乘法算子、7 个加法算子不变。",
        "声明计数包含仿真断言/调试状态，无用高位可能原本就会被综合删除，因此不能视作实际触发器或面积节省。",
        "",
        "乘法移到上游输入至乘积寄存器的路径，可能拉长关键路径。本轮没有综合/STA，不宣称面积、功耗或 Fmax 改善，也不给出工艺面积估计。",
        "如果某负载的周期加速比为 S，实际运行时间加速比还需乘以 F候选/F基础；要获得时间收益，需要 F候选/F基础 > 1/S。",
        "",
        "## 正确性和覆盖闭环",
        "",
        "- 两种 FU 模式分别通过 22 组定向及 10,000 组随机完整 128 位结果，包含身份、反压、非法配置、取消/环绕、复位和随机控制；身份及取消错误注入被拒绝。",
        "- 基础模式生成的整个 FU 只规范化注释、空白及断言诊断行号后与冻结原版相同。算术子模块不变；这不是形式等价证明。",
        "- 候选全核通过 hello/vadd、117 个唯一功能/异常用例（124 次执行）、真实 DiffTest bit100 故障注入及正常参考库恢复。bit100 是人工故障注入，不是发现了真实 RTL 高位错误。",
        "- 原控制镜像在候选版结果正确，但未覆盖写回反压；严格判为不完整。失败记录保存在 historical/，未被覆盖。",
        "- 补充 F2v 广播次数 1..16 扫描；重复写入相同 3.5f，完整 golden 和 vdot 提交数量不变。同一补充镜像在基础与候选两版均通过全部原覆盖条件。",
        "- 其余 10 个已完成 T12 作业按字节与摘要复用，新增控制作业单独运行。t12-reuse-receipt.json 记录来源，不把复用称为再次执行。",
        "- 13 个校准窗口、108 次功能调用、1,404 个性能窗口、48 个相同已编译镜像、126 次执行、3 次重放全部通过。",
        "- 计数器使用完整 64 位整数，逐窗口检查 ELF、退休指令和 fence 边界；不扣空窗，不用宿主耗时替代处理器周期。",
        "- 离线核验重算原始日志、ELF/golden、控制覆盖和配对结果；离线通过不等于重新运行硬件。",
        "",
        "| 扫描版本 | 接受 | 响应 | 取消 | 写回反压周期 | 共享 VFEX4 等待 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for variant in ("baseline", "candidate"):
        counts = load(base / ("runs/control-sweep-" + variant + "-02/control-result.json"))["counts"]
        lines.append("| " + " | ".join([variant] + [str(counts.get(k, 0)) for k in ("ACCEPT", "RESPONSE", "KILL", "STALL", "VFEX4_WAIT")]) + " |")
    lines += [
        "",
        "压力测试的接受/取消次数受投机时序影响，两版整套压力测试总周期不能作为应用加速比。",
        "",
        "## 固定版本和复核入口",
        "",
        "- 开发起点：zjhwork 3b337a5b186ed60163a8d11edaeb3677dfd67750。",
        "- 实际候选硬件构建源码：" + pins["source_commit"] + "。",
        "- 候选 EMU SHA-256：" + pins["emu_sha256"] + "。",
        "- 恢复驱动执行源码：" + state["source"] + "；驱动摘要：" + state["driver_sha256"] + "。",
        "- 工作区：/home/riscv/riscv-lab/t14-optimization-20261015。",
        "- [单一变量合同](../spec/t14-ablation.md) · [建议评估](t14-suggestion-review.md) · [覆盖补齐过程](t14-control-coverage.md)。",
        "- [精简证据](../evidence/t14-optimization-20261016/README.md)：fullcore/analysis 为候选数据，ablation 为比较，hardware-build 为实际构建输入与命令。",
        "",
        "离线核验命令：python3 -B team/scripts/verify-t14-archive.py --archive team/evidence/t14-optimization-20261016 --output /tmp/t14-offline-new。输出目录须是新目录。",
        "硬件复建先加载 team/scripts/activate.sh，使用固定依赖、全新构建输出和证据中的实际命令；不要混用两个开关模式的构建缓存。",
        "",
        "## 团队复核",
        "",
        "A 复核输入路径与时序代价；B 复核相同镜像、公平计时、RVV 对照变化和退化样本；C 复核完整状态、取消/身份、故障注入及覆盖补齐。这些是待办，不代替成员签字。",
        "T15 扩展及响应/新请求同拍握手另立任务，不混入本轮。建议文档中的位宽、RESP 重叠、面积估算等判断已单独评估。",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "offline", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    report(args.base, args.offline, args.output)
