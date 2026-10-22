#include "VVDotParamTestTop.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Words = std::array<uint32_t, 4>;
struct InputError : std::runtime_error { using std::runtime_error::runtime_error; };
struct Vector { std::string suite, id; Words a, b, expected; };
struct Pending { size_t index; uint32_t tag; uint64_t accepted; };

Words parse(const std::string& text) {
  if (text.size() != 32) throw InputError("expected 32 hexadecimal digits");
  Words words{};
  for (size_t i = 0; i < text.size(); ++i) {
    const char ch = text[i];
    unsigned value;
    if (ch >= '0' && ch <= '9') value = ch - '0';
    else if (ch >= 'a' && ch <= 'f') value = ch - 'a' + 10;
    else if (ch >= 'A' && ch <= 'F') value = ch - 'A' + 10;
    else throw InputError("invalid hexadecimal digit");
    words[3 - i / 8] = (words[3 - i / 8] << 4) | value;
  }
  return words;
}
std::string hex(const Words& words) {
  std::ostringstream out;
  out << std::hex << std::setfill('0');
  for (int i = 3; i >= 0; --i) out << std::setw(8) << words[i];
  return out.str();
}
std::vector<Vector> load(const char* path) {
  std::ifstream in(path);
  if (!in) throw InputError("cannot open vectors");
  std::vector<Vector> rows;
  std::set<std::string> ids;
  size_t directed = 0, random = 0;
  std::string line;
  while (std::getline(in, line)) {
    std::istringstream fields(line);
    std::string suite, id, a, b, expected, extra;
    if (!(fields >> suite >> id >> a >> b >> expected) || (fields >> extra)) throw InputError("five fields required");
    if (suite == "directed") ++directed;
    else if (suite == "random") ++random;
    else throw InputError("unknown suite");
    if (!ids.insert(suite + ":" + id).second) throw InputError("duplicate case id");
    rows.push_back({suite, id, parse(a), parse(b), parse(expected)});
  }
  if (!in.eof() || rows.size() != T15_COUNT || directed != T15_DIRECTED || random != 10000)
    throw InputError("corpus count mismatch");
  return rows;
}
uint32_t next(uint32_t& state) { state = state * 1664525u + 1013904223u; return state; }

class Runner {
 public:
  std::unique_ptr<VerilatedContext> context = std::make_unique<VerilatedContext>();
  std::unique_ptr<VVDotParamTestTop> dut = std::make_unique<VVDotParamTestTop>(context.get());
  const std::vector<Vector>& vectors;
  std::ofstream trace, comb;
  std::optional<Pending> pending;
  std::string fault;
  bool injected = false;
  uint64_t cycle = 0, accepted = 0, responses = 0, killed = 0, reset_dropped = 0, stalls = 0;
  uint64_t minimum_interval = std::numeric_limits<uint64_t>::max(), last_functional_accept = 0;
  bool had_functional_accept = false;

  Runner(const std::vector<Vector>& rows, const std::string& prefix, const std::string& mode)
      : vectors(rows), trace(prefix + "-cycles.tsv"), comb(prefix + "-comb.tsv"), fault(mode) {
    if (!trace || !comb) throw InputError("cannot open output trace");
    trace << "cycle phase index reset flush in_valid in_ready tag_in out_valid out_ready tag_out result\n";
    comb << "index result legacy\n";
  }
  void fail(const std::string& message) {
    throw std::runtime_error("cycle=" + std::to_string(cycle) + " " + message);
  }
  void sources(size_t index) {
    for (size_t i = 0; i < 4; ++i) {
      dut->io_vs1[i] = vectors[index].a[i];
      dut->io_vs2[i] = vectors[index].b[i];
    }
  }
  Words pipe_result() {
    Words result{};
    for (size_t i = 0; i < 4; ++i) result[i] = dut->io_pipeResult[i];
    return result;
  }
  void combination(size_t index) {
    dut->clock = 0;
    sources(index);
    dut->eval();
    Words actual{}, legacy{};
    for (size_t i = 0; i < 4; ++i) {
      actual[i] = dut->io_combResult[i];
      legacy[i] = dut->io_legacyResult[i];
    }
    comb << index << ' ' << hex(actual) << ' ' << hex(legacy) << '\n';
    if (actual != vectors[index].expected) fail("combinational mismatch index=" + std::to_string(index));
    if (T15_BASELINE && legacy != actual) fail("production baseline mismatch");
  }
  void step(const std::string& phase, size_t index, bool valid, bool ready,
            bool flush = false, bool reset = false, uint32_t tag = 0) {
    dut->clock = 0;
    dut->reset = reset;
    dut->io_flush = flush;
    dut->io_inValid = valid;
    dut->io_outReady = ready;
    dut->io_tagIn = tag;
    sources(index);
    dut->eval();
    const bool in_ready = dut->io_inReady, out_valid = dut->io_outValid;
    Words actual = pipe_result();
    uint32_t out_tag = dut->io_tagOut;
    if (out_valid && !fault.empty() && !injected) {
      injected = true;
      if (fault == "tag") out_tag ^= 0x80000000u;
      else {
        const unsigned bit = static_cast<unsigned>(std::stoi(fault.substr(3)));
        actual[bit / 32] ^= uint32_t{1} << (bit % 32);
      }
      std::cerr << "T15_READBACK_INJECTION fault=" << fault << " cycle=" << cycle << '\n';
    }
    trace << cycle << ' ' << phase << ' ' << index << ' ' << reset << ' ' << flush << ' '
          << valid << ' ' << in_ready << ' ' << tag << ' ' << out_valid << ' ' << ready << ' '
          << out_tag << ' ' << hex(actual) << '\n';
    const bool expected_ready = !pending && !flush && !reset;
    const bool expected_valid = pending && cycle - pending->accepted >= 2 && !flush && !reset;
    if (in_ready != expected_ready) fail("input-ready contract");
    if (out_valid != expected_valid) fail("response latency/cancellation contract");
    if (out_valid) {
      if (actual != vectors[pending->index].expected) fail("full-128-bit mismatch index=" + std::to_string(pending->index));
      if (out_tag != pending->tag) fail("transaction identity mismatch");
      if (!ready) ++stalls;
    }
    if (reset) {
      if (pending) ++reset_dropped;
      pending.reset();
    } else if (flush) {
      if (pending) ++killed;
      pending.reset();
    } else {
      if (out_valid && ready) { ++responses; pending.reset(); }
      if (valid && in_ready) {
        if (pending) fail("overlapping acceptance");
        pending = Pending{index, tag, cycle};
        ++accepted;
        if (phase == "functional") {
          if (had_functional_accept) minimum_interval = std::min(minimum_interval, cycle - last_functional_accept);
          had_functional_accept = true;
          last_functional_accept = cycle;
        }
      }
    }
    if (accepted != responses + killed + reset_dropped + (pending ? 1 : 0)) fail("transaction conservation");
    dut->clock = 1;
    dut->eval();
    ++cycle;
  }
  void run() {
    step("startup",0,false,false,false,true);
    step("startup",0,false,false,false,true);
    const unsigned hold[] = {0,1,2,7};
    for (size_t i = 0; i < vectors.size(); ++i) {
      combination(i);
      step("functional",i,true,true,false,false,0xa5100000u ^ static_cast<uint32_t>(i));
      step("functional",(i+1)%vectors.size(),true,false,false,false,0xdeadbeefu);
      for (unsigned j = 0; j < hold[i%4]; ++j)
        step("functional",(i+j+2)%vectors.size(),true,false,false,false,0x5a5a0000u+j);
      step("functional",(i+7)%vectors.size(),true,true,false,false,0xffffffffu);
      if (pending) fail("functional transaction not drained");
    }
    if (minimum_interval != 3) fail("minimum no-cancel initiation interval must be 3");
    const uint64_t functional_cycles = cycle - 2;
    // Conflict on acceptance, early cancellation, response-edge cancellation,
    // cancellation after output stalls, plus the same positions under reset.
    step("control",0,true,true,true,false,0x12345678u);
    for (unsigned is_reset = 0; is_reset < 2; ++is_reset) {
      for (unsigned age : {1u,2u,5u}) {
        for (unsigned repeat = 0; repeat < 16; ++repeat) {
          size_t idx = (repeat*17+age)%vectors.size();
          step("control",idx,true,true,false,false,0xf0000000u+repeat);
          for (unsigned wait = 1; wait < age; ++wait)
            step("control",(idx+wait)%vectors.size(),true,false,false,false,wait);
          step("control",(idx+1)%vectors.size(),true,true,!is_reset,is_reset,0x11223344u);
          step("control",(idx+2)%vectors.size(),false,true);
        }
      }
    }
    uint32_t rng = 0x20261017u;
    for (size_t i = 0; i < 10000; ++i) {
      uint32_t flags = next(rng), tag = next(rng);
      size_t idx = next(rng)%vectors.size();
      step("random-control",idx,(flags&7)!=0,((flags>>3)&7)>1,
           (flags>>6)%37==0,(flags>>12)%101==0,tag);
    }
    for (unsigned i = 0; i < 4; ++i) step("drain",i,false,true);
    if (pending || !killed || !reset_dropped || !stalls) fail("incomplete control coverage");
    if (!fault.empty()) fail("injected readback error was not rejected");
    dut->final();
    trace.flush(); comb.flush();
    if (!trace || !comb) fail("trace write failed");
    std::cout << "{\"status\":\"T15_RTL_PASS\",\"profile\":\"" << (T15_BASELINE ? "s8x8" : "s16x8")
              << "\",\"vectors\":" << vectors.size() << ",\"directed\":" << T15_DIRECTED
              << ",\"random\":10000,\"first_valid_latency\":2,\"minimum_functional_accept_interval\":" << minimum_interval
              << ",\"functional_cycles\":" << functional_cycles << ",\"cycles\":" << cycle
              << ",\"accepted\":" << accepted << ",\"responses\":" << responses
              << ",\"killed\":" << killed << ",\"reset_dropped\":" << reset_dropped
              << ",\"stall_cycles\":" << stalls << ",\"random_control_cycles\":10000}\n";
  }
};
int main(int argc, char** argv) {
  try {
    if (argc < 3 || argc > 4) throw InputError("usage: vectors.tsv trace-prefix [--inject=bit0|bit33|bit63|bit127|tag]");
    std::string fault;
    if (argc == 4) {
      std::string opt = argv[3];
      const std::set<std::string> allowed = {"--inject=bit0","--inject=bit33","--inject=bit63","--inject=bit127","--inject=tag"};
      if (!allowed.count(opt)) throw InputError("invalid injection option");
      fault = opt.substr(9);
    }
    auto vectors = load(argv[1]);
    Runner runner(vectors,argv[2],fault);
    runner.run();
    return 0;
  } catch (const InputError& error) {
    std::cerr << "T15_INPUT_ERROR " << error.what() << '\n'; return 2;
  } catch (const std::exception& error) {
    std::cerr << "T15_RTL_FAIL " << error.what() << '\n'; return 1;
  }
}
