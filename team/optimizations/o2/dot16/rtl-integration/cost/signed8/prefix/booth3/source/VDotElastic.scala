package xiangshan.backend.fu.wrapper

import chisel3._
import chisel3.util._
import org.chipsalliance.cde.config.Parameters
import xiangshan.ExceptionNO
import xiangshan.backend.fu.{FuConfig, FuType, FuncUnit, FuncUnitCtrlOutput}
import xiangshan.backend.fu.vector.{VDotCarrySaveRows, VDotPrefixFinish, VecFuncUnitAlias}
import xiangshan.backend.fu.vector.Bundles.{VLmul, VSew}

/** Functional occupancy, before this edge's kill/response/accept transitions.
  * The parent uses real slot state for dispatch exclusion and clock gating.
  */
class VDotElasticStatus extends Bundle {
  val pValid = Bool()
  val rValid = Bool()
  val occupancy = UInt(2.W)
}

/** Two elastic slots: E0 captures carry-save rows/control, E1 transfers the reduced
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

  // Elaboration-only: disabled builds retain exactly eight signed-byte terms.
  private val dot16Enabled = VDot16Feature.enabled
  private val storedResultBits = if (dot16Enabled) 20 else 19

  private val pValid = RegInit(false.B)
  private val rValid = RegInit(false.B)
  private val pRows = Reg(Vec(if (dot16Enabled) 2 else 1, Vec(3, UInt(storedResultBits.W))))
  private val pCtrl = Reg(chiselTypeOf(io.out.bits.ctrl))
  private val pPerf = Reg(chiselTypeOf(io.out.bits.perfDebugInfo))
  // Store the exact signed sum; extend to the architectural word at the output.
  // Keep each slot's complete control/perf identity on the same transfer edge.
  private val rPacket = Reg(new Bundle {
    val ctrl = chiselTypeOf(io.out.bits.ctrl)
    val res = new Bundle {
      val data = UInt(storedResultBits.W)
    }
    val perfDebugInfo = chiselTypeOf(io.out.bits.perfDebugInfo)
  })

  pipelineStatus.pValid := pValid
  pipelineStatus.rValid := rValid
  pipelineStatus.occupancy := pValid.asUInt +& rValid.asUInt

  private val isDot16 = if (dot16Enabled) fuOpType === VDotOpType.s8x16 else false.B
  private val illegalInput = if (dot16Enabled) {
    vill || vsew =/= VSew.e8 || vlmul =/= VLmul.m1 || !vm || vstart =/= 0.U ||
      Mux(isDot16, vl =/= 16.U, vl =/= 8.U) ||
      (fuOpType =/= VDotOpType.s8x8 && fuOpType =/= VDotOpType.s8x16)
  } else {
    vill || vsew =/= VSew.e8 || vlmul =/= VLmul.m1 ||
      !vm || vstart =/= 0.U || vl =/= 8.U || fuOpType =/= VDotOpType.s8x8
  }
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
  private val outputWord = Wire(SInt(32.W))
  outputWord := rPacket.res.data.asSInt
  io.out.bits.res.data := Cat(0.U(96.W), outputWord.asUInt)

  private val products = Module(new VDotCarrySaveRows)
  private val highProducts = if (dot16Enabled) Some(Module(new VDotCarrySaveRows)) else None
  products.io.vs1 := inData.src(0)(63, 0)
  products.io.vs2 := inData.src(1)(63, 0)
  if (dot16Enabled) {
    highProducts.get.io.vs1 := inData.src(0)(127, 64)
    highProducts.get.io.vs2 := inData.src(1)(127, 64)
  }
  // Each unsigned 20-bit half encodes signed dot8 + 2^19 modulo 2^20.
  // Feature0 stores only low19, so that bias vanishes. Feature1 stores both
  // full halves; their biases add to 2^20 and vanish in the exact R finish.
  // A disabled high half is biased zero, saved with the accepted request.
  private val rowWords = for {
    half <- 0 until (if (dot16Enabled) 2 else 1)
    row <- 0 until 3
  } yield pRows(half)(row)
  require(rowWords.forall(_.getWidth == storedResultBits), "unsigned rows share the exact sum width")
  // Fixed-width additions are associative modulo 2^19/2^20. The true final
  // eight/sixteen-term result fits that signed width, so reconstruction is exact.
  private val prefixSum = Module(new VDotPrefixFinish(storedResultBits, if (dot16Enabled) 6 else 3))
  for ((word, index) <- rowWords.zipWithIndex) prefixSum.io.rows(index) := word.asUInt
  private val compressedSum = prefixSum.io.result.asSInt
  require(compressedSum.getWidth == storedResultBits, "exact fixed-width carry-save finish")

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
    pRows(0)(0) := products.io.row0(storedResultBits - 1, 0)
    pRows(0)(1) := products.io.row1(storedResultBits - 1, 0)
    pRows(0)(2) := products.io.row2(storedResultBits - 1, 0)
    if (dot16Enabled) {
      // Both modes save a half with the same +2^19 bias. Dot8 masks all high
      // operand bits by saving biased zero, without a post-P mode or correction.
      pRows(1)(0) := Mux(isDot16, highProducts.get.io.row0, (BigInt(1) << 19).U(20.W))
      pRows(1)(1) := Mux(isDot16, highProducts.get.io.row1, 0.U(20.W))
      pRows(1)(2) := Mux(isDot16, highProducts.get.io.row2, 0.U(20.W))
    }
    pCtrl := acceptedCtrl
    pPerf := io.in.bits.perfDebugInfo
  }
  when(move) {
    // Reads pre-edge P even when a new request replaces it at this same edge.
    rPacket.ctrl := pCtrl
    rPacket.perfDebugInfo := pPerf
    rPacket.res.data := Mux(pCtrl.exceptionVec.get(ExceptionNO.illegalInstr),
      0.U(storedResultBits.W),
      compressedSum.asUInt)
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
