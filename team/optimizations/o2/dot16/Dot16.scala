package team.vdot.dot16

import chisel3._
import chisel3.util._
import _root_.circt.stage.ChiselStage
import team.vdot.param.{DotParameters, ParamProducts, ParamReduce}

/** Independent arithmetic/flow prototype; not the production XiangShan FU.
  * killP/killR are externally supplied decisions. This module does not implement
  * RobPtr comparison, parent DIV arbitration, decode, CSR state, or DiffTest.
  * Product and response slots have the same transition equations as O2.
  */
class Dot16Prototype(pairs: Int, splitResult: Boolean) extends Module {
  require(pairs == 8 || pairs == 16)
  require(!splitResult || pairs == 16)
  override def desiredName = "Dot16Prototype"
  val io = IO(new Bundle {
    val in_valid = Input(Bool())
    val in_ready = Output(Bool())
    val out_valid = Output(Bool())
    val out_ready = Input(Bool())
    val vs1 = Input(UInt(128.W))
    val vs2 = Input(UInt(128.W))
    val op = Input(UInt(2.W)) // 0: unchanged dot8; 1: candidate dot16
    val vl = Input(UInt(8.W))
    val vsew = Input(UInt(2.W))
    val vlmul = Input(UInt(3.W))
    val vstart = Input(UInt(8.W))
    val vill = Input(Bool())
    val vm = Input(Bool())
    val vta = Input(Bool())
    val vma = Input(Bool())
    val tag = Input(UInt(32.W))
    val write_v0 = Input(Bool())
    val flush_valid = Input(Bool())
    val kill_p = Input(Bool())
    val kill_r = Input(Bool())
    val p_valid = Output(Bool())
    val r_valid = Output(Bool())
    val occupancy = Output(UInt(2.W))
    val result = Output(UInt(128.W))
    val out_tag = Output(UInt(32.W))
    val illegal = Output(Bool())
    val vec_wen = Output(Bool())
    val v0_wen = Output(Bool())
  })

  private val isDot16 = if (pairs == 16) io.op === 1.U else false.B
  private val supportedOp = io.op === 0.U || isDot16
  private val expectedVl = Mux(isDot16, 16.U(8.W), 8.U(8.W))
  private val illegalInput = !supportedOp || io.vill || io.vsew =/= 0.U ||
    io.vlmul =/= 0.U || !io.vm || io.vstart =/= 0.U || io.vl =/= expectedVl

  private val pValid = RegInit(false.B)
  private val rValid = RegInit(false.B)
  private val pProducts = Reg(Vec(pairs, SInt(16.W)))
  private val pTag = Reg(UInt(32.W))
  private val pIllegal = Reg(Bool())
  private val pV0 = Reg(Bool())
  private val rTag = Reg(UInt(32.W))
  private val rIllegal = Reg(Bool())
  private val rV0 = Reg(Bool())

  private val liveP = pValid && !io.kill_p && !reset.asBool
  private val liveR = rValid && !io.kill_r && !reset.asBool
  private val rReady = !liveR || io.out_ready
  private val move = liveP && rReady
  private val pReady = !liveP || rReady
  io.in_ready := pReady && !io.flush_valid && !reset.asBool
  io.out_valid := liveR
  private val accept = io.in_valid && io.in_ready
  private val respond = io.out_valid && io.out_ready
  pValid := (liveP && !move) || accept
  rValid := (liveR && !respond) || move

  io.p_valid := pValid
  io.r_valid := rValid
  io.occupancy := pValid.asUInt +& rValid.asUInt
  io.out_tag := rTag
  io.illegal := rIllegal
  io.vec_wen := !rIllegal && !rV0
  io.v0_wen := !rIllegal && rV0

  private val products = Module(new ParamProducts(DotParameters(8, pairs, 32)))
  products.io.vs1 := io.vs1
  products.io.vs2 := io.vs2
  when(accept) {
    // Encode the old operation by zeroing unused products before the P register.
    // No later mode bit is needed; both reductions read precisely the captured P.
    for (lane <- 0 until pairs) {
      if (lane < 8) pProducts(lane) := products.io.products(lane)
      else pProducts(lane) := Mux(isDot16, products.io.products(lane), 0.S(16.W))
    }
    pTag := io.tag
    pIllegal := illegalInput
    pV0 := io.write_v0
  }
  when(move) {
    rTag := pTag
    rIllegal := pIllegal
    rV0 := pV0
  }

  private val result32 = Wire(UInt(32.W))
  if (splitResult) {
    // P->R keeps two independent 8-product trees. R->output adds the partials.
    val half = Seq.fill(2)(Module(new ParamReduce(DotParameters(8, 8, 32))))
    val partial = Reg(Vec(2, SInt(19.W)))
    for (h <- 0 until 2) {
      half(h).io.products := VecInit(pProducts.slice(h * 8, h * 8 + 8))
      when(move) {
        partial(h) := Mux(pIllegal, 0.S(19.W), half(h).io.result(18, 0).asSInt)
      }
    }
    val sum20 = partial(0) +& partial(1)
    require(sum20.getWidth == 20)
    val extended = Wire(SInt(32.W))
    extended := sum20
    result32 := extended.asUInt
  } else {
    val reduce = Module(new ParamReduce(DotParameters(8, pairs, 32)))
    reduce.io.products := pProducts
    val registered = Reg(UInt(32.W))
    when(move) { registered := Mux(pIllegal, 0.U(32.W), reduce.io.result(31, 0)) }
    result32 := registered
  }
  io.result := Cat(0.U(96.W), result32)

  when(io.out_valid) {
    assert(io.result(127, 32) === 0.U)
    when(io.illegal) { assert(!io.vec_wen && !io.v0_wen && result32 === 0.U) }
  }
  when(reset.asBool) { assert(!accept && !respond) }
  private val blocked = RegNext(io.out_valid && !io.out_ready, false.B)
  private val packet = Cat(io.out_tag, io.illegal, io.vec_wen, io.v0_wen, io.result)
  private val held = RegEnable(packet, io.out_valid && !io.out_ready)
  when(blocked && !io.kill_r && !reset.asBool) {
    assert(io.out_valid && packet === held, "changed or lost blocked response")
  }
}

object GenerateDot16 {
  def main(args: Array[String]): Unit = {
    require(args.length == 2, "variant output-dir")
    val (pairs, split) = args(0) match {
      case "baseline8" => (8, false)
      case "direct16" => (16, false)
      case "split16" => (16, true)
      case other => throw new IllegalArgumentException("unknown variant " + other)
    }
    ChiselStage.emitSystemVerilogFile(new Dot16Prototype(pairs, split),
      args = Array("--target-dir", args(1)),
      firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info",
        "--lowering-options=disallowLocalVariables,disallowPackedArrays"))
  }
}
