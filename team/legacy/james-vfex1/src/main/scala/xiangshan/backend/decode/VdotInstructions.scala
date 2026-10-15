// Licensed under Mulan PSL v2; see LICENSE at the repository root.
package xiangshan.backend.decode

import chisel3.util.BitPat

/** Candidate vdot-s8x8-r32-v0.1: only the three register fields vary.
  * In particular vm=0 and adjacent custom-0 encodings are not VDOT.
  */
object VdotInstructions {
  val VDOT = BitPat("b0000001_?????_?????_000_?????_0001011")
}
