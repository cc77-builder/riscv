import chisel3._
import chiseltest._
import org.scalatest.flatspec.AnyFlatSpec
import xiangshan.backend.fu.vector.VdotExec

import scala.collection.mutable
import scala.io.Source
import scala.util.Random
import scala.util.control.NonFatal

class VdotExecSpec extends AnyFlatSpec with ChiselScalatestTester {
  private case class Request(id: String, instruction: BigInt, a: BigInt, b: BigInt,
                             vl: Int, vtype: BigInt, vstart: BigInt, vs: Int,
                             tag: BigInt, expected: BigInt, illegal: Boolean)

  private val vectorFile = sys.env.getOrElse("VDOT_HW_VECTORS",
    throw new IllegalArgumentException("Set VDOT_HW_VECTORS to model-generated vectors.tsv"))
  private val source = Source.fromFile(vectorFile)
  private val vectors = try {
    source.getLines().filterNot(_.startsWith("#")).map { line =>
      val v = line.split("\t")
      require(v.length == 11, s"Malformed vector: $line")
      Request(v(0), BigInt(v(1), 16), BigInt(v(2), 16), BigInt(v(3), 16),
        v(4).toInt, BigInt(v(5), 16), BigInt(v(6), 16), v(7).toInt,
        BigInt(v(8)), BigInt(v(9), 16), v(10) == "1")
    }.toVector
  } finally source.close()
  require(vectors.size == 12022 && vectors.count(_.illegal) == 435,
    "Use the complete standalone hardware corpus")

  private def drive(d: VdotExec, r: Request): Unit = {
    d.io.in.bits.instruction.poke(r.instruction.U)
    d.io.in.bits.src1.poke(r.a.U)
    d.io.in.bits.src2.poke(r.b.U)
    d.io.in.bits.vl.poke(r.vl.U)
    d.io.in.bits.vtype.poke(r.vtype.U)
    d.io.in.bits.vstart.poke(r.vstart.U)
    d.io.in.bits.vs.poke(r.vs.U)
    d.io.in.bits.tag.poke(r.tag.U)
  }

  private def check(d: VdotExec, r: Request): Unit = {
    val context = s"contract=vdot-s8x8-r32-v0.1 id=${r.id} tag=${r.tag} instruction=0x${r.instruction.toString(16)} " +
      s"vd=${(r.instruction >> 7) & 31} vs1=${(r.instruction >> 15) & 31} vs2=${(r.instruction >> 20) & 31} " +
      s"src1_128=0x${r.a.toString(16)} src2_128=0x${r.b.toString(16)} " +
      s"vl=${r.vl} vtype=0x${r.vtype.toString(16)} vstart=0x${r.vstart.toString(16)} vs=${r.vs} " +
      s"expected128=0x${r.expected.toString(16)} actual128=0x${d.io.out.bits.data.peek().litValue.toString(16)}"
    try {
      d.io.pendingTag.valid.expect(true.B)
      d.io.pendingTag.bits.expect(r.tag.U)
      d.io.out.bits.tag.expect(r.tag.U)
      d.io.out.bits.vd.expect(((r.instruction >> 7) & 31).U)
      d.io.out.bits.data.expect(r.expected.U)
      d.io.out.bits.illegal.expect(r.illegal.B)
      d.io.out.bits.cause.expect((if (r.illegal) 2 else 0).U)
      d.io.out.bits.writeEnable.expect((!r.illegal).B)
      d.io.out.bits.setVsDirty.expect((!r.illegal).B)
    } catch {
      // Chiseltest failures need not implement ScalaTest's withClue protocol.
      case NonFatal(error) =>
        println(s"VDOT_HW_DIAGNOSTIC $context")
        throw error
    }
  }

  private def init(d: VdotExec): Unit = {
    d.io.flush.poke(false.B)
    d.io.in.valid.poke(false.B)
    d.io.out.ready.poke(true.B)
    drive(d, vectors.head)
    d.reset.poke(true.B)
    d.clock.step(2)
    d.reset.poke(false.B)
    d.io.out.valid.expect(false.B)
    d.io.pendingTag.valid.expect(false.B)
  }

  behavior of "VdotExec"

  it should "match the independent model and complete an illegal request without writes" in {
    test(new VdotExec()).withAnnotations(Seq(VerilatorBackendAnnotation)) { d =>
      init(d)
      for (i <- vectors.indices) {
        d.io.in.valid.poke(true.B)
        drive(d, vectors(i))
        d.io.in.ready.expect(true.B)
        d.io.out.valid.expect((i > 0).B)
        if (i > 0) check(d, vectors(i - 1))
        d.clock.step()
      }
      d.io.in.valid.poke(false.B)
      d.io.out.valid.expect(true.B)
      check(d, vectors.last)
      d.clock.step()
      d.io.out.valid.expect(false.B)
      println(s"VDOT_HW_MODEL_PASS vectors=${vectors.size} legal=${vectors.count(!_.illegal)} illegal=${vectors.count(_.illegal)}")
    }
  }

  it should "hold all response fields under backpressure and replace only on a handshake" in {
    test(new VdotExec()).withAnnotations(Seq(VerilatorBackendAnnotation)) { d =>
      init(d)
      val first = vectors.find(_.id == "D03").get
      val second = vectors.find(_.id == "X06-VS-off").get
      d.io.out.ready.poke(false.B)
      d.io.in.valid.poke(true.B)
      drive(d, first)
      d.io.in.ready.expect(true.B)
      d.clock.step()
      drive(d, second)
      for (_ <- 0 until 12) {
        d.io.in.ready.expect(false.B)
        d.io.out.valid.expect(true.B)
        check(d, first)
        d.clock.step()
      }
      // Retire the old result and accept a different, illegal request together.
      d.io.out.ready.poke(true.B)
      d.io.in.ready.expect(true.B)
      check(d, first)
      d.clock.step()
      d.io.in.valid.poke(false.B)
      d.io.out.valid.expect(true.B)
      check(d, second)
      d.clock.step()
      d.io.out.valid.expect(false.B)
      println("VDOT_HW_BACKPRESSURE_PASS stall_cycles=12 simultaneous_replace=true")
    }
  }

  it should "give flush priority over both handshakes and reset an occupied slot" in {
    test(new VdotExec()).withAnnotations(Seq(VerilatorBackendAnnotation)) { d =>
      init(d)
      for (ready <- Seq(false, true)) {
        d.io.in.valid.poke(true.B)
        drive(d, vectors(1))
        d.clock.step()
        d.io.out.valid.expect(true.B)
        d.io.out.ready.poke(ready.B)
        drive(d, vectors(2))
        d.io.flush.poke(true.B)
        d.io.in.ready.expect(false.B)
        d.io.out.valid.expect(false.B)
        // The cancellation owner can still identify the pending instruction.
        d.io.pendingTag.valid.expect(true.B)
        d.io.pendingTag.bits.expect(vectors(1).tag.U)
        d.clock.step()
        d.io.flush.poke(false.B)
        d.io.in.valid.poke(false.B)
        d.io.out.ready.poke(true.B)
        d.io.out.valid.expect(false.B)
        d.io.pendingTag.valid.expect(false.B)
        d.clock.step(2)
        d.io.out.valid.expect(false.B)
        // Resubmit a request that was refused on the flush cycle.
        d.io.in.valid.poke(true.B)
        drive(d, vectors(2))
        d.clock.step()
        d.io.in.valid.poke(false.B)
        d.io.out.valid.expect(true.B)
        check(d, vectors(2))
        d.clock.step()
      }
      d.io.in.valid.poke(true.B)
      drive(d, vectors(3))
      d.io.out.ready.poke(false.B)
      d.clock.step()
      d.io.out.valid.expect(true.B)
      d.io.in.valid.poke(false.B)
      d.reset.poke(true.B)
      d.clock.step()
      d.reset.poke(false.B)
      d.io.out.valid.expect(false.B)
      println("VDOT_HW_CANCEL_PASS flush_stalled=true flush_replace=true reset_occupied=true")
    }
  }

  it should "preserve identities with random bubbles, stalls and cancellation" in {
    test(new VdotExec()).withAnnotations(Seq(VerilatorBackendAnnotation)) { d =>
      init(d)
      val random = new Random(0x20261012L)
      val pending = mutable.Queue.empty[Request]
      var offered = Option.empty[Request]
      var accepted = 0
      var returned = 0
      var cancelled = 0
      var stalled = 0
      for (cycle <- 0 until 4000) {
        if (offered.isEmpty && random.nextInt(4) != 0) {
          offered = Some(vectors(random.nextInt(vectors.size)).copy(tag = BigInt(cycle)))
        }
        val flush = random.nextInt(17) == 0
        val ready = random.nextInt(4) != 0
        d.io.flush.poke(flush.B)
        d.io.out.ready.poke(ready.B)
        d.io.in.valid.poke(offered.nonEmpty.B)
        offered.foreach(drive(d, _))
        d.io.pendingTag.valid.expect(pending.nonEmpty.B)
        if (pending.nonEmpty) d.io.pendingTag.bits.expect(pending.front.tag.U)
        d.io.out.valid.expect((pending.nonEmpty && !flush).B)
        val canAccept = !flush && (pending.isEmpty || ready)
        d.io.in.ready.expect(canAccept.B)
        if (flush) {
          cancelled += pending.size
          pending.clear()
          offered = None
        } else {
          if (pending.nonEmpty) {
            check(d, pending.front) // Check stable fields even without out.fire.
            if (ready) { pending.dequeue(); returned += 1 } else stalled += 1
          }
          if (canAccept && offered.nonEmpty) {
            pending.enqueue(offered.get)
            offered = None
            accepted += 1
          }
        }
        d.clock.step()
      }
      d.io.flush.poke(false.B)
      d.io.in.valid.poke(false.B)
      d.io.out.ready.poke(true.B)
      if (pending.nonEmpty) {
        d.io.out.valid.expect(true.B)
        check(d, pending.dequeue())
        returned += 1
        d.clock.step()
      }
      d.io.out.valid.expect(false.B)
      assert(accepted == returned + cancelled, "Request conservation failed")
      assert(cancelled > 0 && stalled > 0 && accepted > 1000, "Missing control coverage")
      println(s"VDOT_HW_SCOREBOARD_PASS cycles=4000 accepted=$accepted returned=$returned cancelled=$cancelled stalled=$stalled")
    }
  }
}
