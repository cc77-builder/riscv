#include "VVDotDecodeTestTop.h"
#include "verilated.h"
#include <cstdint>
#include <iostream>
#include <stdexcept>

static VVDotDecodeTestTop d;
static uint64_t cases = 0;
static void require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
static void eval() { d.clock = 0; d.eval(); }
static void tick() { eval(); d.clock = 1; d.eval(); eval(); }
static uint32_t word(unsigned vd, unsigned vs1, unsigned vs2) {
  return 0x0200000bU | vd << 7 | vs1 << 15 | vs2 << 20;
}
static unsigned snapshot() {
  return d.io_vill << 15 | d.io_vma << 14 | d.io_vta << 13 |
    d.io_vsew << 11 | d.io_vlmul << 8 | d.io_vstart;
}
static void check(unsigned vd, unsigned vs1, unsigned vs2, bool illegal,
                  unsigned expected_snapshot, bool available = true) {
  // DecodeUnitComp offers outputs only when its downstream group is ready.
  require(d.io_out_valid == available && !d.io_extra_valid, "output count while ready/stalled");
  require(d.io_src0 == vs1 && d.io_src1 == vs2 && d.io_dest == vd, "source/destination fields");
  // Source classes 0..4: vector, vector, none, none, renamed VL.
  require(d.io_types == 0x40044, "source classes or VL dependency");
  require(d.io_exception == illegal, "illegal configuration/VS classification");
  require(d.io_vec_wen && !d.io_other_wen, "write enables before DecodeStage v0 routing");
  require(!d.io_old_dep && !d.io_partial, "old destination dependence");
  require(!d.io_flush && !d.io_block_back, "normal completion flags on vdot");
  require(d.io_first && d.io_last && d.io_uop_idx == 0, "uop boundaries");
  require(d.io_snapshot == expected_snapshot, "vtype/vstart snapshot changed");
}
static void transaction(unsigned vd, unsigned vs1, unsigned vs2, bool illegal, bool stall = false) {
  d.io_word = word(vd, vs1, vs2); d.io_valid = 1; d.io_out_ready = 1; eval();
  require(d.io_ready, "decoder not ready after previous transaction");
  require(d.io_classified && d.io_simple_vdot && d.io_complex, "precise vector decode");
  require(d.io_num_uops == 1 && d.io_num_wb == 1, "LMUL expanded custom instruction");
  const unsigned saved = snapshot();
  tick(); d.io_valid = 0; eval(); check(vd, vs1, vs2, illegal, saved);
  if (stall) {
    d.io_out_ready = 0;
    // Later decode input must not change this instruction's metadata.
    d.io_word = word(31, 30, 29); d.io_vsew ^= 1; d.io_vlmul ^= 1;
    d.io_vill ^= 1; d.io_vstart ^= 7;
    for (int n = 0; n < 7; ++n) { tick(); check(vd, vs1, vs2, illegal, saved, false); }
    d.io_vsew ^= 1; d.io_vlmul ^= 1; d.io_vill ^= 1; d.io_vstart ^= 7;
    d.io_out_ready = 1;
    eval(); check(vd, vs1, vs2, illegal, saved);
  }
  tick(); require(!d.io_out_valid, "duplicate output"); ++cases;
}
int main(int argc, char **argv) {
  Verilated::commandArgs(argc, argv);
  try {
    d.io_word = 0; d.io_valid = 0; d.io_redirect = 0;
    d.io_vsew = 0; d.io_vlmul = 0; d.io_vill = 0;
    d.io_vta = 0; d.io_vma = 0; d.io_vstart = 0; d.io_vs_off = 0;
    d.reset = 1; d.io_out_ready = 1; tick(); tick(); d.reset = 0;
    for (unsigned policy = 0; policy < 4; ++policy) {
      d.io_vta = policy & 1; d.io_vma = policy >> 1;
      for (unsigned vd = 0; vd < 32; ++vd)
        for (unsigned vs1 = 0; vs1 < 32; ++vs1)
          for (unsigned vs2 = 0; vs2 < 32; ++vs2) transaction(vd, vs1, vs2, false);
    }
    for (unsigned sew = 0; sew < 4; ++sew)
      for (unsigned lmul = 0; lmul < 8; ++lmul) {
        d.io_vsew = sew; d.io_vlmul = lmul;
        transaction(10, 9, 8, sew != 0 || lmul != 0, true);
      }
    d.io_vsew = 0; d.io_vlmul = 0;
    d.io_vill = 1; transaction(0, 0, 0, true); d.io_vill = 0;
    d.io_vs_off = 1; transaction(10, 9, 8, true); d.io_vs_off = 0;
    d.io_vstart = 7; transaction(10, 9, 8, true, true); d.io_vstart = 0;
    transaction(0, 0, 0, false);
    d.io_word = word(10, 9, 8); d.io_valid = 1; d.io_out_ready = 0; tick();
    d.io_valid = 0; d.io_redirect = 1; tick();
    require(!d.io_out_valid && !d.io_extra_valid, "decoder redirect left a pending uop");
    d.io_redirect = 0; d.io_out_ready = 1;
    transaction(10, 9, 8, false);
    for (unsigned bit = 0; bit < 32; ++bit) if (0xfe00707fU & (1U << bit)) {
      d.io_word = word(10, 9, 8) ^ (1U << bit); eval();
      require(!d.io_classified && !d.io_simple_vdot, "custom neighbour decoded as vdot");
    }
    d.io_word = 0x02940557; eval(); // existing vadd.vv
    require(!d.io_classified && !d.io_simple_vdot && d.io_complex, "vadd vector regression");
    std::cout << "VDOT_DECODE_PASS transactions=" << cases << " (decoder RTL only)\n";
    d.final(); return 0;
  } catch (const std::exception &e) {
    std::cerr << "VDOT_DECODE_FAIL case=" << cases << " word=0x" << std::hex << d.io_word
              << " reason=" << e.what() << '\n'; d.final(); return 1;
  }
}
