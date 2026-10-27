#!/usr/bin/env python3
"""Read sealed H1/O4 netlists/reports only. No synthesis, simulation or repo writes."""
import argparse
import csv
import gzip
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    if not __debug__:
        raise RuntimeError("Run without -O/-OO: extraction validation requires assertions")
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    actual_head = subprocess.check_output(["git", "-C", str(args.repo), "rev-parse", "HEAD"], text=True).strip()
    h1 = args.repo / "team/optimizations/o2/result-width/h1/evidence/20261021-local"
    o4 = args.repo / "team/optimizations/o4/evidence/20261020-cost"
    inputs = {}
    manifests = {}
    expected_manifests = {
        h1: "73fe5f79d3209937a3278a16f8bfc70f90333fc46657de161810bcf9c2d8974a",
        o4: "9f95c19b737b0428afca36686aabd1454d7fb44880040f2bf41109b71c39c0a1",
    }
    for root in (h1, o4):
        raw = (root / "manifest.json").read_bytes()
        assert sha(raw) == expected_manifests[root], "Pinned sealed manifest mismatch: " + str(root)
        manifests[root] = {v["path"]: v for v in json.loads(raw)["entries"]}
        inputs[str((root / "manifest.json").relative_to(args.repo))] = sha(raw)
    def read(root, path, as_json=False):
        e = manifests[root][path]
        p = root / "files" / e["stored"]
        stored = p.read_bytes()
        assert sha(stored) == e["stored_sha256"] and len(stored) == e["stored_bytes"], p
        raw = gzip.decompress(stored) if e["gzip"] else stored
        assert sha(raw) == e["sha256"] and len(raw) == e["bytes"], p
        inputs[str(p.relative_to(args.repo))] = sha(stored)
        return json.loads(raw) if as_json else raw.decode("utf-8")
    lib = read(o4, "library/NangateOpenCellLibrary_typical.lib")
    areas = {k: float(v) for k, v in re.findall(
        r"cell\s*\(\s*(\w+)\s*\)\s*\{.*?\barea\s*:\s*([0-9.eE+-]+)", lib, re.S)}
    old = read(h1, "cost-comparison-01/summary.json", True)
    results = {}
    timing_rows = []
    for boundary in ("fu", "parent"):
        prefix = "dut." if boundary == "fu" else "dut.Vdot."
        top = "CommonFuCostTop" if boundary == "fu" else "CommonParentCostTop"
        summary = read(h1, f"{boundary}-map-01/summary.json", True)
        module = read(h1, f"{boundary}-map-01/mapped.json", True)["modules"][top]
        cells = module["cells"]
        hist = Counter(c["type"] for c in cells.values())
        assert dict(hist) == summary["cell_histogram"]
        area = sum(areas[k] * v for k, v in hist.items())
        assert abs(area - summary["cell_area_sum"]) < 1e-5
        drivers, consumers = {}, defaultdict(set)
        for n,c in cells.items():
            for pin,d in c["port_directions"].items():
                for bit in c["connections"][pin]:
                    if d == "output" and isinstance(bit,int):
                        assert bit not in drivers
                        drivers[bit] = (n,pin)
                    elif d == "input":
                        consumers[bit].add((n,pin))
        portsout = {b for p in module["ports"].values() if p["direction"]=="output" for b in p["bits"]}
        groups = {}
        patterns = {"products": "pProducts_", "result": "rPacket_res_data",
                    "stage_state": "[pr]Valid$", "p_control": "pCtrl_",
                    "p_perf": "pPerf_", "r_control": "rPacket_ctrl_",
                    "r_perf": "rPacket_perfDebugInfo_"}
        for group, pattern in patterns.items():
            target = set()
            for name,net in module["netnames"].items():
                if name.startswith(prefix) and re.search(pattern,name[len(prefix):]):
                    for b in net["bits"]:
                        if b in drivers:
                            n,pin = drivers[b]
                            if pin=="Q" and cells[n]["type"]=="DFF_X1":
                                target.add(n)
            muxes = set()
            unmatched = Counter()
            for n in target:
                c=cells[n]; q=c["connections"]["Q"][0]; d=c["connections"]["D"][0]
                dn,dp=drivers.get(d,("",""))
                dc=cells.get(dn,{})
                if (dc.get("type")=="MUX2_X1" and
                    q in dc["connections"].get("A",[])+dc["connections"].get("B",[]) and
                    consumers[d] == {(n,"D")} and d not in portsout):
                    muxes.add(dn)
                else:
                    unmatched[dc.get("type","unknown")]+=1
            dff_area = sum(areas[cells[n]["type"]] for n in target)
            mux_area = sum(areas[cells[n]["type"]] for n in muxes)
            groups[group] = {"dff_count":len(target),"dff_area":round(dff_area,6),
                "exclusive_direct_hold_mux_count":len(muxes),"exclusive_direct_hold_mux_area":round(mux_area,6),
                "dff_plus_identified_mux_local_area":round(dff_area+mux_area,6),
                "direct_d_driver_without_verified_own_q_exclusive_mux":dict(unmatched)}
        expected=old["results"][boundary]["candidate"]["structure_register_groups"]["groups"]
        assert {k:v["dff_count"] for k,v in groups.items()}==expected
        sta=read(h1,f"{boundary}-sta-01/summary.json",True)
        binding=read(h1,"parent-sta-01/instance-binding.json",True) if boundary=="parent" else None
        # FU mapped.v has write_verilog canonical instance names, while parent STA uses explicit binding.
        if boundary=="fu":
            vt=read(h1,"fu-map-01/mapped.v")
            fu_written_to_original={}
            # The Yosys mapped JSON has original instance names; mapped.v contains attributes src naming
            # no safe automatic binding is assumed. Raw FU path names/net aliases remain in report.
        endcells=set()
        for profile in sta["profiles"]:
            for path,v in profile["paths"].items():
                reportpath=f"{boundary}-sta-01/{profile['profile']}/{path}.rpt"
                text=read(h1,reportpath)
                row={"boundary":boundary,"profile":profile["profile"],"period_ns":profile["period_ns"],
                     "load_ff":profile["load_ff"],"path":path,**v,"report":str((h1/"files"/reportpath).relative_to(args.repo))}
                timing_rows.append(row)
                if binding:
                    endcells.update(re.findall(r"^(?:Startpoint|Endpoint): (c\d+)",text,re.M))
        gate_names={n for n,c in cells.items() if c["type"]=="CLKGATETST_X1"}
        if binding:
            gate_canonical={c for c,n in binding.items() if n in gate_names}
            endcells |= gate_canonical
            bits=defaultdict(list)
            aliases={c:{"mapped_instance":binding[c],"type":cells[binding[c]]["type"],"pins":{}} for c in endcells}
            for c in endcells:
                cell=cells[binding[c]]
                for pin in ("Q","E","GCK"):
                    for b in cell["connections"].get(pin,[]):
                        bits[b].append((c,pin))
            for n,net in module["netnames"].items():
                if n.startswith("$"):continue
                for i,b in enumerate(net["bits"]):
                    for c,pin in bits.get(b,[]):
                        aliases[c]["pins"].setdefault(pin,[]).append(n+(f"[{i}]" if len(net["bits"])>1 else ""))
            for row in timing_rows:
                if row["boundary"]!=boundary:continue
                for what in ("startpoint","endpoint"):
                    c=row[what].split(" ")[0]
                    row[what+"_binding"]=aliases.get(c, {})
            path=read(h1,"parent-sta-01/nominal/gate_enable.rpt")
            datapart=path.split("data arrival time")[0]
            pathcells=set(re.findall(r"[v^] (c\d+)/[^\s]+ \(",datapart))
            pathhist=Counter(cells[binding[c]]["type"] for c in pathcells)
            # Count unique combinational cell arc delays, excluding input pin wire delay and FF Q.
            gate_detail={"worst_gate_path_cell_histogram":dict(pathhist),"bindings":aliases}
        else:
            gate_detail={"note":"FU original report signal aliases available; no guessed canonical cell binding"}
        results[boundary]={"area":round(area,6),"cell_count":len(cells),"dff_count":hist["DFF_X1"],
             "icg_count":hist["CLKGATETST_X1"],"register_groups":groups,"path_binding":gate_detail,
             "baseline_area":old["results"][boundary]["baseline"]["area"],
             "baseline_dff_count":old["results"][boundary]["baseline"]["dff_count"]}
        del module,cells,drivers,consumers
    result={"status":"R3_READONLY_TIMING_EXTRACTION_PASS",
        "actual_head": actual_head,
        "analyzed_head":"4669c487f3024ee5fce514c37270297f99066b2a",
        "identity_note": "actual_head records the Git HEAD at extraction; analyzed_head is the review anchor, not a newly simulated source identity. Actual analyzed hardware inputs are historical H1/O4 sealed snapshots bound by pinned manifests and per-file hashes.",
        "scope":"Existing sealed H1/O4 common-interface local mappings; no new hardware run",
        "library_cell_area":{"DFF_X1":areas["DFF_X1"],"MUX2_X1":areas["MUX2_X1"],"CLKGATETST_X1":areas["CLKGATETST_X1"]},
        "warning":"Register+exclusive direct own-Q mux cost is existing mapped local attribution, NOT realizable saving, full-core area, power or Fmax. Shared control/buffers/loads not attributed.",
        "boundaries":results,"timing_rows":timing_rows,"inputs_sha256":inputs}
    (args.output/"timing-cost-extraction.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    columns=["boundary","profile","period_ns","load_ff","path","arrival_ns","slack_ns","startpoint","endpoint","report"]
    with (args.output/"timing-all-profiles.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction="ignore");w.writeheader();w.writerows(timing_rows)
    print(result["status"],"read_inputs",len(inputs),"paths",len(timing_rows))
    for b,v in results.items():
        print(b,"area",v["area"],"DFF",v["dff_count"])
        print(json.dumps(v["register_groups"],ensure_ascii=False))
if __name__=="__main__":
    main()
