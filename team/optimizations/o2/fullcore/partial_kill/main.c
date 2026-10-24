#include <stdint.h>
#include "cases.h"
extern void _putc(char);
static struct {
  uint8_t before[16];
  uint8_t values[TRIALS][32][16];
  uint8_t after[16];
} output __attribute__((aligned(16)));
static void text(const char *s) { while (*s) _putc(*s++); }
static void dec(unsigned value) {
  char buf[12]; unsigned n=0;
  do { buf[n++]='0'+value%10; value/=10; } while (value);
  while (n) _putc(buf[--n]);
}
int main(void) {
  __asm__ volatile("li t0,0x6600; csrs mstatus,t0; csrwi vstart,0; csrwi vcsr,7; csrwi fcsr,0" ::: "t0","memory");
  text("PARTIAL_V2_BEGIN groups=8 trials=128\n");
  for (unsigned g=0;g<GROUPS;++g) {
    const uint8_t *want=(const uint8_t *)expected[g];
    uint8_t *got=(uint8_t *)output.values;
    /* Identical goldens across groups must not allow stale stores to pass. */
    for (unsigned i=0;i<sizeof(output.values);++i) got[i]=want[i]^0xff;
    for (unsigned i=0;i<16;++i) output.before[i]=output.after[i]=0xa5;
    entries[g](input,output.values,&trials[g*TRIALS]);
    for (unsigned i=0;i<16;++i) if (output.before[i]!=0xa5 || output.after[i]!=0xa5) {
      text("PARTIAL_V2_FAIL guard\n");return 3;
    }
    for (unsigned i=0;i<sizeof(output.values);++i) if (got[i]!=want[i]) {
      text("PARTIAL_V2_FAIL group=");dec(g);text(" byte=");dec(i);_putc('\n');return 1;
    }
    uint64_t vl,vtype,vstart,vcsr,fflags;
    __asm__ volatile("csrr %0,vl; csrr %1,vtype; csrr %2,vstart; csrr %3,vcsr; csrr %4,fflags"
                     :"=r"(vl),"=r"(vtype),"=r"(vstart),"=r"(vcsr),"=r"(fflags));
    if (vl!=8 || vtype || vstart || vcsr!=7 || fflags) { text("PARTIAL_V2_FAIL csr\n");return 2; }
    text("PARTIAL_V2_GROUP_PASS id=");dec(g);text(" trials=16 register_bytes=8192 csr_fields=5\n");
  }
  text("PARTIAL_V2_SUMMARY groups=8 trials=128 register_bytes=65536 failures=0\n");
  return 0;
}
