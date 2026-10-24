/* Test-only reference wrapper: corrupt bit64 of the admitted first VDOT's
 * returned COPY. The underlying reference state and every other byte stay intact.
 * Build with the authenticated REF_SO, TARGET_PC and TARGET_WORD. */
#include <dlfcn.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if !defined(REF_SO) || !defined(TARGET_PC) || !defined(TARGET_WORD)
#error "Explicit authenticated reference and decoded target required"
#endif
#define STATE_BYTES 1400u
#define PC_OFFSET 656u
#define VECTOR_OFFSET 800u
static void (*ref_exec)(uint64_t);
static void (*ref_regcpy)(void *, bool);
static void (*ref_memcpy)(uint64_t, void *, size_t, bool);
static void *handle;
static bool pending, injected;

static void fail(const char *reason) {
  fprintf(stderr, "NEGATIVE_FIXTURE_SETUP_FAIL %s\n", reason);
  abort();
}
static void *symbol(const char *name) {
  void *value = dlsym(handle, name);
  if (!value) fail(name);
  return value;
}
__attribute__((constructor)) static void configure(void) {
  handle = dlopen(REF_SO, RTLD_NOW | RTLD_LOCAL);
  if (!handle) fail("reference load");
  if (*(const unsigned *)symbol("DIFFTEST_REG_SIZE") != STATE_BYTES) fail("ABI size");
  ref_exec = (void (*)(uint64_t))symbol("difftest_exec");
  ref_regcpy = (void (*)(void *, bool))symbol("difftest_regcpy");
  ref_memcpy = (void (*)(uint64_t, void *, size_t, bool))symbol("difftest_memcpy");
  if (((TARGET_WORD >> 7) & 31u) != 0u || (TARGET_WORD & 0xfe00707fu) != 0x0200000bu)
    fail("admitted v0 instruction required");
}
void difftest_exec(uint64_t count) {
  if (injected || count != 1) { ref_exec(count); return; }
  unsigned char state[STATE_BYTES];
  uint64_t pc;
  uint32_t word = 0;
  ref_regcpy(state, false);
  memcpy(&pc, state + PC_OFFSET, sizeof(pc));
  if (pc >= UINT64_C(0x80000000) && pc < UINT64_C(0x88000000))
    ref_memcpy(pc, &word, sizeof(word), false);
  ref_exec(count);
  if ((word & 0xfe00707fu) == 0x0200000bu) {
    if (pending || pc != TARGET_PC || word != TARGET_WORD) fail("wrong first custom target");
    pending = true;
  }
}
static void dump(const char *label, const unsigned char *state) {
  fprintf(stderr, "FIRSTDOT_STATE_%s=", label);
  for (unsigned i = 0; i < STATE_BYTES; ++i) fprintf(stderr, "%02x", state[i]);
  fputc('\n', stderr);
}
void difftest_regcpy(void *state, bool to_reference) {
  ref_regcpy(state, to_reference);
  if (to_reference) {
    if (pending) fail("reference overwrite before injection");
    return;
  }
  if (!pending || injected) return;
  unsigned char before[STATE_BYTES], unchanged[STATE_BYTES];
  memcpy(before, state, STATE_BYTES);
  ((unsigned char *)state)[VECTOR_OFFSET + 8u] ^= 1u;
  ref_regcpy(unchanged, false);
  if (memcmp(before, unchanged, STATE_BYTES) != 0) fail("underlying reference state changed");
  injected = true;
  pending = false;
  fprintf(stderr, "DIFFTEST_FIRSTDOT_BIT64_INJECTED vd=0 pc=0x%llx instruction=0x%08x\n",
          (unsigned long long)TARGET_PC, (unsigned)TARGET_WORD);
  dump("BEFORE", before);
  dump("AFTER", state);
  fprintf(stderr, "FIRSTDOT_REFERENCE_UNCHANGED=1\n");
  fflush(stderr);
}
