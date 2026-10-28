"""Read sealed S1 traces without executing EMU; cross-check the existing diagnostic."""
import argparse, collections, gzip, hashlib, json
from pathlib import Path
def require(ok, message):
    if not ok: raise ValueError(message)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);args=ap.parse_args()
    require(not args.output.exists(),"new output required")
    root=args.repo/"team/optimizations/o2/r2-vector-accum/evidence/merged-v2"
    mb=(root/"archive-manifest.json").read_bytes()
    require(hashlib.sha256(mb).hexdigest()=="a1af4314c83b29d97b58b7ae9fe65dbc96bb3d050530d2fe7378c022b9415d73","manifest identity")
    manifest=json.loads(mb);by_stored={x["stored"]:x for x in manifest["files"]};by_original={x["original"]:x for x in manifest["files"]};used={}
    def raw(row):
        stored=(root/row["stored"]).read_bytes()
        require(len(stored)==row["stored_bytes"] and hashlib.sha256(stored).hexdigest()==row["stored_sha256"],"stored hash")
        data=gzip.decompress(stored) if row["encoding"]=="gzip" else stored
        require(len(data)==row["raw_bytes"] and hashlib.sha256(data).hexdigest()==row["raw_sha256"],"raw hash")
        used[row["stored"]]={"raw_sha256":row["raw_sha256"],"stored_sha256":row["stored_sha256"]}
        return data
    diagnostic=json.loads(raw(by_stored["files/support/completed-large-shape-fu-diagnostic.json.gz"]))
    import re
    def events(text,prefix):
        return [{k:v for k,v in re.findall(r"(\w+)=\s*([^\s]+)",line)} for line in text.splitlines() if line.startswith(prefix+" ")]
    grouped={};perf_events=0;perf_nonzero=0
    for source in diagnostic["sources"]:
        result_raw=raw(by_original[source["result"]])
        require(hashlib.sha256(result_raw).hexdigest()==source["result_sha256"],"result association")
        result=json.loads(result_raw)
        directory=Path(source["result"]).parent
        texts={}
        for name,digest in source["raw_sha256"].items():
            value=raw(by_original[str(directory/name)])
            require(hashlib.sha256(value).hexdigest()==digest,"diagnostic stream association")
            require(result["raw_sha256"][name]==digest,"result stream association")
            texts[name]=value.decode()
        accepted=events(texts["stderr.log"],"O2_ACCEPT");responded=events(texts["stderr.log"],"O2_RESPONSE");states=events(texts["stderr.log"],"O2_STATE")
        responses={int(v["seq"]):v for v in responded}
        require(len(responses)==len(responded),"duplicate responses")
        for x in accepted+responded:
            perf_events+=1;perf_nonzero+=int(int(x["perf"],16)!=0)
        for sample in result["samples"]:
            if sample["phase"]!="measured" or sample["method"]!="vdot":continue
            begin,end=sample["sample_ticks"][1:3]
            require(end-begin==sample["cycles"],"cycle window geometry")
            a=[v for v in accepted if begin<=int(v["cycle"])<=end]
            require(len(a)==sample["dots"]==128,"window accepted count")
            key=(result["shard"],result["variant"],sample["software"])
            entry=grouped.setdefault(key,{"cycles":[],"instructions":set(),"counts":[],"gaps":collections.Counter(),"latencies":collections.Counter(),"stalls":0,"spans":[]})
            entry["cycles"].append(sample["cycles"]);entry["instructions"].add(sample["instructions"]);entry["counts"].append(len(a))
            cycles=[int(v["cycle"]) for v in a];entry["gaps"].update(y-x for x,y in zip(cycles,cycles[1:]))
            for v in a:
                response=responses[int(v["seq"])]
                require(int(response["cycle"])<=end,"response outside measured window")
                entry["latencies"].update([int(response["cycle"])-int(v["cycle"])])
            entry["spans"].append(cycles[-1]-cycles[0])
            entry["stalls"]+=sum(begin<=int(x["cycle"])<=end and x["outvalid"]=="1" and x["outready"]=="0" for x in states)
    rows=[]
    for key,e in sorted(grouped.items()):
        row={"shard":key[0],"variant":key[1],"software":key[2],"windows":len(e["cycles"]),"mean_cycles":sum(e["cycles"])/len(e["cycles"]),"instructions":sorted(e["instructions"]),"accepted_range":[min(e["counts"]),max(e["counts"])],"accept_gaps":{str(k):v for k,v in sorted(e["gaps"].items())},"response_latencies":{str(k):v for k,v in sorted(e["latencies"].items())},"writeback_stall_events":e["stalls"],"mean_accept_span":sum(e["spans"])/len(e["spans"])}
        expected=next(v for v in diagnostic["rows"] if (v["shard"],v["variant"],v["software"])==key)
        require(row==expected,"raw recomputation differs from sealed diagnostic: "+str(key))
        rows.append(row)
    require(len(diagnostic["sources"])==12 and len(rows)==8 and sum(x["windows"] for x in rows)==96,"complete fixed diagnostic coverage")
    require(perf_events==36864 and perf_nonzero==0,"fixed archive perf statistics")
    output={"status":"R3_S1_READONLY_RAW_DIAGNOSTIC_RECOMPUTE_PASS","scope":"12 existing S0/S1 16x64 core/endtoend processes, 96 measured vdot windows; no new hardware execution, not causal stall attribution","new_emu_runs":0,"manifest_sha256":hashlib.sha256(mb).hexdigest(),"verified_inputs":used,"rows":rows,"perf_trace_events":perf_events,"perf_trace_nonzero":perf_nonzero,"constant_input_inference":"Trace zeros alone do not prove constant hardware; source and generated DataPath assignments are reviewed separately."}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(output,indent=2)+"\n")
    print(output["status"],"windows",sum(x["windows"] for x in rows),"perf_events",perf_events,"nonzero",perf_nonzero)
if __name__=="__main__":main()
