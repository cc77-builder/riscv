package xiangshan.backend.fu.wrapper

import chisel3._
import chisel3.util._
import org.chipsalliance.cde.config.Parameters
import xiangshan.ExceptionNO
import xiangshan.backend.fu.{FuConfig, FuType, FuncUnit, FuncUnitCtrlOutput}
import xiangshan.backend.fu.vector.{VDotProducts, VDotReduce, VecFuncUnitAlias}
import xiangshan.backend.fu.vector.Bundles.{VLmul, VSew}

/** Functional occupancy, before this edge's kill/response/accept transitions.
  * The parent uses real slot state for dispatch exclusion and clock gating.
  */
class VDotElasticStatus extends Bundle {
  val pValid = Bool()
  val rValid = Bool()
  val occupancy = UInt(2.W)
}

/** Two elastic slots: E0 captures products/control, E1 transfers the reduced
  * result/control, and E2 is the first possible response. In the absence of
  * stalls/redirects, old R response, old P transfer and new acceptance overlap.
  * The surrounding EXU owns exclusion against DIV; no single-request base
  * class or bypassed control can supply identities for these two requests.
  */
class VDotElastic(cfg: FuConfig)(implicit p: Parameters) extends FuncUnit(cfg)
  with VecFuncUnitAlias {
  require(VDotO2.enabled, "VDotElastic requires VDOT_O2_ELASTIC=1")
  require(VLEN == 128, "VDotElastic requires VLEN=128")
  require(cfg.fuType == FuType.vdot && !cfg.piped && cfg.latency.latencyVal.isEmpty)
  require(cfg.destDataBits == 128 && cfg.vconfigWakeUp && cfg.maskWakeUp)
  require(cfg.writeVecRf && cfg.writeV0Rf && cfg.exceptionOut == Seq(ExceptionNO.illegalInstr))
  require(!cfg.writeIntRf && !cfg.writeFpRf && !cfg.writeVlRf && !cfg.writeFakeIntRf)
  require(!cfg.writeFflags && !cfg.writeVxsat && !cfg.flushPipe && !cfg.replayInst)

  val pipelineStatus = IO(Output(new VDotElasticStatus))

  private val pValid = RegInit(false.B)
  private val rValid = RegInit(false.B)
  private val pProducts = Reg(Vec(8, SInt(16.W)))
  private val pCtrl = Reg(chiselTypeOf(io.out.bits.ctrl))
  private val pPerf = Reg(chiselTypeOf(io.out.bits.perfDebugInfo))
  // H1 stores only the architectural low word; the public result stays 128 bits.
  // Keep each slot's complete control/perf identity on the same transfer edge.
  private val rPacket = Reg(new Bundle {
    val ctrl = chiselTypeOf(io.out.bits.ctrl)
    val res = new Bundle {
      val data = UInt(32.W)
    }
    val perfDebugInfo = chiselTypeOf(io.out.bits.perfDebugInfo)
  })

  pipelineStatus.pValid := pValid
  pipelineStatus.rValid := rValid
  pipelineStatus.occupancy := pValid.asUInt +& rValid.asUInt

  private val illegalInput = vill || vsew =/= VSew.e8 || vlmul =/= VLmul.m1 ||
    !vm || vstart =/= 0.U || vl =/= 8.U || fuOpType =/= VDotOpType.s8x8
  private val killP = pValid && pCtrl.robIdx.needFlush(io.flush)
  private val killR = rValid && rPacket.ctrl.robIdx.needFlush(io.flush)
  private val liveP = pValid && !killP && !reset.asBool
  private val liveR = rValid && !killR && !reset.asBool
  private val rReady = !liveR || io.out.ready
  private val move = liveP && rReady
  private val pReady = !liveP || rReady

  // Parent admission is enforced by its atomic child dispatch. The FU also
  // suppresses every new accept on redirect/reset, including unrelated flush.
  io.in.ready := pReady && !io.flush.valid && !reset.asBool
  io.out.valid := liveR
  io.out.bits.ctrl := rPacket.ctrl
  io.out.bits.perfDebugInfo := rPacket.perfDebugInfo
  io.out.bits.res := 0.U.asTypeOf(io.out.bits.res)
  io.out.bits.res.data := Cat(0.U(96.W), rPacket.res.data)

  private val products = Module(new VDotProducts)
  private val reduce = Module(new VDotReduce)
  products.io.vs1 := inData.src(0)
  products.io.vs2 := inData.src(1)
  reduce.io.products := pProducts

  // One output-shaped control packet per slot. Every output control field is
  // initialized, then the complete supported identity is captured on acceptance.
  // vpu/perf are whole bundles; newly arriving inputs never bypass saved state.
  private val acceptedCtrl = Wire(new FuncUnitCtrlOutput(cfg))
  acceptedCtrl := 0.U.asTypeOf(acceptedCtrl)
  acceptedCtrl.robIdx := inCtrl.robIdx
  acceptedCtrl.pdest := inCtrl.pdest
  acceptedCtrl.vecWen.get := inCtrl.vecWen.get && !illegalInput
  acceptedCtrl.v0Wen.get := inCtrl.v0Wen.get && !illegalInput
  acceptedCtrl.vpu.get := inCtrl.vpu.get
  acceptedCtrl.exceptionVec.get(ExceptionNO.illegalInstr) := illegalInput

  pValid := (liveP && !move) || io.in.fire
  rValid := (liveR && !io.out.fire) || move

  when(io.in.fire) {
    pProducts := products.io.products
    pCtrl := acceptedCtrl
    pPerf := io.in.bits.perfDebugInfo
  }
  when(move) {
    // Reads pre-edge P even when a new request replaces it at this same edge.
    rPacket.ctrl := pCtrl
    rPacket.perfDebugInfo := pPerf
    rPacket.res.data := Mux(pCtrl.exceptionVec.get(ExceptionNO.illegalInstr),
      0.U(32.W), reduce.io.result(31, 0))
  }

  // Read-only handles for the separate G1/G2 observation harness. These carry
  // no debug sequence state and never feed back into functional decisions.
  private[backend] def o2ObservedPPerf: xiangshan.PerfDebugInfo = pPerf
  private[backend] def o2ObservedPCtrl: FuncUnitCtrlOutput = pCtrl
  private[backend] def o2ObservedRCtrl: FuncUnitCtrlOutput = rPacket.ctrl
  private[backend] def o2ObservedPValid: Bool = pValid
  private[backend] def o2ObservedRValid: Bool = rValid
  // Build derived observations in the child's elaboration context. A parent
  // tap must only read a pre-existing node, never construct child logic there.
  private val observedKillP = killP && !reset.asBool
  private val observedKillR = killR && !reset.asBool
  private[backend] def o2ObservedKillP: Bool = observedKillP
  private[backend] def o2ObservedKillR: Bool = observedKillR
  private[backend] def o2ObservedMove: Bool = move
  private[backend] def o2ObservedIllegalInput: Bool = illegalInput
  private[backend] def o2ObservedVl: UInt = vl

  when(io.in.fire) {
    assert(inCtrl.vecWen.get ^ inCtrl.v0Wen.get,
      "VDotElastic requires one destination class")
  }
  when(io.out.valid) {
    assert(io.out.bits.res.data(127, 32) === 0.U)
    when(io.out.bits.ctrl.exceptionVec.get(ExceptionNO.illegalInstr)) {
      assert(!io.out.bits.ctrl.vecWen.get && !io.out.bits.ctrl.v0Wen.get)
    }
  }
  when(reset.asBool) {
    assert(!io.in.fire && !io.out.fire)
  }

  // Only a matching kill or reset may withdraw a blocked old R response.
  private val stalled = RegNext(io.out.valid && !io.out.ready, false.B)
  private val heldResponse = RegEnable(io.out.bits.asUInt, io.out.valid && !io.out.ready)
  when(stalled && !killR && !reset.asBool) {
    assert(io.out.valid, "VDotElastic lost a stalled response")
    assert(io.out.bits.asUInt === heldResponse, "VDotElastic changed a stalled response")
  }
}
