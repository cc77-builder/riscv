from pathlib import Path
import json,statistics
w=Path("/home/riscv/riscv-lab/o2-performance-20261019/campaign-01")
data={}
for p in w.glob("*/performance/*/result.json"):
    r=json.loads(p.read_text())
    if r["status"]!="PAIRED_IMAGE_DIFFTEST_AND_WINDOWS_PASS":continue
    data[(r["mode"],r["image"])]=[s for s in r["samples"] if s["phase"]=="measured" and r["replay"]==0]
out=[]
for image in sorted({k[1] for k in data}):
    if not all((m,image) in data for m in ("o1","o2")):continue
    modes={m:{method:statistics.mean(x["cycles"] for x in data[(m,image)] if x["method"]==method) for method in ("vdot","rvv")} for m in ("o1","o2")}
    out.append(dict(image=image,scope="one completed dataset,4/12 planned measured samples per method; provisional",
                    reduction=1-modes["o2"]["vdot"]/modes["o1"]["vdot"],**modes))
print(json.dumps(out))
