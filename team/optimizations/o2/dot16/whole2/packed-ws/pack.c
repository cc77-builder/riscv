#include "packed_ws.h"

/* Character accesses copy the complete representation without evaluating a
 * float, changing a NaN payload, rounding, or using an incompatible lvalue.
 * Preconditions: non-null complete disjoint spans, fixed dimensions as below.
 */
static void prepare(unsigned char *restrict dst,
                    const unsigned char *restrict src, unsigned groups) {
    for (unsigned tile=0; tile<36; ++tile)
        for (unsigned group=0; group<groups; ++group)
            for (unsigned lane=0; lane<8; ++lane) {
                unsigned to=((tile*groups+group)*8+lane)*4;
                unsigned from=((tile*8+lane)*groups+group)*4;
                for (unsigned byte=0; byte<4; ++byte)
                    dst[to+byte]=src[from+byte];
            }
}

void q288_prepare_packed_ws(struct q288_packed_ws_scales *restrict dst,
                          const float *restrict src) {
    prepare((unsigned char*)dst, (const unsigned char*)src, 9);
}

void q768_prepare_packed_ws(struct q768_packed_ws_scales *restrict dst,
                          const float *restrict src) {
    prepare((unsigned char*)dst, (const unsigned char*)src, 24);
}
