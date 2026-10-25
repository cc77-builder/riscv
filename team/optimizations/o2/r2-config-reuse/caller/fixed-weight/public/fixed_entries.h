#ifndef XS_FIXED_WEIGHT_ENTRIES_H
#define XS_FIXED_WEIGHT_ENTRIES_H
#include "fixed.h"
/* Packed leaves consume 256B A followed by 32B x, and write 8 full slots. */
void config_reuse_gemv_8x32_reuse_vdot(const int8_t *,void *);
void r4_gemv_8x32_basic_rvv(const int8_t *,void *);
void r4_gemv_8x32_reuse_rvv(const int8_t *,void *);
void config_reuse_gemv_8x32_basic_rvv(const int8_t *,void *);
void firstdot_gemv_8x32_reuse_rvv(const int8_t *,void *);
void config_reuse_gemv_8x32_reuse_rvv(const int8_t *,void *);
#endif
