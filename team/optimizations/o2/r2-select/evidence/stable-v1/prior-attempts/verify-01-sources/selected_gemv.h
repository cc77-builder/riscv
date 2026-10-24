#ifndef XS_SELECTED_GEMV_H
#define XS_SELECTED_GEMV_H

#include "gemv.h"

/* C source aliases only: no additional ELF symbols or runtime dispatcher.
 * Packed signed INT8 A||x, VLEN=128, VS enabled, disjoint aligned buffers.
 * Each output row occupies 16 bytes; vector registers/configuration clobbered.
 * Define XS_GEMV_FORCE_RVV before the first include; rebuild callers to change it.
 * See ../STABLE.md and the frozen ENTRY_CONTRACT.md for the complete ABI. */
#define XS_GEMV_STABLE_API_VERSION 1

#ifndef XS_GEMV_FORCE_RVV
#define XS_GEMV_FORCE_RVV 0
#endif
#define XS_GEMV_DETAIL_VALID_0_END 1
#define XS_GEMV_DETAIL_VALID_1_END 1
#define XS_GEMV_DETAIL_VALID_INNER(x) XS_GEMV_DETAIL_VALID_##x##_END
#define XS_GEMV_DETAIL_VALID(x) XS_GEMV_DETAIL_VALID_INNER(x)
#if !XS_GEMV_DETAIL_VALID(XS_GEMV_FORCE_RVV)
#error "XS_GEMV_FORCE_RVV must expand to the literal 0 or 1"
#endif
#undef XS_GEMV_DETAIL_VALID
#undef XS_GEMV_DETAIL_VALID_INNER
#undef XS_GEMV_DETAIL_VALID_0_END
#undef XS_GEMV_DETAIL_VALID_1_END

#define xs_gemv_4x8_rvv r4_gemv_4x8_reuse_rvv
#define xs_gemv_8x32_rvv r4_gemv_8x32_reuse_rvv
#define xs_gemv_16x64_rvv r4_gemv_16x64_reuse_rvv
#define xs_gemv_4x13_rvv r4_gemv_4x13_reuse_rvv

#if XS_GEMV_FORCE_RVV
#define xs_gemv_4x8 xs_gemv_4x8_rvv
#define xs_gemv_8x32 xs_gemv_8x32_rvv
#define xs_gemv_16x64 xs_gemv_16x64_rvv
#else
#define xs_gemv_4x8 r4_gemv_4x8_reuse_vdot
#define xs_gemv_8x32 r4_gemv_8x32_reuse_vdot
#define xs_gemv_16x64 r4_gemv_16x64_reuse_vdot
#endif
#define xs_gemv_4x13 xs_gemv_4x13_rvv

#endif
