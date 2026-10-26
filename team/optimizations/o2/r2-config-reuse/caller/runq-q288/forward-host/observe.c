/* Team-owned read-only observer of the unmodified upstream forward code. */
#define TESTING
#include "upstream/runq.c"
#include "q288.h"
#include <fenv.h>
#include <stdalign.h>

#define NI __attribute__((no_instrument_function))
#define D 288
#define H 768
#define L 6
#define V 32000
#define S 256

struct prepared_q {
    QuantizedTensor *weight;
    int8_t *packed;
};
static struct prepared_q prepared[24];
static Transformer *observed;
static const char *destination;
static unsigned active, pass_number, position_number;
static unsigned matmuls, quantizes, rmsnorms, softmaxes, q_calls, groups, input_elements;
static unsigned active_q;
static float *active_output;
static unsigned char x_before[D + 9*sizeof(float)];
static alignas(16) float candidate_output[D];
static alignas(16) struct caller_slot candidate_slots[8];
static uint32_t random_state=UINT32_C(0x53485041);

static NI void require(int condition,const char *message) {
    if(!condition) { fprintf(stderr,"FORWARD_OBSERVER_FAIL %s pass=%u pos=%u matmuls=%u quantizes=%u\n",
                            message,pass_number,position_number,matmuls,quantizes);exit(2); }
}

static NI void write_file(const char *name,const void *data,size_t bytes) {
    char path[4096];int n=snprintf(path,sizeof(path),"%s/%s",destination,name);
    require(n>0 && (size_t)n<sizeof(path),"bounded output path");
    FILE *file=fopen(path,"wb");require(file!=NULL,"open output");
    require(fwrite(data,1,bytes,file)==bytes,"complete output write");require(fclose(file)==0,"close output");
}

static NI uint32_t random_word(void) {
    uint32_t x=random_state;x^=x<<13;x^=x>>17;x^=x<<5;random_state=x;return x;
}

static NI void fill_tensor(unsigned char **cursor,size_t size,float scale_unit) {
    int8_t *q=(int8_t *)*cursor;
    for(size_t i=0;i<size;++i) q[i]=(int8_t)((int)(random_word()%17)-8);
    *cursor+=size;float *scales=(float *)*cursor;
    for(size_t i=0;i<size/32;++i) scales[i]=(float)(1+random_word()%4)*scale_unit;
    *cursor+=size/32*sizeof(float);
}

static NI unsigned char *make_weights(Transformer *transformer,size_t *bytes) {
    size_t norm_count=2*L*D+D,products=(size_t)V*D+4*L*D*D+3*L*D*H;
    *bytes=norm_count*sizeof(float)+products+products/32*sizeof(float);
    unsigned char *data=malloc(*bytes);require(data!=NULL,"weight allocation");
    float *norms=(float *)data;
    for(size_t i=0;i<norm_count;++i)norms[i]=1.0f+(float)(i%5)*0x1p-7f;
    unsigned char *cursor=data+norm_count*sizeof(float);
    fill_tensor(&cursor,(size_t)V*D,0x1p-5f);
    for(unsigned kind=0;kind<4;++kind)
        for(unsigned layer=0;layer<L;++layer)fill_tensor(&cursor,D*D,0x1p-10f);
    for(unsigned kind=0;kind<3;++kind)
        for(unsigned layer=0;layer<L;++layer)fill_tensor(&cursor,D*H,0x1p-10f);
    require(cursor==data+*bytes,"exact upstream serialized weight layout");
    GS=32;memory_map_weights(&transformer->weights,&transformer->config,data,1);
    require(transformer->weights.wcls==transformer->weights.q_tokens,"shared embedding/classifier");
    return data;
}

static NI void integer_leaf(const int8_t *weight,const int8_t *input,struct caller_slot *slots) {
    for(unsigned row=0;row<8;++row) {
        int32_t sum=0;for(unsigned k=0;k<32;++k)sum+=(int32_t)weight[32*row+k]*input[k];
        slots[row].value=sum;for(unsigned i=0;i<3;++i)slots[row].high[i]=0;
    }
}

static NI void prepare_weights(Transformer *transformer) {
    TransformerWeights *w=&transformer->weights;
    for(unsigned layer=0;layer<L;++layer) {
        QuantizedTensor *rows[4]={w->wq+layer,w->wk+layer,w->wv+layer,w->wo+layer};
        for(unsigned kind=0;kind<4;++kind) {
            unsigned id=4*layer+kind;prepared[id].weight=rows[kind];
            prepared[id].packed=malloc(D*D);require(prepared[id].packed!=NULL,"persistent packed allocation");
            struct q288_pack_context pack={rows[kind]->q,prepared[id].packed};q288_pack(&pack);
            for(unsigned t=0;t<36;++t)for(unsigned g=0;g<9;++g)for(unsigned r=0;r<8;++r)for(unsigned k=0;k<32;++k)
                require(prepared[id].packed[((t*9+g)*8+r)*32+k]==rows[kind]->q[(8*t+r)*D+32*g+k],"complete packed identity");
            char name[80];snprintf(name,sizeof(name),"weight-%02u.bin",id);write_file(name,rows[kind]->q,D*D);
            snprintf(name,sizeof(name),"scale-%02u.bin",id);write_file(name,rows[kind]->s,D*9*sizeof(float));
            snprintf(name,sizeof(name),"packed-%02u.bin",id);write_file(name,prepared[id].packed,D*D);
        }
    }
}

void NI __cyg_profile_func_enter(void *function,void *caller) {
    (void)caller;if(!active)return;
    if(function==(void *)matmul) {
        unsigned call=matmuls++;active_q=24;active_output=NULL;
        if(call<42 && call%7<4) {
            unsigned kind=call%7,layer=call/7;active_q=4*layer+kind;
            float *outputs[4]={observed->state.q,observed->state.k,observed->state.v,observed->state.xb2};
            active_output=outputs[kind];
            memcpy(x_before,observed->state.xq.q,D);memcpy(x_before+D,observed->state.xq.s,9*sizeof(float));
        }
    } else if(function==(void *)quantize) {
        unsigned call=quantizes++;int size=(call<24 && call%4==3)?H:D;
        float *input=call==24?observed->state.x:(call%4==3?observed->state.hb:observed->state.xb);
        require(call<25,"bounded quantize sequence");
        for(int start=0;start<size;start+=32) {
            float maximum=0.0f;
            for(int i=0;i<32;++i) { float value=input[start+i];require(isfinite(value),"finite pre-quantize value");
                float magnitude=fabsf(value);if(magnitude>maximum)maximum=magnitude; }
            require(maximum>0.0f,"nonzero quantizer group; upstream zero-scale behavior not changed");
            volatile float scale=maximum/127.0f;
            require(isfinite(scale) && scale>0.0f,"positive representable quantizer scale");
            for(int i=0;i<32;++i) {
                volatile float scaled=input[start+i]/scale;
                double rounded=round((double)scaled);
                require(isfinite(scaled) && rounded>=-128.0 && rounded<=127.0,"defined upstream int8 conversion domain");
            }
            ++groups;
        }
        input_elements+=(unsigned)size;
    } else if(function==(void *)rmsnorm)++rmsnorms;
    else if(function==(void *)softmax)++softmaxes;
}

void NI __cyg_profile_func_exit(void *function,void *caller) {
    (void)caller;if(!active)return;
    if(function==(void *)quantize) {
        unsigned call=quantizes-1;int size=(call<24 && call%4==3)?H:D;
        QuantizedTensor *q=(call<24 && call%4==3)?&observed->state.hq:&observed->state.xq;
        for(int i=0;i<size/32;++i)require(isfinite(q->s[i]) && q->s[i]>0.0f,"actual finite positive quantizer scales");
        return;
    }
    if(function!=(void *)matmul || active_q==24)return;
    unsigned id=active_q;struct prepared_q *p=&prepared[id];
    require(memcmp(x_before,observed->state.xq.q,D)==0 &&
            memcmp(x_before+D,observed->state.xq.s,9*sizeof(float))==0,"original matmul input readonly");
    struct q288_context context={p->packed,observed->state.xq.q,p->weight->s,observed->state.xq.s,
                                 candidate_output,candidate_slots,integer_leaf};
    q288_full(&context);
    require(memcmp(candidate_output,active_output,D*sizeof(float))==0,"acc8 host wrapper vs actual upstream matmul");
    for(unsigned i=0;i<D;++i)require(isfinite(active_output[i]),"finite full Q output");
    if(pass_number==0) {
        char name[80];snprintf(name,sizeof(name),"pos-%u-q-%02u-input.bin",position_number,id);write_file(name,x_before,sizeof(x_before));
        snprintf(name,sizeof(name),"pos-%u-q-%02u-output.bin",position_number,id);write_file(name,active_output,D*sizeof(float));
    }
    ++q_calls;active_q=24;active_output=NULL;
}

static NI void finite_cache_and_unchanged_rows(Transformer *t,const float *before_key,const float *before_value,unsigned pos) {
    size_t row_bytes=D*sizeof(float);
    for(unsigned layer=0;layer<L;++layer)for(unsigned at=0;at<S;++at) {
        size_t offset=((size_t)layer*S+at)*D;
        const float *key=t->state.key_cache+offset,*value=t->state.value_cache+offset;
        if(at!=pos) {
            require(memcmp(key,before_key+offset,row_bytes)==0 && memcmp(value,before_value+offset,row_bytes)==0,"all other KV rows unchanged");
        } else {
            unsigned nonzero_key=0,nonzero_value=0;
            for(unsigned i=0;i<D;++i) { require(isfinite(key[i]) && isfinite(value[i]),"finite KV row");
                nonzero_key+=key[i]!=0.0f;nonzero_value+=value[i]!=0.0f; }
            require(nonzero_key>0 && nonzero_value>0,"nondegenerate current KV row");
        }
    }
}

int NI main(int argc,char **argv) {
    require(argc==2,"one fresh output directory argument");destination=argv[1];
    require(sizeof(float)==4 && sizeof(void *)==8 && fesetround(FE_TONEAREST)==0,"host binary32/RV64-sized interface and RNE");
    Transformer first={0};first.config=(Config){D,H,L,6,6,V,S};
    size_t weight_bytes;unsigned char *weights=make_weights(&first,&weight_bytes);
    unsigned char *weight_copy=malloc(weight_bytes);require(weight_copy!=NULL,"weight snapshot");memcpy(weight_copy,weights,weight_bytes);
    size_t embedding_bytes=(size_t)V*D*sizeof(float);float *embedding_copy=malloc(embedding_bytes);require(embedding_copy!=NULL,"embedding snapshot");
    memcpy(embedding_copy,first.weights.token_embedding_table,embedding_bytes);prepare_weights(&first);
    Transformer replay={0};replay.config=first.config;replay.weights=first.weights;
    malloc_run_state(&first.state,&first.config);malloc_run_state(&replay.state,&replay.config);
    size_t cache_bytes=(size_t)L*S*D*sizeof(float),logit_bytes=V*sizeof(float);
    float *before_key=malloc(cache_bytes),*before_value=malloc(cache_bytes);
    float *saved_logits=malloc(3*logit_bytes),*saved_key=malloc(3*cache_bytes),*saved_value=malloc(3*cache_bytes);
    require(before_key && before_value && saved_logits && saved_key && saved_value,"state comparison buffers");
    const int tokens[3]={1,7,19};unsigned negative_controls=0;
    for(pass_number=0;pass_number<2;++pass_number) {
        observed=pass_number?&replay:&first;
        for(position_number=0;position_number<3;++position_number) {
            memcpy(before_key,observed->state.key_cache,cache_bytes);memcpy(before_value,observed->state.value_cache,cache_bytes);
            matmuls=quantizes=rmsnorms=softmaxes=q_calls=groups=input_elements=0;active_q=24;active=1;
            float *logits=forward(observed,tokens[position_number],(int)position_number);active=0;
            require(matmuls==43 && quantizes==25 && rmsnorms==13 && softmaxes==36 && q_calls==24 && groups==315 && input_elements==10080,"complete forward observed call/quantizer inventory");
            for(unsigned i=0;i<V;++i)require(isfinite(logits[i]),"all logits finite");
            finite_cache_and_unchanged_rows(observed,before_key,before_value,position_number);
            require(memcmp(weights,weight_copy,weight_bytes)==0 && memcmp(first.weights.token_embedding_table,embedding_copy,embedding_bytes)==0,"all original weight/embedding bytes readonly");
            size_t logit_offset=(size_t)position_number*V,cache_offset=(size_t)position_number*L*S*D;
            if(pass_number==0) {
                memcpy(saved_logits+logit_offset,logits,logit_bytes);memcpy(saved_key+cache_offset,observed->state.key_cache,cache_bytes);memcpy(saved_value+cache_offset,observed->state.value_cache,cache_bytes);
                char name[80];snprintf(name,sizeof(name),"pos-%u-logits.bin",position_number);write_file(name,logits,logit_bytes);
                snprintf(name,sizeof(name),"pos-%u-key.bin",position_number);write_file(name,observed->state.key_cache,cache_bytes);
                snprintf(name,sizeof(name),"pos-%u-value.bin",position_number);write_file(name,observed->state.value_cache,cache_bytes);
            } else {
                require(memcmp(saved_logits+logit_offset,logits,logit_bytes)==0 &&
                        memcmp(saved_key+cache_offset,observed->state.key_cache,cache_bytes)==0 &&
                        memcmp(saved_value+cache_offset,observed->state.value_cache,cache_bytes)==0,"fresh-state complete logits/KV replay bit equality");
                uint32_t old;memcpy(&old,logits,sizeof(old));uint32_t changed=old^1;memcpy(logits,&changed,sizeof(changed));
                require(memcmp(saved_logits+logit_offset,logits,logit_bytes)!=0,"nonvacuous full-logit comparator");
                memcpy(logits,&old,sizeof(old));++negative_controls;
            }
            printf("FORWARD pass=%u pos=%u token=%d matmuls=%u quantizes=%u rmsnorms=%u softmaxes=%u q_calls=%u groups=%u quantized_elements=%u\n",
                   pass_number,position_number,tokens[position_number],matmuls,quantizes,rmsnorms,softmaxes,q_calls,groups,input_elements);
        }
    }
    printf("HOST_FORWARD_PASS calls=6 q_observations=144 exported_q_cases=72 pack_calls=24 packed_bytes=1990656 weight_bytes=%zu embedding_bytes=%zu controls=%u model_trained=0 target_cycles=0\n",weight_bytes,embedding_bytes,negative_controls);
    return 0;
}
