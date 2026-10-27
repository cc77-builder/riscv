#ifndef XS_RUNQ_Q288_FUSED_H
#define XS_RUNQ_Q288_FUSED_H

#include "../q288.h"

/* RV64/lp64d, VLEN128; FS/VS enabled and FRM=RNE on entry.
 * Uses the existing Q288 packed weights and scale layouts. All buffers and
 * the context are disjoint; float pointers are 4-byte aligned and slots are
 * 16-byte aligned. The final eight complete 128-bit slots are overwritten.
 * The context's entry field is ignored. The explicit function selects the
 * integer implementation; there is no runtime dispatch or allocation.
 * Both functions preserve the ordinary scalar/FP ABI, may clobber all vector
 * registers, and return vl=8, vtype=0, vstart=0, vcsr=7. FRM is preserved.
 * See CONTRACT.md and target/RESULT.md for the validated numerical domain
 * and the exact target execution/performance qualification.
 */
_Static_assert(offsetof(struct q288_context, packed) == 0, "packed ABI");
_Static_assert(offsetof(struct q288_context, x) == 8, "input ABI");
_Static_assert(offsetof(struct q288_context, weight_scale) == 16, "weight scale ABI");
_Static_assert(offsetof(struct q288_context, input_scale) == 24, "input scale ABI");
_Static_assert(offsetof(struct q288_context, y) == 32, "output ABI");
_Static_assert(offsetof(struct q288_context, slots) == 40, "complete slots ABI");
_Static_assert(offsetof(struct q288_context, entry) == 48, "retained entry ABI");

void q288_fused_vdot(struct q288_context *);
void q288_fused_rvv4(struct q288_context *);

#endif
