/* Host-only adapter. The included upstream reference is not edited. */
#define TESTING
#include "../../upstream/runq.c"
#include <fenv.h>
#include <stdint.h>

int qkv_reference_quantize(float *input,int8_t *output,float *scales) {
    if(fesetround(FE_TONEAREST) || fegetround()!=FE_TONEAREST)return 1;
    GS=32;
    /* Reject before invoking the original float-to-int8 conversion. */
    for(unsigned g=0;g<9;++g) {
        float maximum=0.0f;
        for(unsigned k=0;k<32;++k) {
            float value=input[g*32+k];if(!isfinite(value))return 2;
            float magnitude=fabsf(value);if(magnitude>maximum)maximum=magnitude;
        }
        if(maximum==0.0f)return 3;
        volatile float scale=maximum/127.0f;
        if(!isfinite(scale) || scale<=0.0f)return 4;
        for(unsigned k=0;k<32;++k) {
            volatile float quotient=input[g*32+k]/scale;
            double rounded=round((double)quotient);
            if(!isfinite(quotient) || rounded < -128.0 || rounded > 127.0)return 5;
        }
    }
    QuantizedTensor result={output,scales};
    quantize(&result,input,288);
    return 0;
}
