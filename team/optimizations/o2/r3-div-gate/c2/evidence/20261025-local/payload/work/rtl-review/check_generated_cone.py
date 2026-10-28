#!/usr/bin/env python3
"""Read generated split RTL; conservatively trace actual DIV gate E to registers/ports.

This is not a general SV parser or a formal equivalence tool. It accepts the fixed
firtool split-RTL assignment/instance syntax, refuses unresolved cone symbols,
and cuts at declared registers. It descends child outputs and maps child inputs
back to the real parent connections. No EDA tool, synthesis, or simulator is run.
"""
import argparse, hashlib, json, re
from pathlib import Path

IDENT=r"[A-Za-z_][A-Za-z0-9_$]*"
def need(x,msg):
    if not x: raise RuntimeError(msg)
def clean(s):
    s=re.sub(r"/\*.*?\*/","",s,flags=re.S)
    return re.sub(r"//[^\n]*","",s)
def tokens(s):
    s=re.sub(r"(?:\d+)?'[sS]?[bBdDhHoO][0-9a-fA-F_xXzZ?]+","",s)
    return sorted(set(re.findall(IDENT,s)) - {"signed","unsigned"})
def paren(s,start):
    need(s[start]=="(","paren start")
    dep=1; end=start+1
    while dep and end<len(s):
        if s[end]=="(":dep+=1
        elif s[end]==")":dep-=1
        end+=1
    need(dep==0,"unterminated paren")
    return s[start+1:end-1],end
def parse_file(path):
    s=clean(path.read_text())
    m=re.search(r"\bmodule\s+("+IDENT+r")\s*\(",s)
    if not m:return None
    name=m[1];header,he=paren(s,m.end()-1);body=s[he:]
    dirs={}; direction=None
    for part in header.split(","):
        p=part.strip()
        mt=re.match(r"(input|output|inout)\b(.*)",p,re.S)
        if mt: direction=mt[1];p=mt[2]
        p=re.sub(r"\[[^\]]*\]","",p)
        ts=[t for t in re.findall(IDENT,p) if t not in {"wire","reg","logic","signed","unsigned"}]
        need(len(ts)==1 and direction is not None,f"unsupported port syntax {path}: {part}")
        dirs[ts[0]]=direction
    regs=set(re.findall(r"\breg\s+(?:signed\s+)?(?:\[[^\]]+\]\s*)?("+IDENT+r")",body))
    drivers={}
    for mt in re.finditer(r"^\s*(?:wire|assign)\s+(?:signed\s+)?(?:\[[^\]]*\]\s*)?("+IDENT+r")\s*=\s*(.*?);",body,re.M|re.S):
        need(mt[1] not in drivers,f"multiple assignments to {name}.{mt[1]}")
        drivers[mt[1]]=mt[2].strip()
    instances={}
    for mt in re.finditer(r"^\s*("+IDENT+r")\s+("+IDENT+r")\s*\(",body,re.M):
        typ,inst=mt.group(1),mt.group(2)
        if typ in {"module","if","else","assert","case","while","for"}:continue
        args,ae=paren(body,mt.end()-1)
        if not body[ae:].lstrip().startswith(";"):continue
        ports={}
        pos=0
        while True:
            pm=re.search(r"\.("+IDENT+r")\s*\(",args[pos:])
            if not pm:break
            beg=pos+pm.end()-1
            expr,pe=paren(args,beg);ports[pm[1]]=expr.strip();pos=pe
        if ports:instances[inst]={"type":typ,"ports":ports}
    return {"name":name,"path":path,"dirs":dirs,"regs":regs,"drivers":drivers,"instances":instances}

class Trace:
    def __init__(self,root):
        self.modules={}
        for p in sorted(root.glob("*.sv")):
            m=parse_file(p)
            if m:
                need(m["name"] not in self.modules,"duplicate module")
                self.modules[m["name"]]=m
        need("ExeUnit" in self.modules,"missing ExeUnit")
        self.root=("ExeUnit",)
        self.stack=set();self.visited=set();self.leaves=set();self.used=set();self.forbidden=set()
    def mod(self,scope):
        mod=self.modules[scope[0]]
        for inst in scope[1:]:
            child=mod["instances"][inst]
            need(child["type"] in self.modules,f"missing module {child['type']}")
            mod=self.modules[child["type"]]
        return mod
    def expr(self,scope,expr):
        for name in tokens(expr):self.net(scope,name)
    def net(self,scope,name):
        key=scope+(name,);label=".".join(key)
        if key in self.visited:return
        need(key not in self.stack,"combinational cycle "+label)
        self.stack.add(key)
        m=self.mod(scope);self.used.add(m["path"])
        # Forbid the actual DIV ready ports/wires and source ready/fire-control aliases.
        if (("Vidiv" in label or "Vfdiv" in label or "VIDiv" in label or "VFDiv" in label)
            and ("io_in_ready" in name or "start_ready" in name)):
            self.forbidden.add(label)
        if any(s in name for s in ["allowInput","childFires","selectedReady"]) or name=="elasticDivOccupied":
            self.forbidden.add(label)
        if name in m["regs"]:
            self.leaves.add(label+" [register]")
        elif name in m["drivers"]:
            self.expr(scope,m["drivers"][name])
        elif m["dirs"].get(name)=="input":
            if len(scope)==1:self.leaves.add(label+" [input]")
            else:
                parent=self.mod(scope[:-1]);conn=parent["instances"][scope[-1]]["ports"]
                need(name in conn,"unconnected input "+label)
                self.expr(scope[:-1],conn[name])
        else:
            matches=[]
            for inst,d in m["instances"].items():
                child=self.modules.get(d["type"])
                if child is None:continue
                for port,expr in d["ports"].items():
                    if expr==name and child["dirs"].get(port)=="output":
                        matches.append((inst,port))
            need(len(matches)==1,f"unresolved or multiply driven {label}: {matches}")
            inst,port=matches[0];self.net(scope+(inst,),port)
        self.stack.remove(key);self.visited.add(key)
    def gate(self,instance):
        self.stack=set();self.visited=set();self.leaves=set();self.used=set();self.forbidden=set()
        m=self.modules["ExeUnit"];g=m["instances"][instance]
        self.expr(self.root,g["ports"]["E"])
        return dict(instance=instance,enable=g["ports"]["E"],clock_output=g["ports"]["Q"],
                    nodes=sorted(".".join(k) for k in self.visited),leaves=sorted(self.leaves),
                    forbidden=sorted(self.forbidden),input_files=sorted(str(p) for p in self.used))
    def run(self):
        m=self.modules["ExeUnit"];result=[]
        for inst,d in m["instances"].items():
            if d["type"]!="ClockGate":continue
            sinks=[(n,x["type"]) for n,x in m["instances"].items() if x["ports"].get("clock")==d["ports"]["Q"]]
            if not any(t in {"VIDiv","VFDivSqrt"} for n,t in sinks):continue
            r=self.gate(inst);r["sinks"]=sinks;result.append(r)
        need(len(result)==2,"must find exactly the two real DIV gates")
        files=set(p for row in result for p in row["input_files"])
        return dict(status="C2_GATE_READY_CONE_PASS" if all(not r["forbidden"] for r in result) else "C2_GATE_READY_CONE_REJECT",
                    gates=result,
                    inputs=[dict(path=p,sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest(),bytes=Path(p).stat().st_size) for p in sorted(files)],
                    method="Generated split RTL assignment/instance graph, cut at declared registers; descend child output cones and map child inputs back to parent; no EDA execution.")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--rtl",type=Path,required=True);ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--expect",choices=["pass","reject"],default="pass");a=ap.parse_args()
    need(not a.output.exists(),"refuse existing output")
    result=Trace(a.rtl).run();a.output.write_text(json.dumps(result,indent=2)+"\n")
    expect="C2_GATE_READY_CONE_PASS" if a.expect=="pass" else "C2_GATE_READY_CONE_REJECT"
    need(result["status"]==expect,"unexpected cone result")
    print(result["status"],"gates",len(result["gates"]),"inputs",len(result["inputs"]))
if __name__=="__main__":main()
