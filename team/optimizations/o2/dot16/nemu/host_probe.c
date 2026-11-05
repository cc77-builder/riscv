/* Validation auxiliary only: host stub, NOT NEMU's real ABI or trap machinery.
 * The tested helpers are included unchanged from the actually patched tree.
 * The oracle reads independent signed byte arrays and accumulates in int64_t.
 */
#include <inttypes.h>
#include <limits.h>
#include <setjmp.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if defined(CONFIG_CUSTOM_VDOT) || defined(CONFIG_CUSTOM_VDOT16)
#define VLEN 128
#define EX_II 2
_Static_assert(CHAR_BIT == 8 && INT8_MIN == -128 && INT8_MAX == 127,
               "probe requires exact signed eight-bit bytes");

typedef struct { uint64_t _64[2]; } Vector;
typedef struct {
  Vector vr[32];
  uint32_t instr;
  unsigned vs_state;
  uint64_t dirty_calls;
} Cpu;
typedef struct { uint64_t val, vill, pad, vsew, vlmul; } Vtype;
typedef struct { uint64_t val; } Csr;
typedef struct {
  Vtype type;
  Csr length, start;
  uint64_t vxrm, vxsat, vcsr, fflags;
} Csrs;
typedef struct { struct { struct { uint32_t val; } instr; } isa; } Decode;

static Cpu cpu, initial_cpu;
static Csrs csrs;
static Vtype *const vtype = &csrs.type;
static Csr *const vl = &csrs.length;
static Csr *const vstart = &csrs.start;
static jmp_buf trap_env;
static int observed_exception;
static int active_lane = -1;
static uint64_t legal_cases[2], illegal_cases[2], alias_cases[2], directed_cases[2];

bool vp_enable(void) { return cpu.vs_state != 0; }
void vp_set_dirty(void) { cpu.vs_state = 3; ++cpu.dirty_calls; }
_Noreturn void longjmp_exception(int cause) {
  observed_exception = cause;
  longjmp(trap_env, 1);
}
#define def_EHelper(name) static void helper_##name(Decode *s)
#include "vdot.h"
#include "vdot16.h"

static unsigned slot(unsigned lanes) { return lanes == 8 ? 0 : 1; }
static uint32_t opcode(unsigned lanes) {
  return lanes == 8 ? UINT32_C(0x0200000b) : UINT32_C(0x0e00000b);
}
static void set_type(uint64_t raw) {
  vtype->val = raw;
  vtype->vill = raw >> 63;
  vtype->pad = (raw >> 8) & ((UINT64_C(1) << 55) - 1);
  vtype->vsew = (raw >> 3) & 7;
  vtype->vlmul = raw & 7;
}
static void prepare(unsigned lanes, unsigned policy) {
  cpu = initial_cpu;
  memset(&csrs, 0, sizeof(csrs));
  set_type((uint64_t)policy << 6);
  vl->val = lanes;
  vstart->val = 0;
  csrs.vxrm = 2;
  csrs.vxsat = 1;
  csrs.vcsr = 5;
  csrs.fflags = 27;
  cpu.vs_state = 1;
  observed_exception = 0;
}
static int64_t oracle(const Cpu *before, unsigned lanes, unsigned vs1, unsigned vs2) {
  int8_t a[16], b[16];
  memcpy(a, before->vr[vs1]._64, sizeof(a));
  memcpy(b, before->vr[vs2]._64, sizeof(b));
  int64_t total = 0;
  for (unsigned lane = 0; lane < lanes; ++lane)
    total += (int64_t)a[lane] * (int64_t)b[lane];
  return total;
}
static void invoke(unsigned lanes, Decode *s) {
  switch (lanes) {
#ifdef CONFIG_CUSTOM_VDOT
    case 8: helper_vdot(s); return;
#endif
#ifdef CONFIG_CUSTOM_VDOT16
    case 16: helper_vdot16(s); return;
#endif
    default: abort();
  }
}
static _Noreturn void fail(const char *label, unsigned lanes, unsigned vd,
                           unsigned vs1, unsigned vs2, const char *reason,
                           uint64_t expected_low) {
  printf("{\"status\":\"FAIL\",\"case\":\"%s\",\"lanes\":%u,"
         "\"vd\":%u,\"vs1\":%u,\"vs2\":%u,\"reason\":\"%s\","
         "\"lane\":%d,\"vl\":%" PRIu64 ",\"vstart\":%" PRIu64 ","
         "\"cause\":%d,\"expected_low64\":\"%016" PRIx64 "\","
         "\"actual_low64\":\"%016" PRIx64 "\","
         "\"actual_high64\":\"%016" PRIx64 "\"}\n",
         label, lanes, vd, vs1, vs2, reason, active_lane, vl->val, vstart->val, observed_exception,
         expected_low, cpu.vr[vd]._64[0], cpu.vr[vd]._64[1]);
  exit(1);
}
static void check(const char *label, unsigned lanes, unsigned vd, unsigned vs1,
                  unsigned vs2, bool legal) {
  Decode decoded = {.isa.instr.val = opcode(lanes) | (vs1 << 15) |
                                     (vs2 << 20) | (vd << 7)};
  cpu.instr = decoded.isa.instr.val;
  const Cpu before = cpu;
  const Csrs before_csrs = csrs;
  const int64_t total = oracle(&before, lanes, vs1, vs2);
  const uint64_t expected_low = (uint32_t)total;
  if (setjmp(trap_env) == 0) invoke(lanes, &decoded);

  if (legal) {
    if (observed_exception != 0)
      fail(label, lanes, vd, vs1, vs2, "legal instruction trapped", expected_low);
    Cpu expected = before;
    expected.vr[vd]._64[0] = expected_low;
    expected.vr[vd]._64[1] = 0;
    expected.vs_state = 3;
    ++expected.dirty_calls;
    if (memcmp(cpu.vr, expected.vr, sizeof(cpu.vr)) != 0)
      fail(label, lanes, vd, vs1, vs2, "full register image mismatch", expected_low);
    if (cpu.instr != expected.instr || cpu.vs_state != expected.vs_state ||
        cpu.dirty_calls != expected.dirty_calls)
      fail(label, lanes, vd, vs1, vs2, "stub dirty or instruction state mismatch", expected_low);
    ++legal_cases[slot(lanes)];
  } else {
    if (observed_exception != EX_II)
      fail(label, lanes, vd, vs1, vs2, "illegal request did not trap as EX_II", expected_low);
    if (memcmp(cpu.vr, before.vr, sizeof(cpu.vr)) != 0 ||
        cpu.instr != before.instr || cpu.vs_state != before.vs_state ||
        cpu.dirty_calls != before.dirty_calls)
      fail(label, lanes, vd, vs1, vs2, "illegal helper partially updated state", expected_low);
    ++illegal_cases[slot(lanes)];
  }
  if (memcmp(&csrs, &before_csrs, sizeof(csrs)) != 0)
    fail(label, lanes, vd, vs1, vs2, "operation CSR sentinel changed", expected_low);
}
static void directed(unsigned lanes) {
  for (unsigned lane = 0; lane < 16; ++lane) {
    active_lane = (int)lane;
    prepare(lanes, lane % 4);
    int8_t a[16] = {0}, b[16] = {0};
    a[lane] = -128;
    b[lane] = lane == 15 ? -128 : 127;
    memcpy(cpu.vr[1]._64, a, sizeof(a));
    memcpy(cpu.vr[2]._64, b, sizeof(b));
    check("single_lane", lanes, 31, 1, 2, true);
    ++directed_cases[slot(lanes)];
  }
  active_lane = -1;
  for (unsigned variant = 0; variant < 4; ++variant) {
    prepare(lanes, variant);
    int8_t a[16], b[16];
    for (unsigned i = 0; i < 16; ++i) {
      a[i] = variant == 2 ? 127 : -128;
      b[i] = variant == 0 ? -128 : (variant == 3 ? 0 : 127);
    }
    memcpy(cpu.vr[1]._64, a, sizeof(a));
    memcpy(cpu.vr[2]._64, b, sizeof(b));
    check("extreme_and_zero", lanes, 31, 1, 2, true);
    ++directed_cases[slot(lanes)];
  }
  if (lanes == 8) {
    for (unsigned variant = 0; variant < 2; ++variant) {
      prepare(lanes, variant);
      int8_t a[16], b[16];
      for (unsigned i = 0; i < 16; ++i) {
        a[i] = i < 8 ? 1 : (variant == 0 ? -128 : 127);
        b[i] = i < 8 ? -1 : (variant == 0 ? -128 : -127);
      }
      memcpy(cpu.vr[1]._64, a, sizeof(a));
      memcpy(cpu.vr[2]._64, b, sizeof(b));
      check("dot8_high_half_ignored", lanes, 31, 1, 2, true);
      ++directed_cases[slot(lanes)];
    }
  }
}
static void all_aliases(unsigned lanes) {
  for (unsigned policy = 0; policy < 4; ++policy)
    for (unsigned vd = 0; vd < 32; ++vd)
      for (unsigned vs1 = 0; vs1 < 32; ++vs1)
        for (unsigned vs2 = 0; vs2 < 32; ++vs2) {
          prepare(lanes, policy);
          cpu.vs_state = 1 + (vd + vs1 + vs2) % 3;
          check("all_register_aliases", lanes, vd, vs1, vs2, true);
          ++alias_cases[slot(lanes)];
        }
}
static void illegal_variant(unsigned lanes, const char *label, uint64_t raw_type,
                            uint64_t length, uint64_t start, unsigned vs_state) {
  static const unsigned regs[4][3] = {{0, 0, 0}, {31, 31, 0}, {31, 0, 31}, {31, 1, 2}};
  for (unsigned policy = 0; policy < 4; ++policy)
    for (unsigned alias = 0; alias < 4; ++alias) {
      prepare(lanes, policy);
      set_type(raw_type | ((uint64_t)policy << 6));
      vl->val = length;
      vstart->val = start;
      cpu.vs_state = vs_state;
      check(label, lanes, regs[alias][0], regs[alias][1], regs[alias][2], false);
    }
}
static void all_illegal(unsigned lanes) {
  illegal_variant(lanes, "VS_off", 0, lanes, 0, 0);
  illegal_variant(lanes, "vill", UINT64_C(1) << 63, lanes, 0, 1);
  for (unsigned bit = 8; bit < 63; ++bit)
    illegal_variant(lanes, "vtype_reserved_bit", UINT64_C(1) << bit, lanes, 0, 1);
  for (unsigned value = 1; value < 8; ++value) {
    illegal_variant(lanes, "vsew", (uint64_t)value << 3, lanes, 0, 1);
    illegal_variant(lanes, "vlmul", value, lanes, 0, 1);
  }
  static const uint64_t lengths[] = {0, 1, 7, 8, 9, 15, 16, 17, 31, 32, 128, UINT64_MAX};
  for (unsigned i = 0; i < sizeof(lengths) / sizeof(lengths[0]); ++i)
    if (lengths[i] != lanes) illegal_variant(lanes, "illegal_VL", 0, lengths[i], 0, 1);
  static const uint64_t starts[] = {1, 7, 8, 15, 16, UINT64_MAX};
  for (unsigned i = 0; i < sizeof(starts) / sizeof(starts[0]); ++i)
    illegal_variant(lanes, "vstart_nonzero", 0, lanes, starts[i], 1);
}
static void run(unsigned lanes) {
  directed(lanes);
  all_aliases(lanes);
  all_illegal(lanes);
}
#else
/* Include actual headers even when disabled: missing/broken feature guards
 * must fail this configuration instead of being hidden by the test harness. */
#include "vdot.h"
#include "vdot16.h"
#endif

int main(void) {
#if defined(CONFIG_CUSTOM_VDOT) || defined(CONFIG_CUSTOM_VDOT16)
  const uint16_t endian_check = 1;
  if (*(const uint8_t *)&endian_check != 1) {
    fputs("probe requires a little-endian host; no real NEMU ABI is assumed\n", stderr);
    return 2;
  }
  memset(&initial_cpu, 0, sizeof(initial_cpu));
  for (unsigned reg = 0; reg < 32; ++reg) {
    uint8_t bytes[16];
    for (unsigned lane = 0; lane < 16; ++lane)
      bytes[lane] = (uint8_t)(reg * 37 + lane * 19 + (reg ^ lane) * 11 + 73);
    memcpy(initial_cpu.vr[reg]._64, bytes, sizeof(bytes));
  }
#ifdef CONFIG_CUSTOM_VDOT16
  run(16);
#endif
#ifdef CONFIG_CUSTOM_VDOT
  run(8);
#endif
  printf("{\"status\":\"PASS\",\"kind\":\"host_stub_not_nemu_abi\","
         "\"dot8\":{\"legal\":%" PRIu64 ",\"aliases\":%" PRIu64
         ",\"directed\":%" PRIu64 ",\"illegal\":%" PRIu64 "},"
         "\"dot16\":{\"legal\":%" PRIu64 ",\"aliases\":%" PRIu64
         ",\"directed\":%" PRIu64 ",\"illegal\":%" PRIu64 "}}\n",
         legal_cases[0], alias_cases[0], directed_cases[0], illegal_cases[0],
         legal_cases[1], alias_cases[1], directed_cases[1], illegal_cases[1]);
#else
  puts("{\"status\":\"PASS\",\"kind\":\"both_helpers_disabled_compile_stub\","
       "\"dot8\":{\"legal\":0,\"aliases\":0,\"directed\":0,\"illegal\":0},"
       "\"dot16\":{\"legal\":0,\"aliases\":0,\"directed\":0,\"illegal\":0}}");
#endif
  return 0;
}
