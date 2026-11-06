#ifndef R2_FORWARD_W2_GS32_CONSUMER_H
#define R2_FORWARD_W2_GS32_CONSUMER_H
#include "consumer_w2.h"

/* Optional fixed-model FR-cache consumer with the qualified GS32 K288 body.
 * Use r2_w2_init/reset and the ownership, alignment and consecutive-position
 * rules from consumer.h. K768 W2 keeps the original FR path. Model layout,
 * state layout, floating-point order and the old method enum are unchanged.
 * The new name is deliberate: method 5 remains invalid in r2_w2_forward.
 * Returns state->logits, or NULL for the same invalid binding/argument domain
 * as r2_w2_forward. This declaration grants no application timing result.
 */
float *r2_w2_gs32_forward(struct r2_consumer_state *state,
                          int token, int position);

#endif
