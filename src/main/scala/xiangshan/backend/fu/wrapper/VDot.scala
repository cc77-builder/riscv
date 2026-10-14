package xiangshan.backend.fu.wrapper

import chisel3._
import chisel3.util._
import org.chipsalliance.cde.config.Parameters
import xiangshan.{ExceptionNO, FuOpTypeWidth}
import xiangshan.backend.fu.{FuConfig, FuType}
import xiangshan.backend.fu.vector.{VDotProducts, VDotReduce, VecNonPipedFuncUnit}
import xiangshan.backend.fu.vector.Bundles.{VLmul, VSew}

object VDotOpType {
  // Internal FU operation, separate from the custom instruction encoding.
  def s8x8: UInt = 0.U(FuOpTypeWidth.W)
}

/** Single-outstanding vdot-s8x8-r32-v0.1 functional unit.
  * E0 accepts sources/control, E1 registers products, E2 registers the result,
  * and E3 is the earliest response handshake. Redirect kills precede response.
  */
class VDot(cfg: FuConfig)(implicit p: Parameters) extends VecNonPipedFuncUnit(cfg) {
  require(VLEN == 128, "VDot requires VLEN=128")
  require(cfg.fuType == FuType.vdot && !cfg.piped && cfg.latency.latencyVal.isEmpty)
  require(cfg.destDataBits == 128 && cfg.vconfigWakeUp && cfg.maskWakeUp)
  require(cfg.writeVecRf && cfg.writeV0Rf && cfg.exceptionOut == Seq(ExceptionNO.illegalInstr))
  require(!cfg.writeIntRf && !cfg.writeFpRf && !cfg.writeVlRf && !cfg.writeFakeIntRf)
  require(!cfg.writeFflags && !cfg.writeVxsat && !cfg.flushPipe && !cfg.replayInst)

  private val idle :: mul :: reduce :: respond :: Nil = Enum(4)
  private val state = RegInit(idle)
  private val src1Reg = Reg(UInt(128.W))
  private val src2Reg = Reg(UInt(128.W))
  private val productsReg = Reg(Vec(8, SInt(16.W)))
  private val resultReg = Reg(UInt(128.W))
  private val illegalReg = Reg(Bool())

  // VL comes from the renamed source. The 8-bit VL port does not carry vtype.
  private val illegalInput = vill || vsew =/= VSew.e8 || vlmul =/= VLmul.m1 ||
    !vm || vstart =/= 0.U || vl =/= 8.U || fuOpType =/= VDotOpType.s8x8
  // The base class registers this RobPtr only on in.fire, together with pdest.
  private val killed = state =/= idle && io.out.bits.ctrl.robIdx.needFlush(io.flush)

  io.in.ready := state === idle && !io.flush.valid && !reset.asBool
  io.out.valid := state === respond && !killed && !reset.asBool

  private val products = Module(new VDotProducts)
  private val sum = Module(new VDotReduce)
  products.io.vs1 := src1Reg
  products.io.vs2 := src2Reg
  sum.io.products := productsReg

  when(killed) {
    state := idle
  }.otherwise {
    switch(state) {
      is(idle) {
        when(io.in.fire) {
          src1Reg := vs1
          src2Reg := vs2
          illegalReg := illegalInput
          state := mul
        }
      }
      is(mul) {
        productsReg := products.io.products
        state := reduce
      }
      is(reduce) {
        resultReg := Mux(illegalReg, 0.U(128.W), sum.io.result)
        state := respond
      }
      is(respond) {
        when(io.out.fire) { state := idle }
      }
    }
  }

  io.out.bits.res.data := resultReg
  io.out.bits.ctrl.vecWen.get := outCtrl.vecWen.get && !illegalReg
  io.out.bits.ctrl.v0Wen.get := outCtrl.v0Wen.get && !illegalReg
  io.out.bits.ctrl.exceptionVec.get := 0.U.asTypeOf(io.out.bits.ctrl.exceptionVec.get)
  io.out.bits.ctrl.exceptionVec.get(ExceptionNO.illegalInstr) := illegalReg

  // A decoded request has exactly one destination class, including trap cases.
  when(io.in.fire) {
    assert(inCtrl.vecWen.get ^ inCtrl.v0Wen.get, "VDot requires one destination class")
  }
  when(io.out.valid) {
    assert(!io.in.ready)
    assert(io.out.bits.res.data(127, 32) === 0.U)
    when(illegalReg) {
      assert(!io.out.bits.ctrl.vecWen.get && !io.out.bits.ctrl.v0Wen.get)
    }
  }

  // A matching redirect may withdraw a stalled response; unrelated redirects may not.
  private val stalled = RegNext(io.out.valid && !io.out.ready, false.B)
  private val heldResponse = RegEnable(io.out.bits.asUInt, io.out.valid && !io.out.ready)
  when(stalled && !killed && !reset.asBool) {
    assert(io.out.valid, "VDot lost a stalled response")
    assert(io.out.bits.asUInt === heldResponse, "VDot changed a stalled response")
  }

  // Opt-in simulation observation only: no signal feeds back into the datapath.
  // Build in a fresh output directory with VDOT_T12_TRACE=1; archive that setting.
  if (sys.env.get("VDOT_T12_TRACE").contains("1")) {
    // Instantiate outside when: GTimer is a local register, not a global read.
    require(!p(xiangshan.DebugOptionsKey).ResetGen, "T12 trace requires the common simulation reset")
    val t12Cycle = utility.GTimer()
    when(io.in.fire) {
      printf(p"T12_ACCEPT cycle=${t12Cycle} rob=${inCtrl.robIdx.flag}:${inCtrl.robIdx.value} pdest=${inCtrl.pdest} vl=${vl} illegal=${illegalInput}\n")
    }
    when(killed && !reset.asBool) {
      printf(p"T12_KILL cycle=${t12Cycle} rob=${outCtrl.robIdx.flag}:${outCtrl.robIdx.value} redirect=${io.flush.bits.robIdx.flag}:${io.flush.bits.robIdx.value} state=${state}\n")
    }
    when(io.out.valid && !io.out.ready) {
      printf(p"T12_STALL cycle=${t12Cycle} rob=${outCtrl.robIdx.flag}:${outCtrl.robIdx.value}\n")
    }
    when(io.out.fire) {
      printf(p"T12_RESPONSE cycle=${t12Cycle} rob=${outCtrl.robIdx.flag}:${outCtrl.robIdx.value} pdest=${outCtrl.pdest} illegal=${illegalReg} data=0x${Hexadecimal(resultReg)}\n")
    }
  }

}
