#include "VDot16Prototype.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

struct Request {
  std::array<uint8_t, 16> a{}, b{};
  uint32_t tag = 0;
  unsigned op = 0, vl = 8, sew = 0, lmul = 0, start = 0;
  bool vill = false, vm = true, vta = false, vma = false, v0 = false;
};
struct Packet { uint32_t result, tag; bool illegal, v0; };

static uint64_t rng = UINT64_C(0x202611050016);
static uint64_t random64() {
  rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; return rng;
}
static int signedByte(uint8_t b) { return b < 128 ? int(b) : int(b) - 256; }
static uint32_t nextTag = 1;
static Request request(unsigned op, int a, int b) {
  Request r; r.op = op; r.vl = op == 1 ? 16 : 8; r.tag = nextTag++;
  r.a.fill(uint8_t(a)); r.b.fill(uint8_t(b));
  r.vta = r.tag & 1; r.vma = r.tag & 2; r.v0 = r.tag & 4; return r;
}

class Test {
public:
  VDot16Prototype dut;
  std::optional<Packet> p, r;
  bool extension, inject, injected = false;
  uint64_t cycle = 0, accepted = 0, responded = 0, killed = 0;
  uint64_t blockedCycles = 0, simultaneous = 0, maxOccupancy = 0;
  uint64_t illegalResponses = 0, dot8Accepted = 0, dot16Accepted = 0;
  uint64_t readyKillR = 0, redirectResponses = 0;
  explicit Test(bool ext, bool inj) : extension(ext), inject(inj) {}
  [[noreturn]] void fail(const std::string &s) {
    throw std::runtime_error("cycle=" + std::to_string(cycle) + " " + s);
  }
  void need(bool ok, const std::string &s) { if (!ok) fail(s); }
  Packet expected(const Request &q) {
    const bool is16 = extension && q.op == 1;
    const bool illegal = !(q.op == 0 || is16) || q.vill || q.sew != 0 ||
      q.lmul != 0 || !q.vm || q.start != 0 || q.vl != (is16 ? 16u : 8u);
    int64_t total = 0;
    if (!illegal) for (unsigned lane = 0; lane < (is16 ? 16u : 8u); ++lane)
      total += int64_t(signedByte(q.a[lane])) * signedByte(q.b[lane]);
    return {uint32_t(total), q.tag, illegal, q.v0};
  }
  // Independent pre-edge packet model. Newly accepted data can never reach R
  // on this same edge, even when an older P is moving out.
  bool tick(const Request &q, bool valid, bool ready, bool flush = false,
            bool killP = false, bool killR = false, bool reset = false) {
    dut.clock = 0; dut.reset = reset;
    dut.io_in_valid = valid; dut.io_out_ready = ready;
    dut.io_flush_valid = flush; dut.io_kill_p = killP; dut.io_kill_r = killR;
    dut.io_op = q.op; dut.io_vl = q.vl; dut.io_vsew = q.sew;
    dut.io_vlmul = q.lmul; dut.io_vstart = q.start; dut.io_vill = q.vill;
    dut.io_vm = q.vm; dut.io_vta = q.vta; dut.io_vma = q.vma;
    dut.io_tag = q.tag; dut.io_write_v0 = q.v0;
    for (unsigned word = 0; word < 4; ++word) {
      uint32_t a = 0, b = 0;
      for (unsigned byte = 0; byte < 4; ++byte) {
        a |= uint32_t(q.a[4 * word + byte]) << (8 * byte);
        b |= uint32_t(q.b[4 * word + byte]) << (8 * byte);
      }
      dut.io_vs1[word] = a; dut.io_vs2[word] = b;
    }
    dut.eval();
    if (cycle != 0) {
      need(bool(dut.io_p_valid) == bool(p), "P occupancy");
      need(bool(dut.io_r_valid) == bool(r), "R occupancy");
      need(dut.io_occupancy == unsigned(bool(p)) + unsigned(bool(r)), "occupancy count");
    }
    const bool liveP = bool(p) && !killP && !reset;
    const bool liveR = bool(r) && !killR && !reset;
    const bool canMove = liveP && (!liveR || ready);
    const bool inReady = (!liveP || !liveR || ready) && !flush && !reset;
    need(bool(dut.io_in_ready) == inReady, "input readiness");
    need(bool(dut.io_out_valid) == liveR, "response validity/latency/kill");
    if (liveR) {
      uint32_t observed = dut.io_result[0];
      if (inject && !injected) { observed ^= 1; injected = true; }
      need(observed == r->result, "low result tag=" + std::to_string(r->tag));
      need(dut.io_result[1] == 0 && dut.io_result[2] == 0 && dut.io_result[3] == 0, "high96 zero");
      need(dut.io_out_tag == r->tag, "response identity");
      need(bool(dut.io_illegal) == r->illegal, "illegal state");
      need(bool(dut.io_v0_wen) == (!r->illegal && r->v0), "v0 write class");
      need(bool(dut.io_vec_wen) == (!r->illegal && !r->v0), "vector write class");
      if (!ready) ++blockedCycles;
    }
    const bool take = valid && inReady;
    if (r && ready && killR && !reset) ++readyKillR;
    if (liveR && ready && flush) ++redirectResponses;
    if (take) {
      ++accepted;
      if (q.op == 0) ++dot8Accepted;
      if (q.op == 1) ++dot16Accepted;
    }
    if (liveR && ready) { ++responded; if (r->illegal) ++illegalResponses; }
    if (p && (killP || reset)) ++killed;
    if (r && (killR || reset)) ++killed;
    if (liveR && ready && canMove && take) ++simultaneous;
    auto newR = liveR && !ready ? r : std::optional<Packet>{};
    if (canMove) newR = p;
    auto newP = liveP && !canMove ? p : std::optional<Packet>{};
    if (take) newP = expected(q);
    dut.clock = 1; dut.eval(); ++cycle;
    p = newP; r = newR;
    const uint64_t occupancy = uint64_t(bool(p)) + uint64_t(bool(r));
    if (occupancy > maxOccupancy) maxOccupancy = occupancy;
    return take;
  }
  void drain() {
    Request idle;
    for (unsigned n = 0; p || r; ++n) { need(n < 20, "drain timeout"); tick(idle, false, true); }
  }
};

int main(int argc, char **argv) {
  Verilated::commandArgs(argc, argv);
  if (argc < 2) return 2;
  const std::string variant(argv[1]);
  if (variant != "baseline8" && variant != "direct16" && variant != "split16") return 2;
  const bool inject = argc > 2 && std::string(argv[2]) == "--inject-result";
  if (inject) std::cout << "DOT16_PROTOTYPE_CHECKER_INJECTION result\n";
  try {
    Test t(variant != "baseline8", inject); Request idle;
    t.tick(idle, false, false, false, false, false, true);
    t.tick(idle, false, false, false, false, false, true);
    // Sustained burst checks the ideal two-edge response and II=1.
    for (unsigned i = 0; i < 64; ++i) {
      auto q = request(i & 1, -128, -128);
      t.need(t.tick(q, true, true), "burst should accept every cycle");
    }
    t.drain();
    // Full queue, unrelated redirect, each-slot kill, both kills, and reset.
    for (bool responseReady : {false, true}) for (unsigned action = 0; action < 5; ++action) {
      auto q1 = request(0, -128, 127), q2 = request(1, -128, -128);
      t.tick(q1, true, false); t.tick(q2, true, false);
      for (unsigned i = 0; i < 5; ++i) t.need(!t.tick(idle, true, false), "full queue blocks");
      t.tick(idle, true, responseReady, true, action == 1 || action == 3,
             action == 2 || action == 3, action == 4);
      t.drain();
    }
    std::vector<Request> samples; samples.reserve(141000);
    for (unsigned op = 0; op < 2; ++op)
      for (int a = -128; a < 128; ++a)
        for (int b = -128; b < 128; ++b) samples.push_back(request(op, a, b));
    for (unsigned i = 0; i < 8192; ++i) {
      auto q = request(i & 1, 0, 0);
      for (unsigned lane = 0; lane < 16; ++lane) { q.a[lane] = random64(); q.b[lane] = random64(); }
      samples.push_back(q);
    }
    for (unsigned op = 0; op < 2; ++op) {
      for (unsigned vl : {0u, 1u, 7u, 8u, 9u, 15u, 16u, 17u, 255u}) {
        auto q = request(op, -128, -128); q.vl = vl; samples.push_back(q);
      }
      for (unsigned sew = 1; sew < 4; ++sew) { auto q = request(op, 127, -128); q.sew = sew; samples.push_back(q); }
      for (unsigned lmul = 1; lmul < 8; ++lmul) { auto q = request(op, 127, -128); q.lmul = lmul; samples.push_back(q); }
      for (unsigned start : {1u, 255u}) { auto q = request(op, 127, -128); q.start = start; samples.push_back(q); }
      auto a = request(op, -128, -128); a.vill = true; samples.push_back(a);
      auto b = request(op, -128, -128); b.vm = false; samples.push_back(b);
    }
    samples.push_back(request(2, -128, -128)); samples.push_back(request(3, -128, -128));
    for (const auto &q : samples) {
      bool taken = false;
      for (unsigned attempts = 0; !taken; ++attempts) {
        t.need(attempts < 1000, "input progress timeout");
        const auto bits = random64();
        const bool flush = (bits & 2047) == 0;
        const bool reset = (bits & 65535) == 32768;
        taken = t.tick(q, true, (bits & 3) != 0, flush,
                       flush && (bits & 4096), flush && (bits & 8192), reset);
      }
    }
    t.drain();
    t.need(t.accepted == t.responded + t.killed, "conservation of requests");
    t.need(t.simultaneous >= 60 && t.maxOccupancy == 2 && t.blockedCycles > 0, "required flow coverage");
    t.need(t.illegalResponses > 0 && t.dot8Accepted > 65536 && t.dot16Accepted > 65536, "mode/illegal coverage");
    t.need(t.readyKillR >= 2 && t.redirectResponses >= 2, "ready response kill and unrelated redirect coverage");
    std::cout << "DOT16_PROTOTYPE_PASS variant=" << variant << " cycles=" << t.cycle
      << " accepted=" << t.accepted << " responded=" << t.responded << " killed=" << t.killed
      << " illegal_responses=" << t.illegalResponses << " simultaneous=" << t.simultaneous
      << " blocked_cycles=" << t.blockedCycles << " occupancy_max=" << t.maxOccupancy
      << " ready_kill_r=" << t.readyKillR << " redirect_responses=" << t.redirectResponses << "\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "DOT16_PROTOTYPE_FAIL " << e.what() << "\n"; return 1;
  }
}
