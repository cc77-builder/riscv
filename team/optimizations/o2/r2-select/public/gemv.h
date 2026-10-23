#ifndef R4_PUBLIC_GEMV_H
#define R4_PUBLIC_GEMV_H
#include <stdint.h>
/* S1 leaves; packed A||x, disjoint 16-byte output slots, VLEN128/VS enabled.
 * Vector configuration is clobbered. See ENTRY_CONTRACT.md. */
void r4_gemv_4x8_basic_vdot(const int8_t *, void *);
void r4_gemv_4x8_basic_rvv(const int8_t *, void *);
void r4_gemv_4x8_reuse_vdot(const int8_t *, void *);
void r4_gemv_4x8_reuse_rvv(const int8_t *, void *);
void r4_gemv_8x32_basic_vdot(const int8_t *, void *);
void r4_gemv_8x32_basic_rvv(const int8_t *, void *);
void r4_gemv_8x32_reuse_vdot(const int8_t *, void *);
void r4_gemv_8x32_reuse_rvv(const int8_t *, void *);
void r4_gemv_16x64_basic_vdot(const int8_t *, void *);
void r4_gemv_16x64_basic_rvv(const int8_t *, void *);
void r4_gemv_16x64_reuse_vdot(const int8_t *, void *);
void r4_gemv_16x64_reuse_rvv(const int8_t *, void *);
void r4_gemv_4x13_basic_vdot(const int8_t *, void *);
void r4_gemv_4x13_basic_rvv(const int8_t *, void *);
void r4_gemv_4x13_reuse_vdot(const int8_t *, void *);
void r4_gemv_4x13_reuse_rvv(const int8_t *, void *);
#endif
