/* Capture each real layer boundary before the next layer overwrites Q/K. */
#define main unused_original_observer_main
#include "observe.c"
#undef main
#include "state_layout.h"
#include "rope.h"
static const unsigned positions[ROPE_CASES]={0,1,2,31,127,255};
static struct rope_case before[ROPE_CASES],after[ROPE_CASES];
static unsigned seen[ROPE_CASES][2][ROPE_LAYERS];
static RunState *capture_state;
static unsigned current;
static void capture(unsigned tag,int layer) {
    if(tag!=7 && tag!=8)return;
    require(layer>=0 && layer<ROPE_LAYERS,"captured real layer");
    for(unsigned c=0;c<ROPE_CASES;++c)if(current==positions[c]) {
        unsigned side=tag==8;
        require(!seen[c][side][layer]++,"one ordered pre/post boundary");
        struct rope_layer *dest=side?&after[c].layer[layer]:&before[c].layer[layer];
        memcpy(dest->q,capture_state->q,sizeof(dest->q));memcpy(dest->k,capture_state->k,sizeof(dest->k));
    }
}
#define STAGE_MARK capture
#define STAGE_QUANTIZE quantize
#define STAGE_TEST_CACHE(table,pos) ((void)0)
#include "forward.inc"
int main(int argc,char **argv) {
    require(argc==2,"fresh output path");destination=argv[1];
    require(fesetround(FE_TONEAREST)==0 && sizeof(struct rope_case)==ROPE_BYTES,"binary32 capture layout");
    Transformer original={0};original.config=(Config){D,H,L,6,6,V,S};
    size_t bytes;random_state=UINT32_C(0x53485041);unsigned char *weights=make_weights(&original,&bytes);
    Transformer traced=original;malloc_run_state(&original.state,&original.config);malloc_run_state(&traced.state,&traced.config);
    capture_state=&traced.state;
    unsigned char *a=malloc(FULL_STATE_BYTES),*b=malloc(FULL_STATE_BYTES);require(a&&b,"complete comparison buffers");
    for(current=0;current<256;++current) {
        int token=current==0?1:current==1?7:current==2?19:(int)((current*7919+17)%V);
        stage_reference(&traced,token,(int)current);forward(&original,token,(int)current);
        require(full_save_state(&traced.state,a)==FULL_STATE_BYTES && full_save_state(&original.state,b)==FULL_STATE_BYTES,"all original state spans");
        require(!memcmp(a,b,FULL_STATE_BYTES),"capture preserves complete original state");
    }
    for(unsigned c=0;c<ROPE_CASES;++c) {
        for(unsigned side=0;side<2;++side)for(unsigned l=0;l<ROPE_LAYERS;++l)require(seen[c][side][l]==1,"complete boundary capture");
        struct rope_case trial=before[c];rope_original(&trial,(int)positions[c]);require(!memcmp(&trial,&after[c],ROPE_BYTES),"isolated original equals captured golden");
        trial=before[c];rope_cached(&trial,(int)positions[c]);require(!memcmp(&trial,&after[c],ROPE_BYTES),"isolated cache equals captured golden");
        printf("ROPE_CAPTURE %u %u %016lx %016lx\n",c,positions[c],(unsigned long)rope_digest(&before[c],ROPE_BYTES),(unsigned long)rope_digest(&after[c],ROPE_BYTES));
    }
    write_file("before.bin",before,sizeof(before));write_file("after.bin",after,sizeof(after));
    write_file("positions.bin",positions,sizeof(positions));
    printf("ROPE_EXPORT_PASS positions=256 captured=6 state_spans=16 bytes=165888\n");
    free(a);free(b);free_run_state(&original.state);free_run_state(&traced.state);
    free(original.weights.token_embedding_table);free(original.weights.q_tokens);
    free(original.weights.wq);free(original.weights.wk);free(original.weights.wv);free(original.weights.wo);
    free(original.weights.w1);free(original.weights.w2);free(original.weights.w3);free(weights);return 0;
}
