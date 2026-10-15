/* Real C judge, exhaustive bit corruption of both 32 x 128-bit snapshots. */
#include "harness.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void check(int ok) { if (!ok) { fputs("JUDGE_REJECT\n",stderr); exit(1); } }
int main(void) {
  unsigned char storage[32*16+8] __attribute__((aligned(8)));
  unsigned char expected[32][16] __attribute__((aligned(8)));
  struct trap_record r={0};
  struct expectation e={{0,8,0,3,1,0,0,1},0,expected,expected};
  r.pre=(struct vector_csrs){0,8,0,3,1,7};r.post=r.pre;
  r.pre_status=0x200;r.raw_status=0x600;r.phase=1;r.pre_valid=1;
  for(unsigned i=0;i<512;++i) ((unsigned char*)expected)[i]=(unsigned char)(i*37);
  memcpy(r.pre_regs,expected,512);
  unsigned checks=0;
  for(unsigned align=0;align<8;++align) {
    unsigned char (*actual)[16]=(void*)(storage+align);memcpy(actual,expected,512);
    check(judge(&r,&e,actual,1)==PASS);++checks;
    for(unsigned bit=0;bit<4096;++bit) {
      unsigned reg=bit/128,byte=(bit%128)/8,mask=1U<<(bit%8);
      actual[reg][byte]^=mask;
      check(judge(&r,&e,actual,1)==VECTOR_CHANGED);++checks;
      check(judge_with_scratch(&r,&e,actual,1,UINT32_C(1)<<reg,0)==PASS);++checks;
      actual[reg][byte]^=mask;
      r.pre_regs[reg][byte]^=mask;
      check(judge_with_scratch(&r,&e,actual,1,UINT32_MAX,0)==PRE_VECTOR_CHANGED);++checks;
      r.pre_regs[reg][byte]^=mask;
    }
  }
  for(unsigned field=0;field<6;++field) {
    ((uint64_t*)&r.post)[field]^=1;
    check(judge(&r,&e,expected,1)==CSR_CHANGED);++checks;
    ((uint64_t*)&r.post)[field]^=1;
  }
  r.trap_count=1;r.cause=2;r.epc=r.expected_pc=0x80000100;e.cause=2;
  struct vector_csrs fault=r.pre;fault.vl=7;r.post=fault;
  check(judge(&r,&e,expected,1)==CSR_CHANGED);++checks;
  check(judge_with_scratch(&r,&e,expected,1,0,&fault)==PASS);++checks;
  r.epc+=4;check(judge_with_scratch(&r,&e,expected,1,0,&fault)==FAULT_PC);++checks;
  printf("T12_JUDGE_PASS checks=%u\n",checks);
  return 0;
}
