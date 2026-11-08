#ifndef O2C_CONTRACT_H
#define O2C_CONTRACT_H
#include <stdint.h>
#include <stddef.h>
struct o2c_result {
  uint8_t a[16], b[16];
  uint64_t before[5], after[5]; /* vl,vtype,vstart,vcsr,fcsr */
  uint64_t fp_bits, flags;
};
struct o2c_trial { uint64_t numerator, divisor, expected_quotient, flags; };
typedef void (*o2c_kernel)(const uint8_t *, struct o2c_result *, const struct o2c_trial *);
_Static_assert(sizeof(struct o2c_result) == 128, "result size");
_Static_assert(offsetof(struct o2c_result, before) == 32, "before offset");
_Static_assert(offsetof(struct o2c_result, after) == 72, "after offset");
_Static_assert(offsetof(struct o2c_result, fp_bits) == 112, "fp offset");
_Static_assert(offsetof(struct o2c_result, flags) == 120, "flags offset");
extern const uint64_t o2c_caller_csrs[5];
extern const uint8_t o2c_input[48], o2c_dot[16], o2c_sentinel[16];
unsigned o2c_judge(const struct o2c_result *r, const uint8_t a[16],
                   const uint8_t b[16], uint64_t fp_bits, uint64_t flags);
#endif
