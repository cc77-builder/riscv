#include "harness.h"

const char *verdict_name(enum verdict value) {
  static const char *names[] = {"PASS","UNREACHABLE","TRAP_PROTOCOL","TRAP_COUNT",
    "CAUSE","FAULT_PC","CSR_CHANGED","VECTOR_CHANGED","GUARD_CHANGED","CAPTURE_PHASE","VS_CHANGED","PRE_VECTOR_CHANGED"};
  return (unsigned)value < sizeof(names)/sizeof(names[0]) ? names[value] : "UNKNOWN";
}

static int same_csrs(const struct vector_csrs *a, const struct vector_csrs *b) {
  return a->vtype==b->vtype && a->vl==b->vl && a->vstart==b->vstart &&
         a->vxrm==b->vxrm && a->vxsat==b->vxsat && a->vcsr==b->vcsr;
}

/* Exact equality, including every bit. memcpy avoids type-punning UB; the
 * alignment branch keeps this API valid for arbitrary byte-array callers. */
static int same_vector(const unsigned char *a, const unsigned char *b) {
  if ((((uintptr_t)a | (uintptr_t)b) & 7)==0) {
    uint64_t a0,a1,b0,b1;
    a=__builtin_assume_aligned(a,8); b=__builtin_assume_aligned(b,8);
    __builtin_memcpy(&a0,a,8); __builtin_memcpy(&a1,a+8,8);
    __builtin_memcpy(&b0,b,8); __builtin_memcpy(&b1,b+8,8);
    return a0==b0 && a1==b1;
  }
  for (unsigned i=0;i<16;++i) if (a[i]!=b[i]) return 0;
  return 1;
}

enum verdict judge_with_scratch(const struct trap_record *r, const struct expectation *e,
                   const unsigned char actual[32][16], int guards_ok,
                   uint32_t scratch, const struct vector_csrs *post) {
  const struct run_config *c = &e->config;
  uint64_t type = c->vtype & 0x100 ? UINT64_C(1)<<63 : c->vtype;
  uint64_t vl = c->vtype & 0x100 ? 0 : c->vl;
  if (r->errors) return TRAP_PROTOCOL;
  if (r->pre.vtype!=type || r->pre.vl!=vl || r->pre.vstart!=c->vstart ||
      r->pre.vxrm!=c->vxrm || r->pre.vxsat!=c->vxsat ||
      r->pre.vcsr!=((c->vxrm<<1)|c->vxsat) ||
      ((r->pre_status>>9)&3)!=(c->vs_off ? 0 : c->vs)) return UNREACHABLE;
  if (e->before && r->pre_valid!=1) return PRE_VECTOR_CHANGED;
  if (e->before)
    for (unsigned reg=0; reg<32; ++reg)
      if (!same_vector(r->pre_regs[reg],e->before[reg])) return PRE_VECTOR_CHANGED;
  if (r->trap_count != (e->cause ? 1U : 0U)) return TRAP_COUNT;
  if (e->cause && r->cause!=e->cause) return CAUSE;
  if (e->cause && r->epc!=r->expected_pc) return FAULT_PC;
  if (r->phase != (c->vs_off ? 2U : 1U)) return CAPTURE_PHASE;
  if (c->vs_off && ((r->raw_status>>9)&3)!=0) return VS_CHANGED;
  if (!e->cause && ((r->raw_status>>9)&3)!=3) return VS_CHANGED;
  if (e->cause && !c->vs_off && ((r->raw_status>>9)&3)!=c->vs && ((r->raw_status>>9)&3)!=3)
    return VS_CHANGED;
  if (!same_csrs(post ? post : &r->pre,&r->post)) return CSR_CHANGED;
  for (unsigned reg=0; reg<32; ++reg)
    if (!(scratch & (UINT32_C(1)<<reg)) && !same_vector(actual[reg],e->regs[reg])) return VECTOR_CHANGED;
  if (!guards_ok) return GUARD_CHANGED;
  return PASS;
}

enum verdict judge(const struct trap_record *r, const struct expectation *e,
                   const unsigned char actual[32][16], int guards_ok) {
  return judge_with_scratch(r,e,actual,guards_ok,0,0);
}
