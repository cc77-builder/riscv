#include <stdint.h>
#include <stddef.h>
#include "harness.h"
#include "cases.h"

extern void _putc(char);
extern void _halt(int);
void platform_halt(int code) { _halt(code); for (;;) {} }
struct trap_record *vdot_active_record;
uint64_t t12_counts[4];
struct vector_csrs t12_recovery_csrs;
uint64_t t12_recovery_status;
unsigned char t12_sink[4][16] __attribute__((aligned(16)));
static struct trap_record record;
static const uint64_t canary = UINT64_C(0xd15ea5e5cafebabe);
static struct { uint64_t head[2]; unsigned char regs[32][16]; uint64_t tail[2]; } after __attribute__((aligned(16)));
static const struct run_config config = {0,8,0,3,1,0,0,1};

static void text(const char *s) { while (*s) _putc(*s++); }
static void decimal(uint64_t n) {
  char buf[21]; unsigned i=0;
  do { buf[i++]=(char)('0'+n%10); n/=10; } while (n);
  while (i) _putc(buf[--i]);
}
static void hex(uint64_t n) {
  text("0x"); for (int i=60;i>=0;i-=4) _putc("0123456789abcdef"[(n>>i)&15]);
}
static void vector(const unsigned char *p) {
  for (int i=15;i>=0;--i) { _putc("0123456789abcdef"[p[i]>>4]); _putc("0123456789abcdef"[p[i]&15]); }
}
static void zero(void *p, size_t n) { unsigned char *q=p; while (n--) *q++=0; }
static int eq(const void *a,const void *b,size_t n) {
  const unsigned char *p=a,*q=b; while (n--) if (*p++!=*q++) return 0; return 1;
}
static int same(const char *a,const char *b) {
  while (*a && *a==*b) { ++a; ++b; } return *a==*b;
}
static int guards(void) {
  return after.head[0]==canary && after.head[1]==canary && after.tail[0]==canary && after.tail[1]==canary;
}
static int verify(const struct t12_case *c) {
  unsigned char comparable[32][16];
  for (unsigned r=0;r<32;++r)
    for (unsigned b=0;b<16;++b)
      comparable[r][b]=(c->scratch & (1U<<r)) ? after.regs[r][b] : c->expected[r][b];
  struct trap_record view=record;
  struct expectation e={config,c->fault_vl>=0 ? 2 : 0,comparable,c->before};
  if (c->fault_vl>=0) {
    struct vector_csrs fault={0,(uint64_t)c->fault_vl,0,3,1,7};
    struct vector_csrs recovered={0,8,0,3,1,7};
    if (!eq(&record.post,&fault,sizeof(fault)) || !eq(&t12_recovery_csrs,&recovered,sizeof(recovered)) ||
        ((t12_recovery_status>>9)&3)!=3 || record.epc!=(uint64_t)c->fault || record.expected_pc!=(uint64_t)c->fault || record.tval!=0) return 20;
    /* The inherited judge checks pre-state/protocol/full vectors. Independently
       checked fault CSRs above; recovery deliberately makes final vectors differ. */
    view.post=record.pre;
  }
  int rc=(int)judge(&view,&e,after.regs,guards());
  if (rc) return rc;
  if (c->kind==2) {
    if (t12_counts[1]<=t12_counts[0] || t12_counts[3]<=t12_counts[2]) return 21;
    unsigned n=same(c->scenario,"independent-batch") ? 4 : 1;
    for (unsigned i=0;i<n;++i) if (!eq(t12_sink[i],c->expected[10+i],16)) return 22;
  }
  return 0;
}
static void csrlog(const struct vector_csrs *c) {
  const uint64_t values[]={c->vtype,c->vl,c->vstart,c->vxrm,c->vxsat,c->vcsr};
  for (unsigned i=0;i<6;++i) { if (i) _putc('/'); hex(values[i]); }
}
static unsigned done;
static int controls_done;
static int run(const struct t12_case *c,unsigned repeat) {
  zero(&record,sizeof(record));zero(t12_counts,sizeof(t12_counts));
  zero(&t12_recovery_csrs,sizeof(t12_recovery_csrs));t12_recovery_status=0;zero(t12_sink,sizeof(t12_sink));
  zero(&after,sizeof(after));after.head[0]=after.head[1]=after.tail[0]=after.tail[1]=canary;
  vdot_run(&record,&config,c->before,after.regs,c->entry);
  int rc=verify(c);
  if (!controls_done && !rc) {
    after.regs[10][15]^=1;int high=verify(c)!=0;after.regs[10][15]^=1;
    after.regs[31][0]^=1;int preserved=verify(c)!=0;after.regs[31][0]^=1;
    record.pre.vl^=1;int csr=verify(c)!=0;record.pre.vl^=1;
    text("T12_CONTROLS high96=");decimal(high);text(" preserved=");decimal(preserved);text(" csr=");decimal(csr);_putc('\n');
    if (!(high && preserved && csr)) return 23;
    controls_done=1;
  }
  text("T12_CASE id=");text(c->id);text(" repeat=");decimal(repeat);text(" result=");text(rc ? "FAIL" : "PASS");
  text(" verdict=");decimal((unsigned)rc);text(" scratch=");hex(c->scratch);
  text(" pre32_checked=");decimal(!rc);text(" vectors_checked=");decimal(!rc);text(" csr_checked=");decimal(!rc);
  text(" guards=");decimal(guards());text(" traps=");decimal(record.trap_count);text(" cause=");decimal(record.cause);
  text(" epc=");hex(record.epc);text(" expected_pc=");hex((uint64_t)c->fault);text(" tval=");hex(record.tval);
  text(" pre_csr=");csrlog(&record.pre);text(" post_csr=");csrlog(&record.post);
  text(" recovered_csr=");csrlog(&t12_recovery_csrs);text(" recovered_status=");hex(t12_recovery_status);text(" dests=");
  for (unsigned i=10;i<14;++i) { if (i!=10) _putc('/');vector(after.regs[i]); }
  text(" cycle_begin=");decimal(t12_counts[0]);text(" cycle_end=");decimal(t12_counts[1]);
  text(" instret_begin=");decimal(t12_counts[2]);text(" instret_end=");decimal(t12_counts[3]);_putc('\n');
  ++done;return rc;
}
static const struct t12_case *find(const char *scenario,const char *method) {
  for (unsigned i=0;i<sizeof(t12_cases)/sizeof(t12_cases[0]);++i)
    if (t12_cases[i].kind==2 && same(t12_cases[i].scenario,scenario) && same(t12_cases[i].method,method)) return &t12_cases[i];
  return 0;
}
int main(void) {
  uint64_t bytes;
  __asm__ volatile("li t0, 0x200; csrs mstatus, t0; csrr %0, vlenb" : "=r"(bytes) : : "t0","memory");
  text("T12_BEGIN contract=vdot-s8x8-r32-v0.1\n");
  if (bytes!=16) { text("FAIL VLEN\n");return 1; }
  for (unsigned i=0;i<sizeof(t12_cases)/sizeof(t12_cases[0]);++i)
    if (t12_cases[i].kind!=2 && run(&t12_cases[i],0)) return 2;
  const char *scenarios[]={"complete","known-config","independent-batch"};
  for (unsigned i=0;i<3;++i) {
    const struct t12_case *empty=find(scenarios[i],"empty"),*vdot=find(scenarios[i],"vdot"),*rvv=find(scenarios[i],"rvv");
    if (!empty || !vdot || !rvv) return 3;
    if (run(empty,0)) return 4;
    for (unsigned repeat=0;repeat<T12_REPEATS;++repeat) {
      if (run(repeat&1 ? rvv : vdot,repeat) || run(repeat&1 ? vdot : rvv,repeat)) return 5;
    }
  }
  text("T12_SUMMARY executed=");decimal(done);text(" failed=0\n");return 0;
}
