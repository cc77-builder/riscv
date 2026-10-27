/* Scalar row-major reference adapted from karpathy/llama2.c runq.c,
 * commit 350e04fe35433e6d2941dce5a1f53308f87058eb, matmul().
 * Copyright (c) 2023 Andrej Karpathy. MIT license: LICENSE.llama2-c.
 * Fixed n=d=288, GS=32, separate pointers instead of QuantizedTensor.
 * The original loop order and floating-point expression are preserved.
 */
#include "q288.h"
__attribute__((noinline,noclone,used))
void q288_oracle(float *xout, const int8_t *xq, const float *xs,
                 const int8_t *wq, const float *ws) {
    for (int i = 0; i < Q288_DIM; ++i) {
        float val = 0.0f;
        int32_t ival = 0;
        int in = i * Q288_DIM;
        for (int j = 0; j <= Q288_DIM - Q288_GS; j += Q288_GS) {
            for (int k = 0; k < Q288_GS; ++k)
                ival += ((int32_t)xq[j+k]) * ((int32_t)wq[in+j+k]);
            val += ((float)ival) * ws[(in+j)/Q288_GS] * xs[j/Q288_GS];
            ival = 0;
        }
        xout[i] = val;
    }
}
