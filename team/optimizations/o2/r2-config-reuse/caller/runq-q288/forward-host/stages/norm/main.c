#include <am.h>
#include <klib.h>
#include <stdint.h>
#include "norm.h"
#define CASES 48
#define GUARD UINT64_C(0x5a1d8c2976e340bf)
extern const float norm_input[CASES][288],norm_weight[CASES][288],norm_gold[CASES][288];
extern const uint32_t norm_expected_flags[CASES];
extern void rmsnorm(float *,float *,float *,int);
volatile uint32_t norm_control[2] __attribute__((section(".data"),used))={0,1};
unsigned char team_tls_area[96] __attribute__((aligned(16)));
__thread int errno;
volatile uint64_t norm_report[64],norm_samples[8][8],norm_flags[384];
float norm_results[384][288] __attribute__((aligned(64)));
struct guarded {uint64_t before[2];float data[288];uint64_t after[2];};
static struct guarded input,output,batch_x[13],batch_y[13];
static unsigned uart,negative,case_id,method,test_id;
static uintptr_t expected_vl,expected_vtype;
static unsigned fcsr(void){unsigned v;__asm__ volatile("csrr %0,fcsr":"=r"(v)::"memory");return v;}
static uint64_t cycle(void){uint64_t v;__asm__ volatile("fence iorw,iorw\nrdcycle %0\nfence iorw,iorw":"=r"(v)::"memory");return v;}
static uint64_t instret(void){uint64_t v;__asm__ volatile("fence iorw,iorw\nrdinstret %0\nfence iorw,iorw":"=r"(v)::"memory");return v;}
__attribute__((noreturn,noinline)) static void reject(const char *name,unsigned byte) {
    norm_report[3]=92;norm_report[8]=case_id;norm_report[9]=byte;
    if(uart)printf("NORM_REJECT case=%u method=%u name=%s byte=%u\n",case_id,method,name,byte);
    __asm__ volatile("li a0,92\n.word 0x0005006b":::"a0","memory");for(;;){}
}
static void check(int ok,const char *s){if(!ok)reject(s,0);}
static uint32_t word(float f){union {float f;uint32_t u;} u={.f=f};return u.u;}
static void compare(const float *a,const float *b,const char *name) {
    const unsigned char *left=(const unsigned char*)a,*right=(const unsigned char*)b;
    for(unsigned j=0;j<288;++j)if(word(a[j])!=word(b[j]))
        for(unsigned k=0;k<4;++k)if(left[j*4+k]!=right[j*4+k])reject(name,j*4+k);
}
static void tls_check(void) {
    uintptr_t tp;__asm__ volatile("mv %0,tp":"=r"(tp));
    check(tp==(uintptr_t)(team_tls_area+16)&&(uintptr_t)&errno==tp,"tls_identity");
    for(unsigned j=0;j<16;++j)check(team_tls_area[j]==0x6b&&team_tls_area[80+j]==0xa7,"tls_guard");
}
static void guard(struct guarded *b) {
    for(unsigned j=0;j<2;++j)b->before[j]=b->after[j]=GUARD;
}
static void guard_check(const struct guarded *b) {
    for(unsigned j=0;j<2;++j)check(b->before[j]==GUARD&&b->after[j]==GUARD,"guard");
}
static void environment(unsigned config,unsigned sticky) {
    if(config%3==0)__asm__ volatile("vsetivli zero,8,e8,m1,tu,mu":::"memory");
    else if(config%3==1)__asm__ volatile("vsetivli zero,3,e32,m2,tu,mu":::"memory");
    else __asm__ volatile("vsetivli zero,13,e16,m2,ta,ma":::"memory");
    __asm__ volatile("csrwi vstart,0\ncsrwi vcsr,7\ncsrw fcsr,%0"::"r"(sticky):"memory");
    __asm__ volatile("csrr %0,vl\ncsrr %1,vtype":"=r"(expected_vl),"=r"(expected_vtype)::"memory");
    errno=73;
}
static void environment_check(unsigned flags) {
    uintptr_t vl,vt,vs,vc;__asm__ volatile("csrr %0,vl\ncsrr %1,vtype\ncsrr %2,vstart\ncsrr %3,vcsr":
        "=r"(vl),"=r"(vt),"=r"(vs),"=r"(vc)::"memory");
    check(vl==expected_vl&&vt==expected_vtype&&vs==0&&vc==7,"vector_csr");
    check(fcsr()==flags,"fcsr");check(errno==73,"errno");tls_check();
}
__attribute__((noinline,noclone)) static void apply(unsigned which,float *out,float *x,const float *w) {
    void (*fn)(float*,float*,float*,int)=which?r2_rmsnorm_rvv:rmsnorm;
    fn(out,x,(float*)w,288);
}
static float *prepare(unsigned id,unsigned alias) {
    guard(&input);guard(&output);memcpy(input.data,norm_input[id],1152);memset(output.data,0xa5,1152);
    return alias?input.data:output.data;
}
static void functional(void) {
    for(case_id=0;case_id<CASES;++case_id)for(method=0;method<2;++method)
        for(unsigned alias=0;alias<2;++alias)for(unsigned sticky=0;sticky<2;++sticky) {
            float *out=prepare(case_id,alias);unsigned expected=norm_expected_flags[case_id]|(sticky?0x18u:0u);
            environment(case_id,sticky?0x18:0);apply(method,out,input.data,norm_weight[case_id]);
            environment_check(expected);compare(out,norm_gold[case_id],"result");
            if(!alias)compare(input.data,norm_input[case_id],"input");
            guard_check(&input);guard_check(&output);
            memcpy(norm_results[test_id],out,1152);norm_flags[test_id]=fcsr();++test_id;++norm_report[5];
        }
}
static void prepare_batch(void) {
    for(unsigned j=0;j<13;++j) {
        guard(&batch_x[j]);guard(&batch_y[j]);
        memcpy(batch_x[j].data,norm_input[26+j],1152);memset(batch_y[j].data,0xa5,1152);
    }
    environment(0,0);
}
__attribute__((noinline,noclone)) static void batch(unsigned which) {
    void (*fn)(float*,float*,float*,int)=which?r2_rmsnorm_rvv:rmsnorm;
    for(unsigned j=0;j<13;++j)fn(j==12?batch_x[j].data:batch_y[j].data,
        batch_x[j].data,(float*)norm_weight[26+j],288);
}
static uint64_t batch_check(void) {
    unsigned flags=0;uint64_t h=UINT64_C(14695981039346656037);
    for(unsigned j=0;j<13;++j) {
        case_id=26+j;float *out=j==12?batch_x[j].data:batch_y[j].data;
        compare(out,norm_gold[case_id],"batch");if(j<12)compare(batch_x[j].data,norm_input[case_id],"batch_input");
        guard_check(&batch_x[j]);guard_check(&batch_y[j]);flags|=norm_expected_flags[case_id];
        for(unsigned k=0;k<1152;++k)h=(h^((const unsigned char*)out)[k])*UINT64_C(1099511628211);
    }
    environment_check(flags);return h;
}
int team_forward_main(const char *args) {
    (void)args;negative=norm_control[0];uart=norm_control[1];
    norm_report[0]=UINT64_C(0x52324e4f524d3031);norm_report[1]=1;norm_report[2]=negative;norm_report[3]=1;norm_report[4]=uart;
    uintptr_t enable=0x2200,status,vlenb;
    __asm__ volatile("csrs mstatus,%2\ncsrr %0,mstatus\ncsrr %1,vlenb":"=r"(status),"=r"(vlenb):"r"(enable):"memory");
    check((status&0x6000)&&(status&0x600)&&vlenb==16&&negative<=1&&uart<=1,"initial");
    check(errno==0,"tls_initial");
    for(unsigned j=0;j<16;++j){team_tls_area[j]=0x6b;team_tls_area[80+j]=0xa7;}
    tls_check();
    norm_report[10]=status;norm_report[11]=vlenb;
    if(uart)printf("NORM_BEGIN real=39 synthetic=9 size=288 control=%u\n",negative);
    if(negative) {
        case_id=38;method=1;float *out=prepare(case_id,1);environment(0,0);
        apply(method,out,input.data,norm_weight[case_id]);environment_check(norm_expected_flags[case_id]);
        ((unsigned char*)out)[1151]^=1;
        compare(out,norm_gold[case_id],"result");reject("negative_not_caught",0);
    }
    functional();check(test_id==384,"functional_count");
    if(uart)printf("NORM_FUNCTIONAL_PASS cases=48 calls=384 alias=both sticky=both\n");
    const unsigned order[8]={0,1,1,0,1,0,0,1};
    for(unsigned sample=0;sample<8;++sample) {
        method=order[sample];prepare_batch();batch(method);batch_check();++norm_report[7];
        prepare_batch();uint64_t c0=cycle(),i0=instret();batch(method);uint64_t i1=instret(),c1=cycle();unsigned flags=fcsr();
        uint64_t hash=batch_check();
        check(c1>c0&&i1>i0&&c1-c0<UINT32_MAX&&i1-i0<UINT32_MAX,"counter");
        norm_samples[sample][0]=method;norm_samples[sample][1]=c0;norm_samples[sample][2]=i0;norm_samples[sample][3]=i1;
        norm_samples[sample][4]=c1;norm_samples[sample][5]=flags;norm_samples[sample][6]=hash;++norm_report[6];
        if(uart)printf("NORM_SAMPLE %u %u %u %u %u %08x%08x\n",sample,method,(unsigned)(c1-c0),(unsigned)(i1-i0),flags,(unsigned)(hash>>32),(unsigned)hash);
    }
    norm_report[3]=0;if(uart)printf("NORM_PASS functional=384 samples=8 batch_calls=208\n");return 0;
}
