package team.vdot

import chisel3._
import chisel3.util._
import _root_.circt.stage.ChiselStage
import org.chipsalliance.cde.config.Parameters
import top.MinimalConfig
import xiangshan._
import xiangshan.backend.decode.{DecodeUnit, DecodeUnitComp}
import xiangshan.backend.decode.isa.bitfield.XSInstBitFields
import xiangshan.backend.fu.FuType

/** Exercises the production simple and complex decoders. No copied decoder.
  * This does not include Rename/RF/EXU/ROB or certify full-core integration.
  */
class VDotDecodeTestTop(implicit p: Parameters) extends XSModule {
  val io = IO(new Bundle {
    val word = Input(UInt(32.W))
    val valid = Input(Bool())
    val ready = Output(Bool())
    val out_ready = Input(Bool())
    val redirect = Input(Bool())
    val vsew = Input(UInt(2.W))
    val vlmul = Input(UInt(3.W))
    val vill = Input(Bool())
    val vta = Input(Bool())
    val vma = Input(Bool())
    val vstart = Input(UInt(8.W))
    val vs_off = Input(Bool())
    val classified = Output(Bool())
    val simple_vdot = Output(Bool())
    val complex = Output(Bool())
    val num_uops = Output(UInt(7.W))
    val num_wb = Output(UInt(7.W))
    val out_valid = Output(Bool())
    val extra_valid = Output(Bool())
    val src0 = Output(UInt(6.W))
    val src1 = Output(UInt(6.W))
    val dest = Output(UInt(6.W))
    val types = Output(UInt(20.W))
    val exception = Output(Bool())
    val vec_wen = Output(Bool())
    val other_wen = Output(Bool())
    val partial = Output(Bool())
    val old_dep = Output(Bool())
    val flush = Output(Bool())
    val block_back = Output(Bool())
    val first = Output(Bool())
    val last = Output(Bool())
    val uop_idx = Output(UInt(7.W))
    val snapshot = Output(UInt(16.W))
  })
  val simple = Module(new DecodeUnit)
  simple.io.enq.ctrlFlow := 0.U.asTypeOf(simple.io.enq.ctrlFlow)
  simple.io.enq.ctrlFlow.instr := io.word
  simple.io.enq.vtype := 0.U.asTypeOf(simple.io.enq.vtype)
  simple.io.enq.vtype.vsew := io.vsew
  simple.io.enq.vtype.vlmul := io.vlmul
  simple.io.enq.vtype.illegal := io.vill
  simple.io.enq.vtype.vta := io.vta
  simple.io.enq.vtype.vma := io.vma
  simple.io.enq.vstart := io.vstart
  simple.io.csrCtrl := 0.U.asTypeOf(simple.io.csrCtrl)
  simple.io.fromCSR := 0.U.asTypeOf(simple.io.fromCSR)
  simple.io.fromCSR.illegalInst.vsIsOff := io.vs_off

  val complex = Module(new DecodeUnitComp)
  complex.io.in.valid := io.valid
  complex.io.in.bits.simpleDecodedInst := simple.io.deq.decodedInst
  complex.io.in.bits.uopInfo := simple.io.deq.uopInfo
  complex.io.redirect := io.redirect
  complex.io.csrCtrl := 0.U.asTypeOf(complex.io.csrCtrl)
  complex.io.vtypeBypass := simple.io.enq.vtype
  complex.io.out.complexDecodedInsts.foreach(_.ready := io.out_ready)
  io.ready := complex.io.in.ready
  io.classified := io.word.asTypeOf(new XSInstBitFields).isVDot
  io.simple_vdot := FuType.FuTypeOrR(simple.io.deq.decodedInst.fuType, FuType.vdot)
  io.complex := simple.io.deq.isComplex
  io.num_uops := simple.io.deq.uopInfo.numOfUop
  io.num_wb := simple.io.deq.uopInfo.numOfWB
  io.out_valid := complex.io.out.complexDecodedInsts.head.valid
  io.extra_valid := complex.io.out.complexDecodedInsts.tail.map(_.valid).reduce(_ || _)
  val out = complex.io.out.complexDecodedInsts.head.bits
  io.src0 := out.lsrc(0)
  io.src1 := out.lsrc(1)
  io.dest := out.ldest
  io.types := Cat(out.srcType.reverse)
  io.exception := out.exceptionVec(ExceptionNO.illegalInstr)
  io.vec_wen := out.vecWen
  io.other_wen := out.rfWen || out.fpWen || out.v0Wen || out.vlWen || out.wfflags
  io.partial := out.vpu.isWritePartVd
  io.old_dep := out.vpu.isDependOldVd
  io.flush := out.flushPipe
  io.block_back := out.blockBackward
  io.first := out.firstUop
  io.last := out.lastUop
  io.uop_idx := out.uopIdx
  io.snapshot := Cat(out.vpu.vill, out.vpu.vma, out.vpu.vta,
    out.vpu.vsew, out.vpu.vlmul, out.vpu.vstart)
}

object GenerateVDotDecode {
  def main(args: Array[String]): Unit = {
    require(args.length == 1)
    val base = new MinimalConfig(1)
    implicit val p: Parameters = base.alterPartial {
      case XSCoreParamsKey => base(XSTileKey).head
      case utility.LogUtilsOptionsKey => utility.LogUtilsOptions(
        enableDebug = false, enablePerf = false, fpgaPlatform = false)
    }
    ChiselStage.emitSystemVerilogFile(new VDotDecodeTestTop,
      args = Array("--target-dir", args(0)),
      firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info"))
  }
}
