/* T10 integration smoke reuses the independently checked T05 data/trap judge.
 * Full T11/T12 coverage still uses vdot-exceptions and check-vdot-run.py.
 */
#include <klib.h>
#include "harness.h"
#include "diagnostics.h"
#include "cases.h"
#include "stubs.h"

extern void _halt(int);
void platform_halt(int code) { _halt(code); for (;;) {} }
struct trap_record *vdot_active_record;
static struct trap_record record;
struct guarded { uint64_t head[2]; unsigned char regs[32][16]; uint64_t tail[2]; };
static struct guarded before __attribute__((aligned(16))), after __attribute__((aligned(16)));
static unsigned char expected[32][16];
static unsigned completed;
static const uint64_t canary = UINT64_C(0xD15EA5E5CAFEBABE);

static void reset(void) {
  memset(&record, 0, sizeof(record));
  before.head[0]=before.head[1]=before.tail[0]=before.tail[1]=canary;
  after.head[0]=after.head[1]=after.tail[0]=after.tail[1]=canary;
  for (unsigned r=0; r<32; ++r) for (unsigned b=0; b<16; ++b) {
    before.regs[r][b]=b%2 ? 0xAA : 0x55; after.regs[r][b]=0;
  }
}
static int selected(const char *id, const char *const *ids, unsigned n) {
  for (unsigned i=0; i<n; ++i) if (!strcmp(id, ids[i])) return 1;
  return 0;
}
static int run(const char *id, unsigned word, const struct run_config *cfg, uint64_t cause) {
  void (*stub)(void)=find_stub(word);
  if (!stub) return 1;
  record.expected_cause=cause;
  vdot_run(&record,cfg,before.regs,after.regs,stub);
  int guards=before.head[0]==canary && before.head[1]==canary && before.tail[0]==canary &&
    before.tail[1]==canary && after.head[0]==canary && after.head[1]==canary &&
    after.tail[0]==canary && after.tail[1]==canary;
  struct expectation e={*cfg,cause,expected,before.regs};
  enum verdict verdict=judge(&record,&e,after.regs,guards);
  printf("T10_CASE id=%s result=%s cause=%d all32=%d pre32=%d\n",id,verdict_name(verdict),(int)record.cause,
    verdict==PASS,verdict==PASS);
  if (verdict!=PASS) {
    struct diagnostic_context context={id,word,0,record.expected_pc,record.resume_pc,&record,after.regs,expected};
    report_diagnostic(&context); return 2;
  }
  ++completed; return 0;
}
static int legal(const struct arithmetic_case *a, unsigned vs, const char *id) {
  reset();
  memcpy(before.regs[a->vd],a->old,16); memcpy(before.regs[a->vs1],a->a,16); memcpy(before.regs[a->vs2],a->b,16);
  memcpy(expected,before.regs,sizeof(expected)); memcpy(expected[a->vd],a->expected,16);
  struct run_config cfg={a->vtype,8,0,a->vxrm,a->vxsat,0,0,vs};
  return run(id,a->word,&cfg,0);
}
int main(void) {
  uint64_t bytes;
  __asm__ volatile("li t0, 0x200; csrs mstatus, t0; csrr %0, vlenb" : "=r"(bytes) : : "t0","memory");
  if (bytes!=16) return 1;
  printf("T10_BEGIN contract=%s full_width=128\n",VDOT_CONTRACT);
  const char *const legal_ids[]={"D03","D05","D07","L04-0-8-9","L04-10-0-9","L04-10-8-0",
    "L04-0-0-9","L04-31-31-31","L05-3-ff"};
  for (unsigned i=0; i<ARITHMETIC_COUNT; ++i) {
    const struct arithmetic_case *a=&arithmetic_cases[i];
    if (!selected(a->id,legal_ids,sizeof(legal_ids)/sizeof(legal_ids[0]))) continue;
    if (legal(a,a->vs,a->id)) return 2;
    if (!strcmp(a->id,"D03") && legal(a,2,"clean-vs")) return 3;
  }
  const char *const illegal_ids[]={"X02-m2","X02-mf2","X03-vl0","X03-vl7","X04-vstart1",
    "X05-vill","X06-VS-off","X07-vm0","X09-v0","X11-VS-1"};
  for (unsigned i=0; i<EXCEPTION_COUNT; ++i) {
    const struct exception_case *x=&exception_cases_data[i];
    if (!selected(x->id,illegal_ids,sizeof(illegal_ids)/sizeof(illegal_ids[0]))) continue;
    reset();
    for (unsigned b=0; b<16; ++b) {
      before.regs[x->vs1][b]=b<8 ? 0xFF : 0xA5;
      if (x->vs2!=x->vs1) before.regs[x->vs2][b]=b<8 ? 1 : 0x5A;
    }
    memcpy(expected,before.regs,sizeof(expected));
    struct run_config cfg={x->vtype,x->vl,x->vstart,x->vxrm,x->vxsat,x->vs_off,0,x->vs};
    if (run(x->id,x->word,&cfg,2)) return 4;
  }
  if (completed!=20) return 5;
  printf("T10_CORE_SMOKE_PASS legal=10 illegal=10 all32=20 pre32=20\n");
  return 0;
}
