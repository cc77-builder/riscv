/* Actual RISC-V full forward, with independent original and RoPE-cache states. */
#define TESTING
#include "upstream/runq.c"
#define D 288
#define H 768
#define L 6
#define V 32000
#define S 256
#include "state_layout.h"

__thread int errno;
uintptr_t __stack_chk_guard=UINT64_C(0x9157a6c2d384ef09);
unsigned char team_tls_area[96] __attribute__((aligned(16)));
volatile uint32_t full_control __attribute__((section(".data"),used))=0;
volatile uint64_t full_report[32];
unsigned char full_snapshots[3][2][FULL_STATE_BYTES] __attribute__((aligned(16)));
struct full_event { uint32_t tag;int32_t layer; };
struct full_event full_events[3][120];
static struct full_storage storage[2] __attribute__((aligned(16)));
static Transformer transforms[2];
static QuantizedTensor token_weights,qweights[L],kweights[L],vweights[L],oweights[L],w1weights[L],w2weights[L],w3weights[L];
extern unsigned char fixture_weights[],fixture_weights_end[],fixture_embedding[],fixture_embedding_end[];
static unsigned position,event_count;

__attribute__((noreturn)) static void stop(unsigned code) {
    full_report[3]=code;
    __asm__ volatile("mv a0,%0\n.word 0x0000006b"::"r"((uintptr_t)code):"a0","memory");
    for(;;) {}
}
__attribute__((noreturn)) void __stack_chk_fail(void) {stop(90);}
static void check(int ok,unsigned code) {if(!ok)stop(code);}
static void tls_check(void) {
    uintptr_t tp;__asm__ volatile("mv %0,tp":"=r"(tp));
    check(tp==(uintptr_t)(team_tls_area+16) && (uintptr_t)&errno==tp+FULL_ERRNO_OFFSET,80);
    for(unsigned i=0;i<16;++i)check(team_tls_area[i]==0x6b && team_tls_area[80+i]==0xa7,81);
}
static unsigned fcsr(void) {unsigned value;__asm__ volatile("csrr %0,fcsr":"=r"(value));return value;}
static void stage_mark(unsigned tag,int layer) {
    check(event_count<120,82);full_events[position][event_count++]=(struct full_event){tag,layer};
}
#define STAGE_MARK stage_mark
#define STAGE_QUANTIZE quantize
#define STAGE_TEST_CACHE(table,pos) ((void)0)
#include "forward.inc"

static void tensor(unsigned char **cursor,QuantizedTensor *t,size_t elements) {
    t->q=(int8_t*)*cursor;*cursor+=elements;t->s=(float*)*cursor;*cursor+=elements/32*4;
}
static void weights(TransformerWeights *w) {
    unsigned char *cursor=fixture_weights;
    w->rms_att_weight=(float*)cursor;cursor+=L*D*4;
    w->rms_ffn_weight=(float*)cursor;cursor+=L*D*4;
    w->rms_final_weight=(float*)cursor;cursor+=D*4;
    tensor(&cursor,&token_weights,(size_t)V*D);w->q_tokens=&token_weights;w->wcls=&token_weights;
    QuantizedTensor *arrays[]={qweights,kweights,vweights,oweights,w1weights,w2weights,w3weights};
    for(unsigned kind=0;kind<7;++kind)for(unsigned l=0;l<L;++l)tensor(&cursor,&arrays[kind][l],kind<4?D*D:D*H);
    w->wq=qweights;w->wk=kweights;w->wv=vweights;w->wo=oweights;w->w1=w1weights;w->w2=w2weights;w->w3=w3weights;
    w->token_embedding_table=(float*)fixture_embedding;
    check(cursor==fixture_weights_end && fixture_embedding_end-fixture_embedding==(size_t)V*D*4,83);
}
static void full_compare_state(RunState *left,RunState *right) {
    struct full_span a[16],b[16];full_spans(left,a);full_spans(right,b);
    for(unsigned s=0;s<16;++s) {
        full_report[6]=s;
        if(memcmp(a[s].data,b[s].data,a[s].bytes)) {
            for(size_t i=0;i<a[s].bytes;++i)if(a[s].data[i]!=b[s].data[i]) {full_report[7]=i;break;}
            stop(84);
        }
    }
}
int team_forward_main(void) {
    full_report[0]=UINT64_C(0x523246554c4c3031);full_report[1]=1;full_report[2]=3;full_report[3]=1;
    check(sizeof(float)==4 && sizeof(uintptr_t)==8 && sizeof(struct full_storage)==FULL_STATE_BYTES,85);
    check(errno==0,86);for(unsigned i=0;i<16;++i) {team_tls_area[i]=0x6b;team_tls_area[80+i]=0xa7;}
    tls_check();GS=32;
    transforms[0].config=(Config){D,H,L,6,6,V,S};weights(&transforms[0].weights);
    transforms[1].config=transforms[0].config;transforms[1].weights=transforms[0].weights;
    for(unsigned m=0;m<2;++m)full_bind_state(&transforms[m].state,&storage[m]);
    const int tokens[3]={1,7,19};
    for(position=0;position<3;++position) {
        full_report[4]=position;
        for(unsigned method=0;method<2;++method) {
            full_report[5]=method;event_count=0;errno=12345;
            __asm__ volatile("csrwi fcsr,0" ::: "memory");
            Transformer *t=&transforms[method];
            float *logits=method?stage_cached(t,tokens[position],(int)position):forward(t,tokens[position],(int)position);
            check(logits==t->state.logits && event_count==(method?120:0),87);
            check((fcsr()>>5)==0 && errno==12345,88);full_report[10+2*position+method]=fcsr();tls_check();
            if(full_control==1 && position==0 && method==1) {uint32_t bits;memcpy(&bits,logits,4);bits^=1;memcpy(logits,&bits,4);}
            check(full_save_state(&t->state,full_snapshots[position][method])==FULL_STATE_BYTES,89);
        }
        full_compare_state(&transforms[0].state,&transforms[1].state);
        full_report[8]=position+1;
    }
    full_report[3]=0;full_report[9]=full_control;return 0;
}
