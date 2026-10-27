#!/usr/bin/env python3
"""Read-only R3 metadata audit; writes only the caller-selected new report file."""
from pathlib import Path
import argparse, collections, gzip, hashlib, json, re, subprocess

if not __debug__:
    raise RuntimeError("Run without python -O: integrity checks require assertions.")

REPO=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
LOCAL=Path("/home/riscv/riscv-lab/o2-h1-result32-20261021")
CORE=Path("/home/riscv/riscv-lab/o2-h1-fullcore-20261021")
EXPECTED_HEAD="4669c487f3024ee5fce514c37270297f99066b2a"
LOCAL_MANIFEST_SHA256="73fe5f79d3209937a3278a16f8bfc70f90333fc46657de161810bcf9c2d8974a"
CORE_MANIFEST_SHA256="41eb086b88d5c6d5e8ff4f2f25310396ea2fad580853ed08d56f1891ab9ca105"
def digest(data): return hashlib.sha256(data).hexdigest()
def identity(path): return {"path":str(path),"bytes":path.stat().st_size,"sha256":digest(path.read_bytes())}
def sealed_local(name):
    archive=REPO/"team/optimizations/o2/result-width/h1/evidence/20261021-local"
    raw_manifest=(archive/"manifest.json").read_bytes()
    assert digest(raw_manifest)==LOCAL_MANIFEST_SHA256, "local archive manifest identity mismatch"
    manifest=json.loads(raw_manifest)
    e=next(x for x in manifest["entries"] if x["path"]==name)
    packed=(archive/"files"/e["stored"]).read_bytes()
    assert digest(packed)==e["stored_sha256"]
    raw=gzip.decompress(packed) if e["gzip"] else packed
    assert digest(raw)==e["sha256"] and len(raw)==e["bytes"]
    disk=(LOCAL/name).read_bytes()
    assert disk==raw
    return raw,{"archive":str(archive),"entry":e,"manifest":identity(archive/"manifest.json")}

def audit_map(name,prefix):
    data,provenance=sealed_local(name+"/mapped.json")
    modules=json.loads(data)["modules"]
    top,m=max(modules.items(),key=lambda pair:len(pair[1].get("cells",{})))
    qdrivers=collections.defaultdict(set)
    for cn,c in m["cells"].items():
        if c["type"].startswith("DFF"):
            for port in ("Q","QN"):
                for b in c["connections"].get(port,[]): qdrivers[b].add(cn)
    names=m["netnames"]
    groups={}
    for group,suffix in {
      "p_vpu":"pCtrl_vpu_", "r_vpu":"rPacket_ctrl_vpu_",
      "p_perf":"pPerf_", "r_perf":"rPacket_perfDebugInfo_",
      "p_ctrl_all":"pCtrl_","r_ctrl_all":"rPacket_ctrl_",
      "p_products":"pProducts_","r_result":"rPacket_res_data",
      "p_valid":"pValid","r_valid":"rValid"}.items():
        selected={n:v for n,v in names.items() if n.startswith(prefix+suffix)}
        bits=set(b for v in selected.values() for b in v["bits"] if isinstance(b,int))
        cells=set(c for b in bits for c in qdrivers.get(b,set()))
        assert all(len(qdrivers.get(b,set()))==1 for b in bits), (name,group)
        groups[group]={
          "net_count":len(selected),"unique_bits":len(bits),"unique_dff":len(cells),
          "cell_types":dict(collections.Counter(m["cells"][c]["type"] for c in cells)),
          "nets":{n:{"width":len(v["bits"]),"bits":v["bits"],
                     "dff_cells":sorted({c for b in v["bits"] for c in qdrivers.get(b,set())})}
                  for n,v in selected.items()}}
    # ctrl groups include vpu; avoid adding the overlapping vpu groups again.
    leaves=["p_ctrl_all","r_ctrl_all","p_perf","r_perf","p_products","r_result","p_valid","r_valid"]
    ids=[{c for v in groups[g]["nets"].values() for c in v["dff_cells"]} for g in leaves]
    assert sum(map(len,ids))==len(set.union(*ids))
    return {"top":top,"provenance":provenance,"all_boundary_dff":sum(
      c["type"].startswith("DFF") for c in m["cells"].values()),
      "vdot_named_dff":len(set.union(*ids)),"groups":groups}

def main():
    global REPO, LOCAL, CORE
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",type=Path,default=REPO)
    parser.add_argument("--local-cost",type=Path,default=LOCAL)
    parser.add_argument("--core",type=Path,default=CORE)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    REPO=args.repo.resolve();LOCAL=args.local_cost.resolve();CORE=args.core.resolve()
    output=args.output;assert not output.exists(),"refuse overwrite"
    head=subprocess.check_output(["git","-C",str(REPO),"rev-parse","HEAD"],text=True).strip()
    assert head==EXPECTED_HEAD, head
    paths=[
      "src/main/scala/xiangshan/Bundle.scala","src/main/scala/xiangshan/backend/Bundles.scala",
      "src/main/scala/xiangshan/backend/fu/FuncUnit.scala",
      "src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala",
      "src/main/scala/xiangshan/backend/exu/ExeUnit.scala",
      "src/main/scala/xiangshan/backend/datapath/DataPath.scala",
      "src/main/scala/xiangshan/backend/datapath/WbArbiter.scala",
      "src/main/scala/xiangshan/backend/CtrlBlock.scala",
      "src/main/scala/xiangshan/backend/rob/Rob.scala",
      "src/main/scala/xiangshan/backend/Backend.scala",
      "src/main/scala/xiangshan/backend/issue/IssueQueue.scala",
      "team/optimizations/o4/GenerateVDotCost.scala",
      "team/optimizations/o2/parent/GenerateVDotElasticParent.scala",
      "team/optimizations/o2/parent/parent_test.cpp"]
    sources=[]
    for name in paths:
        info=identity(REPO/name)
        info["git_blob"]=subprocess.check_output(["git","-C",str(REPO),"rev-parse",f"{head}:{name}"],text=True).strip()
        sources.append(info)
    maps={"fu":audit_map("fu-map-01","dut."),"parent":audit_map("parent-map-01","dut.Vdot.")}
    core_archive=REPO/"team/optimizations/o2/result-width/h1/fullcore/evidence/20261021-fullcore"
    core_manifest_raw=(core_archive/"archive-manifest.json").read_bytes()
    assert digest(core_manifest_raw)==CORE_MANIFEST_SHA256, "core archive manifest identity mismatch"
    manifest=json.loads(core_manifest_raw)
    def verified_core_file(relative):
        suffix="/"+relative
        e=next(x for x in manifest["files"] if x["original"].endswith(suffix))
        packed=(core_archive/e["stored"]).read_bytes()
        assert digest(packed)==e["stored_sha256"]
        raw=gzip.decompress(packed) if e["encoding"]=="gzip" else packed
        assert digest(raw)==e["raw_sha256"] and len(raw)==e["raw_bytes"]
        assert raw==(CORE/relative).read_bytes(), relative
        return raw,e
    generated=json.loads(verified_core_file("build-01/generated-artifacts.json")[0])
    build_state=json.loads(verified_core_file("build-01/build-state.json")[0])
    selected=["build/rtl/VDotElastic.sv","build/rtl/ExeUnit_17.sv","build/rtl/ExuBlock_2.sv",
              "build/rtl/DataPath.sv","build/rtl/Backend.sv"]
    generated_checks=[]
    for name in selected:
        item=next(x for x in generated if x["path"]==name)
        info=identity(REPO/name); assert info["sha256"]==item["sha256"]
        generated_checks.append(info)
    sv=(REPO/"build/rtl/VDotElastic.sv").read_text()
    regs=[{"name":n,"bits":int(ms or "0")+1} for ms,n in re.findall(
      r"^\s*reg\s+(?:\[(\d+):0\]\s+)?(pPerf_\w+|rPacket_perfDebugInfo_\w+|pCtrl_vpu_\w+|rPacket_ctrl_vpu_\w+);",sv,re.M)]
    datalines=(REPO/"build/rtl/DataPath.sv").read_text().splitlines()
    zero_assignments=[{"line":i+1,"text":line.strip()} for i,line in enumerate(datalines)
                      if re.search(r"assign io_toVecExu_2_0_bits_perfDebugInfo_",line)]
    assert len(zero_assignments)==10 and all(re.search(r"= (1|64)'h0;",x["text"]) for x in zero_assignments)
    cpp=REPO/"build/emu-compile/VSimTop___024root.h"
    cpptext=cpp.read_text()
    cpp_fields=[{"line":i+1,"text":line.strip()} for i,line in enumerate(cpptext.splitlines())
                if re.search(r"Vdot__DOT__(?:pPerf_|rPacket_perfDebugInfo_)\w+;",line)]
    assert len(cpp_fields)==20
    # Raw H1 fullcore accept observations, each checked against its archived SHA.
    fields=[("eliminatedMove",1)]+[(f,64) for f in (
      "renameTime","dispatchTime","enqRsTime","selectTime","issueTime","writebackTime",
      "runahead_checkpoint_id","tlbFirstReqTime","tlbRespTime")]
    stats={f:{"nonzero":0,"min":None,"max":0} for f,_ in fields};count=0;logs=[]
    for path in sorted((CORE/"core-01").glob("*/run.log")):
        if path.parent.name in ("negative-vdot","hello-vadd"): continue
        raw,e=verified_core_file(path.relative_to(CORE).as_posix())
        n=0
        for line in raw.decode().splitlines():
            if not line.startswith("O2_ACCEPT "): continue
            match=re.search(r"perf=0x([0-9a-fA-F]+)",line);assert match
            value=int(match[1],16);n+=1;count+=1
            for f,bits in reversed(fields):
                v=value&((1<<bits)-1);value>>=bits
                st=stats[f];st["nonzero"]+=int(v!=0);st["max"]=max(st["max"],v)
                st["min"]=v if st["min"] is None else min(st["min"],v)
            assert value==0
        logs.append({"path":str(path),"accepts":n,"archive_entry":e})
    assert len(logs)==10, f"expected 10 sealed normal logs, found {len(logs)}"
    assert count==3137, f"expected 3137 accepts, found {count}"
    assert all(x["nonzero"]==0 and x["min"]==0 and x["max"]==0 for x in stats.values()), "unexpected nonzero perf field"
    result={"status":"R3_METADATA_READONLY_AUDIT_PASS","head":head,"sources":sources,
      "input_roots":{"repo":str(REPO),"local_cost":str(LOCAL),"core":str(CORE)},
      "pinned_manifests":{"local":LOCAL_MANIFEST_SHA256,"core":CORE_MANIFEST_SHA256},
      "mapped":maps,"fullcore":{
        "build_state":build_state,
        "generated_hash_checks":generated_checks,"declared_metadata_registers":regs,
        "datapath_vfex4_zero_assignments":zero_assignments,
        "compiled_header":identity(cpp),"compiled_fields":cpp_fields,
        "accept_trace":{"count":count,"logs":logs,"fields":stats},
        "scope":"observe profile; SV declarations and C++ state are not a mapped whole-core DFF count"},
      "limitations":[
        "Public FU/parent harness outputs keep arbitrary perf inputs observable.",
        "No new synthesis, STA, simulation, runtime or hardware mutation.",
        "Mapped DFF categories are existing cost; not candidate net area savings.",
        "All-zero input in this generated core does not authorize weakening public nonzero-identity contract.",
        "Trace sample statistics do not prove constants; generated DataPath assignments provide the independent constant-input evidence."]}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"fu_dff":maps["fu"]["vdot_named_dff"],
      "parent_vdot_dff":maps["parent"]["vdot_named_dff"],"accepts":count,"output":str(output)}))
if __name__=="__main__": main()
