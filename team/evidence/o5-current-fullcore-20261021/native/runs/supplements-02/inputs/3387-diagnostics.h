#ifndef VDOT_DIAGNOSTICS_H
#define VDOT_DIAGNOSTICS_H
#include "harness.h"
struct diagnostic_context {
  const char *id;
  uint32_t word, scratch_mask;
  uint64_t begin_pc, end_pc;
  const struct trap_record *record;
  const unsigned char (*actual)[16], (*expected)[16];
};
void report_diagnostic(const struct diagnostic_context *context);
#endif
