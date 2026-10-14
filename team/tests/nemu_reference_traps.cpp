// Exercise the reference ABI using the exact DiffTest state generated for DUT.
#include "diffstate.h"
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <dlfcn.h>

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

static void require(bool ok, const char *message) {
  if (!ok) { std::fprintf(stderr, "REFERENCE_TRAP_FAIL: %s\n", message); std::exit(1); }
}
template <class T> static T symbol(void *handle, const char *name) {
  auto value = dlsym(handle, name);
  require(value != nullptr, name);
  return reinterpret_cast<T>(value);
}

int main(int argc, char **argv) {
  require(argc == 2, "usage: reference-traps <candidate.so>");
  void *handle = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
  require(handle != nullptr, "cannot load candidate reference");
  auto init = symbol<void (*)(unsigned)>(handle, "difftest_init_v2");
  auto regcpy = symbol<void (*)(void *, bool, bool)>(handle, "difftest_regcpy");
  auto memcpy_ref = symbol<void (*)(uint64_t, void *, size_t, bool)>(handle, "difftest_memcpy");
  auto csrcpy = symbol<void (*)(void *, bool)>(handle, "difftest_csrcpy");
  auto exec = symbol<void (*)(uint64_t)>(handle, "difftest_exec");
  init(sizeof(ReferenceState)); // Reject a mismatched register-copy ABI.
  std::array<uint64_t, 4096> csrs{};
  csrcpy(csrs.data(), false);
  require((csrs[0x744] & 8) != 0, "Smrnmi NMIE reset is 0; XiangShan resets to 1");
  ReferenceState state{};
  regcpy(&state, false, false);
  constexpr uint64_t pc = 0x80000000, illegal_pc = pc + 4, legal_pc = pc + 8, handler = 0x80000100;
  uint32_t ebreak = 0x00100073, vdot = 0x0294050b;
  memcpy_ref(pc, &ebreak, sizeof(ebreak), true);
  state.pc = pc; state.csr.mtvec = handler;
  state.csr.mstatus &= ~(uint64_t(1) << 42); // Ordinary trap, not a double trap.
  regcpy(&state, true, false);
  exec(1); regcpy(&state, false, false);
  require(state.pc == handler && state.csr.mepc == pc && state.csr.mcause == 3,
          "single-step ebreak did not enter mtvec with exact cause/PC");

  // Distinct fixed sites avoid changing an already decoded tcache instruction.
  memcpy_ref(illegal_pc, &vdot, sizeof(vdot), true);
  memcpy_ref(legal_pc, &vdot, sizeof(vdot), true);
  state.pc = illegal_pc; state.csr.mstatus &= ~((uint64_t(1) << 42) | 0x600);
  state.csr.mstatus |= 0x200;
  state.vcsr.vtype = 1; state.vcsr.vl = 8; state.vcsr.vstart = 0;
  // A marker in every byte makes any illegal partial write observable.
  std::memset(&state.regs_vec, 0xA5, sizeof(state.regs_vec));
  auto before = state.regs_vec;
  regcpy(&state, true, false); exec(1); regcpy(&state, false, false);
  require(state.pc == handler && state.csr.mepc == illegal_pc && state.csr.mcause == 2 && state.csr.mtval == vdot,
          "single-step illegal-config VDOT did not trap with exact cause/PC/word");
  require(std::memcmp(&before, &state.regs_vec, sizeof(before)) == 0, "illegal VDOT changed vector state");

  state.pc = legal_pc; state.csr.mstatus &= ~((uint64_t(1) << 42) | 0x600);
  state.csr.mstatus |= 0x200;
  state.vcsr.vtype = 0; state.vcsr.vl = 8; state.vcsr.vstart = 0;
  // Byte access avoids relying on the generated vector array's scalar shape.
  auto *bytes = reinterpret_cast<unsigned char *>(&state.regs_vec);
  std::memset(bytes + 8 * 16, 0xFF, 16);
  std::memset(bytes + 9 * 16, 1, 16);
  regcpy(&state, true, false); exec(1); regcpy(&state, false, false);
  require(state.pc == legal_pc + 4 && ((state.csr.mstatus >> 9) & 3) == 3,
          "legal VDOT failed to advance PC and set VS Dirty");
  bytes = reinterpret_cast<unsigned char *>(&state.regs_vec);
  uint32_t result; std::memcpy(&result, bytes + 10 * 16, sizeof(result));
  require(result == 0xFFFFFFF8u, "wrong signed dot result");
  for (unsigned i = 4; i < 16; ++i) require(bytes[10 * 16 + i] == 0, "high96 not cleared");
  require(state.vcsr.vl == 8 && state.vcsr.vtype == 0 && state.vcsr.vstart == 0,
          "legal VDOT changed configuration");
  std::puts("NEMU_REFERENCE_TRAPS_PASS cases=3 abi=true nmie_reset=1 full128=true");
  dlclose(handle);
}
