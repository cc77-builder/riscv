"""Compile the actual guest judge with native GCC and exhaustively flip bits."""
import argparse
import json
from pathlib import Path
import subprocess
import generate as g

BODY=r'''
#include <stdio.h>
#include <string.h>
#define main guest_main
#include "GUEST_PATH"
#undef main
void _putc(char c) { (void)c; }
STUBS
static unsigned long flips=0, allowed=0, cases_checked=0;
static void seed(const struct t13_case *c) {
  memset(&observed,0,sizeof(observed)); memset(&sink,0,sizeof(sink));
  observed.head[0]=observed.head[1]=observed.tail[0]=observed.tail[1]=canary;
  sink.head[0]=sink.head[1]=sink.tail[0]=sink.tail[1]=canary;
  memcpy(observed.value.regs,c->expected,512);
  observed.value.iterations=c->iterations;
  uint64_t wanted[]={c->vtype,8,0,3,1,7,0};
  memcpy(observed.value.csr,wanted,sizeof(wanted));
  memset(sink.value,0xa6,sizeof(sink.value));
  for(unsigned i=0;i<c->stream_count;++i)memcpy(sink.value[i],c->outputs[i],16);
}
int main(void) {
  for(unsigned k=0;k<sizeof(cases)/sizeof(cases[0]);++k) {
    const struct t13_case *c=&cases[k];seed(c);
    if(judge(c))return 10;
    for(unsigned r=0;r<32;++r)for(unsigned bit=0;bit<128;++bit) {
      observed.value.regs[r][bit/8]^=1U<<(bit%8);
      unsigned got=judge(c), scratch=!!(c->scratch&(1U<<r));
      if((got==0)!=scratch)return 11;
      if(scratch)++allowed;else ++flips;
      observed.value.regs[r][bit/8]^=1U<<(bit%8);
    }
    for(unsigned r=0;r<6;++r)for(unsigned bit=0;bit<64;++bit) {
      observed.value.csr[r]^=UINT64_C(1)<<bit;
      if(!judge(c))return 12;
      ++flips;observed.value.csr[r]^=UINT64_C(1)<<bit;
    }
    for(unsigned bit=0;bit<64;++bit) {
      observed.value.iterations^=UINT64_C(1)<<bit;
      if(!judge(c))return 13;
      ++flips;observed.value.iterations^=UINT64_C(1)<<bit;
    }
    for(unsigned bit=0;bit<2;++bit) {
      observed.value.csr[6]^=1U<<(2*bit);if(!judge(c))return 14;
      ++flips;observed.value.csr[6]^=1U<<(2*bit);
    }
    uint64_t *guards[]={observed.head,observed.tail,sink.head,sink.tail};
    for(unsigned r=0;r<4;++r)for(unsigned bit=0;bit<128;++bit) {
      guards[r][bit/64]^=UINT64_C(1)<<(bit%64);if(!judge(c))return 15;
      ++flips;guards[r][bit/64]^=UINT64_C(1)<<(bit%64);
    }
    for(unsigned r=0;r<64;++r)for(unsigned bit=0;bit<128;++bit) {
      sink.value[r][bit/8]^=1U<<(bit%8);if(!judge(c))return 16;
      ++flips;sink.value[r][bit/8]^=1U<<(bit%8);
    }
    if(!run_controls(c))return 17;
    ++cases_checked;
  }
  printf("HOST_JUDGE_PASS cases=%lu rejected=%lu scratch_allowed=%lu\n",cases_checked,flips,allowed);
  return 0;
}
'''


def main(a):
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    records=[]
    for suite,dataset in [('functional',0),('performance',0),('performance',1),('performance',2)]:
        name=f'{suite}-{dataset}';d=out/name;d.mkdir();m=g.generate(d/'data',suite,dataset)
        stubs='\n'.join(f'void t13_kernel_{i}(const void *a,void *b,const void *c,void *d) {{(void)a;(void)b;(void)c;(void)d;}}' for i in range(len(m['rows'])))
        (d/'judge.c').write_text(BODY.replace('GUEST_PATH',str(Path(__file__).with_name('main.c').resolve())).replace('STUBS',stubs))
        for mode,flags in [('plain',[]),('ubsan',['-fsanitize=undefined','-fno-sanitize-recover=all'])]:
            command=['gcc','-std=c11','-O2','-I'+str(d/'data')]+flags+[str(d/'judge.c'),'-o',str(d/mode)]
            subprocess.run(command,check=True)
            result=subprocess.run([str(d/mode)],capture_output=True,text=True)
            (d/(mode+'.log')).write_text(result.stdout+result.stderr)
            records.append(dict(name=name,mode=mode,command=command,exit_code=result.returncode,result=result.stdout.strip()))
            assert result.returncode==0,records[-1]
    (out/'result.json').write_text(json.dumps(dict(status='PASS',runs=records),indent=2)+'\n');print(json.dumps(records))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);main(p.parse_args())
