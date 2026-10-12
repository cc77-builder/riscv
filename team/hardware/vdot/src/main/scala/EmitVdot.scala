import circt.stage.ChiselStage
import xiangshan.backend.fu.vector.VdotExec

object EmitVdot extends App {
  require(args.length == 1, "Usage: EmitVdot <target-dir>")
  ChiselStage.emitSystemVerilogFile(
    new VdotExec(),
    Array("--target-dir", args(0)),
    Array("--disable-all-randomization", "--strip-debug-info")
  )
}
