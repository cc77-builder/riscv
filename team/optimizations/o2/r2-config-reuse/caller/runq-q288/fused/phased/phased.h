#ifndef XS_RUNQ_Q288_PHASED_H
#define XS_RUNQ_Q288_PHASED_H
#include "../fused.h"

/* Same fixed Q288 buffers, ordinary ABI and final vector state as fused.h.
 * Explicit phased scheduling entry; no change to R5 or automatic dispatch.
 * See target/RESULT.md for the exact qualified target experiment. */
void q288_phased_vdot(struct q288_context *);
#endif
