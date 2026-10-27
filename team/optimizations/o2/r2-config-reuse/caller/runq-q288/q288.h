#ifndef XS_RUNQ_Q288_H
#define XS_RUNQ_Q288_H
#include "split.h"
#define Q288_DIM 288
#define Q288_GS 32
#define Q288_GROUPS 9
#define Q288_TILES 36
#define Q288_WEIGHTS (288 * 288)

/* RV64/lp64d, VLEN128. Enable FS and VS, use FRM=RNE.
 * All arrays/context are disjoint; float pointers are 4-byte aligned,
 * slots are 16-byte aligned. Quantized bytes may have any alignment.
 * Pack once: P[t,g,r,k] = W[(8*t+r)*288 + 32*g+k].
 * Weight scales retain their original row-major [288][9] layout.
 * q288_full overwrites all 288 float outputs; it does not allocate or pack.
 * Strict binary32 order per row: ((float)dot * Ws) * Xs, then +=,
 * groups 0..8. Compile with -ffp-contract=off and without fast math.
 * The selected leaf clobbers vector state and returns vl=8,vtype=0,
 * vstart=0,vcsr=7. FS flags may record normal inexact operations.
 */
struct q288_context {
    const int8_t *packed;
    const int8_t *x;
    const float *weight_scale;
    const float *input_scale;
    float *y;
    struct caller_slot *slots;
    split_leaf entry;
};
struct q288_pack_context { const int8_t *weight; int8_t *packed; };
_Static_assert(sizeof(struct q288_context) == 56, "RV64 consumer ABI");
_Static_assert(sizeof(struct q288_pack_context) == 16, "RV64 pack ABI");
void q288_pack(struct q288_pack_context *);
void q288_full(struct q288_context *);
void q288_oracle(float *, const int8_t *, const float *, const int8_t *, const float *);
#endif
