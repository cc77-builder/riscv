#include "fixed_entries.h"

/* Caller enables VS. count must be exactly 1 or 4; A[256], X[count*32],
 * Y[count*8] are valid/disjoint. The entry is an explicit caller decision.
 * This example uses local scratch and retains every full intermediate slot.
 */
void fixed_stream_example(const int8_t *a,const int8_t *x,int32_t *y,
                          size_t count,split_leaf entry) {
    _Alignas(16) struct caller_slot slots[FIXED_MAX_COUNT*8];
    int8_t packed[288];
    struct fixed_context context={.a=a,.x=x,.y=y,.slots=slots,.packed=packed,
        .packed_entry=config_reuse_gemv_8x32_reuse_vdot,
        .split_entry=entry,.count=count};
    fixed_split(&context);
}
