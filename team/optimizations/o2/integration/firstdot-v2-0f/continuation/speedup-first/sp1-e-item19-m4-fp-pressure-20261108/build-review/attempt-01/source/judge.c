#include "contract.h"
const uint64_t o2c_caller_csrs[5] = {8, 0, 0, 7, 0x60};
unsigned o2c_judge(const struct o2c_result *r, const uint8_t a[16],
                   const uint8_t b[16], uint64_t fp_bits, uint64_t flags) {
  unsigned error = 0;
  for (unsigned i = 0; i < 16; ++i) {
    if (r->a[i] != a[i]) error |= 1;
    if (r->b[i] != b[i]) error |= 2;
  }
  for (unsigned i = 0; i < 5; ++i) {
    if (r->before[i] != o2c_caller_csrs[i]) error |= 4;
    if (r->after[i] != o2c_caller_csrs[i]) error |= 8;
  }
  if (r->fp_bits != fp_bits) error |= 16;
  if (r->flags != flags) error |= 32;
  return error;
}
