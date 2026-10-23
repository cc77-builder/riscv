#include <stdint.h>
#include <stddef.h>
#include "cases.h"

extern void _putc(char);

struct result {
  uint64_t cycle_begin, cycle_end, instret_begin, instret_end, iterations;
  uint64_t csr[7];
  uint64_t reserved[4];
  unsigned char regs[32][16];
};
_Static_assert(offsetof(struct result, regs) == 128, "assembly result layout");
static const uint64_t canary = UINT64_C(0xd15ea5e5cafebabe);
static struct {
  uint64_t head[2];
  struct result value;
  uint64_t tail[2];
} observed __attribute__((aligned(16), section(".benchmark.result")));
static struct {
  uint64_t head[2];
  unsigned char value[64][16];
  uint64_t tail[2];
} sink __attribute__((aligned(16), section(".benchmark.sink")));

static void text(const char *s) { while (*s) _putc(*s++); }
static void decimal(uint64_t x) {
  char buf[21]; unsigned n = 0;
  do { buf[n++] = (char)('0' + x % 10); x /= 10; } while (x);
  while (n) _putc(buf[--n]);
}
#if !T13_COMPACT
static void vector(const unsigned char *p) {
  for (int i = 15; i >= 0; --i) {
    _putc("0123456789abcdef"[p[i] >> 4]);
    _putc("0123456789abcdef"[p[i] & 15]);
  }
}
#endif
static void fill(void *ptr, unsigned n, unsigned char value) {
  unsigned char *p = ptr;
  if (((uintptr_t)p & 7) == 0) {
    const uint64_t wide = UINT64_C(0x0101010101010101) * value;
    while (n >= 8) { __builtin_memcpy(p, &wide, 8); p += 8; n -= 8; }
  }
  while (n--) *p++ = value;
}
static int equal(const void *aa, const void *bb, unsigned n) {
  const unsigned char *a = aa, *b = bb;
  if ((((uintptr_t)a | (uintptr_t)b) & 7) == 0) {
    while (n >= 8) {
      uint64_t x, y;
      __builtin_memcpy(&x, a, 8); __builtin_memcpy(&y, b, 8);
      if (x != y) return 0;
      a += 8; b += 8; n -= 8;
    }
  }
  while (n--) if (*a++ != *b++) return 0;
  return 1;
}
static int guards(void) {
  return observed.head[0] == canary && observed.head[1] == canary &&
         observed.tail[0] == canary && observed.tail[1] == canary &&
         sink.head[0] == canary && sink.head[1] == canary &&
         sink.tail[0] == canary && sink.tail[1] == canary;
}
static unsigned judge(const struct t13_case *c) {
  const struct result *r = &observed.value;
  if (!guards()) return 1;
  if (r->iterations != c->iterations) return 2;
  const uint64_t wanted[] = {c->vtype, 8, 0, 3, 1, 7};
  if (!equal(r->csr, wanted, sizeof(wanted))) return 3;
  if (r->csr[6] & 5) return 4;
  for (unsigned reg = 0; reg < 32; ++reg)
    if (!(c->scratch & (1U << reg)) && !equal(r->regs[reg], c->expected[reg], 16))
      return 100 + reg;
  for (unsigned i = 0; i < c->stream_count; ++i)
    if (!equal(sink.value[i], c->outputs[i], 16)) return 200 + i;
  for (unsigned i = c->stream_count; i < 64; ++i) {
    uint64_t lo, hi;
    __builtin_memcpy(&lo, sink.value[i], 8);
    __builtin_memcpy(&hi, sink.value[i] + 8, 8);
    if (lo != UINT64_C(0xa6a6a6a6a6a6a6a6) || hi != lo) return 500;
  }
  return 0;
}
static unsigned run_controls(const struct t13_case *c) {
  struct result *r = &observed.value;
  unsigned ok = 0;
  r->regs[c->dest][0] ^= 1; ok += judge(c) != 0; r->regs[c->dest][0] ^= 1;
  r->regs[c->dest][15] ^= 0x80; ok += judge(c) != 0; r->regs[c->dest][15] ^= 0x80;
  unsigned other = c->dest == 15 ? 14 : 15;
  r->regs[other][5] ^= 1; ok += judge(c) != 0; r->regs[other][5] ^= 1;
  r->csr[1] ^= 1; ok += judge(c) != 0; r->csr[1] ^= 1;
  r->iterations ^= 1; ok += judge(c) != 0; r->iterations ^= 1;
  sink.tail[1] ^= 1; ok += judge(c) != 0; sink.tail[1] ^= 1;
  text("T13_CONTROLS detected="); decimal(ok); text(" expected=6\n");
  return ok == 6 && judge(c) == 0;
}
int main(void) {
  text("T13_BEGIN suite="); text(T13_SUITE);
  text(" dataset="); decimal(T13_DATASET);
  text(" plan="); decimal(T13_PLAN_COUNT);
  text(" contract="); text(O3_CONTRACT); _putc('\n');
  unsigned scratch_control = 0;
  for (unsigned seq = 0; seq < T13_PLAN_COUNT; ++seq) {
    const struct t13_case *c = &cases[plan[seq].index];
    fill(&observed, sizeof(observed), 0);
    fill(sink.value, sizeof(sink.value), 0xa6);
    observed.head[0] = observed.head[1] = observed.tail[0] = observed.tail[1] = canary;
    sink.head[0] = sink.head[1] = sink.tail[0] = sink.tail[1] = canary;
    c->entry(c->before, &observed.value, c->stream, sink.value);
    unsigned verdict = judge(c);
    if (verdict) {
      text("T13_FAIL seq="); decimal(seq); text(" verdict="); decimal(verdict); _putc('\n');
      return 1;
    }
    if (seq == 0 && !run_controls(c)) return 2;
    if (!scratch_control && c->scratch) {
      unsigned reg = 0;
      while (!(c->scratch & (1U << reg))) ++reg;
      observed.value.regs[reg][7] ^= 0x80;
      unsigned allowed = judge(c) == 0;
      observed.value.regs[reg][7] ^= 0x80;
      text("T13_SCRATCH_CONTROL allowed="); decimal(allowed); _putc('\n');
      if (!allowed) return 3;
      scratch_control = 1;
    }
    const struct result *r = &observed.value;
#if T13_COMPACT
    /* Full byte/state checks above are unchanged; only UART serialization is
       compact. Raw absolute values remain in the hardware CSR trace. */
    text("T13_P seq="); decimal(seq);
    text(" c="); decimal(r->cycle_end - r->cycle_begin);
    text(" i="); decimal(r->instret_end - r->instret_begin); _putc('\n');
#else
    text("T13_CASE seq="); decimal(seq); text(" id="); text(c->id);
    text(" phase="); text(plan[seq].phase); text(" repeat="); decimal(plan[seq].repeat);
    text(" result=PASS cycles="); decimal(r->cycle_begin); _putc(','); decimal(r->cycle_end);
    text(" instret="); decimal(r->instret_begin); _putc(','); decimal(r->instret_end);
    text(" iterations="); decimal(r->iterations);
    text(" csr=");
    for (unsigned i = 0; i < 7; ++i) { if (i) _putc('/'); decimal(r->csr[i]); }
    text(" dest="); vector(r->regs[c->dest]);
    text(" checked_regs=");
    unsigned checked = 0;
    for (unsigned reg = 0; reg < 32; ++reg) checked += !(c->scratch & (1U << reg));
    decimal(checked); text(" stream_checked="); decimal(c->stream_count); _putc('\n');
#endif
  }
  text("T13_SUMMARY executed="); decimal(T13_PLAN_COUNT);
  text(" failures=0 scratch_control="); decimal(scratch_control); _putc('\n');
  return 0;
}
