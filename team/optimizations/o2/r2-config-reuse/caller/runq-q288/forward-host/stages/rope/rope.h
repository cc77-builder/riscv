#ifndef TEAM_ROPE_STAGE_H
#define TEAM_ROPE_STAGE_H
#include <stdint.h>
#define ROPE_D 288
#define ROPE_LAYERS 6
#define ROPE_CASES 6
#define ROPE_SELECTED 2
#define ROPE_BYTES (ROPE_LAYERS*2*ROPE_D*4)
struct rope_layer { float q[ROPE_D],k[ROPE_D]; };
struct rope_case { struct rope_layer layer[ROPE_LAYERS]; };
void rope_original(struct rope_case *,int);
void rope_cached(struct rope_case *,int);
static inline uint64_t rope_digest(const void *data,unsigned bytes) {
    const unsigned char *p=data;uint64_t value=UINT64_C(14695981039346656037);
    for(unsigned i=0;i<bytes;++i)value=(value^p[i])*UINT64_C(1099511628211);
    return value;
}
#endif
