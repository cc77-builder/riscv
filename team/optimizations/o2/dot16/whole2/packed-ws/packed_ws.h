#ifndef XS_DOT16_NP_PACKED_WS_H
#define XS_DOT16_NP_PACKED_WS_H
#include <stddef.h>
#include <stdint.h>
#include <limits.h>
#include <float.h>

/* Separate layout and entry types: never pass a row-major q288/w2 context here.
 * RV64/lp64d, VLEN128, FS/VS enabled, FRM=RNE. Fixed M=288, GS=32.
 * All spans/context are disjoint. packed weights retain tile/group/row/byte
 * order. Input scales and y are FP32 and 4-byte aligned; slots are 16-byte
 * aligned. The new scale objects are 64-byte aligned, with no padding between
 * words or groups. A group is eight consecutive 32-bit object representations.
 * prepare must finish before a kernel call and must be repeated after Ws changes.
 * Kernels do not prepare, allocate, or quantize; each overwrites 288 outputs.
 * Each row keeps cast(dot), multiply Ws, multiply Xs, left-fold add in group
 * order. Compile callers with -ffp-contract=off, without fast math.
 * N and P clobber vector state and return vl=8,vtype=0,vstart=0,vcsr=7.
 * Slots preserve the parent's last tile/group low32 dot and zero high96.
 */
struct q288_packed_ws_scales { uint32_t bits[288*9]; } __attribute__((aligned(64)));
struct q768_packed_ws_scales { uint32_t bits[288*24]; } __attribute__((aligned(64)));
struct packed_ws_slot { uint32_t word[4]; } __attribute__((aligned(16)));

struct q288_packed_ws_context {
    const int8_t *packed;
    const int8_t *x;
    const struct q288_packed_ws_scales *weight_scale;
    const float *input_scale;
    float *y;
    struct packed_ws_slot *slots;
    uintptr_t reserved;
};
struct q768_packed_ws_context {
    const int8_t *packed;
    const int8_t *x;
    const struct q768_packed_ws_scales *weight_scale;
    const float *input_scale;
    float *y;
    struct packed_ws_slot *slots;
    uintptr_t reserved;
};

_Static_assert(CHAR_BIT==8 && sizeof(float)==4 && sizeof(uint32_t)==4, "32-bit scale objects");
_Static_assert(FLT_RADIX==2 && FLT_MANT_DIG==24 && FLT_MAX_EXP==128, "binary32 ABI");
_Static_assert(sizeof(void*)==8 && sizeof(uintptr_t)==8, "RV64-sized pointers");
_Static_assert(sizeof(struct q288_packed_ws_scales)==10368, "K288 complete scale span");
_Static_assert(sizeof(struct q768_packed_ws_scales)==27648, "K768 complete scale span");
_Static_assert(_Alignof(struct q288_packed_ws_scales)==64, "K288 alignment");
_Static_assert(_Alignof(struct q768_packed_ws_scales)==64, "K768 alignment");
_Static_assert(sizeof(struct packed_ws_slot)==16, "full register slot");
#define PACKED_WS_ASSERT_CONTEXT(type) \
    _Static_assert(sizeof(struct type)==56, "context extent"); \
    _Static_assert(offsetof(struct type,packed)==0, "packed offset"); \
    _Static_assert(offsetof(struct type,x)==8, "x offset"); \
    _Static_assert(offsetof(struct type,weight_scale)==16, "Ws offset"); \
    _Static_assert(offsetof(struct type,input_scale)==24, "Xs offset"); \
    _Static_assert(offsetof(struct type,y)==32, "y offset"); \
    _Static_assert(offsetof(struct type,slots)==40, "slots offset"); \
    _Static_assert(offsetof(struct type,reserved)==48, "reserved offset")
PACKED_WS_ASSERT_CONTEXT(q288_packed_ws_context);
PACKED_WS_ASSERT_CONTEXT(q768_packed_ws_context);
#undef PACKED_WS_ASSERT_CONTEXT

void q288_prepare_packed_ws(struct q288_packed_ws_scales *restrict, const float *restrict);
void q768_prepare_packed_ws(struct q768_packed_ws_scales *restrict, const float *restrict);
void q288_dot16_whole8_narrow_packed_ws(const struct q288_packed_ws_context *);
void q288_paired16_rvv_packed_ws(const struct q288_packed_ws_context *);
void q768_dot16_whole8_narrow_packed_ws(const struct q768_packed_ws_context *);
void q768_paired16_rvv_packed_ws(const struct q768_packed_ws_context *);
#endif
