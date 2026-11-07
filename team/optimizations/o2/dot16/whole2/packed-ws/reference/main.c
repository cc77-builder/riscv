/* Team-only fixed-geometry screening harness; authoritative oracles are copied unchanged. */
#include <am.h>
#include <klib.h>
#include <stdint.h>
#include <stddef.h>
#include "packed_ws.h"

#if SCREEN_K == 288
#include "q288.h"
typedef struct q288_context RowContext;
typedef struct caller_slot RowSlot;
typedef struct q288_packed_ws_context PackedContext;
typedef struct q288_packed_ws_scales PackedScales;
#define ROW_P q288_paired16_rvv
#define ROW_N q288_dot16_whole8_narrow
#define PACK_P q288_paired16_rvv_packed_ws
#define PACK_N q288_dot16_whole8_narrow_packed_ws
#define PREPARE q288_prepare_packed_ws
#elif SCREEN_K == 768
#include "w2.h"
typedef struct w2_context RowContext;
typedef struct w2_slot RowSlot;
typedef struct q768_packed_ws_context PackedContext;
typedef struct q768_packed_ws_scales PackedScales;
#define ROW_P q768_paired16_rvv
#define ROW_N q768_dot16_whole8_narrow
#define PACK_P q768_paired16_rvv_packed_ws
#define PACK_N q768_dot16_whole8_narrow_packed_ws
#define PREPARE q768_prepare_packed_ws
extern int GS;
#else
#error SCREEN_K must be exactly 288 or 768
#endif

#define GROUPS (SCREEN_K/32)
#define SCALE_BYTES (288*GROUPS*4)
#define GUARD UINT64_C(0x5a1d8c2976e340bf)
void ROW_P(RowContext *);
void ROW_N(RowContext *);
extern const int8_t w2_input[SCREEN_K],w2_weight[288*SCREEN_K],w2_packed[288*SCREEN_K];
extern const float w2_input_scales[GROUPS],w2_scales[288*GROUPS],w2_gold[288];
extern const unsigned char w2_slot_gold[128],w2_packed_scales[SCALE_BYTES];
extern const uint32_t w2_expected_flags[1];

/* Negative/UART are the only per-case control words. Geometry is compile-time fixed. */
volatile uint32_t w2_control[2] __attribute__((section(".data"),used))={0,1};
unsigned char team_tls_area[96] __attribute__((aligned(16)));
volatile uint64_t w2_report[64],w2_samples[8][8];
static struct {uint64_t before[2];float data[288];uint64_t after[2];} output __attribute__((aligned(64)));
static struct {uint64_t before[2];RowSlot data[8];uint64_t after[2];} slots __attribute__((aligned(64)));
static struct {uint64_t before[2];struct packed_ws_slot data[8];uint64_t after[2];} packed_slots __attribute__((aligned(64)));
struct prepared_object {uint64_t before[8];PackedScales data;uint64_t after[8];};
static struct prepared_object prepared __attribute__((aligned(64)));
_Static_assert(sizeof(output)==1184 && sizeof(slots)==160 && sizeof(packed_slots)==160,"complete guarded outputs");
_Static_assert(offsetof(struct prepared_object,data)==64,"prepared payload alignment");
_Static_assert(offsetof(struct prepared_object,after)==64+SCALE_BYTES,"prepared tail offset");
_Static_assert(sizeof(struct prepared_object)==SCALE_BYTES+128,"complete guarded scale object");
static unsigned sample,method,uart,negative;

__attribute__((noreturn)) static void reject(const char *name,unsigned byte) {
    w2_report[3]=91;w2_report[8]=sample;w2_report[9]=byte;
    if(uart)printf("PWS_REJECT k=%u sample=%u method=%u name=%s byte=%u\n",SCREEN_K,sample,method,name,byte);
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
static void prepared_equal(void) {
    const unsigned char *a=(const unsigned char*)&prepared.data;
    for(unsigned i=0;i<SCALE_BYTES;++i)if(a[i]!=w2_packed_scales[i])reject("prepared",i);
    for(unsigned i=0;i<8;++i)check(prepared.before[i]==GUARD && prepared.after[i]==GUARD,"prepared_guard");
}
static void restore(void) {
    memset(output.data,0xa5,sizeof(output.data));
    memset(slots.data,0xa5,sizeof(slots.data));
    memset(packed_slots.data,0xa5,sizeof(packed_slots.data));
    __asm__ volatile("vsetivli zero,8,e8,m1,tu,mu\ncsrwi vstart,0\ncsrwi vcsr,7\ncsrwi fcsr,0":::"memory");
}
static void compare(void) {
    const unsigned char *a=(const unsigned char*)output.data,*b=(const unsigned char*)w2_gold;
    for(unsigned i=0;i<sizeof(output.data);++i)if(a[i]!=b[i])reject("result",i);
    a=(const unsigned char*)slots.data;b=w2_slot_gold;
    for(unsigned i=0;i<sizeof(slots.data);++i)if(a[i]!=((method==1 || method==2)?b[i]:0xa5))reject("slot",i);
    a=(const unsigned char*)packed_slots.data;
    for(unsigned i=0;i<sizeof(packed_slots.data);++i)if(a[i]!=(method>=3?b[i]:0xa5))reject("packed_slot",i);
    for(unsigned i=0;i<2;++i)check(output.before[i]==GUARD && output.after[i]==GUARD &&
        slots.before[i]==GUARD && slots.after[i]==GUARD &&
        packed_slots.before[i]==GUARD && packed_slots.after[i]==GUARD,"guard");
    for(unsigned i=0;i<8;++i)check(prepared.before[i]==GUARD && prepared.after[i]==GUARD,"prepared_guard");
    uintptr_t vl,vt,vs,vc;__asm__ volatile("csrr %0,vl\ncsrr %1,vtype\ncsrr %2,vstart\ncsrr %3,vcsr":"=r"(vl),"=r"(vt),"=r"(vs),"=r"(vc));
    check(vl==8 && vt==0 && vs==0 && vc==7,"csr");
}
__attribute__((noinline,noclone)) static void apply(unsigned which) {
    if(!which) {
#if SCREEN_K == 288
        q288_oracle(output.data,w2_input,w2_input_scales,w2_weight,w2_scales);
#else
        w2_scalar(output.data,w2_weight,w2_scales,w2_input,w2_input_scales);
#endif
        return;
    }
    if(which<=2) {
        RowContext c={w2_packed,w2_input,w2_scales,w2_input_scales,output.data,slots.data,0};
        if(which==1)ROW_P(&c);else ROW_N(&c);
    } else {
        PackedContext c={w2_packed,w2_input,&prepared.data,w2_input_scales,output.data,packed_slots.data,0};
        if(which==3)PACK_P(&c);else PACK_N(&c);
    }
}
int team_forward_main(const char *args) {
    (void)args;
#if SCREEN_K == 768
    GS=32;
#endif
    negative=w2_control[0];uart=w2_control[1];
    w2_report[0]=UINT64_C(0x5232573254473031);w2_report[1]=1;w2_report[2]=negative;w2_report[3]=1;w2_report[4]=uart;
    uintptr_t enable=0x2200,status,vlenb;__asm__ volatile("csrs mstatus,%2\ncsrr %0,mstatus\ncsrr %1,vlenb":"=r"(status),"=r"(vlenb):"r"(enable):"memory");
    check((status&0x6000) && (status&0x600) && vlenb==16 && negative<=1 && uart<=1,"initial");
    w2_report[10]=status;w2_report[11]=vlenb;
    for(unsigned i=0;i<2;++i)output.before[i]=output.after[i]=slots.before[i]=slots.after[i]=packed_slots.before[i]=packed_slots.after[i]=GUARD;
    for(unsigned i=0;i<8;++i)prepared.before[i]=prepared.after[i]=GUARD;
    memset(&prepared.data,0xa5,sizeof(prepared.data));
    PREPARE(&prepared.data,w2_scales);prepared_equal();
    if(uart)printf("PWS_BEGIN k=%u rows=288 groups=%u control=%u\n",SCREEN_K,GROUPS,negative);
    const unsigned order[8]={1,2,3,4,4,3,2,1};
    for(sample=0;sample<(negative?1u:8u);++sample) {
        method=negative?2:order[sample];
        restore();apply(method);compare();check(fcsr()==w2_expected_flags[0],"warm_flags");++w2_report[5];
        restore();uint64_t c0=cycle(),i0=instret();apply(method);uint64_t i1=instret(),c1=cycle();unsigned flags=fcsr();
        if(negative)((unsigned char*)output.data)[287*4]^=1;
        compare();check(flags==w2_expected_flags[0],"flags");
        check(c1>c0 && i1>i0 && c1-c0<UINT32_MAX && i1-i0<UINT32_MAX,"counter");
        uint64_t hash=digest(output.data,sizeof(output.data));
        w2_samples[sample][0]=method;w2_samples[sample][1]=c0;w2_samples[sample][2]=i0;w2_samples[sample][3]=i1;
        w2_samples[sample][4]=c1;w2_samples[sample][5]=flags;w2_samples[sample][6]=hash;++w2_report[6];
        if(uart)printf("PWS_SAMPLE %u %u %u %u %u %08x%08x\n",sample,method,(unsigned)(c1-c0),(unsigned)(i1-i0),flags,(unsigned)(hash>>32),(unsigned)hash);
    }
    prepared_equal();
    w2_report[3]=0;if(uart)printf("PWS_PASS k=%u samples=8 full_comparisons=16 prepared_bytes=%u\n",SCREEN_K,SCALE_BYTES);
    return 0;
}
