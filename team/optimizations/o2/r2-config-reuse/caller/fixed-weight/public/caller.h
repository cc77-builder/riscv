#ifndef CONFIG_REUSE_CALLER_H
#define CONFIG_REUSE_CALLER_H
#include <stdint.h>
#include <stddef.h>

typedef void (*caller_leaf)(const int8_t *, void *);
struct caller_slot { int32_t value; uint32_t high[3]; };
struct caller_workspace {
    uint64_t head[2];
    int8_t packed[288];
    uint64_t middle[2];
    struct caller_slot slots[8];
    uint64_t tail[2];
} __attribute__((aligned(16)));
struct caller_context {
    const int8_t *a;
    const int8_t *x;
    int32_t *y;
    struct caller_workspace *workspace;
    caller_leaf entry;
};
struct caller_measurement { uint64_t cycles, instructions; };
_Static_assert(sizeof(struct caller_slot) == 16, "full vector output slot");
_Static_assert(offsetof(struct caller_workspace, packed) == 16, "packed offset");
_Static_assert(offsetof(struct caller_workspace, slots) == 320, "slots offset");
_Static_assert(sizeof(struct caller_context) == 40, "RV64 context ABI");

/* A and x are separate, row-major signed INT8 arrays. y holds eight INT32s.
 * All buffers are disjoint; workspace must have 16-byte alignment. VS is on.
 * entry is one of the already qualified 8x32 reuse leaves. */
void caller_full(struct caller_context *);
void caller_pack(struct caller_context *);
void caller_core(struct caller_context *);
void caller_extract(struct caller_context *);
void gemv8(const int8_t a[8][32], const int8_t x[32], int32_t y[8]);
#endif
