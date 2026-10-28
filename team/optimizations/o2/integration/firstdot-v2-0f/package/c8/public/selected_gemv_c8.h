#ifndef XS_C8_SELECTED_GEMV_H
#define XS_C8_SELECTED_GEMV_H

#include "config_reuse_gemv.h"

/* Ordinary C aliases only: no runtime wrapper or CPU detection.
 * Signed INT8 A[8][32] || x[32], VLEN exactly 128, VS enabled.
 * Input and output are aligned to 16 bytes and do not overlap.
 * Output is eight 16-byte slots, not eight packed int32_t values.
 * See CONTRACT.md before use. Recompile every related translation unit
 * after changing the selection or API version. */
#define XS_C8_GEMV_API_VERSION 1
#define XS_C8_GEMV_PROFILE "divfix0f-clean02-config-reuse-8x32-v1"

#ifndef XS_C8_GEMV_FORCE_RVV
#define XS_C8_GEMV_FORCE_RVV 0
#endif
#define XS_C8_DETAIL_VALID_0_END 1
#define XS_C8_DETAIL_VALID_1_END 1
#define XS_C8_DETAIL_VALID_INNER(x) XS_C8_DETAIL_VALID_##x##_END
#define XS_C8_DETAIL_VALID(x) XS_C8_DETAIL_VALID_INNER(x)
#define XS_C8_DETAIL_STRING_INNER(x) #x
#define XS_C8_DETAIL_STRING(x) XS_C8_DETAIL_STRING_INNER(x)
typedef char xs_c8_force_rvv_must_be_literal_0_or_1[
    sizeof(XS_C8_DETAIL_STRING(XS_C8_GEMV_FORCE_RVV)) == 2 ? 1 : -1];
#if !(XS_C8_DETAIL_VALID(XS_C8_GEMV_FORCE_RVV))
#error "XS_C8_GEMV_FORCE_RVV must expand to the literal 0 or 1"
#endif
#undef XS_C8_DETAIL_VALID
#undef XS_C8_DETAIL_VALID_INNER
#undef XS_C8_DETAIL_VALID_0_END
#undef XS_C8_DETAIL_VALID_1_END
#undef XS_C8_DETAIL_STRING
#undef XS_C8_DETAIL_STRING_INNER

#define xs_c8_gemv_8x32_rvv config_reuse_gemv_8x32_reuse_rvv
#if XS_C8_GEMV_FORCE_RVV
#define xs_c8_gemv_8x32 xs_c8_gemv_8x32_rvv
#else
#define xs_c8_gemv_8x32 config_reuse_gemv_8x32_reuse_vdot
#endif

#endif
