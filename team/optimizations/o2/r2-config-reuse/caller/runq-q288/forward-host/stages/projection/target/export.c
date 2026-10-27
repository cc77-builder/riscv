/* Real call-site capture; final xq belongs to classifier, not to W1. */
#define main unused_original_observer_main
#include "observe.c"
#undef main
#include "state_layout.h"
static RunState *capture_state;
static unsigned current,seen[2][2];
static int8_t inputs[2][288];
static float scales[2][9],outputs[2][768];
static void capture(unsigned tag,int layer) {
    if(current!=2)return;
    if((tag==15 || tag==16) && layer==5) {
        unsigned side=tag==16;require(!seen[1][side]++,"one W1 pre/post boundary");
        if(side)memcpy(outputs[1],capture_state->hb,768*4);
        else {memcpy(inputs[1],capture_state->xq.q,288);memcpy(scales[1],capture_state->xq.s,9*4);}
    }
    if(tag==23 || tag==24) {
        unsigned side=tag==24;require(layer==-1 && !seen[0][side]++,"one classifier pre/post boundary");
        if(side)memcpy(outputs[0],capture_state->logits+31680,320*4);
        else {memcpy(inputs[0],capture_state->xq.q,288);memcpy(scales[0],capture_state->xq.s,9*4);}
    }
}
#define STAGE_MARK capture
#define STAGE_QUANTIZE quantize
#define STAGE_TEST_CACHE(table,pos) ((void)0)
#include "forward.inc"
int main(int argc,char **argv) {
    require(argc==2,"fresh output path");destination=argv[1];require(fesetround(FE_TONEAREST)==0,"host RNE");
    Transformer original={0};original.config=(Config){D,H,L,6,6,V,S};size_t bytes;
    random_state=UINT32_C(0x53485041);unsigned char *weights=make_weights(&original,&bytes);
    write_file("weights.bin",weights,bytes);write_file("embedding.bin",original.weights.token_embedding_table,(size_t)V*D*4);
    Transformer traced=original;malloc_run_state(&original.state,&original.config);malloc_run_state(&traced.state,&traced.config);
    capture_state=&traced.state;unsigned char *a=malloc(FULL_STATE_BYTES),*b=malloc(FULL_STATE_BYTES);require(a&&b,"complete states");
    const int tokens[]={1,7,19};
    for(current=0;current<3;++current) {
        stage_reference(&traced,tokens[current],(int)current);forward(&original,tokens[current],(int)current);
        require(full_save_state(&traced.state,a)==FULL_STATE_BYTES && full_save_state(&original.state,b)==FULL_STATE_BYTES,"all spans");
        require(!memcmp(a,b,FULL_STATE_BYTES),"capture preserves whole original state");
        char name[32];snprintf(name,sizeof(name),"host-state-p%u.bin",current);write_file(name,b,FULL_STATE_BYTES);
    }
    for(unsigned c=0;c<2;++c)for(unsigned side=0;side<2;++side)require(seen[c][side]==1,"actual complete captures");
    uint32_t flags[2];float isolated[768];
    for(unsigned c=0;c<2;++c) {
        QuantizedTensor x={inputs[c],scales[c]},w=c?original.weights.w1[5]:*original.weights.wcls;
        if(!c) {w.q+=31680*288;w.s+=31680*9;}
        require(feclearexcept(FE_ALL_EXCEPT)==0,"clear host arithmetic flags");
        matmul(isolated,&x,&w,288,c?768:320);
        require(fetestexcept(FE_ALL_EXCEPT)==FE_INEXACT,"isolated host kernel NX-only mapping");flags[c]=1;
        require(!memcmp(isolated,outputs[c],(c?768:320)*4),"isolated exact matrix equals real captured output");
    }
    write_file("input-q.bin",inputs,sizeof(inputs));write_file("input-scales.bin",scales,sizeof(scales));write_file("gold.bin",outputs,sizeof(outputs));
    write_file("expected-flags.bin",flags,sizeof(flags));
    puts("PROJECTION_BOUNDARY_EXPORT_PASS positions=3 full_state_bytes=3691424 cases=2 rows=320,768");
    free(a);free(b);free_run_state(&original.state);free_run_state(&traced.state);
    free(original.weights.token_embedding_table);free(original.weights.q_tokens);free(original.weights.wq);free(original.weights.wk);
    free(original.weights.wv);free(original.weights.wo);free(original.weights.w1);free(original.weights.w2);free(original.weights.w3);free(weights);return 0;
}
