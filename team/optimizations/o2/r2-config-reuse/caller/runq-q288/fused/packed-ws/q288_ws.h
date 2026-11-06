#ifndef XS_Q288_PACKED_WS_H
#define XS_Q288_PACKED_WS_H

#include "q288.h"
#include <stddef.h>

/* Explicit new interface; the original q288_context and its row-major scales
 * are unchanged. RV64/lp64d, VLEN128, FS/VS enabled, FRM=RNE.
 * packed_scale[(tile*9+group)*8+lane] preserves the complete float object
 * representation of original_scale[(tile*8+lane)*9+group].
 * Float pointers need only 4-byte alignment. Slots need 16-byte alignment.
 * Every input, output, slot array and context is disjoint.
 * Kernels retain the original integer/FP order and return state:
 * vl=8, vtype=0, vstart=0, vcsr=7; FRM and scalar callee-saved state preserved.
 * Normal floating-point exception accumulation follows the existing kernel.
 * These entry points neither allocate nor pack scales or quantize inputs.
 */
struct q288_ws_context {
    const int8_t *packed;
    const int8_t *x;
    const float *packed_scale;
    const float *input_scale;
    float *y;
    struct caller_slot *slots;
};

struct q288_ws_pack_context {
    const float *row_major;
    float *packed_scale;
};

_Static_assert(sizeof(float) == 4, "binary32 object size");
_Static_assert(sizeof(struct q288_ws_context) == 48, "new RV64 six-pointer ABI");
_Static_assert(offsetof(struct q288_ws_context, packed_scale) == 16, "scale pointer ABI");
_Static_assert(offsetof(struct q288_ws_context, slots) == 40, "slot pointer ABI");
_Static_assert(sizeof(struct q288_ws_pack_context) == 16, "RV64 pack ABI");

/* Copies 2592 complete 32-bit representations; no FP arithmetic is performed.
 * Source and destination each contain 10368 bytes and must not overlap.
 */
void q288_ws_pack(struct q288_ws_pack_context *);
void q288_ws_vdot(struct q288_ws_context *);
void q288_ws_rvv4(struct q288_ws_context *);

#endif
