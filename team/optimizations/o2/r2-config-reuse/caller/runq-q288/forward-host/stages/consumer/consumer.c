/* Team adapter around unchanged MIT-licensed upstream/runq.c.
 * No oracle, counter, trace, snapshot, or validation callback in forward.
 */
#define TESTING
#include "upstream/runq.c"
#include "consumer.h"
#include "q288.h"

_Static_assert(sizeof(struct r2_consumer_state)==R2_CONSUMER_STATE_BYTES,"exact state inventory");
_Static_assert(sizeof(float)==4,"binary32");
extern void q288_fused_rvv4(struct q288_context *);
extern void q288_tail_vdot(struct q288_context *);
static TransformerWeights model;
static QuantizedTensor token_weights,arrays[7][6];
struct matrix { QuantizedTensor *tensor; unsigned rows,first,tail; };
static struct matrix matrices[37];
static const int8_t *packed_model;
static const float *tail_model;
static int initialized;

static void tensor(const unsigned char **cursor,QuantizedTensor *t,size_t elements) {
    t->q=(int8_t*)*cursor; *cursor+=elements;
    t->s=(float*)*cursor; *cursor+=elements/32*4;
}
int r2_consumer_init(const void *weights,size_t weight_bytes,
                     const void *embedding,size_t embedding_bytes,
                     const void *packed,size_t packed_bytes,
                     const void *tail_scales,size_t tail_scale_bytes) {
    initialized=0;
    if(!weights || !embedding || !packed || !tail_scales ||
       weight_bytes!=R2_CONSUMER_WEIGHT_BYTES || embedding_bytes!=R2_CONSUMER_EMBEDDING_BYTES ||
       packed_bytes!=R2_CONSUMER_PACKED_BYTES || tail_scale_bytes!=R2_CONSUMER_TAIL_SCALE_BYTES ||
       (uintptr_t)weights%4 || (uintptr_t)embedding%4 || (uintptr_t)packed%16 || (uintptr_t)tail_scales%4) return -1;
    const unsigned char *cursor=weights;
    model.rms_att_weight=(float*)cursor; cursor+=6*288*4;
    model.rms_ffn_weight=(float*)cursor; cursor+=6*288*4;
    model.rms_final_weight=(float*)cursor; cursor+=288*4;
    tensor(&cursor,&token_weights,32000u*288); model.q_tokens=&token_weights; model.wcls=&token_weights;
    for(unsigned kind=0;kind<7;++kind)for(unsigned layer=0;layer<6;++layer)
        tensor(&cursor,&arrays[kind][layer],kind<4?288u*288:288u*768);
    if(cursor!=(const unsigned char*)weights+weight_bytes)return -1;
    model.wq=arrays[0]; model.wk=arrays[1]; model.wv=arrays[2]; model.wo=arrays[3];
    model.w1=arrays[4]; model.w2=arrays[5]; model.w3=arrays[6];
    model.token_embedding_table=(float*)embedding;
    unsigned block=0,tail=0;
    const unsigned kinds[]={0,1,2,3,4,6};
    for(unsigned i=0;i<37;++i) {
        struct matrix *m=&matrices[i];
        m->tensor=i==36?&token_weights:&arrays[kinds[i/6]][i%6];
        m->rows=i==36?32000:(i<24?288:768);m->first=block;
        m->tail=m->rows%288?tail++:0;block+=(m->rows+287)/288;
    }
    if(block!=172 || tail!=13)return -1;
    packed_model=packed; tail_model=tail_scales; GS=32; initialized=1;return 0;
}
void r2_consumer_reset(struct r2_consumer_state *s) { if(s)memset(s,0,sizeof(*s)); }
static void bind_state(RunState *s,struct r2_consumer_state *m) {
    s->x=m->x; s->xb=m->xb; s->xb2=m->xb2; s->hb=m->hb; s->hb2=m->hb2;
    s->xq=(QuantizedTensor){m->xq,m->xs}; s->hq=(QuantizedTensor){m->hq,m->hs};
    s->q=m->q; s->k=m->k; s->v=m->v; s->att=m->att; s->logits=m->logits;
    s->key_cache=m->key; s->value_cache=m->value;
}
/* Both paths have exactly the same routing and tail handling. W2's K768
 * remains the original scalar left fold. Only the complete Q kernel differs.
 */
__attribute__((noinline)) static void route_matmul(float *out,QuantizedTensor *x,QuantizedTensor *w,
                                                  int n,int d,void (*kernel)(struct q288_context *)) {
    if(n!=288) {matmul(out,x,w,n,d);return;}
    const struct matrix *m=NULL;
    for(unsigned id=0;id<37;++id)if(w==matrices[id].tensor) {m=&matrices[id];break;}
    /* Internal generated calls use only the fixed model's known tensors. */
    if(!m) {matmul(out,x,w,n,d);return;}
    struct caller_slot slots[8] __attribute__((aligned(16)));
    float tail_output[288] __attribute__((aligned(16)));
    for(unsigned row=0,block=m->first;row<m->rows;row+=288,++block) {
        unsigned valid=m->rows-row;if(valid>288)valid=288;
        struct q288_context c={packed_model+(size_t)block*82944,x->q,
            valid<288?tail_model+(size_t)m->tail*288*9:w->s+row*9,
            x->s,valid<288?tail_output:out+row,slots,0};
        kernel(&c);
        if(valid<288)memcpy(out+row,tail_output,valid*4);
    }
}
static void route_fr(float *out,QuantizedTensor *x,QuantizedTensor *w,int n,int d) {
    route_matmul(out,x,w,n,d,q288_fused_rvv4);
}
static void route_ta(float *out,QuantizedTensor *x,QuantizedTensor *w,int n,int d) {
    route_matmul(out,x,w,n,d,q288_tail_vdot);
}
#define STAGE_QUANTIZE quantize
#define STAGE_TEST_CACHE(table,position) ((void)0)
#include "consumer.inc"

__attribute__((noinline)) float *r2_consumer_forward(struct r2_consumer_state *state,
                          enum r2_consumer_method method,int token,int position) {
    if(!initialized || !state || token<0 || token>=32000 || position<0 || position>=256)return NULL;
    Transformer t={0};t.config=(Config){288,768,6,6,6,32000,256};t.weights=model;bind_state(&t.state,state);
    switch(method) {
    case R2_SCALAR:return forward(&t,token,position);
    case R2_FR:return consumer_fr(&t,token,position);
    case R2_TA:return consumer_ta(&t,token,position);
    case R2_FR_CACHE:return consumer_fr_cache(&t,token,position);
    case R2_TA_CACHE:return consumer_ta_cache(&t,token,position);
    default:return NULL;
    }
}
