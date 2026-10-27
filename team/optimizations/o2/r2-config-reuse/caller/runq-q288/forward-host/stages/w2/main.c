#include <am.h>
#include <klib.h>
#include <stdint.h>
#include "w2.h"
extern const int8_t w2_input[768],w2_weight[221184],w2_packed[221184];
extern const float w2_input_scales[24],w2_scales[6912],w2_gold[288];
extern const struct w2_slot w2_slot_gold[8];
/* The unchanged upstream matmul reads the model's global group size. */
extern int GS;
/* negative, UART; only these data words differ between actual runs. */
volatile uint32_t w2_control[2] __attribute__((section(".data"),used))={0,1};
unsigned char team_tls_area[96] __attribute__((aligned(16)));
volatile uint64_t w2_report[64],w2_samples[9][8];
static struct {uint64_t before[2];float data[288];uint64_t after[2];} output __attribute__((aligned(64)));
static struct {uint64_t before[2];struct w2_slot data[8];uint64_t after[2];} slots __attribute__((aligned(64)));
static unsigned sample,method,uart,negative;
#define GUARD UINT64_C(0x5a1d8c2976e340bf)
__attribute__((noreturn)) static void reject(const char *name,unsigned byte) {
    w2_report[3]=91;w2_report[8]=sample;w2_report[9]=byte;
    if(uart)printf("W2_REJECT sample=%u method=%u name=%s byte=%u\n",sample,method,name,byte);
    __asm__ volatile("li a0,91\n.word 0x0005006b":::"a0","memory");for(;;){}
}
static void check(int ok,const char *name) {if(!ok)reject(name,0);}
static unsigned fcsr(void) {unsigned x;__asm__ volatile("csrr %0,fcsr":"=r"(x)::"memory");return x;}
static uint64_t cycle(void) {uint64_t x;__asm__ volatile("fence iorw,iorw\nrdcycle %0\nfence iorw,iorw":"=r"(x)::"memory");return x;}
static uint64_t instret(void) {uint64_t x;__asm__ volatile("fence iorw,iorw\nrdinstret %0\nfence iorw,iorw":"=r"(x)::"memory");return x;}
static uint64_t digest(const void *data,unsigned size) {
    const unsigned char *p=data;uint64_t h=UINT64_C(14695981039346656037);
    for(unsigned i=0;i<size;++i)h=(h^p[i])*UINT64_C(1099511628211);
    return h;
}
static void restore(void) {
    memset(output.data,0xa5,sizeof(output.data));memset(slots.data,0xa5,sizeof(slots.data));
    __asm__ volatile("vsetivli zero,8,e8,m1,tu,mu\ncsrwi vstart,0\ncsrwi vcsr,7\ncsrwi fcsr,0":::"memory");
}
static void compare(void) {
    const unsigned char *a=(const unsigned char*)output.data,*b=(const unsigned char*)w2_gold;
    for(unsigned i=0;i<sizeof(output.data);++i)if(a[i]!=b[i])reject("result",i);
    a=(const unsigned char*)slots.data;b=(const unsigned char*)w2_slot_gold;
    for(unsigned i=0;i<sizeof(slots.data);++i)if(a[i]!=(method?b[i]:0xa5))reject("slot",i);
    for(unsigned i=0;i<2;++i)check(output.before[i]==GUARD && output.after[i]==GUARD && slots.before[i]==GUARD && slots.after[i]==GUARD,"guard");
    uintptr_t vl,vt,vs,vc;__asm__ volatile("csrr %0,vl\ncsrr %1,vtype\ncsrr %2,vstart\ncsrr %3,vcsr":"=r"(vl),"=r"(vt),"=r"(vs),"=r"(vc));
    check(vl==8 && vt==0 && vs==0 && vc==7,"csr");
}
__attribute__((noinline,noclone)) static void apply(unsigned which) {
    if(!which){w2_scalar(output.data,w2_weight,w2_scales,w2_input,w2_input_scales);return;}
    struct w2_context c={w2_packed,w2_input,w2_scales,w2_input_scales,output.data,slots.data,0};
    void (*entry)(struct w2_context*)=which==1?q768_fr:q768_ta;entry(&c);
}
int team_forward_main(const char *args) {
    (void)args;GS=32;negative=w2_control[0];uart=w2_control[1];
    w2_report[0]=UINT64_C(0x5232573254473031);w2_report[1]=1;w2_report[2]=negative;w2_report[3]=1;w2_report[4]=uart;
    uintptr_t enable=0x2200,status,vlenb;__asm__ volatile("csrs mstatus,%2\ncsrr %0,mstatus\ncsrr %1,vlenb":"=r"(status),"=r"(vlenb):"r"(enable):"memory");
    check((status&0x6000) && (status&0x600) && vlenb==16 && negative<=1 && uart<=1,"initial");
    w2_report[10]=status;w2_report[11]=vlenb;
    for(unsigned i=0;i<2;++i)output.before[i]=output.after[i]=slots.before[i]=slots.after[i]=GUARD;
    if(uart)printf("W2_BEGIN position=2 layer=5 rows=288 k=768 control=%u\n",negative);
    const unsigned order[9]={0,1,2,2,1,2,1,1,2};
    for(sample=0;sample<(negative?1u:9u);++sample) {
        method=negative?2:order[sample];
        restore();apply(method);compare();check(fcsr()==1,"warm_flags");++w2_report[5];
        restore();uint64_t c0=cycle(),i0=instret();apply(method);uint64_t i1=instret(),c1=cycle();unsigned flags=fcsr();
        if(negative)((unsigned char*)output.data)[287*4]^=1;
        compare();check(flags==1,"flags");
        check(c1>c0 && i1>i0 && c1-c0<UINT32_MAX && i1-i0<UINT32_MAX,"counter");
        uint64_t hash=digest(output.data,sizeof(output.data));
        w2_samples[sample][0]=method;w2_samples[sample][1]=c0;w2_samples[sample][2]=i0;w2_samples[sample][3]=i1;
        w2_samples[sample][4]=c1;w2_samples[sample][5]=flags;w2_samples[sample][6]=hash;++w2_report[6];
        if(uart)printf("W2_SAMPLE %u %u %u %u %u %08x%08x\n",sample,method,(unsigned)(c1-c0),(unsigned)(i1-i0),flags,(unsigned)(hash>>32),(unsigned)hash);
    }
    w2_report[3]=0;if(uart)printf("W2_PASS samples=9 full_comparisons=18\n");return 0;
}
