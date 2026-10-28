"""Read-only attribution and fixed-endpoint STA on the sealed R3 parent maps."""
import argparse, collections, datetime, hashlib, json, re, subprocess
from pathlib import Path

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(p, x):
    Path(p).write_text(json.dumps(x, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def need(ok, msg):
    if not ok:
        raise ValueError(msg)

def stamp():
    return datetime.datetime.now().astimezone().isoformat()

class Design:
    def __init__(self, root):
        self.root = root
        self.sta = root / "parent-sta-01"
        self.mapping = json.loads((root / "parent-map-01/mapped.json").read_text())["modules"]["CommonParentCostTop"]
        self.binding = json.loads((self.sta / "instance-binding.json").read_text())
        self.reverse = {v: k for k, v in self.binding.items()}
        self.names = collections.defaultdict(list)
        for name, desc in self.mapping["netnames"].items():
            if not name.startswith("dut."):
                continue
            for idx, bit in enumerate(desc["bits"]):
                if isinstance(bit, int):
                    self.names[bit].append(name + (f"[{idx}]" if len(desc["bits"]) > 1 else ""))
        self.drivers = {}
        for name, cell in self.mapping["cells"].items():
            for pin, direction in cell["port_directions"].items():
                if direction == "output":
                    for bit in cell["connections"][pin]:
                        if isinstance(bit, int):
                            need(bit not in self.drivers, f"multiple drivers {bit}")
                            self.drivers[bit] = (name, pin)
    def net_bit(self, name):
        n = self.mapping["netnames"]
        if name in n and len(n[name]["bits"]) == 1:
            return n[name]["bits"][0]
        m = re.fullmatch(r"(.*)\[(\d+)\]", name)
        need(m and m[1] in n, f"missing semantic net {name}")
        return n[m[1]]["bits"][int(m[2])]
    def reg(self, semantic):
        bit = self.net_bit(semantic)
        c, pin = self.drivers[bit]
        need(pin == "Q" and self.mapping["cells"][c]["type"].startswith("DFF"), semantic)
        return self.reverse[c]
    def pin_names(self, canonical, pin):
        c = self.mapping["cells"][self.binding[canonical]]
        return sorted({n for b in c["connections"][pin] for n in self.names.get(b, [])})
    def parse(self, path):
        text = path.read_text()
        need("data arrival time" in text and "slack (" in text, f"no valid timing path {path}")
        rows = []
        for line in text.split("data arrival time")[0].splitlines():
            m = re.match(r"\s+([-0-9.]+)\s+([-0-9.]+)\s+([-0-9.]+)\s+[\^v]\s+(c\d+)/(\w+)\s+\((\w+)\)", line)
            if not m:
                continue
            slew, delay, at, canon, pin, typ = m.groups()
            cell = self.mapping["cells"][self.binding[canon]]
            need(cell["type"] == typ, "type binding mismatch")
            if cell["port_directions"][pin] != "output":
                continue
            rows.append(dict(cell=canon, original_cell=self.binding[canon], pin=pin, type=typ,
                             delay_ns=float(delay), arrival_ns=float(at), slew_ns=float(slew),
                             rtl_nets=self.pin_names(canon, pin)))
        arrival = float(re.search(r"([-0-9.]+)\s+data arrival time", text)[1])
        slack = float(re.search(r"([-0-9.]+)\s+slack \(", text)[1])
        return dict(startpoint=re.search(r"Startpoint: ([^\n]+)", text)[1],
                    endpoint=re.search(r"Endpoint: ([^\n]+)", text)[1],
                    arrival_ns=arrival, slack_ns=slack, stages=rows,
                    output_cell_count=len(rows),
                    buffer_count=sum(x["type"].startswith("BUF") for x in rows),
                    buffer_delay_ns=sum(x["delay_ns"] for x in rows if x["type"].startswith("BUF")),
                    hold_register_on_path=any(any(n in ("dut.uncer_en_reg","dut.uncer_en_reg_1") for n in x["rtl_nets"]) for x in rows),
                    divbusy_register_on_path=any("dut.elasticDivOccupied_divBusy" in x["rtl_nets"] for x in rows))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--before", type=Path, required=True)
    p.add_argument("--after", type=Path, required=True)
    p.add_argument("--tools", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(exist_ok=False)
    state = dict(status="running", started=stamp(), steps=[])
    save(a.output/"state.json", state)
    designs = {k: Design(v) for k,v in [("before",a.before),("after",a.after)]}
    exe = a.tools/"tools/root/usr/bin/sta"
    identities = json.loads((a.tools/"tools/executable-identities.json").read_text())["sta"]
    need(sha(exe) == identities["sha256"], "STA executable changed")
    for path,digest in identities["shared_library_sha256"].items():
        need(sha(path)==digest, "STA library changed "+path)
    inputs = {str(exe): sha(exe), str(Path(__file__).resolve()):sha(__file__)}
    inputs.update(identities["shared_library_sha256"])
    lib = a.tools/"library/NangateOpenCellLibrary_typical.lib"
    inputs[str(lib)] = sha(lib)
    for d in designs.values():
        paths = [d.root/"parent-map-01/mapped.json", d.sta/"instance-binding.json",d.sta/"sta-canonical.v",
                 d.sta/"nominal/timing.tcl",d.root/"parent-cost-01/rtl/ExeUnit.sv"]
        paths += list((d.sta/"nominal").glob("*.rpt"))
        for path in paths:
            inputs[str(path)] = sha(path)
    save(a.output/"inputs.json", inputs)
    try:
        original = {k:{p.stem:d.parse(p) for p in (d.sta/"nominal").glob("*.rpt") if p.stem != "setup-checks"} for k,d in designs.items()}
        save(a.output/"original-paths.json", original)
        # Bind both versions' original worst paths to semantic register names.
        anchors = {}
        for version in designs:
            d = designs[version]
            for kind in ("r2r","i2r"):
                path = original[version][kind]
                end = path["endpoint"].split()[0]
                aliases = d.pin_names(end,"Q")
                common = [n for n in aliases if all(any(n in names for names in other.names.values()) for other in designs.values())]
                need(common, "no shared endpoint "+kind)
                endpoint = common[0]
                start = path["startpoint"].split()[0]
                if start in d.binding:
                    aliases = d.pin_names(start,"Q")
                    common = [n for n in aliases if all(any(n in names for names in other.names.values()) for other in designs.values())]
                    need(common, "no shared startpoint")
                    start = common[0]
                anchors[version+"_"+kind] = dict(start=start, endpoint=endpoint, start_is_reg=kind=="r2r")
        save(a.output/"anchors.json", anchors)
        results = {}
        for version,d in designs.items():
            out = a.output/version
            out.mkdir()
            # Copy all original constraints verbatim up to the first report side effect.
            lines = (d.sta/"nominal/timing.tcl").read_text().splitlines()
            stop = next(i for i,l in enumerate(lines) if l.startswith("check_setup "))
            tcl = lines[:stop]
            tcl += ["set q [all_registers -output_pins]","set d [all_registers -data_pins]"]
            queries = {}
            for label,semantic in [("float_hold","dut.uncer_en_reg"),("int_hold","dut.uncer_en_reg_1"),("div_busy","dut.elasticDivOccupied_divBusy")]:
                reg = d.reg(semantic)
                for source,expr in [("regs","$q"),("inputs","$inputs"),("flush","[get_ports {io_flush*}]")]:
                    queries[label+"_"+source] = (expr, "[get_pins {"+reg+"/D}]")
            for idx in range(3):
                cell = "dut.ClockGate"+("_"+str(idx) if idx else "")+".impl"
                canonical=d.reverse[cell]
                queries["icg"+str(idx)+"_all"]=(None,"[get_pins {"+canonical+"/E}]")
                if idx<2:
                    semantic="dut.uncer_en_reg"+("_1" if idx else "")
                    queries["icg"+str(idx)+"_hold"]=("[get_pins {"+d.reg(semantic)+"/Q}]","[get_pins {"+canonical+"/E}]")
            for name,x in anchors.items():
                start = "[get_pins {"+d.reg(x["start"])+"/Q}]" if x["start_is_reg"] else "[get_ports {"+x["start"]+"}]"
                queries["fixed_"+name]=(start,"[get_pins {"+d.reg(x["endpoint"])+"/D}]")
            for name,(frm,to) in queries.items():
                tcl += [f"report_checks "+(f"-from {frm} " if frm else "")+f"-to {to} -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {{capacitance slew input_pin net}} -digits 6 -no_line_splits > {out/(name+'.rpt')}"]
            tcl += ['puts "R3_TARGETED_STA_COMPLETE"',"exit"]
            (out/"timing.tcl").write_text("\n".join(tcl)+"\n")
            save(out/"queries.json", queries)
            cmd=[str(exe),"-no_init","-exit",str(out/"timing.tcl")]
            step=dict(version=version,command=cmd,started=stamp(),status="running")
            state["steps"].append(step);save(a.output/"state.json",state)
            print("START",version,flush=True)
            with (out/"sta.log").open("xb") as log:
                rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=300).returncode
            step.update(exit_code=rc,finished=stamp(),status="passed" if rc==0 else "failed")
            save(out/"run.json",step)
            log=(out/"sta.log").read_text()
            need(rc==0 and "R3_TARGETED_STA_COMPLETE" in log and not re.search(r"(?im)^Error",log),"STA failure")
            results[version] = {n:d.parse(out/(n+".rpt")) for n in queries}
            save(out/"paths.json",results[version])
            save(a.output/"state.json",state)
            print("PASS",version,flush=True)
        for path,h in inputs.items():
            need(sha(path)==h,"input changed "+path)
        pairs={n:dict(before_arrival_ns=results["before"][n]["arrival_ns"],after_arrival_ns=results["after"][n]["arrival_ns"],
                      delta_ps=round(1000*(results["after"][n]["arrival_ns"]-results["before"][n]["arrival_ns"]),3),
                      after_slack_ns=results["after"][n]["slack_ns"]) for n in results["before"]}
        save(a.output/"comparison.json",dict(status="R3_TARGETED_STA_REVIEW_PASS",paths=pairs,input_sha_unchanged=True,
              scope="Same fixed parent maps/nominal constraints; no synthesis, RTL change, EMU, or post-layout qualification"))
        state.update(status="R3_TARGETED_STA_REVIEW_PASS",finished=stamp(),input_sha_unchanged=True)
        save(a.output/"state.json",state)
        print(json.dumps(pairs,indent=2),flush=True)
    except BaseException as e:
        state.update(status="failed",error=repr(e),finished=stamp())
        save(a.output/"state.json",state)
        raise

if __name__=="__main__":
    main()
