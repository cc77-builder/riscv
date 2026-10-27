/* Team-owned explicit inventory of the original RunState allocations. */
#include <stdint.h>
#include <stddef.h>
#define FULL_STATE_BYTES 3691424u
struct full_span { unsigned char *data; size_t bytes; };
static unsigned full_spans(RunState *s,struct full_span *out) {
    struct full_span spans[]={
        {(unsigned char*)s->x,D*4},{(unsigned char*)s->xb,D*4},{(unsigned char*)s->xb2,D*4},
        {(unsigned char*)s->hb,H*4},{(unsigned char*)s->hb2,H*4},
        {(unsigned char*)s->xq.q,D},{(unsigned char*)s->xq.s,D*4},
        {(unsigned char*)s->hq.q,H},{(unsigned char*)s->hq.s,H*4},
        {(unsigned char*)s->q,D*4},{(unsigned char*)s->k,D*4},{(unsigned char*)s->v,D*4},
        {(unsigned char*)s->att,6*S*4},{(unsigned char*)s->logits,V*4},
        {(unsigned char*)s->key_cache,L*S*D*4},{(unsigned char*)s->value_cache,L*S*D*4}
    };
    for(unsigned i=0;i<16;++i)out[i]=spans[i];
    return 16;
}
static size_t full_save_state(RunState *s,unsigned char *output) {
    struct full_span spans[16];full_spans(s,spans);size_t used=0;
    for(unsigned i=0;i<16;++i) {memcpy(output+used,spans[i].data,spans[i].bytes);used+=spans[i].bytes;}
    return used;
}

struct full_storage {
    float x[D],xb[D],xb2[D],hb[H],hb2[H];
    int8_t xq[D];float xs[D];int8_t hq[H];float hs[H];
    float q[D],k[D],v[D],att[6*S],logits[V],key[L*S*D],value[L*S*D];
};
static void full_bind_state(RunState *s,struct full_storage *m) {
    s->x=m->x;s->xb=m->xb;s->xb2=m->xb2;s->hb=m->hb;s->hb2=m->hb2;
    s->xq=(QuantizedTensor){m->xq,m->xs};s->hq=(QuantizedTensor){m->hq,m->hs};
    s->q=m->q;s->k=m->k;s->v=m->v;s->att=m->att;s->logits=m->logits;
    s->key_cache=m->key;s->value_cache=m->value;
}
