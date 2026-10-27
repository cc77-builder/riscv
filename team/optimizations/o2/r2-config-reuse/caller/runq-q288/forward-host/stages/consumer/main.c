/* Validation harness. The complete pure consumer lives in consumer.c. */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "consumer.h"

extern unsigned char fixture_weights[],fixture_weights_end[],fixture_embedding[],fixture_embedding_end[];
extern unsigned char fixture_packed[],fixture_packed_end[],fixture_tail_scales[],fixture_tail_scales_end[];
__thread int errno;
uintptr_t __stack_chk_guard=UINT64_C(0x9157a6c2d384ef09);
unsigned char team_tls_area[96] __attribute__((aligned(16)));
/* method, consecutive positions, application negative, save selected states */
volatile uint32_t consumer_control[4] __attribute__((section(".data"),used))={4,3,0,1};
volatile uint64_t consumer_report[64];
uint64_t consumer_flags[256],consumer_times[256][4];
unsigned char consumer_snapshots[6][R2_CONSUMER_STATE_BYTES] __attribute__((aligned(16)));
struct r2_consumer_state consumer_state __attribute__((aligned(16)));
static const unsigned selected_positions[6]={0,1,2,31,127,255};

__attribute__((noreturn)) static void stop(unsigned code) {
    consumer_report[3]=code;
    __asm__ volatile("mv a0,%0\n.word 0x0000006b"::"r"((uintptr_t)code):"a0","memory");
    for(;;) {}
}
__attribute__((noreturn)) void __stack_chk_fail(void) {stop(90);}
static void check(int ok,unsigned code) {if(!ok)stop(code);}
static unsigned fcsr(void) {unsigned value;__asm__ volatile("csrr %0,fcsr":"=r"(value));return value;}
static uint64_t cycle(void) {uint64_t v;__asm__ volatile("fence iorw,iorw\nrdcycle %0\nfence iorw,iorw":"=r"(v)::"memory");return v;}
static uint64_t instret(void) {uint64_t v;__asm__ volatile("fence iorw,iorw\nrdinstret %0\nfence iorw,iorw":"=r"(v)::"memory");return v;}
static void tls_check(void) {
    uintptr_t tp,error_address;
    __asm__ volatile("mv %0,tp":"=r"(tp));
    __asm__ volatile("mv %0,%1":"=r"(error_address):"r"(&errno));
    check(tp==(uintptr_t)(team_tls_area+16) && error_address==tp+FULL_ERRNO_OFFSET,80);
    for(unsigned i=0;i<16;++i)check(team_tls_area[i]==0x6b && team_tls_area[80+i]==0xa7,81);
}
int team_forward_main(void) {
    unsigned method=consumer_control[0],positions=consumer_control[1],negative=consumer_control[2],snapshots=consumer_control[3];
    consumer_report[0]=UINT64_C(0x5232434f4e533031);consumer_report[1]=1;consumer_report[2]=method;consumer_report[3]=1;
    consumer_report[4]=positions;consumer_report[5]=negative;consumer_report[6]=snapshots;
    check(method<=4 && positions>=1 && positions<=256 && negative<=1 && snapshots<=1,82);
    uintptr_t status,vlenb;__asm__ volatile("csrr %0,mstatus\ncsrr %1,vlenb":"=r"(status),"=r"(vlenb));
    check((status&0x6000)!=0 && (status&0x600)!=0 && vlenb==16,83);
    consumer_report[10]=status;consumer_report[11]=vlenb;
    check(errno==0,84);for(unsigned i=0;i<16;++i) {team_tls_area[i]=0x6b;team_tls_area[80+i]=0xa7;}tls_check();
    check(r2_consumer_init(fixture_weights,fixture_weights_end-fixture_weights,
                          fixture_embedding,fixture_embedding_end-fixture_embedding,
                          fixture_packed,fixture_packed_end-fixture_packed,
                          fixture_tail_scales,fixture_tail_scales_end-fixture_tail_scales)==0,85);
    /* The complete raw image contains zero-filled state, verified from ELF.
     * No runtime reset or prewarm is silently charged to the forward window. */
    const unsigned first_tokens[3]={1,7,19};unsigned saved=0;
    for(unsigned p=0;p<positions;++p) {
        int token=p<3?(int)first_tokens[p]:(int)((p*17+5)%32000);
        errno=12345;__asm__ volatile("csrwi fcsr,0":::"memory");
        consumer_report[7]=p;
        consumer_times[p][0]=cycle();consumer_times[p][1]=instret();
        float *logits=r2_consumer_forward(&consumer_state,(enum r2_consumer_method)method,token,(int)p);
        consumer_times[p][2]=instret();consumer_times[p][3]=cycle();
        consumer_flags[p]=fcsr();
        check(logits==consumer_state.logits && errno==12345 && fcsr()>>5==0,86);tls_check();
        if(negative && p==0) {
            uint32_t value;memcpy(&value,&consumer_state.logits[31999],4);value^=1;
            memcpy(&consumer_state.logits[31999],&value,4);
        }
        if(snapshots && saved<6 && p==selected_positions[saved]) {
            memcpy(consumer_snapshots[saved],&consumer_state,sizeof(consumer_state));++saved;
        }
        consumer_report[8]=p+1;consumer_report[9]=saved;
        if(negative)stop(94);
    }
    consumer_report[3]=0;return 0;
}
