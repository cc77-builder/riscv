package team.vdot

import chisel3._
import chisel3.util._
import chisel3.util.experimental.BoringUtils.tapAndRead
import _root_.circt.stage.ChiselStage
import freechips.rocketchip.diplomacy.LazyModule
import org.chipsalliance.cde.config.Parameters
import top.MinimalConfig
import utility.{ClockGate, XSLog}
import xiangshan._
import xiangshan.backend.Bundles.UopIdx
import xiangshan.backend.exu.ExeUnit
import xiangshan.backend.fu.FuType

/** Flat stimulus adapter around the unmodified production VFEX4 ExeUnit.
  * The real Dispatcher, busy register, clock gates and all three real FUs remain
  * instantiated. Additional observations only read existing implementation nets.
  */
class VDotParentTestTop(implicit p: Parameters) extends XSModule {
  require(RobSize == 48 && VLEN == 128, "parent test requires MinimalConfig ROB=48/VLEN=128")
  require(EnableClockGate, "parent test must retain production clock gating")

  // Perform the same parameter binding as BackendInlined before constructing IO.
  // These are the original MinimalConfig objects; no private replacement EXU/FU config.
  backendParams.configChecks
  backendParams.allSchdParams.foreach(_.bindBackendParam(backendParams))
  backendParams.allIssueParams.foreach(_.bindBackendParam(backendParams))
  backendParams.allExuParams.zipWithIndex.foreach { case (cfg, index) =>
    cfg.bindBackendParam(backendParams)
    cfg.updateIQWakeUpConfigs(backendParams.iqWakeUpParams)
    cfg.updateExuIdx(index)
  }
  private val exuParams = backendParams.allExuParams.find(_.name == "VFEX4").get
  require(exuParams.fuConfigs.map(_.fuType) == Seq(FuType.vfdiv, FuType.vidiv, FuType.vdot),
    "parent test requires original VFEX4 VFDiv/VIDiv/VDot ordering")
  require(!exuParams.latencyCertain && exuParams.numRegSrc == 5 && exuParams.numCopySrc == 0)
  require(exuParams.wbPathNum == 3 && exuParams.wbVecIndex == 1 && exuParams.wbV0Index == 2)
  println(s"VDOT_PARENT_REAL_EXU name=${exuParams.name} clockGate=$EnableClockGate " +
    s"fu=${exuParams.fuConfigs.map(_.name).mkString(",")} wbPaths=${exuParams.wbPathNum}")

  val io = IO(new Bundle {
    val in_valid = Input(Bool())
    val in_ready = Output(Bool())
    val out_valid = Output(Bool())
    val out_ready = Input(Bool())
    // 0 = VDot, 1 = vector integer divide/remainder, 2 = vector FP divide/sqrt.
    val kind = Input(UInt(2.W))
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
    val vuop_idx = Input(UopIdx())
    val op = Input(UInt(FuOpTypeWidth.W))
    val frm = Input(UInt(3.W))
    val fp_rm = Input(UInt(3.W))
    val fp_wflags = Input(Bool())
    val rob_flag = Input(Bool())
    val rob_value = Input(UInt(log2Ceil(RobSize).W))
    val pdest = Input(UInt(exuParams.wbPregIdxWidth.W))
    val write_v0 = Input(Bool())
    val perf_tag = Input(UInt(64.W))
    val flush_valid = Input(Bool())
    val flush_flag = Input(Bool())
    val flush_value = Input(UInt(log2Ceil(RobSize).W))
    val flush_self = Input(Bool())
    // Actual production ClockGate TE: use only during reset initialization.
    val test_enable = Input(Bool())
    val result = Output(UInt(128.W))
    val result_vec = Output(UInt(128.W))
    val result_v0 = Output(UInt(128.W))
    val out_rob_flag = Output(Bool())
    val out_rob_value = Output(UInt(log2Ceil(RobSize).W))
    val out_pdest = Output(UInt(exuParams.wbPregIdxWidth.W))
    val out_int_wen = Output(Bool())
    val out_fp_wen = Output(Bool())
    val out_vec_wen = Output(Bool())
    val out_v0_wen = Output(Bool())
    val out_vl_wen = Output(Bool())
    val out_exception = Output(UInt(ExceptionVec.ExceptionVecSize.W))
    val out_fflags = Output(UInt(5.W))
    val out_wflags = Output(Bool())
    val out_vxsat = Output(Bool())
    val out_perf_tag = Output(UInt(64.W))
    val out_rename_tag = Output(UInt(64.W))
    // ExuOutput has no vpu field: this reads the selected real child FU snapshot.
    val out_ctrl = Output(UInt(27.W))
    // Read-only observed signals. Bit 0 = VDot, bit 1 = VIDiv, bit 2 = VFDiv.
    val fu_in_valid = Output(UInt(3.W))
    val fu_in_ready = Output(UInt(3.W))
    val fu_out_valid = Output(UInt(3.W))
    val fu_out_ready = Output(UInt(3.W))
    val fu_clock = Output(UInt(3.W))
    val busy = Output(Bool())
  })

  val dut = Module(LazyModule(new ExeUnit(exuParams)).module)
  dut.io.in.bits := 0.U.asTypeOf(dut.io.in.bits)
  dut.io.flush := 0.U.asTypeOf(dut.io.flush)
  dut.io.in.valid := io.in_valid
  io.in_ready := dut.io.in.ready
  dut.io.out.ready := io.out_ready
  io.out_valid := dut.io.out.valid
  val in = dut.io.in.bits
  in.fuType := MuxLookup(io.kind, FuType.vdot.U)(Seq(
    0.U -> FuType.vdot.U, 1.U -> FuType.vidiv.U, 2.U -> FuType.vfdiv.U))
  when(io.in_valid && !reset.asBool) { assert(io.kind <= 2.U, "invalid parent test FU kind") }
  in.fuOpType := io.op
  in.src(0) := io.vs1
  in.src(1) := io.vs2
  in.src(2) := io.old_vd
  in.src(3) := io.mask
  in.src(4) := io.vl
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
  vpu.vuopIdx := io.vuop_idx
  vpu.lastUop := true.B
  vpu.frm := io.frm
  in.fpu.get.rm := io.fp_rm
  in.fpu.get.wflags := io.fp_wflags
  dut.io.frm.get := io.frm
  in.perfDebugInfo.issueTime := io.perf_tag
  in.perfDebugInfo.renameTime := io.perf_tag ^ "hf0e1d2c3b4a59687".U
  dut.io.flush.valid := io.flush_valid
  dut.io.flush.bits.robIdx.flag := io.flush_flag
  dut.io.flush.bits.robIdx.value := io.flush_value
  dut.io.flush.bits.level := io.flush_self

  val out = dut.io.out.bits
  io.result := out.data(0)
  io.result_vec := out.data(exuParams.wbVecIndex)
  io.result_v0 := out.data(exuParams.wbV0Index)
  io.out_rob_flag := out.robIdx.flag
  io.out_rob_value := out.robIdx.value
  io.out_pdest := out.pdest
  io.out_int_wen := out.intWen.getOrElse(false.B)
  io.out_fp_wen := out.fpWen.getOrElse(false.B)
  io.out_vec_wen := out.vecWen.get
  io.out_v0_wen := out.v0Wen.get
  io.out_vl_wen := out.vlWen.getOrElse(false.B)
  io.out_exception := out.exceptionVec.get.asUInt
  io.out_fflags := out.fflags.get
  io.out_wflags := out.wflags.get
  io.out_vxsat := out.vxsat.getOrElse(false.B)
  io.out_perf_tag := out.debugInfo.issueTime
  io.out_rename_tag := out.debugInfo.renameTime

  // tapAndRead adds observation-only wiring; it does not drive the real design.
  private val observed = Seq(FuType.vdot, FuType.vidiv, FuType.vfdiv).map { kind =>
    dut.funcUnits(exuParams.fuConfigs.indexWhere(_.fuType == kind))
  }
  private val childInValid = observed.map(fu => tapAndRead(fu.io.in.valid))
  private val childInReady = observed.map(fu => tapAndRead(fu.io.in.ready))
  private val childOutValid = observed.map(fu => tapAndRead(fu.io.out.valid))
  private val childOutReady = observed.map(fu => tapAndRead(fu.io.out.ready))
  private val childClock = observed.map(fu => tapAndRead(fu.clock).asBool)
  io.fu_in_valid := VecInit(childInValid).asUInt
  io.fu_in_ready := VecInit(childInReady).asUInt
  io.fu_out_valid := VecInit(childOutValid).asUInt
  io.fu_out_ready := VecInit(childOutReady).asUInt
  io.fu_clock := VecInit(childClock).asUInt
  io.busy := tapAndRead(dut.busy)
  private val childVpu = observed.map(fu => tapAndRead(fu.io.out.bits.ctrl.vpu.get))
  private val packedChildVpu = childVpu.map(v => Cat(v.vill, v.vma, v.vta, v.vsew,
    v.vlmul, v.vm, v.vstart, v.vl, v.vxrm))
  io.out_ctrl := Mux1H(childOutValid, packedChildVpu)

  // Complete the same clock-test source wiring used by the production backend.
  private val clockTest = ClockGate.genTeSrc
  clockTest.cgen := io.test_enable
  dontTouch(clockTest)
  XSLog.collect(0.U(64.W), false.B, false.B, false.B)
}

object GenerateVDotParent {
  def main(args: Array[String]): Unit = {
    require(args.length == 1, "usage: GenerateVDotParent /fresh/rtl/output")
    val base = new MinimalConfig(1)
    implicit val p: Parameters = base.alterPartial {
      case XSCoreParamsKey => base(XSTileKey).head
      case utility.LogUtilsOptionsKey => utility.LogUtilsOptions(
        enableDebug = false, enablePerf = false, fpgaPlatform = false)
      case utility.PerfCounterOptionsKey => utility.PerfCounterOptions(
        enablePerfPrint = false, enablePerfDB = false,
        perfLevel = utility.XSPerfLevel.VERBOSE, perfDBHartID = 0)
    }
    ChiselStage.emitSystemVerilogFile(new VDotParentTestTop,
      args = Array("--target-dir", args(0)),
      firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info"))
  }
}
