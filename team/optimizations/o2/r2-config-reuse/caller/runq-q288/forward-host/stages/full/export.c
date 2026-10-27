/* Export the exact existing deterministic fixture and original host states. */
#define main unused_original_observer_main
#include "observe.c"
#undef main
#include "state_layout.h"

int main(int argc,char **argv) {
    require(argc==2,"one fresh destination");destination=argv[1];
    require(sizeof(float)==4 && fesetround(FE_TONEAREST)==0,"binary32 RNE");
    Transformer t={0};t.config=(Config){D,H,L,6,6,V,S};
    size_t bytes;random_state=UINT32_C(0x53485041);unsigned char *weights=make_weights(&t,&bytes);
    write_file("weights.bin",weights,bytes);
    write_file("embedding.bin",t.weights.token_embedding_table,(size_t)V*D*4);
    malloc_run_state(&t.state,&t.config);
    unsigned char *snapshot=malloc(FULL_STATE_BYTES);require(snapshot!=NULL,"snapshot allocation");
    const int tokens[3]={1,7,19};
    for(unsigned p=0;p<3;++p) {
        float *logits=forward(&t,tokens[p],(int)p);
        require(logits==t.state.logits,"actual original full forward");
        for(unsigned i=0;i<V;++i)require(isfinite(logits[i]),"finite original logits");
        require(full_save_state(&t.state,snapshot)==FULL_STATE_BYTES,"complete state export");
        char name[32];snprintf(name,sizeof(name),"host-state-p%u.bin",p);write_file(name,snapshot,FULL_STATE_BYTES);
    }
    printf("FULL_EXPORT_PASS positions=3 weights=%zu embedding=%zu state=%u\n",bytes,(size_t)V*D*4,FULL_STATE_BYTES);
    free(snapshot);free_run_state(&t.state);
    free(t.weights.token_embedding_table);free(t.weights.q_tokens);
    free(t.weights.wq);free(t.weights.wk);free(t.weights.wv);free(t.weights.wo);
    free(t.weights.w1);free(t.weights.w2);free(t.weights.w3);free(weights);return 0;
}
