// Team dot16 ISS/API candidate. Derived from team/tests/nemu_reference_traps.cpp.
// The pinned NEMU export is TWO-argument regcpy when CONFIG_LIGHTQS is off.
#include "diffstate.h"
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <dlfcn.h>
#include <map>
#include <string>

struct ReferenceState {
  DifftestArchIntRegState regs_int;
  DifftestArchFpRegState regs_fp;
  DifftestCSRState csr;
  uint64_t pc;
  DifftestHCSRState hcsr;
  DifftestArchVecRegState regs_vec;
  DifftestVecCSRState vcsr;
  DifftestFpCSRState fcsr;
  DifftestTriggerCSRState triggercsr;
};
static_assert(sizeof(DifftestArchVecRegState) == 32 * 16, "VLEN128 required");
static_assert(sizeof(DifftestArchIntRegState) == 32 * 8, "RV64 GPR required");
static_assert(sizeof(DifftestArchFpRegState) == 32 * 8, "RV64 FPR required");

static constexpr uint64_t HANDLER = 0x80f00000;
static constexpr uint64_t VS_MASK = uint64_t(3) << 9;
static constexpr uint64_t MDT_MASK = uint64_t(1) << 42;
static constexpr uint32_t DOT8 = 0x0200000b, DOT16 = 0x0e00000b;
static uint64_t rng_state = 0x9e3779b97f4a7c15ULL;
static uint64_t random_word() {
  rng_state ^= rng_state << 13; rng_state ^= rng_state >> 7;
  rng_state ^= rng_state << 17; return rng_state;
}
static unsigned char *vec(ReferenceState &s) {
  return reinterpret_cast<unsigned char *>(&s.regs_vec);
}
static const unsigned char *vec(const ReferenceState &s) {
  return reinterpret_cast<const unsigned char *>(&s.regs_vec);
}
static uint32_t instruction(unsigned lanes, unsigned vd, unsigned a, unsigned b) {
  return (lanes == 16 ? DOT16 : DOT8) | (vd << 7) | (a << 15) | (b << 20);
}
static int signed_byte(unsigned char x) { return x < 128 ? x : int(x) - 256; }
static uint32_t oracle(const ReferenceState &s, unsigned a, unsigned b, unsigned lanes) {
  int64_t sum = 0;
  for (unsigned k = 0; k < lanes; ++k)
    sum += int64_t(signed_byte(vec(s)[a * 16 + k])) *
           signed_byte(vec(s)[b * 16 + k]);
  return uint32_t(sum);
}

class Probe {
 public:
  explicit Probe(const char *library, bool bad_oracle) : negative_oracle(bad_oracle) {
    handle = dlopen(library, RTLD_NOW | RTLD_LOCAL);
    if (!handle) {
      std::fprintf(stderr, "DOT16_API_LOAD_FAIL: %s\n", dlerror()); std::exit(2);
    }
    init = symbol<void (*)(unsigned)>("difftest_init_v2");
    regcpy = symbol<void (*)(void *, bool)>("difftest_regcpy");
    memcopy = symbol<void (*)(uint64_t, void *, size_t, bool)>("difftest_memcpy");
    csrcpy = symbol<void (*)(void *, bool)>("difftest_csrcpy");
    execute = symbol<void (*)(uint64_t)>("difftest_exec");
    auto ram = symbol<void (*)(size_t)>("difftest_set_ramsize");
    auto size = symbol<const unsigned *>("DIFFTEST_REG_SIZE");
    check(*size == sizeof(ReferenceState), "ABI-size", *size, sizeof(ReferenceState));
    ram(16 * 1024 * 1024); init(sizeof(ReferenceState));
    csrcpy(csrs.data(), false);
    check((csrs[0x744] & 8) != 0, "NMIE-reset", csrs[0x744] & 8, 8);
    regcpy(&initial, false);
    check((initial.csr.mstatus & MDT_MASK) == 0, "MDT-reset",
          initial.csr.mstatus & MDT_MASK, 0);
    check(initial.vcsr.vlenb == 16, "vlenb", initial.vcsr.vlenb, 16);
  }
  ~Probe() { dlclose(handle); }

  ReferenceState state(unsigned lanes, unsigned policy = 0, unsigned vs = 1) {
    ReferenceState s = initial;
    s.csr.privilegeMode = 3; s.hcsr.virtMode = 0;
    s.csr.mtvec = HANDLER; s.csr.medeleg = 0; s.csr.mideleg = 0;
    s.csr.mie = 0; s.csr.mip = 0; s.csr.satp = 0;
    s.csr.mcause = 0; s.csr.mepc = 0; s.csr.mtval = 0;
    s.csr.mstatus &= ~(MDT_MASK | VS_MASK | uint64_t(0x88));
    s.csr.mstatus |= uint64_t(vs) << 9;
    s.vcsr.vtype = policy; s.vcsr.vl = lanes; s.vcsr.vstart = 0; s.vcsr.vlenb = 16;
    s.vcsr.vxrm = random_word() & 3; s.vcsr.vxsat = random_word() & 1;
    s.vcsr.vcsr = (s.vcsr.vxrm << 1) | s.vcsr.vxsat;
    s.fcsr.fcsr = 0x5b;
    for (unsigned i = 0; i < 32; ++i) {
      s.regs_int.value[i] = i ? 0x1234567800000000ULL + i : 0;
      s.regs_fp.value[i] = 0x3ff0000000000000ULL + i;
    }
    for (unsigned i = 0; i < 512; ++i) vec(s)[i] = random_word() & 255;
    return s;
  }

  void legal(ReferenceState s, unsigned lanes, unsigned vd, unsigned a, unsigned b,
             const char *label) {
    auto expected = s.regs_vec;
    uint32_t want = oracle(s, a, b, lanes);
    if (negative_oracle) want ^= 1;  // Checker negative control; reference is unchanged.
    auto *bytes = reinterpret_cast<unsigned char *>(&expected);
    std::memset(bytes + vd * 16, 0, 16);
    for (unsigned i = 0; i < 4; ++i) bytes[vd * 16 + i] = (want >> (8 * i)) & 255;
    auto after = step(s, instruction(lanes, vd, a, b), label);
    check(after.pc == before.pc + 4, "legal-pc", after.pc, before.pc + 4);
    check(after.csr.mcause == 0, "legal-mcause", after.csr.mcause, 0);
    check(((after.csr.mstatus >> 9) & 3) == 3, "legal-VS",
          (after.csr.mstatus >> 9) & 3, 3);
    check(std::memcmp(&expected, &after.regs_vec, sizeof(expected)) == 0,
          "full-vector-result", 1, 0);
    preserved(after, false);
    ++counts[lanes == 16 ? "dot16_legal" : "dot8_legal"];
  }

  void illegal(ReferenceState s, uint32_t word, uint64_t tval, const char *label) {
    auto after = step(s, word, label);
    check(after.pc == HANDLER, "trap-pc", after.pc, HANDLER);
    check(after.csr.mepc == before.pc, "trap-mepc", after.csr.mepc, before.pc);
    check(after.csr.mcause == 2, "trap-mcause", after.csr.mcause, 2);
    check(after.csr.mtval == tval, "trap-mtval", after.csr.mtval, tval);
    check((after.csr.mstatus & VS_MASK) == (before.csr.mstatus & VS_MASK),
          "illegal-VS", after.csr.mstatus & VS_MASK, before.csr.mstatus & VS_MASK);
    preserved(after, true);
    ++counts["illegal"];
  }

  void ordinary() {
    auto s = state(16);
    auto after = step(s, 0x00100073, "ebreak");
    check(after.pc == HANDLER && after.csr.mepc == before.pc && after.csr.mcause == 3,
          "ebreak", after.csr.mcause, 3);
    preserved(after, true); ++counts["ebreak"];

    s = state(16);
    after = step(s, 0x00730293, "addi-x5-x6-7");
    auto want_int = before.regs_int; want_int.value[5] = want_int.value[6] + 7;
    check(after.pc == before.pc + 4 && after.csr.mcause == 0, "addi-flow", after.pc, before.pc + 4);
    check(std::memcmp(&want_int, &after.regs_int, sizeof(want_int)) == 0, "addi-gpr", 1, 0);
    check(std::memcmp(&before.regs_vec, &after.regs_vec, sizeof(before.regs_vec)) == 0,
          "addi-vector", 1, 0);
    check((after.csr.mstatus & VS_MASK) == (before.csr.mstatus & VS_MASK),
          "addi-VS", after.csr.mstatus & VS_MASK, before.csr.mstatus & VS_MASK);
    ++counts["addi"];

    s = state(16);
    auto want_vec = s.regs_vec;
    auto *w = reinterpret_cast<unsigned char *>(&want_vec);
    for (unsigned i = 0; i < 16; ++i) w[10 * 16 + i] = vec(s)[8 * 16 + i] + vec(s)[9 * 16 + i];
    after = step(s, 0x02940557, "vadd-vv");
    check(after.pc == before.pc + 4 && after.csr.mcause == 0, "vadd-flow", after.pc, before.pc + 4);
    check(std::memcmp(&want_vec, &after.regs_vec, sizeof(want_vec)) == 0, "vadd-vector", 1, 0);
    check(((after.csr.mstatus >> 9) & 3) == 3, "vadd-VS", (after.csr.mstatus >> 9) & 3, 3);
    preserved(after, false); ++counts["vadd"];
  }

  void report(bool feature) const {
    std::printf("{\"status\":\"PASS_NEMU_REFERENCE_API\",\"expected_feature\":%u,"
                "\"abi_size\":%zu,\"regcpy_arguments\":2,\"unique_instruction_sites\":%zu,"
                "\"final_rng_state\":\"%016llx\",\"xs_dot16_tval_enabled\":false,"
                "\"fullcore_qualified\":false,\"state_injection\":true,\"counts\":{",
                unsigned(feature), sizeof(ReferenceState), sites.size(),
                static_cast<unsigned long long>(rng_state));
    bool comma = false;
    for (const auto &item : counts) {
      std::printf("%s\"%s\":%llu", comma ? "," : "", item.first.c_str(),
                  static_cast<unsigned long long>(item.second)); comma = true;
    }
    std::puts("}}");
  }

 private:
  template <class T> T symbol(const char *name) {
    auto value = dlsym(handle, name);
    if (!value) { std::fprintf(stderr, "DOT16_API_SYMBOL_FAIL: %s\n", name); std::exit(2); }
    return reinterpret_cast<T>(value);
  }
  void check(bool ok, const char *field, uint64_t got, uint64_t want) const {
    if (ok) return;
    std::fprintf(stderr,
      "{\"status\":\"DOT16_API_FAIL\",\"case\":\"%s\",\"field\":\"%s\","
      "\"instruction\":\"%08x\",\"pc\":\"%llx\",\"got\":\"%llx\",\"want\":\"%llx\"}\n",
      current_case, field, current_word,
      static_cast<unsigned long long>(before.pc), static_cast<unsigned long long>(got),
      static_cast<unsigned long long>(want));
    std::exit(2);
  }
  ReferenceState step(ReferenceState s, uint32_t word, const char *label) {
    current_case = label; current_word = word;
    auto it = sites.find(word);
    if (it == sites.end()) {
      uint64_t pc = 0x80001000 + sites.size() * 16;
      check(pc + 16 < HANDLER, "code-space", pc + 16, HANDLER);
      // A fixed ebreak terminates decode-ahead before the next unique slot.
      std::array<uint32_t, 4> code{word, 0x00100073, 0x00100073, 0x00100073};
      memcopy(pc, code.data(), sizeof(code), true);
      it = sites.emplace(word, pc).first;
    }
    s.pc = it->second;
    regcpy(&s, true); regcpy(&before, false);
    check(std::memcmp(&s.regs_vec, &before.regs_vec, sizeof(s.regs_vec)) == 0,
          "injection-vector", 1, 0);
    check(std::memcmp(&s.vcsr, &before.vcsr, sizeof(s.vcsr)) == 0,
          "injection-vcsr", 1, 0);
    execute(1);
    ReferenceState after{}; regcpy(&after, false); return after;
  }
  void preserved(const ReferenceState &after, bool preserve_vector) const {
    check(std::memcmp(&before.regs_int, &after.regs_int, sizeof(before.regs_int)) == 0,
          "preserve-gpr", 1, 0);
    check(std::memcmp(&before.regs_fp, &after.regs_fp, sizeof(before.regs_fp)) == 0,
          "preserve-fpr", 1, 0);
    check(std::memcmp(&before.vcsr, &after.vcsr, sizeof(before.vcsr)) == 0,
          "preserve-vcsr", 1, 0);
    check(std::memcmp(&before.fcsr, &after.fcsr, sizeof(before.fcsr)) == 0,
          "preserve-fcsr", 1, 0);
    if (preserve_vector)
      check(std::memcmp(&before.regs_vec, &after.regs_vec, sizeof(before.regs_vec)) == 0,
            "preserve-vector", 1, 0);
  }
  void *handle = nullptr;
  void (*init)(unsigned) = nullptr;
  void (*regcpy)(void *, bool) = nullptr;
  void (*memcopy)(uint64_t, void *, size_t, bool) = nullptr;
  void (*csrcpy)(void *, bool) = nullptr;
  void (*execute)(uint64_t) = nullptr;
  std::array<uint64_t, 4096> csrs{};
  ReferenceState initial{}, before{};
  const char *current_case = "initialization";
  uint32_t current_word = 0;
  bool negative_oracle;
  std::map<uint32_t, uint64_t> sites;
  std::map<std::string, uint64_t> counts;
};

int main(int argc, char **argv) {
  if (argc < 3 || argc > 4 || (std::strcmp(argv[2], "0") && std::strcmp(argv[2], "1")) ||
      (argc == 4 && std::strcmp(argv[3], "negative-oracle"))) {
    std::fputs("usage: reference-api <candidate.so> <expected-feature:0|1> [negative-oracle]\n", stderr);
    return 64;
  }
  const bool feature = argv[2][0] == '1';
  Probe p(argv[1], argc == 4);
  p.ordinary();
  constexpr unsigned triples[][3] = {{10,8,9},{8,8,9},{9,8,9},{10,8,8},
                                      {8,8,8},{0,0,31},{31,31,0},{31,0,31}};
  for (unsigned lanes : {8u,16u}) {
    if (lanes == 16 && !feature) continue;
    for (unsigned policy : {0u,64u,128u,192u}) for (unsigned vs : {1u,2u,3u}) {
      for (unsigned fixture = 0; fixture < 12; ++fixture) for (const auto &t : triples) {
        auto s = p.state(lanes, policy, vs);
        auto *a = vec(s) + t[1] * 16, *b = vec(s) + t[2] * 16;
        if (fixture < 6) {
          const unsigned char x[] = {0,128,128,127,255,128};
          const unsigned char y[] = {0,128,127,127,1,255};
          std::memset(a, x[fixture], 16); std::memset(b, y[fixture], 16);
        } else if (fixture == 6 || fixture == 7) {
          std::memset(a, 1, 16); std::memset(b, 2, 16);
          if (fixture == 7) { std::memset(a + 8, 128, 8); std::memset(b + 8, 127, 8); }
        }
        p.legal(s, lanes, t[0], t[1], t[2], "directed-and-random");
      }
    }
    for (unsigned k = 0; k < 16; ++k) {
      auto s = p.state(lanes); std::memset(vec(s) + 8 * 16, 0, 16);
      std::memset(vec(s) + 9 * 16, 0, 16);
      vec(s)[8 * 16 + k] = 128; vec(s)[9 * 16 + k] = 127;
      p.legal(s, lanes, 10, 8, 9, "one-hot-lane");
    }
  }
  if (feature) {
    // Full encoded-register cross product, after all writes, for all four policies.
    for (unsigned policy : {0u,64u,128u,192u})
      for (unsigned vd = 0; vd < 32; ++vd) for (unsigned a = 0; a < 32; ++a)
        for (unsigned b = 0; b < 32; ++b)
          p.legal(p.state(16, policy, 1 + (vd % 3)), 16, vd, a, b, "all-register-aliases");
  } else {
    for (const auto &t : triples) for (unsigned policy : {0u,64u,128u,192u}) {
      auto s = p.state(16, policy);
      auto w = instruction(16, t[0], t[1], t[2]);
      p.illegal(s, w, w, "disabled-dot16");
    }
  }
  for (unsigned lanes : {8u,16u}) {
    const uint32_t w = instruction(lanes, 10, 8, 9);
    auto bad = [&](ReferenceState s, const char *name, bool vl_only = false) {
      p.illegal(s, w, lanes == 8 && vl_only ? 0 : w, name);
    };
    auto s = p.state(lanes, 0, 0); bad(s, "VS-off");
    for (uint64_t type : {uint64_t(1)<<63, uint64_t(8), uint64_t(1), uint64_t(7),
                         uint64_t(1)<<8, uint64_t(1)<<62}) {
      s=p.state(lanes); s.vcsr.vtype=type; bad(s, "illegal-vtype");
    }
    for (uint64_t start : {uint64_t(1),uint64_t(16)}) {
      s=p.state(lanes); s.vcsr.vstart=start; bad(s, "illegal-vstart");
    }
    for (uint64_t length : {uint64_t(0),uint64_t(7),uint64_t(8),uint64_t(15),uint64_t(16),uint64_t(17)}) {
      if (length == lanes) continue;
      s=p.state(lanes); s.vcsr.vl=length; bad(s, "illegal-vl", true);
    }
    s=p.state(lanes,0,0);s.vcsr.vtype=8;s.vcsr.vstart=1;s.vcsr.vl=0;
    bad(s,"combined-illegal");
    for (unsigned bit : {12u,13u,14u,25u,26u,27u,28u,29u,30u,31u}) {
      s=p.state(lanes); uint32_t neighbor=w^(uint32_t(1)<<bit);
      p.illegal(s,neighbor,neighbor,"custom0-neighbor");
    }
  }
  p.report(feature);
}
