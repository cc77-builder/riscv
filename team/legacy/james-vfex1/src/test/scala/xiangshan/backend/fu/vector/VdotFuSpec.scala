// Licensed under Mulan PSL v2; see LICENSE at the repository root.
package xiangshan.backend.fu.vector

import chisel3._
import chisel3.util._
import chiseltest._
import org.chipsalliance.cde.config.Parameters
import org.scalatest.flatspec.AnyFlatSpec
import top.MinimalConfig
import xiangshan.{RedirectLevel, XSCoreParamsKey, XSTileKey}
import xiangshan.backend.fu.FuConfig
import xiangshan.backend.fu.wrapper.VdotFu

import scala.util.Random
import scala.util.control.NonFatal

object EmitVdotFu extends App {
  require(args.length == 1, "Usage: EmitVdotFu <target-dir>")
  private val base = new MinimalConfig
  private implicit val p: Parameters = base.alterPartial {
    case XSCoreParamsKey => base(XSTileKey).head
  }
  _root_.circt.stage.ChiselStage.emitSystemVerilogFile(new VdotFu(FuConfig.VdotCfg),
    Array("--target-dir", args(0)), Array("--disable-all-randomization", "--strip-debug-info"))
}

/** Harness instantiates the production FU and real ROB/Redirect types; only the
  * otherwise unused test inputs are tied off. It does not replace core logic.
  */
class VdotFuHarness(implicit p: Parameters) extends Module {
  val dut = Module(new VdotFu(FuConfig.VdotCfg))
  val io = IO(new Bundle {
    val in = Flipped(Decoupled(new Bundle {
      val a = UInt(128.W)
      val b = UInt(128.W)
      val vl = UInt(8.W)
      val shadowVl = UInt(8.W)
      val vtype = UInt(64.W)
      val vstart = UInt(8.W)
      val vm = Bool()
      val op = UInt(8.W)
      val robValue = UInt(6.W)
      val robFlag = Bool()
      val pdest = UInt(8.W)
      val v0 = Bool()
      val debugId = UInt(64.W)
    }))
    val redirect = Input(new Bundle {
      val valid = Bool()
      val value = UInt(6.W)
      val flag = Bool()
      val itself = Bool()
    })
    val out = Decoupled(new Bundle {
      val data = UInt(128.W)
      val illegal = Bool()
      val exceptions = UInt(24.W)
      val robValue = UInt(6.W)
      val robFlag = Bool()
      val pdest = UInt(8.W)
      val vecWen = Bool()
      val v0Wen = Bool()
      val shadowVl = UInt(8.W)
      val debugId = UInt(64.W)
    })
  })
  require(p(XSCoreParamsKey).RobSize == 48)
  require(!FuConfig.VdotCfg.writeVxsat && !FuConfig.VdotCfg.writeVlRf && !FuConfig.VdotCfg.writeFflags)
  require(FuConfig.VdotCfg.getSrcMaxWidthVec == Seq(128, 128, 128, 128, 8))
  dut.io.in.bits := 0.U.asTypeOf(dut.io.in.bits)
  dut.io.in.valid := io.in.valid
  io.in.ready := dut.io.in.ready
  dut.io.in.bits.data.src(0) := io.in.bits.a
  dut.io.in.bits.data.src(1) := io.in.bits.b
  dut.io.in.bits.data.src(2) := Fill(128, 1.U(1.W)) // Old vd must not leak into the result.
  dut.io.in.bits.data.src(3) := 0.U // Mask must not affect unmasked vdot.
  dut.io.in.bits.data.src(4) := io.in.bits.vl
  dut.io.in.bits.ctrl.robIdx.value := io.in.bits.robValue
  dut.io.in.bits.ctrl.robIdx.flag := io.in.bits.robFlag
  dut.io.in.bits.ctrl.pdest := io.in.bits.pdest
  dut.io.in.bits.ctrl.vecWen.get := !io.in.bits.v0
  dut.io.in.bits.ctrl.v0Wen.get := io.in.bits.v0
  dut.io.in.bits.ctrl.fuOpType := io.in.bits.op
  val vec = dut.io.in.bits.ctrl.vpu.get
  vec.vill := io.in.bits.vtype(63)
  vec.vma := io.in.bits.vtype(7)
  vec.vta := io.in.bits.vtype(6)
  vec.vsew := io.in.bits.vtype(4, 3) // Real VPU snapshot carries only two SEW bits.
  vec.vlmul := io.in.bits.vtype(2, 0)
  vec.vstart := io.in.bits.vstart
  vec.vm := io.in.bits.vm
  vec.vl := io.in.bits.shadowVl
  dut.io.in.bits.perfDebugInfo.runahead_checkpoint_id := io.in.bits.debugId
  dut.io.flush.bits := 0.U.asTypeOf(dut.io.flush.bits)
  dut.io.flush.valid := io.redirect.valid
  dut.io.flush.bits.robIdx.value := io.redirect.value
  dut.io.flush.bits.robIdx.flag := io.redirect.flag
  dut.io.flush.bits.level := Mux(io.redirect.itself, RedirectLevel.flush, RedirectLevel.flushAfter)
  io.out.valid := dut.io.out.valid
  dut.io.out.ready := io.out.ready
  io.out.bits.data := dut.io.out.bits.res.data
  io.out.bits.illegal := dut.io.out.bits.ctrl.exceptionVec.get(2)
  io.out.bits.exceptions := dut.io.out.bits.ctrl.exceptionVec.get.asUInt
  io.out.bits.robValue := dut.io.out.bits.ctrl.robIdx.value
  io.out.bits.robFlag := dut.io.out.bits.ctrl.robIdx.flag
  io.out.bits.pdest := dut.io.out.bits.ctrl.pdest
  io.out.bits.vecWen := dut.io.out.bits.ctrl.vecWen.get
  io.out.bits.v0Wen := dut.io.out.bits.ctrl.v0Wen.get
  io.out.bits.shadowVl := dut.io.out.bits.ctrl.vpu.get.vl
  io.out.bits.debugId := dut.io.out.bits.perfDebugInfo.runahead_checkpoint_id
}

class VdotFuSpec extends AnyFlatSpec with ChiselScalatestTester {
  private val base = new MinimalConfig
  private implicit val p: Parameters = base.alterPartial {
    case XSCoreParamsKey => base(XSTileKey).head
  }
  private case class Req(a: BigInt = BigInt("a5" * 8 + "80" * 8, 16),
                         b: BigInt = BigInt("5a" * 8 + "7f" * 8, 16),
                         vl: Int = 8, vt: BigInt = 0, start: Int = 0, vm: Boolean = true, op: Int = 0,
                         ptr: Int = 0, pdest: Int = 1, v0: Boolean = false, id: Int = 1, shadowVl: Int = 255)
  private def drive(d: VdotFuHarness, r: Req): Unit = {
    d.io.in.bits.a.poke(r.a.U); d.io.in.bits.b.poke(r.b.U)
    d.io.in.bits.vl.poke(r.vl.U); d.io.in.bits.shadowVl.poke(r.shadowVl.U)
    d.io.in.bits.vtype.poke(r.vt.U); d.io.in.bits.vstart.poke(r.start.U)
    d.io.in.bits.vm.poke(r.vm.B); d.io.in.bits.op.poke(r.op.U)
    d.io.in.bits.robValue.poke((r.ptr % 48).U); d.io.in.bits.robFlag.poke((r.ptr >= 48).B)
    d.io.in.bits.pdest.poke(r.pdest.U); d.io.in.bits.v0.poke(r.v0.B)
    d.io.in.bits.debugId.poke(r.id.U)
  }
  private def redirect(d: VdotFuHarness, valid: Boolean = false, ptr: Int = 0, itself: Boolean = false): Unit = {
    d.io.redirect.valid.poke(valid.B); d.io.redirect.value.poke((ptr % 48).U)
    d.io.redirect.flag.poke((ptr >= 48).B); d.io.redirect.itself.poke(itself.B)
  }
  private def init(d: VdotFuHarness): Unit = {
    drive(d, Req()); redirect(d)
    d.io.in.valid.poke(false.B); d.io.out.ready.poke(true.B)
    d.reset.poke(true.B); d.clock.step(2); d.reset.poke(false.B)
    d.io.out.valid.expect(false.B)
  }
  private def illegal(r: Req): Boolean = r.vl != 8 || (r.vt & ~BigInt(192)) != 0 || r.start != 0 || !r.vm || r.op != 0
  private def expected(r: Req): BigInt = {
    def signed(x: Int): Int = if (x >= 128) x - 256 else x
    val sum = (0 until 8).map(i => signed(((r.a >> (8 * i)) & 255).toInt) * signed(((r.b >> (8 * i)) & 255).toInt)).sum
    if (illegal(r)) BigInt(0) else BigInt(sum) & BigInt("ffffffff", 16)
  }
  private def check(d: VdotFuHarness, r: Req): Unit = {
    try {
      d.io.out.valid.expect(true.B)
      d.io.out.bits.data.expect(expected(r).U)
      d.io.out.bits.illegal.expect(illegal(r).B)
      d.io.out.bits.exceptions.expect((if (illegal(r)) 4 else 0).U)
      d.io.out.bits.robValue.expect((r.ptr % 48).U); d.io.out.bits.robFlag.expect((r.ptr >= 48).B)
      d.io.out.bits.pdest.expect(r.pdest.U); d.io.out.bits.debugId.expect(r.id.U)
      d.io.out.bits.shadowVl.expect(r.shadowVl.U)
      d.io.out.bits.vecWen.expect((!illegal(r) && !r.v0).B)
      d.io.out.bits.v0Wen.expect((!illegal(r) && r.v0).B)
    } catch {
      case NonFatal(error) =>
        println(s"VDOT_FU_DIAGNOSTIC id=${r.id} ptr=${r.ptr} v0=${r.v0} pdest=${r.pdest} " +
          s"vl=${r.vl} vt=${r.vt} start=${r.start} vm=${r.vm} op=${r.op} " +
          s"src1_128=0x${r.a.toString(16)} src2_128=0x${r.b.toString(16)} " +
          s"expected128=0x${expected(r).toString(16)} actual128=0x${d.io.out.bits.data.peek().litValue.toString(16)}")
        throw error
    }
  }
  // Independent circular position rule, with one flag bit and 48 entries.
  private def killed(ptr: Int, cut: Int, itself: Boolean): Boolean = {
    val distance = (ptr - cut + 96) % 96
    // The existing comparator treats the exactly-full-ring boundary as after.
    // Such a pair is not two simultaneous live instructions in a 48-entry ROB.
    val after = distance > 0 && distance <= 48
    after || (itself && ptr == cut)
  }

  behavior of "VdotFu"
  it should "preserve real metadata, route whole vector/v0 results and complete every configuration rejection" in {
    test(new VdotFuHarness).withAnnotations(Seq(VerilatorBackendAnnotation)) { d =>
      init(d)
      val legal = for (v0 <- Seq(false, true); vt <- Seq(0, 64, 128, 192)) yield Req(vt = vt, v0 = v0)
      val invalid = Seq(Req(vl = 0), Req(vl = 9), Req(vl = 255), Req(vt = BigInt(1) << 63),
        Req(start = 1), Req(start = 255), Req(vm = false), Req(op = 1)) ++
        (0 until 3).map(i => Req(vt = BigInt(1) << i)) ++
        Seq(8, 16, 24).map(sew => Req(vt = sew)) // Representable e16/e32/e64.
      val requests = (legal ++ invalid.flatMap(r => Seq(r, r.copy(v0 = true)))).zipWithIndex.map {
        case (r, i) => r.copy(ptr = i % 96, pdest = 2 + i, id = i + 100)
      }
      for (r <- requests) {
        drive(d, r); d.io.in.valid.poke(true.B); d.io.in.ready.expect(true.B); d.clock.step()
        d.io.in.valid.poke(false.B); d.io.out.ready.poke(false.B)
        drive(d, Req(id = 999, ptr = 70, pdest = 99, shadowVl = 0))
        for (_ <- 0 until 3) { check(d, r); d.clock.step() }
        d.io.out.ready.poke(true.B); check(d, r); d.clock.step(); d.io.out.valid.expect(false.B)
      }
      println(s"VDOT_FU_CONFIG_PASS requests=${requests.size} legal=${requests.count(!illegal(_))} illegal=${requests.count(illegal)} full128=true metadata_stalls=true")
    }
  }

  it should "select pending and incoming cancellation by actual ROB age, wrap and redirect level" in {
    test(new VdotFuHarness).withAnnotations(Seq(VerilatorBackendAnnotation)) { d =>
      init(d)
      var pendingChecks = 0
      var incomingChecks = 0
      for (ptr <- 0 until 96; cut <- 0 until 96; itself <- Seq(false, true)) {
        val r = Req(ptr = ptr, id = 10000 + pendingChecks, v0 = ptr % 2 == 0)
        redirect(d); drive(d, r); d.io.in.valid.poke(true.B); d.io.in.ready.expect(true.B); d.clock.step()
        d.io.in.valid.poke(false.B); d.io.out.ready.poke(false.B); redirect(d, true, cut, itself)
        d.io.out.valid.expect((!killed(ptr, cut, itself)).B)
        if (!killed(ptr, cut, itself)) check(d, r)
        d.clock.step(); redirect(d); d.io.out.ready.poke(true.B)
        if (!killed(ptr, cut, itself)) check(d, r) else d.io.out.valid.expect(false.B)
        d.clock.step(); d.io.out.valid.expect(false.B); pendingChecks += 1
        // A squashed incoming request must never enter an empty executor slot.
        drive(d, r); d.io.in.valid.poke(true.B); redirect(d, true, cut, itself)
        d.io.in.ready.expect((!killed(ptr, cut, itself)).B); d.clock.step()
        d.io.in.valid.poke(false.B); redirect(d)
        if (!killed(ptr, cut, itself)) check(d, r) else d.io.out.valid.expect(false.B)
        d.clock.step(); incomingChecks += 1
      }
      println(s"VDOT_FU_AGE_PASS pending=$pendingChecks incoming=$incomingChecks rob_entries=48 wrap=true flush_itself=true")
    }
  }

  it should "conserve request identity under randomized stalls, simultaneous replacement, selective cancellation and reset" in {
    test(new VdotFuHarness).withAnnotations(Seq(VerilatorBackendAnnotation)) { d =>
      init(d)
      val rng = new Random(0x06072026L)
      var pending = Option.empty[Req]
      var accepted = 0; var returned = 0; var cancelled = 0; var stalls = 0; var replacements = 0; var resets = 0
      for (cycle <- 0 until 4000) {
        val r = Req(a = BigInt(128, rng), b = BigInt(128, rng), ptr = rng.nextInt(96),
          pdest = 1 + rng.nextInt(100), id = cycle + 1, v0 = rng.nextBoolean(),
          vl = if (rng.nextInt(5) == 0) 9 else 8, vt = Seq(0, 64, 128, 192)(rng.nextInt(4)))
        val inputValid = rng.nextInt(4) != 0; val outputReady = rng.nextInt(3) != 0
        val cutValid = rng.nextInt(12) == 0; val cut = rng.nextInt(96); val itself = rng.nextBoolean()
        drive(d, r); d.io.in.valid.poke(inputValid.B); d.io.out.ready.poke(outputReady.B)
        redirect(d, cutValid, cut, itself)
        val drop = pending.exists(x => cutValid && killed(x.ptr, cut, itself))
        val incomingDrop = cutValid && killed(r.ptr, cut, itself)
        val ready = !drop && !incomingDrop && (pending.isEmpty || outputReady)
        d.io.in.ready.expect(ready.B); d.io.out.valid.expect((pending.nonEmpty && !drop).B)
        if (pending.nonEmpty && !drop) check(d, pending.get)
        val outFire = pending.nonEmpty && !drop && outputReady
        val inFire = inputValid && ready
        if (drop) { cancelled += 1; pending = None }
        if (outFire) { returned += 1; pending = None }
        if (inFire) { accepted += 1; pending = Some(r) }
        if (outFire && inFire) replacements += 1
        if (pending.nonEmpty && !outputReady) stalls += 1
        d.clock.step()
        // Reset occupied metadata/result together, separately counted as cancellation.
        if (cycle % 997 == 996 && pending.nonEmpty) {
          cancelled += 1; resets += 1; pending = None
          d.reset.poke(true.B); d.clock.step(); d.reset.poke(false.B); d.io.out.valid.expect(false.B)
        }
      }
      redirect(d); d.io.in.valid.poke(false.B); d.io.out.ready.poke(true.B)
      pending.foreach { r => check(d, r); returned += 1 }; d.clock.step(); d.io.out.valid.expect(false.B)
      assert(accepted == returned + cancelled && cancelled > 0 && stalls > 0 && replacements > 0 && resets > 0)
      println(s"VDOT_FU_SCOREBOARD_PASS cycles=4000 accepted=$accepted returned=$returned cancelled=$cancelled stalled=$stalls replaced=$replacements resets=$resets")
    }
  }
}
