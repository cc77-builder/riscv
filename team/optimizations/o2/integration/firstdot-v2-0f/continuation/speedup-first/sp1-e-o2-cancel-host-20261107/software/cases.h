#ifndef O2C_CASES_H
#define O2C_CASES_H
#include "contract.h"
extern void o2c_guard(const uint8_t *, struct o2c_result *, const struct o2c_trial *);
extern void o2c_s0_p0(const uint8_t *, struct o2c_result *, const struct o2c_trial *);
extern void o2c_s1_p0(const uint8_t *, struct o2c_result *, const struct o2c_trial *);
extern void o2c_s0_p1(const uint8_t *, struct o2c_result *, const struct o2c_trial *);
extern void o2c_s1_p1(const uint8_t *, struct o2c_result *, const struct o2c_trial *);
extern void o2c_s0_p2(const uint8_t *, struct o2c_result *, const struct o2c_trial *);
extern void o2c_s1_p2(const uint8_t *, struct o2c_result *, const struct o2c_trial *);
extern void o2c_s0_p4(const uint8_t *, struct o2c_result *, const struct o2c_trial *);
extern void o2c_s1_p4(const uint8_t *, struct o2c_result *, const struct o2c_trial *);
struct o2c_case { o2c_kernel kernel; const char *stage; unsigned phase, probe; struct o2c_trial trial; };
#define O2C_CALL_COUNT 41
static const struct o2c_case o2c_cases[O2C_CALL_COUNT] = {
  {o2c_guard, "prelude", 0, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 0}},
  {o2c_s0_p0, "S0", 0, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 1}},
  {o2c_s1_p0, "S1", 0, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 2}},
  {o2c_s1_p0, "S1", 0, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 3}},
  {o2c_s1_p0, "S1", 0, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 4}},
  {o2c_s1_p0, "S1", 0, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 5}},
  {o2c_s1_p0, "S1", 0, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 6}},
  {o2c_s1_p0, "S1", 0, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 7}},
  {o2c_s1_p0, "S1", 0, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 8}},
  {o2c_s1_p0, "S1", 0, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 9}},
  {o2c_s1_p0, "S1", 0, 1, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababeULL, 10}},
  {o2c_s0_p1, "S0", 1, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 11}},
  {o2c_s1_p1, "S1", 1, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 12}},
  {o2c_s1_p1, "S1", 1, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 13}},
  {o2c_s1_p1, "S1", 1, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 14}},
  {o2c_s1_p1, "S1", 1, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 15}},
  {o2c_s1_p1, "S1", 1, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 16}},
  {o2c_s1_p1, "S1", 1, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 17}},
  {o2c_s1_p1, "S1", 1, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 18}},
  {o2c_s1_p1, "S1", 1, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 19}},
  {o2c_s1_p1, "S1", 1, 1, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababeULL, 20}},
  {o2c_s0_p2, "S0", 2, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 21}},
  {o2c_s1_p2, "S1", 2, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 22}},
  {o2c_s1_p2, "S1", 2, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 23}},
  {o2c_s1_p2, "S1", 2, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 24}},
  {o2c_s1_p2, "S1", 2, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 25}},
  {o2c_s1_p2, "S1", 2, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 26}},
  {o2c_s1_p2, "S1", 2, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 27}},
  {o2c_s1_p2, "S1", 2, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 28}},
  {o2c_s1_p2, "S1", 2, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 29}},
  {o2c_s1_p2, "S1", 2, 1, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababeULL, 30}},
  {o2c_s0_p4, "S0", 4, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 31}},
  {o2c_s1_p4, "S1", 4, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 32}},
  {o2c_s1_p4, "S1", 4, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 33}},
  {o2c_s1_p4, "S1", 4, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 34}},
  {o2c_s1_p4, "S1", 4, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 35}},
  {o2c_s1_p4, "S1", 4, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 36}},
  {o2c_s1_p4, "S1", 4, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 37}},
  {o2c_s1_p4, "S1", 4, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 38}},
  {o2c_s1_p4, "S1", 4, 0, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababdULL, 39}},
  {o2c_s1_p4, "S1", 4, 1, {0x8000000000003039ULL, 3, 0x2aaaaaaaaaaababeULL, 40}},
};
#endif
