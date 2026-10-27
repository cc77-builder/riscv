/* Exact binary32 witnesses for two algebraic rewrites; this is a host probe. */
#include <fenv.h>
#include <inttypes.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static float from_bits(uint32_t bits) {float value;memcpy(&value,&bits,4);return value;}
static uint32_t bits(float value) {uint32_t result;memcpy(&result,&value,4);return result;}
int main(void) {
    if(sizeof(float)!=4 || fesetround(FE_TONEAREST)!=0 || fegetround()!=FE_TONEAREST)return 2;
    volatile float maximum=from_bits(UINT32_C(0x3dc6318c));
    volatile float input=from_bits(UINT32_C(0x3ba24cdb));
    volatile float scale=maximum/127.0f;
    volatile float reciprocal=1.0f/scale;
    volatile float division=input/scale;
    volatile float multiplication=input*reciprocal;
    int q_division=(int)round((double)division),q_multiplication=(int)round((double)multiplication);
    printf("QUANT max=%08" PRIx32 " input=%08" PRIx32 " scale=%08" PRIx32
           " reciprocal=%08" PRIx32 " division=%08" PRIx32 " multiply=%08" PRIx32 " q_div=%d q_mul=%d\n",
           bits(maximum),bits(input),bits(scale),bits(reciprocal),bits(division),bits(multiplication),q_division,q_multiplication);
    if(bits(scale)!=UINT32_C(0x3a47c10e) || bits(division)!=UINT32_C(0x40d00000) ||
       bits(multiplication)!=UINT32_C(0x40cfffff) || q_division!=7 || q_multiplication!=6)return 3;
    volatile float x=from_bits(UINT32_C(0x3b03126f)),denominator=from_bits(UINT32_C(0x3fffbe88));
    volatile float inverse=1.0f/denominator;
    volatile float product=x*inverse,direct=x/denominator;
    printf("SILU_ARITHMETIC x=%08" PRIx32 " denominator=%08" PRIx32 " product=%08" PRIx32 " direct=%08" PRIx32 "\n",
           bits(x),bits(denominator),bits(product),bits(direct));
    if(bits(product)!=UINT32_C(0x3a8333fc) || bits(direct)!=UINT32_C(0x3a8333fd))return 4;
    puts("BINARY32_REWRITE_COUNTEREXAMPLES_PASS host_only fixed_denominator_not_full_silu");
    return 0;
}
