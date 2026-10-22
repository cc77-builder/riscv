#include <stdint.h>
#include "cases.h"
extern void _putc(char);
static uint8_t actual[32][16] __attribute__((aligned(16)));
static uint64_t control[7];
static void text(const char *s) { while (*s) _putc(*s++); }
static void dec(unsigned value) {
  char buf[12]; unsigned n = 0;
  do { buf[n++] = '0' + value % 10; value /= 10; } while (value);
  while (n) _putc(buf[--n]);
}
static unsigned judge(const struct diag_case *c) {
  const unsigned char *a = (const unsigned char *)actual;
  const unsigned char *b = (const unsigned char *)c->expected;
  for (unsigned i = 0; i < sizeof(actual); ++i) if (a[i] != b[i]) return i + 1;
  const uint64_t want[7] = {0, 8, 0, 3, 1, 7, 0};
  for (unsigned i = 0; i < 7; ++i) if (control[i] != want[i]) return 1000 + i;
  return 0;
}
int main(void) {
  text("O2_DIAG_BEGIN cases=10 fixed_dots=128 contract=vdot-s8x8-r32-v0.1\n");
  unsigned total = 0;
  for (unsigned i = 0; i < O2_DIAG_CASES; ++i) {
    const struct diag_case *c = &cases[i];
    c->entry(c->before, actual, control);
    unsigned verdict = judge(c);
    if (verdict) {
      text("O2_DIAG_FAIL case="); dec(i); text(" verdict="); dec(verdict); _putc('\n'); return 1;
    }
    if (i == 0) {
      actual[16][15] ^= 0x80;
      unsigned detected = judge(c) != 0;
      actual[16][15] ^= 0x80;
      if (!detected || judge(c)) return 2;
      text("O2_DIAG_CHECKER_CONTROL highbit_detected=1\n");
    }
    total += c->dots;
    text("O2_DIAG_CASE_PASS seq="); dec(i); text(" id="); text(c->id);
    text(" dots="); dec(c->dots); text(" register_bytes=512 csr_fields=7\n");
  }
  text("O2_DIAG_SUMMARY cases="); dec(O2_DIAG_CASES); text(" dots="); dec(total);
  text(" failures=0\n");
  return 0;
}
