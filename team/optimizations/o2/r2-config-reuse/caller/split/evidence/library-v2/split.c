#include "split.h"

/* Pointer capture, actual leaf call, and tight INT32 extraction are all inside
 * the full-call measurement. The same wrapper serves vdot and every RVV leaf.
 */
__attribute__((noinline,noclone)) void split_full(struct split_context *c) {
    const int8_t *a = c->a, *x = c->x;
    int32_t *y = c->y;
    struct caller_slot *slots = c->slots;
    split_leaf entry = c->entry;
    entry(a, x, slots);
    for (unsigned r = 0; r < 8; ++r) y[r] = slots[r].value;
}
