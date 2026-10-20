from pathlib import Path
from collections import defaultdict
import importlib.util,json,hashlib,re
d=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location("frozen",d/"analyze.frozen.py");m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
formal=json.loads((d/"result.json").read_text())
for name in ("stderr.log","stdout.log"):
 assert hashlib.sha256((d/name).read_bytes()).hexdigest()==formal["raw_logs_sha256"][name]
text=(d/"stderr.log").read_text()+(d/"stdout.log").read_text()
result=m.analyze(text,require_complete=True)
assert result["status"]=="O2_TRACE_PASS" and result["counts"]==formal["observation_counts"]
assert formal["status"]=="O2_CONTROL_LEGACY_PASS"
(d/"independent-analysis.json").write_text(json.dumps(result,indent=2)+"\n")
events,_=m.extract_events_and_uart(text)
groups=defaultdict(list)
for c,_,k,f in events:
 if k!="SCHEMA":groups[c].append((k,f))
first={}
for c,items in sorted(groups.items()):
 by=defaultdict(list)
 for k,f in items:by[k].append(f)
 st=by["STATE"][0] if by["STATE"] else None
 checks={
 "multi_inflight":bool(st and st["occupancy"]==2),
 "triple_overlap":bool(by["ACCEPT"] and by["MOVE"] and by["RESPONSE"]),
 "full_stall":bool(st and st["occupancy"]==2 and by["STALL"]),
 "kill_p":any(x["slot"]=="P" for x in by["KILL"]),
 "kill_r":any(x["slot"]=="R" for x in by["KILL"]),
 "partial_kill":bool(st and st["occupancy"]==2 and st["killp"]!=st["killr"]),
 }
 for kind,yes in checks.items():
  if yes and kind not in first:
   first[kind]={"cycle":c,"events":[{"kind":k,**f} for k,f in items],"previous_cycle":[{"kind":k,**f} for k,f in groups.get(c-1,[])],"next_cycle":[{"kind":k,**f} for k,f in groups.get(c+1,[])]}
assert set(first)=={"multi_inflight","triple_overlap","full_stall","kill_p","kill_r"}
assert not result["o2_coverage"]["partial_kill"]
enqueues=[f for _,_,k,f in events if k=="ENQUEUE"]
kills=[]
for c,_,k,f in events:
 if k!="KILL":continue
 seq=f["seq"];life=[{"kind":n,**x} for _,_,n,x in events if n in ("VFEX4_ACCEPT","ACCEPT","MOVE","STALL","RESPONSE","KILL") and x.get("seq")==seq]
 accept=[x for x in life if x["kind"]=="ACCEPT"];assert len(accept)==1
 assert not [x for x in life if x["kind"]=="RESPONSE"]
 a=accept[0];en=max((e for e in enqueues if e["rob"]==a["rob"] and e["cycle"]<=a["cycle"]),key=lambda x:x["cycle"])
 stop=min((e["cycle"] for e in enqueues if e["rob"]==a["rob"] and e["cycle"]>en["cycle"]),default=1<<64)
 commits=[x for t,_,n,x in events if n=="COMMIT" and x["rob"]==a["rob"] and en["cycle"]<t<stop]
 assert not commits
 state=[x for n,x in groups[c] if n=="STATE"][0]
 assert state["occupancy"]==1 and state["killp"]+state["killr"]==1
 prior=[x for n,x in groups[c-1] if n=="REDIRECT"];parent=[x for n,x in groups[c] if n=="VFEX4_REDIRECT"]
 assert len(prior)==len(parent)==1
 assert (prior[0]["rob"],prior[0]["self"])==(parent[0]["rob"],parent[0]["self"])==(f["redirect"],f["self"])
 kills.append({"slot":f["slot"],"cycle":c,"seq":seq,"rob":f["rob"],"state":state,"lifecycle":life,"enqueue":en,"rob_redirect":prior[0],"parent_redirect":parent[0],"normal_commit":False,"response":False,"partial_kill":False})
(d/"first-coverage-examples.json").write_text(json.dumps(first,indent=2)+"\n")
(d/"all-five-slot-kills.json").write_text(json.dumps(kills,indent=2)+"\n")
cycles={x["cycle"] for x in first.values()}|{x["cycle"] for x in kills}
context=set(t for c in cycles for t in (c-1,c,c+1))
lines=[]
for no,line in enumerate((d/"stderr.log").read_text().splitlines(),1):
 hit=re.match(r"O2_[A-Z_]+ cycle=\s*(\d+)",line)
 if hit and int(hit[1]) in context:lines.append(f"{no}: {line}")
(d/"raw-event-excerpts.txt").write_text("\n".join(lines)+"\n")
summary={"status":"COMPLETE_CONTROL_OBSERVER_CHECK_PASS","counts":result["counts"],"coverage":result["o2_coverage"],"first_cycles":{k:v["cycle"] for k,v in first.items()},"all_slot_kills":[{k:x[k] for k in ("slot","cycle","seq","rob","partial_kill")} for x in kills],"pending_count":result["pending_count"],"unfinished_rob_count":result["unfinished_rob_count"],"notes":["All five slot kills occur with occupancy=1; no partial survivor exists in this run.","No inference about the writer winning downstream arbitration.","This is control-only review, not final G3 acceptance."]}
(d/"review-result.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
