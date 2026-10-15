// Licensed under Mulan PSL v2; see LICENSE at the repository root.
package xiangshan.backend.fu.wrapper

import chisel3._
import chisel3.util._
import xiangshan.backend.decode.VdotInstructions

/** Late VDOT legality depends on physical VL and can fail after decode.
  * The ROB supplies the original instruction of the precise trap head;
  * the decode-only TrapInstMod buffer need not contain this instruction.
  */
object VdotTrapInstruction {
  def apply(trapValid: Bool, interrupt: Bool, illegal: Bool, instruction: UInt,
            buffered: ValidIO[UInt]): ValidIO[UInt] = {
    require(instruction.getWidth == 32 && buffered.bits.getWidth == 32)
    val ownFault = trapValid && !interrupt && illegal && (VdotInstructions.VDOT === instruction)
    val result = Wire(Valid(UInt(32.W)))
    result.valid := buffered.valid || ownFault
    result.bits := Mux(ownFault, instruction, buffered.bits)
    result
  }
}
