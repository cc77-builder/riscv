// Licensed under Mulan PSL v2; see LICENSE at the repository root.
package xiangshan.backend.fu.vector

import chisel3._
import chisel3.util._
import chiseltest._
import org.scalatest.flatspec.AnyFlatSpec
import xiangshan.backend.fu.wrapper.VdotTrapInstruction

class VdotTrapInstructionHarness extends Module {
  val io = IO(new Bundle {
    val trap = Input(Bool())
    val interrupt = Input(Bool())
    val illegal = Input(Bool())
    val instruction = Input(UInt(32.W))
    val buffered = Flipped(Valid(UInt(32.W)))
    val out = Valid(UInt(32.W))
  })
  io.out := VdotTrapInstruction(io.trap, io.interrupt, io.illegal, io.instruction, io.buffered)
}

class VdotTrapInstructionSpec extends AnyFlatSpec with ChiselScalatestTester {
  behavior of "VDOT precise trap instruction"
  it should "report the actual late-fault word without changing buffered non-VDOT traps" in {
    test(new VdotTrapInstructionHarness).withAnnotations(Seq(VerilatorBackendAnnotation)) { dut =>
      dut.io.trap.poke(true.B); dut.io.interrupt.poke(false.B); dut.io.illegal.poke(true.B)
      val poison = BigInt("deadbeef", 16)
      dut.io.buffered.bits.poke(poison.U)
      var checks = 0
      for (vd <- 0 until 32; a <- 0 until 32; b <- 0 until 32; buffered <- Seq(false, true)) {
        val word = BigInt(0x0200000bL | vd.toLong << 7 | a.toLong << 15 | b.toLong << 20)
        dut.io.instruction.poke(word.U); dut.io.buffered.valid.poke(buffered.B)
        dut.io.out.valid.expect(true.B); dut.io.out.bits.expect(word.U); checks += 1
      }
      for (trap <- Seq(false, true); interrupt <- Seq(false, true); illegal <- Seq(false, true);
           buffered <- Seq(false, true)) {
        dut.io.trap.poke(trap.B); dut.io.interrupt.poke(interrupt.B); dut.io.illegal.poke(illegal.B)
        dut.io.buffered.valid.poke(buffered.B); dut.io.instruction.poke("h0294050b".U)
        val own = trap && !interrupt && illegal
        dut.io.out.valid.expect((buffered || own).B)
        dut.io.out.bits.expect((if (own) BigInt("0294050b", 16) else poison).U); checks += 1
      }
      dut.io.trap.poke(true.B); dut.io.interrupt.poke(false.B); dut.io.illegal.poke(true.B)
      val mask = BigInt("fe00707f", 16)
      for (bit <- 0 until 32 if mask.testBit(bit); buffered <- Seq(false, true)) {
        dut.io.buffered.valid.poke(buffered.B)
        dut.io.instruction.poke((BigInt("0294050b", 16) ^ (BigInt(1) << bit)).U)
        dut.io.out.valid.expect(buffered.B); dut.io.out.bits.expect(poison.U); checks += 1
      }
      println(s"VDOT_TRAP_INSTRUCTION_PASS checks=$checks original_words=32768 buffered_priorities=2")
    }
  }
}
