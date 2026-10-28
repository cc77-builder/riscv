from pathlib import Path
import json,shutil
root=Path(__file__).resolve().parent
fin=root/"final";record=json.loads((fin/"record.json").read_text())
p=fin/"RESULT.md";raw=p.read_text()
assert not (fin/"RESULT.raw.md").exists()
shutil.copyfile(p,fin/"RESULT.raw.md")
lines=["## 逐数据集","",
"下表只列逐组的局部指标判定；最终采用还受完整控制窗口与重放门禁约束，以上表总体判定为准。","",
"| 尺寸 | 数据集 | firstdot cycles | 配置复用 cycles | 最快RVV cycles | RVV/vdot | 局部指标判定 |",
"| --- | --- | ---: | ---: | ---: | ---: | --- |"]
for shape,d in record["performance"].items():
 for dataset,v in d["dataset_decisions"].items():
  f,c,r=[v[x]/4 for x in ["firstdot_total","candidate_total","fastest_current_rvv_total"]]
  lines.append(f"| {shape} | {dataset} | {f:.4f} | {c:.4f} | {r:.4f} | {r/c:.6f}x | {v['decision']} |")
lines+=["","## 控制差异与采用判断","",
"- **8×32：保留性能候选。** 三组数据均为282.25→273 cycles，较firstdot少3.2772%，相对本轮最快RVV为1.095238×；控制窗口、同版本重放均一致。",
"- **4×8：保留收益信号，暂待归因。** 主项157.75→153 cycles；未改动basic RVV的正式均值仍为225.25，但部分首轮/正式窗口有±1周期变化。总体判定为INCONCLUSIVE，不能以平均相同替代逐窗门禁。",
"- **16×64：暂待归因。** 主项707→702.75 cycles，仅少0.6011%；未改动basic RVV的均值990→991，六窗记录也变化。总体判定为INCONCLUSIVE。",
"- **4×13：本轮不采用该候选，保留较优RVV。** 主项204.5→205.5 cycles，慢0.4890%，且慢于最快RVV的187 cycles；basic vdot与reuse RVV也有配对退化、未改RVV窗口存在差异。合同总体标记为INCONCLUSIVE，完整原因列表保存在record.json。",
"",
"这些差异出现在已通过功能和NEMU差分的运行中。12个firstdot同BIN对照的288个完整样本与干净基线一致，8次同版本独立重放也一致；跨软件变体的控制周期变化因此仍需单独归因。本轮不修改门禁、不补跑到出现更好的结果，也不把静态少指令直接等同于性能收益。",""]
start=raw.index("## 逐数据集")
end=raw.index("## 验证与留档",start)
p.write_text(raw[:start]+"\n".join(lines)+"\n"+raw[end:])
print("RESULT_PRESENTATION_V2_WRITTEN")
