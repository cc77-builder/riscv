// Licensed under Mulan PSL v2; see LICENSE at the repository root.
package xiangshan.backend.decode

import chisel3._
import chisel3.util._
import chiseltest._
import chiseltest.simulator.VerilatorFlags
import org.chipsalliance.cde.config.Parameters
import org.scalatest.flatspec.AnyFlatSpec
import top.MinimalConfig
import utility.{LogUtilsOptions, LogUtilsOptionsKey, PerfCounterOptions, PerfCounterOptionsKey, XSPerfLevel}
import xiangshan.{ExceptionNO, SrcType, UopSplitType, XSCoreParamsKey, XSTileKey}
import xiangshan.backend.Bundles.DecodedInst
import xiangshan.backend.decode.isa.bitfield.XSInstBitFields
import xiangshan.backend.fu.{FuConfig, FuType}

/** The production DecodeStage owns splitting, vtype recovery and v0 routing.
  * Only frontend/RAT/CSR inputs unrelated to these tests are tied off.
  */
class VdotDecodeHarness(implicit p: Parameters) extends Module {
  val io = IO(new Bundle {
    val instruction = Input(UInt(32.W))
    val valid = Input(Bool())
    val ready = Input(Bool())
    val redirect = Input(Bool())
    val recover = Input(Bool())
    val vtype = Input(UInt(64.W))
    val vstart = Input(UInt(8.W))
    val vsOff = Input(Bool())
    val accepted = Output(Bool())
    val recognized = Output(Bool())
    val out = Vec(p(XSCoreParamsKey).RenameWidth, Valid(new DecodedInst))
  })
  val dut = Module(new DecodeStage)
  dut.io.in.foreach { in =>
    in.valid := false.B
    in.bits := 0.U.asTypeOf(in.bits)
  }
  dut.io.in(0).valid := io.valid
  dut.io.in(0).bits.instr := io.instruction
  dut.io.out.foreach(_.ready := io.ready)
  dut.io.redirect := io.redirect
  dut.io.csrCtrl := 0.U.asTypeOf(dut.io.csrCtrl)
  dut.io.fromCSR := 0.U.asTypeOf(dut.io.fromCSR)
  dut.io.fromCSR.illegalInst.vsIsOff := io.vsOff
  dut.io.fusion.foreach(_ := false.B)
  dut.io.fromRob := 0.U.asTypeOf(dut.io.fromRob)
  dut.io.fromRob.walkVType.valid := io.recover
  val vt = dut.io.fromRob.walkVType.bits
  vt.illegal := io.vtype(63)
  vt.vma := io.vtype(7)
  vt.vta := io.vtype(6)
  vt.vsew := io.vtype(4, 3)
  vt.vlmul := io.vtype(2, 0)
  dut.io.vsetvlVType := 0.U.asTypeOf(dut.io.vsetvlVType)
  dut.io.vstart := io.vstart
  dut.io.intRat.foreach(_.foreach(_.data := 0.U))
  dut.io.fpRat.foreach(_.foreach(_.data := 0.U))
  dut.io.vecRat.foreach(_.foreach(_.data := 0.U))
  dut.io.v0Rat.foreach(_.data := 0.U)
  dut.io.vlRat.foreach(_.data := 0.U)
  dut.io.stallReason.in.reason.foreach(_ := 0.U)
  dut.io.stallReason.out.backReason := 0.U.asTypeOf(dut.io.stallReason.out.backReason)
  io.accepted := dut.io.in(0).fire
  io.recognized := io.instruction.asTypeOf(new XSInstBitFields).isVdot
  io.out.zip(dut.io.out).foreach { case (out, in) =>
    out.valid := in.valid
    out.bits := in.bits
  }
  // Keep production local XSError assertions enabled. No global log endpoint:
  // chiseltest6's bridge cannot convert the endpoint's Chisel6 Probe ports.
}

class VdotDecodeSpec extends AnyFlatSpec with ChiselScalatestTester {
  private val base = new MinimalConfig
  private implicit val p: Parameters = base.alterPartial {
    case XSCoreParamsKey => base(XSTileKey).head
    case LogUtilsOptionsKey => LogUtilsOptions(enableDebug = false, enablePerf = false, fpgaPlatform = false)
    case PerfCounterOptionsKey => PerfCounterOptions(false, false, XSPerfLevel.NORMAL, 0)
  }
  private def word(vd: Int, a: Int, b: Int): BigInt = BigInt(0x0200000bL | vd.toLong << 7 | a.toLong << 15 | b.toLong << 20)

  behavior of "VDOT production decode"

  it should "recognize only the frozen candidate bits without overlapping existing entries" in {
    assert(FuConfig.VdotCfg.isVecArith && FuConfig.VdotCfg.needOg2,
      "VDOT must itself be a vector arithmetic FU, independent of neighboring EXU owners")
    assert(FuConfig.VdotCfg.exceptionOut.contains(ExceptionNO.illegalInstr))
    val pattern = VdotInstructions.VDOT
    assert(pattern.mask == BigInt("fe00707f", 16) && pattern.value == BigInt("0200000b", 16))
    for (vd <- 0 until 32; a <- 0 until 32; b <- 0 until 32) {
      assert((word(vd, a, b) & pattern.mask) == pattern.value)
    }
    val existing = XDecode.table ++ FpDecode.table ++ BitmanipDecode.table ++ ScalarCryptoDecode.table ++
      XSTrapDecode.table ++ CBODecode.table ++ SvinvalDecode.table ++ HypervisorDecode.table ++
      VecDecoder.table ++ ZicondDecode.table ++ ZimopDecode.table ++ ZfaDecode.table
    assert(existing.forall { case (other, _) =>
      ((other.value ^ pattern.value) & other.mask & pattern.mask) != 0
    }, "VDOT overlaps a pre-existing decode entry")
    val owners = p(XSCoreParamsKey).vfSchdParams.issueBlockParams.flatMap(_.exuBlockParams)
      .filter(_.fuConfigs.contains(FuConfig.VdotCfg))
    assert(owners.size == 1 && owners.head.name == "VFEX1")
    assert(owners.head.latencyCertain && owners.head.fuLatencyMap(FuType.vdot) == 2)
    assert(owners.head.wakeUpFuLatencyMap(FuType.vdot) == 1)
    assert(owners.head.vfFuLatencyMap(FuType.vdot) == 2 && owners.head.v0FuLatencyMap(FuType.vdot) == 2)
    println("VDOT_DECODE_TABLE_PASS register_encodings=32768 overlap=0 owners=1")
  }

  it should "emit one uop with exact sources and recovered snapshots including stalls and redirects" in {
    // chiseltest6 injects a forced top-header include that prevents GCC PCH
    // reuse in Verilator5.020's split build. A single translation unit avoids
    // that toolchain mismatch; production RTL and assertions are unchanged.
    test(new VdotDecodeHarness).withAnnotations(Seq(VerilatorBackendAnnotation,
      VerilatorFlags(Seq("--output-split", "0")))) { dut =>
      dut.io.valid.poke(false.B); dut.io.ready.poke(true.B); dut.io.redirect.poke(false.B)
      dut.io.recover.poke(false.B); dut.io.vtype.poke(0.U); dut.io.vstart.poke(0.U)
      dut.io.vsOff.poke(false.B); dut.io.instruction.poke(0.U)
      dut.reset.poke(true.B); dut.clock.step(2); dut.reset.poke(false.B)
      var requests = 0
      def issue(vd: Int, a: Int, b: Int, vt: BigInt, start: Int = 0, off: Boolean = false, stall: Boolean = false): Unit = {
        dut.io.vtype.poke(vt.U); dut.io.recover.poke(true.B); dut.clock.step()
        dut.io.recover.poke(false.B); dut.io.vstart.poke(start.U); dut.io.vsOff.poke(off.B)
        dut.io.instruction.poke(word(vd, a, b).U); dut.io.valid.poke(true.B)
        dut.io.recognized.expect(true.B)
        var waited = 0
        while (!dut.io.accepted.peek().litToBoolean && waited < 10) { dut.clock.step(); waited += 1 }
        assert(waited < 10, "DecodeStage did not accept VDOT")
        dut.clock.step(); dut.io.valid.poke(false.B)
        waited = 0
        while (!dut.io.out.head.valid.peek().litToBoolean && waited < 10) { dut.clock.step(); waited += 1 }
        assert(waited < 10, "DecodeStage lost VDOT")
        def check(): Unit = {
          // Production complexNum is capped by readyCounter, so valid is
          // gated off under rename stall; the buffered payload must survive.
          dut.io.out.head.valid.expect(true.B)
          dut.io.out.tail.foreach(_.valid.expect(false.B))
          val out = dut.io.out.head.bits
          out.fuType.expect(FuType.vdot.U); out.fuOpType.expect(0.U)
          out.numUops.expect(1.U); out.numWB.expect(1.U)
          out.firstUop.expect(true.B); out.lastUop.expect(true.B); out.uopIdx.expect(0.U)
          out.uopSplitType.expect(UopSplitType.dummy)
          out.lsrc(0).expect(a.U); out.lsrc(1).expect(b.U); out.ldest.expect(vd.U)
          out.srcType(0).expect(SrcType.vp); out.srcType(1).expect(SrcType.vp)
          out.srcType(2).expect(SrcType.no)
          out.srcType(3).expect(if (a == 0 || b == 0) SrcType.v0 else SrcType.no)
          out.srcType(4).expect(SrcType.vp)
          out.v0Wen.expect((vd == 0).B); out.vecWen.expect((vd != 0).B)
          out.rfWen.expect(false.B); out.fpWen.expect(false.B); out.vlWen.expect(false.B)
          out.vpu.isDependOldVd.expect(false.B); out.vpu.isWritePartVd.expect(false.B)
          out.vpu.vill.expect(vt.testBit(63).B); out.vpu.vsew.expect(((vt >> 3) & 3).U)
          out.vpu.vlmul.expect((vt & 7).U); out.vpu.vta.expect(vt.testBit(6).B)
          out.vpu.vma.expect(vt.testBit(7).B); out.vpu.vstart.expect(start.U)
          if (off || vt.testBit(63) || start != 0) out.exceptionVec(ExceptionNO.illegalInstr).expect(true.B)
        }
        check()
        if (stall) {
          dut.io.ready.poke(false.B)
          dut.io.instruction.poke(word(2, 3, 4).U)
          dut.io.vstart.poke(7.U); dut.io.vsOff.poke(true.B)
          for (_ <- 0 until 3) { dut.clock.step(); dut.io.out.foreach(_.valid.expect(false.B)) }
          dut.io.ready.poke(true.B)
          check()
        }
        dut.clock.step(); dut.io.out.foreach(_.valid.expect(false.B)); requests += 1
      }
      for (vd <- Seq(0, 1, 31); a <- Seq(0, 1, 31); b <- Seq(0, 1, 31)) issue(vd, a, b, 0, stall = true)
      for (sew <- 0 until 4; lmul <- 0 until 8; policy <- 0 until 4) issue(31, 31, 31, (policy << 6) | (sew << 3) | lmul)
      issue(0, 0, 0, BigInt(1) << 63); issue(1, 0, 31, 0, off = true)
      for (start <- Seq(1, 7, 8, 127)) issue(0, 0, 31, 0, start = start)
      for (bit <- 0 until 32 if ((BigInt("fe00707f", 16) >> bit) & 1) == 1) {
        dut.io.instruction.poke((word(31, 31, 31) ^ (BigInt(1) << bit)).U)
        dut.io.recognized.expect(false.B)
      }
      // A redirect drops an already buffered custom instruction under stall.
      dut.io.instruction.poke(word(0, 0, 31).U); dut.io.vstart.poke(0.U)
      dut.io.vsOff.poke(false.B); dut.io.valid.poke(true.B)
      dut.io.accepted.expect(true.B); dut.clock.step(); dut.io.valid.poke(false.B)
      dut.io.out.head.valid.expect(true.B); dut.io.ready.poke(false.B)
      dut.clock.step(2); dut.io.out.head.valid.expect(false.B)
      dut.io.redirect.poke(true.B); dut.clock.step(); dut.io.redirect.poke(false.B)
      dut.io.ready.poke(true.B); dut.io.out.foreach(_.valid.expect(false.B))
      dut.clock.step(3); dut.io.out.foreach(_.valid.expect(false.B))
      println(s"VDOT_DECODE_STAGE_PASS requests=$requests aliases=27 configs=128 stalled=27")
    }
  }
}
