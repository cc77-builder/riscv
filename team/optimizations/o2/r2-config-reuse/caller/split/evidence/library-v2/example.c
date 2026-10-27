#include "split.h"

/* The caller enables VS on the qualified RV64/lp64d, VLEN128 platform first.
 * A and x are independent, valid, disjoint int8 buffers; y has 8 int32 values.
 * The selected entry below illustrates the ABI, not a new default decision.
 */
void split_example(const int8_t *a, const int8_t *x, int32_t *y) {
    _Alignas(16) struct caller_slot slots[8];
    struct split_context context = {
        .a=a, .x=x, .y=y, .slots=slots, .entry=split_gemv_8x32_vdot
    };
    split_full(&context);
}
