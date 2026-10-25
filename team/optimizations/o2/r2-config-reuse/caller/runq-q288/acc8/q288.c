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

/* Only the independent row dimension is unrolled. Each output retains the
 * original g=0..8 order and two separately rounded multiplies before its add.
 * All six integer leaves use this same wrapper and unchanged public ABI. */
PUBLIC void q288_full(struct q288_context *c) {
    const int8_t *p = c->packed;
    const int8_t *x = c->x;
    const float *ws = c->weight_scale;
    const float *xs = c->input_scale;
    float *y = c->y;
    struct caller_slot *slots = c->slots;
    split_leaf entry = c->entry;
    for (unsigned t = 0; t < Q288_TILES; ++t) {
        float s0=0.0f, s1=0.0f, s2=0.0f, s3=0.0f;
        float s4=0.0f, s5=0.0f, s6=0.0f, s7=0.0f;
        for (unsigned g = 0; g < Q288_GROUPS; ++g) {
            entry(p, x + Q288_GS*g, slots);
            const float sx = xs[g];
            float a0 = (float)slots[0].value;
            float a1 = (float)slots[1].value;
            float a2 = (float)slots[2].value;
            float a3 = (float)slots[3].value;
            float a4 = (float)slots[4].value;
            float a5 = (float)slots[5].value;
            float a6 = (float)slots[6].value;
            float a7 = (float)slots[7].value;
            a0 = a0 * ws[(8*t+0)*Q288_GROUPS+g];
            a1 = a1 * ws[(8*t+1)*Q288_GROUPS+g];
            a2 = a2 * ws[(8*t+2)*Q288_GROUPS+g];
            a3 = a3 * ws[(8*t+3)*Q288_GROUPS+g];
            a4 = a4 * ws[(8*t+4)*Q288_GROUPS+g];
            a5 = a5 * ws[(8*t+5)*Q288_GROUPS+g];
            a6 = a6 * ws[(8*t+6)*Q288_GROUPS+g];
            a7 = a7 * ws[(8*t+7)*Q288_GROUPS+g];
            a0 = a0 * sx;
            a1 = a1 * sx;
            a2 = a2 * sx;
            a3 = a3 * sx;
            a4 = a4 * sx;
            a5 = a5 * sx;
            a6 = a6 * sx;
            a7 = a7 * sx;
            s0 = s0 + a0;
            s1 = s1 + a1;
            s2 = s2 + a2;
            s3 = s3 + a3;
            s4 = s4 + a4;
            s5 = s5 + a5;
            s6 = s6 + a6;
            s7 = s7 + a7;
            p += 8*Q288_GS;
        }
        y[8*t+0]=s0; y[8*t+1]=s1; y[8*t+2]=s2; y[8*t+3]=s3;
        y[8*t+4]=s4; y[8*t+5]=s5; y[8*t+6]=s6; y[8*t+7]=s7;
    }
}
