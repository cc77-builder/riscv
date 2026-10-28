#!/usr/bin/env python3
"""Audit actual generated clock-gate pins against pinned Liberty Boolean statetable."""
import argparse, hashlib, itertools, json, re
from pathlib import Path
def main():
    p=argparse.ArgumentParser();p.add_argument("library",type=Path);p.add_argument("output",type=Path);a=p.parse_args()
    lib=a.library.read_text();start=lib.index("cell (CLKGATETST_X1)");end=lib.find("\n  cell (",start+10);cell=lib[start:end]
    tab=re.search(r'statetable\s*\("CK E SE","IQ"\)\s*\{\s*table\s*:\s*"([^"]+)"',cell,re.S).group(1)
    rows=[]
    for row in tab.replace("\\","").split(","):
        fields=row.strip().split(":");assert len(fields)==3
        rows.append([fields[0].split(),fields[1].strip(),fields[2].strip()])
    output=re.search(r'pin\s*\(GCK\).*?state_function\s*:\s*"([^"]+)"',cell,re.S).group(1)
    assert output=="(IQ & CK)"
    checks=[]
    for ck,e,se,old in itertools.product([0,1],repeat=4):
        matched=[out for pattern,oldpat,out in rows if all(x=="-" or (x=="H")==bool(b) for x,b in zip(pattern,[ck,e,se]))]
        assert len(matched)==1
        libstate=old if matched[0]=="N" else int(matched[0]=="H")
        rtlstate=(e|se) if not ck else old
        assert libstate==rtlstate
        checks.append({"CK":ck,"E":e,"SE":se,"old_EN":old,"lib_new_IQ":libstate,"rtl_new_EN":rtlstate,"Q":ck&rtlstate})
    result={"scope":"Boolean state-transition/pin-mapping audit, not formal RTL equivalence or timing simulation","library_sha256":hashlib.sha256(a.library.read_bytes()).hexdigest(),"cell":"CLKGATETST_X1","pin_map":{"CK":"CK","E":"E","TE":"SE","Q":"GCK"},"parsed_statetable":rows,"output_state_function":output,"transitions":checks,"pass":True}
    a.output.write_text(json.dumps(result,indent=2)+"\n");print("O4_CLOCKGATE_BOOLEAN_AUDIT_PASS")
if __name__=="__main__":main()
