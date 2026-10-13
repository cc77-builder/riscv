#include "harness.h"
#include "diagnostics.h"
#include "cases.h"
#include "stubs.h"

#ifndef VDOT_MODE_SELFTEST
#define VDOT_MODE_SELFTEST 0
#endif
#ifndef VDOT_LOG_COMPACT
#define VDOT_LOG_COMPACT 0
#endif
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
static unsigned passed, failed, unreachable, executed;
static const uint64_t canary = UINT64_C(0xD15EA5E5CAFEBABE);

static void text(const char *s) { while (*s) _putc(*s++); }
#if !VDOT_LOG_COMPACT
static void hex64(uint64_t v) {
  text("0x");
  for (int shift=60; shift>=0; shift-=4) _putc("0123456789abcdef"[(v>>shift)&15]);
}
#endif
static void decimal(unsigned v) {
  char buffer[11]; unsigned n=0;
  do { buffer[n++]='0'+v%10; v/=10; } while (v);
  while (n) _putc(buffer[--n]);
}
#if !VDOT_LOG_COMPACT
static void vector_hex(const unsigned char *v) {
  text("0x");
  for (int i=15; i>=0; --i) {
    _putc("0123456789abcdef"[v[i]>>4]); _putc("0123456789abcdef"[v[i]&15]);
  }
}
static void csr_log(const char *prefix, const struct vector_csrs *c) {
  text(prefix); hex64(c->vtype); _putc('/'); hex64(c->vl); _putc('/'); hex64(c->vstart);
  _putc('/'); hex64(c->vxrm); _putc('/'); hex64(c->vxsat); _putc('/'); hex64(c->vcsr);
}
#endif
static void reset(void) {
  unsigned char *p=(unsigned char *)&record;
  for (unsigned i=0; i<sizeof(record); ++i) p[i]=0;
  before.head[0]=before.head[1]=before.tail[0]=before.tail[1]=canary;
  after.head[0]=after.head[1]=after.tail[0]=after.tail[1]=canary;
  for (unsigned r=0; r<32; ++r)
    for (unsigned b=0; b<16; ++b) { before.regs[r][b]=b%2 ? 0xAA : 0x55; after.regs[r][b]=0; }
}
static int guards_ok(void) {
  return before.head[0]==canary && before.head[1]==canary && before.tail[0]==canary &&
    before.tail[1]==canary && after.head[0]==canary && after.head[1]==canary &&
    after.tail[0]==canary && after.tail[1]==canary;
}
static void copy_expected(void) {
  for (unsigned r=0; r<32; ++r)
    for (unsigned b=0; b<16; ++b) expected_regs[r][b]=before.regs[r][b];
}
static void setup_sources(unsigned vd, unsigned vs1, unsigned vs2) {
  for (unsigned b=0; b<16; ++b) before.regs[vd][b]=255;
  for (unsigned b=0; b<16; ++b) before.regs[vs1][b]=b<8 ? 255 : 0xA5;
  if (vs1!=vs2) for (unsigned b=0; b<16; ++b) before.regs[vs2][b]=b<8 ? 1 : 0x5A;
}
/* Lossless encoding of the exact verbose fields, not a replacement judge.
 * Each value is either an earlier value index (0..33), or 0x80 plus unsigned
 * LEB128. Base64 is only the transport encoding. The host reconstructs all
 * fields and executes the unchanged semantic checker. */
#if VDOT_LOG_COMPACT
static uint64_t read_le64(const unsigned char *p) {
  uint64_t v=0; for (unsigned i=0;i<8;++i) v|=(uint64_t)p[i]<<(8*i); return v;
}
static void packed_case(const char *id, unsigned word, unsigned vd,
                        const struct run_config *cfg, uint64_t cause,
                        enum verdict result, int report) {
  const uint64_t values[34]={word,record.trap_count,cause,record.cause,
    record.expected_pc,record.epc,record.resume_pc,record.tval,
    record.pre_status,record.raw_status,record.phase,record.errors,
    cfg->vs_off ? 0 : cfg->vs,
    record.pre.vtype,record.pre.vl,record.pre.vstart,record.pre.vxrm,record.pre.vxsat,record.pre.vcsr,
    record.post.vtype,record.post.vl,record.post.vstart,record.post.vxrm,record.post.vxsat,record.post.vcsr,
    read_le64(before.regs[vd]),read_le64(before.regs[vd]+8),
    read_le64(expected_regs[vd]),read_le64(expected_regs[vd]+8),
    read_le64(after.regs[vd]),read_le64(after.regs[vd]+8),
    result==PASS || result==GUARD_CHANGED,result==PASS || result==GUARD_CHANGED,(unsigned)guards_ok()};
  unsigned char bytes[34*11]; unsigned count=0;
  for (unsigned i=0;i<34;++i) {
    unsigned ref=0; while(ref<i && values[ref]!=values[i])++ref;
    if(ref<i){bytes[count++]=(unsigned char)ref;continue;}
    bytes[count++]=0x80;
    uint64_t v=values[i];
    do { unsigned char part=v&127; v>>=7; bytes[count++]=part|(v ? 128 : 0); } while(v);
  }
  static const char alphabet[]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  text(report ? "VDOT_PACKED id=" : "HARNESS_PACKED id=");text(id);
  text(" result=");text(verdict_name(result));text(" payload=");
  for(unsigned i=0;i<count;i+=3){
    unsigned rem=count-i;
    uint32_t x=(uint32_t)bytes[i]<<16;
    if(rem>1)x|=(uint32_t)bytes[i+1]<<8;
    if(rem>2)x|=bytes[i+2];
    _putc(alphabet[(x>>18)&63]);_putc(alphabet[(x>>12)&63]);
    _putc(rem>1 ? alphabet[(x>>6)&63] : '=');_putc(rem>2 ? alphabet[x&63] : '=');
  }
  _putc('\n');
}
#endif

static enum verdict run(const char *id, unsigned word, unsigned vd, const struct run_config *cfg,
                        uint64_t cause, int negative_destination, int report) {
  void (*stub)(void)=find_stub(word);
  if (!stub) { text("FAIL missing_fixed_instruction_stub\n"); platform_halt(90); }
  record.expected_cause=cause;
  vdot_run(&record,cfg,before.regs,after.regs,stub);
  if (negative_destination==1) expected_regs[vd][15]^=1;
  if (negative_destination==2) record.raw_status=(record.raw_status & ~UINT64_C(0x600))|0x200;
  struct expectation e={*cfg,cause,expected_regs,before.regs};
  enum verdict result=judge(&record,&e,after.regs,guards_ok());
#if VDOT_LOG_COMPACT
  packed_case(id,word,vd,cfg,cause,result,report);
#else
  text(report ? "VDOT_CASE id=" : "HARNESS_NEGATIVE id="); text(id);
  text(" result="); text(verdict_name(result)); text(" instruction="); hex64(word);
  text(" trap_count="); decimal((unsigned)record.trap_count);
  text(" expected_cause="); hex64(cause); text(" actual_cause="); hex64(record.cause);
  text(" fault_pc="); hex64(record.expected_pc); text(" actual_epc="); hex64(record.epc);
  text(" resume_pc="); hex64(record.resume_pc); text(" mtval="); hex64(record.tval);
  text(" pre_mstatus="); hex64(record.pre_status); text(" raw_mstatus="); hex64(record.raw_status);
  text(" capture_phase="); decimal((unsigned)record.phase);
  text(" protocol_errors="); hex64(record.errors);
  text(" requested_vs="); decimal(cfg->vs_off ? 0 : (unsigned)cfg->vs);
  csr_log(" pre_csr=",&record.pre); csr_log(" post_csr=",&record.post);
  text(" pre_vd128="); vector_hex(before.regs[vd]);
  text(" expected_vd128="); vector_hex(expected_regs[vd]);
  text(" post_vd128="); vector_hex(after.regs[vd]);
  text(" all32_checked="); decimal(result==PASS || result==GUARD_CHANGED);
  text(" pre32_checked="); decimal(result==PASS || result==GUARD_CHANGED);
  text(" guards_ok="); decimal((unsigned)guards_ok()); _putc('\n');
#endif
  if (result!=PASS && (!VDOT_LOG_COMPACT || report)) {
    struct diagnostic_context context={id,word,0,record.expected_pc,record.resume_pc,&record,after.regs,expected_regs};
    report_diagnostic(&context);
  }
  if (report) {
    ++executed;
    if (result==PASS) ++passed;
    else if (result==UNREACHABLE) ++unreachable;
    else ++failed;
  }
  return result;
}

static int selftests(void) {
  struct run_config cfg={0,8,0,3,1,0,0,3};
  for (unsigned i=0; i<7; ++i) {
    reset(); setup_sources(10,8,9); copy_expected();
    cfg.vtype=i==4 ? 0x100 : 0; cfg.vstart=i==3 ? 7 : 0; cfg.vs_off=i==2;
    cfg.vs=i==5 ? 1 : i==6 ? 2 : 3;
    int legal=i==0 || i>=5;
    unsigned word=legal ? 0x02940557 : 0x00100073;
    if (legal) for (unsigned b=0; b<8; ++b) expected_regs[10][b]=0;
    const char *names[]={"H00-vadd-control","H01-ebreak","H02-VS-off","H03-vstart7","H04-vill","H05-vadd-initial","H06-vadd-clean"};
    if (run(names[i],word,10,&cfg,legal ? 0 : 3,0,1)!=PASS) return 0;
  }
  cfg=(struct run_config){0,8,0,0,0,0,4,3};
  reset(); setup_sources(10,8,9); copy_expected();
  if (run("N01-wrong-pc",0x00100073,10,&cfg,3,0,0)!=TRAP_PROTOCOL || record.errors!=ERR_PC) return 0;
  cfg.pc_bias=0;
  reset(); setup_sources(10,8,9); copy_expected();
  if (run("N02-wrong-high-byte",0x00100073,10,&cfg,3,1,0)!=VECTOR_CHANGED) return 0;
  reset(); setup_sources(10,8,9); copy_expected();
  if (run("N03-wrong-vs",0x00100073,10,&cfg,3,2,0)!=VS_CHANGED) return 0;
  text("HARNESS_SELFTEST_PASS cases=7 negative_controls=3\n");
  return 1;
}

static void exception_cases(void) {
  for (unsigned i=0; i<EXCEPTION_COUNT; ++i) {
    const struct exception_case *e=&exception_cases_data[i];
    struct run_config c={e->vtype,e->vl,e->vstart,e->vxrm,e->vxsat,e->vs_off,0,e->vs};
    reset(); setup_sources(e->vd,e->vs1,e->vs2);
    if (e->alternating)
      for (unsigned b=0; b<16; ++b) before.regs[e->vd][b]=b%2 ? 0xAA : 0x55;
    copy_expected(); (void)run(e->id,e->word,e->vd,&c,2,0,1);
  }
}

static void summary(const char *mode, unsigned planned) {
  text("VDOT_SUMMARY mode="); text(mode); text(" contract="); text(VDOT_CONTRACT);
  text(" planned="); decimal(planned); text(" executed="); decimal(executed);
  text(" passed="); decimal(passed); text(" failed="); decimal(failed);
  text(" unreachable="); decimal(unreachable); _putc('\n');
}

int main(void) {
  uint64_t bytes;
  __asm__ volatile("li t0, 0x200; csrs mstatus, t0; csrr %0, vlenb" : "=r"(bytes) : : "t0","memory");
  text("VDOT_BEGIN contract="); text(VDOT_CONTRACT); text(" mode=");
  text(VDOT_MODE_SELFTEST ? "selftest\n" : "full\n");
  if (VDOT_LOG_COMPACT) text("VDOT_LOG_FORMAT packed-u64-v1\n");
  if (bytes!=16) { text("FAIL VLEN must equal128\n"); return 1; }
  if (!selftests()) { summary("selftest",7); return 2; }
  if (VDOT_MODE_SELFTEST) { summary("selftest",7); return 0; }
  passed=failed=unreachable=executed=0;
  text("VDOT_EXTENSION_BEGIN\n");
  for (unsigned i=0; i<ARITHMETIC_COUNT; ++i) {
    const struct arithmetic_case *a=&arithmetic_cases[i];
    reset();
    for (unsigned b=0; b<16; ++b) before.regs[a->vd][b]=a->old[b];
    for (unsigned b=0; b<16; ++b) before.regs[a->vs1][b]=a->a[b];
    for (unsigned b=0; b<16; ++b) before.regs[a->vs2][b]=a->b[b];
    copy_expected(); for (unsigned b=0; b<16; ++b) expected_regs[a->vd][b]=a->expected[b];
    struct run_config cfg={a->vtype,8,0,a->vxrm,a->vxsat,0,0,a->vs};
    enum verdict result=run(a->id,a->word,a->vd,&cfg,0,0,1);
    /* A failing legal control invalidates subsequent extension exception claims. */
    if (result!=PASS) { summary("full",ARITHMETIC_COUNT+EXCEPTION_COUNT); return 3; }
  }
  exception_cases(); summary("full",ARITHMETIC_COUNT+EXCEPTION_COUNT);
  return failed || unreachable || executed!=ARITHMETIC_COUNT+EXCEPTION_COUNT ? 4 : 0;
}
