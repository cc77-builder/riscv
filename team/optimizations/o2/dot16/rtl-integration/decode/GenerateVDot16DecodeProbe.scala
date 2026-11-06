package team.vdot

import chisel3._
import _root_.circt.stage.ChiselStage
import org.chipsalliance.cde.config.Parameters
import top.MinimalConfig
import xiangshan._

/** Read-only visibility added to the unchanged production-decoder harness. */
class VDot16DecodeProbe(implicit p: Parameters) extends VDotDecodeTestTop {
  val simple_op = IO(Output(chiselTypeOf(simple.io.deq.decodedInst.fuOpType)))
  val complex_op = IO(Output(chiselTypeOf(out.fuOpType)))
  simple_op := simple.io.deq.decodedInst.fuOpType
  complex_op := out.fuOpType
}

object GenerateVDot16DecodeProbe {
  def main(args: Array[String]): Unit = {
    require(args.length == 1)
    val base = new MinimalConfig(1)
    implicit val p: Parameters = base.alterPartial {
      case XSCoreParamsKey => base(XSTileKey).head
      case utility.LogUtilsOptionsKey => utility.LogUtilsOptions(
        enableDebug = false, enablePerf = false, fpgaPlatform = false)
    }
    ChiselStage.emitSystemVerilogFile(new VDot16DecodeProbe,
      args = Array("--target-dir", args(0)),
      firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info"))
  }
}
