/* Team full consumer: unchanged scalar baseline, original FR and original TA. */
#define TESTING
#include "upstream/runq.c"
#define D 288
#define H 768
#define L 6
#define V 32000
#define S 256
#include "state_layout.h"
#include "q288.h"

extern void q288_fused_rvv4(struct q288_context *);
extern void q288_tail_vdot(struct q288_context *);
extern unsigned char fixture_weights[],fixture_weights_end[],fixture_embedding[],fixture_embedding_end[];
__thread int errno;
uintptr_t __stack_chk_guard=UINT64_C(0x9157a6c2d384ef09);
unsigned char team_tls_area[96] __attribute__((aligned(16)));
volatile uint32_t projection_control __attribute__((section(".data"),used))=0;
volatile uint64_t projection_report[32];
unsigned char projection_snapshots[3][3][FULL_STATE_BYTES] __attribute__((aligned(16)));
int8_t projection_packed[172][Q288_WEIGHTS] __attribute__((aligned(16)));
float projection_tail_scales[13][288*9] __attribute__((aligned(16)));
struct counts {uint64_t quant_calls,quant_groups,quant_elements,matmuls,routed,scalar,blocks,tails;};
struct counts projection_counts[3][3];
static struct counts *count;
static struct full_storage storage[3] __attribute__((aligned(16)));
static Transformer transforms[3];
static QuantizedTensor token_weights,qweights[L],kweights[L],vweights[L],oweights[L],w1weights[L],w2weights[L],w3weights[L];
struct matrix {QuantizedTensor *tensor;unsigned rows,first,tail;};
static struct matrix matrices[37];
static unsigned position,method;
static int8_t pack_scratch[Q288_WEIGHTS] __attribute__((aligned(16)));
static float reference_output[V] __attribute__((aligned(16)));
static struct {uint64_t before[2];float value[288];uint64_t after[2];} tail_output __attribute__((aligned(16)));
static struct {uint64_t before[2];struct caller_slot value[8];uint64_t after[2];} slot_output __attribute__((aligned(16)));
#define GUARD UINT64_C(0x5a1d8c2976e340bf)

__attribute__((noreturn)) static void stop(unsigned code) {
    projection_report[3]=code;
    __asm__ volatile("mv a0,%0\n.word 0x0000006b"::"r"((uintptr_t)code):"a0","memory");
    for(;;) {}
}
__attribute__((noreturn)) void __stack_chk_fail(void) {stop(90);}
static void check(int ok,unsigned code) {if(!ok)stop(code);}
static uint32_t bits(float value) {uint32_t result;memcpy(&result,&value,4);return result;}
static int finite_float(float value) {return (bits(value)&UINT32_C(0x7f800000))!=UINT32_C(0x7f800000);}
static unsigned fcsr(void) {unsigned value;__asm__ volatile("csrr %0,fcsr":"=r"(value));return value;}
static void tls_check(void) {
    uintptr_t tp,error_address;
    __asm__ volatile("mv %0,tp":"=r"(tp));
    /* Observe the resolved address: C's distinct-object inference does not
     * describe this team's explicit bare-metal TLS backing allocation. */
    __asm__ volatile("mv %0,%1":"=r"(error_address):"r"(&errno));
    check(tp==(uintptr_t)(team_tls_area+16) && error_address==tp+FULL_ERRNO_OFFSET,80);
    for(unsigned i=0;i<16;++i)check(team_tls_area[i]==0x6b && team_tls_area[80+i]==0xa7,81);
}
static void tensor(unsigned char **cursor,QuantizedTensor *t,size_t elements) {
    t->q=(int8_t*)*cursor;*cursor+=elements;t->s=(float*)*cursor;*cursor+=elements/32*4;
}
static void weights(TransformerWeights *w) {
    unsigned char *cursor=fixture_weights;
    w->rms_att_weight=(float*)cursor;cursor+=L*D*4;
    w->rms_ffn_weight=(float*)cursor;cursor+=L*D*4;
    w->rms_final_weight=(float*)cursor;cursor+=D*4;
    tensor(&cursor,&token_weights,(size_t)V*D);w->q_tokens=&token_weights;w->wcls=&token_weights;
    QuantizedTensor *arrays[]={qweights,kweights,vweights,oweights,w1weights,w2weights,w3weights};
    for(unsigned kind=0;kind<7;++kind)for(unsigned l=0;l<L;++l)tensor(&cursor,&arrays[kind][l],kind<4?D*D:D*H);
    w->wq=qweights;w->wk=kweights;w->wv=vweights;w->wo=oweights;w->w1=w1weights;w->w2=w2weights;w->w3=w3weights;
    w->token_embedding_table=(float*)fixture_embedding;
    check(cursor==fixture_weights_end && fixture_embedding_end-fixture_embedding==(size_t)V*D*4,82);
}
static void prepare(void) {
    QuantizedTensor *arrays[]={qweights,kweights,vweights,oweights,w1weights,w3weights};
    for(unsigned kind=0;kind<6;++kind)for(unsigned l=0;l<L;++l)
        matrices[kind*L+l]=(struct matrix){&arrays[kind][l],kind<4?D:H,0,0};
    matrices[36]=(struct matrix){&token_weights,V,0,0};
    unsigned block=0,tail=0;
    for(unsigned id=0;id<37;++id) {
        struct matrix *m=&matrices[id];m->first=block;
        for(unsigned row=0;row<m->rows;row+=288) {
            unsigned valid=m->rows-row;if(valid>288)valid=288;
            const int8_t *source=m->tensor->q+row*D;
            if(valid<288) {
                check(tail<13,83);m->tail=tail;
                memset(pack_scratch,0,sizeof(pack_scratch));memcpy(pack_scratch,source,valid*D);source=pack_scratch;
                memcpy(projection_tail_scales[tail],m->tensor->s+row*9,valid*9*4);
                for(unsigned i=valid*9;i<288*9;++i)projection_tail_scales[tail][i]=1.0f;
                ++tail;
            }
            check(block<172,83);struct q288_pack_context p={source,projection_packed[block++]};q288_pack(&p);
        }
    }
    check(block==172 && tail==13,83);projection_report[12]=block;projection_report[13]=tail;
}
static void checked_quantize(QuantizedTensor *qx,float *x,int n) {
    check((n==D || n==H) && GS==32,84);
    /* Check the original cast's domain before calling unchanged quantize. */
    for(int g=0;g<n/32;++g) {
        float max=0.0f;
        for(int k=0;k<32;++k) {float value=x[g*32+k];check(finite_float(value),84);float a=fabsf(value);if(a>max)max=a;}
        float scale=max/127.0f;check(max>0.0f && scale>0.0f && finite_float(scale),84);
        for(int k=0;k<32;++k) {
            float quotient=x[g*32+k]/scale;check(finite_float(quotient),84);
            double rounded=round((double)quotient);check(rounded>=-128.0 && rounded<=127.0,84);
        }
    }
    quantize(qx,x,n);++count->quant_calls;count->quant_groups+=n/32;count->quant_elements+=n;
}
static void check_context(struct q288_context *c) {
    uintptr_t starts[]={(uintptr_t)c->packed,(uintptr_t)c->x,(uintptr_t)c->weight_scale,(uintptr_t)c->input_scale,
        (uintptr_t)c->y,(uintptr_t)c->slots,(uintptr_t)c};
    const size_t bytes[]={82944,288,10368,36,1152,128,sizeof(*c)};
    check(starts[2]%4==0 && starts[3]%4==0 && starts[4]%4==0 && starts[5]%16==0,85);
    for(unsigned i=0;i<7;++i)for(unsigned j=i+1;j<7;++j)
        check(starts[i]+bytes[i]<=starts[j] || starts[j]+bytes[j]<=starts[i],85);
}
static void checked_matmul(float *out,QuantizedTensor *x,QuantizedTensor *w,int n,int d) {
    unsigned id=43;
    for(unsigned i=0;i<37;++i)if(w==matrices[i].tensor)id=i;
    for(unsigned l=0;l<L;++l)if(w==&w2weights[l])id=37+l;
    projection_report[6]=id;
    static const unsigned phases[]={0,6,12,18,24,30,37};
    unsigned call=count->matmuls;
    check(call<43 && id==(call==42?36:phases[call%7]+call/7),86);
    ++count->matmuls;
    if(id>=37) {check(id<43 && n==H && d==D,86);++count->scalar;matmul(out,x,w,n,d);return;}
    struct matrix *m=&matrices[id];check(n==D && d==(int)m->rows,86);++count->routed;
    for(unsigned row=0,block=m->first;row<m->rows;row+=288,++block) {
        unsigned valid=m->rows-row;if(valid>288)valid=288;
        tail_output.before[0]=tail_output.before[1]=tail_output.after[0]=tail_output.after[1]=GUARD;
        slot_output.before[0]=slot_output.before[1]=slot_output.after[0]=slot_output.after[1]=GUARD;
        memset(slot_output.value,0xa5,sizeof(slot_output.value));
        if(valid<288)memset(tail_output.value,0xa5,sizeof(tail_output.value));
        struct q288_context c={projection_packed[block],x->q,valid<288?projection_tail_scales[m->tail]:w->s+row*9,
            x->s,valid<288?tail_output.value:out+row,slot_output.value,0};
        check_context(&c);
        if(method==1)q288_fused_rvv4(&c);else {check(method==2,86);q288_tail_vdot(&c);}
        ++count->blocks;
        uintptr_t vl,vt,vs,vc;__asm__ volatile("csrr %0,vl\ncsrr %1,vtype\ncsrr %2,vstart\ncsrr %3,vcsr":"=r"(vl),"=r"(vt),"=r"(vs),"=r"(vc));
        check(vl==8 && vt==0 && vs==0 && vc==7 && fcsr()>>5==0,87);
        for(unsigned i=0;i<2;++i)check(tail_output.before[i]==GUARD && tail_output.after[i]==GUARD &&
            slot_output.before[i]==GUARD && slot_output.after[i]==GUARD,88);
        for(unsigned r=0;r<8;++r) {
            int32_t dot=0;for(unsigned k=0;k<32;++k)dot+=(int32_t)c.packed[(35*9+8)*256+r*32+k]*x->q[256+k];
            check(slot_output.value[r].value==dot && slot_output.value[r].high[0]==0 &&
                slot_output.value[r].high[1]==0 && slot_output.value[r].high[2]==0,89);
        }
        if(valid<288) {
            for(unsigned i=valid;i<288;++i)check(bits(tail_output.value[i])==0,91);
            if(projection_control==1 && position==0 && method==1 && id==36) {
                uint32_t value=bits(tail_output.value[valid-1])^1;memcpy(&tail_output.value[valid-1],&value,4);
            }
            memcpy(out+row,tail_output.value,valid*4);++count->tails;
        }
    }
    /* This reference output is never consumed by the candidate. */
    matmul(reference_output,x,w,n,d);
    for(unsigned row=0;row<(unsigned)d;++row)if(bits(out[row])!=bits(reference_output[row])) {
        projection_report[7]=row;stop(94);
    }
}
#include "projection.inc"

static void compare_state(RunState *a,RunState *b) {
    struct full_span left[16],right[16];full_spans(a,left);full_spans(b,right);
    for(unsigned span=0;span<16;++span) {
        projection_report[8]=span;
        for(size_t i=0;i<left[span].bytes;++i)if(left[span].data[i]!=right[span].data[i]) {
            projection_report[9]=i;stop(95);
        }
    }
}
int team_forward_main(void) {
    projection_report[0]=UINT64_C(0x523250524f4a3031);projection_report[1]=1;projection_report[2]=3;projection_report[3]=1;
    check(sizeof(struct full_storage)==FULL_STATE_BYTES && sizeof(float)==4,96);
    uintptr_t status,vlenb;__asm__ volatile("csrr %0,mstatus\ncsrr %1,vlenb":"=r"(status),"=r"(vlenb));
    check((status&0x6000)!=0 && (status&0x600)!=0 && vlenb==16,96);projection_report[14]=status;projection_report[15]=vlenb;
    check(errno==0,97);for(unsigned i=0;i<16;++i) {team_tls_area[i]=0x6b;team_tls_area[80+i]=0xa7;}tls_check();GS=32;
    transforms[0].config=(Config){D,H,L,6,6,V,S};weights(&transforms[0].weights);
    for(unsigned m=0;m<3;++m) {transforms[m].config=transforms[0].config;transforms[m].weights=transforms[0].weights;full_bind_state(&transforms[m].state,&storage[m]);}
    prepare();const int tokens[]={1,7,19};
    for(position=0;position<3;++position) {
        projection_report[4]=position;
        for(method=0;method<3;++method) {
            projection_report[5]=method;count=&projection_counts[position][method];errno=12345;
            __asm__ volatile("csrwi fcsr,0" ::: "memory");
            Transformer *t=&transforms[method];
            float *logits=method?projection_forward(t,tokens[position],(int)position):forward(t,tokens[position],(int)position);
            check(logits==t->state.logits && errno==12345 && fcsr()>>5==0,98);tls_check();
            projection_report[16+position*3+method]=fcsr();
            if(method)check(count->quant_calls==25 && count->quant_groups==315 && count->quant_elements==10080 &&
                count->matmuls==43 && count->routed==37 && count->scalar==6 && count->blocks==172 && count->tails==13,99);
            check(full_save_state(&t->state,projection_snapshots[position][method])==FULL_STATE_BYTES,100);
            if(method)compare_state(&transforms[0].state,&t->state);
        }
        projection_report[10]=position+1;
    }
    projection_report[11]=projection_control;projection_report[3]=0;return 0;
}
