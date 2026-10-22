from pathlib import Path
import importlib.util,json,hashlib
d=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("frozen",d/"analyze.frozen.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
events,_=m.extract_events_and_uart((d/"stderr.log").read_text())
result=json.loads((d/"result.json").read_text())
cases=json.loads((d/"exceptions.json").read_text())
assert result["status"]=="VDOT_MATRIX_SHARD_PASS"
assert result["observation_status"]=="O2_TRACE_PASS"
for name in ("stdout.log","stderr.log"):
 assert hashlib.sha256((d/name).read_bytes()).hexdigest()==result["raw_logs_sha256"][name]
accepts=[f for _,_,k,f in events if k=="ACCEPT"]
illegal=[f for f in accepts if f["illegal"]]
legal=[f for f in accepts if not f["illegal"]]
assert len(accepts)==13 and len(illegal)==2 and len(legal)==11
out=[]
for a in illegal:
 en=max((f for _,_,k,f in events if k=="ENQUEUE" and f["rob"]==a["rob"] and f["cycle"]<=a["cycle"]),key=lambda f:f["cycle"])
 match=[x for x in cases if x["word"]==en["word"] and x["vl"]==a["vl"]]
 assert len(match)==1
 case=match[0]
 assert case["id"] in ("X09-v31","X10-3-0") and case["expected_cause"]==2 and a["vl"]==7
 vd=(en["word"]>>7)&31;vs1=(en["word"]>>15)&31;vs2=(en["word"]>>20)&31
 assert (vd,vs1,vs2)==(case["vd"],case["vs1"],case["vs2"])
 assert (a["vecwen"],a["v0wen"])==(1,0)
 steps={k:[f for _,_,n,f in events if n==k and f.get("seq")==a["seq"]] for k in ("MOVE","RESPONSE","KILL","VFEX4_ACCEPT")}
 assert len(steps["MOVE"])==len(steps["RESPONSE"])==len(steps["VFEX4_ACCEPT"])==1
 assert not steps["KILL"]
 parent=steps["VFEX4_ACCEPT"][0];move=steps["MOVE"][0];response=steps["RESPONSE"][0]
 assert parent["cycle"]==a["cycle"] and move["cycle"]==a["cycle"]+1 and response["cycle"]==a["cycle"]+2
 for f in (parent,move,response):
  assert (f["seq"],f["rob"],f["pdest"])==(a["seq"],a["rob"],a["pdest"])
 for f in (move,response):
  assert (f["illegal"],f["exception"],f["vecwen"],f["v0wen"])==(1,4,0,0)
  assert (f["vpu"],f["perf"])==(a["vpu"],a["perf"])
 assert response["data"]==0
 redirect=min((f for _,_,k,f in events if k=="REDIRECT" and f["cycle"]>response["cycle"] and m.flushed(a["rob"],f["rob"],f["self"])),key=lambda f:f["cycle"])
 assert (redirect["rob"],redirect["self"])==(a["rob"],1)
 parent_flush=[f for _,_,k,f in events if k=="VFEX4_REDIRECT" and f["cycle"]==redirect["cycle"]+1]
 assert len(parent_flush)==1 and (parent_flush[0]["rob"],parent_flush[0]["self"])==(a["rob"],1)
 assert not [f for _,_,k,f in events if k=="COMMIT" and f["rob"]==a["rob"] and en["cycle"]<=f["cycle"]<=redirect["cycle"]]
 assert f'VDOT_PACKED id={case["id"]} result=PASS payload=' in (d/"stdout.log").read_text()
 out.append(dict(case_id=case["id"],decoded_registers=dict(vd=vd,vs1=vs1,vs2=vs2),enqueue=en,accept=a,move=move,response=response,redirect=redirect,parent_redirect=parent_flush[0],fu_kill=False,normal_commit=False))
# Inspect legal write-enable contrast only; do not repeat alias/arithmetic audit.
for a in legal:
 assert (a["vecwen"],a["v0wen"])==(1,0)
 for _,_,k,f in events:
  if k in ("MOVE","RESPONSE") and f["seq"]==a["seq"]:
   assert (f["illegal"],f["exception"],f["vecwen"],f["v0wen"])==(0,0,1,0)
assert result["observation_counts"]["ACCEPTED_THEN_SQUASHED"]==2
assert result["observation_counts"]["ACCEPTED_YOUNGER_SQUASHED"]==0
assert result["observation_counts"]["KILL"]==0
summary=dict(status="FINAL_ILLEGAL_FU_SEMANTIC_CHECK_PASS",legal_accepts=len(legal),illegal_accepts=len(illegal),v0_accepts=sum(a["v0wen"] for a in accepts),illegal_transactions=out,
 scope="Final functional-1 semantic review only; not full G3 acceptance. Complete-run status comes from original frozen runner.")
(d/"semantic-result.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
