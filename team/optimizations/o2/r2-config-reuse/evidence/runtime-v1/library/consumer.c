#include <stdint.h>
#include "gemv.h"
typedef void (*entry_t)(const int8_t *, void *);
entry_t const config_reuse_all_entries[] = {
  config_reuse_gemv_16x64_basic_rvv,
  config_reuse_gemv_16x64_basic_vdot,
  config_reuse_gemv_16x64_reuse_rvv,
  config_reuse_gemv_16x64_reuse_vdot,
  config_reuse_gemv_4x13_basic_rvv,
  config_reuse_gemv_4x13_basic_vdot,
  config_reuse_gemv_4x13_reuse_rvv,
  config_reuse_gemv_4x13_reuse_vdot,
  config_reuse_gemv_4x8_basic_rvv,
  config_reuse_gemv_4x8_basic_vdot,
  config_reuse_gemv_4x8_reuse_rvv,
  config_reuse_gemv_4x8_reuse_vdot,
  config_reuse_gemv_8x32_basic_rvv,
  config_reuse_gemv_8x32_basic_vdot,
  config_reuse_gemv_8x32_reuse_rvv,
  config_reuse_gemv_8x32_reuse_vdot,
};
void config_reuse_link_all(const int8_t *p, void *q) {
  for (unsigned i=0; i<16; ++i) config_reuse_all_entries[i](p,q);
}
