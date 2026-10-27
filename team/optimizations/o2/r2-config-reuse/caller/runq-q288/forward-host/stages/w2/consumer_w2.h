#ifndef R2_FORWARD_W2_CONSUMER_H
#define R2_FORWARD_W2_CONSUMER_H
#include "consumer.h"

/* Optional fixed-model consumer with six prepacked K768 W2 matrices.
 * The original consumer state and method enum remain unchanged. All buffers
 * are borrowed and immutable; init/reset/forward ownership rules are the same
 * as consumer.h. This interface has distinct symbols and an extra model input.
 * w2_packed is 16-byte aligned, six consecutive [36][24][8][32] matrices.
 */
#define R2_W2_PACKED_BYTES (6u*221184u)
int r2_w2_init(const void *weights,size_t weight_bytes,
              const void *embedding,size_t embedding_bytes,
              const void *packed,size_t packed_bytes,
              const void *tail_scales,size_t tail_scale_bytes,
              const void *w2_packed,size_t w2_packed_bytes);
void r2_w2_reset(struct r2_consumer_state *state);
float *r2_w2_forward(struct r2_consumer_state *state,
                    enum r2_consumer_method method,int token,int position);
#endif
