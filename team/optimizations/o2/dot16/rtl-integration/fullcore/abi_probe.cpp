#include <cstdio>
#include <cstddef>
#include "refproxy.h"

#if !defined(CONFIG_DIFFTEST_ARCHFPREGSTATE) || !defined(CONFIG_DIFFTEST_HCSRSTATE) || \
    !defined(CONFIG_DIFFTEST_ARCHVECREGSTATE) || !defined(CONFIG_DIFFTEST_VECCSRSTATE) || \
    !defined(CONFIG_DIFFTEST_FPCSRSTATE) || !defined(CONFIG_DIFFTEST_TRIGGERCSRSTATE)
#error "This fixed reference requires all recorded architectural state sections"
#endif

/* GCC's conditionally-supported offsetof measures the actual compiled RefProxy
 * prefix without creating a proxy or invoking the reference library. */
int main() {
  const size_t base = offsetof(RefProxy, regs_int);
#define OFFSET(field) (offsetof(RefProxy, field) - base)
  const size_t bytes = OFFSET(triggercsr) + sizeof(DifftestTriggerCSRState);
  std::printf("{\"bytes\":%zu,\"regs_int\":%zu,\"regs_fp\":%zu,\"csr\":%zu,\"pc\":%zu,"
              "\"hcsr\":%zu,\"regs_vec\":%zu,\"vcsr\":%zu,\"fcsr\":%zu,\"triggercsr\":%zu}\n",
              bytes, OFFSET(regs_int), OFFSET(regs_fp), OFFSET(csr), OFFSET(pc),
              OFFSET(hcsr), OFFSET(regs_vec), OFFSET(vcsr), OFFSET(fcsr), OFFSET(triggercsr));
  return 0;
}
