#ifndef TEAM_ACTIVE_QKV_BOUNDARY_H
#define TEAM_ACTIVE_QKV_BOUNDARY_H
#include "q288.h"
typedef void (*qkv_kernel)(struct q288_context *);
struct qkv_context {
    const float *fp;
    int8_t *x;
    float *xs;
    struct q288_context *projection[3];
    qkv_kernel kernel;
};
_Static_assert(sizeof(struct qkv_context)==56,"RV64 QKV consumer ABI");
void qkv_quantize(const float *,int8_t *,float *);
void qkv_boundary(struct qkv_context *);
void q288_tail_vdot(struct q288_context *);
void q288_fused_rvv4(struct q288_context *);
#endif
