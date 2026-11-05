"""Pure report helpers copied unchanged from the fixed team O4 sources.

Upstream cc77-builder/riscv@352789e1975a3a409d39f67d143de6cf04938745;
synthesize.py/library_areas and timing.py/{parse_path,constant_warnings}.
This small frozen adapter avoids importing a different local O4 tool version.
"""

import math

import re

def require(ok, message):
    if not ok:
        raise ValueError(message)

def library_areas(path):
    text=path.read_text()
    # Nangate cells each have a scalar area before their pins.
    pairs=re.findall(r"cell\s*\(\s*(\w+)\s*\)\s*\{.*?\barea\s*:\s*([0-9.eE+-]+)",text,re.S)
    if not pairs: raise ValueError("no cell areas")
    return {k:float(v) for k,v in pairs}

def constant_warnings(checks,design,case_zero_ports=()):
    constants=set()
    for port,info in design["ports"].items():
        if info["direction"]!="output":continue
        for i,bit in enumerate(info["bits"]):
            if bit in ["0","1"]:
                constants.add(port if len(info["bits"])==1 else f"{port}[{i+info.get('offset',0)}]")
    case_bits=set()
    for name in case_zero_ports:
        port=design["ports"][name]
        if port["direction"]!="input" or len(port["bits"])!=1:raise ValueError("unsupported case-analysis port")
        case_bits.update(port["bits"])
    for name,cell in design.get("cells",{}).items():
        if cell["type"]=="CLKGATETST_X1" and len(cell["connections"].get("SE",[]))==1 and cell["connections"]["SE"][0] in case_bits:
            constants.add(name+"/SE")
    warnings=re.findall(r"Warning: There are (\d+) unconstrained endpoints\.\n((?:  [^\n]+\n)*)",checks)
    allowed=set()
    for count,body in warnings:
        endpoints={x.strip() for x in body.strip().splitlines()}
        if len(endpoints)!=int(count) or not endpoints<=constants:
            raise ValueError(f"nonconstant unconstrained endpoints: {endpoints-constants}")
        allowed|=endpoints
    remaining=re.sub(r"Warning: There are \d+ unconstrained endpoints\.\n(?:  [^\n]+\n)*","",checks).strip()
    if remaining:raise ValueError(f"unreviewed setup warning: {remaining}")
    return sorted(allowed)

def parse_path(text):
    if "No paths found." in text:
        require(text.strip()=="No paths found.","ambiguous no-path report")
        return {"exists":False}
    if text.count("Startpoint:")!=1 or text.count("Endpoint:")!=1:
        raise ValueError("missing path or explicit no-path result")
    arrivals=re.findall(r"^\s*([-+0-9.]+)\s+data arrival time\s*$",text,re.M)
    slacks=re.findall(r"^\s*([-+0-9.]+)\s+slack \((?:MET|VIOLATED)\)",text,re.M)
    if len(arrivals) not in (1,2) or len(slacks)!=1: raise ValueError("missing/ambiguous arrival/slack")
    values=[float(v) for v in arrivals+slacks]
    require(all(math.isfinite(v) for v in values) and values[0]>=0,"nonfinite or negative path delay")
    if len(arrivals)==2:
        require(math.isclose(float(arrivals[1]),-values[0],abs_tol=1e-6),"inconsistent slack arrival subtraction")
    return {"exists":True,"arrival_ns":float(arrivals[0]),"slack_ns":float(slacks[-1]),"startpoint":re.search(r"Startpoint:\s*([^\n]+)",text).group(1),"endpoint":re.search(r"Endpoint:\s*([^\n]+)",text).group(1)}
