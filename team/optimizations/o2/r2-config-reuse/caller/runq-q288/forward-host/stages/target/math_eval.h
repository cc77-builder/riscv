#ifndef TEAM_FORWARD_MATH_EVAL_H
#define TEAM_FORWARD_MATH_EVAL_H
#include <stdint.h>
enum math_kind { M_POWF, M_SINF, M_COSF, M_SINCOSF, M_EXPF, M_SQRTF,
                 M_ROUNDF, M_ROUND, M_FABSF, M_FABS, M_KIND_COUNT };
struct math_input { uint32_t kind, nan_mask, required_fflags, allowed_fflags; uint64_t a, b; };
struct math_expected { uint64_t first, second; int32_t error; uint32_t host_exceptions; };
void math_evaluate(const struct math_input *, uint64_t output[2]);
#define MATH_ERRNO_SENTINEL 12345
#endif
