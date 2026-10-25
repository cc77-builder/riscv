#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static uint64_t host_csr[4];
#define main split_guest_main
#include "split.h"
#include "data.h"
extern void _putc(char);
/* Assembly bridge: a0 is the typed wrapper's context, a1 the result pointer,
 * a2 the actual function address. C never calls an incompatible function type. */
extern void split_measure(void *, struct caller_measurement *, uintptr_t);

/* Real union members make the aligned word operations valid GNU C11 accesses.
 * Equality of all unsigned 64-bit words is equality of every byte, with no
 * checksum, padding omission, unaligned word access, or pointer type punning. */
union arena_storage { uint64_t words[96]; unsigned char bytes[768]; };
union packed_storage { uint64_t words[36]; int8_t bytes[288]; };
union workspace_storage { struct caller_workspace value; uint64_t words[58]; };
union arena_storage split_arena __attribute__((aligned(16)));
static union arena_storage arena_reference __attribute__((aligned(16)));
static union packed_storage packed_reference __attribute__((aligned(16)));
struct guarded_y { uint64_t head[2]; int32_t value[8]; uint64_t tail[2]; };
struct guarded_y caller_y __attribute__((aligned(16)));
union workspace_storage caller_workspace;
struct caller_context caller_context;
struct split_context split_context;
struct caller_measurement caller_measurement;
struct caller_measurement split_samples[SPLIT_WINDOWS];
static unsigned a_offset, x_offset;
static unsigned prepared_dataset=7, prepared_layout=3;
static int32_t scalar_golden[7][8];
static const uint64_t guard = UINT64_C(0xd15ea5e5cafebabe);
static const uint64_t poison = UINT64_C(0xa6a6a6a6a6a6a6a6);
_Static_assert(sizeof(union arena_storage)==768 && sizeof(union packed_storage)==288,"whole-word reference sizes");
_Static_assert(sizeof(union workspace_storage)==464 && offsetof(struct caller_workspace,packed)==16 &&
    offsetof(struct caller_workspace,slots)==320,"unchanged workspace representation");
_Static_assert(__alignof__(split_arena)>=16 && __alignof__(caller_workspace)>=16,"aligned whole-word buffers");
static void text(const char *s) { while (*s) _putc(*s++); }
static void number(uint64_t v) {
    char b[21]; unsigned n=0;
    do { b[n++]=(char)('0'+v%10); v/=10; } while(v);
    while(n) _putc(b[--n]);
}
static void fill(void *ptr, unsigned n, unsigned char v) {
    unsigned char *p=ptr; while(n--) *p++=v;
}
static int32_t expected(unsigned d, unsigned r) {
    int32_t sum=0;
    for(unsigned k=0;k<32;++k) sum+=(int32_t)split_inputs[d][r*32+k]*split_inputs[d][256+k];
    return sum;
}
static void prepare_reference(unsigned dataset, unsigned layout) {
    if(prepared_dataset==dataset && prepared_layout==layout) return;
    /* Performance uses aligned disjoint X-before-A. Functional layouts also
     * put X after A and deliberately use byte-misaligned input addresses. */
    a_offset=layout==0 ? 96 : layout==1 ? 97 : 39;
    x_offset=layout==0 ? 32 : layout==1 ? 35 : 427;
    for(unsigned i=0;i<96;++i) arena_reference.words[i]=poison;
    for(unsigned i=0;i<288;++i) packed_reference.bytes[i]=split_inputs[dataset][i];
    for(unsigned i=0;i<256;++i) arena_reference.bytes[a_offset+i]=(unsigned char)split_inputs[dataset][i];
    for(unsigned i=0;i<32;++i) arena_reference.bytes[x_offset+i]=(unsigned char)split_inputs[dataset][256+i];
    prepared_dataset=dataset; prepared_layout=layout;
}
static void initialize(unsigned dataset, unsigned choice, unsigned layout) {
    prepare_reference(dataset,layout);
    for(unsigned i=0;i<96;++i) split_arena.words[i]=arena_reference.words[i];
    for(unsigned i=0;i<58;++i) caller_workspace.words[i]=poison;
    fill(caller_y.value,sizeof(caller_y.value),0xa6);
    for(unsigned i=0;i<2;++i) {
        caller_y.head[i]=caller_y.tail[i]=guard;
        caller_workspace.value.head[i]=caller_workspace.value.middle[i]=caller_workspace.value.tail[i]=guard;
    }
    unsigned kind=choice==12 ? 0 : choice%6;
    caller_context=(struct caller_context){(const int8_t *)split_arena.bytes+a_offset,
        (const int8_t *)split_arena.bytes+x_offset,caller_y.value,&caller_workspace.value,packed_entries[kind]};
    split_context=(struct split_context){(const int8_t *)split_arena.bytes+a_offset,
        (const int8_t *)split_arena.bytes+x_offset,caller_y.value,caller_workspace.value.slots,split_entries[kind]};
    host_csr[0]=8; host_csr[1]=0; host_csr[2]=0; host_csr[3]=7;
}
static unsigned judge(unsigned dataset, unsigned mode) {
    for(unsigned i=0;i<96;++i) if(split_arena.words[i]!=arena_reference.words[i]) return 1;
    for(unsigned i=0;i<2;++i) if(caller_y.head[i]!=guard || caller_y.tail[i]!=guard ||
        caller_workspace.value.head[i]!=guard || caller_workspace.value.middle[i]!=guard || caller_workspace.value.tail[i]!=guard) return 2;
    for(unsigned i=0;i<36;++i) if(caller_workspace.words[2+i] !=
        (mode ? poison : packed_reference.words[i])) return 3;
    for(unsigned r=0;r<8;++r) {
        if(caller_y.value[r]!=scalar_golden[dataset][r] || caller_workspace.value.slots[r].value!=scalar_golden[dataset][r]) return 4;
        for(unsigned i=0;i<3;++i) if(caller_workspace.value.slots[r].high[i]) return 5;
    }
    uint64_t vl,vt,vs,vc;
    vl=host_csr[0]; vt=host_csr[1]; vs=host_csr[2]; vc=host_csr[3];
    return vl!=8 || vt!=0 || vs!=0 || vc!=7 ? 6 : 0;
}
static unsigned controls(void) {
    unsigned n=0;
    caller_y.value[0]^=1; n+=judge(0,1)!=0; caller_y.value[0]^=1;
    caller_workspace.value.slots[0].high[2]^=0x10; n+=judge(0,1)!=0; caller_workspace.value.slots[0].high[2]^=0x10;
    caller_workspace.value.packed[0]^=1; n+=judge(0,1)!=0; caller_workspace.value.packed[0]^=1;
    split_arena.bytes[a_offset]^=1; n+=judge(0,1)!=0; split_arena.bytes[a_offset]^=1;
    caller_workspace.value.middle[0]^=1; n+=judge(0,1)!=0; caller_workspace.value.middle[0]^=1;
    split_arena.bytes[0]^=1; n+=judge(0,1)!=0; split_arena.bytes[0]^=1;
    return n;
}
static unsigned measured(unsigned dataset,unsigned choice,unsigned seq) {
    initialize(dataset,10,0); /* Firstdot reuse RVV, identical conditioning. */
    split_full(&split_context);
    if(judge(dataset,1)) return 7;
    initialize(dataset,choice,0);
    if(choice<6) split_measure(&caller_context,&caller_measurement,(uintptr_t)&caller_full);
    else split_measure(&split_context,&caller_measurement,(uintptr_t)&split_full);
    split_samples[seq]=caller_measurement;
    return judge(dataset,choice>=6);
}
int main(void) {
    (void)0;
    /* Independent scalar oracle, computed only from the frozen input table,
     * before any leaf runs. Every call still checks every output and guard. */
    for(unsigned d=0;d<7;++d) for(unsigned r=0;r<8;++r) scalar_golden[d][r]=expected(d,r);
    text("SPLIT_BEGIN contract=" SPLIT_CONTRACT " windows=");number(SPLIT_WINDOWS);_putc('\n');
    unsigned calls=0,detected=0;
    for(unsigned d=0;d<7;++d) for(unsigned layout=1;layout<=2;++layout)
        for(unsigned kind=0;kind<6;++kind) {
            initialize(d,6+kind,layout);
            split_full(&split_context);
            if(judge(d,1)) { text("SPLIT_FAIL functional\n"); return 1; }
            if(calls==0) { detected=controls(); if(detected!=6 || judge(0,1)) return 2; }
            ++calls;
        }
    text("SPLIT_FUNCTIONAL calls=");number(calls);text(" controls=");number(detected);_putc('\n');
    unsigned seq=0;
    for(unsigned d=0;d<3;++d) for(unsigned rep=0;rep<6;++rep) {
        unsigned verdict=measured(d,12,seq++);
        if(verdict) return 3;
        for(unsigned pos=0;pos<12;++pos) {
            unsigned choice=(rep&1) ? 11-pos : pos;
            verdict=measured(d,choice,seq++);
            if(verdict) { text("SPLIT_FAIL measured seq=");number(seq-1);text(" verdict=");number(verdict);_putc('\n');return 4; }
        }
        verdict=measured(d,12,seq++);
        if(verdict) return 5;
    }
    /* No data-dependent decimal conversion or UART traffic between windows. */
    for(unsigned i=0;i<seq;++i) {
        text("SW ");number(i);_putc(' ');number(split_samples[i].cycles);_putc(' ');
        number(split_samples[i].instructions);_putc('\n');
    }
    text("SPLIT_END windows=");number(seq);text(" failures=0\n");
    return seq!=SPLIT_WINDOWS;
}

void config_reuse_gemv_8x32_reuse_vdot(const int8_t *a,void *b){(void)a;(void)b;abort();}
void r4_gemv_8x32_basic_rvv(const int8_t *a,void *b){(void)a;(void)b;abort();}
void r4_gemv_8x32_reuse_rvv(const int8_t *a,void *b){(void)a;(void)b;abort();}
void config_reuse_gemv_8x32_basic_rvv(const int8_t *a,void *b){(void)a;(void)b;abort();}
void firstdot_gemv_8x32_reuse_rvv(const int8_t *a,void *b){(void)a;(void)b;abort();}
void config_reuse_gemv_8x32_reuse_rvv(const int8_t *a,void *b){(void)a;(void)b;abort();}
void split_gemv_8x32_vdot(const int8_t *a,const int8_t *x,struct caller_slot *s){(void)a;(void)x;(void)s;abort();}
void split_gemv_8x32_rvv0(const int8_t *a,const int8_t *x,struct caller_slot *s){(void)a;(void)x;(void)s;abort();}
void split_gemv_8x32_rvv1(const int8_t *a,const int8_t *x,struct caller_slot *s){(void)a;(void)x;(void)s;abort();}
void split_gemv_8x32_rvv2(const int8_t *a,const int8_t *x,struct caller_slot *s){(void)a;(void)x;(void)s;abort();}
void split_gemv_8x32_rvv3(const int8_t *a,const int8_t *x,struct caller_slot *s){(void)a;(void)x;(void)s;abort();}
void split_gemv_8x32_rvv4(const int8_t *a,const int8_t *x,struct caller_slot *s){(void)a;(void)x;(void)s;abort();}
void _putc(char c){(void)c;abort();}
void split_measure(void *c,struct caller_measurement *m,uintptr_t f){(void)c;(void)m;(void)f;abort();}
void caller_full(struct caller_context *c){(void)c;abort();}
void split_full(struct split_context *c){(void)c;abort();}

#undef main
static void must(int ok,unsigned line) {
    if(!ok) { fprintf(stderr,"HARNESS_REJECT line=%u\n",line); exit(1); }
}
#define CHECK(x) must((x),__LINE__)
int main(void) {
    unsigned cases=0,byte_faults=0,csr_faults=0,original_controls=0;
    const unsigned aa[3]={96,97,39},xx[3]={32,35,427};
    for(unsigned d=0;d<7;++d) for(unsigned r=0;r<8;++r) scalar_golden[d][r]=expected(d,r);
    for(unsigned d=0;d<7;++d) for(unsigned l=0;l<3;++l) for(unsigned mode=0;mode<2;++mode) {
        initialize(d,mode?6:0,l);
        CHECK(a_offset==aa[l] && x_offset==xx[l]);
        CHECK(caller_context.a==(int8_t *)split_arena.bytes+aa[l] && caller_context.x==(int8_t *)split_arena.bytes+xx[l]);
        CHECK(caller_context.workspace==&caller_workspace.value && split_context.slots==caller_workspace.value.slots);
        CHECK(split_context.a==caller_context.a && split_context.x==caller_context.x);
        CHECK(caller_context.y==caller_y.value && split_context.y==caller_y.value);
        CHECK(caller_context.entry==packed_entries[0] && split_context.entry==split_entries[0]);
        for(unsigned i=0;i<768;++i) {
            unsigned char want=0xa6;
            if(i>=aa[l] && i<aa[l]+256) want=(unsigned char)split_inputs[d][i-aa[l]];
            if(i>=xx[l] && i<xx[l]+32) want=(unsigned char)split_inputs[d][256+i-xx[l]];
            CHECK(split_arena.bytes[i]==want);
        }
        for(unsigned i=0;i<464;++i) {
            unsigned char want=0xa6;
            if(i<16 || (i>=304 && i<320) || i>=448) want=((const unsigned char *)&guard)[i%8];
            CHECK(((unsigned char *)&caller_workspace)[i]==want);
        }
        for(unsigned i=0;i<64;++i) {
            unsigned char want=(i<16 || i>=48)?((const unsigned char *)&guard)[i%8]:0xa6;
            CHECK(((unsigned char *)&caller_y)[i]==want);
        }
        /* Populate a correct result independently; no candidate implementation
         * is run or substituted for a claimed ISA/functional result. */
        for(unsigned r=0;r<8;++r) {
            int64_t sum=0;
            for(unsigned k=0;k<32;++k) sum+=(int64_t)split_inputs[d][r*32+k]*(int64_t)split_inputs[d][256+k];
            CHECK(scalar_golden[d][r]==sum);
            caller_y.value[r]=caller_workspace.value.slots[r].value=(int32_t)sum;
            for(unsigned k=0;k<3;++k) caller_workspace.value.slots[r].high[k]=0;
        }
        if(!mode) for(unsigned i=0;i<288;++i) caller_workspace.value.packed[i]=split_inputs[d][i];
        CHECK(judge(d,mode)==0);
        unsigned char *regions[3]={split_arena.bytes,(unsigned char *)&caller_workspace,(unsigned char *)&caller_y};
        const unsigned sizes[3]={768,464,64};
        for(unsigned region=0;region<3;++region) for(unsigned i=0;i<sizes[region];++i) {
            regions[region][i]^=1; CHECK(judge(d,mode)!=0);
            regions[region][i]^=1; CHECK(judge(d,mode)==0); ++byte_faults;
        }
        for(unsigned i=0;i<4;++i) {
            host_csr[i]^=1; CHECK(judge(d,mode)!=0);
            host_csr[i]^=1; CHECK(judge(d,mode)==0); ++csr_faults;
        }
        if(d==0 && l==1 && mode==1) { original_controls=controls(); CHECK(original_controls==6 && judge(d,mode)==0); }
        /* The next initialize must restore the real buffers even on a cache
         * hit for the same dataset/layout. References are never corrupted. */
        memset(&split_arena,0x11,sizeof(split_arena));
        memset(&caller_workspace,0x22,sizeof(caller_workspace));
        memset(&caller_y,0x33,sizeof(caller_y));
        ++cases;
    }
    printf("HARNESS_BYTES_PASS cases=%u byte_faults=%u csr_faults=%u controls=%u\n",cases,byte_faults,csr_faults,original_controls);
    return 0;
}
