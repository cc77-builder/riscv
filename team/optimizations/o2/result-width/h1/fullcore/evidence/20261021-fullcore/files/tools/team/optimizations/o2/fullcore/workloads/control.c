#include <stdint.h>
#include "cases.h"
extern void _putc(char);
static uint8_t actual[16][32][16] __attribute__((aligned(16)));
static void text(const char *s) { while (*s) _putc(*s++); }
static void dec(unsigned value) {
  char buf[12]; unsigned n = 0;
  do { buf[n++] = '0' + value % 10; value /= 10; } while (value);
  while (n) _putc(buf[--n]);
}
int main(void) {
  __asm__ volatile("li t0,0x6600; csrs mstatus,t0; csrwi vstart,0; csrwi vcsr,7; csrwi fcsr,0" ::: "t0","memory");
  text("O2_CONTROL_BEGIN groups=16 trials=256 contract=vdot-s8x8-r32-v0.1\n");
  for (unsigned g = 0; g < O2_CONTROL_GROUPS; ++g) {
    entries[g](input,actual,&trials[g*16]);
    const uint8_t *got = (const uint8_t *)actual;
    const uint8_t *want = (const uint8_t *)expected[g];
    for (unsigned i = 0; i < sizeof(actual); ++i) if (got[i] != want[i]) {
      text("O2_CONTROL_FAIL group="); dec(g); text(" byte="); dec(i); _putc('\n'); return 1;
    }
    text("O2_CONTROL_GROUP_PASS id="); dec(g); text(" trials=16 register_bytes=8192\n");
  }
  uint64_t vl, vtype, vstart, vcsr, fflags;
  __asm__ volatile("csrr %0,vl; csrr %1,vtype; csrr %2,vstart; csrr %3,vcsr; csrr %4,fflags"
                   : "=r"(vl),"=r"(vtype),"=r"(vstart),"=r"(vcsr),"=r"(fflags));
  if (vl != 8 || vtype || vstart || vcsr != 7 || fflags) {
    text("O2_CONTROL_FAIL csr\n"); return 2;
  }
  text("O2_CONTROL_SUMMARY groups=16 trials=256 register_bytes=131072 failures=0\n");
  return 0;
}
