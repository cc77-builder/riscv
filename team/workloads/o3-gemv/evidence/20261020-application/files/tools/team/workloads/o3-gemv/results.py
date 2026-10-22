"""Strict O3 raw evidence recheck and tables; never invokes EMU."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import campaign as c

def csv_file(path,rows):
    if not rows:return
    with path.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def recheck(root,output):
    root=Path(root);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    state=json.loads((root/"state.json").read_text())
    c.require(state["status"]=="O3_PAIRED_APPLICATION_CAMPAIGN_PASS","campaign incomplete")
    files=json.loads((root/"artifact-pins.json").read_text());c.verify_hashes(files)
    for path in (root/"source").rglob("*"):
        if not path.is_file():continue
        name=path.relative_to(root/"source").as_posix()
        expected=files[str(c.ROOT/name)]
        c.require(c.sha(path)==expected,"runtime source snapshot mismatch "+name)
        body=subprocess.check_output(["git","show",state["source_commit"]+":"+name],cwd=c.ROOT)
        c.require(hashlib.sha256(body).hexdigest()==expected,"Git runtime source mismatch "+name)
    gate=c.load("o3_recheck_runtime_gate",c.ROOT/"team/optimizations/o1/audit/runtime_gate.py")
    fatal=c.load("o3_recheck_fatal",c.ROOT/"team/optimizations/o2/fullcore/workloads/check.py")
    observers={m:c.load("o3_recheck_observer_"+m,c.ROOT/("team/optimizations/"+m+"/fullcore/analyze.py")) for m in ("o1","o2")}
    aggregate=json.loads((root/"result.json").read_text());records=[]
    recovery_module=c.load("o3_linux_recovery_check",Path(__file__).with_name("recovery_check.py"))
    paths=sorted([*root.glob("o1/*/result.json"),*root.glob("o2/*/result.json")])
    c.require(len(paths)==56,"strict exact run count")
    recorded={(r["mode"],r["image"],r["replay"]):r for r in aggregate["runs"]}
    c.require(len(recorded)==56,"aggregate duplicate run")
    for path in paths:
        directory=path.parent;r=json.loads(path.read_text())
        c.require(r["status"]=="O3_IMAGE_DIFFTEST_STATE_WINDOWS_AND_PROTOCOL_PASS" and r["exit_code"]==0,"failed run "+str(path))
        c.require((directory/"exit-code.txt").read_text()=="0\n","exit code receipt")
        runtime=json.loads((directory/"runtime.json").read_text())
        for key in ("mode","image","suite","shard","dataset","build","replay","command","cwd","started_utc","files"):
            c.require(runtime[key]==r[key],"runtime identity changed "+key)
        c.require(r==recorded[(r["mode"],r["image"],r["replay"])],"aggregate/disk run disagreement")
        build=Path(r["build"]);manifest=json.loads((build/"data/manifest.json").read_text())
        stdout=(directory/"stdout.log").read_text();stderr=(directory/"stderr.log").read_text()
        for text in (stdout,stderr):fatal.reject_fatal_output(text);gate.validate_failure_markers(text)
        c.g4.validate_loaded_reference(stderr+stdout,c.g4.REFERENCE,gate.normalize_console)
        windows=c.check.verify(build,directory)
        analysis=observers[r["mode"]].analyze(stderr+stdout)
        c.g4.observer_gate(r["mode"],analysis,c.g4.expected_commits(manifest))
        c.require(windows==json.loads((directory/"windows.json").read_text()),"saved window mismatch")
        c.require(analysis==json.loads((directory/"observation.json").read_text()),"saved protocol mismatch")
        samples=[]
        for sample,entry in zip(windows["samples"],manifest["plan"]):
            row=manifest["rows"][entry["index"]]
            samples.append(dict(sample,mode=r["mode"],shard=r["shard"],software=row["software"],m=row["m"],k=row["k"],
                                scope=row["scope"],image_sha256=c.sha(build/"vdot-perf.bin")))
        c.require(samples==r["samples"],"saved sample mismatch")
        records.append(r)
    for mode in ("o1","o2"):
        rows=[r for r in records if r["mode"]==mode and r["image"]=="performance-d0-s05"]
        c.require(len(rows)==3 and {r["replay"] for r in rows}=={0,1,2},"replay inventory")
        baseline=next(r for r in rows if r["replay"]==0)
        for r in rows:
            c.require([(s["seq"],s["cycles"],s["instructions"]) for s in r["samples"]]==[(s["seq"],s["cycles"],s["instructions"]) for s in baseline["samples"]],"replay drift")
    recovery=recovery_module.validate(root.parent,root,records,str(root.parent))
    stats=c.summarize(records)
    ordering=c.load("o3_exact_measured_identity",Path(__file__).with_name("evidence_order.py"))
    for key,value in stats.items():
        if key=="measured_samples":
            ordering.require_same_measured(value,aggregate[key])
        else:
            c.require(value==aggregate[key],"aggregate statistics drift "+key)
    c.verify_hashes(files)
    samples=[]
    for r in records:
        for s in r["samples"]:
            samples.append({k:v for k,v in dict(s,suite=r["suite"],replay=r["replay"],image=r["image"]).items() if k not in ("counter_values","sample_ticks")})
    csv_file(output/"samples.csv",samples)
    rows=[]
    for row in stats["rows"]:
        v={key:row[key] for key in ("m","k","scope","software","o2_vdot_cycle_reduction","o2_rvv_cycle_reduction")}
        for mode in ("o1","o2"):
            for method in ("vdot","rvv"):
                for key,value in row[mode][method].items():v[mode+"_"+method+"_"+key]=value
            v[mode+"_rvv_over_vdot"]=row[mode]["rvv_over_vdot"]
        rows.append(v)
    csv_file(output/"comparison.csv",rows);csv_file(output/"best-rvv.csv",stats["best_rvv_comparison"])
    table=["# O3 GEMV工程结果","",
           ("中断恢复：46项原通过作业逐字节复用，10项恢复补跑；另2项中断尝试完整保留、不计入正式统计。共56项合格作业、58次启动尝试。" if recovery["recovered"] else "无中断恢复。"),"",
           "O1/O2相同镜像、相同数学输入输出。全部56项实际EMU运行、1280个校验窗口、768条正式性能窗口通过严格原始日志重审；4项重放逐seq一致。",
           "正式样本每shape/scope/software/mode/method为3数据集×4measured。first/warmup/重放均保留，不作为额外独立样本。","",
           "|M×K|口径|软件|O1 vdot cycles|O2 vdot cycles|O2周期降低|O1 RVV cycles|O2 RVV cycles|O2 RVV/vdot|",
           "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for v in rows:
        table.append(f'|{v["m"]}×{v["k"]}|{v["scope"]}|{v["software"]}|{v["o1_vdot_mean_cycles"]:.2f}|{v["o2_vdot_mean_cycles"]:.2f}|{100*v["o2_vdot_cycle_reduction"]:.2f}%|{v["o1_rvv_mean_cycles"]:.2f}|{v["o2_rvv_mean_cycles"]:.2f}|{v["o2_rvv_over_vdot"]:.3f}×|')
    table += ["","## 更快RVV对照","",
              "同一硬件/尺寸/口径内，从basic/reuse两版各自选择周期和更小者，显示vdot与较快RVV的比较，不以较慢RVV放大收益。",
              "|M×K|口径|硬件|vdot软件|较快RVV软件|RVV/vdot|","|---|---|---|---|---|---:|"]
    for row in stats["best_rvv_comparison"]:
        table.append(f'|{row["m"]}×{row["k"]}|{row["scope"]}|{row["mode"]}|{row["vdot_software"]}|{row["rvv_software"]}|{row["rvv_over_vdot"]:.3f}×|')
    table+=["","core包含A/x加载、运算、跨块累加及结果寄存器形成；endtoend再计入kernel配置及全部输出存储。输入无打包；VS启用和测试框架初始化在窗外。输出为每行16字节槽，不能冒称最优GEMV库或完整LLM端到端。",
            "K=13的vdot标量尾部成本计入，RVV可用动态VL。所有有利/不利预定尺寸均展示；本轮不推断PPA/Fmax、官方得分或最终采用。O4/O5/G5和正式T16仍待后续。"]
    (output/"结果与工程记录.md").write_text("\n".join(table)+"\n",encoding="utf-8")
    v=dict(status="O3_RAW_EVIDENCE_RECHECK_PASS",source_commit=state["source_commit"],recovery=recovery,jobs=56,windows=len(samples),
           measured_windows=len(stats["measured_samples"]),replay_jobs=4,original_inputs_unchanged=True,new_emu_run=False,
           rows=stats["rows"],best_rvv_comparison=stats["best_rvv_comparison"])
    c.require(v["windows"]==1280,"window inventory")
    c.save(output/"verification.json",v)
    print(json.dumps({k:v[k] for k in ("status","jobs","windows","measured_windows","replay_jobs")}),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--campaign",required=True,type=Path);p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();recheck(a.campaign,a.output)
