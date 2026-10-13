#include "VVDotFuTestTop.h"
#include "verilated.h"

#include <array>
#include <cstdlib>

#ifndef VDOT_RESPONSE_LATENCY
#define VDOT_RESPONSE_LATENCY 3
#endif
static_assert(VDOT_RESPONSE_LATENCY == 2 || VDOT_RESPONSE_LATENCY == 3);
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <optional>
#include <random>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using Words = std::array<uint32_t, 4>;
struct Vector {
  std::string id;
  Words vs1, vs2, expected;
};

Words parse_hex(const std::string& text) {
  if (text.size() != 32 || text.find_first_not_of("0123456789abcdef") != std::string::npos)
    throw std::runtime_error("invalid 128-bit input");
  Words words{};
  for (unsigned i = 0; i < 4; ++i)
    words[i] = static_cast<uint32_t>(std::stoul(text.substr(24 - 8 * i, 8), nullptr, 16));
  return words;
}

std::string hex(const Words& value) {
  std::ostringstream out;
  out << std::hex << std::setfill('0');
  for (int i = 3; i >= 0; --i) out << std::setw(8) << value[i];
  return out.str();
}

std::vector<Vector> load_vectors(const char* path) {
  std::ifstream input(path);
  if (!input) throw std::runtime_error("cannot open vector TSV");
  std::vector<Vector> vectors;
  std::set<std::string> ids;
  unsigned directed = 0, random = 0;
  std::string line;
  while (std::getline(input, line)) {
    std::istringstream row(line);
    std::string suite, id, a, b, expected, extra;
    if (!(row >> suite >> id >> a >> b >> expected) || (row >> extra))
      throw std::runtime_error("invalid vector row");
    if (!ids.insert(id).second) throw std::runtime_error("duplicate vector id");
    if (suite == "directed") ++directed;
    else if (suite == "random") ++random;
    else throw std::runtime_error("unknown suite");
    vectors.push_back({id, parse_hex(a), parse_hex(b), parse_hex(expected)});
  }
  if (!input.eof() || directed != 22 || random != 10000)
    throw std::runtime_error("expected exactly 22 directed and 10000 random vectors");
  return vectors;
}

struct Request {
  Vector data;
  unsigned vl = 8, ctrl_vl = 0, vsew = 0, vlmul = 0, vstart = 0, vxrm = 0, op = 0;
  bool vill = false, vm = true, vta = false, vma = false;
  bool rob_flag = false, write_v0 = false;
  unsigned rob_value = 0, pdest = 0;
  uint64_t tag = 0;

  bool illegal() const {
    return vill || vsew != 0 || vlmul != 0 || !vm || vstart != 0 || vl != 8 || op != 0;
  }
  uint32_t packed_ctrl() const {
    return (uint32_t(vill) << 26) | (uint32_t(vma) << 25) | (uint32_t(vta) << 24) |
           (vsew << 22) | (vlmul << 19) | (uint32_t(vm) << 18) |
           (vstart << 10) | (ctrl_vl << 2) | vxrm;
  }
};

struct Flush {
  bool valid = false, flag = false;
  unsigned value = 0;
  bool self = false;
};

// Independent circular-distance oracle; test pairs always lie within a ROB window.
bool should_kill(const Request& req, const Flush& flush) {
  if (!flush.valid) return false;
  const unsigned pos = unsigned(req.rob_flag) * 48 + req.rob_value;
  const unsigned redirect = unsigned(flush.flag) * 48 + flush.value;
  const unsigned distance = (pos + 96 - redirect) % 96;
  if (distance == 48) throw std::runtime_error("ambiguous test ROB window");
  return distance == 0 ? flush.self : distance < 48;
}

struct Pending {
  Request req;
  uint64_t accepted_cycle;
};

class Bench {
 public:
  std::unique_ptr<VerilatedContext> context = std::make_unique<VerilatedContext>();
  std::unique_ptr<VVDotFuTestTop> dut = std::make_unique<VVDotFuTestTop>(context.get());
  std::optional<Pending> pending;
  uint64_t cycle = 0, accepted = 0, responded = 0, killed = 0, reset_dropped = 0;
  uint64_t illegal_responses = 0, stall_cycles = 0, groups = 0;
  std::string label = "boot", inject;
  bool injected = false;

  static constexpr unsigned latency = VDOT_RESPONSE_LATENCY;
  std::ofstream trace;
  explicit Bench(std::string injection) : inject(std::move(injection)) {
    if (const char* path = std::getenv("VDOT_AB_TRACE")) {
      trace.open(path);
      if (!trace) throw std::runtime_error("cannot open raw trace");
      trace << "cycle\tlabel\tin_valid\tin_ready\tout_ready\tout_valid\treset\tflush_valid\tflush_flag\tflush_value\tflush_self\tin_rob_flag\tin_rob_value\tin_pdest\tin_tag\tinput_vector_id\tresult128\tout_rob_flag\tout_rob_value\tout_pdest\tout_vec_wen\tout_v0_wen\tout_exception\tout_ctrl\tout_tag\tout_rename_tag\tpost_edge_out_valid\n";
    }
  }

  void check(bool condition, const std::string& reason) const {
    if (!condition) {
      throw std::runtime_error("case=" + label + " cycle=" + std::to_string(cycle) + " " + reason);
    }
  }

  bool step(const Request& r, bool valid = false, bool ready = true,
            Flush flush = {}, bool reset = false) {
    dut->clock = 0;
    dut->reset = reset;
    dut->io_in_valid = valid;
    dut->io_out_ready = ready;
    for (unsigned i = 0; i < 4; ++i) {
      dut->io_vs1[i] = r.data.vs1[i];
      dut->io_vs2[i] = r.data.vs2[i];
      dut->io_old_vd[i] = uint32_t(cycle * 7919 + i) ^ 0xffffffffU;
      dut->io_mask[i] = uint32_t(cycle * 65537 + i) ^ 0x5a5a5a5aU;
    }
    dut->io_vl = r.vl;
    dut->io_ctrl_vl = r.ctrl_vl;
    dut->io_vsew = r.vsew;
    dut->io_vlmul = r.vlmul;
    dut->io_vstart = r.vstart;
    dut->io_vill = r.vill;
    dut->io_vm = r.vm;
    dut->io_vta = r.vta;
    dut->io_vma = r.vma;
    dut->io_vxrm = r.vxrm;
    dut->io_op = r.op;
    dut->io_rob_flag = r.rob_flag;
    dut->io_rob_value = r.rob_value;
    dut->io_pdest = r.pdest;
    dut->io_write_v0 = r.write_v0;
    dut->io_perf_tag = r.tag;
    dut->io_flush_valid = flush.valid;
    dut->io_flush_flag = flush.flag;
    dut->io_flush_value = flush.value;
    dut->io_flush_self = flush.self;
    dut->eval();

    const bool cancel = pending && should_kill(pending->req, flush);
    const bool expected_ready = !pending && !flush.valid && !reset;
    const bool expected_valid = pending && cycle >= pending->accepted_cycle + Bench::latency && !cancel && !reset;
    Words raw_result{};
    for (unsigned i = 0; i < 4; ++i) raw_result[i] = dut->io_result[i];
    if (trace) trace << cycle << '\t' << label << '\t' << valid << '\t'
      << unsigned(dut->io_in_ready) << '\t' << ready << '\t' << unsigned(dut->io_out_valid)
      << '\t' << reset << '\t' << flush.valid << '\t' << flush.flag << '\t' << flush.value << '\t' << flush.self
      << '\t' << r.rob_flag << '\t' << r.rob_value << '\t' << r.pdest << '\t' << r.tag
      << '\t' << r.data.id << '\t' << hex(raw_result) << '\t' << unsigned(dut->io_out_rob_flag) << '\t' << dut->io_out_rob_value
      << '\t' << dut->io_out_pdest << '\t' << unsigned(dut->io_out_vec_wen) << '\t' << unsigned(dut->io_out_v0_wen)
      << '\t' << dut->io_out_exception << '\t' << dut->io_out_ctrl << '\t' << dut->io_out_perf_tag
      << '\t' << dut->io_out_rename_tag;
    bool actual_valid = dut->io_out_valid;
    if (inject == "drop" && expected_valid && !injected) {
      actual_valid = false;
      injected = true;
      std::cerr << "VDOT_FU_FAULT_INJECTION drop\n";
    }
    if (inject == "cancel-leak" && cancel && !reset && !injected) {
      actual_valid = true;
      injected = true;
      std::cerr << "VDOT_FU_FAULT_INJECTION cancel-leak\n";
    }
    check(bool(dut->io_in_ready) == expected_ready, "input ready mismatch");
    check(actual_valid == expected_valid, "output valid/kill/latency mismatch");

    if (expected_valid) {
      const Request& saved = pending->req;
      const bool illegal = saved.illegal();
      Words result{};
      for (unsigned i = 0; i < 4; ++i) result[i] = dut->io_result[i];
      const Words expected = illegal ? Words{} : saved.data.expected;
      check(result == expected, "id=" + saved.data.id + " expected=0x" + hex(expected) + " actual=0x" + hex(result));
      unsigned dest = dut->io_out_pdest;
      if (inject == "identity" && !injected) {
        dest ^= 1;
        injected = true;
        std::cerr << "VDOT_FU_FAULT_INJECTION identity\n";
      }
      check(dest == saved.pdest, "pdest identity mismatch");
      check(bool(dut->io_out_rob_flag) == saved.rob_flag && dut->io_out_rob_value == saved.rob_value,
            "ROB identity mismatch");
      check(dut->io_out_exception == (illegal ? 4U : 0U), "exception vector mismatch");
      check(bool(dut->io_out_vec_wen) == (!illegal && !saved.write_v0) &&
            bool(dut->io_out_v0_wen) == (!illegal && saved.write_v0), "destination write enable mismatch");
      check(dut->io_out_ctrl == saved.packed_ctrl(), "vector control snapshot mismatch");
      check(dut->io_out_perf_tag == saved.tag &&
            dut->io_out_rename_tag == (saved.tag ^ UINT64_C(0xf0e1d2c3b4a59687)), "debug identity mismatch");
      if (!ready) ++stall_cycles;
    }

    const bool input_fire = valid && expected_ready;
    if (reset) {
      if (pending) ++reset_dropped;
      pending.reset();
    } else if (cancel) {
      ++killed;
      pending.reset();
    } else if (expected_valid && ready) {
      ++responded;
      if (pending->req.illegal()) ++illegal_responses;
      pending.reset();
    }
    if (input_fire) {
      check(!pending, "more than one request in flight");
      pending = Pending{r, cycle};
      ++accepted;
    }
    check(accepted == responded + killed + reset_dropped + unsigned(pending.has_value()), "transaction accounting mismatch");
    dut->clock = 1;
    dut->eval();
    if (trace) trace << '\t' << unsigned(dut->io_out_valid) << '\n';
    context->timeInc(1);
    ++cycle;
    return input_fire;
  }

  void drain(const Request& noise, unsigned stalls = 0) {
    unsigned watchdog = 0;
    while (pending) {
      check(++watchdog <= stalls + 10, "response timeout");
      const bool mature = cycle >= pending->accepted_cycle + Bench::latency;
      const bool ready = !mature || stalls == 0;
      if (mature && stalls) --stalls;
      // Continuously alter unaccepted data to expose failures to snapshot.
      Request changing = noise;
      changing.tag ^= cycle;
      changing.pdest = unsigned(cycle % 160);
      step(changing, true, ready);
    }
  }

  void run(const Request& r, const Request& noise, unsigned stalls = 0) {
    check(!pending, "run requires idle");
    check(step(r, true), "request was not accepted");
    drain(noise, stalls);
  }

  void group(const std::string& name) {
    ++groups;
    std::cout << "VDOT_FU_GROUP_PASS " << name << '\n';
  }
};

Request request(const Vector& v, unsigned serial) {
  Request r;
  r.data = v;
  r.pdest = serial % 160;
  r.rob_value = serial % 48;
  r.rob_flag = (serial / 48) % 2;
  r.write_v0 = serial % 2;
  r.tag = UINT64_C(0xf123456789abcdef) ^ (UINT64_C(0x100000001) * serial);
  r.ctrl_vl = (serial * 17) % 256;  // Decoy: legality must use the renamed VL port.
  r.vta = (serial >> 1) & 1;
  r.vma = (serial >> 2) & 1;
  r.vxrm = serial % 4;
  return r;
}

void tests(Bench& b, const std::vector<Vector>& data) {
  const Request noise = request(data[7], 777);
  b.step(noise, false, true, {}, true);
  b.step(noise, false, true, {}, true);
  for (unsigned i = 0; i < 4; ++i) b.step(noise);  // No valid input means no response.

  b.label = "all-vectors-with-backpressure";
  const unsigned stalls[] = {0, 1, 2, 7};
  size_t next = 0;
  unsigned held = 0;
  uint64_t previous_accept = 0;
  while (next < data.size() || b.pending) {
    const Request r = next < data.size() ? request(data[next], unsigned(next)) : noise;
    bool ready = true;
    if (b.pending && b.cycle >= b.pending->accepted_cycle + Bench::latency) {
      ready = held == 0;
      if (held) --held;
    }
    const uint64_t before = b.cycle;
    if (b.step(r, next < data.size(), ready)) {
      if (next) b.check(before - previous_accept == Bench::latency + 1 + stalls[(next - 1) % 4], "initiation interval mismatch");
      previous_accept = before;
      held = stalls[next % 4];
      ++next;
    }
    b.check(b.cycle < 150000, "vector stream timeout");
  }
  b.step(noise);
  b.check(b.responded == 10022, "not all arithmetic requests completed");
  b.group("arithmetic=10022 stalls=0,1,2,7 continuous-valid identity-snapshot latency-II");

  b.label = "configuration-rejection";
  const uint64_t before_illegal = b.illegal_responses;
  unsigned serial = 20000;
  auto bad = [&](auto change) {
    Request r = request(data[3], serial++);
    change(r);
    b.check(r.illegal(), "invalid test must be rejected");
    b.run(r, noise, 2);
  };
  for (unsigned v : {1U, 2U, 3U}) bad([&](Request& r) { r.vsew = v; });
  for (unsigned v = 1; v < 8; ++v) bad([&](Request& r) { r.vlmul = v; });
  for (unsigned v : {0U, 1U, 7U, 9U, 16U, 255U}) bad([&](Request& r) { r.vl = v; });
  for (unsigned v : {1U, 127U, 255U}) bad([&](Request& r) { r.vstart = v; });
  bad([](Request& r) { r.vill = true; });
  bad([](Request& r) { r.vm = false; });
  bad([](Request& r) { r.op = 1; });
  b.check(b.illegal_responses - before_illegal == 22, "illegal coverage count");
  for (unsigned policy = 0; policy < 4; ++policy) {
    for (unsigned vxrm = 0; vxrm < 4; ++vxrm) {
      Request r = request(data[7], serial++);
      r.vta = policy & 1;
      r.vma = policy & 2;
      r.vxrm = vxrm;
      r.ctrl_vl = 255;
      b.run(r, noise, 1);
    }
  }
  b.group("illegal=22 policy-vxrm=16 renamed-VL exception-no-write");

  b.label = "idle-redirect-blocks-new-input";
  Request r = request(data[3], serial++);
  for (bool self : {false, true}) {
    b.check(!b.step(r, true, true, {true, r.rob_flag, r.rob_value, self}), "accepted during redirect");
    for (unsigned i = 0; i < 5; ++i) b.step(noise);
    b.run(r, noise);
  }
  b.group("idle-flush input-not-accepted recovery");

  struct Relation { bool rf; unsigned rv; bool ff; unsigned fv; bool self; bool kill; };
  const Relation relations[] = {
    {0,12,0,10,0,1}, {0,8,0,10,0,0}, {0,10,0,10,0,0}, {0,10,0,10,1,1},
    {1,1,0,47,0,1}, {0,47,1,1,0,0}, {0,1,1,47,0,1}, {1,47,0,1,0,0}
  };
  const std::vector<unsigned> phases = Bench::latency == 3 ?
    std::vector<unsigned>{1, 2, 3, 10} : std::vector<unsigned>{1, 2, 9};
  unsigned cancel_cases = 0;
  for (const auto& relation : relations) {
    for (unsigned phase : phases) {
      for (bool ready : {false, true}) {
        b.label = "redirect-case-" + std::to_string(cancel_cases++);
        Request q = request(data[3], serial++);
        q.rob_flag = relation.rf; q.rob_value = relation.rv;
        const Flush flush{true, relation.ff, relation.fv, relation.self};
        b.check(should_kill(q, flush) == relation.kill, "incorrect directed oracle");
        b.check(b.step(q, true), "accept before redirect");
        for (unsigned age = 1; age < phase; ++age) b.step(noise, true, false);
        b.step(noise, true, ready, flush);
        if (relation.kill) {
          b.check(!b.pending, "cancel failed");
          for (unsigned i = 0; i < 5; ++i) b.step(noise);
        } else {
          b.drain(noise, 2);
        }
        b.run(request(data[7], serial++), noise);  // Recovery, including a changed destination class.
      }
    }
  }
  b.check(cancel_cases == 16 * phases.size(), "redirect matrix incomplete");
  b.group("redirect-matrix=" + std::to_string(cancel_cases) + " all-active-phases older-self-wrap handshake-priority");

  b.label = "reset-at-each-phase";
  const uint64_t before_reset = b.reset_dropped;
  for (unsigned phase : phases) {
    b.check(b.step(request(data[7], serial++), true), "accept before reset");
    for (unsigned age = 1; age < phase; ++age) b.step(noise, true, false);
    b.step(noise, true, true, {}, true);
    for (unsigned i = 0; i < 5; ++i) b.step(noise);
    b.run(request(data[3], serial++), noise);
  }
  b.check(b.reset_dropped - before_reset == phases.size(), "reset matrix incomplete");
  b.group("reset-phases=" + std::to_string(phases.size()) + " no-ghost-response recovery");

  b.label = "random-control-stress";
  std::mt19937 rng(0x20261013);
  for (unsigned i = 0; i < 5000; ++i) {
    Request q = request(data[rng() % data.size()], serial++);
    if (rng() % 11 == 0) q.vl = 7;
    Flush f{};
    if (rng() % 7 == 0) {
      const unsigned pos = b.pending ? unsigned(b.pending->req.rob_flag) * 48 + b.pending->req.rob_value : 0;
      const unsigned redirect = (pos + 96 + (rng() % 25) - 12) % 96;
      f = {true, bool(redirect / 48), redirect % 48, bool(rng() % 2)};
    }
    const bool valid = rng() % 4 != 0;
    const bool ready = rng() % 3 != 0;
    const bool reset = rng() % 211 == 0;
    b.step(q, valid, ready, f, reset);
  }
  b.drain(noise);
  for (unsigned i = 0; i < 8; ++i) b.step(noise);
  b.group("random-control cycles=5000 seed=0x20261013 conservation-watchdog");
  b.check(!b.pending && b.accepted == b.responded + b.killed + b.reset_dropped, "final accounting");
  b.dut->final();
}
}  // namespace

int main(int argc, char** argv) {
  if (argc < 2 || argc > 3) {
    std::cerr << "usage: fu_test vectors.tsv [--inject-identity|--inject-cancel-leak|--inject-drop]\n";
    return 2;
  }
  std::string injection;
  if (argc == 3) {
    const std::string arg = argv[2];
    if (arg == "--inject-identity") injection = "identity";
    else if (arg == "--inject-cancel-leak") injection = "cancel-leak";
    else if (arg == "--inject-drop") injection = "drop";
    else return 2;
  }
  try {
    auto data = load_vectors(argv[1]);
    Bench bench(injection);
    tests(bench, data);
    if (!injection.empty()) throw std::runtime_error("fault injection was not rejected");
    std::cout << "VDOT_FU_PASS groups=" << bench.groups << " cycles=" << bench.cycle
              << " response_latency=" << Bench::latency << " no_stall_II=" << Bench::latency + 1
              << " accepted=" << bench.accepted << " responded=" << bench.responded
              << " killed=" << bench.killed << " reset_dropped=" << bench.reset_dropped
              << " illegal_responses=" << bench.illegal_responses << " stall_cycles=" << bench.stall_cycles << '\n';
    return 0;
  } catch (const std::exception& e) {
    std::cerr << "VDOT_FU_FAIL " << e.what() << '\n';
    return 1;
  }
}
