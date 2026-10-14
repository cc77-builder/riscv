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
/* Optional sparse diagnosis, outside the measured assembly kernels. */
static void phase(unsigned seq, const char *name) {
#ifdef T12_DIAG
  text("T12_PHASE seq="); decimal(seq); text(" at="); text(name); _putc('\n');
#else
  (void)seq; (void)name;
#endif
}
static void vector(const unsigned char *p) {
  for (int i=15;i>=0;--i) { _putc("0123456789abcdef"[p[i]>>4]); _putc("0123456789abcdef"[p[i]&15]); }
}
static void zero(void *p, size_t n) {
  unsigned char *q=p;
  if (((uintptr_t)q & 7)==0) {
    const uint64_t z=0;
    q=__builtin_assume_aligned(q,8);
    while(n>=8) { __builtin_memcpy(q,&z,8); q+=8; n-=8; }
  }
  while(n--) *q++=0;
}
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
  struct expectation e={config,c->fault_vl>=0 ? 2 : 0,c->expected,c->before};
  struct vector_csrs fault={0,(uint64_t)c->fault_vl,0,3,1,7};
  if (c->fault_vl>=0) {
    struct vector_csrs recovered={0,8,0,3,1,7};
    if (!eq(&record.post,&fault,sizeof(fault)) || !eq(&t12_recovery_csrs,&recovered,sizeof(recovered)) ||
        ((t12_recovery_status>>9)&3)!=3 || record.epc!=(uint64_t)c->fault || record.expected_pc!=(uint64_t)c->fault || record.tval!=0) return 20;
  }
  int rc=(int)judge_with_scratch(&record,&e,after.regs,guards(),c->scratch,
                                c->fault_vl>=0 ? &fault : 0);
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
#ifndef T12_START
#define T12_START 0
#endif
#ifndef T12_COUNT
#define T12_COUNT T12_PLAN_COUNT
#endif
static unsigned done;
/* A bit is set only after the exact full-state judge succeeds. This is an
 * ordered result bitmap, not a probabilistic state hash. The generated plan
 * maps every bit to one (id, repeat), and the host requires the exact bitmap. */
static unsigned char passed_bits[(T12_PLAN_COUNT+7)/8];

static int controls_done;
static int run(const struct t12_case *c,unsigned repeat,unsigned seq) {
  if (seq>=T12_PLAN_COUNT || (passed_bits[seq/8] & (1U<<(seq%8)))) return 24;
  zero(&record,sizeof(record));zero(t12_counts,sizeof(t12_counts));
  zero(&t12_recovery_csrs,sizeof(t12_recovery_csrs));t12_recovery_status=0;zero(t12_sink,sizeof(t12_sink));
  zero(&after,sizeof(after));after.head[0]=after.head[1]=after.tail[0]=after.tail[1]=canary;
  phase(seq,"enter");
  vdot_run(&record,&config,c->before,after.regs,c->entry);
  phase(seq,"returned");
  int rc=verify(c);
  phase(seq,"verified");
  if (!controls_done && !rc) {
    after.regs[10][15]^=1;int high=verify(c)!=0;after.regs[10][15]^=1;
    after.regs[31][0]^=1;int preserved=verify(c)!=0;after.regs[31][0]^=1;
    record.pre.vl^=1;int csr=verify(c)!=0;record.pre.vl^=1;
    text("T12_CONTROLS high96=");decimal(high);text(" preserved=");decimal(preserved);text(" csr=");decimal(csr);_putc('\n');
    if (!(high && preserved && csr)) return 23;
    controls_done=1;
  }
  if (!rc) {
    passed_bits[seq/8] |= 1U<<(seq%8);
    if(c->kind==2) {
      text("T12R_PERF seq="); decimal(seq);
      text(" cy="); decimal(t12_counts[0]); _putc(','); decimal(t12_counts[1]);
      text(" ir="); decimal(t12_counts[2]); _putc(','); decimal(t12_counts[3]); _putc('\n');
    }
    ++done; return 0;
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
int main(void) {
  uint64_t bytes;
  __asm__ volatile("li t0, 0x200; csrs mstatus, t0; csrr %0, vlenb" : "=r"(bytes) : : "t0","memory");
  text("T12R_BEGIN start="); decimal(T12_START); text(" limit="); decimal(T12_COUNT); _putc('\n');
  if (bytes!=16) { text("FAIL VLEN\n");return 1; }
  if (T12_START>=T12_PLAN_COUNT || T12_COUNT==0 || T12_COUNT>T12_PLAN_COUNT-T12_START) return 6;
  for (unsigned seq=T12_START;seq<T12_START+T12_COUNT;++seq)
    if (run(&t12_cases[t12_plan[seq].index],t12_plan[seq].repeat,seq)) return 2;
  text("T12R_END executed="); decimal(done); text(" bits=");
  for (unsigned i=0;i<sizeof(passed_bits);++i) {
    _putc("0123456789abcdef"[passed_bits[i]>>4]);
    _putc("0123456789abcdef"[passed_bits[i]&15]);
  }
  _putc('\n'); return 0;
}
