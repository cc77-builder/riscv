#include <am.h>
#include <klib.h>
#include <stdint.h>
#include "rope.h"
__thread int errno;
uintptr_t __stack_chk_guard=UINT64_C(0x9157a6c2d384ef09);
unsigned char team_tls_area[96] __attribute__((aligned(16)));
volatile uint32_t rope_control __attribute__((section(".data"),used))=0;
extern const struct rope_case rope_before[ROPE_CASES],rope_after[ROPE_CASES];
extern const unsigned rope_positions[ROPE_CASES];
static struct { uint64_t first[2];struct rope_case data;uint64_t last[2]; } work __attribute__((aligned(64)));
static unsigned sample;
__attribute__((noreturn)) static void reject(const char *name,unsigned byte) {
    printf("ROPE_REJECT %u %s %u\n",sample,name,byte);_halt(91);for(;;){}
}
__attribute__((noreturn)) void __stack_chk_fail(void) {reject("stack",0);}
static void check(int ok,const char *name) {if(!ok)reject(name,0);}
static unsigned fcsr(void) {unsigned x;__asm__ volatile("csrr %0,fcsr":"=r"(x)::"memory");return x;}
static uint64_t cycle(void) {uint64_t x;__asm__ volatile("fence rw,rw\nrdcycle %0\nfence rw,rw":"=r"(x)::"memory");return x;}
static uint64_t instret(void) {uint64_t x;__asm__ volatile("fence rw,rw\nrdinstret %0\nfence rw,rw":"=r"(x)::"memory");return x;}
static void guards(void) {
    uintptr_t tp;__asm__ volatile("mv %0,tp":"=r"(tp));
    check(tp==(uintptr_t)(team_tls_area+16) && (uintptr_t)&errno==tp,"tls");
    for(unsigned i=0;i<16;++i)check(team_tls_area[i]==0x6b && team_tls_area[80+i]==0xa7,"tls_guard");
    for(unsigned i=0;i<2;++i)check(work.first[i]==UINT64_C(0x2ae641c3709bd58f) && work.last[i]==UINT64_C(0xc4802ad7b196e35f),"data_guard");
}
static void restore(void) {memcpy(&work.data,&rope_before[ROPE_SELECTED],ROPE_BYTES);}
static void compare(void) {
    const unsigned char *a=(const unsigned char*)&work.data,*b=(const unsigned char*)&rope_after[ROPE_SELECTED];
    for(unsigned i=0;i<ROPE_BYTES;++i)if(a[i]!=b[i])reject("result",i);
}
int team_math_main(void) {
    check(sizeof(work.data)==ROPE_BYTES && errno==0,"initial");
    for(unsigned i=0;i<16;++i){team_tls_area[i]=0x6b;team_tls_area[80+i]=0xa7;}
    for(unsigned i=0;i<2;++i){work.first[i]=UINT64_C(0x2ae641c3709bd58f);work.last[i]=UINT64_C(0xc4802ad7b196e35f);}
    guards();check(rope_positions[ROPE_SELECTED]==2 && rope_control<=1,"identity");
    printf("ROPE_BEGIN cases=6 selected=2 position=2 layers=6 pairs=24 bytes=%u control=%u\n",ROPE_BYTES,rope_control);
    const unsigned order[4]={0,1,1,0};unsigned flags[4];
    for(sample=0;sample<4;++sample) {
        void (*function)(struct rope_case*,int)=order[sample]?rope_cached:rope_original;
        restore();errno=12345;__asm__ volatile("csrwi fcsr,0":::"memory");
        function(&work.data,(int)rope_positions[ROPE_SELECTED]);compare();guards();check(errno==12345,"warm_errno");
        restore();errno=12345;__asm__ volatile("csrwi fcsr,0":::"memory");
        uint64_t c0=cycle(),i0=instret();
        function(&work.data,(int)rope_positions[ROPE_SELECTED]);
        uint64_t i1=instret(),c1=cycle();unsigned value=fcsr();flags[sample]=value;
        if(rope_control==1 && sample==1)((unsigned char*)&work.data)[0]^=1;
        compare();guards();check(errno==12345 && value>>5==0,"environment");
        uint64_t hash=rope_digest(&work.data,ROPE_BYTES),cycles=c1-c0,insns=i1-i0;
        check(cycles>0 && insns>0 && cycles<UINT32_MAX && insns<UINT32_MAX,"counter");
        printf("ROPE_SAMPLE %u %u %u %u %u %08x%08x\n",sample,order[sample],(unsigned)cycles,(unsigned)insns,value,(unsigned)(hash>>32),(unsigned)hash);
    }
    check(flags[0]==flags[1] && flags[0]==flags[2] && flags[0]==flags[3],"flags_equal");
    printf("ROPE_PASS samples=4 full_comparisons=8 bytes=%u\n",ROPE_BYTES);return 0;
}
