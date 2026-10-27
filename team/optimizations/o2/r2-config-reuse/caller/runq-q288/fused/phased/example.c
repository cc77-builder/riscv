#include "phased.h"
#ifdef Q288_INCLUDE_TAIL
#include "tail/tail.h"
#endif

/* A complete ordinary-C call boundary, with caller-owned buffers/context.
 * The caller fills inputs/scales, enables FS/VS, sets FRM=RNE, and gives
 * disjoint arrays. This symbol demonstrates required slot alignment. */
_Alignas(16) struct caller_slot q288_api_slots[8];

void q288_api_pack(const int8_t *weight, int8_t *packed) {
    struct q288_pack_context context = {weight, packed};
    q288_pack(&context);
}
void q288_api_phased(struct q288_context *context) { q288_phased_vdot(context); }
void q288_api_fused(struct q288_context *context) { q288_fused_vdot(context); }
void q288_api_rvv4(struct q288_context *context) { q288_fused_rvv4(context); }
#ifdef Q288_INCLUDE_TAIL
void q288_api_tail(struct q288_context *context) { q288_tail_vdot(context); }
#endif
