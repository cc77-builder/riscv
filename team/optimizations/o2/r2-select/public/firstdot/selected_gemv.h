/* A later V2 include must never silently keep a prior V1 selection. */
#if defined(XS_GEMV_STABLE_API_VERSION) && XS_GEMV_STABLE_API_VERSION != 2
#error "Select one GEMV API version per translation unit; V1 was already included"
#endif

/* Shared with frozen V1: including V1 after V2 cannot downgrade these aliases. */
#ifndef XS_SELECTED_GEMV_H
#define XS_SELECTED_GEMV_H

#include "firstdot_gemv.h"

/* Compile-time C aliases; no new ELF symbols or runtime dispatch.
 * INT8 row-major A||x, VLEN=128, VS enabled, aligned disjoint buffers.
 * Each output row occupies 16 bytes. See FIRSTDOT_STABLE.md for the full ABI.
 * Set XS_GEMV_FORCE_RVV before the first include and recompile to change it. */
#define XS_GEMV_STABLE_API_VERSION 2

#ifndef XS_GEMV_FORCE_RVV
#define XS_GEMV_FORCE_RVV 0
#endif
#define XS_GEMV_DETAIL_VALID_0_END 1
#define XS_GEMV_DETAIL_VALID_1_END 1
#define XS_GEMV_DETAIL_VALID_INNER(x) XS_GEMV_DETAIL_VALID_##x##_END
#define XS_GEMV_DETAIL_VALID(x) XS_GEMV_DETAIL_VALID_INNER(x)
#define XS_GEMV_DETAIL_STRING_INNER(x) #x
#define XS_GEMV_DETAIL_STRING(x) XS_GEMV_DETAIL_STRING_INNER(x)
typedef char xs_gemv_force_rvv_must_be_literal_0_or_1[
    sizeof(XS_GEMV_DETAIL_STRING(XS_GEMV_FORCE_RVV)) == 2 ? 1 : -1];
#if !(XS_GEMV_DETAIL_VALID(XS_GEMV_FORCE_RVV))
#error "XS_GEMV_FORCE_RVV must expand to the literal 0 or 1"
#endif
#undef XS_GEMV_DETAIL_VALID
#undef XS_GEMV_DETAIL_VALID_INNER
#undef XS_GEMV_DETAIL_VALID_0_END
#undef XS_GEMV_DETAIL_VALID_1_END
#undef XS_GEMV_DETAIL_STRING
#undef XS_GEMV_DETAIL_STRING_INNER

#define xs_gemv_4x8_rvv firstdot_gemv_4x8_reuse_rvv
#define xs_gemv_8x32_rvv firstdot_gemv_8x32_reuse_rvv
#define xs_gemv_16x64_rvv firstdot_gemv_16x64_reuse_rvv
#define xs_gemv_4x13_rvv firstdot_gemv_4x13_reuse_rvv

#if XS_GEMV_FORCE_RVV
#define xs_gemv_4x8 xs_gemv_4x8_rvv
#define xs_gemv_8x32 xs_gemv_8x32_rvv
#define xs_gemv_16x64 xs_gemv_16x64_rvv
#else
#define xs_gemv_4x8 firstdot_gemv_4x8_reuse_vdot
#define xs_gemv_8x32 firstdot_gemv_8x32_reuse_vdot
#define xs_gemv_16x64 firstdot_gemv_16x64_reuse_vdot
#endif
#define xs_gemv_4x13 xs_gemv_4x13_rvv

#endif
