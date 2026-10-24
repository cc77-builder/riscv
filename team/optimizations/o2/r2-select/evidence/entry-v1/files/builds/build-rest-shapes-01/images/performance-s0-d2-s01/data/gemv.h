#ifndef R4_GEMV_H
#define R4_GEMV_H
#include <stdint.h>
/* VLEN128; VS enabled; disjoint packed A||x and M zero-high96 output slots.
 * All input loads, state setup and output stores are inside each leaf.
 * Vector configuration is caller-clobbered. See ENTRY_CONTRACT.md. */
void r4_gemv_4x8_basic_vdot(const int8_t *packed_ax, void *output_slots);
void r4_gemv_4x8_basic_rvv(const int8_t *packed_ax, void *output_slots);
void r4_gemv_4x8_reuse_vdot(const int8_t *packed_ax, void *output_slots);
void r4_gemv_4x8_reuse_rvv(const int8_t *packed_ax, void *output_slots);
#endif
