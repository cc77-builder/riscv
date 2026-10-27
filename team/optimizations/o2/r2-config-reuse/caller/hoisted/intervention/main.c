#include "caller.h"
#include "gemv.h"
#include "data.h"
extern void _putc(char);
extern void caller_measure_0(struct caller_context *, struct caller_measurement *);
extern void caller_measure_1(struct caller_context *, struct caller_measurement *);
extern void caller_measure_2(struct caller_context *, struct caller_measurement *);
extern void caller_measure_3(struct caller_context *, struct caller_measurement *);
struct guarded_a { uint64_t head[2]; int8_t value[256]; uint64_t tail[2]; };
struct guarded_x { uint64_t head[2]; int8_t value[32]; uint64_t tail[2]; };
struct guarded_y { uint64_t head[2]; int32_t value[8]; uint64_t tail[2]; };
struct guarded_a caller_a __attribute__((aligned(16)));
struct guarded_x caller_x __attribute__((aligned(16)));
struct guarded_y caller_y __attribute__((aligned(16)));
struct caller_workspace caller_workspace;
struct caller_context caller_context;
struct caller_measurement caller_measurement;
static const uint64_t guard = UINT64_C(0xd15ea5e5cafebabe);
static void text(const char *s) { while (*s) _putc(*s++); }
static void number(uint64_t v) {
    char b[21]; unsigned n=0;
    do { b[n++]=(char)('0'+v%10); v/=10; } while (v);
    while (n) _putc(b[--n]);
}
static void fill(void *ptr, unsigned n, unsigned char v) {
    unsigned char *p=ptr; while(n--) *p++=v;
}
static int32_t expected(unsigned d, unsigned r) {
    int32_t y=0;
    for (unsigned k=0;k<32;++k) y+=(int32_t)caller_inputs[d][r*32+k]*caller_inputs[d][256+k];
    return y;
}
static __attribute__((noinline,noclone)) void initialize(caller_leaf entry) {
    const unsigned dataset=0, stage=0;
    fill(&caller_workspace,sizeof(caller_workspace),0xa6);
    fill(caller_y.value,sizeof(caller_y.value),0xa6);
    for(unsigned i=0;i<256;++i) caller_a.value[i]=caller_inputs[dataset][i];
    for(unsigned i=0;i<32;++i) caller_x.value[i]=caller_inputs[dataset][256+i];
    for(unsigned i=0;i<2;++i) {
        caller_a.head[i]=caller_a.tail[i]=caller_x.head[i]=caller_x.tail[i]=guard;
        caller_y.head[i]=caller_y.tail[i]=guard;
        caller_workspace.head[i]=caller_workspace.middle[i]=caller_workspace.tail[i]=guard;
    }
    caller_context=(struct caller_context){caller_a.value,caller_x.value,caller_y.value,&caller_workspace,
        entry};
    if(stage==2) for(unsigned i=0;i<288;++i) caller_workspace.packed[i]=caller_inputs[dataset][i];
    if(stage==3) for(unsigned r=0;r<8;++r) {
        caller_workspace.slots[r].value=expected(dataset,r);
        for(unsigned i=0;i<3;++i) caller_workspace.slots[r].high[i]=0;
    }
    __asm__ volatile("csrwi vstart,0; csrwi vcsr,7; vsetivli zero,8,e8,m1,tu,mu":::"memory");
}
static unsigned judge(unsigned dataset, unsigned stage) {
    for(unsigned i=0;i<2;++i) {
        if(caller_a.head[i]!=guard || caller_a.tail[i]!=guard || caller_x.head[i]!=guard || caller_x.tail[i]!=guard ||
           caller_y.head[i]!=guard || caller_y.tail[i]!=guard || caller_workspace.head[i]!=guard ||
           caller_workspace.middle[i]!=guard || caller_workspace.tail[i]!=guard) return 1;
    }
    for(unsigned i=0;i<256;++i) if(caller_a.value[i]!=caller_inputs[dataset][i]) return 2;
    for(unsigned i=0;i<32;++i) if(caller_x.value[i]!=caller_inputs[dataset][256+i]) return 3;
    for(unsigned i=0;i<288;++i) if((unsigned char)caller_workspace.packed[i] !=
        (stage==3 ? 0xa6 : (unsigned char)caller_inputs[dataset][i])) return 4;
    for(unsigned r=0;r<8;++r) {
        if(stage==0 || stage==3) {
            if(caller_y.value[r]!=expected(dataset,r)) return 5;
        } else if((uint32_t)caller_y.value[r]!=UINT32_C(0xa6a6a6a6)) return 6;
        if(stage==1) {
            const unsigned char *p=(const unsigned char *)&caller_workspace.slots[r];
            for(unsigned i=0;i<16;++i) if(p[i]!=0xa6) return 7;
        } else {
            if(caller_workspace.slots[r].value!=expected(dataset,r)) return 8;
            for(unsigned i=0;i<3;++i) if(caller_workspace.slots[r].high[i]) return 9;
        }
    }
    uint64_t vl,vt,vs,vc;
    __asm__ volatile("csrr %0,vl; csrr %1,vtype; csrr %2,vstart; csrr %3,vcsr"
        :"=r"(vl),"=r"(vt),"=r"(vs),"=r"(vc));
    return vl!=8 || vt!=0 || vs!=0 || vc!=7 ? 10 : 0;
}
static unsigned controls(void) {
    unsigned n=0;
    caller_y.value[0]^=1; n+=judge(0,0)!=0; caller_y.value[0]^=1;
    caller_workspace.slots[0].high[2]^=0x10; n+=judge(0,0)!=0; caller_workspace.slots[0].high[2]^=0x10;
    caller_workspace.packed[0]^=1; n+=judge(0,0)!=0; caller_workspace.packed[0]^=1;
    caller_a.value[0]^=1; n+=judge(0,0)!=0; caller_a.value[0]^=1;
    caller_workspace.middle[0]^=1; n+=judge(0,0)!=0; caller_workspace.middle[0]^=1;
    caller_y.tail[1]^=1; n+=judge(0,0)!=0; caller_y.tail[1]^=1;
    return n;
}
/* One successful path for both arms; no output between the windows. */
struct captured { struct caller_measurement value; unsigned verdict; };
static struct captured captures[CALLER_WINDOWS];
static __attribute__((noinline,noclone)) void take(caller_leaf entry, struct captured *out) {
    initialize(entry);
    caller_measure_0(&caller_context,&caller_measurement);
    out->verdict=judge(0,0);
    out->value=caller_measurement;
}
int main(void) {
    __asm__ volatile("csrs mstatus,%0"::"r"((uint64_t)0x600):"memory");
    for(unsigned trial=0;trial<CONTEXT_TRIALS;++trial) {
        unsigned arm=context_order[trial];
        if(arm>1) return 11;
        take(context_predecessors[arm],&captures[2*trial]);
        take(context_target[0],&captures[2*trial+1]);
    }
    unsigned detected=controls();
    unsigned restored=judge(0,0);
    text("CI_BEGIN contract=" CALLER_CONTRACT " trials=");number(CONTEXT_TRIALS);
    text(" windows=");number(CALLER_WINDOWS);_putc('\n');
    unsigned failures=0;
    for(unsigned seq=0;seq<CALLER_WINDOWS;++seq) {
        text("CW ");number(seq);_putc(' ');number(captures[seq].value.cycles);
        _putc(' ');number(captures[seq].value.instructions);_putc(' ');number(captures[seq].verdict);_putc('\n');
        failures+=captures[seq].verdict!=0;
    }
    text("CI_CONTROLS detected=");number(detected);text(" expected=6 restored=");number(restored);_putc('\n');
    failures+=detected!=6 || restored!=0;
    text("CI_END windows=");number(CALLER_WINDOWS);text(" failures=");number(failures);_putc('\n');
    return failures ? 12 : 0;
}
