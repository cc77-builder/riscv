package team.vdot

import chisel3._
import chisel3.util._
import chisel3.util.experimental.BoringUtils
import _root_.circt.stage.ChiselStage
import freechips.rocketchip.diplomacy.LazyModule
import org.chipsalliance.cde.config.Parameters
import top.MinimalConfig
import utility.ClockGate
import xiangshan._
import xiangshan.backend.exu.ExeUnit
import xiangshan.backend.fu.FuType

/** Stimulus/observation only. Busy, dispatch, output mux and clocks are production RTL. */
class VDotExuTestTop(implicit p: Parameters) extends XSModule {
  require(RobSize == 48 && EnableClockGate)
  // The same parameter bindings performed by Backend, without instantiating the CPU.
  backendParams.allSchdParams.foreach(_.bindBackendParam(backendParams))
  backendParams.allIssueParams.foreach(_.bindBackendParam(backendParams))
  backendParams.allExuParams.zipWithIndex.foreach { case (cfg, i) =>
    cfg.bindBackendParam(backendParams)
    cfg.updateIQWakeUpConfigs(backendParams.iqWakeUpParams)
    cfg.updateExuIdx(i)
  }
  val cfg = backendParams.getExuParamByName("VFEX4")
  require(cfg.fuConfigs.map(_.fuType).toSet == Set(FuType.vdot, FuType.vidiv, FuType.vfdiv))
  val io = IO(new Bundle {
    val in_valid = Input(Bool())
    val in_ready = Output(Bool())
    val out_valid = Output(Bool())
    val out_ready = Input(Bool())
    val kind = Input(UInt(2.W)) // 0 vdot, 1 vidiv, 2 vfdiv
    val op = Input(UInt(FuOpTypeWidth.W))
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
    val vec_result = Output(UInt(128.W))
    val v0_result = Output(UInt(128.W))
    val out_rob_flag = Output(Bool())
    val out_rob_value = Output(UInt(log2Ceil(RobSize).W))
    val out_pdest = Output(UInt(PhyRegIdxWidth.W))
    val out_vec_wen = Output(Bool())
    val out_v0_wen = Output(Bool())
    val out_exception = Output(UInt(ExceptionVec.ExceptionVecSize.W))
    val out_fflags = Output(UInt(5.W))
    val out_perf_tag = Output(UInt(64.W))
    val out_rename_tag = Output(UInt(64.W))
    val busy = Output(Bool())
    val fu_clocks = Output(UInt(3.W))
    val fu_accept = Output(UInt(3.W))
    val fu_valid = Output(UInt(3.W))
  })
  // Top.childReset comes from ResetGen as AsyncReset, including simulation mode.
  // A synchronous reset behind a closed clock gate would not reset idle dividers.
  val dut = withReset(reset.asAsyncReset) { Module(LazyModule(new ExeUnit(cfg)).module) }
  dut.io.in.bits := 0.U.asTypeOf(dut.io.in.bits)
  dut.io.flush := 0.U.asTypeOf(dut.io.flush)
  dut.io.in.valid := io.in_valid
  io.in_ready := dut.io.in.ready
  dut.io.out.ready := io.out_ready
  io.out_valid := dut.io.out.valid
  val in = dut.io.in.bits
  in.fuType := MuxLookup(io.kind, FuType.vdot.U)(Seq(1.U -> FuType.vidiv.U, 2.U -> FuType.vfdiv.U))
  in.fuOpType := io.op
  in.src.zip(Seq(io.vs1, io.vs2, io.old_vd, io.mask, io.vl)).foreach { case (a,b) => a := b }
  in.copySrc.foreach(_.foreach(_.zip(Seq(io.vs1, io.vs2)).foreach { case (a,b) => a := b }))
  in.robIdx.flag := io.rob_flag
  in.robIdx.value := io.rob_value
  in.pdest := io.pdest
  in.vecWen.get := !io.write_v0
  in.v0Wen.get := io.write_v0
  val vpu = in.vpu.get
  vpu.vill := io.vill
  vpu.vm := io.vm
  vpu.vta := io.vta
  vpu.vma := io.vma
  vpu.vsew := io.vsew
  vpu.vlmul := io.vlmul
  vpu.vstart := io.vstart
  vpu.vl := io.ctrl_vl
  vpu.vxrm := io.vxrm
  in.perfDebugInfo.issueTime := io.perf_tag
  in.perfDebugInfo.renameTime := io.perf_tag ^ "hf0e1d2c3b4a59687".U
  dut.io.frm.foreach(_ := 0.U)
  dut.io.vxrm.foreach(_ := io.vxrm)
  dut.io.flush.valid := io.flush_valid
  dut.io.flush.bits.robIdx.flag := io.flush_flag
  dut.io.flush.bits.robIdx.value := io.flush_value
  dut.io.flush.bits.level := io.flush_self
  val out = dut.io.out.bits
  io.result := out.data(0)
  io.vec_result := out.data(cfg.wbVecIndex)
  io.v0_result := out.data(cfg.wbV0Index)
  io.out_rob_flag := out.robIdx.flag
  io.out_rob_value := out.robIdx.value
  io.out_pdest := out.pdest
  io.out_vec_wen := out.vecWen.get
  io.out_v0_wen := out.v0Wen.get
  io.out_exception := out.exceptionVec.get.asUInt
  io.out_fflags := out.fflags.get.asUInt
  io.out_perf_tag := out.debugInfo.issueTime
  io.out_rename_tag := out.debugInfo.renameTime
  io.busy := BoringUtils.bore(dut.busy)
  val observed = Seq(FuType.vdot, FuType.vidiv, FuType.vfdiv).map { t =>
    dut.funcUnits(cfg.fuConfigs.indexWhere(_.fuType == t))
  }
  io.fu_clocks := VecInit(observed.map(f => BoringUtils.bore(f.clock).asBool)).asUInt
  io.fu_accept := VecInit(observed.map(f => BoringUtils.bore(f.io.in.valid) && BoringUtils.bore(f.io.in.ready))).asUInt
  io.fu_valid := VecInit(observed.map(f => BoringUtils.bore(f.io.out.valid))).asUInt
  ClockGate.genTeSrc.cgen := false.B // Backend without MBIST: no forced-open test clocks.
}

object GenerateVDotExu {
  def main(args: Array[String]): Unit = {
    require(args.length == 1)
    val base = new MinimalConfig(1)
    val core = base(XSTileKey).head
    implicit val p: Parameters = base.alterPartial {
      case XSCoreParamsKey => core
      case utility.LogUtilsOptionsKey => utility.LogUtilsOptions(
        enableDebug = false, enablePerf = false, fpgaPlatform = false)
      case utility.PerfCounterOptionsKey => utility.PerfCounterOptions(
        enablePerfPrint = false, enablePerfDB = false,
        perfLevel = utility.XSPerfLevel.VERBOSE, perfDBHartID = 0)
    }
    ChiselStage.emitSystemVerilogFile(new VDotExuTestTop,
      args = Array("--target-dir", args(0), "--split-verilog"),
      firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info"))
  }
}
