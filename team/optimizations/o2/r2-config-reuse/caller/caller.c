#include "caller.h"

static inline __attribute__((always_inline)) void pack(struct caller_context *c) {
    for (unsigned r = 0; r < 8; ++r)
        for (unsigned k = 0; k < 32; ++k)
            c->workspace->packed[r * 32 + k] = c->a[r * 32 + k];
    for (unsigned k = 0; k < 32; ++k)
        c->workspace->packed[256 + k] = c->x[k];
}
static inline __attribute__((always_inline)) void extract(struct caller_context *c) {
    for (unsigned r = 0; r < 8; ++r) c->y[r] = c->workspace->slots[r].value;
}
__attribute__((noinline,noclone)) void caller_full(struct caller_context *c) {
    pack(c);
    c->entry(c->workspace->packed, c->workspace->slots);
    extract(c);
}
__attribute__((noinline,noclone)) void caller_pack(struct caller_context *c) { pack(c); }
__attribute__((noinline,noclone)) void caller_core(struct caller_context *c) {
    c->entry(c->workspace->packed, c->workspace->slots);
}
__attribute__((noinline,noclone)) void caller_extract(struct caller_context *c) { extract(c); }
