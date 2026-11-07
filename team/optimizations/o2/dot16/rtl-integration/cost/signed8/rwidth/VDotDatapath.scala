package xiangshan.backend.fu.vector

import chisel3._
import chisel3.util._

/** Exact signed-byte product with explicit widths in every generated consumer.
  * A real combinational implementation is emitted for simulation and synthesis.
  * No clock, state, latency, approximation or synthesis-only replacement.
  */
class VDotSignedByteProduct extends BlackBox with HasBlackBoxInline {
  val io = IO(new Bundle {
    val a = Input(UInt(8.W))
    val b = Input(UInt(8.W))
    val product = Output(SInt(16.W))
  })

  setInline("VDotSignedByteProduct.sv",
    """
      |module VDotSignedByteProduct(
      |  input  wire [7:0] a,
      |  input  wire [7:0] b,
      |  output wire signed [15:0] product
      |);
      |  assign product = $signed(a) * $signed(b);
      |endmodule
      |""".stripMargin)
}

/** Eight signed byte products for the vdot-s8x8-r32-v0.1 contract.
  * Lane 0 is bits 7:0; bits 127:64 of both operands are ignored.
  * This combinational module can precede the wrapper's product registers.
  */
class VDotProducts extends RawModule {
  val io = IO(new Bundle {
    val vs1 = Input(UInt(128.W))
    val vs2 = Input(UInt(128.W))
    val products = Output(Vec(8, SInt(16.W)))
  })

  for (lane <- 0 until 8) {
    val multiply = Module(new VDotSignedByteProduct)
    multiply.io.a := io.vs1(8 * lane + 7, 8 * lane)
    multiply.io.b := io.vs2(8 * lane + 7, 8 * lane)
    io.products(lane) := multiply.io.product
  }
}

/** Balanced, widening signed reduction of eight 16-bit products.
  * Only the low 32 bits receive the sign-extended sum; bits 127:32 are zero.
  * No mask, tail, old destination, rounding, or saturation is involved.
  */
class VDotReduce extends RawModule {
  val io = IO(new Bundle {
    val products = Input(Vec(8, SInt(16.W)))
    val result = Output(UInt(128.W))
  })

  private val sums17 = Wire(Vec(4, SInt(17.W)))
  private val sums18 = Wire(Vec(2, SInt(18.W)))
  private val sum19 = Wire(SInt(19.W))

  for (pair <- 0 until 4) {
    sums17(pair) := io.products(2 * pair) +& io.products(2 * pair + 1)
  }
  for (pair <- 0 until 2) {
    sums18(pair) := sums17(2 * pair) +& sums17(2 * pair + 1)
  }
  sum19 := sums18(0) +& sums18(1)

  private val result32 = Wire(SInt(32.W))
  result32 := sum19
  io.result := Cat(0.U(96.W), result32.asUInt)
}

/** Combinational arithmetic top for independent verification.
  * The future functional-unit wrapper instantiates the same two submodules
  * separately, with registers between them; this top has no cycle protocol.
  */
class VDotDatapath extends RawModule {
  val io = IO(new Bundle {
    val vs1 = Input(UInt(128.W))
    val vs2 = Input(UInt(128.W))
    val result = Output(UInt(128.W))
  })

  private val products = Module(new VDotProducts)
  private val reduce = Module(new VDotReduce)

  products.io.vs1 := io.vs1
  products.io.vs2 := io.vs2
  reduce.io.products := products.io.products
  io.result := reduce.io.result
}
