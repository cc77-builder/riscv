/* The authoritative upstream function is included unchanged, not reimplemented. */
#define TESTING
#include "upstream/runq.c"
#include "w2.h"
__attribute__((noinline,noclone)) void w2_scalar(float *out,const int8_t *weights,
                                               const float *scales,const int8_t *input,const float *xs) {
    QuantizedTensor x={(int8_t*)input,(float*)xs},w={(int8_t*)weights,(float*)scales};
    matmul(out,&x,&w,768,288);
}
