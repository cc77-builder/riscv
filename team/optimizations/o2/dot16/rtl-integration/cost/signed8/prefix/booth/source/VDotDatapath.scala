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

/** Two unsigned 20-bit carry-save rows encoding signed dot8 + 2^19.
  * Radix-4 Booth uses 9-bit selected/complemented rows and separate neg carries.
  * There is no carry-propagate addition, clock or state inside this module.
  * Dot8 takes the low 19-bit modular sum. Dot16 adds two biased halves modulo
  * 2^20; the two biases cancel. A disabled high half must encode 2^19.
  */
class VDotCarrySaveRows extends BlackBox with HasBlackBoxInline {
  val io = IO(new Bundle {
    val vs1 = Input(UInt(64.W))
    val vs2 = Input(UInt(64.W))
    val row0 = Output(UInt(20.W))
    val row1 = Output(UInt(20.W))
  })

  setInline("VDotCarrySaveRows.sv", VDotCarrySaveRows.inlineText)
}

object VDotCarrySaveRows {
  // Each compressor consumes only previous-layer bits. Recoding and negation
  // use scalar Boolean equations; the +1 for a negative digit stays in the heap.
  val inlineText: String = {
    val width = 20
    val lines = scala.collection.mutable.ArrayBuffer[String](
      "module VDotCarrySaveRows(",
      "  input wire [63:0] vs1,",
      "  input wire [63:0] vs2,",
      "  output wire [19:0] row0,",
      "  output wire [19:0] row1",
      ");")
    def wire(name: String, expression: String): Unit = {
      lines += s"  wire $name;"
      lines += s"  assign $name = $expression;"
    }
    var columns = Vector.fill(width)(Vector.empty[String])
    for (lane <- 0 until 8; group <- 0 until 4) {
      val low = if (group == 0) "1'b0" else s"vs2[${8 * lane + 2 * group - 1}]"
      val mid = s"vs2[${8 * lane + 2 * group}]"
      val high = s"vs2[${8 * lane + 2 * group + 1}]"
      val one = s"one_${lane}_${group}"
      val two = s"two_${lane}_${group}"
      val neg = s"neg_${lane}_${group}"
      wire(one, s"$low ^ $mid")
      wire(two, s"(~$high & $mid & $low) | ($high & ~$mid & ~$low)")
      wire(neg, high)
      for (bit <- 0 until 9) {
        val name = s"pp_${lane}_${group}_${bit}"
        val a = s"vs1[${8 * lane + math.min(bit, 7)}]"
        val twiceA = if (bit == 0) "1'b0" else s"vs1[${8 * lane + bit - 1}]"
        val q = s"(($one & $a) | ($two & $twiceA)) ^ $neg"
        wire(name, if (bit == 8) s"~($q)" else q)
        val column = 2 * group + bit
        columns = columns.updated(column, columns(column) :+ name)
      }
      columns = columns.updated(2 * group, columns(2 * group) :+ neg)
    }
    // The complemented sign bit makes each row q+256, where q+neg is the
    // signed Booth digit product. Four shifted rows add bias 21760 per lane.
    // 8*21760 + 350208 = 2^19. Keep the neg carry outside the 9-bit row:
    // a=-128,digit=-2 uses q=255 and neg=1, giving the exact product +256.
    for (column <- Seq(18, 16, 14, 12, 11)) {
      columns = columns.updated(column, columns(column) :+ "1'b1")
    }
    for ((limit, level) <- Seq(28, 19, 13, 9, 6, 4, 3, 2).zipWithIndex) {
      val next = Array.fill(width)(scala.collection.mutable.ArrayBuffer.empty[String])
      for (column <- 0 until width) {
        val old = columns(column)
        var consumed = 0
        var cell = 0
        while (old.size - consumed + next(column).size > limit) {
          val excess = old.size - consumed + next(column).size - limit
          val full = excess >= 2
          val count = if (full) 3 else 2
          require(old.size - consumed >= count, "carry-save level must not consume its new carries")
          val x = old(consumed)
          val y = old(consumed + 1)
          val sum = s"s_${level}_${column}_${cell}"
          val carry = s"c_${level}_${column}_${cell}"
          if (full) {
            val z = old(consumed + 2)
            wire(sum, s"$x ^ $y ^ $z")
            wire(carry, s"($x & $y) | (($x ^ $y) & $z)")
          } else {
            wire(sum, s"$x ^ $y")
            wire(carry, s"$x & $y")
          }
          next(column) += sum
          if (column + 1 < width) next(column + 1) += carry
          consumed += count
          cell += 1
        }
        next(column) ++= old.drop(consumed)
        require(next(column).size <= limit, "fixed carry-save level height")
      }
      columns = next.toVector.map(_.toVector)
    }
    require(columns.forall(_.size <= 2), "exactly two final rows")
    for (row <- 0 until 2) {
      val bits = (width - 1 to 0 by -1).map(column => columns(column).lift(row).getOrElse("1'b0"))
      lines += s"  assign row$row = " + bits.mkString("{", ", ", "};")
    }
    lines += "endmodule"
    lines.mkString("\n") + "\n"
  }
}

/** Fixed-width modulo sum of the saved carry-save rows. No state or clock.
  * The W20 form first compresses four rows to two; W19 already has two rows.
  * A fixed parallel prefix computes the final carry using only the old layer.
  */
class VDotPrefixFinish(val width: Int, val rowCount: Int)
  extends BlackBox with HasBlackBoxInline {
  require((width == 19 && rowCount == 2) || (width == 20 && rowCount == 4))
  override def desiredName: String = s"VDotPrefixFinish$width"
  val io = IO(new Bundle {
    val rows = Input(Vec(rowCount, UInt(width.W)))
    val result = Output(UInt(width.W))
  })
  setInline(s"VDotPrefixFinish$width.sv", VDotPrefixFinish.inlineText(width, rowCount))
}

object VDotPrefixFinish {
  def inlineText(width: Int, rowCount: Int): String = {
    require((width == 19 && rowCount == 2) || (width == 20 && rowCount == 4))
    val lines = scala.collection.mutable.ArrayBuffer[String](s"module VDotPrefixFinish$width(")
    for (row <- 0 until rowCount) lines += s"  input wire [${width - 1}:0] rows_$row,"
    lines += s"  output wire [${width - 1}:0] result"
    lines += ");"
    def wire(name: String, expression: String): Unit = {
      lines += s"  wire [${width - 1}:0] $name;"
      lines += s"  assign $name = $expression;"
    }
    if (rowCount == 4) {
      wire("cs0_sum", "rows_0 ^ rows_1 ^ rows_2")
      wire("cs0_raw", "(rows_0 & rows_1) | ((rows_0 ^ rows_1) & rows_2)")
      wire("cs0_carry", s"{cs0_raw[${width - 2}:0], 1'b0}")
      wire("x", "cs0_sum ^ cs0_carry ^ rows_3")
      wire("cs1_raw", "(cs0_sum & cs0_carry) | ((cs0_sum ^ cs0_carry) & rows_3)")
      wire("y", s"{cs1_raw[${width - 2}:0], 1'b0}")
    } else {
      wire("x", "rows_0")
      wire("y", "rows_1")
    }
    wire("p0", "x ^ y")
    wire("g0", "x & y")
    for ((distance, index) <- Seq(1, 2, 4, 8, 16).zipWithIndex) {
      val old = index
      val next = index + 1
      val upper = s"${width - 1}:$distance"
      val lower = s"${width - distance - 1}:0"
      val bypass = s"${distance - 1}:0"
      wire(s"p$next", s"{p$old[$upper] & p$old[$lower], p$old[$bypass]}")
      wire(s"g$next", s"{g$old[$upper] | (p$old[$upper] & g$old[$lower]), g$old[$bypass]}")
    }
    lines += s"  assign result = p0 ^ {g5[${width - 2}:0], 1'b0};"
    lines += "endmodule"
    lines.mkString("\n") + "\n"
  }
}
