"""Mapped-netlist naming/alias-only normalization, with connectivity invariant."""
import hashlib,json
from collections import Counter
def annotate(original):
    import copy
    m=copy.deepcopy(original)
    bits={b for n,v in m["netnames"].items() if n.startswith("dut.Vdot.") for b in v["bits"] if isinstance(b,int)}
    for name,c in m["cells"].items():
        c.setdefault("attributes",{})["o4_origin"]="orig:"+name
        if c["type"].startswith("DFF") and any(b in bits for b in c["connections"].get("Q",[])):
            c["attributes"]["o4_vdot"]="1"
    return m
def topology(m,annotated=False):
    names={n:c["attributes"]["o4_origin"][5:] if annotated else n for n,c in m["cells"].items()}
    drivers={}
    def drive(bit,key):
        if isinstance(bit,str):return
        if bit in drivers and drivers[bit]!=key:raise ValueError("multiple drivers in normalized graph")
        drivers[bit]=key
    def portbits(name,info):
        for i,b in enumerate(info["bits"]):
            yield b,name if len(info["bits"])==1 else f"{name}[{i+info.get('offset',0)}]"
    for n,info in m["ports"].items():
        if info["direction"]=="input":
            for bit,label in portbits(n,info):drive(bit,("input",label))
    for n,c in m["cells"].items():
        for pin,bits in c["connections"].items():
            if c["port_directions"][pin]=="output":
                for i,b in enumerate(bits):drive(b,("cell",names[n],pin,i))
    def source(b):
        if isinstance(b,str):return ("const",b)
        if b not in drivers:raise ValueError("undriven consumed bit")
        return drivers[b]
    cells={}
    for n,c in m["cells"].items():
        cells[names[n]]={"type":c["type"],"parameters":c["parameters"],"inputs":{p:[source(b) for b in bs] for p,bs in c["connections"].items() if c["port_directions"][p]=="input"}}
    outputs={}
    for n,info in m["ports"].items():
        if info["direction"]=="output":
            for b,label in portbits(n,info):outputs[label]=source(b)
    return hashlib.sha256(json.dumps({"cells":cells,"outputs":outputs},sort_keys=True,separators=(",",":")).encode()).hexdigest()
