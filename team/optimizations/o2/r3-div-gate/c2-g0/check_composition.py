"""Bind the actually used system quotient to the independently reviewed FP FSM."""
import argparse, hashlib, importlib.util, itertools, json, sys
from pathlib import Path

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name, p):
    spec = importlib.util.spec_from_file_location(name,p)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--fp-dir",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    assert not a.output.exists()
    module=Path(__file__).resolve().parent
    mainpath=module/"system_model.py"
    fppath=a.fp_dir/"fp_control_model.py"
    top=load("g0_system_model",mainpath)
    fp=load("g0_fp_control",fppath)
    rows=edges=0
    for kind,n,out,fn in [("DIV",6,5,fp.d_next),("SQRT",4,3,fp.s_next)]:
        q=lambda s: top.IDLE if s==0 else (top.OUT if s==out else top.RUN)
        for state,start,consume,cancel,clk,rst,asynchronous in itertools.product(
                range(n),range(2),range(2),range(2),range(2),range(2),range(2)):
            if rst and asynchronous: concrete=(0,)
            elif not clk: concrete=(state,)
            elif rst or cancel: concrete=(0,)
            else: concrete=fn(state,start,consume)
            abstract=top.unit_next(q(state),start,consume,cancel,clk,rst,asynchronous)
            assert {q(x) for x in concrete}<=set(abstract),(kind,state,concrete,abstract)
            rows+=1
            edges+=len(concrete)
    assert (rows,edges)==(640,660)
    # The integer top is already I/R/O; finish is permitted nondeterministically.
    int_rows=0
    for st,start,consume,finish,cancel,clk,rst,asynchronous in itertools.product(
            range(3),range(2),range(2),range(2),range(2),range(2),range(2),range(2)):
        if rst and asynchronous: concrete=0
        elif not clk: concrete=st
        elif rst or cancel: concrete=0
        elif st==0: concrete=1 if start else 0
        elif st==1: concrete=2 if finish else 1
        else: concrete=0 if consume else 2
        assert concrete in top.unit_next(st,start,consume,cancel,clk,rst,asynchronous)
        int_rows+=1
    data=dict(status="ACTUAL_SYSTEM_QUOTIENT_INCLUSION_PASS",
        fp_rows=rows,fp_edges=edges,integer_top_rows=int_rows,
        inputs={str(mainpath):sha(mainpath),str(fppath):sha(fppath)},
        scope="Containment of source-reviewed hand control models, not automatic extraction or equivalence of full RTL.")
    a.output.write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps(data,indent=2))
if __name__=="__main__":main()
