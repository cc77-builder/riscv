#include "contract.h"
#include "cases.h"
extern void _putc(char);
static struct o2c_result result __attribute__((aligned(16)));
static void text(const char *s) { while (*s) _putc(*s++); }
static void decimal(uint64_t x) {
  char b[24]; unsigned n = 0;
  do { b[n++] = '0' + x % 10; x /= 10; } while (x);
  while (n) _putc(b[--n]);
}
static void init_csrs(void) {
  __asm__ volatile("li t0,0x6600\n csrs mstatus,t0\n csrwi vstart,0\n"
                   "vsetivli zero,8,e8,m1,tu,mu\n csrwi vcsr,7\n csrwi fcsr,0x0\n"
                   "li t0,0x60\n csrw fcsr,t0" ::: "t0", "memory");
}
int main(void) {
  init_csrs();
  text("OC19_BEGIN calls=41 custom=77 phases=0,1,2,4\n");
  for (unsigned i = 0; i < O2C_CALL_COUNT; ++i) {
    const struct o2c_case *c = &o2c_cases[i];
    text("OC19_CALL seq="); decimal(i); text(" phase="); decimal(c->phase);
    text(" stage="); text(c->stage); text(" probe="); decimal(c->probe); _putc('\n');
    c->kernel(o2c_input, &result, &c->trial);
    unsigned error = o2c_judge(&result, o2c_dot,
        c->probe || i == 0 ? o2c_sentinel : o2c_dot,
        i == 0 ? 0 : 0x40600000, c->trial.flags);
    if (error) {
      text("OC19_FAIL seq="); decimal(i); text(" error="); decimal(error); _putc('\n');
      return 1;
    }
    text("OC19_PASS seq="); decimal(i); _putc('\n');
  }
  text("OC19_SUMMARY calls=41 custom=77\n");
  return 0;
}
