#ifndef XS_SPLIT_GEMV_8X32_H
#define XS_SPLIT_GEMV_8X32_H
#include "caller.h"

/* Optional RV64/lp64d, VLEN128 interface. VS must be enabled.
 * A[256], x[32], slots[8], y[8] and context are valid and disjoint.
 * A/x may have any byte alignment; slots must be 16-byte aligned.
 * Every slot receives int32 sum(A[row,k]*x[k]) and 96 zero high bits.
 * Vector registers/configuration are clobbered as in the parent library.
 * Returns vl=8,vtype=0,vstart=0,vcsr=7. No hidden dispatch or allocation.
 */
typedef void (*split_leaf)(const int8_t *, const int8_t *, struct caller_slot *);
struct split_context {
    const int8_t *a;
    const int8_t *x;
    int32_t *y;
    struct caller_slot *slots;
    split_leaf entry;
};
_Static_assert(sizeof(struct split_context) == 40, "RV64 split context ABI");
void split_full(struct split_context *);
void split_gemv_8x32_vdot(const int8_t *, const int8_t *, struct caller_slot *);
void split_gemv_8x32_rvv0(const int8_t *, const int8_t *, struct caller_slot *);
void split_gemv_8x32_rvv1(const int8_t *, const int8_t *, struct caller_slot *);
void split_gemv_8x32_rvv2(const int8_t *, const int8_t *, struct caller_slot *);
void split_gemv_8x32_rvv3(const int8_t *, const int8_t *, struct caller_slot *);
void split_gemv_8x32_rvv4(const int8_t *, const int8_t *, struct caller_slot *);
#endif
