#include <stdint.h>
#include <klib.h>
#include "sequences.h"
static uint8_t actual[32][32][16] __attribute__((aligned(16)));
static uint64_t csr[512];
static uint8_t speculative[256][16] __attribute__((aligned(16)));
static unsigned errors;
static void check(unsigned group, const uint8_t *want, unsigned size) {
  const uint8_t *got=(const uint8_t *)actual;
  for (unsigned i=0;i<size;++i) if(got[i]!=want[i]) {
    printf("T12_MISMATCH group=%d byte=%d actual=%d expected=%d\n",group,i,got[i],want[i]);
    ++errors; return;
  }
  printf("T12_GROUP_PASS id=%d checkpoints=32 bytes=%d\n",group,size);
}
int main(void) {
  __asm__ volatile("li t0,0x6600; csrs mstatus,t0; csrwi vstart,0; csrwi vcsr,0" ::: "t0","memory");
  printf("T12_BEGIN seed=0x20261014 contract=vdot-s8x8-r32-v0.1\n");
  t12_group0(input0,actual,csr); check(0,(const uint8_t *)expected0,sizeof(expected0));
  t12_group1(input1,actual,csr); check(1,(const uint8_t *)expected1,sizeof(expected1));
  for(unsigned i=0;i<512;++i) if(csr[i]!=(i/16+i%16)%8) { ++errors; printf("T12_CSR_FAIL index=%d\n",i); break; }
  t12_group2(input2,actual,csr); check(2,(const uint8_t *)expected2,sizeof(expected2));
  t12_group3(input3,actual,csr); check(3,(const uint8_t *)expected3,sizeof(expected3));
  t12_speculate(spec_input,speculative,(void *)spec_trials);
  for(unsigned i=0;i<sizeof(speculative);++i) if(((uint8_t *)speculative)[i]!=((const uint8_t *)spec_expected)[i]) {
    ++errors; printf("T12_SPEC_FAIL byte=%d\n",i); break;
  }
  printf("T12_SUMMARY groups=4 checkpoints=128 speculative_attempts=256 failures=%d\n",errors);
  return errors ? 1 : 0;
}
