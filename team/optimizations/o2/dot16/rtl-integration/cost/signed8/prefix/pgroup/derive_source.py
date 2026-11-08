#!/usr/bin/env python3
"""Derive one P-heap grouping candidate; no compiler, solver or simulator."""
from pathlib import Path
import difflib
import hashlib
import json

ROOT = Path(__file__).resolve().parent
BASE_SHA = "1d02d8a34772e7d9b9947f997f32465f3e946f4b24cacc66159eef7ee10ab3bb"
WRAPPER_SHA = "912c1a038ef8e9a1ac56cfa349161ae1c582d763acfce5352b08ebde2a227f92"
CONTRACT = "dot16-prefix-pgroup-local-v1"

NEW_OBJECT = r"""object VDotCarrySaveRows {
  // These elaboration-only scores order old-layer bits; they add no RTL state.
  // Gate depth is a unit two-input-gate estimate, not a library timing model.
  private case class HeapBit(name: String, compressorDepth: Int, gateDepth: Int)

  // Keep the original fixed heights and consume only the previous level.
  // Prefer shallow bits, then put the latest of each FA's inputs on z.
  val inlineText: String = {
    val width = 19
    val lines = scala.collection.mutable.ArrayBuffer[String](
      "module VDotCarrySaveRows(",
      "  input wire [63:0] vs1,",
      "  input wire [63:0] vs2,",
      "  output wire [18:0] row0,",
      "  output wire [18:0] row1",
      ");")
    def wire(name: String, expression: String): Unit = {
      lines += s"  wire $name;"
      lines += s"  assign $name = $expression;"
    }
    var columns = Vector.fill(width)(Vector.empty[HeapBit])
    for (lane <- 0 until 8; i <- 0 until 8; j <- 0 until 8) {
      val name = s"pp_${lane}_${i}_${j}"
      val term = s"(vs1[${8 * lane + i}] & vs2[${8 * lane + j}])"
      val complemented = (i == 7) != (j == 7)
      wire(name, if (complemented) s"~$term" else term)
      val bit = HeapBit(name, 0, if (complemented) 2 else 1)
      columns = columns.updated(i + j, columns(i + j) :+ bit)
    }
    // Each complemented signed product heap is a*b + 32512.
    // Eight heaps plus bits 18 and 11 equal the exact signed sum + 2^19.
    // All later arithmetic is modulo 2^19; there is no post-P correction.
    for (column <- Seq(18, 11)) {
      columns = columns.updated(column, columns(column) :+ HeapBit("1'b1", 0, 0))
    }
    for ((limit, level) <- Seq(63, 42, 28, 19, 13, 9, 6, 4, 3, 2).zipWithIndex) {
      val next = Array.fill(width)(scala.collection.mutable.ArrayBuffer.empty[HeapBit])
      for (column <- 0 until width) {
        val old = columns(column).zipWithIndex.sortBy { case (bit, order) =>
          (bit.compressorDepth, bit.gateDepth, order)
        }.map(_._1)
        var consumed = 0
        var cell = 0
        while (old.size - consumed + next(column).size > limit) {
          val excess = old.size - consumed + next(column).size - limit
          val full = excess >= 2
          val count = if (full) 3 else 2
          require(old.size - consumed >= count, "carry-save level must not consume its new carries")
          val selected = old.slice(consumed, consumed + count).zipWithIndex.sortBy { case (bit, order) =>
            (bit.gateDepth, order)
          }.map(_._1)
          val x = selected(0)
          val y = selected(1)
          val sum = s"s_${level}_${column}_${cell}"
          val carry = s"c_${level}_${column}_${cell}"
          val depth = selected.map(_.compressorDepth).max + 1
          val xyDepth = math.max(x.gateDepth, y.gateDepth) + 1
          val (sumDepth, carryDepth) = if (full) {
            val z = selected(2)
            wire(sum, s"${x.name} ^ ${y.name} ^ ${z.name}")
            wire(carry, s"(${x.name} & ${y.name}) | ((${x.name} ^ ${y.name}) & ${z.name})")
            val zDepth = math.max(xyDepth, z.gateDepth) + 1
            (zDepth, math.max(xyDepth, zDepth) + 1)
          } else {
            wire(sum, s"${x.name} ^ ${y.name}")
            wire(carry, s"${x.name} & ${y.name}")
            (xyDepth, xyDepth)
          }
          next(column) += HeapBit(sum, depth, sumDepth)
          if (column + 1 < width) next(column + 1) += HeapBit(carry, depth, carryDepth)
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
      val bits = (width - 1 to 0 by -1).map(column =>
        columns(column).lift(row).map(_.name).getOrElse("1'b0"))
      lines += s"  assign row$row = " + bits.mkString("{", ", ", "};")
    }
    lines += "endmodule"
    lines.mkString("\n") + "\n"
  }
}
"""

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    source = ROOT / "base/source/VDotDatapath.scala"
    wrapper = ROOT / "base/source/VDotElastic.scala"
    raw = source.read_bytes()
    wraw = wrapper.read_bytes()
    assert digest(raw) == BASE_SHA and digest(wraw) == WRAPPER_SHA
    original = raw.decode("utf-8")
    start = original.index("object VDotCarrySaveRows {")
    end = original.index("\n/** Fixed-width modulo sum", start)
    old = original[start:end]
    assert old.endswith("}\n")
    changed = original[:start] + NEW_OBJECT + original[end:]
    assert changed.count(NEW_OBJECT) == 1
    assert changed.replace(NEW_OBJECT, old, 1).encode() == raw
    dest = ROOT / "source"
    dest.mkdir(exist_ok=False)
    candidate = changed.encode("utf-8")
    (dest / "VDotDatapath.scala").write_bytes(candidate)
    (dest / "VDotElastic.scala").write_bytes(wraw)
    proof = dict(
        status="SOURCE_DERIVED_NOT_EXECUTED", contract=CONTRACT,
        baseline_datapath_sha256=BASE_SHA, baseline_datapath_bytes=len(raw),
        candidate_datapath_sha256=digest(candidate), candidate_datapath_bytes=len(candidate),
        baseline_wrapper_sha256=WRAPPER_SHA, candidate_wrapper_sha256=digest(wraw),
        wrapper_byte_identical=True, exact_inverse=True,
        edits=[dict(before=old, after=NEW_OBJECT)],
        scope="Only P carry-save input grouping and FA pin order; R finish and wrapper unchanged.",
        structural_hypothesis=dict(compressor_depth=9, unit_gate_depth=22,
                                   assumption="two-input gates, complemented PP AND+NOT=2, no constant folding"),
        measured_timing=False, new_qualification=False)
    (dest / "source-derivation.json").write_text(json.dumps(proof, indent=2)+"\n")
    (dest / "source.diff").write_text("".join(difflib.unified_diff(
        original.splitlines(True), changed.splitlines(True),
        fromfile="prefix/source/VDotDatapath.scala", tofile="pgroup/source/VDotDatapath.scala")))
    print(json.dumps({k:v for k,v in proof.items() if k != "edits"},indent=2))

if __name__ == "__main__":
    main()

