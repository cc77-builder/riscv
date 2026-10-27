import datetime,hashlib,json,subprocess
from pathlib import Path
w=Path("/home/riscv/riscv-lab/o2-c3-hf-20261025")
r=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
m=r/"team/optimizations/o2/r3-div-gate/c3-hf"
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(4194304),b""):h.update(b)
 return h.hexdigest()
run=lambda cmd:subprocess.run(cmd,capture_output=True,text=True,check=True).stdout
final=read(w/"final-record.json")
cost=final["cost"]; ok=cost["status"]=="C3_HF_SCREEN_PASS"
head=run(["git","-C",str(r),"rev-parse","HEAD"]).strip()
exe=sha(r/"src/main/scala/xiangshan/backend/exu/ExeUnit.scala")
emu=sha(r/"build/emu")
assert head=="0f12df675378556670afd0dd2153f47fcb330610"
assert exe=="fd98aaced17c39dabd4776a53948f05650c8956178f6540bf5695d15753d60fa"
assert emu=="2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8"
assert not run(["git","-C",str(w/"repo"),"status","--porcelain","--untracked-files=no"]).strip()
assert run(["git","-C",str(w/"repo"),"rev-parse","HEAD"]).strip()==final["candidate_commit"]
assert not run(["git","-C",str(r),"diff","--name-only","--","src"]).strip()
assert not run(["git","-C",str(r),"diff","--cached","--name-only","--","src"]).strip()
processes=run(["ps","-eo","pid,args"])
active=[x for x in processes.splitlines() if "/tools/root/usr/bin/yosys " in x or "/tools/root/usr/bin/berkeley-abc " in x or "/tools/root/usr/bin/sta " in x]
assert not active,active
now=datetime.datetime.now().astimezone().isoformat()
protection=dict(status="C3_HF_PRODUCTION_RETAINED_PASS",time=now,head=head,exeunit_sha256=exe,emu_sha256=emu,candidate_head=final["candidate_commit"],candidate_clean=True,production_source_unchanged=True,active_eda_processes=active)
(w/"production-final-check.json").write_text(json.dumps(protection,ensure_ascii=False,indent=2)+"\n")
n=sum(x["pass_"] for x in cost["comparisons"])
decision="成本通过，尚待新全核/NEMU及同镜像周期；当前仍保留0f" if ok else "成本拒绝，关闭本轮门控优化；保留0f，转回稳定集成和T17干净复现"
summary=(f"[C3-HF最小试验](../optimizations/o2/r3-div-gate/c3-hf/RESULT.md)完成：只改FP DIV/SQRT hold置位，原门控/接收/双hold保留；局部功能通过，"
 f"父级面积{cost['area_delta_percent']:+.6f}%，三控制D最差{cost['control_before_ns']:.6f}→{cost['control_after_ns']:.6f}ns，五档{n}/45路径通过、{45-n}/45未通过。{decision}。"
 "无新全核、周期、功耗或整核Fmax；未上传。旧C1/C2否决保持；今后改RTL仍提前告知，数据追加[版本档案](version-data-ledger.md)")
path=r/"team/docs/development-route-current.md"
s=path.read_text()
lines=s.splitlines()
found=0
for i,line in enumerate(lines):
 if line.startswith("| R3 |"):
  lines[i]="| R3 | [DIV取消关钟修复0f](../optimizations/o2/r3-div-gate/PERFORMANCE_COST_RESULT.md)已通过全核/NEMU及96对窗口周期不变；batch保持3.067873×RVV，父级部分STA退化已留档 | "+summary+" |"
  found+=1
 elif line.startswith("| R3 ") and "门控" in line:
  cells=line.split("|")
  lines[i]=f"| {cells[1].strip()} | {summary} | 不自动扩大改法、不放宽阈值，不将局部PASS转授T17；稳定工程接续按R4/O5、T17、R5/G5各自合同执行。发布仍按用户授权 |"
  found+=1
assert found==2,found
path.write_text("\n".join(lines)+"\n")
score=r/"开发计分板.md"
s=score.read_text()
marker="## 填写示例（不是实际记录）"
assert marker in s and "20261025-cc77-builder-c3-hf-01 /" not in s
record=(f"| 20261025-cc77-builder-c3-hf-01 / 2026-10-25 22:03～{now[11:16]}（UTC+08:00；含综合等待，非人工工时） | @cc77-builder / Agent；沿用本会话核实身份 | R3 C3-HF 单次最小范围试验 | "
 "改RTL前已说明，独立候选77d0a1228f0da7d584d5c7375b404dcda9763cf3，仅FP hold SET；原0f源码/EMU不变。"
 f"面积{cost['area_delta_percent']:+.6f}%，控制D最差{cost['control_before_ns']:.6f}→{cost['control_after_ns']:.6f}ns。 | "
 f"局部PASS：51主机项、10022完整128位向量、FU31499拍、原父级13组35075拍、补充115场景2959拍及保持递推2958合格拍，36分层拒错；54取消窗162采样零额外时钟。"
 f"一次综合、5常规+10定向STA，{n}/45路径通过、{45-n}/45未通过；独立原文审计通过。观察器首次编译失败及解析初检保留。[结果](team/optimizations/o2/r3-div-gate/c3-hf/RESULT.md)、[第21条档案](team/docs/version-data-ledger.md)。 | "
 f"{decision}。新全核/周期NOT_TESTED，无新加速比；未推送/未发Issue。候选本地提交，证据文档未提交，原始根/home/riscv/riscv-lab/o2-c3-hf-20261025；无在途硬件。 |\n\n")
score.write_text(s.replace(marker,record+marker))
(m/"README.md").write_text("""# C3-HF：FP DIV/SQRT 保持位最小试验\n\n"""+decision+"""\n\n- [完整结果与取舍](RESULT.md)\n- [冻结合同](CONTRACT.md)与[成本合同](cost/CONTRACT.md)\n- [固定候选身份](candidate.json)与[精确生产补丁](c3-hf-production.patch)\n- [封存证据](evidence/20261025-trial/manifest.json)\n- [统一版本数据档案](../../../../docs/version-data-ledger.md)\n\n只做一次生产候选；测试观察器编译及解析初检失败完整保留。复用套件中的C2标签不是本候选身份。候选局部与成本结果不转授全核、周期或功耗资格。原始工作目录为 /home/riscv/riscv-lab/o2-c3-hf-20261025；生产仍为0f。\n""")
print(json.dumps(protection,ensure_ascii=False))
