// Licensed under Mulan PSL v2; see LICENSE at the repository root.
package xiangshan.backend.fu.vector

import chisel3._
import chisel3.util._

/** Inputs belong to one instruction. vl must come from its physical VL source,
  * and vtype/vstart/VS must be that instruction's control snapshot.
  * tag is opaque: the adapter owns ROB, physical destination and PC metadata.
  */
class VdotRequest(tagWidth: Int) extends Bundle {
  val instruction = UInt(32.W)
  val src1 = UInt(128.W)
  val src2 = UInt(128.W)
  val vl = UInt(8.W)
  val vtype = UInt(64.W)
  val vstart = UInt(64.W)
  val vs = UInt(2.W)
  val tag = UInt(tagWidth.W)
}

class VdotResponse(tagWidth: Int) extends Bundle {
  val tag = UInt(tagWidth.W)
  val vd = UInt(5.W)
  val data = UInt(128.W)
  val illegal = Bool()
  val cause = UInt(4.W)
  // Response controls, not pulses: the adapter samples them on out.fire.
  // Architectural effects still require successful retirement.
  val writeEnable = Bool()
  val setVsDirty = Bool()
}

/** Standalone exact executor for vdot-s8x8-r32-v0.1.
  * One registered response, one-cycle unstalled latency, up to one accept/cycle.
  * flush wins over both handshakes and discards this module's pending request.
  * This module does not own architectural state or perform commit/rollback.
  */
class VdotExec(tagWidth: Int = 16) extends Module {
  require(tagWidth > 0, "vdot tag width must be positive")

  val io = IO(new Bundle {
    val in = Flipped(Decoupled(new VdotRequest(tagWidth)))
    val out = Decoupled(new VdotResponse(tagWidth))
    // Unmasked identity lets the adapter select cancellation by ROB age without
    // feeding flush-masked out.valid back into flush (a combinational loop).
    val pendingTag = Output(Valid(UInt(tagWidth.W)))
    val flush = Input(Bool())
  })

  val pending = RegInit(false.B)
  val response = Reg(new VdotResponse(tagWidth))

  // Each multiplication is signed 8x8 -> 16. A balanced +& tree grows to
  // 17/18/19 bits; [-130048, 131072] fits without truncating any intermediate.
  val products = (0 until 8).map { lane =>
    val low = lane * 8
    io.in.bits.src1(low + 7, low).asSInt * io.in.bits.src2(low + 7, low).asSInt
  }
  val pairs = products.grouped(2).map(p => p(0) +& p(1)).toSeq
  val quads = pairs.grouped(2).map(p => p(0) +& p(1)).toSeq
  val sum32 = (quads(0) +& quads(1)).pad(32).asUInt

  val encodingValid = (io.in.bits.instruction & "hfe00707f".U(32.W)) === "h0200000b".U(32.W)
  // Only vta/vma may be nonzero: also rejects vill and reserved vtype bits.
  val configValid = (io.in.bits.vtype & "hffffffffffffff3f".U(64.W)) === 0.U &&
    io.in.bits.vl === 8.U && io.in.bits.vstart === 0.U && io.in.bits.vs =/= 0.U
  val legal = encodingValid && configValid

  io.in.ready := !io.flush && (!pending || io.out.ready)
  io.out.valid := pending && !io.flush
  io.out.bits := response
  io.pendingTag.valid := pending
  io.pendingTag.bits := response.tag

  when(io.flush) {
    pending := false.B
  }.elsewhen(io.in.ready) {
    pending := io.in.valid
    when(io.in.valid) {
      response.tag := io.in.bits.tag
      response.vd := io.in.bits.instruction(11, 7)
      response.data := Mux(legal, Cat(0.U(96.W), sum32), 0.U(128.W))
      response.illegal := !legal
      response.cause := Mux(legal, 0.U, 2.U)
      response.writeEnable := legal
      response.setVsDirty := legal
    }
  }
}
