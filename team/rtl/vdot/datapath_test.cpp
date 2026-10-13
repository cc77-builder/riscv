#include "VVDotDatapath.h"
#include "verilated.h"

#include <array>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <set>
#include <sstream>
#include <string>

namespace {

using Words = std::array<uint32_t, 4>;

bool parse_hex128(const std::string& text, Words& words) {
  if (text.size() != 32) return false;
  words.fill(0);
  for (size_t i = 0; i < text.size(); ++i) {
    const char c = text[i];
    unsigned digit;
    if (c >= '0' && c <= '9') {
      digit = static_cast<unsigned>(c - '0');
    } else if (c >= 'a' && c <= 'f') {
      digit = static_cast<unsigned>(c - 'a' + 10);
    } else if (c >= 'A' && c <= 'F') {
      digit = static_cast<unsigned>(c - 'A' + 10);
    } else {
      return false;
    }
    const size_t word = 3 - i / 8;
    words[word] = (words[word] << 4) | digit;
  }
  return true;
}

std::string hex128(const Words& words) {
  std::ostringstream out;
  out << std::hex << std::setfill('0');
  for (int i = 3; i >= 0; --i) out << std::setw(8) << words[i];
  return out.str();
}

int input_error(const std::string& message) {
  std::cerr << "VDOT_DATAPATH_INPUT_ERROR " << message << '\n';
  return 2;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc < 2 || argc > 3) {
    return input_error("usage: datapath_test vectors.tsv [--inject-bit=0|--inject-bit=127]");
  }
  int inject_bit = -1;
  if (argc == 3) {
    const std::string option = argv[2];
    if (option == "--inject-bit=0") {
      inject_bit = 0;
    } else if (option == "--inject-bit=127") {
      inject_bit = 127;
    } else {
      return input_error("unsupported option: " + option);
    }
  }

  std::ifstream input(argv[1]);
  if (!input) return input_error("cannot open vector file: " + std::string(argv[1]));

  auto context = std::make_unique<VerilatedContext>();
  auto dut = std::make_unique<VVDotDatapath>(context.get());
  std::set<std::string> seen_ids;
  size_t directed_count = 0;
  size_t random_count = 0;
  size_t line_number = 0;
  bool injected = false;
  std::string line;
  while (std::getline(input, line)) {
    ++line_number;
    std::istringstream fields(line);
    std::string suite, id, vs1_text, vs2_text, expected_text, extra;
    if (!(fields >> suite >> id >> vs1_text >> vs2_text >> expected_text) || (fields >> extra)) {
      return input_error("line=" + std::to_string(line_number) + " requires exactly five fields");
    }
    if (suite != "directed" && suite != "random") {
      return input_error("line=" + std::to_string(line_number) + " unknown suite=" + suite);
    }
    if (!seen_ids.insert(suite + ":" + id).second) {
      return input_error("line=" + std::to_string(line_number) + " duplicate suite/id=" + suite + "/" + id);
    }
    Words vs1, vs2, expected;
    if (!parse_hex128(vs1_text, vs1) || !parse_hex128(vs2_text, vs2) ||
        !parse_hex128(expected_text, expected)) {
      return input_error("line=" + std::to_string(line_number) + " requires three 32-digit hex values without 0x");
    }
    if (suite == "directed") {
      ++directed_count;
    } else {
      ++random_count;
    }
    if (directed_count > 22 || random_count > 10000) {
      return input_error("line=" + std::to_string(line_number) + " exceeds expected suite size");
    }

    for (size_t i = 0; i < 4; ++i) {
      dut->io_vs1[i] = vs1[i];
      dut->io_vs2[i] = vs2[i];
    }
    dut->eval();
    Words actual;
    for (size_t i = 0; i < 4; ++i) actual[i] = dut->io_result[i];
    if (inject_bit >= 0 && !injected) {
      actual[static_cast<unsigned>(inject_bit) / 32] ^= uint32_t{1} << (inject_bit % 32);
      injected = true;
      std::cerr << "VDOT_DATAPATH_FAULT_INJECTION bit=" << inject_bit
                << " suite=" << suite << " id=" << id << '\n';
    }
    if (actual != expected) {
      std::cerr << "VDOT_DATAPATH_MISMATCH suite=" << suite << " id=" << id
                << " vs1=0x" << hex128(vs1) << " vs2=0x" << hex128(vs2)
                << " expected=0x" << hex128(expected) << " actual=0x" << hex128(actual) << '\n';
      dut->final();
      return 1;
    }
  }
  if (!input.eof()) return input_error("failed while reading vector file");
  if (directed_count != 22 || random_count != 10000) {
    return input_error("expected directed=22 random=10000; observed directed=" +
                       std::to_string(directed_count) + " random=" + std::to_string(random_count));
  }
  dut->final();
  if (inject_bit >= 0) {
    std::cerr << "VDOT_DATAPATH_FAULT_INJECTION_NOT_REJECTED bit=" << inject_bit << '\n';
    return 1;
  }
  std::cout << "VDOT_DATAPATH_SUITE_PASS suite=directed count=" << directed_count << '\n'
            << "VDOT_DATAPATH_SUITE_PASS suite=random count=" << random_count << '\n'
            << "VDOT_DATAPATH_PASS directed=22 random=10000 total=10022\n";
  return 0;
}
