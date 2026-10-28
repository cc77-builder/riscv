/* Compile/link example only; platform startup and VS enable are external.
 * This file is not a performance fixture and has no target-run qualification. */
#include <stdint.h>
#include "selected_gemv_c8.h"

struct c8_output_slot {
  int32_t value;
  uint32_t upper_zero[3];
};

static _Alignas(16) int8_t packed_ax[8 * 32 + 32];
static _Alignas(16) struct c8_output_slot output_slots[8];
_Static_assert(sizeof(packed_ax) == 288, "A then x require 288 bytes");
_Static_assert(sizeof(struct c8_output_slot) == 16, "one output slot is 128 bits");
_Static_assert(sizeof(output_slots) == 128, "eight complete output slots required");
_Static_assert(XS_C8_GEMV_API_VERSION == 1, "select the C8 v1 contract");

/* Populate packed_ax with signed INT8 A in row-major order followed by x.
 * Input/output storage is disjoint; both calls overwrite the same output slots.
 * The caller must initialize the platform/VS before executing either function. */
void c8_example(void) {
  xs_c8_gemv_8x32(packed_ax, output_slots);
}

void c8_example_rvv(void) {
  xs_c8_gemv_8x32_rvv(packed_ax, output_slots);
}
