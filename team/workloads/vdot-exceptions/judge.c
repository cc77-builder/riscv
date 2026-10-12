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

enum verdict judge(const struct trap_record *r, const struct expectation *e,
                   const unsigned char actual[32][16], int guards_ok) {
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
      for (unsigned byte=0; byte<16; ++byte)
        if (r->pre_regs[reg][byte]!=e->before[reg][byte]) return PRE_VECTOR_CHANGED;
  if (r->trap_count != (e->cause ? 1U : 0U)) return TRAP_COUNT;
  if (e->cause && r->cause!=e->cause) return CAUSE;
  if (e->cause && r->epc!=r->expected_pc) return FAULT_PC;
  if (r->phase != (c->vs_off ? 2U : 1U)) return CAPTURE_PHASE;
  if (c->vs_off && ((r->raw_status>>9)&3)!=0) return VS_CHANGED;
  if (!e->cause && ((r->raw_status>>9)&3)!=3) return VS_CHANGED;
  if (e->cause && !c->vs_off && ((r->raw_status>>9)&3)!=c->vs && ((r->raw_status>>9)&3)!=3)
    return VS_CHANGED;
  if (!same_csrs(&r->pre,&r->post)) return CSR_CHANGED;
  for (unsigned reg=0; reg<32; ++reg)
    for (unsigned byte=0; byte<16; ++byte)
      if (actual[reg][byte]!=e->regs[reg][byte]) return VECTOR_CHANGED;
  if (!guards_ok) return GUARD_CHANGED;
  return PASS;
}
