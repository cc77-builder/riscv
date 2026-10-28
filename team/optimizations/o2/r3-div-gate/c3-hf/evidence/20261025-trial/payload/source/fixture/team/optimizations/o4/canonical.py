"""Lossless standard-cell netlist serialization from Yosys canonical bit IDs."""
import json,re
def emit(module,top,path):
    def ident(n):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9$]*",n):raise ValueError(f"unsafe identifier {n}")
        return n
    def signal(b):
        if isinstance(b,int):return f"n{b}"
        if b not in ["0","1","x","z"]:raise ValueError("invalid constant")
        return "1'b"+b
    bits={b for c in module["cells"].values() for bs in c["connections"].values() for b in bs if isinstance(b,int)}
    bits|={b for p in module["ports"].values() for b in p["bits"] if isinstance(b,int)}
    ports=list(module["ports"]);lines=[f"module {ident(top)}("+", ".join(map(ident,ports))+");"]
    for name,p in module["ports"].items():
        offset=p.get("offset",0);width=len(p["bits"])
        shape=f"[{offset+width-1}:{offset}] " if width>1 else ""
        if p["direction"] not in ["input","output"]:raise ValueError("unexpected inout")
        lines.append(f"  {p['direction']} {shape}{ident(name)};")
    for b in sorted(bits):lines.append(f"  wire n{b};")
    for name,p in module["ports"].items():
        for i,b in enumerate(p["bits"]):
            port=ident(name) if len(p["bits"])==1 else f"{ident(name)}[{i+p.get('offset',0)}]"
            lhs,rhs=(signal(b),port) if p["direction"]=="input" else (port,signal(b))
            if lhs.startswith("1'b"):raise ValueError("constant input port")
            lines.append(f"  assign {lhs} = {rhs};")
    by_instance={}
    for index,(old,c) in enumerate(sorted(module["cells"].items())):
        if c["parameters"]:raise ValueError("parameterized mapped standard cell")
        new=f"c{index}";by_instance[new]=old
        pins=[]
        for pin,bs in c["connections"].items():
            if len(bs)!=1:raise ValueError("non-scalar standard-cell pin")
            pins.append(f".{ident(pin)}({signal(bs[0])})")
        lines.append(f"  {ident(c['type'])} {new} ("+", ".join(pins)+");")
    lines.append("endmodule");path.write_text("\n".join(lines)+"\n")
    return by_instance
def bind(module,original,by_instance):
    from compact import annotate
    tagged=annotate(original)
    if set(by_instance)!=set(module["cells"]):raise ValueError("serialized instance set differs")
    for new,c in module["cells"].items():
        old=by_instance[new]
        c["attributes"]["o4_origin"]="orig:"+old
        if tagged["cells"][old].get("attributes",{}).get("o4_vdot")=="1":c["attributes"]["o4_vdot"]="1"
    return module
