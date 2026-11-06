#include "q288_ws.h"

void q288_ws_pack(struct q288_ws_pack_context *context) {
    for (unsigned tile = 0; tile < Q288_TILES; ++tile) {
        for (unsigned group = 0; group < Q288_GROUPS; ++group) {
            for (unsigned lane = 0; lane < 8; ++lane) {
                const unsigned source = (tile * 8 + lane) * Q288_GROUPS + group;
                const unsigned target = (tile * Q288_GROUPS + group) * 8 + lane;
                /* Explicit fixed-size builtin remains a byte copy under
                 * -ffreestanding/-fno-builtin and avoids float/type punning. */
                __builtin_memcpy(context->packed_scale + target,
                                 context->row_major + source, sizeof(float));
            }
        }
    }
}
