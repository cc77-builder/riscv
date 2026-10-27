/* Actual API/state-isolation checks, linked with the qualified consumer.o. */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "consumer.h"
extern unsigned char fixture_weights[],fixture_weights_end[],fixture_embedding[],fixture_embedding_end[];
extern unsigned char fixture_packed[],fixture_packed_end[],fixture_tail_scales[],fixture_tail_scales_end[];
__thread int errno;
uintptr_t __stack_chk_guard=UINT64_C(0x9157a6c2d384ef09);
unsigned char team_tls_area[96] __attribute__((aligned(16)));
volatile uint64_t api_report[64];
struct guarded_state { uint64_t before[2];struct r2_consumer_state state;uint64_t after[2]; };
struct guarded_state api_states[2] __attribute__((aligned(16)));
unsigned char api_snapshots[6][2][R2_CONSUMER_STATE_BYTES] __attribute__((aligned(16)));
static const uint64_t guard=UINT64_C(0xb5e9c13f6a0742d8);
static unsigned saved,calls;

__attribute__((noreturn)) static void stop(unsigned code) {
    api_report[3]=code;
    __asm__ volatile("mv a0,%0\n.word 0x0000006b"::"r"((uintptr_t)code):"a0","memory");
    for(;;) {}
}
__attribute__((noreturn)) void __stack_chk_fail(void) {stop(90);}
static void check(int ok,unsigned code) {if(!ok)stop(code);}
static unsigned fcsr(void) {unsigned v;__asm__ volatile("csrr %0,fcsr":"=r"(v));return v;}
static void guards(void) {
    for(unsigned i=0;i<2;++i)for(unsigned j=0;j<2;++j)
        check(api_states[i].before[j]==guard && api_states[i].after[j]==guard,81);
    for(unsigned i=0;i<16;++i)check(team_tls_area[i]==0x6b && team_tls_area[80+i]==0xa7,82);
}
static int initialize(const void *weights,size_t weight_bytes,const void *packed) {
    return r2_consumer_init(weights,weight_bytes,fixture_embedding,fixture_embedding_end-fixture_embedding,
        packed,fixture_packed_end-fixture_packed,fixture_tail_scales,fixture_tail_scales_end-fixture_tail_scales);
}
static void initialize_valid(void) {
    check(initialize(fixture_weights,fixture_weights_end-fixture_weights,fixture_packed)==0,83);++api_report[6];
}
static void rejected(struct r2_consumer_state *state,int method,int token,int pos) {
    check(r2_consumer_forward(state,(enum r2_consumer_method)method,token,pos)==NULL,84);++api_report[4];
}
static void save_states(void) {
    guards();check(saved<6,85);
    for(unsigned i=0;i<2;++i)memcpy(api_snapshots[saved][i],&api_states[i].state,R2_CONSUMER_STATE_BYTES);
    ++saved;api_report[8]=saved;
}
static void invoke(unsigned state,int method,int token,int pos) {
    errno=12345;__asm__ volatile("csrwi fcsr,0":::"memory");
    float *logits=r2_consumer_forward(&api_states[state].state,(enum r2_consumer_method)method,token,pos);
    check(logits==api_states[state].state.logits && errno==12345 && fcsr()>>5==0,86);
    api_report[16+calls]=fcsr();++calls;api_report[7]=calls;save_states();
}
int team_forward_main(void) {
    api_report[0]=UINT64_C(0x5232434150493031);api_report[1]=1;api_report[3]=1;
    uintptr_t status,vlenb,tp,address;
    __asm__ volatile("csrr %0,mstatus\ncsrr %1,vlenb\nmv %2,tp":"=r"(status),"=r"(vlenb),"=r"(tp));
    __asm__ volatile("mv %0,%1":"=r"(address):"r"(&errno));
    check((status&0x6000)!=0 && (status&0x600)!=0 && vlenb==16 && errno==0,87);
    check(tp==(uintptr_t)(team_tls_area+16) && address==tp+FULL_ERRNO_OFFSET,88);
    api_report[10]=status;api_report[11]=vlenb;
    for(unsigned i=0;i<16;++i){team_tls_area[i]=0x6b;team_tls_area[80+i]=0xa7;}
    for(unsigned i=0;i<2;++i)for(unsigned j=0;j<2;++j)
        api_states[i].before[j]=api_states[i].after[j]=guard;
    struct r2_consumer_state *a=&api_states[0].state,*b=&api_states[1].state;
    rejected(a,R2_TA_CACHE,1,0);initialize_valid();
    check(initialize(fixture_weights,R2_CONSUMER_WEIGHT_BYTES-1,fixture_packed)==-1,89);++api_report[5];
    rejected(a,R2_TA_CACHE,1,0);initialize_valid();
    check(initialize(fixture_weights,R2_CONSUMER_WEIGHT_BYTES,fixture_packed+1)==-1,91);++api_report[5];
    rejected(a,R2_TA_CACHE,1,0);initialize_valid();
    rejected(NULL,R2_TA_CACHE,1,0);rejected(a,-1,1,0);rejected(a,5,1,0);
    rejected(a,R2_TA_CACHE,-1,0);rejected(a,R2_TA_CACHE,32000,0);
    rejected(a,R2_TA_CACHE,1,-1);rejected(a,R2_TA_CACHE,1,256);
    for(unsigned state=0;state<2;++state) {
        const unsigned char *p=(const unsigned char*)&api_states[state].state;
        for(size_t i=0;i<R2_CONSUMER_STATE_BYTES;++i)check(p[i]==0,92);
    }
    r2_consumer_reset(NULL);guards();
    invoke(0,R2_TA_CACHE,1,0);invoke(1,R2_FR_CACHE,1,0);invoke(0,R2_TA_CACHE,7,1);
    r2_consumer_reset(b);save_states();invoke(1,R2_FR_CACHE,1,0);invoke(0,R2_TA_CACHE,19,2);
    check(api_report[4]==10 && api_report[5]==2 && api_report[6]==3 && calls==5 && saved==6,93);
    api_report[3]=0;return 0;
}
