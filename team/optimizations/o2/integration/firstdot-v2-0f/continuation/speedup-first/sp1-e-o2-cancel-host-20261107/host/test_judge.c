#include "contract.h"
#include <stdio.h>
#include <string.h>
#include <inttypes.h>
static unsigned checks;
static int expect(unsigned actual, unsigned wanted, const char *name) {
  ++checks;
  if (actual != wanted) { fprintf(stderr, "HOST_JUDGE_FAIL %s got=%u expected=%u\n", name, actual, wanted); return 1; }
  return 0;
}
int main(void) {
  int64_t sum = 0;
  uint8_t reference[16] = {0};
  for (unsigned i=0;i<8;i++) {
    int x=o2c_input[i], y=o2c_input[16+i];
    if (x>=128) x-=256;
    if (y>=128) y-=256;
    sum += x*y;
  }
  uint32_t low=(uint32_t)sum;
  for (unsigned i=0;i<4;i++) reference[i]=(low>>(8*i))&255;
  if (memcmp(reference,o2c_dot,16)) return 2;
  if (memcmp(o2c_input+32,o2c_sentinel,16)) return 3;
  if (UINT64_C(0x8000000000003039)/3 != UINT64_C(0x2aaaaaaaaaaababd)) return 4;
  float f=7.0f/2.0f; uint32_t bits; memcpy(&bits,&f,4);
  if (bits!=UINT32_C(0x40600000) || (bits&255)!=0) return 5;
  for (unsigned phase=0;phase<=4;phase++) {
    if (phase==3) continue;
    uint64_t x=bits&255;
    for (unsigned j=0;j<phase;j++) {x^=1;x^=1;}
    if (x) return 6;
  }
  for (unsigned mode=0;mode<2;mode++) {
    const uint8_t *b=mode?o2c_sentinel:reference;
    struct o2c_result good={0};
    memcpy(good.a,reference,16);memcpy(good.b,b,16);
    memcpy(good.before,o2c_caller_csrs,sizeof(good.before));
    memcpy(good.after,o2c_caller_csrs,sizeof(good.after));
    good.fp_bits=bits;good.flags=mode+10;
    if (expect(o2c_judge(&good,reference,b,bits,mode+10),0,"positive")) return 7;
    for (unsigned side=0;side<2;side++) for(unsigned bit=0;bit<128;bit++) {
      struct o2c_result bad=good;
      uint8_t *dst=side?bad.b:bad.a;
      dst[bit/8]^=1u<<(bit%8);
      if(expect(o2c_judge(&bad,reference,b,bits,mode+10),side?2:1,"full128_bit"))return 8;
    }
    for (unsigned side=0;side<2;side++) for(unsigned csr=0;csr<5;csr++) {
      struct o2c_result bad=good;
      uint64_t *dst=side?bad.after:bad.before;dst[csr]^=1;
      if(expect(o2c_judge(&bad,reference,b,bits,mode+10),side?8:4,"csr"))return 9;
    }
    struct o2c_result bad=good;bad.fp_bits^=1;
    if(expect(o2c_judge(&bad,reference,b,bits,mode+10),16,"fp"))return 10;
    bad=good;bad.flags^=1;
    if(expect(o2c_judge(&bad,reference,b,bits,mode+10),32,"call_identity"))return 11;
  }
  printf("HOST_JUDGE_PASS checks=%u numeric_sum=%" PRId64 " full128=true csr_slots=5 target_execution=false\n",checks,sum);
  return 0;
}
