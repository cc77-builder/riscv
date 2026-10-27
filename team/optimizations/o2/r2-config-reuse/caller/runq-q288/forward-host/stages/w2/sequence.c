/* Full supported sequence: original scalar and the two cached vector methods.
 * This harness links the already-qualified consumer-w2.o without recompiling it.
 * Complete state comparisons are outside the core and are not performance data.
 */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "consumer_w2.h"

extern unsigned char fixture_weights[],fixture_weights_end[],fixture_embedding[],fixture_embedding_end[];
extern unsigned char fixture_packed[],fixture_packed_end[],fixture_tail_scales[],fixture_tail_scales_end[];
extern unsigned char fixture_w2_packed[],fixture_w2_packed_end[];
extern unsigned char fixture_prefix_gold[],fixture_prefix_gold_end[];
__thread int errno;
uintptr_t __stack_chk_guard=UINT64_C(0x9157a6c2d384ef09);
unsigned char team_tls_area[96] __attribute__((aligned(16)));
volatile uint32_t sequence_control[2]={0,256};
volatile uint64_t sequence_report[64];
struct guarded_state { uint64_t before[2];struct r2_consumer_state state;uint64_t after[2]; };
struct guarded_state sequence_states[3] __attribute__((aligned(16)));
uint64_t sequence_flags[256][3];
int32_t sequence_tokens[256];
static const uint64_t guard=UINT64_C(0xb5e9c13f6a0742d8);
static const enum r2_consumer_method methods[3]={R2_SCALAR,R2_FR_CACHE,R2_TA_CACHE};
_Static_assert(sizeof(struct r2_consumer_state)==R2_CONSUMER_STATE_BYTES,"fixed complete state");
_Static_assert(R2_CONSUMER_STATE_BYTES%8==0,"complete word comparison");

__attribute__((noreturn)) static void stop(unsigned code) {
    sequence_report[3]=code;
    __asm__ volatile("mv a0,%0\n.word 0x0005006b"::"r"((uintptr_t)code):"a0","memory");
    for(;;) {}
}
__attribute__((noreturn)) void __stack_chk_fail(void) {stop(90);}
static void check(int ok,unsigned code) {if(!ok)stop(code);}
static unsigned fcsr(void) {unsigned value;__asm__ volatile("csrr %0,fcsr":"=r"(value));return value;}
static void guards(void) {
    for(unsigned i=0;i<3;++i)for(unsigned j=0;j<2;++j)
        check(sequence_states[i].before[j]==guard && sequence_states[i].after[j]==guard,91);
    for(unsigned i=0;i<16;++i)check(team_tls_area[i]==0x6b && team_tls_area[80+i]==0xa7,92);
}
__attribute__((noinline,noclone)) static void compare(const void *left,const void *right,unsigned method,unsigned code) {
    const unsigned char *a=__builtin_assume_aligned(left,8);
    const unsigned char *b=__builtin_assume_aligned(right,8);
    for(size_t i=0;i<R2_CONSUMER_STATE_BYTES;i+=8) {
        uint64_t x,y;
        /* Explicit builtins preserve aliasing and remain inline under the
         * inherited -fno-builtin flag. Both fixed spans are 16-byte aligned. */
        __builtin_memcpy(&x,a+i,8);__builtin_memcpy(&y,b+i,8);
        if(x!=y) {
            for(unsigned j=0;j<8;++j)if(a[i+j]!=b[i+j]) {
                sequence_report[9]=i+j;sequence_report[12]=method;stop(code);
            }
            stop(96);
        }
    }
}
int team_forward_main(void) {
    unsigned negative=sequence_control[0],positions=sequence_control[1];
    sequence_report[0]=UINT64_C(0x5232573253455131);sequence_report[1]=1;
    sequence_report[2]=negative;sequence_report[3]=1;sequence_report[4]=positions;
    check(negative<=1 && positions==256,80);
    uintptr_t status,vlenb,tp,address;
    __asm__ volatile("csrr %0,mstatus\ncsrr %1,vlenb\nmv %2,tp":"=r"(status),"=r"(vlenb),"=r"(tp));
    __asm__ volatile("mv %0,%1":"=r"(address):"r"(&errno));
    check((status&0x6000)!=0 && (status&0x600)!=0 && vlenb==16 && errno==0,81);
    check(tp==(uintptr_t)(team_tls_area+16) && address==tp+FULL_ERRNO_OFFSET,82);
    sequence_report[10]=status;sequence_report[11]=vlenb;
    check(fixture_prefix_gold_end-fixture_prefix_gold==3*R2_CONSUMER_STATE_BYTES,83);
    for(unsigned i=0;i<16;++i){team_tls_area[i]=0x6b;team_tls_area[80+i]=0xa7;}
    for(unsigned i=0;i<3;++i)for(unsigned j=0;j<2;++j)
        sequence_states[i].before[j]=sequence_states[i].after[j]=guard;
    check(r2_w2_init(fixture_weights,fixture_weights_end-fixture_weights,
        fixture_embedding,fixture_embedding_end-fixture_embedding,
        fixture_packed,fixture_packed_end-fixture_packed,
        fixture_tail_scales,fixture_tail_scales_end-fixture_tail_scales,
        fixture_w2_packed,fixture_w2_packed_end-fixture_w2_packed)==0,84);
    for(unsigned i=0;i<3;++i)r2_w2_reset(&sequence_states[i].state);
    for(unsigned pos=0;pos<positions;++pos) {
        int token=pos==0?1:pos==1?7:pos==2?19:(int)((pos*7919u+1u)%32000u);
        sequence_report[5]=pos;sequence_tokens[pos]=token;
        for(unsigned which=0;which<3;++which) {
            errno=12345;__asm__ volatile("csrwi fcsr,0":::"memory");
            struct r2_consumer_state *state=&sequence_states[which].state;
            float *logits=r2_w2_forward(state,methods[which],token,(int)pos);
            unsigned flags=fcsr();sequence_flags[pos][which]=flags;
            ++sequence_report[7];
            check(logits==state->logits && errno==12345 && flags>>5==0,85);
            guards();
        }
        check(sequence_flags[pos][0]==sequence_flags[pos][1] && sequence_flags[pos][0]==sequence_flags[pos][2],93);
        if(pos<3) {
            compare(&sequence_states[0].state,fixture_prefix_gold+(size_t)pos*R2_CONSUMER_STATE_BYTES,R2_SCALAR,95);
            ++sequence_report[16];
        }
        if(negative && pos==0) {
            unsigned char *last=(unsigned char*)&sequence_states[2].state.logits[31999];
            last[0]^=1;
        }
        for(unsigned which=1;which<3;++which) {
            compare(&sequence_states[0].state,&sequence_states[which].state,methods[which],94);
            ++sequence_report[8];
        }
        sequence_report[6]=pos+1;
    }
    for(unsigned which=0;which<3;++which) {
        check(r2_w2_forward(&sequence_states[which].state,methods[which],1,256)==NULL,86);
        ++sequence_report[14];
    }
    guards();
    check(sequence_report[6]==256 && sequence_report[7]==768 && sequence_report[8]==512 &&
          sequence_report[14]==3 && sequence_report[16]==3,87);
    sequence_report[3]=0;return 0;
}
