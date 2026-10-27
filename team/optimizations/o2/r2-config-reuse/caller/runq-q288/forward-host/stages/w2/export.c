/* Capture the actual p2/layer5 W2 boundary in an unchanged-source forward. */
#define main unused_original_observer_main
#include "observe.c"
#undef main
#include "state_layout.h"
static RunState *capture_state;
static unsigned current,seen[2];
static int8_t input[768];
static float scales[24],output[288];
static void capture(unsigned tag,int layer) {
    if(current!=2 || layer!=5 || (tag!=19 && tag!=20))return;
    unsigned side=tag==20;require(!seen[side]++,"one W2 pre/post boundary");
    if(side)memcpy(output,capture_state->xb,sizeof(output));
    else {memcpy(input,capture_state->hq.q,sizeof(input));memcpy(scales,capture_state->hq.s,sizeof(scales));}
}
#define STAGE_MARK capture
#define STAGE_QUANTIZE quantize
#define STAGE_TEST_CACHE(table,pos) ((void)0)
#include "forward.inc"
int main(int argc,char **argv) {
    require(argc==2,"fresh output path");destination=argv[1];require(!fesetround(FE_TONEAREST),"host RNE");
    Transformer original={0};original.config=(Config){D,H,L,6,6,V,S};size_t bytes;
    random_state=UINT32_C(0x53485041);unsigned char *weights=make_weights(&original,&bytes);
    Transformer traced=original;malloc_run_state(&original.state,&original.config);malloc_run_state(&traced.state,&traced.config);
    capture_state=&traced.state;unsigned char *a=malloc(FULL_STATE_BYTES),*b=malloc(FULL_STATE_BYTES);require(a&&b,"complete states");
    const int tokens[]={1,7,19};
    for(current=0;current<3;++current) {
        stage_reference(&traced,tokens[current],(int)current);forward(&original,tokens[current],(int)current);
        require(full_save_state(&traced.state,a)==FULL_STATE_BYTES && full_save_state(&original.state,b)==FULL_STATE_BYTES,"all spans");
        require(!memcmp(a,b,FULL_STATE_BYTES),"capture preserves every original state byte");
        char name[32];snprintf(name,sizeof(name),"host-state-p%u.bin",current);write_file(name,b,FULL_STATE_BYTES);
    }
    require(seen[0]==1 && seen[1]==1,"actual complete W2 capture");
    QuantizedTensor x={input,scales},w=original.weights.w2[5];float isolated[288];
    require(!feclearexcept(FE_ALL_EXCEPT),"clear arithmetic flags");matmul(isolated,&x,&w,768,288);
    require(fetestexcept(FE_ALL_EXCEPT)==FE_INEXACT,"original W2 NX-only flags");
    require(!memcmp(isolated,output,sizeof(output)),"isolated original matmul equals real forward output");
    write_file("weight.bin",w.q,288*768);write_file("scales.bin",w.s,288*24*4);
    write_file("input.bin",input,sizeof(input));write_file("input-scales.bin",scales,sizeof(scales));write_file("gold.bin",output,sizeof(output));
    uint32_t flags=1;write_file("expected-flags.bin",&flags,4);
    puts("W2_EXPORT_PASS positions=3 full_state_bytes=3691424 position=2 layer=5 rows=288 k=768");
    free(a);free(b);free_run_state(&original.state);free_run_state(&traced.state);
    free(original.weights.token_embedding_table);free(original.weights.q_tokens);free(original.weights.wq);free(original.weights.wk);
    free(original.weights.wv);free(original.weights.wo);free(original.weights.w1);free(original.weights.w2);free(original.weights.w3);free(weights);return 0;
}
