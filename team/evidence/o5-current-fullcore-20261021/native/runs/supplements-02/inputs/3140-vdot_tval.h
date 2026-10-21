/* Team platform adapter; Mulan PSL v2, like the surrounding NEMU code.
 * RISC-V Privileged 1.13 permits zero or instruction bits for illegal xTVAL.
 * This profile matches pinned XS DecodeStage -> TrapInstMod -> TrapEntry:
 * only VL is unavailable at decode for an otherwise valid vdot request.
 * It does not inspect a DUT result, PC, test ID, or expected output.
 */
#ifndef XS_VDOT_TVAL_POLICY_H
#define XS_VDOT_TVAL_POLICY_H
#include <stdbool.h>
#include <stdint.h>
static inline bool xs_vdot_tval_is_zero(uint32_t instruction, bool vector_enabled,
                                        uint64_t type, uint64_t length, uint64_t start) {
  return (instruction & UINT32_C(0xfe00707f)) == UINT32_C(0x0200000b) &&
         vector_enabled && (type & ~UINT64_C(0xc0)) == 0 &&
         start == 0 && length != 8;
}
#endif
