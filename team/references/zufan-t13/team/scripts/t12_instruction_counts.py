"""Count the bounded inclusive rdinstret bracket from final ELF machine words.
This validates workload length. It does not calibrate rdcycle as FU latency.
"""
import struct
from pathlib import Path
def require(ok,message):
 if not ok:raise ValueError(message)
def counts(path):
 data=Path(path).read_bytes();require(data[:6]==b'\x7fELF\x02\x01','expected ELF64 little endian')
 require(struct.unpack_from('<H',data,18)[0]==243,'expected RISC-V ELF')
 shoff=struct.unpack_from('<Q',data,40)[0];entsize,n=struct.unpack_from('<HH',data,58)
 require(entsize==64,'ELF section size')
 sections=[struct.unpack_from('<IIQQQQIIQQ',data,shoff+i*64) for i in range(n)]
 def raw(s):return data[s[4]:s[4]+s[5]]
 symbols={}
 for s in sections:
  if s[1]!=2:continue
  names=raw(sections[s[6]])
  for off in range(s[4],s[4]+s[5],s[9]):
   name,info,other,section,value,size=struct.unpack_from('<IBBHQQ',data,off)
   end=names.find(b'\0',name);label=names[name:end].decode()
   if label.startswith('t12_perf_') and info&15==2:symbols[label]=(section,value,size)
 require(symbols,'no measured kernels')
 def sext(v,n):return v-(1<<n) if v>>(n-1) else v
 result={}
 for name,(section,start,size) in symbols.items():
  s=sections[section];base=s[4]+start-s[3];code={start+i:struct.unpack_from('<I',data,base+i)[0] for i in range(0,size,4)}
  pc=start;t6=0;active=False;count=0
  for steps in range(100000):
   require(pc in code,'escaped measured function');w=code[pc];require(w&3==3,'compressed measured instruction')
   if w==0xc0202873:require(not active,'repeated begin');active=True
   if active:count+=1
   if w==0xc02028f3:
    require(active,'end before begin');result[name.replace('t12_','',1).replace('_','-')]=count;break
   opcode=w&127;rd=(w>>7)&31;rs1=(w>>15)&31;rs2=(w>>20)&31
   if opcode==0x13 and rd==31:
    require((w>>12)&7==0 and rs1 in (0,31),'unmodelled loop register update');t6=(0 if rs1==0 else t6)+sext(w>>20,12)
   if opcode==0x63:
    require((w>>12)&7==1 and rs1==31 and rs2==0,'unexpected measured branch')
    imm=((w>>31)<<12)|(((w>>7)&1)<<11)|(((w>>25)&63)<<5)|(((w>>8)&15)<<1)
    pc=pc+sext(imm,13) if t6!=0 else pc+4
   else:
    require(opcode not in (0x67,0x6f),'unexpected measured jump');pc+=4
  else:raise ValueError('unbounded measured loop')
 return result
if __name__=='__main__':
 import argparse,json
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('elf',type=Path);a=p.parse_args();print(json.dumps(counts(a.elf),indent=2))
