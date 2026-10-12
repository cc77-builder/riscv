#include "harness.h"
#include "diagnostics.h"
#include "cases.h"
#include "baseline-stubs.h"

extern void _putc(char);
#ifndef VDOT_VIRT
extern void _halt(int);
void platform_halt(int code) { _halt(code); for (;;) {} }
#endif
struct trap_record *vdot_active_record;
static struct trap_record record;
struct guarded_regs { uint64_t head[2]; unsigned char regs[32][16]; uint64_t tail[2]; };
static struct guarded_regs before __attribute__((aligned(16)));
static struct guarded_regs after __attribute__((aligned(16)));
static unsigned char expected_regs[32][16];
static const uint64_t canary=UINT64_C(0xD15EA5E5CAFEBABE);

static void text(const char *s) { while (*s) _putc(*s++); }
static void decimal(unsigned v) {
  char b[11]; unsigned n=0;
  do { b[n++]='0'+v%10; v/=10; } while (v);
  while (n) _putc(b[--n]);
}
static void hex64(uint64_t v) {
  text("0x");
  for (int i=60; i>=0; i-=4) _putc("0123456789abcdef"[(v>>i)&15]);
}
static void vector_hex(const unsigned char *v) {
  text("0x");
  for (int i=15; i>=0; --i) { _putc("0123456789abcdef"[v[i]>>4]); _putc("0123456789abcdef"[v[i]&15]); }
}
static void csr_log(const struct vector_csrs *c) {
  hex64(c->vtype); _putc('/'); hex64(c->vl); _putc('/'); hex64(c->vstart);
  _putc('/'); hex64(c->vxrm); _putc('/'); hex64(c->vxsat); _putc('/'); hex64(c->vcsr);
}
static int guards_ok(void) {
  return before.head[0]==canary && before.head[1]==canary && before.tail[0]==canary &&
    before.tail[1]==canary && after.head[0]==canary && after.head[1]==canary &&
    after.tail[0]==canary && after.tail[1]==canary;
}
static enum verdict baseline_judge(const struct run_config *config, unsigned scratch) {
  unsigned char comparable[32][16];
  for (unsigned r=0; r<32; ++r)
    for (unsigned b=0; b<16; ++b)
      comparable[r][b]=(scratch & (1U<<r)) ? after.regs[r][b] : expected_regs[r][b];
  struct expectation e={*config,0,comparable,before.regs};
  return judge(&record,&e,after.regs,guards_ok());
}
static int negative_controls(const struct run_config *config, const struct baseline_site *site, unsigned vd) {
  unsigned clean=0, scratch=0;
  while (clean==vd || (site->scratch_mask & (1U<<clean))) ++clean;
  while (!(site->scratch_mask & (1U<<scratch))) ++scratch;
  after.regs[vd][15]^=1;
  int ok=baseline_judge(config,site->scratch_mask)==VECTOR_CHANGED;
  struct diagnostic_context context={"baseline-negative-high96",site->word,site->scratch_mask,
    (uint64_t)site->begin,(uint64_t)site->end,&record,after.regs,expected_regs};
  report_diagnostic(&context);
  after.regs[vd][15]^=1;
  after.regs[clean][0]^=1;
  ok &= baseline_judge(config,site->scratch_mask)==VECTOR_CHANGED;
  after.regs[clean][0]^=1;
  record.post.vl^=1;
  ok &= baseline_judge(config,site->scratch_mask)==CSR_CHANGED;
  record.post.vl^=1;
  after.regs[scratch][0]^=1;
  ok &= baseline_judge(config,site->scratch_mask)==PASS;
  after.regs[scratch][0]^=1;
  text(ok ? "BASELINE_CONTROLS_PASS high96=detected preserved_register=detected csr=detected declared_scratch=allowed\n" :
            "FAIL baseline controls\n");
  return ok;
}

int main(void) {
  uint64_t bytes;
  __asm__ volatile("li t0, 0x200; csrs mstatus, t0; csrr %0, vlenb" : "=r"(bytes) : : "t0","memory");
  text("BASELINE_BEGIN contract="); text(VDOT_CONTRACT); text(" baseline=rvv-vdot-s8x8-r32-v1\n");
  if (bytes!=16) { text("FAIL VLEN must equal128\n"); return 1; }
  unsigned passed=0, failed=0;
  for (unsigned i=0; i<ARITHMETIC_COUNT; ++i) {
    const struct arithmetic_case *a=&arithmetic_cases[i];
    const struct baseline_site *site=find_baseline(a->word);
    if (!site) { text("FAIL missing baseline site\n"); return 2; }
    unsigned char *p=(unsigned char *)&record;
    for (unsigned b=0; b<sizeof(record); ++b) p[b]=0;
    before.head[0]=before.head[1]=before.tail[0]=before.tail[1]=canary;
    after.head[0]=after.head[1]=after.tail[0]=after.tail[1]=canary;
    for (unsigned r=0; r<32; ++r)
      for (unsigned b=0; b<16; ++b) { before.regs[r][b]=b%2 ? 0xAA : 0x55; after.regs[r][b]=0; }
    for (unsigned b=0; b<16; ++b) before.regs[a->vd][b]=a->old[b];
    for (unsigned b=0; b<16; ++b) before.regs[a->vs1][b]=a->a[b];
    for (unsigned b=0; b<16; ++b) before.regs[a->vs2][b]=a->b[b];
    for (unsigned r=0; r<32; ++r)
      for (unsigned b=0; b<16; ++b) expected_regs[r][b]=before.regs[r][b];
    for (unsigned b=0; b<16; ++b) expected_regs[a->vd][b]=a->expected[b];
    struct run_config config={a->vtype,8,0,a->vxrm,a->vxsat,0,0,a->vs};
    vdot_run(&record,&config,before.regs,after.regs,site->entry);
    enum verdict result=baseline_judge(&config,site->scratch_mask);
    text("BASELINE_CASE id="); text(a->id); text(" result="); text(verdict_name(result));
    text(" instruction="); hex64(a->word); text(" scratch_mask="); hex64(site->scratch_mask);
    text(" pre_csr="); csr_log(&record.pre); text(" post_csr="); csr_log(&record.post);
    text(" expected_vd128="); vector_hex(expected_regs[a->vd]);
    text(" post_vd128="); vector_hex(after.regs[a->vd]);
    text(" pre_mstatus="); hex64(record.pre_status); text(" raw_mstatus="); hex64(record.raw_status);
    text(" trap_count="); decimal((unsigned)record.trap_count);
    text(" protocol_errors="); hex64(record.errors);
    text(" requested_vs="); decimal(a->vs);
    text(" begin_pc="); hex64((uint64_t)site->begin); text(" end_pc="); hex64((uint64_t)site->end);
    text(" all32_except_scratch_checked="); decimal(result==PASS);
    text(" pre32_checked="); decimal(result==PASS);
    text(" guards_ok="); decimal(guards_ok()); _putc('\n');
    if (result!=PASS) {
      struct diagnostic_context context={a->id,a->word,site->scratch_mask,(uint64_t)site->begin,
        (uint64_t)site->end,&record,after.regs,expected_regs};
      report_diagnostic(&context);
    }
    if (result==PASS) ++passed; else ++failed;
    if (i==0 && (result!=PASS || !negative_controls(&config,site,a->vd))) return 3;
  }
  text("BASELINE_SUMMARY contract="); text(VDOT_CONTRACT); text(" baseline=rvv-vdot-s8x8-r32-v1 planned=");
  decimal(ARITHMETIC_COUNT); text(" executed="); decimal(passed+failed);
  text(" passed="); decimal(passed); text(" failed="); decimal(failed); _putc('\n');
  return failed ? 4 : 0;
}
