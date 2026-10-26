"""Offline phased Q288 supply coordinates; no new EMU or performance decision."""
from __future__ import annotations
import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
import gzip, hashlib, importlib.util, json, os, re, struct, sys, time, zipfile
from pathlib import Path, PurePosixPath

CONTRACT = "r2-s3-runq-q288-phased-cost-v1"
TARGET = "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/phased/target"
BASE = "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/target/cost.py"
BASE_SHA = "322f27b809f0b89da67beee35443225363d58c875617db93bf8161ebebfe50b7"
CONTEXT = "team/optimizations/o2/r2-config-reuse/caller/hoisted/context_prefix.py"
CONTEXT_SHA = "e65e4a6056c9059af4a407445e3485256fbd976ad3778a7c24655cb08753015b"
ELF_SHA = "bcbe7088f3548813d8ea24fd3a71ce5cb268e7074e7573bb74680d641e5a33b4"
BIN_SHA = "73bc3a0e8b6d172cb427b09c2f6ff5ca2e0b56c0e0c1617b426cdc20bf84342d"
TARGET_CONTRACT_SHA = "03b06d38356696a73cb846b9f20e5212282bc4c2e7b3ed36d7d7976a4dd32792"
ORDER = [2,0,1,2,2,1,0,2]
MASK, MATCH = 0xfe00707f, 0x0200000b
c = None
sys.dont_write_bytecode = True

def need(ok,message):
    if not ok: raise ValueError(message)

def digest(raw): return hashlib.sha256(raw).hexdigest()

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def source_coordinate(item,start):
    """Compressed retire instructions keep the same observed cycle."""
    return dict(position=item["position"],pc=item["pc"],word=item["word"],
                retire_cycle=start+item["tick"],observation_group=item["group"],
                group_offset=item["group_offset"],group_count=item["group_count"],
                slot=item["slot"])

def adjacent_pair(previous,current):
    p,n,e=previous["accept"],current["accept"],current["enqueue"]
    need(e<=n,"allocation before acceptance")
    gap=n-p
    if gap<0:return dict(signed_accept_delta=gap,negative=True)
    boundary=min(n,max(p,e))
    result=dict(signed_accept_delta=gap,negative=False,
                before_next_allocation=boundary-p,after_next_allocation=n-boundary)
    need(result["before_next_allocation"]+result["after_next_allocation"]==gap,"adjacent partition")
    return result

def latest_load(writes,reg):
    value=writes.get(reg)
    need(value is not None and value["kind"]=="load","latest writer must be a qualifying load")
    return value

def dependency_groups(frontier,transactions,row,elf,start):
    """Bind the two low-64-bit producers from exact dynamic integer cores."""
    words=131 if row["variant"]=="phased" else 140
    begin=elf.symbols[row["wrapper"]][0]+60
    starts=[i for i,v in enumerate(frontier) if v["pc"]==begin]
    need(len(starts)==324 and len(transactions)==10368,"complete dynamic core inventory")
    result,groups,cursor=[],[],0
    for group,position in enumerate(starts):
        block=frontier[position:position+words]
        need(len(block)==words and all(v["pc"]==begin+4*i for i,v in enumerate(block)),"exact contiguous core")
        pointers={11:("X",0),12:("W",0)};writes={};mode=None;config=None;count=0;products=set()
        for item in block:
            word=item["word"];op=word&127;f3=(word>>12)&7
            rd,a,b=(word>>7)&31,(word>>15)&31,(word>>20)&31
            if word in (0xc0047057,0xc1027057):
                mode=(8,8) if word==0xc0047057 else (4,32);config=item
            elif op==0x13 and f3==0:
                imm=word>>20;imm=imm-4096 if imm&2048 else imm
                need(a in pointers,"known scalar address producer")
                region,offset=pointers[a];pointers[rd]=(region,offset+imm)
            elif word&0xfff0707f==0x02000007:
                need(mode==(8,8) and a in pointers,"qualified low-eight-byte unmasked load")
                region,offset=pointers[a];limit=32 if region=="X" else 256
                need(0<=offset<=limit-8 and offset%8==0,"input chunk range")
                writes[rd]=dict(kind="load",region=region,offset=offset,coordinate=source_coordinate(item,start))
            elif word&MASK==MATCH:
                need(mode==(8,8) and config is not None,"qualified dot configuration")
                left,right=latest_load(writes,a),latest_load(writes,b)
                need(left["region"]=="W" and right["region"]=="X" and
                     left["offset"]%32==right["offset"],"matching W/X logical chunk")
                semantic=(left["offset"]//32,right["offset"]//8)
                need(semantic not in products,"one dot per row/chunk");products.add(semantic)
                tx=transactions[cursor];cursor+=1
                need(tx["pc"]==item["pc"] and tx["word"]==word and tx["commit"]==start+item["tick"],
                     "dynamic dot commit coordinate")
                producers=dict(weight=left["coordinate"],input=right["coordinate"],
                               configuration=source_coordinate(config,start))
                need(all(v["position"]<item["position"] and v["retire_cycle"]<=tx["commit"]
                         for v in producers.values()),"preceding producer retirement")
                maturity=max(tx["enqueue"],*(v["retire_cycle"] for v in producers.values()))
                result.append(dict(tx,group=group,tile=group//9,quant_group=group%9,dot_index=count,
                    logical_row=semantic[0],chunk=semantic[1],position=item["position"],
                    producers=producers,producer_retired_bound=maturity,
                    accept_minus_producer_retired_bound=tx["accept"]-maturity))
                # Resolve both inputs before updating the architectural destination.
                writes[rd]=dict(kind="dot");count+=1
            elif op==0x57 and word>>26==0 and f3==0 and (word>>25)&1:
                need(mode==(4,32),"full-width reduction mode")
                writes[rd]=dict(kind="add")
            else:raise ValueError("unclassified integer-core instruction "+hex(word))
        need(count==32 and products=={(r,k) for r in range(8) for k in range(4)},"complete semantic dot set")
        tx=result[-32:]
        tail=frontier[position+words:starts[group+1] if group+1<len(starts) else len(frontier)]
        convert=[v for v in tail if v["word"]&127==0x57 and (v["word"]>>26,(v["word"]>>12)&7)==(0x12,1)]
        adds=[v for v in tail if v["word"]&127==0x57 and (v["word"]>>26,(v["word"]>>12)&7)==(0,1)]
        need(len(convert)==len(adds)==1,"one complete FP epilogue per core")
        groups.append(dict(group=group,tile=group//9,quant_group=group%9,entry_position=position,
            core_words=words,first_retire_cycle=start+block[0]["tick"],last_retire_cycle=start+block[-1]["tick"],
            convert_retire_cycle=start+convert[0]["tick"],add_retire_cycle=start+adds[0]["tick"],
            first_enqueue=min(v["enqueue"] for v in tx),first_accept=min(v["accept"] for v in tx),
            last_response=max(v["response"] for v in tx),last_commit=max(v["commit"] for v in tx)))
    need(cursor==len(transactions),"all transactions bound to exact producers")
    return result,groups

def supply_statistics(transactions,events,start,stop,silence_bound):
    buckets=defaultdict(list);pairs=[]
    for previous,current in zip(transactions,transactions[1:]):
        category=("within-core" if previous["group"]==current["group"] else
                  "between-quant-groups" if previous["tile"]==current["tile"] else "between-tiles")
        pair=adjacent_pair(previous,current);pair.update(category=category,next_dot=current["dot_index"])
        buckets[category].append(pair);pairs.append(pair)
    need(Counter(v["category"] for v in pairs)==Counter({"within-core":10044,"between-quant-groups":288,"between-tiles":35}),
         "all 10367 program-neighbor pairs including boundaries")
    def summaries(values):
        positive=[v for v in values if not v["negative"]]
        return dict(pairs=len(values),negative_pairs=sum(v["negative"] for v in values),
            signed_accept_delta=c.stats(v["signed_accept_delta"] for v in values),
            nonnegative_before_allocation=c.stats(v["before_next_allocation"] for v in positive),
            nonnegative_after_allocation=c.stats(v["after_next_allocation"] for v in positive))
    states={v["cycle"]:v for _,_,kind,v in events if kind=="STATE"}
    redirects={v["cycle"] for _,_,kind,v in events if kind=="VFEX4_REDIRECT"}
    mature=c.merged_waits([dict(enqueue=v["producer_retired_bound"],accept=v["accept"]) for v in transactions],start,stop)
    pending=c.merged_waits(transactions,start,stop);need(mature<=pending,"mature waiting is a subset of allocated waiting")
    observed={tick for tick in mature if tick in states and states[tick]["vready"]==1 and
              states[tick]["invalid"]==0 and states[tick]["divoccupied"]==0 and tick not in redirects}
    silent=mature-states.keys()
    return dict(program_neighbors=summaries(pairs),by_boundary={k:summaries(v) for k,v in buckets.items()},
        by_next_dot={str(k):summaries([v for v in buckets["within-core"] if v["next_dot"]==k]) for k in range(1,32)},
        allocated_wait_union_cycles=len(pending),producers_retired_wait_union_cycles=len(mature),
        producers_retired_and_ready_without_request_observed=len(observed),
        producers_retired_during_silence=len(silent),
        producers_retired_in_source_bound_empty_domain=len(silent) if silence_bound else None,
        producer_bound_not_before_accept=sum(v["producer_retired_bound"]>=v["accept"] for v in transactions),
        accept_minus_producer_retired_bound=c.stats(v["accept_minus_producer_retired_bound"] for v in transactions),
        scope="program-neighbor durations can overlap and contain other accepts; producer retirement is only a completion upper bound; no IQ/port/cache causal attribution")

def controls():
    """Counterexamples for temporal and latest-writer mistakes, not target samples."""
    results=[]
    p=adjacent_pair(dict(accept=10),dict(enqueue=3,accept=20))
    need(p["before_next_allocation"]==0 and p["after_next_allocation"]==10,"clamp old allocation")
    results.append("allocation-before-previous-accept")
    q=adjacent_pair(dict(accept=20),dict(enqueue=5,accept=12))
    need(q==dict(signed_accept_delta=-8,negative=True),"negative order retained")
    results.append("intervening-out-of-order-accept")
    try:latest_load({2:dict(kind="dot")},2)
    except ValueError as error:need(str(error)=="latest writer must be a qualifying load","specific stale-load rejection")
    else:raise ValueError("stale load accepted")
    results.append("intervening-writer-rejected")
    same=dict(position=4,pc=0x1000,word=0,group=3,group_offset=0,group_count=2,slot=1,tick=7)
    other=dict(same,position=5,group_offset=1)
    need(source_coordinate(same,100)["retire_cycle"]==source_coordinate(other,100)["retire_cycle"]==107,
         "compressed retirement shares one observation cycle")
    results.append("compressed-retirement-no-fabricated-subcycle")
    a=[dict(enqueue=2,accept=8),dict(enqueue=4,accept=10),dict(enqueue=12,accept=9)]
    union=c.merged_waits(a,0,15)
    need(union==set(range(3,10)),"strict endpoint overlap union")
    results.append("overlap-union-and-late-maturity")
    shifted=c.merged_waits([dict(enqueue=x["enqueue"]+100,accept=x["accept"]+100) for x in a],100,115)
    need({v-100 for v in shifted}==union,"global time translation invariance")
    results.append("global-time-translation")
    need(not c.merged_waits([dict(enqueue=8,accept=8),dict(enqueue=10,accept=8)],0,15),"mature at/after acceptance empty")
    results.append("no-positive-bound-required")
    # No STATE can establish directly observed ready, irrespective of silence interpretation.
    states={};need(not {v for v in union if v in states},"silence is not directly observed ready")
    results.append("missing-state-not-observed-ready")
    return dict(status="PHASED_COST_TEMPORAL_CONTROLS_PASS",controls=results,new_emu_runs=0)


def trace_inputs(archive, entries, samples, observer):
    """Use frozen field grammar, gated by an exact previously qualified archive.

    Selection does not constitute a fresh whole-stream O2 state/UART audit.
    """
    starts = [row["sample_ticks"][1] for row in samples]
    stops = [row["sample_ticks"][2] for row in samples]
    inside = lambda t: (i := bisect_right(starts, t) - 1) >= 0 and t < stops[i]
    names = "|".join(sorted(observer.FIELDS, key=len, reverse=True))
    pattern = re.compile(r"O2_(" + names + r")[ \t]+([^\n]*)\n")
    global_kinds = {"ENQUEUE", "ACCEPT", "RESPONSE", "COMMIT"}
    local_kinds = {"STATE", "MOVE", "STALL", "VFEX4_WAIT", "VFEX4_REDIRECT", "KILL",
                   "DIV_ACCEPT", "DIV_KILL", "DIV_OUTPUT"}
    events, local, t13 = [], [[] for _ in samples], []
    counts, schema, raw_sha, raw_size = Counter(), None, hashlib.sha256(), 0
    name = "run/runs/recovery/stderr.log"
    with archive.open(name) as stream:
        for raw in stream:
            raw_sha.update(raw)
            raw_size += len(raw)
            line = raw.decode("utf-8")
            if line.startswith(("T13_COUNTER_ENQUEUE", "T13_CSR_SAMPLE", "T13_RETIRE")):
                t13.append(line)
            match = pattern.search(line)
            if match is None:
                continue
            kind, body = match.groups()
            counts[kind] += 1
            if kind == "SCHEMA":
                need(schema is None, "duplicate schema")
                schema = observer.parse_fields(kind, body, observer.FIELDS[kind])
                continue
            need(schema is not None and kind != "RESET", "missing schema or runtime reset")
            tick_match = re.match(r"cycle=\s*([0-9]+)", body)
            need(tick_match is not None, "missing event cycle")
            tick = int(tick_match.group(1))
            if not (kind in global_kinds or kind in local_kinds and inside(tick)):
                continue
            row = observer.parse_fields(kind, body, observer.FIELDS[kind], schema)
            event = (tick, len(events), kind, row)
            if kind in global_kinds:
                events.append(event)
            if inside(tick):
                local[bisect_right(starts, tick) - 1].append(event)
    pin = entries[name]
    need(raw_size == pin["raw_bytes"] and raw_sha.hexdigest() == pin["raw_sha256"], "recovery raw identity")
    fixed = dict(version=1, clock="global", latency=2, slots=2, rob_size=48, ftq_size=8, vlen=128,
                 vpu_width=195, perf_width=577)
    need(schema == fixed and counts["COMMIT"] == 124417, "fixed schema and complete custom inventory")
    need(all(a[0] <= b[0] for a, b in zip(events, events[1:])), "event clock order")
    replay = "run/runs/replay/stderr.log"
    replay_hash, replay_size = hashlib.sha256(), 0
    with archive.open(replay) as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            replay_hash.update(chunk)
            replay_size += len(chunk)
    need(replay_size == entries[replay]["raw_bytes"] == raw_size and
         replay_hash.hexdigest() == entries[replay]["raw_sha256"] == raw_sha.hexdigest(),
         "replay exact trace identity")
    return events, local, "".join(t13), dict(schema=schema, full_event_counts=dict(counts),
        stderr_bytes=raw_size, stderr_sha256=raw_sha.hexdigest(), replay_input_identical=True,
        replay_interpretation="same deterministic input bytes; no new target run or independent sample")


def analyze(repo, archive_path, seal_path, seal_sha, fresh_path, output):
    global c
    started=time.time()
    need(digest((repo/BASE).read_bytes())==BASE_SHA,"published cost helper identity")
    c=module("phased_cost_published_helpers",repo/BASE)
    need(c.file_digest(seal_path)==seal_sha,"explicit invocation seal identity")
    seal=json.loads(seal_path.read_text())
    archive_pins=seal["archive_files"]
    need(seal["contract"]==CONTRACT and seal["source_freeze_commit"]==
         "34092ebcf579a5de76e70cadfb6a5333173891ae" and
         set(archive_pins)=={"payload.zip","archive-manifest.json","original-audit.json"},"exact sealed campaign identity")
    for name,pin in archive_pins.items():
        need(c.file_digest(archive_path/name)==pin,"sealed archive identity: "+name)
    need(c.file_digest(fresh_path)==seal["fresh_source_result_sha256"],"fresh-source receipt identity")
    fresh=json.loads(fresh_path.read_text())
    need(fresh["status"]=="PHASED_TARGET_ARCHIVE_FRESH_SOURCE_AUDIT_PASS" and
         fresh["fresh_python_process"] is True and
         fresh["archive_manifest_sha256"]==archive_pins["archive-manifest.json"],"completed isolated source audit")
    manifest=json.loads((archive_path/"archive-manifest.json").read_text())
    need(manifest["format"]=="split-evidence-zip-v1" and
         manifest["payload_sha256"]==archive_pins["payload.zip"] and
         (archive_path/"payload.zip").stat().st_size==manifest["stored_bytes"],"manifest and sealed payload agreement")
    audit=json.loads((archive_path/"original-audit.json").read_text())
    need(manifest["contract"]=="r2-s3-runq-q288-phased-target-v1" and
         audit["status"]=="PHASED_TARGET_RAW_EVIDENCE_AUDIT_PASS" and
         audit["original_emu_runs"]==3 and audit["windows_per_normal_run"]==8 and
         audit["committed_vdot_per_normal_run"]==124417,"original completed qualification")
    entries={row["path"]:row for row in manifest["files"]}
    need(len(entries)==len(manifest["files"]),"unique archive inventory")
    input_hashes={}
    with zipfile.ZipFile(archive_path/"payload.zip") as archive:
        names=archive.namelist()
        need(len(names)==len(set(names)) and set(names)==set(entries),"ZIP inventory")
        for name in names:
            path=PurePosixPath(name);info=archive.getinfo(name)
            need(not path.is_absolute() and ".." not in path.parts and "\\" not in name and ":" not in name,
                 "safe archive member path")
            need(not info.is_dir() and info.file_size==entries[name]["raw_bytes"] and
                 info.external_attr>>16==0o100644,"archive member type and size")
        def read(name):
            raw=archive.read(name)
            need(len(raw)==entries[name]["raw_bytes"] and digest(raw)==entries[name]["raw_sha256"],
                 "selected archive member identity: "+name)
            input_hashes[name]=digest(raw);return raw
        build=json.loads(read("build/build.json"));plan=json.loads(read("build/source/manifest.json"))
        certificate=json.loads(read("build/elf-validation.json"))
        validation_raw=read("run/runs/recovery/validation.json");validation=json.loads(validation_raw)
        need(validation_raw==read("run/runs/replay/validation.json"),"replay validation identity")
        need(validation["status"]=="PHASED_TARGET_DIFFTEST_AND_PLAN_PASS" and
             [r["index"] for r in plan["plan"]]==ORDER and len(plan["rows"])==3 and
             len(validation["samples"])==8 and plan["full_q_calls"]==22,"frozen three-method plan")
        pins=build["software_files"]
        need(len(pins)==106 and pins[TARGET+"/CONTRACT.md"]==TARGET_CONTRACT_SHA and
             pins[TARGET+"/run.py"]=="2743e9757fc466bb6af69b27de7441e37ca07e392521175cf3212e6cae467d18",
             "frozen source closure and exact target checker")
        def check_sources():
            for name,pin in pins.items():need(c.file_digest(repo/name)==pin,"frozen source changed: "+name)
            need(c.file_digest(repo/CONTEXT)==CONTEXT_SHA and c.file_digest(repo/BASE)==BASE_SHA,
                 "unchanged analysis helpers")
        check_sources()
        target=module("phased_cost_target",repo/TARGET/"run.py")
        context=module("phased_cost_context",repo/CONTEXT)
        counter=module("phased_cost_counter",repo/"team/workloads/unified-vdot/check.py")
        observer=module("phased_cost_observer",repo/"team/optimizations/o2/fullcore/analyze.py")
        c.save(output/"controls.json",dict(identity=c.negative_controls(context,counter),temporal=controls()))
        raw=read("build/vdot-perf.elf");need(digest(raw)==ELF_SHA,"fixed build-03 actual ELF")
        need(digest(read("build/vdot-perf.bin"))==BIN_SHA,"fixed executable image")
        elf=target.g.ELF(raw);paths,details=target.paths_for_plan(elf,plan)
        need(details==certificate["paths"],"all actual ELF path certificates")
        hardware=c.bind_hardware(repo,read,entries)
        events,local,t13,trace_identity=trace_inputs(archive,entries,validation["samples"],observer)
    counters=counter.parse_events(t13);counter.walk=lambda stream:stream
    samples=counter.trace_windows(counters,plan,paths)
    need(len(samples)==8,"eight CSR windows")
    for actual,prior in zip(samples,validation["samples"]):
        need(all(prior.get(key)==value for key,value in actual.items()),"original CSR sample equality")
    windows=context.window_records(counters);need(len(windows)==8,"all retirement windows")
    index=context.transaction_index(events)
    commits=[row for _,_,kind,row in events if kind=="COMMIT"]
    expected=[elf.symbols["q_fault_probe"][0]+5*4];phases=[]
    for i,call in enumerate(plan["call_plan"]):
        pcs=[pc for pc,word in paths[call["arm"]] if word&MASK==MATCH]
        phases.append(dict(seq=i,**call,vdot_count=len(pcs),first_commit_index=len(expected)));expected.extend(pcs)
    need(phases==validation["custom_phases"] and [row["pc"] for row in commits]==expected and
         digest(b"".join(struct.pack("<Q",pc) for pc in expected))==validation["all_stage_custom_pc_sha256"],
         "all-stage custom phase and PC identity")
    timed=[row for row in phases if row["stage"]==2];need(len(timed)==8,"eight isolated timed phases")
    results,details_out=[],[]
    for i,(records,sample,step,phase) in enumerate(zip(windows,samples,plan["plan"],timed)):
        row=plan["rows"][step["index"]];start,stop=sample["sample_ticks"][1:3]
        tx=c.bind_transactions(records,index,row["dots"])
        original=commits[phase["first_commit_index"]:phase["first_commit_index"]+phase["vdot_count"]]
        need([(v["commit"],v["pc"],v["rob"]) for v in tx]==
             [(v["cycle"],v["pc"],list(map(int,v["rob"].split(":")))) for v in original],"timed-phase isolation")
        frontier=context.expanded_frontier(records,paths[row["id"]],start)
        fu=c.fu_statistics(tx,local[i],start,stop,hardware["silence_semantics_bound"])
        record=dict(seq=i,label=row["label"],block=step["block"],role=step["role"],
                    cycles=sample["cycles"],instructions=sample["instructions"],sample_ticks=sample["sample_ticks"],fu=fu)
        if tx:
            bound,groups=dependency_groups(frontier,tx,row,elf,start)
            record["supply"]=supply_statistics(bound,local[i],start,stop,hardware["silence_semantics_bound"])
            record["group_spans"]=dict(
                first_enqueue_to_last_commit=c.stats(v["last_commit"]-v["first_enqueue"] for v in groups),
                accept_to_response=c.stats(v["last_response"]-v["first_accept"] for v in groups),
                core_retirement=c.stats(v["last_retire_cycle"]-v["first_retire_cycle"] for v in groups),
                last_core_retire_to_convert=c.stats(v["convert_retire_cycle"]-v["last_retire_cycle"] for v in groups),
                convert_to_add_retire=c.stats(v["add_retire_cycle"]-v["convert_retire_cycle"] for v in groups))
            details_out.append(dict(seq=i,label=row["label"],sample_start=start,transactions=bound,groups=groups))
        else:
            grouped=c.group_diagnostics(frontier,tx,row,elf)
            record["group_retirement_envelope"]=grouped["group_retirement_envelope"]
            details_out.append(dict(seq=i,label=row["label"],sample_start=start,**grouped))
        results.append(record)
    check_sources()
    need(c.file_digest(repo/hardware["observer_source_path"])==hardware["observer_source_sha256"],
         "unchanged source-bound observation semantics")
    raw=json.dumps(details_out,sort_keys=True,separators=(",",":")).encode()
    compressed=gzip.compress(raw,compresslevel=9,mtime=0);(output/"coordinates.json.gz").write_bytes(compressed)
    result=dict(status="PHASED_COST_DIAGNOSTIC_PASS",contract=CONTRACT,windows=results,
        archive_pins=archive_pins,seal_sha256=seal_sha,fresh_source_result_sha256=seal["fresh_source_result_sha256"],
        original_selection=validation["selection"],selected_input_sha256=input_hashes,trace_identity=trace_identity,
        source_files_checked=len(pins),frozen_sources_unchanged=True,context_helper_sha256=CONTEXT_SHA,
        published_helper_sha256=BASE_SHA,hardware_observation_binding=hardware,
        coordinates=dict(raw_bytes=len(raw),raw_sha256=digest(raw),stored_bytes=len(compressed),stored_sha256=digest(compressed)),
        new_emu_runs=0,hardware_changed=False,stable_default_changed=False,new_performance_qualification=False,
        scope="fixed synthetic prepacked Q; global retirement and FU-boundary coordinates; no exclusive-cycle attribution",
        unavailable_causality=["operand ready cycle before retirement","issue selection and RF-port arbitration",
            "physical-register free-list pressure","load-cache latency attribution","FP issue/completion","token/model quality/ASIC"],
        diagnostics_seconds=time.time()-started)
    c.save(output/"result.json",result);return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("repo","archive","seal","fresh-audit","output"):p.add_argument("--"+key,type=Path,required=True)
    p.add_argument("--seal-sha256",required=True);a=p.parse_args()
    output=a.output.resolve();repo=a.repo.resolve()
    roots=[repo,a.archive.resolve(),a.seal.resolve(),a.fresh_audit.resolve()]
    need(not output.exists() and all(output!=x and x not in output.parents for x in roots),"fresh output outside inputs")
    need(re.fullmatch(r"[0-9a-f]{64}",a.seal_sha256) is not None,"explicit seal SHA256")
    output.mkdir(parents=True,exist_ok=False)
    if hasattr(os,"sched_setaffinity"):os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])
    def save(name,value):
        (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    save("invocation.json",dict(argv=sys.argv,started_epoch=time.time(),analyzer_sha256=digest(Path(__file__).read_bytes()),
        cpu_affinity=sorted(os.sched_getaffinity(0)) if hasattr(os,"sched_getaffinity") else None))
    try:result=analyze(repo,a.archive.resolve(),a.seal.resolve(),a.seal_sha256,a.fresh_audit.resolve(),output)
    except Exception as error:
        save("failure.json",dict(status="PHASED_COST_REJECTED",exception=type(error).__name__,error=str(error),new_emu_runs=0));raise
    print(json.dumps(dict(status=result["status"],output=str(output),windows=[dict(seq=w["seq"],label=w["label"],
        cycles=w["cycles"],supply=w.get("supply",{}).get("producers_retired_wait_union_cycles"),
        output_stalls=w["fu"]["target_output_stall_events"]) for w in result["windows"]]),indent=2))


if __name__=="__main__":main()
