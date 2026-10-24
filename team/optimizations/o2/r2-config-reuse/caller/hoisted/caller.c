#include "caller.h"

/* The context record and all writable buffers are disjoint. Capture views
 * inside the measured call; both vdot and RVV use this exact C implementation.
 */
static inline __attribute__((always_inline)) void pack(
    const int8_t *a, const int8_t *x, struct caller_workspace *workspace) {
    int8_t *out = workspace->packed;
    for (unsigned r = 0; r < 8; ++r)
        for (unsigned k = 0; k < 32; ++k)
            out[r * 32 + k] = a[r * 32 + k];
    for (unsigned k = 0; k < 32; ++k) out[256 + k] = x[k];
}
static inline __attribute__((always_inline)) void extract(
    const struct caller_workspace *workspace, int32_t *y) {
    for (unsigned r = 0; r < 8; ++r) y[r] = workspace->slots[r].value;
}
__attribute__((noinline,noclone)) void caller_full(struct caller_context *c) {
    const int8_t *a = c->a, *x = c->x;
    struct caller_workspace *workspace = c->workspace;
    int32_t *y = c->y;
    caller_leaf entry = c->entry;
    pack(a, x, workspace);
    entry(workspace->packed, workspace->slots);
    extract(workspace, y);
}
__attribute__((noinline,noclone)) void caller_pack(struct caller_context *c) {
    const int8_t *a = c->a, *x = c->x;
    struct caller_workspace *workspace = c->workspace;
    pack(a, x, workspace);
}
__attribute__((noinline,noclone)) void caller_core(struct caller_context *c) {
    struct caller_workspace *workspace = c->workspace;
    caller_leaf entry = c->entry;
    entry(workspace->packed, workspace->slots);
}
__attribute__((noinline,noclone)) void caller_extract(struct caller_context *c) {
    const struct caller_workspace *workspace = c->workspace;
    int32_t *y = c->y;
    extract(workspace, y);
}
