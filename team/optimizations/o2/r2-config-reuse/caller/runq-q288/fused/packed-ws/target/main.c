#include "q288_ws.h"
struct guarded_packed { uint64_t head[2]; int8_t value[82944]; uint64_t tail[2]; };
#include "data.h"
extern void _putc(char);
extern void split_measure(void *, struct caller_measurement *, uintptr_t);
extern void q_fault_probe(const int8_t *, const int8_t *, struct caller_slot *);

struct guarded_slots { uint64_t head[2]; struct caller_slot value[8]; uint64_t tail[2]; };
union float_words { float value[288]; uint32_t bits[288]; };
struct guarded_output { uint64_t head[2]; union float_words data; uint64_t tail[2]; };
struct guarded_scales { uint64_t head[2]; float value[2592]; uint64_t tail[2]; };
struct guarded_ws_context { uint64_t head[2]; struct q288_ws_context value; uint64_t tail[2]; };
struct guarded_slots q_slots __attribute__((aligned(16)));
struct guarded_output q_output __attribute__((aligned(16)));
struct guarded_scales q_packed_scale __attribute__((aligned(16)));
struct guarded_ws_context q_ws_guarded __attribute__((aligned(16)));
struct q288_context q_context;
struct q288_ws_pack_context q_pack_context;
struct caller_measurement q_measurement;
struct caller_measurement q_samples[Q_WINDOWS];
struct call_record { unsigned stage,arm,dataset; };
struct call_record q_call_records[Q_TOTAL_CALLS];
unsigned q_call_count;
static const uint64_t guard=UINT64_C(0xd15ea5e5cafebabe);
_Static_assert(offsetof(struct guarded_packed,value)==16 && offsetof(struct guarded_slots,value)==16 &&
               offsetof(struct guarded_output,data)==16 && offsetof(struct guarded_scales,value)==16 &&
               offsetof(struct guarded_ws_context,value)==16,"guarded offsets");
_Static_assert(sizeof(((struct guarded_ws_context *)0)->value)==48,"real six-pointer context");
static void text(const char *s) { while(*s) _putc(*s++); }
static void number(uint64_t v) {
    char b[21];unsigned n=0;do { b[n++]=(char)('0'+v%10);v/=10; } while(v);
    while(n) _putc(b[--n]);
}
static int fail(const char *where,unsigned detail) {
    text("Q_FAIL ");text(where);_putc(' ');number(detail);_putc('\n');return 1;
}
static void state(void) {
    __asm__ volatile("csrwi fcsr,0; csrwi vstart,0; csrwi vcsr,7; vsetivli zero,8,e8,m1,tu,mu":::"memory");
}
static uint32_t bits_at(const float *p) {
    uint32_t value;__builtin_memcpy(&value,p,sizeof(value));return value;
}
static int32_t dot(unsigned d,unsigned row,unsigned group) {
    int32_t v=0;for(unsigned k=0;k<32;++k) v+=(int32_t)q_weights[row*288+group*32+k]*q_inputs[d][group*32+k];
    return v;
}
static unsigned guards(void) {
    const volatile struct guarded_packed *p=&q_packed;
    for(unsigned i=0;i<2;++i)
        if(p->head[i]!=guard || p->tail[i]!=guard || q_slots.head[i]!=guard ||
           q_slots.tail[i]!=guard || q_output.head[i]!=guard || q_output.tail[i]!=guard ||
           q_packed_scale.head[i]!=guard || q_packed_scale.tail[i]!=guard ||
           q_ws_guarded.head[i]!=guard || q_ws_guarded.tail[i]!=guard) return 1;
    return 0;
}
__attribute__((noinline,noclone)) static unsigned pack_judge(void) {
    for(unsigned i=0;i<2;++i)
        if(q_packed_scale.head[i]!=guard || q_packed_scale.tail[i]!=guard) return 1;
    if(q_pack_context.row_major!=q_weight_scale || q_pack_context.packed_scale!=q_packed_scale.value) return 2;
    /* Independent row/column traversal of the original row-major scales. */
    for(unsigned row=0;row<288;++row)
        for(unsigned group=0;group<9;++group)
            if(bits_at(q_packed_scale.value+(row/8)*72+group*8+row%8)!=
               bits_at(q_weight_scale+row*9+group)) return 3;
    return 0;
}
static unsigned pack_controls(void) {
    unsigned n=0;uint32_t value=bits_at(q_packed_scale.value)^1;
    __builtin_memcpy(q_packed_scale.value,&value,4);n+=pack_judge()!=0;
    value^=1;__builtin_memcpy(q_packed_scale.value,&value,4);
    q_packed_scale.tail[0]^=1;n+=pack_judge()!=0;q_packed_scale.tail[0]^=1;
    q_pack_context.row_major=q_weight_scale+1;n+=pack_judge()!=0;q_pack_context.row_major=q_weight_scale;
    return n;
}
static void prepare(unsigned d,unsigned arm) {
    for(unsigned i=0;i<2;++i) {
        q_slots.head[i]=q_slots.tail[i]=guard;q_output.head[i]=q_output.tail[i]=guard;
        q_ws_guarded.head[i]=q_ws_guarded.tail[i]=guard;
    }
    for(unsigned i=0;i<288;++i) q_output.data.bits[i]=0x7fc00bad;
    for(unsigned r=0;r<8;++r) {
        q_slots.value[r].value=(int32_t)0xa6a6a6a6;
        for(unsigned j=0;j<3;++j) q_slots.value[r].high[j]=0xa6a6a6a6;
    }
    q_context=(struct q288_context){q_packed.value,q_inputs[d],q_weight_scale,q_input_scale[d],
        q_output.data.value,q_slots.value,split_entries[q_methods[arm]]};
    q_ws_guarded.value=(struct q288_ws_context){q_packed.value,q_inputs[d],q_packed_scale.value,
        q_input_scale[d],q_output.data.value,q_slots.value};
    state();
}
static void *context_for(unsigned arm) {
    return arm<2 ? (void *)&q_context : (void *)&q_ws_guarded.value;
}
/* All C calls use the actual declared interface; the common assembly timer
 * receives the same raw entry addresses for its indirect call. */
static void call(unsigned arm) {
    switch(arm) {
    case 0:q288_fused_rvv4(&q_context);break;
    case 1:q288_tail_vdot(&q_context);break;
    case 2:q288_ws_rvv4(&q_ws_guarded.value);break;
    case 3:q288_ws_vdot(&q_ws_guarded.value);break;
    }
}
__attribute__((noinline,noclone)) static unsigned judge(unsigned d,unsigned arm) {
    if(guards()) return 1;
    for(unsigned r=0;r<288;++r) if(q_output.data.bits[r]!=q_golden[d][r]) return 2;
    for(unsigned r=0;r<8;++r) {
        if(q_slots.value[r].value!=dot(d,280+r,8)) return 3;
        for(unsigned j=0;j<3;++j) if(q_slots.value[r].high[j]) return 4;
    }
    if(arm<2) {
        if(q_context.packed!=q_packed.value || q_context.x!=q_inputs[d] ||
           q_context.weight_scale!=q_weight_scale || q_context.input_scale!=q_input_scale[d] ||
           q_context.y!=q_output.data.value || q_context.slots!=q_slots.value ||
           q_context.entry!=split_entries[q_methods[arm]]) return 5;
    } else {
        const struct q288_ws_context *c=&q_ws_guarded.value;
        if(c->packed!=q_packed.value || c->x!=q_inputs[d] || c->packed_scale!=q_packed_scale.value ||
           c->input_scale!=q_input_scale[d] || c->y!=q_output.data.value || c->slots!=q_slots.value) return 5;
    }
    uint64_t vl,vt,vs,vc,frm;
    __asm__ volatile("csrr %0,vl; csrr %1,vtype; csrr %2,vstart; csrr %3,vcsr; csrr %4,frm"
        :"=r"(vl),"=r"(vt),"=r"(vs),"=r"(vc),"=r"(frm));
    return vl!=8 || vt!=0 || vs!=0 || vc!=7 || frm!=0 ? 6 : 0;
}
static unsigned controls(unsigned d,unsigned arm) {
    unsigned n=0;
    q_output.data.bits[0]^=1;n+=judge(d,arm)!=0;q_output.data.bits[0]^=1;
    q_slots.value[0].value^=1;n+=judge(d,arm)!=0;q_slots.value[0].value^=1;
    q_slots.value[0].high[2]^=0x10;n+=judge(d,arm)!=0;q_slots.value[0].high[2]^=0x10;
    q_output.tail[0]^=1;n+=judge(d,arm)!=0;q_output.tail[0]^=1;
    if(arm<2) { q_context.x=q_inputs[0];n+=judge(d,arm)!=0;q_context.x=q_inputs[d]; }
    else { q_ws_guarded.value.x=q_inputs[0];n+=judge(d,arm)!=0;q_ws_guarded.value.x=q_inputs[d]; }
    return n;
}
static void record(unsigned stage,unsigned arm,unsigned dataset) {
    q_call_records[q_call_count++]=(struct call_record){stage,arm,dataset};
}
int main(void) {
    __asm__ volatile("csrs mstatus,%0"::"r"((uint64_t)0x6600):"memory");
    text("Q_BEGIN contract=" Q_CONTRACT " windows=12\n");
    for(unsigned i=0;i<2;++i) q_packed_scale.head[i]=q_packed_scale.tail[i]=guard;
    for(unsigned i=0;i<2592;++i) {
        uint32_t poison=0x7fc00bad;__builtin_memcpy(q_packed_scale.value+i,&poison,4);
    }
    q_pack_context=(struct q288_ws_pack_context){q_weight_scale,q_packed_scale.value};
    q288_ws_pack(&q_pack_context);
    if(pack_judge()) return fail("pack",1);
    unsigned packed_controls=pack_controls();
    if(packed_controls!=3 || pack_judge()) return fail("pack_controls",packed_controls);
    text("Q_PACK words=2592 controls=3 failures=0\n");
    prepare(0,0);q_fault_probe(q_weights,q_inputs[0],q_slots.value);
    int32_t expected=0;for(unsigned k=0;k<8;++k) expected+=(int32_t)q_weights[k]*q_inputs[0][k];
    if(q_slots.value[0].value!=expected || guards()) return fail("probe",1);
    for(unsigned j=0;j<3;++j) if(q_slots.value[0].high[j]) return fail("probe_high",j);
    unsigned detected=0;
    for(unsigned i=0;i<8;++i) {
        unsigned arm=q_functional_order[i],d=q_functional_datasets[i];
        prepare(d,arm);call(arm);
        unsigned verdict=judge(d,arm);if(verdict) return fail("functional",i*10+verdict);
        record(0,arm,d);
        if(i==0 || i==2) {
            unsigned n=controls(d,arm);detected+=n;
            if(n!=5 || judge(d,arm)) return fail("controls",i*10+n);
        }
    }
    for(unsigned i=0;i<Q_WINDOWS;++i) {
        unsigned arm=q_order[i];
        prepare(0,arm);call(arm);
        unsigned verdict=judge(0,arm);if(verdict) return fail("warm",i*10+verdict);
        record(1,arm,0);
        prepare(0,arm);split_measure(context_for(arm),&q_measurement,q_entry_addresses[arm]);
        q_samples[i]=q_measurement;verdict=judge(0,arm);
        if(verdict) return fail("measured",i*10+verdict);
        record(2,arm,0);
    }
    if(q_call_count!=Q_TOTAL_CALLS || detected!=10 || pack_judge()) return fail("final",q_call_count);
    text("Q_FUNCTIONAL calls=32 controls=10 outputs=9216 warm=12 extra=8\n");
    for(unsigned i=0;i<Q_TOTAL_CALLS;++i) {
        text("Q_CALL ");number(i);_putc(' ');number(q_call_records[i].stage);_putc(' ');
        number(q_call_records[i].arm);_putc(' ');number(q_call_records[i].dataset);_putc('\n');
    }
    for(unsigned i=0;i<Q_WINDOWS;++i) {
        text("QW ");number(i);_putc(' ');number(q_samples[i].cycles);_putc(' ');
        number(q_samples[i].instructions);_putc('\n');
    }
    text("Q_END windows=12 full_calls=32 leaf_calls=0 inline_calls=32 probe_dots=1 failures=0\n");
    return 0;
}
