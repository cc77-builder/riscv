#ifndef R2_FORWARD_CONSUMER_H
#define R2_FORWARD_CONSUMER_H
#include <stddef.h>
#include <stdint.h>

/* Fixed D288/H768/L6/HQ6/HKV6/V32000/S256/GS32 model adapter, version 1.
 * Model buffers are borrowed, aligned, immutable, and prepared offline.
 * Initialize once before using independent states; do not rebind concurrently.
 * Calls on the same state must use consecutive positions starting at zero.
 * States must be properly aligned, mutually disjoint and disjoint from model
 * buffers. An invalid init clears the binding; initialize successfully again.
 */
#define R2_CONSUMER_STATE_BYTES 3691424u
#define R2_CONSUMER_WEIGHT_BYTES 17101440u
#define R2_CONSUMER_EMBEDDING_BYTES 36864000u
#define R2_CONSUMER_PACKED_BYTES (172u*82944u)
#define R2_CONSUMER_TAIL_SCALE_BYTES (13u*288u*9u*4u)
enum r2_consumer_method { R2_SCALAR=0, R2_FR=1, R2_TA=2, R2_FR_CACHE=3, R2_TA_CACHE=4 };
struct r2_consumer_state {
    float x[288],xb[288],xb2[288],hb[768],hb2[768];
    int8_t xq[288]; float xs[288]; int8_t hq[768]; float hs[768];
    float q[288],k[288],v[288],att[6*256],logits[32000];
    float key[6*256*288],value[6*256*288];
};
int r2_consumer_init(const void *weights,size_t weight_bytes,
                     const void *embedding,size_t embedding_bytes,
                     const void *packed,size_t packed_bytes,
                     const void *tail_scales,size_t tail_scale_bytes);
void r2_consumer_reset(struct r2_consumer_state *state);
float *r2_consumer_forward(struct r2_consumer_state *state,
                          enum r2_consumer_method method,int token,int position);
#endif
