package team.vdot

import chisel3._
import _root_.circt.stage.ChiselStage
import freechips.rocketchip.diplomacy.LazyModule
import org.chipsalliance.cde.config.Parameters
import top.MinimalConfig
import utility.{ClockGate, XSLog}
import xiangshan._
import xiangshan.backend.exu.ExeUnit
import xiangshan.backend.fu.{FuConfig, FuncUnit, FuType}
import xiangshan.backend.fu.wrapper.{VDot, VDotElastic, VDotO2}

/** Common full production FU interface, with no test/observer/tap outputs. */
class CommonFuCostTop(implicit p: Parameters) extends XSModule {
  val dut: FuncUnit = if (VDotO2.enabled) {
    Module(new VDotElastic(FuConfig.VDotCfg))
  } else {
    Module(new VDot(FuConfig.VDotCfg))
  }
  val io = IO(chiselTypeOf(dut.io))
  io <> dut.io
}

/** Real VFEX4 and all real DIV/gates, exposing the same production IO in both modes. */
class CommonParentCostTop(implicit p: Parameters) extends XSModule {
  backendParams.configChecks
  backendParams.allSchdParams.foreach(_.bindBackendParam(backendParams))
  backendParams.allIssueParams.foreach(_.bindBackendParam(backendParams))
  backendParams.allExuParams.zipWithIndex.foreach { case (cfg, index) =>
    cfg.bindBackendParam(backendParams)
    cfg.updateIQWakeUpConfigs(backendParams.iqWakeUpParams)
    cfg.updateExuIdx(index)
  }
  private val cfg = backendParams.allExuParams.find(_.name == "VFEX4").get
  require(EnableClockGate && !cfg.latencyCertain)
  require(cfg.fuConfigs.map(_.fuType) == Seq(FuType.vfdiv, FuType.vidiv, FuType.vdot))
  val dut = Module(LazyModule(new ExeUnit(cfg)).module)
  val io = IO(chiselTypeOf(dut.io))
  io <> dut.io
  val testEnable = IO(Input(Bool()))
  val clockTest = ClockGate.genTeSrc
  clockTest.cgen := testEnable
  dontTouch(clockTest)
  XSLog.collect(0.U(64.W), false.B, false.B, false.B)
}

object GenerateVDotCost {
  def main(args: Array[String]): Unit = {
    require(args.length == 2 && Set("fu", "parent").contains(args(0)))
    for (key <- Seq("VDOT_T12_TRACE", "VDOT_T13_TRACE", "VDOT_O1_TRACE", "VDOT_O2_TRACE")) {
      require(sys.env.get(key).contains("0"), s"$key must be explicitly disabled for cost evaluation")
    }
    require(sys.env.get("VDOT_T14_FUSED_INPUT").contains("1"))
    require(VDotO2.enabled || sys.env.get("VDOT_O1_HANDOFF").contains("1"))
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
    ChiselStage.emitSystemVerilogFile(
      if (args(0) == "fu") new CommonFuCostTop else new CommonParentCostTop,
      args = Array("--target-dir", args(1), "--split-verilog"),
      firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info"))
  }
}
