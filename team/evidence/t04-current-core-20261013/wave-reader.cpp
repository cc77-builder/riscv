#include <fstapi.h>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <string>
#include <vector>
#include <map>
#include <regex>

static std::map<fstHandle, std::vector<std::string>> selected;
static void change(void*, uint64_t time, fstHandle handle, const unsigned char* value) {
  for (const auto& name : selected.at(handle))
    std::printf("%llu,%s,%s\n", static_cast<unsigned long long>(time), name.c_str(), value);
}
int main(int argc, char** argv) {
  if (argc != 4) return 2;
  void* reader = fstReaderOpen(argv[1]);
  if (!reader) return 3;
  std::regex pattern(argv[3]);
  std::vector<std::string> scopes;
  fstReaderClrFacProcessMaskAll(reader);
  while (auto* h = fstReaderIterateHier(reader)) {
    if (h->htyp == FST_HT_SCOPE) scopes.push_back(h->u.scope.name);
    else if (h->htyp == FST_HT_UPSCOPE) scopes.pop_back();
    else if (h->htyp == FST_HT_VAR) {
      std::string name;
      for (const auto& scope : scopes) name += scope + ".";
      name += h->u.var.name;
      if (std::regex_search(name, pattern)) {
        selected[h->u.var.handle].push_back(name);
        fstReaderSetFacProcessMask(reader, h->u.var.handle);
        if (std::string(argv[2]) == "list")
          std::printf("%s,%u,%u\n", name.c_str(), h->u.var.handle, h->u.var.length);
      }
    }
  }
  if (selected.empty()) return 4;
  if (std::string(argv[2]) == "events") {
    std::puts("time,signal,value");
    if (!fstReaderIterBlocks(reader, change, nullptr, nullptr)) return 5;
  } else if (std::string(argv[2]) != "list") return 2;
  fstReaderClose(reader);
  return 0;
}
