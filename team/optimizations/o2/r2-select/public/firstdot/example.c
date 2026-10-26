#include <stdint.h>
#include "selected_gemv.h"

_Static_assert(XS_GEMV_STABLE_API_VERSION == 2, "Select the V2 include directory");
struct xs_gemv_slot { int32_t value; uint32_t high[3]; };
_Static_assert(sizeof(struct xs_gemv_slot) == 16, "16-byte output slot required");

/* Caller supplies aligned, disjoint, fully initialized buffers on the qualified
 * RV64/VLEN128 platform with VS enabled. No packing or allocation is hidden. */
void example_gemv8(const int8_t packed_ax[8 * 32 + 32],
                   struct xs_gemv_slot output_slots[8]) {
    xs_gemv_8x32(packed_ax, output_slots);
}
