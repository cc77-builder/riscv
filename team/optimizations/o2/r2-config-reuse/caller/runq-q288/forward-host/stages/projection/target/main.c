#include <am.h>
#include <klib.h>
#include <stdint.h>
#include "q288.h"
extern void q288_fused_rvv4(struct q288_context *);
extern void q288_tail_vdot(struct q288_context *);
extern const int8_t tile_input_q[2][288],tile_packed[5][82944];
extern const float tile_input_scales[2][9],tile_scales[5][2592],tile_gold[2][768];
volatile uint32_t tile_control __attribute__((section(".data"),used))=0;
static struct {uint64_t before[2];float data[768];uint64_t after[2];} output __attribute__((aligned(64)));
static struct {uint64_t before[2];float data[288];uint64_t after[2];} tail __attribute__((aligned(64)));
static struct {uint64_t before[2];struct caller_slot data[8];uint64_t after[2];} slots __attribute__((aligned(64)));
static unsigned current,sample;
#define GUARD UINT64_C(0x5a1d8c2976e340bf)
static const unsigned rows[2]={320,768},first[2]={0,2},blocks[2]={2,3};
__attribute__((noreturn)) static void reject(const char *name,unsigned byte) {
    printf("TILE_REJECT %u %u %s %u\n",current,sample,name,byte);_halt(91);for(;;){}
}
static void check(int ok,const char *name) {if(!ok)reject(name,0);}
static unsigned fcsr(void) {unsigned x;__asm__ volatile("csrr %0,fcsr":"=r"(x)::"memory");return x;}
static uint64_t cycle(void) {uint64_t x;__asm__ volatile("fence iorw,iorw\nrdcycle %0\nfence iorw,iorw":"=r"(x)::"memory");return x;}
static uint64_t instret(void) {uint64_t x;__asm__ volatile("fence iorw,iorw\nrdinstret %0\nfence iorw,iorw":"=r"(x)::"memory");return x;}
static uint64_t digest(const void *data,unsigned bytes) {
    const unsigned char *p=data;uint64_t hash=UINT64_C(14695981039346656037);
    for(unsigned i=0;i<bytes;++i)hash=(hash^p[i])*UINT64_C(1099511628211);
    return hash;
}
static void restore(void) {
    memset(output.data,0xa5,sizeof(output.data));memset(tail.data,0xa5,sizeof(tail.data));memset(slots.data,0xa5,sizeof(slots.data));
}
static void compare(void) {
    const unsigned char *a=(const unsigned char*)output.data,*b=(const unsigned char*)tile_gold[current];
    for(unsigned i=0;i<rows[current]*4;++i)if(a[i]!=b[i])reject("result",i);
    for(unsigned i=rows[current]*4;i<sizeof(output.data);++i)if(a[i]!=0xa5)reject("unused_output",i);
    unsigned valid=rows[current]-(blocks[current]-1)*288;
    const unsigned char *t=(const unsigned char*)tail.data;
    for(unsigned i=valid*4;i<sizeof(tail.data);++i)if(t[i])reject("pad",i);
    for(unsigned i=0;i<sizeof(slots.data);++i)if(((const unsigned char*)slots.data)[i])reject("slot",i);
    for(unsigned i=0;i<2;++i)check(output.before[i]==GUARD && output.after[i]==GUARD && tail.before[i]==GUARD &&
        tail.after[i]==GUARD && slots.before[i]==GUARD && slots.after[i]==GUARD,"guard");
    uintptr_t vl,vt,vs,vc;__asm__ volatile("csrr %0,vl\ncsrr %1,vtype\ncsrr %2,vstart\ncsrr %3,vcsr":"=r"(vl),"=r"(vt),"=r"(vs),"=r"(vc));
    check(vl==8 && vt==0 && vs==0 && vc==7,"csr");
}
__attribute__((noinline,noclone)) static void apply(unsigned c,void (*entry)(struct q288_context *)) {
    for(unsigned block=0;block<blocks[c];++block) {
        unsigned row=block*288,valid=rows[c]-row;if(valid>288)valid=288;
        struct q288_context ctx={tile_packed[first[c]+block],tile_input_q[c],tile_scales[first[c]+block],
            tile_input_scales[c],valid<288?tail.data:output.data+row,slots.data,0};
        entry(&ctx);
        if(valid<288)memcpy(output.data+row,tail.data,valid*4);
    }
}
int main(const char *args) {
    (void)args;uintptr_t enable=0x2200,status,vlenb;__asm__ volatile("csrs mstatus,%2\ncsrr %0,mstatus\ncsrr %1,vlenb":"=r"(status),"=r"(vlenb):"r"(enable):"memory");
    check((status&0x6000) && (status&0x600) && vlenb==16 && tile_control<=1,"initial");
    for(unsigned i=0;i<2;++i)output.before[i]=output.after[i]=tail.before[i]=tail.after[i]=slots.before[i]=slots.after[i]=GUARD;
    printf("TILE_BEGIN position=2 cases=2 rows=320,768 q_calls=40 control=%u\n",tile_control);
    const unsigned order[4]={0,1,1,0};
    for(current=0;current<2;++current) {
        unsigned flags[4];
        for(sample=0;sample<4;++sample) {
            void (*entry)(struct q288_context*)=order[sample]?q288_tail_vdot:q288_fused_rvv4;
            restore();__asm__ volatile("csrwi fcsr,0":::"memory");apply(current,entry);compare();check(fcsr()==1,"warm_flags");
            restore();__asm__ volatile("csrwi fcsr,0":::"memory");
            uint64_t c0=cycle(),i0=instret();apply(current,entry);uint64_t i1=instret(),c1=cycle();unsigned value=fcsr();flags[sample]=value;
            if(tile_control==1 && current==0 && sample==1)((unsigned char*)output.data)[319*4]^=1;
            compare();check(value==1,"flags");uint64_t hash=digest(output.data,rows[current]*4);
            check(c1>c0 && i1>i0 && c1-c0<UINT32_MAX && i1-i0<UINT32_MAX,"counter");
            printf("TILE_SAMPLE %u %u %u %u %u %u %u %08x%08x\n",current,sample,order[sample],rows[current],
                (unsigned)(c1-c0),(unsigned)(i1-i0),value,(unsigned)(hash>>32),(unsigned)hash);
        }
        check(flags[0]==flags[1] && flags[0]==flags[2] && flags[0]==flags[3],"flags_equal");
    }
    printf("TILE_PASS samples=8 full_comparisons=16 q_calls=40\n");return 0;
}
