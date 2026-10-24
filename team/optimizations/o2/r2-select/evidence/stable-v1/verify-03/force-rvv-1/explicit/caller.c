#include "gemv.h"
void call_4x8_default(const int8_t *a, void *b) { r4_gemv_4x8_reuse_rvv(a, b); }
void call_4x8_rvv(const int8_t *a, void *b) { r4_gemv_4x8_reuse_rvv(a, b); }
void call_8x32_default(const int8_t *a, void *b) { r4_gemv_8x32_reuse_rvv(a, b); }
void call_8x32_rvv(const int8_t *a, void *b) { r4_gemv_8x32_reuse_rvv(a, b); }
void call_16x64_default(const int8_t *a, void *b) { r4_gemv_16x64_reuse_rvv(a, b); }
void call_16x64_rvv(const int8_t *a, void *b) { r4_gemv_16x64_reuse_rvv(a, b); }
void call_4x13_default(const int8_t *a, void *b) { r4_gemv_4x13_reuse_rvv(a, b); }
void call_4x13_rvv(const int8_t *a, void *b) { r4_gemv_4x13_reuse_rvv(a, b); }
