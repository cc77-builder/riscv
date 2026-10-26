#include <stdio.h>
#include <inttypes.h>
#include <errno.h>
#include <fenv.h>
#include "math_eval.h"
#include "math_inputs.h"

int main(void) {
    if (fesetround(FE_TONEAREST)!=0) return 2;
    for (unsigned i=0;i<MATH_CASES;++i) {
        uint64_t out[2];errno=MATH_ERRNO_SENTINEL;feclearexcept(FE_ALL_EXCEPT);
        math_evaluate(&math_inputs[i],out);
        int error=errno,flags=fetestexcept(FE_ALL_EXCEPT);
        printf("%u %016" PRIx64 " %016" PRIx64 " %d %u\n",i,out[0],out[1],error,(unsigned)flags);
    }
    return 0;
}
