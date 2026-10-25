#ifndef XS_FIXED_WEIGHT_8X32_H
#define XS_FIXED_WEIGHT_8X32_H
#include "split.h"

#define FIXED_MAX_COUNT 4u
/* GNU C11 / RV64 / VLEN128. Valid count: exactly 1 or 4; others are outside
 * this contract. FIXED_MAX_COUNT is a capacity bound. VS is enabled.
 * A[256], X[count*32], Y[count*8], slots[count*8], packed[288], and context
 * are valid and disjoint. Slots start at a 16-byte boundary; Y is naturally
 * aligned. A and X permit any byte alignment. No allocation/argument checks.
 * All inputs/context are stable for the call. Every step retains full slots.
 * Clobbers vector registers/configuration; returns VL=8,VTYPE=0,VSTART=0,VCSR=7.
 */
struct fixed_context {
    const int8_t *a;
    const int8_t *x;
    int32_t *y;
    struct caller_slot *slots;
    int8_t *packed;
    caller_leaf packed_entry;
    split_leaf split_entry;
    size_t count;
};
_Static_assert(sizeof(struct fixed_context)==64, "RV64 stream context ABI");
void fixed_packed(struct fixed_context *);
void fixed_split(struct fixed_context *);
#endif
