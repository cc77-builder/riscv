"""Read-only mapped graph and buffer-tree attribution for frozen C1/baseline."""
import argparse, collections, hashlib, importlib.util, json, re
from pathlib import Path

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok, text):
    if not ok: raise ValueError(text)
def groups(text, name):
    pattern=re.compile(r"\b"+name+r"\s*\(\s*([^()]+?)\s*\)\s*\{")
    for match in pattern.finditer(text):
        start=match.end();depth=1;i=start
        while depth:
            if text[i]=="{": depth+=1
            if text[i]=="}": depth-=1
            i+=1
        yield match[1].strip().strip('"'), text[start:i-1]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--before",type=Path,required=True);p.add_argument("--after",type=Path,required=True)
    p.add_argument("--repo",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();need(not a.output.exists(),"new output required");a.output.mkdir()
    helper=a.repo/"team/optimizations/o2/r3-div-gate/timing-review/review.py"
    spec=importlib.util.spec_from_file_location("review",helper);review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
    lib=Path("/home/riscv/riscv-lab/o4-cost-20261020/library/NangateOpenCellLibrary_typical.lib")
    libtext=lib.read_text();need(re.search(r"capacitive_load_unit\s*\(1,ff\)",libtext),"cap unit")
    caps={}
    for cell,block in groups(libtext,"cell"):
        for pin,body in groups(block,"pin"):
            match=re.search(r"(?m)^\s*capacitance\s*:\s*([0-9.eE+-]+)",body)
            if match:caps[cell,pin]=float(match[1])
    pins={str(helper):sha(helper),str(lib):sha(lib),str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
    aggregate={}
    for version,root in [("before",a.before),("after",a.after)]:
        d=review.Design(root);cells=d.mapping["cells"]
        for rel in ["parent-map-01/mapped.json","parent-sta-01/instance-binding.json","parent-cost-01/rtl/ExeUnit.sv"]:
            f=root/rel;pins[str(f)]=sha(f)
        reportroot=a.after/"screen-01"/version/"nominal"
        report=reportroot/"icg1.rpt";pins[str(report)]=sha(report)
        path=d.parse(report)
        sinks=collections.defaultdict(list)
        for name,c in cells.items():
            for pin,direction in c["port_directions"].items():
                if direction=="input":
                    for bit in c["connections"][pin]:
                        if isinstance(bit,int):sinks[bit].append((name,pin))
        def sink_info(cell,pin):
            c=cells[cell]
            aliases=sorted({n for q,direction in c["port_directions"].items() if direction=="output"
                             for bit in c["connections"][q] for n in d.names.get(bit,[])})
            return dict(cell=d.reverse[cell],original_cell=cell,type=c["type"],pin=pin,
                        cap_ff=caps.get((c["type"],pin)),output_aliases=aliases)
        def buffer_tree(start):
            # Only identity BUF cells; stop at INV/logic/FF/ICG. No Boolean-dependency assumption.
            visited=set();bufs=set();leaves=set();stack=[(start,0)];depth=0
            while stack:
                bit,n=stack.pop()
                if bit in visited:continue
                visited.add(bit);depth=max(depth,n)
                for cell,pin in sinks[bit]:
                    c=cells[cell]
                    if c["type"].startswith("BUF") and pin=="A":
                        bufs.add(cell)
                        for q,di in c["port_directions"].items():
                            if di=="output":
                                for b in c["connections"][q]:stack.append((b,n+1))
                    else:leaves.add((cell,pin))
            infos=[sink_info(*x) for x in sorted(leaves)]
            return dict(buffer_count=len(bufs),max_depth=depth,terminal_count=len(leaves),
                        terminal_types=dict(collections.Counter(x["type"] for x in infos)),
                        terminal_pin_cap_ff=sum(x["cap_ff"] or 0 for x in infos),
                        unknown_cap_pins=sum(x["cap_ff"] is None for x in infos),terminals=infos)
        enriched=[]
        for stage in path["stages"]:
            cell=stage["original_cell"];pin=stage["pin"]
            bit=cells[cell]["connections"][pin][0]
            direct=[sink_info(*s) for s in sinks[bit]]
            enriched.append(dict(**stage,bit=bit,direct_fanout=len(direct),
                                 direct_pin_cap_ff=sum(x["cap_ff"] or 0 for x in direct),
                                 direct_sinks=direct,buffer_tree=buffer_tree(bit)))
        semantic={}
        for name in ["dut.dispatchedInputs_childFires_0","dut.dispatchedInputs_childFires_1",
                     "dut.dispatchedInputs_allowInput","dut.elasticDivOccupied_divBusy",
                     "dut.elasticDivOccupied_divOwnerIsFp","dut.uncer_en_reg","dut.uncer_en_reg_1",
                     "dut.ClockGate_1.E","dut._Vfdiv_io_in_ready","dut._Vidiv_io_in_ready"]:
            if name not in d.mapping["netnames"]:continue
            bit=d.net_bit(name)
            if bit not in d.drivers:continue
            cell,pin=d.drivers[bit]
            semantic[name]=dict(bit=bit,driver=d.reverse[cell],pin=pin,type=cells[cell]["type"],
                               direct=[sink_info(*s) for s in sinks[bit]],buffer_tree=buffer_tree(bit))
        result=dict(version=version,root=str(root),icg1=path,path_stages=enriched,semantic=semantic,
                    note="Structural BUF-only trees terminate at first non-BUF pin. Pin-cap sums exclude wires and are not STA effective capacitance.")
        (a.output/(version+".json")).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
        aggregate[version]=dict(arrival_ns=path["arrival_ns"],buffer_count=path["buffer_count"],
                               buffer_delay_ns=path["buffer_delay_ns"],
                               chain=[dict(cell=x["cell"],type=x["type"],delay_ns=x["delay_ns"],
                                           aliases=x["rtl_nets"],fanout=x["direct_fanout"],
                                           buf_tree_terminals=x["buffer_tree"]["terminal_count"],
                                           buf_tree_depth=x["buffer_tree"]["max_depth"]) for x in enriched])
        print(version,json.dumps(aggregate[version],ensure_ascii=False),flush=True)
    for path,digest in pins.items():need(sha(Path(path))==digest,"input changed "+path)
    (a.output/"inputs.json").write_text(json.dumps(pins,indent=2)+"\n")
    (a.output/"summary.json").write_text(json.dumps(aggregate,ensure_ascii=False,indent=2)+"\n")
if __name__=="__main__":main()
