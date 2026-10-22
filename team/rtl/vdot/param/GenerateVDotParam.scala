package team.vdot.param

import chisel3._
import circt.stage.ChiselStage
import xiangshan.backend.fu.vector.VDotDatapath

class VDotParamTestTop(p: DotParameters) extends Module {
  val io = IO(new Bundle {
    val vs1 = Input(UInt(128.W))
    val vs2 = Input(UInt(128.W))
    val inValid = Input(Bool())
    val inReady = Output(Bool())
    val tagIn = Input(UInt(32.W))
    val outValid = Output(Bool())
    val outReady = Input(Bool())
    val pipeResult = Output(UInt(128.W))
    val tagOut = Output(UInt(32.W))
    val flush = Input(Bool())
    val combResult = Output(UInt(128.W))
    val legacyResult = Output(UInt(128.W))
  })
  private val comb = Module(new ParamDatapath(p))
  private val pipe = Module(new ParamPipe(p))
  comb.io.vs1 := io.vs1
  comb.io.vs2 := io.vs2
  io.combResult := comb.io.result
  pipe.io.vs1 := io.vs1
  pipe.io.vs2 := io.vs2
  pipe.io.inValid := io.inValid
  io.inReady := pipe.io.inReady
  pipe.io.tagIn := io.tagIn
  io.outValid := pipe.io.outValid
  pipe.io.outReady := io.outReady
  io.pipeResult := pipe.io.result
  io.tagOut := pipe.io.tagOut
  pipe.io.flush := io.flush
  if (p == DotParameters(8, 8, 32)) {
    val legacy = Module(new VDotDatapath)
    legacy.io.vs1 := io.vs1
    legacy.io.vs2 := io.vs2
    io.legacyResult := legacy.io.result
  } else io.legacyResult := 0.U
}

object GenerateVDotParam {
  def main(args: Array[String]): Unit = {
    require(args.length == 2, "usage: GenerateVDotParam output profile")
    val p = args(1) match {
      case "s8x8" => DotParameters(8, 8, 32)
      case "s16x8" => DotParameters(16, 8, 64)
      case "invalid-result32" => DotParameters(16, 8, 32)
      case "invalid-result34" => DotParameters(16, 8, 34)
      case "invalid-result129" => DotParameters(16, 8, 129)
      case "invalid-pairs0" => DotParameters(16, 0, 64)
      case "invalid-pairs3" => DotParameters(16, 3, 64)
      case "invalid-input-overflow" => DotParameters(16, 16, 64)
      case "invalid-element" => DotParameters(7, 8, 32)
      case "invalid-container" => DotParameters(8, 8, 32, 64)
      case _ => throw new IllegalArgumentException("T15_PARAMETER: unknown profile")
    }
    println(s"T15_CONFIG elementBits=${p.elementBits} pairs=${p.pairs} resultBits=${p.resultBits} accumulatorBits=${p.accumulatorBits} levels=${p.levels}")
    ChiselStage.emitSystemVerilogFile(new VDotParamTestTop(p),
      args = Array("--target-dir", args(0)),
      firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info"))
  }
}
