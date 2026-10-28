#ifndef CONFIG_REUSE_PUBLIC_GEMV_H
#define CONFIG_REUSE_PUBLIC_GEMV_H
#include <stdint.h>
/* Config-reuse leaves; packed A||x, disjoint 16-byte output slots, VLEN128/VS enabled.
 * Vector configuration is clobbered. See ../C_CONTRACT.md. */
void config_reuse_gemv_4x8_basic_vdot(const int8_t *, void *);
void config_reuse_gemv_4x8_basic_rvv(const int8_t *, void *);
void config_reuse_gemv_4x8_reuse_vdot(const int8_t *, void *);
void config_reuse_gemv_4x8_reuse_rvv(const int8_t *, void *);
void config_reuse_gemv_8x32_basic_vdot(const int8_t *, void *);
void config_reuse_gemv_8x32_basic_rvv(const int8_t *, void *);
void config_reuse_gemv_8x32_reuse_vdot(const int8_t *, void *);
void config_reuse_gemv_8x32_reuse_rvv(const int8_t *, void *);
void config_reuse_gemv_16x64_basic_vdot(const int8_t *, void *);
void config_reuse_gemv_16x64_basic_rvv(const int8_t *, void *);
void config_reuse_gemv_16x64_reuse_vdot(const int8_t *, void *);
void config_reuse_gemv_16x64_reuse_rvv(const int8_t *, void *);
void config_reuse_gemv_4x13_basic_vdot(const int8_t *, void *);
void config_reuse_gemv_4x13_basic_rvv(const int8_t *, void *);
void config_reuse_gemv_4x13_reuse_vdot(const int8_t *, void *);
void config_reuse_gemv_4x13_reuse_rvv(const int8_t *, void *);
#endif
