#include "gemv.h"
void r4_header_link_test(const int8_t *a, void *b) {
  r4_gemv_4x13_basic_vdot(a, b);
  r4_gemv_4x13_basic_rvv(a, b);
  r4_gemv_4x13_reuse_vdot(a, b);
  r4_gemv_4x13_reuse_rvv(a, b);
}
