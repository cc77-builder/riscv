package team.vdot.param

import chisel3._
import chisel3.util._

/** Elaboration parameters for an independently tested arithmetic component.
  * Only s8x8/r32 and s16x8/r64 are part of the T15 acceptance matrix.
  */
case class DotParameters(elementBits: Int, pairs: Int, resultBits: Int, registerBits: Int = 128) {
  require(Set(8, 16).contains(elementBits), "T15_PARAMETER: elementBits must be 8 or 16")
  require(pairs > 0 && (pairs & (pairs - 1)) == 0, "T15_PARAMETER: pairs must be a positive power of two")
  require(registerBits == 128 && elementBits.toLong * pairs <= registerBits,
    "T15_PARAMETER: inputs must fit 128 bits")
  val productBits = 2 * elementBits
  val levels = log2Ceil(pairs)
  val accumulatorBits = productBits + levels
  require(resultBits >= accumulatorBits && resultBits <= registerBits,
    "T15_PARAMETER: result field cannot represent the exact range")
}

class ParamProducts(p: DotParameters) extends RawModule {
  val io = IO(new Bundle {
    val vs1 = Input(UInt(p.registerBits.W))
    val vs2 = Input(UInt(p.registerBits.W))
    val products = Output(Vec(p.pairs, SInt(p.productBits.W)))
  })
  for (lane <- 0 until p.pairs) {
    val low = lane * p.elementBits
    io.products(lane) := io.vs1(low + p.elementBits - 1, low).asSInt *
                        io.vs2(low + p.elementBits - 1, low).asSInt
  }
}

class ParamReduce(p: DotParameters) extends RawModule {
  val io = IO(new Bundle {
    val products = Input(Vec(p.pairs, SInt(p.productBits.W)))
    val result = Output(UInt(p.registerBits.W))
  })
  private def tree(values: Seq[SInt]): SInt = {
    if (values.size == 1) values.head
    else tree(values.grouped(2).map(pair => pair(0) +& pair(1)).toSeq)
  }
  private val sum = tree(io.products.toSeq)
  require(sum.getWidth == p.accumulatorBits, "T15_PARAMETER: unexpected reduction width")
  private val field = Wire(SInt(p.resultBits.W))
  field := sum
  if (p.resultBits == p.registerBits) io.result := field.asUInt
  else io.result := Cat(0.U((p.registerBits - p.resultBits).W), field.asUInt)
}

class ParamDatapath(p: DotParameters) extends RawModule {
  val io = IO(new Bundle {
    val vs1 = Input(UInt(p.registerBits.W))
    val vs2 = Input(UInt(p.registerBits.W))
    val result = Output(UInt(p.registerBits.W))
  })
  private val products = Module(new ParamProducts(p))
  private val reduce = Module(new ParamReduce(p))
  products.io.vs1 := io.vs1
  products.io.vs2 := io.vs2
  reduce.io.products := products.io.products
  io.result := reduce.io.result
}

/** Standalone single-outstanding experiment; not XiangShan's FU/ROB interface.
  * E0 captures products and tag, E1 captures result, E2 may respond; II >= 3.
  */
class ParamPipe(p: DotParameters) extends Module {
  val io = IO(new Bundle {
    val vs1 = Input(UInt(p.registerBits.W))
    val vs2 = Input(UInt(p.registerBits.W))
    val inValid = Input(Bool())
    val inReady = Output(Bool())
    val tagIn = Input(UInt(32.W))
    val outValid = Output(Bool())
    val outReady = Input(Bool())
    val result = Output(UInt(p.registerBits.W))
    val tagOut = Output(UInt(32.W))
    val flush = Input(Bool())
  })
  private val idle :: reduceState :: respond :: Nil = Enum(3)
  private val state = RegInit(idle)
  private val productsReg = Reg(Vec(p.pairs, SInt(p.productBits.W)))
  private val resultReg = Reg(UInt(p.registerBits.W))
  private val tagReg = Reg(UInt(32.W))
  private val products = Module(new ParamProducts(p))
  private val reduce = Module(new ParamReduce(p))
  products.io.vs1 := io.vs1
  products.io.vs2 := io.vs2
  reduce.io.products := productsReg
  io.inReady := state === idle && !io.flush && !reset.asBool
  io.outValid := state === respond && !io.flush && !reset.asBool
  io.result := resultReg
  io.tagOut := tagReg
  when(io.flush) {
    state := idle
  }.otherwise {
    switch(state) {
      is(idle) {
        when(io.inValid && io.inReady) {
          productsReg := products.io.products
          tagReg := io.tagIn
          state := reduceState
        }
      }
      is(reduceState) {
        resultReg := reduce.io.result
        state := respond
      }
      is(respond) {
        when(io.outReady) { state := idle }
      }
    }
  }
}
