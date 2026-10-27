/* Full forward measurement; all validation/UART are outside the pure call. */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <klib.h>
#include "consumer.h"
extern unsigned char fixture_weights[],fixture_weights_end[],fixture_embedding[],fixture_embedding_end[];
extern unsigned char fixture_packed[],fixture_packed_end[],fixture_tail_scales[],fixture_tail_scales_end[],fixture_gold[];
__thread int errno;
uintptr_t __stack_chk_guard=UINT64_C(0x9157a6c2d384ef09);
unsigned char team_tls_area[96] __attribute__((aligned(16)));
/* FR_CACHE/TA_CACHE, actual application negative, UART enabled. */
volatile uint32_t target_control[3] __attribute__((section(".data"),used))={4,0,1};
volatile uint64_t target_report[64];
struct r2_consumer_state target_state __attribute__((aligned(16)));
static unsigned uart,method,negative;
typedef uint64_t alias_word __attribute__((may_alias));

__attribute__((noreturn)) static void reject(unsigned code,unsigned byte) {
    target_report[3]=code;target_report[9]=byte;
    if(uart)printf("CONSUMER_REJECT code=%u byte=%u\n",code,byte);
    __asm__ volatile("mv a0,%0\n.word 0x0000006b"::"r"((uintptr_t)code):"a0","memory");
    for(;;) {}
}
__attribute__((noreturn)) void __stack_chk_fail(void) {reject(90,0);}
static void check(int ok,unsigned code) {if(!ok)reject(code,0);}
static unsigned fcsr(void) {unsigned value;__asm__ volatile("csrr %0,fcsr":"=r"(value));return value;}
static uint64_t cycle(void) {uint64_t v;__asm__ volatile("fence iorw,iorw\nrdcycle %0\nfence iorw,iorw":"=r"(v)::"memory");return v;}
static uint64_t instret(void) {uint64_t v;__asm__ volatile("fence iorw,iorw\nrdinstret %0\nfence iorw,iorw":"=r"(v)::"memory");return v;}
static void tls_check(void) {
    uintptr_t tp,address;__asm__ volatile("mv %0,tp":"=r"(tp));
    __asm__ volatile("mv %0,%1":"=r"(address):"r"(&errno));
    check(tp==(uintptr_t)(team_tls_area+16) && address==tp+FULL_ERRNO_OFFSET,80);
    for(unsigned i=0;i<16;++i)check(team_tls_area[i]==0x6b && team_tls_area[80+i]==0xa7,81);
}
static void complete_compare(void) {
    _Static_assert(R2_CONSUMER_STATE_BYTES%8==0,"complete word comparison");
    const alias_word *actual=(const alias_word*)&target_state,*gold=(const alias_word*)fixture_gold;
    for(unsigned i=0;i<R2_CONSUMER_STATE_BYTES/8;++i)if(actual[i]!=gold[i]) {
        const unsigned char *a=(const unsigned char*)&target_state;
        for(unsigned j=i*8;j<i*8+8;++j)if(a[j]!=fixture_gold[j])reject(94,j);
        reject(95,i*8);
    }
    target_report[8]=R2_CONSUMER_STATE_BYTES;
}
int team_forward_main(void) {
    method=target_control[0];negative=target_control[1];uart=target_control[2];
    target_report[0]=UINT64_C(0x5232435447543031);target_report[1]=1;target_report[2]=method;target_report[3]=1;
    target_report[4]=1;target_report[5]=negative;target_report[6]=uart;
    check((method==R2_FR_CACHE || method==R2_TA_CACHE) && negative<=1 && uart<=1,82);
    uintptr_t status,vlenb;__asm__ volatile("csrr %0,mstatus\ncsrr %1,vlenb":"=r"(status),"=r"(vlenb));
    check((status&0x6000)!=0 && (status&0x600)!=0 && vlenb==16 && errno==0,83);
    target_report[10]=status;target_report[11]=vlenb;
    for(unsigned i=0;i<16;++i){team_tls_area[i]=0x6b;team_tls_area[80+i]=0xa7;}tls_check();
    check(r2_consumer_init(fixture_weights,fixture_weights_end-fixture_weights,
        fixture_embedding,fixture_embedding_end-fixture_embedding,fixture_packed,fixture_packed_end-fixture_packed,
        fixture_tail_scales,fixture_tail_scales_end-fixture_tail_scales)==0,84);
    if(uart)printf("CONSUMER_BEGIN method=%u token=1 position=0 negative=%u\n",method,negative);
    errno=12345;__asm__ volatile("csrwi fcsr,0":::"memory");
    uint64_t c0=cycle(),i0=instret();
    float *logits=r2_consumer_forward(&target_state,(enum r2_consumer_method)method,1,0);
    uint64_t i1=instret(),c1=cycle();unsigned flags=fcsr();
    target_report[16]=c0;target_report[17]=i0;target_report[18]=i1;target_report[19]=c1;target_report[20]=flags;
    check(logits==target_state.logits && errno==12345 && flags>>5==0,85);tls_check();
    check(c1>c0 && i1>i0 && c1-c0<UINT32_MAX && i1-i0<UINT32_MAX,86);target_report[7]=1;
    if(negative)((unsigned char*)&target_state.logits[31999])[0]^=1;
    complete_compare();
    if(uart) {
        printf("CONSUMER_COUNTERS %u %08x%08x %08x%08x %08x%08x %08x%08x\n",method,
            (unsigned)(c0>>32),(unsigned)c0,(unsigned)(i0>>32),(unsigned)i0,
            (unsigned)(i1>>32),(unsigned)i1,(unsigned)(c1>>32),(unsigned)c1);
        printf("CONSUMER_PASS bytes=%u flags=%u\n",R2_CONSUMER_STATE_BYTES,flags);
    }
    target_report[3]=0;return 0;
}
