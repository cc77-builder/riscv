from pathlib import Path
import json
d=Path(__file__).resolve().parent
records=json.loads((d/"selected-records.json").read_text())
assert [(x["shard"],x["case"]["id"]) for x in records]==[(2,"L04-0-8-9"),(3,"L04-10-0-9")]
summary=[]
for x in records:
 e,a,m,r,c=(x[k] for k in ("enqueue","accept","move","response","commit"))
 wd=e["word"];vd=(wd>>7)&31;s1=(wd>>15)&31;s2=(wd>>20)&31
 assert (vd,s1,s2)==tuple(x["decoded"][k] for k in ("vd","vs1","vs2"))
 assert a["illegal"]==0 and a["vl"]==8
 expected_wen=(int(vd!=0),int(vd==0))
 for f in (a,m,r):
  assert (f["seq"],f["rob"],f["pdest"])==(a["seq"],a["rob"],a["pdest"])
  assert (f["vecwen"],f["v0wen"])==expected_wen
  assert (f["vpu"],f["perf"])==(a["vpu"],a["perf"])
 for f in (m,r):assert (f["illegal"],f["exception"])==(0,0)
 assert (m["cycle"],r["cycle"])==(a["cycle"]+1,a["cycle"]+2)
 assert e["cycle"]<a["cycle"]<r["cycle"]<c["cycle"]
 assert (c["rob"],c["pc"],c["ftq"])==(e["rob"],e["pc"],e["ftq"])
 assert a["vs1"]==int(x["case"]["src1_128"],16) and a["vs2"]==int(x["case"]["src2_128"],16)
 signed=lambda z:z-256 if z&128 else z
 math_sum=sum(signed((a["vs1"]>>(8*i))&255)*signed((a["vs2"]>>(8*i))&255) for i in range(8))
 assert math_sum==-8
 assert r["data"]==(math_sum&0xffffffff)==int(x["case"]["expected_128"],16)
 assert r["data"]>>32==0
 summary.append(dict(shard=x["shard"],case=x["case"]["id"],seq=a["seq"],rob=a["rob"],pdest=a["pdest"],decoded=x["decoded"],write_enables=expected_wen,full128=f'{r["data"]:032x}',cycles={k:x[k]["cycle"] for k in ("enqueue","accept","move","response","commit")}))
assert all(x["decoded"]["vs2"]!=0 for x in records)
assert all(len(set(x["decoded"].values()))==3 for x in records)
out=dict(status="FOCUSED_V0_SEMANTIC_CHECK_PASS",transactions=summary,coverage=dict(v0_destination=True,v0_source_vs1=True,v0_source_vs2=False,v0_same_register_alias=False),scope="functional-0..3 only; no inference about later shards or full G3 completion")
(d/"semantic-result.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out,indent=2))
