#ifndef R2_REAL_W2_H
#define R2_REAL_W2_H
#include <stdint.h>
#include <stddef.h>
/* Fixed RV64/lp64d, VLEN128, M288/K768, GS32, RNE; FS/VS enabled.
 * Pack P[t,g,r,k] = W[(8*t+r)*768 + 32*g+k], 36*24*8*32 bytes.
 * Scales remain row-major [288][24]; x has 768 int8 and 24 FP32 scales.
 * All spans/context are disjoint. Float pointers are 4-byte aligned and slots
 * 16-byte aligned. Each call overwrites all 288 outputs. Groups 0..23 retain
 * separate binary32 cast, multiply Ws, multiply Xs, then left-fold add.
 * No packing/quantization/allocation in the kernels; vector registers clobbered.
 * Return vl=8,vtype=0,vstart=0; vcsr is preserved (profile enters with 7).
 * Slots hold the last 8 dot32 values in
 * low32 and zero high96. No default consumer or R5 dispatch is changed.
 */
struct w2_slot { uint32_t word[4]; } __attribute__((aligned(16)));
struct w2_context {
    const int8_t *packed,*x;
    const float *weight_scale,*input_scale;
    float *y;
    struct w2_slot *slots;
    void *reserved;
};
_Static_assert(sizeof(struct w2_context)==56,"RV64 context");
_Static_assert(offsetof(struct w2_context,slots)==40,"assembly slot offset");
void q768_fr(struct w2_context *);
void q768_ta(struct w2_context *);
void w2_scalar(float *,const int8_t *,const float *,const int8_t *,const float *);
#endif
