/* Standalone differential experiment around the unchanged original object. */
#include <stdint.h>
#include <stddef.h>

enum { N = 768, CASES = 30 };
typedef struct { int8_t *q; float *s; } QuantizedTensor;
typedef void (*quant_fn)(QuantizedTensor *, float *, int);
extern int GS;
extern void quantize(QuantizedTensor *, float *, int);
extern void r2_quantize_gs32_rvv(QuantizedTensor *, float *, int);
extern void r2_quantize_bad_rne(QuantizedTensor *, float *, int);
extern void r2_quantize_bad_keep_flags(QuantizedTensor *, float *, int);
extern void r2_quantize_bad_entry_flags(QuantizedTensor *, float *, int);

struct probe { uint64_t before[5], after[5], abi, i0, i1; };
extern void quant_probe(QuantizedTensor *, float *, int, quant_fn, struct probe *);
struct input { uint64_t lo[2]; float x[N]; uint64_t hi[2]; };
struct output { uint64_t lo[2]; int8_t q[N]; uint64_t mid[2]; float s[N]; uint64_t hi[2]; };
struct context { uint64_t lo[2]; QuantizedTensor t; uint64_t hi[2]; };
struct config { uint64_t id, n, gs, frm, flags, vl, vtype, vstart, vcsr; };
struct result {
  struct config config;
  struct input input, after_scalar, after_candidate;
  struct output scalar, candidate;
  struct context context_before[2], context_after[2];
  struct probe probe[2];
  uint64_t failure;
};
_Static_assert(sizeof(QuantizedTensor)==16 && offsetof(QuantizedTensor,s)==8,"original RV64 ABI");
_Static_assert(sizeof(struct probe)==104,"probe assembly layout");
_Static_assert(sizeof(struct config)==72,"config dump layout");
_Static_assert(sizeof(struct input)==3104,"whole input and guards");
_Static_assert(sizeof(struct output)==3888,"whole q/scales and guards");
_Static_assert(sizeof(struct context)==48,"context guards");
_Static_assert(sizeof(struct result)==17568,"whole per-case record");

volatile uint64_t quant_control[2] __attribute__((section(".data"),used))={UINT64_C(0x5154475333325631),0};
volatile uint64_t quant_report[16];
struct result quant_cases[CASES] __attribute__((aligned(16)));
static struct input working;
static struct context context;

static void copy(void *dst,const void *src,size_t n) {
  unsigned char *d=dst; const unsigned char *s=src;
  for(size_t i=0;i<n;++i)d[i]=s[i];
}
static void fill(void *dst,unsigned char x,size_t n) {
  unsigned char *d=dst;for(size_t i=0;i<n;++i)d[i]=x;
}
static int same(const void *a,const void *b,size_t n) {
  const unsigned char *x=a,*y=b;
  for(size_t i=0;i<n;++i)if(x[i]!=y[i])return 0;
  return 1;
}
static void bits(float *p,uint32_t value) { copy(p,&value,4); }
static void zero_group(struct input *p,unsigned first) {
  for(unsigned i=0;i<32;++i)bits(p->x+first+i,0);
}
static void halves(struct input *p,unsigned first) {
  static const uint32_t values[]={0x42fe0000,0x3f000000,0xbf000000,0x3effffff,
    0x3f000001,0xbeffffff,0xbf000001,0xc2fe0000,0x80000000,0,0x3fc00000,0xbfc00000};
  zero_group(p,first);
  for(unsigned i=0;i<sizeof(values)/sizeof(*values);++i)bits(p->x+first+i,values[i]);
}
static void configure(struct result *r,unsigned id) {
  r->config=(struct config){id,32,32,0,0,7,0xc8,0,5};
  if(id==2 || id==13 || id==14 || id==15)r->config.n=288;
  if(id==3 || id==29)r->config.n=768;
  if(id==3)r->config.flags=0x1f;
  if(id==5 || id==9 || id==12 || id==28)r->config.n=64;
  if(id>=16 && id<=19)r->config.frm=id-15;
  if(id==20)r->config.n=33;
  if(id==21)r->config.n=31;
  if(id==22)r->config.n=0;
  if(id==23)r->config.n=(uint64_t)(int64_t)-32;
  if(id==24){r->config.n=64;r->config.gs=16;}
  if(id==25){r->config.n=128;r->config.gs=64;}
  if(id==26)r->config.vl=0;
  if(id==27)r->config.vstart=3;
  if(id==28){r->config.vtype=UINT64_C(1)<<63;r->config.vl=0;}
  if(id==29){r->config.flags=0x15;r->config.vl=5;r->config.vtype=0xd1;}
  if(id==11){r->config.vl=7;r->config.vtype=0xc7;}
  fill(&r->input,0xcd,sizeof(r->input));
  unsigned count=(int64_t)r->config.n>0?(unsigned)r->config.n:0;
  uint32_t state=0x9e3779b9u+id;
  for(unsigned i=0;i<count;++i){
    state=1664525u*state+1013904223u;
    bits(r->input.x+i,(state&0x807fffffu)|((121u+i%10u)<<23));
  }
  if(id==0 || (id>=16 && id<=19) || id==26 || id==27)halves(&r->input,0);
  if(id==1){zero_group(&r->input,0);bits(r->input.x,0x3f800000);}
  if(id==4)zero_group(&r->input,0);
  if(id==5){halves(&r->input,0);zero_group(&r->input,32);}
  if(id==6)bits(r->input.x,0x7fc12345);
  if(id==7)bits(r->input.x,0x7f812345);
  if(id==8)bits(r->input.x,0x7f800000);
  if(id==9){halves(&r->input,0);bits(r->input.x+32,0xff800000);}
  if(id==10){zero_group(&r->input,0);bits(r->input.x,190);}
  if(id==11){zero_group(&r->input,0);bits(r->input.x,0x437e0000);bits(r->input.x+1,1);bits(r->input.x+2,0x80000001);}
  if(id==12){halves(&r->input,0);zero_group(&r->input,32);bits(r->input.x+32,190);}
  if(id==13)zero_group(&r->input,256);
  if(id==14)bits(r->input.x+287,0xffc12345);
  if(id==15){zero_group(&r->input,256);bits(r->input.x+256,190);}
  if(id==29){bits(r->input.x,0x7f7fffff);bits(r->input.x+1,1);bits(r->input.x+2,0xff7fffff);}
}
static void environment(const struct config *c) {
  uint64_t vl,flags=(c->frm<<5)|c->flags;
  __asm__ volatile("csrwi vstart,0\nvsetvl %0,%1,%2\ncsrw vcsr,%3\ncsrw vstart,%4\nfscsr %5"
    :"=&r"(vl):"r"(c->vl),"r"(c->vtype),"r"(c->vcsr),"r"(c->vstart),"r"(flags):"memory");
}
static void check_case(struct result *r,quant_fn fn) {
  struct output *outputs[]={&r->scalar,&r->candidate};
  struct input *afters[]={&r->after_scalar,&r->after_candidate};
  quant_fn functions[]={quantize,fn};
  GS=(int)r->config.gs;
  for(unsigned k=0;k<2;++k){
    fill(outputs[k],0xa5,sizeof(*outputs[k]));
    fill(&context,0x69,sizeof(context));
    context.t=(QuantizedTensor){outputs[k]->q,outputs[k]->s};
    copy(&r->context_before[k],&context,sizeof(context));
    copy(&working,&r->input,sizeof(working));
    environment(&r->config);
    quant_probe(&context.t,working.x,(int)r->config.n,functions[k],&r->probe[k]);
    copy(&r->context_after[k],&context,sizeof(context));
    copy(afters[k],&working,sizeof(working));
  }
  uint64_t f=0;
  if(!same(&r->scalar,&r->candidate,sizeof(r->scalar)))f|=1;
  if(!same(&r->input,&r->after_scalar,sizeof(r->input)))f|=2;
  if(!same(&r->input,&r->after_candidate,sizeof(r->input)))f|=4;
  if(r->probe[0].after[0]!=r->probe[1].after[0])f|=8;
  for(unsigned k=0;k<2;++k){
    for(unsigned j=1;j<5;++j)if(r->probe[k].before[j]!=r->probe[k].after[j])f|=16;
    if(r->probe[k].abi)f|=32;
    if(!same(&r->context_before[k],&r->context_after[k],sizeof(context)))f|=64;
    const uint64_t expected[]={r->config.frm*32+r->config.flags,r->config.vl,r->config.vtype,r->config.vstart,r->config.vcsr};
    if(!same(r->probe[k].before,expected,sizeof(expected)))f|=128;
  }
  r->failure=f;
}
__attribute__((noreturn,noinline,noclone)) static void finish(unsigned code) {
  __asm__ volatile("mv a0,%0\n.global quant_finish_trap\nquant_finish_trap:\n.word 0x0005006b"::"r"((uintptr_t)code):"a0","memory");
  for(;;){}
}
int team_quantize_main(void) {
  const quant_fn functions[]={r2_quantize_gs32_rvv,r2_quantize_bad_rne,
    r2_quantize_bad_keep_flags,r2_quantize_bad_entry_flags};
  uint64_t mode=quant_control[1],mstatus,vlenb;
  __asm__ volatile("csrr %0,mstatus\ncsrr %1,vlenb":"=r"(mstatus),"=r"(vlenb));
  quant_report[0]=quant_control[0];quant_report[1]=1;quant_report[2]=mode;
  quant_report[3]=CASES;quant_report[4]=sizeof(struct result);quant_report[5]=mstatus;quant_report[6]=vlenb;
  if(quant_control[0]!=UINT64_C(0x5154475333325631) || mode>3 || vlenb!=16 || !(mstatus&0x6000) || !(mstatus&0x600))finish(90);
  unsigned failed=0;uint64_t mask=0;
  for(unsigned i=0;i<CASES;++i){
    configure(&quant_cases[i],i);check_case(&quant_cases[i],functions[mode]);
    if(quant_cases[i].failure){++failed;mask|=UINT64_C(1)<<i;}
  }
  quant_report[7]=failed;quant_report[8]=mask;quant_report[9]=failed?94:0;
  __asm__ volatile("csrwi vstart,0\ncsrwi fcsr,0":::"memory");
  finish(failed?94:0);
}
