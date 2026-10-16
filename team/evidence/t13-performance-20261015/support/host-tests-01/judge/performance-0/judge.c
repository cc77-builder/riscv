
#include <stdio.h>
#include <string.h>
#define main guest_main
#include "/home/riscv/riscv-lab/t13-performance-20261015/repo/team/workloads/vdot-perf/main.c"
#undef main
void _putc(char c) { (void)c; }
void t13_kernel_0(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_1(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_2(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_3(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_4(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_5(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_6(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_7(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_8(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_9(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_10(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_11(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_12(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_13(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_14(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_15(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_16(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_17(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_18(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_19(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_20(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_21(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_22(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_23(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_24(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
void t13_kernel_25(const void *a,void *b,const void *c,void *d) {(void)a;(void)b;(void)c;(void)d;}
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
