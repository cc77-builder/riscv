"""Independent interpreter of emitted straight-line kernels, not RTL evidence."""
import json
from pathlib import Path
import re
import tempfile
import unittest
import generate as g

def signed(v,b):
    return v-(1<<b) if v&(1<<(b-1)) else v

def interpret(row):
    memory=bytes.fromhex("".join(row["stream"]))
    vectors=[bytearray.fromhex(x) for x in row["before"]]
    regs={"zero":0,"a2":0,"a3":0x100000}
    vl,sew,lmul=8,8,1
    output={}
    def read(r,n):
        return bytes().join(bytes(vectors[i]) for i in range(r,r+(n+15)//16))[:n]
    def write(r,data):
        for at,value in enumerate(data):
            vectors[r+at//16][at%16]=value
    for line in row["body"]:
        fields=line.replace(",","").split()
        op=fields[0];a=fields[1:]
        if op=="vsetivli":
            vl,sew=int(a[1]),int(a[2][1:]);lmul=int(a[3][1:])
            if vl*sew>128*lmul:raise ValueError("VL exceeds VLMAX")
        elif op=="li":regs[a[0]]=int(a[1])
        elif op=="mv":regs[a[0]]=regs[a[1]]
        elif op=="addi":regs[a[0]]=regs[a[1]]+int(a[2])
        elif op in ("csrwi",):pass
        elif op=="vle8.v":
            r=int(a[0][1:]);base=regs[a[1].strip("()")]
            if not 0<=base<=len(memory)-vl:raise ValueError("out-of-bounds vector load")
            write(r,memory[base:base+vl])
        elif op=="lb":
            m=re.fullmatch(r"(\d+)\((\w+)\)",a[1]);at=regs[m[2]]+int(m[1])
            if not 0<=at<len(memory):raise ValueError("out-of-bounds scalar load")
            regs[a[0]]=signed(memory[at],8)
        elif op=="mulw":regs[a[0]]=signed((regs[a[1]]*regs[a[2]])&0xffffffff,32)
        elif op=="addw":regs[a[0]]=signed((regs[a[1]]+regs[a[2]])&0xffffffff,32)
        elif op==".word":
            word=int(a[0],16)
            if word&0xfe00707f!=0x0200000b or vl!=8 or sew!=8:raise ValueError("illegal custom")
            d,x,y=(word>>7)&31,(word>>15)&31,(word>>20)&31
            val=sum(signed(u,8)*signed(v,8) for u,v in zip(read(x,8),read(y,8)))
            write(d,(val&0xffffffff).to_bytes(4,"little")+bytes(12))
        elif op=="vwmul.vv":
            d,x,y=[int(v[1:]) for v in a]
            if sew!=8 or lmul!=1 or d%2:raise ValueError("widening multiply group")
            write(d,b"".join(((signed(u,8)*signed(v,8))&65535).to_bytes(2,"little") for u,v in zip(read(x,vl),read(y,vl))))
        elif op=="vmv.v.i":
            r=int(a[0][1:]);value=int(a[1])&((1<<sew)-1)
            write(r,value.to_bytes(sew//8,"little")*vl)
        elif op=="vwredsum.vs":
            d,x,seed=[int(v[1:]) for v in a]
            if sew!=16 or lmul!=2:raise ValueError("reduction input configuration")
            data=read(x,vl*2)
            value=signed(int.from_bytes(read(seed,4),"little"),32)+sum(signed(int.from_bytes(data[i:i+2],"little"),16) for i in range(0,len(data),2))
            write(d,(value&0xffffffff).to_bytes(4,"little"))
        elif op=="vmv.x.s":
            regs[a[0]]=signed(int.from_bytes(read(int(a[1][1:]),sew//8),"little"),sew)
        elif op=="vmv.s.x":
            write(int(a[0][1:]),(regs[a[1]]&((1<<sew)-1)).to_bytes(sew//8,"little"))
        elif op=="vs1r.v":
            at=regs[a[1].strip("()")]-0x100000
            output[at]=read(int(a[0][1:]),16).hex()
        else:raise ValueError("unsupported assembly "+line)
    return vectors,output,vl,sew,regs

class ModelTests(unittest.TestCase):
    def test_signed_limits(self):
        self.assertEqual(g.oracle.gemv([[-128]*64,[127]*64],[-128]*64),[1048576,-1040384])
    def test_invalid_inputs(self):
        for a,x in [([],[]),([[1,2]],[1]),([[128]],[1]),([[True]],[1])]:
            with self.subTest(a=a):
                with self.assertRaises(ValueError):g.oracle.gemv(a,x)
    def test_all_emitted_kernels_against_independent_gemv(self):
        for dataset in range(3):
            for m,k in g.SHAPES:
                for scope in g.SCOPES:
                    for software in ("basic","reuse"):
                        for method in ("vdot","rvv"):
                            row=g.case(m,k,dataset,method,software,scope)
                            with self.subTest(case=row["id"],dataset=dataset):
                                regs,output,vl,sew,scalar=interpret(row)
                                for i in range(16):self.assertEqual(regs[i].hex(),row["expected"][i])
                                self.assertEqual((vl,sew,scalar["t5"]),(8,8,m*k))
                                self.assertEqual(output,{} if scope=="core" else {16*i:v for i,v in enumerate(row["outputs"])})
    def test_inputs_shared_and_no_row_padding(self):
        for m,k in g.SHAPES:
            rows=[g.case(m,k,2,method,sw,"core") for sw in ("basic","reuse") for method in ("vdot","rvv")]
            self.assertTrue(all(row["stream"]==rows[0]["stream"] for row in rows))
            a,x=g.inputs(m,k,2);raw=bytes.fromhex("".join(rows[0]["stream"]))
            self.assertEqual(raw[:m*k],bytes(v&255 for row in a for v in row))
            self.assertEqual(raw[m*k:m*k+k],bytes(v&255 for v in x))
    def test_reuse_reduces_x_loads(self):
        for method in ("vdot","rvv"):
            a=g.kernel(16,64,method,"basic","core")
            b=g.kernel(16,64,method,"reuse","core")
            self.assertLess(sum("vle8.v" in l for l in b),sum("vle8.v" in l for l in a))
    def test_deterministic_generator(self):
        with tempfile.TemporaryDirectory() as t:
            a=g.generate(Path(t)/"a","performance",2,7,8)
            b=g.generate(Path(t)/"b","performance",2,7,8)
            self.assertEqual(a,b);self.assertEqual(len(a["plan"]),24)
            self.assertEqual(sum(p["phase"]=="measured" for p in a["plan"]),16)
    def test_scope_stores_after_counter(self):
        with tempfile.TemporaryDirectory() as t:
            g.generate(Path(t)/"core","smoke",0,0,8)
            s=(Path(t)/"core/kernels.S").read_text()
            first=s.split("t13_kernel_0:",1)[1].split(".size",1)[0]
            self.assertGreater(first.index("vs1r.v v0"),first.index("0x51400013"))
    def test_oracle_detects_input_error(self):
        row=g.case(4,13,0,"vdot","reuse","endtoend")
        before=row["outputs"]
        row["stream"][0]="00"+row["stream"][0][2:]
        _,actual,_,_,_=interpret(row)
        self.assertNotEqual(actual,{16*i:v for i,v in enumerate(before)})

if __name__=="__main__":unittest.main()
