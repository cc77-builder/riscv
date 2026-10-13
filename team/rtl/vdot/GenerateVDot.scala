package team.vdot

import circt.stage.ChiselStage
import xiangshan.backend.fu.vector.VDotDatapath

/** Emit the actual production arithmetic modules without constructing a CPU. */
object GenerateVDot {
  def main(args: Array[String]): Unit = {
    require(args.length == 1, "usage: GenerateVDot <target-directory>")
    ChiselStage.emitSystemVerilogFile(
      new VDotDatapath,
      args = Array("--target-dir", args(0)),
      firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info"),
    )
  }
}
