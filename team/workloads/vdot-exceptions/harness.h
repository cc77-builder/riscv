#ifndef VDOT_HARNESS_H
#define VDOT_HARNESS_H
#include <stdint.h>
#include <stddef.h>
#include "layout.h"

struct vector_csrs { uint64_t vtype, vl, vstart, vxrm, vxsat, vcsr; };
struct trap_record {
  uint64_t expected_pc, resume_pc, expected_cause, armed, trap_count;
  uint64_t cause, epc, tval, raw_status, errors, in_handler, phase, abort_pc;
  struct vector_csrs pre, post;
  uint64_t pre_status;
};
struct run_config { uint64_t vtype, vl, vstart, vxrm, vxsat, vs_off, pc_bias; };
struct expectation {
  struct run_config config;
  uint64_t cause;
  const unsigned char (*regs)[16];
};
enum verdict {
  PASS, UNREACHABLE, TRAP_PROTOCOL, TRAP_COUNT, CAUSE, FAULT_PC,
  CSR_CHANGED, VECTOR_CHANGED, GUARD_CHANGED, CAPTURE_PHASE, VS_CHANGED
};
const char *verdict_name(enum verdict value);
enum verdict judge(const struct trap_record *record, const struct expectation *expected,
                   const unsigned char actual[32][16], int guards_ok);
void vdot_run(struct trap_record *, const struct run_config *, const unsigned char [32][16],
              unsigned char [32][16], void (*stub)(void));
void platform_halt(int code) __attribute__((noreturn));
extern struct trap_record *vdot_active_record;

#define VERIFY_OFFSET(type, member, offset) _Static_assert(offsetof(type,member)==offset, #member " ABI offset")
VERIFY_OFFSET(struct trap_record, expected_pc, REC_EXPECTED_PC);
VERIFY_OFFSET(struct trap_record, trap_count, REC_TRAP_COUNT);
VERIFY_OFFSET(struct trap_record, errors, REC_ERRORS);
VERIFY_OFFSET(struct trap_record, phase, REC_PHASE);
VERIFY_OFFSET(struct trap_record, pre, REC_PRE_CSR);
VERIFY_OFFSET(struct trap_record, post, REC_POST_CSR);
VERIFY_OFFSET(struct trap_record, pre_status, REC_PRE_STATUS);
_Static_assert(sizeof(struct trap_record)==208,"record ABI size");
VERIFY_OFFSET(struct run_config, vs_off, CFG_VS_OFF);
VERIFY_OFFSET(struct run_config, pc_bias, CFG_PC_BIAS);
#endif
