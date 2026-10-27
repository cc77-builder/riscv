#include "q288.h"
#define PUBLIC __attribute__((noinline,noclone,used))

PUBLIC void q288_pack(struct q288_pack_context *c) {
    int8_t *p = c->packed;
    const int8_t *w = c->weight;
    for (unsigned t = 0; t < Q288_TILES; ++t)
        for (unsigned g = 0; g < Q288_GROUPS; ++g)
            for (unsigned r = 0; r < 8; ++r)
                for (unsigned k = 0; k < Q288_GS; ++k)
                    *p++ = w[(8*t+r)*Q288_DIM + Q288_GS*g+k];
}

PUBLIC void q288_full(struct q288_context *c) {
    const int8_t *p = c->packed;
    const int8_t *x = c->x;
    const float *ws = c->weight_scale;
    const float *xs = c->input_scale;
    float *y = c->y;
    struct caller_slot *slots = c->slots;
    split_leaf entry = c->entry;
    for (unsigned t = 0; t < Q288_TILES; ++t) {
        float sums[8] = {0.0f};
        for (unsigned g = 0; g < Q288_GROUPS; ++g) {
            entry(p, x + Q288_GS*g, slots);
            const float sx = xs[g];
            for (unsigned r = 0; r < 8; ++r) {
                float term = (float)slots[r].value;
                term = term * ws[(8*t+r)*Q288_GROUPS+g];
                term = term * sx;
                sums[r] = sums[r] + term;
            }
            p += 8*Q288_GS;
        }
        for (unsigned r = 0; r < 8; ++r) y[8*t+r] = sums[r];
    }
}
