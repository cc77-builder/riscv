#!/usr/bin/env python3
"""Derive one radix-4 Booth candidate from the frozen prefix sources."""
from pathlib import Path
import difflib
import hashlib
import json

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / 'prefix-pgroup-candidate-01/base/source'
OUT = ROOT / 'source'
CONTRACT = 'dot16-prefix-booth9-local-v1'
EXPECTED = {
    'VDotDatapath.scala': '1d02d8a34772e7d9b9947f997f32465f3e946f4b24cacc66159eef7ee10ab3bb',
    'VDotElastic.scala': '912c1a038ef8e9a1ac56cfa349161ae1c582d763acfce5352b08ebde2a227f92',
}

HEAP = r'''/** Two unsigned 20-bit carry-save rows encoding signed dot8 + 2^19.
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

'''


def main():
    originals = {name: (BASE/name).read_bytes() for name in EXPECTED}
    for name, data in originals.items():
        assert hashlib.sha256(data).hexdigest() == EXPECTED[name], name
    changed = {name: data.decode('utf-8') for name, data in originals.items()}
    edits = []

    def edit(name, before, after):
        assert changed[name].count(before) == 1, (name, before[:60])
        assert before != after and changed[name].count(after) == 0
        changed[name] = changed[name].replace(before, after, 1)
        edits.append(dict(file=name, before=before, after=after))

    dp = changed['VDotDatapath.scala']
    begin = dp.index('/** Two unsigned carry-save rows')
    end = dp.index('/** Fixed-width modulo sum', begin)
    edit('VDotDatapath.scala', dp[begin:end], HEAP)
    name = 'VDotElastic.scala'
    edit(name,
        '  private val pRows = Reg(Vec(if (dot16Enabled) 2 else 1, Vec(2, UInt(19.W))))',
        '  private val pRows = Reg(Vec(if (dot16Enabled) 2 else 1, Vec(2, UInt(storedResultBits.W))))')
    start = changed[name].index('  // This fixed heap has row0[18]=1')
    end = changed[name].index('  // Fixed-width additions are associative', start)
    edit(name, changed[name][start:end], '''  // Each unsigned 20-bit half encodes signed dot8 + 2^19 modulo 2^20.
  // Feature0 stores only low19, so that bias vanishes. Feature1 stores both
  // full halves; their biases add to 2^20 and vanish in the exact R finish.
  // A disabled high half is biased zero, saved with the accepted request.
  private val rowWords = for {
    half <- 0 until (if (dot16Enabled) 2 else 1)
    row <- 0 until 2
  } yield pRows(half)(row)
  require(rowWords.forall(_.getWidth == storedResultBits), "unsigned rows share the exact sum width")
''')
    edit(name,
        '    pRows(0)(0) := products.io.row0\n    pRows(0)(1) := products.io.row1',
        '    pRows(0)(0) := products.io.row0(storedResultBits - 1, 0)\n    pRows(0)(1) := products.io.row1(storedResultBits - 1, 0)')
    edit(name, '''      // Encode this accepted request's mode before P. Both zero rows decode to
      // zero; no later mode input or extra correction enters the saved result.
      pRows(1)(0) := Mux(isDot16, highProducts.get.io.row0, 0.U(19.W))
      pRows(1)(1) := Mux(isDot16, highProducts.get.io.row1, 0.U(19.W))''', '''      // Both modes save a half with the same +2^19 bias. Dot8 masks all high
      // operand bits by saving biased zero, without a post-P mode or correction.
      pRows(1)(0) := Mux(isDot16, highProducts.get.io.row0, (BigInt(1) << 19).U(20.W))
      pRows(1)(1) := Mux(isDot16, highProducts.get.io.row1, 0.U(20.W))''')
    restored = changed.copy()
    for e in reversed(edits):
        assert restored[e['file']].count(e['after']) == 1
        restored[e['file']] = restored[e['file']].replace(e['after'], e['before'], 1)
    assert all(restored[n].encode() == b for n, b in originals.items())
    OUT.mkdir(parents=True, exist_ok=False)
    for n, text in changed.items():
        (OUT/n).write_bytes(text.encode())
    digest = lambda n: hashlib.sha256(changed[n].encode()).hexdigest()
    proof = dict(contract=CONTRACT, baseline_datapath_sha256=EXPECTED['VDotDatapath.scala'],
        baseline_wrapper_sha256=EXPECTED['VDotElastic.scala'],
        candidate_datapath_sha256=digest('VDotDatapath.scala'),
        candidate_wrapper_sha256=digest('VDotElastic.scala'),
        exact_inverse=True, edits=edits, wrapper_byte_identical=False,
        external_interface_unchanged=True, clock_reset_slot_protocol_unchanged=True,
        old_prefix_finish_source_retained=True, arithmetic_equivalence_verified=False,
        local_fu_tested=False, local_cost_measured=False, parent_tested=False,
        core_tested=False, application_tested=False, production_default_changed=False)
    (OUT/'source-derivation.json').write_text(json.dumps(proof, indent=2, ensure_ascii=False)+'\n')
    diff = ''.join(''.join(difflib.unified_diff(originals[n].decode().splitlines(True),
        changed[n].splitlines(True), fromfile='prefix/'+n, tofile='booth9/'+n)) for n in EXPECTED)
    (OUT/'source.diff').write_text(diff)
    print(json.dumps({k:v for k,v in proof.items() if k!='edits'}, indent=2))


if __name__ == '__main__':
    main()
