/* Passive capture around exact original RMSNorm in an original forward. */
#define main unused_observer_main
#include "observe.c"
#undef main
#include "state_layout.h"
#include <errno.h>
#include <float.h>
#define CASES 48
static float inputs[CASES][288],weights[CASES][288],gold[CASES][288];
static uint32_t flags[CASES],aliases[39];
static unsigned position,call;
static void capture_norm(float *o,float *x,float *w,int n) {
    require(position<3 && call<13 && n==288,"exact norm geometry");
    unsigned id=position*13+call++;
    memcpy(inputs[id],x,1152);memcpy(weights[id],w,1152);
    aliases[id]=o==x;
    rmsnorm(o,x,w,n);
    memcpy(gold[id],o,1152);
}
#define STAGE_MARK(tag,layer) ((void)0)
#define STAGE_QUANTIZE quantize
#define STAGE_TEST_CACHE(table,pos) ((void)0)
#include "capture.inc"
static float bits(uint32_t u) {float f;memcpy(&f,&u,4);return f;}
static unsigned rvflags(int f) {
    return ((f&FE_INEXACT)?1:0)|((f&FE_UNDERFLOW)?2:0)|((f&FE_OVERFLOW)?4:0)|
           ((f&FE_DIVBYZERO)?8:0)|((f&FE_INVALID)?16:0);
}
int main(int argc,char **argv) {
    require(argc==2,"fresh output");destination=argv[1];require(!fesetround(FE_TONEAREST),"RNE");
    Transformer a={0};a.config=(Config){D,H,L,6,6,V,S};size_t bytes;
    random_state=UINT32_C(0x53485041);unsigned char *model=make_weights(&a,&bytes);
    Transformer b=a;malloc_run_state(&a.state,&a.config);malloc_run_state(&b.state,&b.config);
    unsigned char *sa=malloc(FULL_STATE_BYTES),*sb=malloc(FULL_STATE_BYTES);require(sa&&sb,"state buffers");
    const int tokens[]={1,7,19};
    for(position=0;position<3;++position) {
        call=0;stage_reference(&a,tokens[position],(int)position);forward(&b,tokens[position],(int)position);
        require(call==13,"all actual norm calls");
        require(full_save_state(&a.state,sa)==FULL_STATE_BYTES && full_save_state(&b.state,sb)==FULL_STATE_BYTES,"complete state spans");
        require(!memcmp(sa,sb,FULL_STATE_BYTES),"capture preserves complete original forward");
        for(unsigned i=0;i<13;++i)require(aliases[position*13+i]==(i==12),"last actual norm is in-place");
        char name[32];snprintf(name,sizeof(name),"host-state-p%u.bin",position);write_file(name,sb,FULL_STATE_BYTES);
    }
    for(unsigned i=39;i<CASES;++i)for(unsigned j=0;j<288;++j){inputs[i][j]=0.0f;weights[i][j]=1.0f;}
    for(unsigned j=0;j<288;++j) {
        inputs[40][j]=bits((j&1)?0x80000000:0);weights[40][j]=(j&2)?-1.0f:1.0f;
        inputs[41][j]=bits((j&1)?0x80000001:1);weights[41][j]=bits(0x00800000);
        inputs[45][j]=inputs[46][j]=1.0f;
        weights[45][j]=bits(0x00800000);weights[46][j]=bits(1);
    }
    inputs[42][0]=FLT_MAX;
    inputs[43][0]=1.0f;weights[43][0]=FLT_MAX;
    inputs[44][0]=4096.0f;inputs[44][1]=inputs[44][2]=1.0f;
    const uint32_t pattern[17]={0xbf924925,0xbf800000,0xbf5b6db7,0xbf36db6e,0xbf124925,
        0xbedb6db7,0xbe924925,0xbe124925,0,0x3e124925,0x3e924925,0x3edb6db7,0x3f124925,
        0x3f36db6e,0x3f5b6db7,0x3f800000,0x3f924925};
    for(unsigned j=0;j<288;++j)inputs[47][j]=bits(pattern[j%17]);
    weights[47][106]=bits(0x3f85eb9f);
    for(unsigned i=0;i<CASES;++i) {
        float actual[288];require(!feclearexcept(FE_ALL_EXCEPT),"clear flags");errno=73;
        rmsnorm(actual,inputs[i],weights[i],288);
        flags[i]=rvflags(fetestexcept(FE_ALL_EXCEPT));require(errno==73,"errno preserved");
        if(i<39)require(!memcmp(actual,gold[i],1152),"isolated norm equals captured full-forward output");
        else memcpy(gold[i],actual,1152);
        for(unsigned j=0;j<288;++j)require(isfinite(inputs[i][j])&&isfinite(weights[i][j]),"finite contract inputs");
    }
    require(flags[45]==1 && flags[46]==3 && flags[42]==5 && flags[43]==5,"specific underflow/overflow witnesses");
    require(gold[45][0]==bits(0x007fffd6) && gold[46][0]==bits(1) &&
            gold[47][106]==bits(0xbf5b530d),"exact subnormal/order witnesses");
    write_file("input.bin",inputs,sizeof(inputs));write_file("weight.bin",weights,sizeof(weights));
    write_file("gold.bin",gold,sizeof(gold));write_file("flags.bin",flags,sizeof(flags));
    write_file("aliases.bin",aliases,sizeof(aliases));
    puts("NORM_EXPORT_PASS real_cases=39 synthetic_cases=9 full_states=3 size=288");
    free(sa);free(sb);free_run_state(&a.state);free_run_state(&b.state);
    free(a.weights.token_embedding_table);free(a.weights.q_tokens);free(a.weights.wq);free(a.weights.wk);
    free(a.weights.wv);free(a.weights.wo);free(a.weights.w1);free(a.weights.w2);free(a.weights.w3);free(model);
    return 0;
}
