#include <stdint.h>
#include "gemv.h"

struct result_slot { int32_t value; uint32_t high[3]; };
_Static_assert(sizeof(struct result_slot) == 16, "16-byte output slot");

void gemv8(const int8_t a[8][32], const int8_t x[32], int32_t y[8]) {
    _Alignas(16) int8_t packed_ax[8 * 32 + 32];
    _Alignas(16) struct result_slot slots[8];
    for (unsigned r = 0; r < 8; ++r)
        for (unsigned k = 0; k < 32; ++k)
            packed_ax[r * 32 + k] = a[r][k];
    for (unsigned k = 0; k < 32; ++k)
        packed_ax[8 * 32 + k] = x[k];
    config_reuse_gemv_8x32_reuse_vdot(packed_ax, slots);
    for (unsigned r = 0; r < 8; ++r) y[r] = slots[r].value;
}
