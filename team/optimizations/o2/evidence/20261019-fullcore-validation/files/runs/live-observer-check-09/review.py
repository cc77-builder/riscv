from pathlib import Path
from collections import defaultdict
import importlib.util,json,re,hashlib
d=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("frozen",d/"analyze.frozen.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
formal=json.loads((d/"result.json").read_text())
assert formal["status"]=="O2_SUPPLEMENT_PASS"
assert formal["workload_status"]=="O2_CONTROL_DIAGNOSTIC_PASS"
assert formal["observation_status"]=="O2_TRACE_PASS"
for name in ("stderr.log","stdout.log"):
 assert hashlib.sha256((d/name).read_bytes()).hexdigest()==formal["raw_logs_sha256"][name]
text=(d/"audit-input.log").read_text()
a=m.analyze(text,require_complete=True)
assert a["status"]=="O2_TRACE_PASS" and a["counts"]["PARTIAL_KILL"]==1
assert a["counts"]==formal["observation_counts"]
assert a["pending_count"]==0 and a["pending_div_count"]==0 and a["unfinished_rob_count"]==0
(d/"complete-analysis.json").write_text(json.dumps(a,indent=2)+"\n")
events,_=m.extract_events_and_uart(text)
groups=defaultdict(list)
for c,_,k,f in events:groups[c].append((k,f))
cycle=609217
one=lambda c,k:next(f for n,f in groups[c] if n==k)
s=one(cycle,"STATE")
assert (s["occupancy"],s["pvalid"],s["rvalid"],s["pseq"],s["rseq"],s["prob"],s["rrob"],s["ppdest"],s["rpdest"])==(2,1,1,1741,1740,"1:2","0:41",49,14)
assert (s["killp"],s["killr"],s["move"],s["outvalid"],s["outready"])==(1,0,0,1,1)
redirect=one(cycle-1,"REDIRECT");parent=one(cycle,"VFEX4_REDIRECT")
assert (redirect["rob"],redirect["self"])==(parent["rob"],parent["self"])==("0:43",0)
assert m.flushed("1:2","0:43",0) and not m.flushed("0:41","0:43",0)
records={}
for seq in (1740,1741):
 life=[{"kind":k,**f} for _,_,k,f in events if k in ("VFEX4_ACCEPT","ACCEPT","MOVE","RESPONSE","STALL","KILL") and f.get("seq")==seq]
 accept=next(x for x in life if x["kind"]=="ACCEPT")
 en=max((f for _,_,k,f in events if k=="ENQUEUE" and f["rob"]==accept["rob"] and f["cycle"]<=accept["cycle"]),key=lambda x:x["cycle"])
 stop=min((f["cycle"] for _,_,k,f in events if k=="ENQUEUE" and f["rob"]==en["rob"] and f["cycle"]>en["cycle"]),default=1<<64)
 commit=[f for c,_,k,f in events if k=="COMMIT" and f["rob"]==en["rob"] and en["cycle"]<c<stop]
 records[str(seq)]={"enqueue":en,"accept":accept,"lifecycle":life,"commits":commit}
p=records["1741"];r=records["1740"]
assert p["accept"]["cycle"]==609216
assert not [x for x in p["lifecycle"] if x["kind"] in ("MOVE","RESPONSE")]
assert [x["cycle"] for x in p["lifecycle"] if x["kind"]=="KILL"]==[609217]
assert not p["commits"]
assert r["accept"]["cycle"]==609215
assert [x["cycle"] for x in r["lifecycle"] if x["kind"]=="MOVE"]==[609216]
responses=[x for x in r["lifecycle"] if x["kind"]=="RESPONSE"]
assert len(responses)==1 and responses[0]["cycle"]==609217
response=responses[0];ra=r["accept"]
assert not [x for x in r["lifecycle"] if x["kind"]=="KILL"]
assert len(r["commits"])==1 and r["commits"][0]["cycle"]==609283
commit=r["commits"][0];en=r["enqueue"]
assert (commit["pc"],commit["ftq"],commit["rob"])==(en["pc"],en["ftq"],en["rob"])==(0x80002978,"1:2","0:41")
for f in [x for x in r["lifecycle"] if x["kind"] in ("MOVE","RESPONSE")]:
 assert (f["seq"],f["rob"],f["pdest"],f["vpu"],f["perf"])==(ra["seq"],ra["rob"],ra["pdest"],ra["vpu"],ra["perf"])
 assert (f["illegal"],f["exception"],f["vecwen"],f["v0wen"])==(0,0,1,0)
signed=lambda x:x-256 if x&128 else x
expected=sum(signed((ra["vs1"]>>(8*i))&255)*signed((ra["vs2"]>>(8*i))&255) for i in range(8))&0xffffffff
assert response["data"]==expected==0xffffe421 and response["data"]>>32==0
nextstate=one(cycle+1,"STATE");assert nextstate["occupancy"]==0
assert not [f for k,f in groups[cycle] if k in ("ACCEPT","MOVE")]
out={"status":"FINAL_PARTIAL_KILL_SURVIVOR_CHECK_PASS","scope":"Complete supplement-01 control stream and sole partial-kill lifecycle; not overall supplement or G3 acceptance.","partial_cycle":cycle,"state":s,"rob_redirect":redirect,"parent_redirect":parent,"transactions":records,"survivor_full128":f"{expected:032x}","next_state":nextstate,"final_counts":a["counts"],"final_coverage":a["o2_coverage"]}
(d/"survivor-check.json").write_text(json.dumps(out,indent=2)+"\n")
context=set(range(609190,609220))|{609283}
excerpt=[]
for no,line in enumerate((d/"stderr.log").read_text().splitlines(),1):
 hit=re.match(r"O2_[A-Z_]+ cycle=\s*(\d+)",line)
 if hit and int(hit[1]) in context:excerpt.append(f"{no}: {line}")
(d/"raw-event-excerpts.txt").write_text("\n".join(excerpt)+"\n")
print(json.dumps({"status":out["status"],"partial_cycle":cycle,"survivor_response_cycle":609217,"survivor_commit_cycle":609283,"counts":a["counts"],"coverage":a["o2_coverage"]},indent=2))
