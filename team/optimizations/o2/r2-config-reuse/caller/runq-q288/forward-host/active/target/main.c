#include "boundary.h"
#include "data.h"
extern void _putc(char);
extern void split_measure(void *,struct caller_measurement *,uintptr_t);
extern void q_fault_probe(const int8_t *,const int8_t *,struct caller_slot *);
struct guarded_x { uint64_t head[2];int8_t value[288];uint64_t tail[2]; };
struct guarded_xs { uint64_t head[2];union { float f[12];uint32_t u[12]; } value;uint64_t tail[2]; };
struct guarded_y { uint64_t head[2];union { float f[3][288];uint32_t u[3][288]; } value;uint64_t tail[2]; };
struct guarded_slots { uint64_t head[2];struct caller_slot value[3][8];uint64_t tail[2]; };
struct guarded_x qkv_x __attribute__((aligned(16)));
struct guarded_xs qkv_xs __attribute__((aligned(16)));
struct guarded_y qkv_y __attribute__((aligned(16)));
struct guarded_slots qkv_slots __attribute__((aligned(16)));
struct q288_context qkv_projection[3];
struct qkv_context qkv_context;
struct caller_measurement qkv_measurement,qkv_samples[6];
struct call_record { unsigned stage,arm,dataset; };
struct call_record qkv_calls[14];
unsigned qkv_count;
static const uint64_t guard=UINT64_C(0xd15ea5e5cafebabe);
_Static_assert(offsetof(struct guarded_x,value)==16 && offsetof(struct guarded_xs,value)==16 &&
               offsetof(struct guarded_y,value)==16 && offsetof(struct guarded_slots,value)==16,"guarded offsets");
static void text(const char *s) { while(*s)_putc(*s++); }
static void number(uint64_t v) { char b[21];unsigned n=0;do {b[n++]=(char)('0'+v%10);v/=10;}while(v);while(n)_putc(b[--n]); }
static int fail(const char *why,unsigned detail) {text("QKV_FAIL ");text(why);_putc(' ');number(detail);_putc('\n');return 1;}
static void state(void) {__asm__ volatile("csrwi fcsr,0;csrwi vstart,0;csrwi vcsr,7;vsetivli zero,8,e8,m1,tu,mu":::"memory");}
static void prepare(unsigned d,unsigned arm) {
    for(unsigned i=0;i<2;++i) {
        qkv_x.head[i]=qkv_x.tail[i]=qkv_xs.head[i]=qkv_xs.tail[i]=guard;
        qkv_y.head[i]=qkv_y.tail[i]=qkv_slots.head[i]=qkv_slots.tail[i]=guard;
    }
    for(unsigned i=0;i<288;++i)qkv_x.value[i]=(int8_t)0xa6;
    for(unsigned i=0;i<12;++i)qkv_xs.value.u[i]=0x7fc00bad;
    for(unsigned m=0;m<3;++m) {
        for(unsigned i=0;i<288;++i)qkv_y.value.u[m][i]=0x7fc00bad;
        for(unsigned i=0;i<8;++i) {
            qkv_slots.value[m][i].value=(int32_t)0xa6a6a6a6;
            for(unsigned j=0;j<3;++j)qkv_slots.value[m][i].high[j]=0xa6a6a6a6;
        }
        qkv_projection[m]=(struct q288_context){qkv_packed[m],qkv_x.value,qkv_weight_scale[m],
            qkv_xs.value.f,qkv_y.value.f[m],qkv_slots.value[m],split_entries[arm?5:0]};
    }
    qkv_context=(struct qkv_context){qkv_fp[d],qkv_x.value,qkv_xs.value.f,
        {qkv_projection,qkv_projection+1,qkv_projection+2},qkv_kernels[arm]};
    state();
}
static unsigned guards(void) {
    for(unsigned i=0;i<2;++i)if(qkv_x.head[i]!=guard || qkv_x.tail[i]!=guard ||
        qkv_xs.head[i]!=guard || qkv_xs.tail[i]!=guard || qkv_y.head[i]!=guard || qkv_y.tail[i]!=guard ||
        qkv_slots.head[i]!=guard || qkv_slots.tail[i]!=guard)return 1;
    for(unsigned i=9;i<12;++i)if(qkv_xs.value.u[i]!=0x7fc00bad)return 2;
    return 0;
}
static unsigned quantized(unsigned d) {
    if(guards())return 1;
    for(unsigned i=0;i<288;++i)if(qkv_x.value[i]!=qkv_expected_x[d][i])return 2;
    for(unsigned i=0;i<9;++i)if(qkv_xs.value.u[i]!=qkv_expected_xs[d][i])return 3;
    uint64_t frm,flags;__asm__ volatile("csrr %0,frm;csrr %1,fflags":"=r"(frm),"=r"(flags));
    return frm || (flags&0x1c) ? 4 : 0;
}
__attribute__((noinline,noclone)) static unsigned judge(unsigned d,unsigned arm) {
    if(quantized(d))return 1;
    for(unsigned m=0;m<3;++m) {
        for(unsigned i=0;i<288;++i)if(qkv_y.value.u[m][i]!=qkv_expected_y[d][m][i])return 2;
        for(unsigned r=0;r<8;++r) {
            int32_t dot=0;for(unsigned k=0;k<32;++k)dot+=(int32_t)qkv_weights[m][(280+r)*288+256+k]*qkv_expected_x[d][256+k];
            if(qkv_slots.value[m][r].value!=dot)return 3;
            for(unsigned j=0;j<3;++j)if(qkv_slots.value[m][r].high[j])return 4;
        }
        const struct q288_context *c=qkv_projection+m;
        if(c->packed!=qkv_packed[m] || c->x!=qkv_x.value || c->weight_scale!=qkv_weight_scale[m] ||
           c->input_scale!=qkv_xs.value.f || c->y!=qkv_y.value.f[m] || c->slots!=qkv_slots.value[m] ||
           c->entry!=split_entries[arm?5:0] || qkv_context.projection[m]!=c)return 5;
    }
    if(qkv_context.fp!=qkv_fp[d] || qkv_context.x!=qkv_x.value || qkv_context.xs!=qkv_xs.value.f ||
       qkv_context.kernel!=qkv_kernels[arm])return 6;
    uint64_t vl,vt,vs,vc;__asm__ volatile("csrr %0,vl;csrr %1,vtype;csrr %2,vstart;csrr %3,vcsr"
        :"=r"(vl),"=r"(vt),"=r"(vs),"=r"(vc));
    return vl!=8 || vt!=0 || vs!=0 || vc!=7 ? 7 : 0;
}
static unsigned controls(unsigned d,unsigned arm) {
    unsigned n=0;
    qkv_x.value[0]^=1;n+=judge(d,arm)!=0;qkv_x.value[0]^=1;
    qkv_xs.value.u[0]^=1;n+=judge(d,arm)!=0;qkv_xs.value.u[0]^=1;
    qkv_y.value.u[1][0]^=1;n+=judge(d,arm)!=0;qkv_y.value.u[1][0]^=1;
    qkv_slots.value[2][0].high[2]^=0x10;n+=judge(d,arm)!=0;qkv_slots.value[2][0].high[2]^=0x10;
    qkv_y.tail[0]^=1;n+=judge(d,arm)!=0;qkv_y.tail[0]^=1;
    qkv_context.fp=qkv_fp[0];n+=judge(d,arm)!=0;qkv_context.fp=qkv_fp[d];
    return n;
}
static void record(unsigned stage,unsigned arm,unsigned d) {qkv_calls[qkv_count++]=(struct call_record){stage,arm,d};}
int main(void) {
    __asm__ volatile("csrs mstatus,%0"::"r"((uint64_t)0x6600):"memory");
    text("QKV_BEGIN contract=" QKV_CONTRACT " windows=6\n");
    prepare(0,0);q_fault_probe(qkv_weights[0],qkv_expected_x[0],qkv_slots.value[0]);
    int32_t expected=0;for(unsigned k=0;k<8;++k)expected+=(int32_t)qkv_weights[0][k]*qkv_expected_x[0][k];
    if(qkv_slots.value[0][0].value!=expected || guards())return fail("probe",1);
    for(unsigned j=0;j<3;++j)if(qkv_slots.value[0][0].high[j])return fail("probe_high",j);
    /* Two actual captures plus one 9-group semantic fixture, outside timers. */
    for(unsigned d=0;d<3;++d) {
        prepare(d,0);qkv_quantize(qkv_fp[d],qkv_x.value,qkv_xs.value.f);
        unsigned verdict=quantized(d);if(verdict)return fail("quantizer",d*10+verdict);
    }
    unsigned detected=0;
    for(unsigned arm=0;arm<2;++arm) {
        prepare(1,arm);qkv_boundary(&qkv_context);unsigned verdict=judge(1,arm);
        if(verdict)return fail("functional",arm*10+verdict);
        record(0,arm,1);
        if(!arm) {detected=controls(1,arm);if(detected!=6 || judge(1,arm))return fail("controls",detected);}
    }
    for(unsigned i=0;i<6;++i) {
        unsigned arm=qkv_order[i];prepare(0,arm);qkv_boundary(&qkv_context);
        unsigned verdict=judge(0,arm);
        if(verdict)return fail("warm",i*10+verdict);
        record(1,arm,0);
        prepare(0,arm);split_measure(&qkv_context,&qkv_measurement,(uintptr_t)qkv_boundary);
        qkv_samples[i]=qkv_measurement;verdict=judge(0,arm);
        if(verdict)return fail("measured",i*10+verdict);
        record(2,arm,0);
    }
    if(qkv_count!=14)return fail("call_count",qkv_count);
    text("QKV_FUNCTIONAL boundaries=14 projections=42 outputs=12096 quantizer_probes=3 controls=6\n");
    for(unsigned i=0;i<14;++i) {text("QKV_CALL ");number(i);_putc(' ');number(qkv_calls[i].stage);_putc(' ');
        number(qkv_calls[i].arm);_putc(' ');number(qkv_calls[i].dataset);_putc('\n');}
    for(unsigned i=0;i<6;++i) {text("QKVW ");number(i);_putc(' ');number(qkv_samples[i].cycles);_putc(' ');
        number(qkv_samples[i].instructions);_putc('\n');}
    text("QKV_END windows=6 boundaries=14 projections=42 probe_dots=1 failures=0\n");return 0;
}
