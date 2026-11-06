#ifndef R2_FORWARD_W2_PAIRED16_CONSUMER_H
#define R2_FORWARD_W2_PAIRED16_CONSUMER_H
#include "consumer_w2.h"

/* Optional fixed-model FR-cache consumer using the frozen paired16 K288 body,
 * including its full-domain guard and embedded FR fallback. Use the existing
 * r2_w2_init/reset and consumer.h ownership/alignment/consecutive-position
 * rules. W2 K768, model/state layout and FP order remain the original FR path.
 * Old methods 0--4 and the rejection of method 5 are unchanged.
 * Returns state->logits, or NULL for the original invalid argument domain.
 * This declaration grants no whole-application timing qualification.
 */
float *r2_w2_paired16_forward(struct r2_consumer_state *state,
                            int token, int position);

#endif
