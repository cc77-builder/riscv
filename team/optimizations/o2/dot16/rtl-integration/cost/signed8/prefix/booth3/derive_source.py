#!/usr/bin/env python3
"""Prepare one three-row Booth P/R boundary from the frozen two-row point."""
from pathlib import Path
import ast
import difflib
import hashlib
import json

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / 'prefix-booth-candidate-01'
CONTRACT = 'dot16-prefix-booth3-local-v1'
EXPECTED = {'VDotDatapath.scala': 'f0a8bbe58440c6113aa56f848387c6b4e4a487d71ec2832a1e43fca55d3a8245',
            'VDotElastic.scala': '0fcc5df10355ee1e6382678ba40bc9d7ddf830b560dcc469c46e6a6888441556'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    original = {n: (BASE/'source'/n).read_bytes() for n in EXPECTED}
    assert all(digest(original[n]) == h for n, h in EXPECTED.items())
    prior = json.loads((BASE/'source/source-derivation.json').read_bytes())
    assert digest((BASE/'source/source-derivation.json').read_bytes()) == '72b19ecbc899c0175c86a31e1032607b65897999c17117e2de21f21fac7c7eae'
    texts = {n: b.decode() for n, b in original.items()}
    edits = []

    def edit(name, before, after):
        assert before != after and texts[name].count(before) == 1, (name, before)
        assert texts[name].count(after) == 0, (name, after)
        texts[name] = texts[name].replace(before, after, 1)
        edits.append(dict(file=name, before=before, after=after))

    name = 'VDotDatapath.scala'
    edit(name, '/** Two unsigned 20-bit carry-save rows encoding signed dot8 + 2^19.',
         '/** Three unsigned 20-bit carry-save rows encoding signed dot8 + 2^19.')
    edit(name, '    val row1 = Output(UInt(20.W))',
         '    val row1 = Output(UInt(20.W))\n    val row2 = Output(UInt(20.W))')
    edit(name, '      "  output wire [19:0] row1",',
         '      "  output wire [19:0] row1,",\n      "  output wire [19:0] row2",')
    edit(name, 'Seq(28, 19, 13, 9, 6, 4, 3, 2).zipWithIndex',
         'Seq(28, 19, 13, 9, 6, 4, 3).zipWithIndex')
    edit(name, '    require(columns.forall(_.size <= 2), "exactly two final rows")\n    for (row <- 0 until 2) {',
         '    require(columns.forall(_.size <= 3), "at most three final rows")\n    for (row <- 0 until 3) {')
    begin = texts[name].index('/** Fixed-width modulo sum')
    end = texts[name].index('    wire("p0", "x ^ y")', begin)
    prefix = texts[name][begin:end]
    replacement = '''/** Fixed-width modulo sum of three/six saved carry-save rows. No state or clock.
  * Each half first compresses three rows to two. W20 combines its four remaining
  * rows using two further CSA layers; W19 directly uses its compressed pair.
  * The fixed parallel prefix network after that pair is byte-for-byte retained.
  */
class VDotPrefixFinish(val width: Int, val rowCount: Int)
  extends BlackBox with HasBlackBoxInline {
  require((width == 19 && rowCount == 3) || (width == 20 && rowCount == 6))
  override def desiredName: String = s"VDotPrefixFinish$width"
  val io = IO(new Bundle {
    val rows = Input(Vec(rowCount, UInt(width.W)))
    val result = Output(UInt(width.W))
  })
  setInline(s"VDotPrefixFinish$width.sv", VDotPrefixFinish.inlineText(width, rowCount))
}

object VDotPrefixFinish {
  def inlineText(width: Int, rowCount: Int): String = {
    require((width == 19 && rowCount == 3) || (width == 20 && rowCount == 6))
    val lines = scala.collection.mutable.ArrayBuffer[String](s"module VDotPrefixFinish$width(")
    for (row <- 0 until rowCount) lines += s"  input wire [${width - 1}:0] rows_$row,"
    lines += s"  output wire [${width - 1}:0] result"
    lines += ");"
    def wire(name: String, expression: String): Unit = {
      lines += s"  wire [${width - 1}:0] $name;"
      lines += s"  assign $name = $expression;"
    }
    wire("low_sum", "rows_0 ^ rows_1 ^ rows_2")
    wire("low_raw", "(rows_0 & rows_1) | ((rows_0 ^ rows_1) & rows_2)")
    wire("low_carry", s"{low_raw[${width - 2}:0], 1'b0}")
    if (rowCount == 6) {
      wire("high_sum", "rows_3 ^ rows_4 ^ rows_5")
      wire("high_raw", "(rows_3 & rows_4) | ((rows_3 ^ rows_4) & rows_5)")
      wire("high_carry", s"{high_raw[${width - 2}:0], 1'b0}")
      wire("cs0_sum", "low_sum ^ low_carry ^ high_sum")
      wire("cs0_raw", "(low_sum & low_carry) | ((low_sum ^ low_carry) & high_sum)")
      wire("cs0_carry", s"{cs0_raw[${width - 2}:0], 1'b0}")
      wire("x", "cs0_sum ^ cs0_carry ^ high_carry")
      wire("cs1_raw", "(cs0_sum & cs0_carry) | ((cs0_sum ^ cs0_carry) & high_carry)")
      wire("y", s"{cs1_raw[${width - 2}:0], 1'b0}")
    } else {
      wire("x", "low_sum")
      wire("y", "low_carry")
    }
'''
    edit(name, prefix, replacement)
    name = 'VDotElastic.scala'
    edit(name, '  private val pRows = Reg(Vec(if (dot16Enabled) 2 else 1, Vec(2, UInt(storedResultBits.W))))',
         '  private val pRows = Reg(Vec(if (dot16Enabled) 2 else 1, Vec(3, UInt(storedResultBits.W))))')
    edit(name, '    row <- 0 until 2', '    row <- 0 until 3')
    edit(name, '  private val prefixSum = Module(new VDotPrefixFinish(storedResultBits, if (dot16Enabled) 4 else 2))',
         '  private val prefixSum = Module(new VDotPrefixFinish(storedResultBits, if (dot16Enabled) 6 else 3))')
    edit(name, '    pRows(0)(1) := products.io.row1(storedResultBits - 1, 0)',
         '    pRows(0)(1) := products.io.row1(storedResultBits - 1, 0)\n    pRows(0)(2) := products.io.row2(storedResultBits - 1, 0)')
    edit(name, '      pRows(1)(1) := Mux(isDot16, highProducts.get.io.row1, 0.U(20.W))',
         '      pRows(1)(1) := Mux(isDot16, highProducts.get.io.row1, 0.U(20.W))\n      pRows(1)(2) := Mux(isDot16, highProducts.get.io.row2, 0.U(20.W))')
    restored = texts.copy()
    for e in reversed(edits):
        assert restored[e['file']].count(e['after']) == 1
        restored[e['file']] = restored[e['file']].replace(e['after'], e['before'], 1)
    assert all(restored[n].encode() == original[n] for n in original)
    combined = prior['edits'] + edits
    restored = texts.copy()
    for e in reversed(combined):
        assert restored[e['file']].count(e['after']) == 1
        restored[e['file']] = restored[e['file']].replace(e['after'], e['before'], 1)
    assert digest(restored['VDotDatapath.scala'].encode()) == prior['baseline_datapath_sha256']
    assert digest(restored['VDotElastic.scala'].encode()) == prior['baseline_wrapper_sha256']
    proof = dict(contract=CONTRACT, baseline_datapath_sha256=prior['baseline_datapath_sha256'],
        baseline_wrapper_sha256=prior['baseline_wrapper_sha256'],
        intermediate_datapath_sha256=EXPECTED['VDotDatapath.scala'],
        intermediate_wrapper_sha256=EXPECTED['VDotElastic.scala'],
        candidate_datapath_sha256=digest(texts['VDotDatapath.scala'].encode()),
        candidate_wrapper_sha256=digest(texts['VDotElastic.scala'].encode()),
        exact_inverse=True, edits=combined, new_edits=len(edits), wrapper_byte_identical=False,
        external_interface_unchanged=True, clock_reset_slot_protocol_unchanged=True,
        old_prefix_finish_source_retained=False, old_prefix_network_suffix_retained=True,
        fresh_three_six_row_unconstrained_proofs_required=True,
        p_rows_per_half=3, p_bits_feature0=57, p_bits_feature1=120,
        latency_unstalled_cycles=2, initiation_interval_cycles=1,
        arithmetic_equivalence_verified=False, local_fu_tested=False, local_cost_measured=False,
        parent_tested=False, core_tested=False, application_tested=False, production_default_changed=False)
    out = ROOT/'source'; out.mkdir(parents=True, exist_ok=False)
    for n,t in texts.items(): (out/n).write_bytes(t.encode())
    (out/'source-derivation.json').write_text(json.dumps(proof,indent=2)+'\n')
    (out/'source.diff').write_text(''.join(''.join(difflib.unified_diff(original[n].decode().splitlines(True),
        texts[n].splitlines(True),fromfile='booth2/'+n,tofile='booth3/'+n)) for n in original))

    checker=(BASE/'controller/verify_booth.py').read_bytes()
    assert digest(checker)=='b3044e637a5f312b71497de1eaa44503e27894cb7fd313ee389208a8fc351dc5'
    text=checker.decode(); vedits=[]
    def ve(before, after, count=1):
        nonlocal text
        assert text.count(before)==count, (before, text.count(before))
        text=text.replace(before,after); vedits.append(dict(before=before,after=after,count=count))
    ve('and two explicit 20-bit concatenations.', 'and three explicit 20-bit concatenations.')
    ve('output wire [19:0] row0, output wire [19:0] row1',
       'output wire [19:0] row0, output wire [19:0] row1, output wire [19:0] row2')
    ve("{'row0', 'row1'}", "{'row0', 'row1', 'row2'}")
    ve("{'vs1', 'vs2', 'row0', 'row1'}", "{'vs1', 'vs2', 'row0', 'row1', 'row2'}")
    ve("for name in ('row0','row1'):", "for name in ('row0','row1','row2'):")
    ve('BOOTH_CSA_STRUCTURAL_EQUIVALENCE_PASS','BOOTH3_CSA_STRUCTURAL_EQUIVALENCE_PASS')
    ve('BOOTH_CSA_STRUCTURAL_EQUIVALENCE_REJECTED','BOOTH3_CSA_STRUCTURAL_EQUIVALENCE_REJECTED')
    ve('(row0+row1)', '(row0+row1+row2)', 2)
    ast.parse(text)
    inverse=text
    for e in reversed(vedits):
        assert inverse.count(e['after'])==e['count']
        inverse=inverse.replace(e['after'],e['before'])
    assert inverse.encode()==checker
    cout=ROOT/'controller';cout.mkdir(exist_ok=False)
    (cout/'verify_booth.py').write_text(text)
    (cout/'verifier-derivation.json').write_text(json.dumps(dict(baseline_sha256=digest(checker),
        candidate_sha256=digest(text.encode()),exact_inverse=True,edits=vedits),indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='edits'},indent=2))
    print('checker',digest(text.encode()),'source-proof',digest((out/'source-derivation.json').read_bytes()))


if __name__=='__main__':main()
