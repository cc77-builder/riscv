package team.vdot

import chisel3._
import chisel3.util._
import _root_.circt.stage.ChiselStage
import org.chipsalliance.cde.config.Parameters
import top.MinimalConfig
import xiangshan._
import xiangshan.backend.fu.FuConfig
import xiangshan.backend.fu.wrapper.VDot

/** Flat stimulus adapter only: every handshake, kill and result comes from VDot. */
class VDotFuTestTop(experimentalFuseInputStage: Boolean = false)(implicit p: Parameters) extends XSModule {
  val io = IO(new Bundle {
    val in_valid = Input(Bool())
    val in_ready = Output(Bool())
    val out_valid = Output(Bool())
    val out_ready = Input(Bool())
    val vs1 = Input(UInt(128.W))
    val vs2 = Input(UInt(128.W))
    val old_vd = Input(UInt(128.W))
    val mask = Input(UInt(128.W))
    val vl = Input(UInt(8.W))
    val ctrl_vl = Input(UInt(8.W))
    val vsew = Input(UInt(2.W))
    val vlmul = Input(UInt(3.W))
    val vstart = Input(UInt(8.W))
    val vill = Input(Bool())
    val vm = Input(Bool())
    val vta = Input(Bool())
    val vma = Input(Bool())
    val vxrm = Input(UInt(2.W))
    val op = Input(UInt(FuOpTypeWidth.W))
    val rob_flag = Input(Bool())
    val rob_value = Input(UInt(log2Ceil(RobSize).W))
    val pdest = Input(UInt(PhyRegIdxWidth.W))
    val write_v0 = Input(Bool())
    val perf_tag = Input(UInt(64.W))
    val flush_valid = Input(Bool())
    val flush_flag = Input(Bool())
    val flush_value = Input(UInt(log2Ceil(RobSize).W))
    val flush_self = Input(Bool())
    val result = Output(UInt(128.W))
    val out_rob_flag = Output(Bool())
    val out_rob_value = Output(UInt(log2Ceil(RobSize).W))
    val out_pdest = Output(UInt(PhyRegIdxWidth.W))
    val out_vec_wen = Output(Bool())
    val out_v0_wen = Output(Bool())
    val out_exception = Output(UInt(ExceptionVec.ExceptionVecSize.W))
    val out_ctrl = Output(UInt(27.W))
    val out_perf_tag = Output(UInt(64.W))
    val out_rename_tag = Output(UInt(64.W))
  })
  require(RobSize == 48, "test scoreboard assumes MinimalConfig ROB=48")
  val dut = Module(new VDot(FuConfig.VDotCfg, experimentalFuseInputStage))
  dut.io.in.bits := 0.U.asTypeOf(dut.io.in.bits)
  dut.io.flush := 0.U.asTypeOf(dut.io.flush)
  dut.io.in.valid := io.in_valid
  io.in_ready := dut.io.in.ready
  dut.io.out.ready := io.out_ready
  io.out_valid := dut.io.out.valid
  dut.io.in.bits.data.src(0) := io.vs1
  dut.io.in.bits.data.src(1) := io.vs2
  dut.io.in.bits.data.src(2) := io.old_vd
  dut.io.in.bits.data.src(3) := io.mask
  dut.io.in.bits.data.src(4) := io.vl
  val ctrl = dut.io.in.bits.ctrl
  ctrl.robIdx.flag := io.rob_flag
  ctrl.robIdx.value := io.rob_value
  ctrl.pdest := io.pdest
  ctrl.vecWen.get := !io.write_v0
  ctrl.v0Wen.get := io.write_v0
  ctrl.fuOpType := io.op
  val vpu = ctrl.vpu.get
  vpu.vill := io.vill
  vpu.vm := io.vm
  vpu.vta := io.vta
  vpu.vma := io.vma
  vpu.vsew := io.vsew
  vpu.vlmul := io.vlmul
  vpu.vstart := io.vstart
  vpu.vl := io.ctrl_vl
  vpu.vxrm := io.vxrm
  dut.io.in.bits.perfDebugInfo.issueTime := io.perf_tag
  dut.io.in.bits.perfDebugInfo.renameTime := io.perf_tag ^ "hf0e1d2c3b4a59687".U
  dut.io.flush.valid := io.flush_valid
  dut.io.flush.bits.robIdx.flag := io.flush_flag
  dut.io.flush.bits.robIdx.value := io.flush_value
  dut.io.flush.bits.level := io.flush_self
  val out = dut.io.out.bits
  io.result := out.res.data
  io.out_rob_flag := out.ctrl.robIdx.flag
  io.out_rob_value := out.ctrl.robIdx.value
  io.out_pdest := out.ctrl.pdest
  io.out_vec_wen := out.ctrl.vecWen.get
  io.out_v0_wen := out.ctrl.v0Wen.get
  io.out_exception := out.ctrl.exceptionVec.get.asUInt
  val outVpu = out.ctrl.vpu.get
  io.out_ctrl := Cat(outVpu.vill, outVpu.vma, outVpu.vta, outVpu.vsew, outVpu.vlmul,
    outVpu.vm, outVpu.vstart, outVpu.vl, outVpu.vxrm)
  io.out_perf_tag := out.perfDebugInfo.issueTime
  io.out_rename_tag := out.perfDebugInfo.renameTime
}

object GenerateVDotFu {
  def main(args: Array[String]): Unit = {
    require(args.nonEmpty && args.drop(1).distinct.length == args.length - 1 &&
      args.drop(1).forall(Set("--invalid-vlen", "--fuse-input-stage").contains))
    val invalidVlen = args.drop(1).contains("--invalid-vlen")
    val fused = args.drop(1).contains("--fuse-input-stage")
    val base = new MinimalConfig(1)
    val core = base(XSTileKey).head
    implicit val p: Parameters = base.alterPartial {
      case XSCoreParamsKey => if (invalidVlen) core.copy(VLEN = 256) else core
    }
    ChiselStage.emitSystemVerilogFile(new VDotFuTestTop(fused),
      args = Array("--target-dir", args(0)),
      firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info"))
  }
}
