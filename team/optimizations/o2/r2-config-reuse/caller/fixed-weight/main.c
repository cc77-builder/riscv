#include "fixed.h"
#include "data.h"
extern void _putc(char);
extern void split_measure(void *,struct caller_measurement *,uintptr_t);

union fixed_arena_storage { uint64_t words[128]; unsigned char bytes[1024]; };
struct fixed_packed_storage { uint64_t head[2]; int8_t bytes[288]; uint64_t tail[2]; };
union fixed_packed_union { struct fixed_packed_storage value; uint64_t words[40]; };
struct fixed_slots_storage { uint64_t head[2]; struct caller_slot value[32]; uint64_t tail[2]; };
union fixed_slots_union { struct fixed_slots_storage value; uint64_t words[68]; };
struct fixed_y_storage { uint64_t head[2]; int32_t value[32]; uint64_t tail[2]; };
union fixed_y_union { struct fixed_y_storage value; uint64_t words[20]; };
union fixed_arena_storage fixed_arena __attribute__((aligned(16)));
union fixed_packed_union fixed_packed_buffer __attribute__((aligned(16)));
union fixed_slots_union fixed_slots __attribute__((aligned(16)));
union fixed_y_union fixed_y __attribute__((aligned(16)));
struct fixed_context fixed_context;
struct caller_measurement fixed_measurement;
struct caller_measurement fixed_samples[FIXED_WINDOWS];
static union fixed_arena_storage arena_reference __attribute__((aligned(16)));
static int32_t scalar_golden[7][4][8];
static unsigned prepared_dataset=7,prepared_layout=3,a_offset,x_offset;
static const uint64_t guard=UINT64_C(0xd15ea5e5cafebabe);
static const uint64_t poison=UINT64_C(0xa6a6a6a6a6a6a6a6);
_Static_assert(sizeof(union fixed_packed_union)==320 && sizeof(union fixed_slots_union)==544 &&
    sizeof(union fixed_y_union)==160,"whole-word guarded storage");
_Static_assert(offsetof(struct fixed_packed_storage,bytes)==16 &&
    offsetof(struct fixed_slots_storage,value)==16 && offsetof(struct fixed_y_storage,value)==16,
    "guarded data offsets");

#ifdef FIXED_HOST_TEST
static uint64_t host_vl=8,host_vt=0,host_vs=0,host_vc=7;
static void enable_vs(void) {}
static void reset_vstate(void) { host_vl=8;host_vt=0;host_vs=0;host_vc=7; }
static void set_vcsr(unsigned n) { host_vc=n; }
static unsigned bad_vstate(void) { return host_vl!=8 || host_vt!=0 || host_vs!=0 || host_vc!=7; }
#else
static void enable_vs(void) { __asm__ volatile("csrs mstatus,%0"::"r"((uint64_t)0x600):"memory"); }
static void reset_vstate(void) {
    __asm__ volatile("csrwi vstart,0; csrwi vcsr,7; vsetivli zero,8,e8,m1,tu,mu":::"memory");
}
static void set_vcsr(unsigned n) {
    if(n) __asm__ volatile("csrwi vcsr,7":::"memory");
    else __asm__ volatile("csrwi vcsr,0":::"memory");
}
static unsigned bad_vstate(void) {
    uint64_t vl,vt,vs,vc;
    __asm__ volatile("csrr %0,vl; csrr %1,vtype; csrr %2,vstart; csrr %3,vcsr"
        :"=r"(vl),"=r"(vt),"=r"(vs),"=r"(vc));
    return vl!=8 || vt!=0 || vs!=0 || vc!=7;
}
#endif
static void text(const char *s) { while(*s) _putc(*s++); }
static void number(uint64_t v) {
    char b[21];unsigned n=0;
    do { b[n++]=(char)('0'+v%10);v/=10; } while(v);
    while(n) _putc(b[--n]);
}
static void prepare_golden(void) {
    for(unsigned d=0;d<7;++d) for(unsigned t=0;t<4;++t) for(unsigned r=0;r<8;++r) {
        int32_t sum=0;
        for(unsigned k=0;k<32;++k) sum+=(int32_t)fixed_inputs[d][r*32+k]*fixed_inputs[d][256+t*32+k];
        scalar_golden[d][t][r]=sum;
    }
}
static void prepare_reference(unsigned d,unsigned layout) {
    if(prepared_dataset==d && prepared_layout==layout) return;
    a_offset=layout==0?96:layout==1?97:601;
    x_offset=layout==0?512:layout==1?513:35;
    for(unsigned i=0;i<128;++i) arena_reference.words[i]=poison;
    for(unsigned i=0;i<256;++i) arena_reference.bytes[a_offset+i]=(unsigned char)fixed_inputs[d][i];
    for(unsigned i=0;i<128;++i) arena_reference.bytes[x_offset+i]=(unsigned char)fixed_inputs[d][256+i];
    prepared_dataset=d;prepared_layout=layout;
}
static void initialize(unsigned d,unsigned kind,unsigned count,unsigned layout) {
    prepare_reference(d,layout);
    for(unsigned i=0;i<128;++i) fixed_arena.words[i]=arena_reference.words[i];
    for(unsigned i=0;i<40;++i) fixed_packed_buffer.words[i]=poison;
    for(unsigned i=0;i<68;++i) fixed_slots.words[i]=poison;
    for(unsigned i=0;i<20;++i) fixed_y.words[i]=poison;
    for(unsigned i=0;i<2;++i) {
        fixed_packed_buffer.value.head[i]=fixed_packed_buffer.value.tail[i]=guard;
        fixed_slots.value.head[i]=fixed_slots.value.tail[i]=guard;
        fixed_y.value.head[i]=fixed_y.value.tail[i]=guard;
    }
    fixed_context=(struct fixed_context){
        (const int8_t *)fixed_arena.bytes+a_offset,(const int8_t *)fixed_arena.bytes+x_offset,
        fixed_y.value.value,fixed_slots.value.value,fixed_packed_buffer.value.bytes,
        packed_entries[kind],split_entries[kind],count};
    reset_vstate();
}
static unsigned judge(unsigned d,unsigned kind,unsigned count,unsigned mode) {
    for(unsigned i=0;i<128;++i) if(fixed_arena.words[i]!=arena_reference.words[i]) return 1;
    for(unsigned i=0;i<2;++i) if(fixed_packed_buffer.value.head[i]!=guard || fixed_packed_buffer.value.tail[i]!=guard ||
        fixed_slots.value.head[i]!=guard || fixed_slots.value.tail[i]!=guard ||
        fixed_y.value.head[i]!=guard || fixed_y.value.tail[i]!=guard) return 2;
    for(unsigned i=0;i<288;++i) {
        unsigned char expected=mode?0xa6:(unsigned char)fixed_inputs[d][i<256?i:256+(count-1)*32+i-256];
        if((unsigned char)fixed_packed_buffer.value.bytes[i]!=expected) return 3;
    }
    for(unsigned i=0;i<32;++i) {
        if(i<count*8) {
            int32_t expected=scalar_golden[d][i/8][i%8];
            if(fixed_y.value.value[i]!=expected || fixed_slots.value.value[i].value!=expected) return 4;
            for(unsigned j=0;j<3;++j) if(fixed_slots.value.value[i].high[j]) return 5;
        } else {
            if((uint32_t)fixed_y.value.value[i]!=UINT32_C(0xa6a6a6a6) ||
                (uint32_t)fixed_slots.value.value[i].value!=UINT32_C(0xa6a6a6a6)) return 6;
            for(unsigned j=0;j<3;++j) if(fixed_slots.value.value[i].high[j]!=UINT32_C(0xa6a6a6a6)) return 6;
        }
    }
    if(fixed_context.a!=(const int8_t *)fixed_arena.bytes+a_offset ||
        fixed_context.x!=(const int8_t *)fixed_arena.bytes+x_offset ||
        fixed_context.y!=fixed_y.value.value || fixed_context.slots!=fixed_slots.value.value ||
        fixed_context.packed!=fixed_packed_buffer.value.bytes ||
        fixed_context.packed_entry!=packed_entries[kind] || fixed_context.split_entry!=split_entries[kind] ||
        fixed_context.count!=count) return 7;
    return bad_vstate()?8:0;
}
static unsigned controls(void) {
    unsigned n=0;
    fixed_y.value.value[0]^=1;n+=judge(0,0,4,1)!=0;fixed_y.value.value[0]^=1;
    fixed_slots.value.value[8].high[2]^=0x10;n+=judge(0,0,4,1)!=0;fixed_slots.value.value[8].high[2]^=0x10;
    fixed_packed_buffer.value.bytes[0]^=1;n+=judge(0,0,4,1)!=0;fixed_packed_buffer.value.bytes[0]^=1;
    fixed_arena.bytes[a_offset]^=1;n+=judge(0,0,4,1)!=0;fixed_arena.bytes[a_offset]^=1;
    fixed_arena.bytes[x_offset+32]^=1;n+=judge(0,0,4,1)!=0;fixed_arena.bytes[x_offset+32]^=1;
    fixed_slots.value.head[0]^=1;n+=judge(0,0,4,1)!=0;fixed_slots.value.head[0]^=1;
    fixed_y.value.tail[0]^=1;n+=judge(0,0,4,1)!=0;fixed_y.value.tail[0]^=1;
    set_vcsr(0);n+=judge(0,0,4,1)!=0;set_vcsr(7);
    return n;
}
static unsigned measured(unsigned d,unsigned choice,unsigned count,unsigned seq) {
    initialize(d,4,count,0); /* identical firstdot RVV conditioning of a whole stream */
    fixed_split(&fixed_context);
    if(judge(d,4,count,1)) return 9;
    unsigned kind=choice==12?0:choice%6,mode=choice>=6;
    initialize(d,kind,count,0);
    split_measure(&fixed_context,&fixed_measurement,(uintptr_t)(mode?&fixed_split:&fixed_packed));
    fixed_samples[seq]=fixed_measurement;
    return judge(d,kind,count,mode);
}
int main(void) {
    enable_vs();prepare_golden();
    text("FIXED_BEGIN contract=" FIXED_CONTRACT " windows=");number(FIXED_WINDOWS);_putc('\n');
    unsigned calls=0,detected=0;
    for(unsigned d=0;d<7;++d) for(unsigned layout=1;layout<=2;++layout)
        for(unsigned mode=1;;--mode) {
            for(unsigned kind=0;kind<6;++kind) {
                initialize(d,kind,4,layout);
                if(mode) fixed_split(&fixed_context);else fixed_packed(&fixed_context);
                if(judge(d,kind,4,mode)) { text("FIXED_FAIL functional\n");return 1; }
                if(calls==0) { detected=controls();if(detected!=8 || judge(0,0,4,1)) return 2; }
                ++calls;
            }
            if(!mode) break;
        }
    text("FIXED_FUNCTIONAL calls=");number(calls);text(" controls=");number(detected);_putc('\n');
    unsigned seq=0;
    for(unsigned d=0;d<3;++d) for(unsigned count_i=0;count_i<2;++count_i)
        for(unsigned rep=0;rep<6;++rep) {
            unsigned count=count_i?4:1;
            unsigned verdict=measured(d,12,count,seq++);
            if(verdict) return 3;
            for(unsigned pos=0;pos<12;++pos) {
                unsigned choice=(rep&1)?11-pos:pos;
                verdict=measured(d,choice,count,seq++);
                if(verdict) { text("FIXED_FAIL measured seq=");number(seq-1);text(" verdict=");number(verdict);_putc('\n');return 4; }
            }
            if(measured(d,12,count,seq++)) return 5;
        }
    for(unsigned i=0;i<seq;++i) {
        text("FW ");number(i);_putc(' ');number(fixed_samples[i].cycles);_putc(' ');
        number(fixed_samples[i].instructions);_putc('\n');
    }
    text("FIXED_END windows=");number(seq);text(" failures=0\n");
    return seq!=FIXED_WINDOWS;
}
