/* Team-owned host execution harness. Reuses immutable fixture helpers only.
 * Generated functions are separately source-checked against original forward.
 * No reference file, target emulator or old validation rule is modified.
 */
#define main unused_passive_observer_main
#include "../observe.c"
#undef main
#include <inttypes.h>

#ifndef STAGES_VALIDATE
#error STAGES_VALIDATE must be explicitly 0 or 1
#endif

static unsigned fault_mode, quantize_calls, event_count, method_id, current_pos;
struct boundary { unsigned tag; int layer; uint64_t tick; };
static struct boundary boundaries[120];

static void ensure(int good, const char *why) {
    if (!good) {
        fprintf(stderr, "FORWARD_STAGES_FAIL %s method=%u pos=%u\n", why, method_id, current_pos);
        exit(2);
    }
}

static uint64_t tick(void) {
    struct timespec value;
    ensure(clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &value) == 0, "process CPU clock available");
    return (uint64_t)value.tv_sec * UINT64_C(1000000000) + (uint64_t)value.tv_nsec;
}

static void stage_mark(unsigned tag, int layer) {
    uint64_t at = tick();
    if (fault_mode == 1 && tag == 5 && layer == 2) return;
    if (fault_mode == 2 && tag == 5 && layer == 2) layer = 3;
    ensure(event_count < 120, "bounded stage recording");
    boundaries[event_count++] = (struct boundary){tag, layer, at};
}

static void checked_quantize(QuantizedTensor *output, float *input, int n) {
    ++quantize_calls;
    ensure(n == D || n == H, "fixed quantizer dimension");
    for (int start = 0; start < n; start += 32) {
        float maximum = 0.0f;
        for (int i = 0; i < 32; ++i) {
            ensure(isfinite(input[start+i]), "finite quantizer input");
            float magnitude = fabsf(input[start+i]);
            if (magnitude > maximum) maximum = magnitude;
        }
        ensure(maximum > 0.0f, "nonzero quantizer group");
        volatile float scale = maximum / 127.0f;
        ensure(isfinite(scale) && scale > 0.0f, "positive finite quantizer scale");
        for (int i = 0; i < 32; ++i) {
            volatile float value = input[start+i] / scale;
            double rounded = round((double)value);
            ensure(isfinite(value) && rounded >= -128.0 && rounded <= 127.0, "defined int8 quantizer domain");
        }
    }
    quantize(output, input, n);
    for (int i = 0; i < n/32; ++i)
        ensure(isfinite(output->s[i]) && output->s[i] > 0.0f, "actual finite positive quantizer scale");
}

#if STAGES_VALIDATE
#define STAGE_QUANTIZE checked_quantize
#define STAGE_TEST_CACHE(table, pos) do { if (fault_mode == 3 && (pos) == 1) (table)[0] = -(table)[0]; } while (0)
#else
#define STAGE_QUANTIZE quantize
#define STAGE_TEST_CACHE(table, pos) ((void)0)
#endif
#define STAGE_MARK stage_mark
#include "forward.inc"

struct span { const char *name; unsigned char *data; size_t bytes; };
static unsigned spans(RunState *s, struct span *out) {
    struct span items[] = {
        {"x",(unsigned char*)s->x,D*4}, {"xb",(unsigned char*)s->xb,D*4},
        {"xb2",(unsigned char*)s->xb2,D*4}, {"hb",(unsigned char*)s->hb,H*4},
        {"hb2",(unsigned char*)s->hb2,H*4}, {"xq.q",(unsigned char*)s->xq.q,D},
        {"xq.s",(unsigned char*)s->xq.s,D*4}, {"hq.q",(unsigned char*)s->hq.q,H},
        {"hq.s",(unsigned char*)s->hq.s,H*4}, {"q",(unsigned char*)s->q,D*4},
        {"k",(unsigned char*)s->k,D*4}, {"v",(unsigned char*)s->v,D*4},
        {"att",(unsigned char*)s->att,6*S*4}, {"logits",(unsigned char*)s->logits,V*4},
        {"key",(unsigned char*)s->key_cache,L*S*D*4},
        {"value",(unsigned char*)s->value_cache,L*S*D*4}
    };
    memcpy(out,items,sizeof(items)); return sizeof(items)/sizeof(items[0]);
}

static void distinct(Transformer *all) {
    struct span items[64]; unsigned count=0;
    for (unsigned i=0; i<4; ++i) count+=spans(&all[i].state,items+count);
    for (unsigned i=0; i<count; ++i) {
        ensure(items[i].data != NULL, "all state allocations exist");
        for (unsigned j=i+1; j<count; ++j) {
            uintptr_t a=(uintptr_t)items[i].data,b=(uintptr_t)items[j].data;
            ensure(a+items[i].bytes<=b || b+items[j].bytes<=a, "independent state spans");
        }
    }
}

static void compare_state(RunState *reference, RunState *candidate) {
    struct span left[16], right[16];
    ensure(spans(reference,left)==16 && spans(candidate,right)==16, "complete 16-span state inventory");
    for (unsigned i=0; i<16; ++i) {
        if (memcmp(left[i].data,right[i].data,left[i].bytes)!=0) {
            fprintf(stderr,"STATE_MISMATCH span=%s method=%u pos=%u\n",left[i].name,method_id,current_pos);
            ensure(0,"complete state equality");
        }
    }
}

static size_t save_state(RunState *state, unsigned method, unsigned position) {
    struct span parts[16];spans(state,parts);
    size_t bytes=0;for(unsigned i=0;i<16;++i)bytes+=parts[i].bytes;
    unsigned char *raw=malloc(bytes);ensure(raw!=NULL,"state export allocation");
    size_t offset=0;
    for(unsigned i=0;i<16;++i) {memcpy(raw+offset,parts[i].data,parts[i].bytes);offset+=parts[i].bytes;}
    char name[80];snprintf(name,sizeof(name),"state-m%u-p%u.bin",method,position);
    write_file(name,raw,bytes);free(raw);return bytes;
}

static uint64_t check_trace(uint64_t begin, uint64_t end, FILE *log) {
    ensure(event_count==120,"exact boundary count");
    uint64_t sum=0;
    for(unsigned i=0;i<120;++i) {
        unsigned tag;int layer;
        if(i<2) {tag=i;layer=-1;}
        else if(i<116) {tag=2+(i-2)%19;layer=(int)((i-2)/19);}
        else {tag=21+i-116;layer=-1;}
        ensure(boundaries[i].tag==tag && boundaries[i].layer==layer,"exact stage and layer sequence");
        ensure(boundaries[i].tick>=begin && boundaries[i].tick<=end,"boundary inside complete call");
        if(i) {
            ensure(boundaries[i].tick>=boundaries[i-1].tick,"monotonic stage clock");
            uint64_t delta=boundaries[i].tick-boundaries[i-1].tick;sum+=delta;
            fprintf(log,"%u,%u,%u,%u,%d,%" PRIu64 ",%" PRIu64 "\n",method_id,current_pos,i-1,
                    boundaries[i-1].tag,boundaries[i-1].layer,boundaries[i-1].tick,boundaries[i].tick);
        }
    }
    ensure(sum==boundaries[119].tick-boundaries[0].tick,"all half-open stages close exactly");
    ensure(sum<=end-begin,"stage span bounded by full call");return sum;
}

int main(int argc,char **argv) {
    ensure(argc==4,"output, positions and control arguments required");
    char *tail;long positions=strtol(argv[2],&tail,10);ensure(!*tail && positions>=3 && positions<=256,"bounded continuous positions");
    long control=strtol(argv[3],&tail,10);ensure(!*tail && control>=0 && control<=5,"bounded control");fault_mode=(unsigned)control;
    ensure(STAGES_VALIDATE || !fault_mode,"controls require validation build");
    destination=argv[1];ensure(sizeof(float)==4 && sizeof(void*)==8 && fesetround(FE_TONEAREST)==0,"host binary32/RNE/64-bit ABI");
    Transformer all[4]={0};all[0].config=(Config){D,H,L,6,6,V,S};
    size_t weight_bytes;random_state=UINT32_C(0x53485041);
    unsigned char *weights=make_weights(all,&weight_bytes),*weight_copy=malloc(weight_bytes);
    size_t embedding_bytes=(size_t)V*D*4,cache_bytes=(size_t)L*S*D*4;
    unsigned char *embedding_copy=malloc(embedding_bytes);
    float *before_key=malloc(cache_bytes),*before_value=malloc(cache_bytes);
    ensure(weight_copy && embedding_copy && before_key && before_value,"validation snapshots allocated");
    memcpy(weight_copy,weights,weight_bytes);memcpy(embedding_copy,all[0].weights.token_embedding_table,embedding_bytes);
    for(unsigned i=0;i<4;++i) {
        all[i].config=all[0].config;all[i].weights=all[0].weights;malloc_run_state(&all[i].state,&all[i].config);
    }
    if(fault_mode==5)all[3].state.x=all[2].state.x;
    distinct(all);
    char path[4096];int n=snprintf(path,sizeof(path),"%s/stages.csv",destination);
    ensure(n>0 && (size_t)n<sizeof(path),"bounded stage path");
    FILE *log=fopen(path,"wb");ensure(log!=NULL,"stage log open");
    fprintf(log,"method,position,index,tag,layer,start_ns,end_ns\n");
    float *(*functions[4])(Transformer*,int,int)={forward,stage_reference,stage_cached,cached_forward};
    const unsigned order[]={1,2,3,0};size_t state_bytes=0;
    for(current_pos=0;current_pos<(unsigned)positions;++current_pos) {
        const int first[]={1,7,19};
        int token=current_pos<3?first[current_pos]:(int)((current_pos*7919u+17u)%V);
        for(unsigned j=0;j<4;++j) {
            method_id=order[j];Transformer *t=&all[method_id];
            memcpy(before_key,t->state.key_cache,cache_bytes);memcpy(before_value,t->state.value_cache,cache_bytes);
            quantize_calls=event_count=0;
            pass_number=method_id;position_number=current_pos;
            uint64_t begin=tick();float *logits=functions[method_id](t,token,(int)current_pos);uint64_t end=tick();
            if(fault_mode==4 && method_id==2 && current_pos==1) {
                uint32_t bit;memcpy(&bit,t->state.key_cache,4);bit^=1;memcpy(t->state.key_cache,&bit,4);
            }
            ensure(logits==t->state.logits,"actual full forward output");
            for(unsigned i=0;i<V;++i)ensure(isfinite(logits[i]),"all logits finite");
            finite_cache_and_unchanged_rows(t,before_key,before_value,current_pos);
            ensure(memcmp(weights,weight_copy,weight_bytes)==0 &&
                   memcmp(t->weights.token_embedding_table,embedding_copy,embedding_bytes)==0,"all weights and embedding unchanged");
            if(STAGES_VALIDATE && method_id)ensure(quantize_calls==25,"all candidate quantizer domains checked");
            uint64_t span=(method_id==1 || method_id==2)?check_trace(begin,end,log):0;
            printf("{\"event\":\"call\",\"method\":%u,\"position\":%u,\"token\":%d,\"outer_ns\":%" PRIu64
                   ",\"stage_span_ns\":%" PRIu64 ",\"boundaries\":%u,\"checked_quantizers\":%u}\n",
                   method_id,current_pos,token,end-begin,span,event_count,quantize_calls);
        }
        for(method_id=1;method_id<4;++method_id)compare_state(&all[0].state,&all[method_id].state);
        if(current_pos<3 || current_pos+1==(unsigned)positions)
            for(unsigned m=0;m<4;++m)state_bytes=save_state(&all[m].state,m,current_pos);
        printf("{\"event\":\"position_pass\",\"position\":%u,\"compared_states\":4,\"spans_per_state\":16}\n",current_pos);
    }
    ensure(fclose(log)==0,"stage log closed");
    printf("{\"event\":\"complete\",\"status\":\"FORWARD_STAGES_PASS\",\"positions\":%ld,\"validation\":%d,\"state_bytes\":%zu,\"target_emu_runs\":0}\n",
           positions,STAGES_VALIDATE,state_bytes);
    for(unsigned i=0;i<4;++i)free_run_state(&all[i].state);
    free(weight_copy);free(embedding_copy);free(before_key);free(before_value);
    free(all[0].weights.token_embedding_table);free(all[0].weights.q_tokens);
    free(all[0].weights.wq);free(all[0].weights.wk);free(all[0].weights.wv);free(all[0].weights.wo);
    free(all[0].weights.w1);free(all[0].weights.w2);free(all[0].weights.w3);free(weights);
    return 0;
}
