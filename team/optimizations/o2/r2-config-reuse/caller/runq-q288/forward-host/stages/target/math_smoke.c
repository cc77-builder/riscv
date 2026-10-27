#include <am.h>
#include <klib.h>
#include <stdint.h>
#include "math_eval.h"
#include "math_inputs.h"
#include "math_expected.h"

__thread int errno;
uintptr_t __stack_chk_guard = UINT64_C(0x9157a6c2d384ef09);
unsigned char team_tls_area[96] __attribute__((aligned(16)));
volatile uint32_t math_control __attribute__((section(".data"),used)) = 0;
extern void team_guard_control(void);

__attribute__((noreturn)) void __stack_chk_fail(void) {
    printf("MATH_STACK_GUARD_REJECT\n");
    _halt(90);
    for(;;) {}
}
static void check(int good,const char *label,unsigned index) {
    if (!good) { printf("MATH_REJECT %u %s\n",index,label);_halt(89); }
}
static uintptr_t tp_value(void) { uintptr_t tp;__asm__ volatile("mv %0, tp":"=r"(tp));return tp; }
static unsigned fcsr_value(void) { unsigned value;__asm__ volatile("csrr %0, fcsr":"=r"(value));return value; }
static int nan32(uint64_t value) { return value<=UINT32_MAX && (value&0x7f800000)==0x7f800000 && (value&0x7fffff)!=0; }
static void guards(unsigned index) {
    check(tp_value()==(uintptr_t)(team_tls_area+16),"tp",index);
    for(unsigned i=0;i<16;++i)check(team_tls_area[i]==0x6b && team_tls_area[80+i]==0xa7,"tls_guard",index);
}

int team_math_main(void) {
    uintptr_t tp=tp_value(),address=(uintptr_t)&errno;
    check(tp==(uintptr_t)(team_tls_area+16) && (tp&15)==0,"tls_storage",0);
    check(address>=tp && address+sizeof(errno)<=tp+64 && (address&3)==0,"errno_address",0);
    check(errno==0,"tls_zero",0);
    for(unsigned i=0;i<16;++i) {team_tls_area[i]=0x6b;team_tls_area[80+i]=0xa7;}
    printf("MATH_BEGIN cases=%u tls_offset=%u control=%u\n",MATH_CASES,(unsigned)(address-tp),math_control);
    if(math_control==2) {team_guard_control();check(0,"guard_returned",0);}
    for(unsigned i=0;i<MATH_CASES;++i) {
        uint64_t out[2];errno=MATH_ERRNO_SENTINEL;
        __asm__ volatile("csrwi fcsr, 0" ::: "memory");
        math_evaluate(&math_inputs[i],out);
        unsigned fcsr=fcsr_value();int error=errno;
        printf("MATH_VALUE %u %u %08x%08x %08x%08x %d %u\n",i,math_inputs[i].kind,
               (unsigned)(out[0]>>32),(unsigned)out[0],(unsigned)(out[1]>>32),(unsigned)out[1],error,fcsr);
        uint64_t wanted[2]={math_expected[i].first,math_expected[i].second};
        if(math_control==1 && i==0)wanted[0]^=1;
        for(unsigned part=0;part<2;++part)
            check(math_inputs[i].nan_mask&(1u<<part) ? nan32(out[part]) : out[part]==wanted[part],"result",i);
        check(error==math_expected[i].error,"errno",i);
        check((fcsr>>5)==0 && (fcsr&math_inputs[i].required_fflags)==math_inputs[i].required_fflags &&
              !(fcsr&~math_inputs[i].allowed_fflags),"fcsr",i);
        guards(i);
    }
    printf("MATH_PASS cases=%u errors_checked=8 guard_checks=%u\n",MATH_CASES,MATH_CASES);
    return 0;
}
