#include "q288.h"
#include "data.h"
extern void _putc(char);
extern void split_measure(void *, struct caller_measurement *, uintptr_t);
extern void q_fault_probe(const int8_t *, const int8_t *, struct caller_slot *);
struct guarded_packed { uint64_t head[2]; int8_t value[82944]; uint64_t tail[2]; };
struct guarded_slots { uint64_t head[2]; struct caller_slot value[8]; uint64_t tail[2]; };
union float_words { float value[288]; uint32_t bits[288]; };
struct guarded_output { uint64_t head[2]; union float_words data; uint64_t tail[2]; };
struct guarded_packed q_packed __attribute__((aligned(16)));
struct guarded_slots q_slots __attribute__((aligned(16)));
struct guarded_output q_output __attribute__((aligned(16)));
struct q288_context q_context;
struct q288_pack_context q_pack_context;
struct caller_measurement q_measurement;
struct caller_measurement q_samples[Q_WINDOWS];
static const uint64_t guard = UINT64_C(0xd15ea5e5cafebabe);
_Static_assert(offsetof(struct guarded_packed,value)==16 && offsetof(struct guarded_slots,value)==16 &&
               offsetof(struct guarded_output,data)==16, "guarded offsets");
static void text(const char *s) { while (*s) _putc(*s++); }
static void number(uint64_t v) {
    char b[21]; unsigned n=0;
    do { b[n++]=(char)('0'+v%10); v/=10; } while(v);
    while(n) _putc(b[--n]);
}
static int fail(const char *where, unsigned detail) {
    text("Q_FAIL ");text(where);_putc(' ');number(detail);_putc('\n');return 1;
}
static void state(void) {
    __asm__ volatile("csrwi fcsr,0; csrwi vstart,0; csrwi vcsr,7; vsetivli zero,8,e8,m1,tu,mu":::"memory");
}
static int32_t dot(unsigned d,unsigned row,unsigned group) {
    int32_t v=0;
    for(unsigned k=0;k<32;++k) v+=(int32_t)q_weights[row*288+group*32+k]*q_inputs[d][group*32+k];
    return v;
}
static unsigned guards(void) {
    for(unsigned i=0;i<2;++i)
        if(q_packed.head[i]!=guard || q_packed.tail[i]!=guard || q_slots.head[i]!=guard ||
           q_slots.tail[i]!=guard || q_output.head[i]!=guard || q_output.tail[i]!=guard) return 1;
    return 0;
}
static void prepare(unsigned d,unsigned kind) {
    for(unsigned i=0;i<2;++i) {
        q_packed.head[i]=q_packed.tail[i]=guard;
        q_slots.head[i]=q_slots.tail[i]=guard;
        q_output.head[i]=q_output.tail[i]=guard;
    }
    for(unsigned i=0;i<288;++i) q_output.data.bits[i]=0x7fc00bad;
    for(unsigned r=0;r<8;++r) {
        q_slots.value[r].value=(int32_t)0xa6a6a6a6;
        for(unsigned j=0;j<3;++j) q_slots.value[r].high[j]=0xa6a6a6a6;
    }
    q_context=(struct q288_context){q_packed.value,q_inputs[d],q_weight_scale,q_input_scale[d],
        q_output.data.value,q_slots.value,split_entries[kind]};
    state();
}
static unsigned leaf_judge(unsigned d,unsigned t,unsigned g) {
    for(unsigned r=0;r<8;++r) {
        if(q_slots.value[r].value!=dot(d,8*t+r,g)) return 1;
        for(unsigned j=0;j<3;++j) if(q_slots.value[r].high[j]) return 2;
    }
    return guards() ? 3 : 0;
}
static unsigned judge(unsigned d,unsigned kind) {
    if(guards()) return 1;
    for(unsigned r=0;r<288;++r) if(q_output.data.bits[r]!=q_golden[d][r]) return 2;
    if(leaf_judge(d,35,8)) return 3;
    if(q_context.packed!=q_packed.value || q_context.x!=q_inputs[d] ||
       q_context.weight_scale!=q_weight_scale || q_context.input_scale!=q_input_scale[d] ||
       q_context.y!=q_output.data.value || q_context.slots!=q_slots.value ||
       q_context.entry!=split_entries[kind]) return 4;
    uint64_t vl,vt,vs,vc,frm;
    __asm__ volatile("csrr %0,vl; csrr %1,vtype; csrr %2,vstart; csrr %3,vcsr; csrr %4,frm"
        :"=r"(vl),"=r"(vt),"=r"(vs),"=r"(vc),"=r"(frm));
    return vl!=8 || vt!=0 || vs!=0 || vc!=7 || frm!=0 ? 5 : 0;
}
static unsigned pack_ok(void) {
    unsigned index=0;
    for(unsigned t=0;t<36;++t) for(unsigned g=0;g<9;++g)
        for(unsigned r=0;r<8;++r) for(unsigned k=0;k<32;++k)
            if(q_packed.value[index++]!=q_weights[(8*t+r)*288+32*g+k]) return 1;
    return guards();
}
static unsigned controls(void) {
    unsigned n=0;
    q_output.data.bits[0]^=1; n+=judge(0,0)!=0; q_output.data.bits[0]^=1;
    q_slots.value[0].value^=1; n+=judge(0,0)!=0; q_slots.value[0].value^=1;
    q_slots.value[0].high[2]^=0x10; n+=judge(0,0)!=0; q_slots.value[0].high[2]^=0x10;
    q_output.tail[0]^=1; n+=judge(0,0)!=0; q_output.tail[0]^=1;
    q_context.x=q_inputs[1]; n+=judge(0,0)!=0; q_context.x=q_inputs[0];
    q_packed.value[0]^=1; n+=pack_ok()!=0; q_packed.value[0]^=1;
    return n;
}
int main(void) {
    __asm__ volatile("csrs mstatus,%0"::"r"((uint64_t)0x6600):"memory");
    text("Q_BEGIN contract=" Q_CONTRACT " windows=11\n");
    prepare(0,0);
    q_fault_probe(q_weights,q_inputs[0],q_slots.value);
    int32_t probe_expected=0;
    for(unsigned k=0;k<8;++k) probe_expected+=(int32_t)q_weights[k]*q_inputs[0][k];
    if(q_slots.value[0].value!=probe_expected || guards()) return fail("early_probe",1);
    for(unsigned j=0;j<3;++j) if(q_slots.value[0].high[j]) return fail("early_probe_high",j);
    q_pack_context=(struct q288_pack_context){q_weights,q_packed.value};
    state(); split_measure(&q_pack_context,&q_measurement,(uintptr_t)&q288_pack);
    q_samples[0]=q_measurement;
    if(pack_ok()) return fail("pack",1);
    unsigned detected=0;
    for(unsigned i=0;i<Q_CALLS;++i) {
        unsigned arm=q_order[i],d=q_datasets[i],method=q_methods[arm];
        prepare(d,method);
        split_measure(&q_context,&q_measurement,(uintptr_t)q_wrappers[arm]);
        q_samples[i+1]=q_measurement;
        unsigned verdict=judge(d,method);
        if(verdict) return fail("functional_cost",i*10+verdict);
        if(i==0) {
            detected=controls();
            if(detected!=6 || judge(0,0)) return fail("controls",detected);
        }
    }
    if(pack_ok()) return fail("final_inputs",1);
    text("Q_FUNCTIONAL calls=10 controls=6 outputs=2880\n");
    for(unsigned i=0;i<Q_WINDOWS;++i) {
        text("QW ");number(i);_putc(' ');number(q_samples[i].cycles);_putc(' ');
        number(q_samples[i].instructions);_putc('\n');
    }
    text("Q_END windows=11 full_calls=10 leaf_calls=3240 probe_dots=1 failures=0\n");
    return 0;
}
