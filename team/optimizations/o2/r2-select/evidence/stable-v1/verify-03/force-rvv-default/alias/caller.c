#include "selected_gemv.h"
void call_4x8_default(const int8_t *a, void *b) { xs_gemv_4x8(a, b); }
void call_4x8_rvv(const int8_t *a, void *b) { xs_gemv_4x8_rvv(a, b); }
void call_8x32_default(const int8_t *a, void *b) { xs_gemv_8x32(a, b); }
void call_8x32_rvv(const int8_t *a, void *b) { xs_gemv_8x32_rvv(a, b); }
void call_16x64_default(const int8_t *a, void *b) { xs_gemv_16x64(a, b); }
void call_16x64_rvv(const int8_t *a, void *b) { xs_gemv_16x64_rvv(a, b); }
void call_4x13_default(const int8_t *a, void *b) { xs_gemv_4x13(a, b); }
void call_4x13_rvv(const int8_t *a, void *b) { xs_gemv_4x13_rvv(a, b); }
