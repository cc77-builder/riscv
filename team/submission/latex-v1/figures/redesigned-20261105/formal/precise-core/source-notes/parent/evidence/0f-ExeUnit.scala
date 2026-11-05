/***************************************************************************************
* Copyright (c) 2020-2021 Institute of Computing Technology, Chinese Academy of Sciences
* Copyright (c) 2020-2021 Peng Cheng Laboratory
*
* XiangShan is licensed under Mulan PSL v2.
* You can use this software according to the terms and conditions of the Mulan PSL v2.
* You may obtain a copy of Mulan PSL v2 at:
*          http://license.coscl.org.cn/MulanPSL2
*
* THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
* EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
* MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
*
* See the Mulan PSL v2 for more details.
***************************************************************************************/

package xiangshan.backend.exu

import org.chipsalliance.cde.config.Parameters
import chisel3._
import chisel3.experimental.hierarchy.{Definition, instantiable}
import chisel3.util._
import chisel3.util.experimental.BoringUtils.tapAndRead
import freechips.rocketchip.diplomacy.{LazyModule, LazyModuleImp}
import utility._
import xiangshan.backend.fu.{CSRFileIO, FenceIO, FuncUnitInput}
import xiangshan.backend.Bundles.{ExuInput, ExuOutput, MemExuInput, MemExuOutput}
import xiangshan.{AddrTransType, FPUCtrlSignals, HasXSParameter, Redirect, XSBundle, XSModule}
import xiangshan.backend.datapath.WbConfig.{PregWB, _}
import xiangshan.backend.fu.FuType
import xiangshan.backend.fu.vector.Bundles.{VType, Vxrm}
import xiangshan.backend.fu.fpu.Bundles.Frm
import xiangshan.backend.fu.wrapper.{CSRInput, CSRToDecode}

class ExeUnitIO(params: ExeUnitParams)(implicit p: Parameters) extends XSBundle {
  val flush = Flipped(ValidIO(new Redirect()))
  val in = Flipped(DecoupledIO(new ExuInput(params, hasCopySrc = true)))
  val out = DecoupledIO(new ExuOutput(params))
  val csrin = Option.when(params.hasCSR)(new CSRInput)
  val csrio = Option.when(params.hasCSR)(new CSRFileIO)
  val csrToDecode = Option.when(params.hasCSR)(Output(new CSRToDecode))
  val fenceio = Option.when(params.hasFence)(new FenceIO)
  val frm = Option.when(params.needSrcFrm)(Input(Frm()))
  val vxrm = Option.when(params.needSrcVxrm)(Input(Vxrm()))
  val vtype = Option.when(params.writeVConfig)((Valid(new VType)))
  val vlIsZero = Option.when(params.writeVConfig)(Output(Bool()))
  val vlIsVlmax = Option.when(params.writeVConfig)(Output(Bool()))
  val instrAddrTransType = Option.when(params.hasJmpFu || params.hasBrhFu)(Input(new AddrTransType))
}

class ExeUnit(val exuParams: ExeUnitParams)(implicit p: Parameters) extends LazyModule {
  override def shouldBeInlined: Boolean = false

  lazy val module = new ExeUnitImp(this)(p, exuParams)
}

class ExeUnitImp(
  override val wrapper: ExeUnit
)(implicit
  p: Parameters, exuParams: ExeUnitParams
) extends LazyModuleImp(wrapper) with HasXSParameter with HasCriticalErrors {
  private val fuCfgs = exuParams.fuConfigs
  // Keep all other EXUs and both old vdot modes on the original Scala branch.
  private val vdotHandoff = fuCfgs.exists(_.fuType == FuType.vdot) &&
    xiangshan.backend.fu.wrapper.VDotHandoff.enabled
  private val vdotElastic = fuCfgs.exists(_.fuType == FuType.vdot) &&
    xiangshan.backend.fu.wrapper.VDotO2.enabled
  if (vdotElastic) {
    require(exuParams.name == "VFEX4" && !exuParams.latencyCertain,
      "O2 elastic dispatch is restricted to the current uncertain-latency VFEX4")
    require(fuCfgs.size == 3 && fuCfgs.map(_.fuType).toSet == Set(FuType.vdot, FuType.vidiv, FuType.vfdiv),
      "O2 requires exactly VDot, VIDiv and VFDivSqrt")
    require(!xiangshan.backend.fu.wrapper.VDotHandoff.traceEnabled,
      "O2 requires its own observer; the single-outstanding O1 observer is unsupported")
  }

  val io = IO(new ExeUnitIO(exuParams))

  val funcUnits = fuCfgs.map(cfg => {
    assert(cfg.fuGen != null, cfg.name + "Cfg'fuGen is null !!!")
    val module = cfg.fuGen(p, cfg)
    module
  })

  private val elasticVDot = if (vdotElastic) {
    Some(funcUnits(fuCfgs.indexWhere(_.fuType == FuType.vdot))
      .asInstanceOf[xiangshan.backend.fu.wrapper.VDotElastic])
  } else None
  private val elasticVDotOccupied = elasticVDot.map { fu =>
    fu.pipelineStatus.pValid || fu.pipelineStatus.rValid
  }
  // Only O2 DIV owns this single ROB identity; VDot retains its P/R occupancy gate.
  private val elasticDivCancelled = if (vdotElastic) Some(WireDefault(false.B)) else None

  if (EnableClockGate) {
    fuCfgs.zip(funcUnits).foreach { case (cfg, fu) =>
      val clk_en = WireInit(false.B)
      val fuVld_en = WireInit(false.B)
      val fuVld_en_reg = RegInit(false.B)
      val uncer_en_reg = RegInit(false.B)

      def latReal: Int = cfg.latency.latencyVal.getOrElse(0)
      def extralat: Int = cfg.latency.extraLatencyVal.getOrElse(0)

      val uncerLat = cfg.latency.uncertainEnable.nonEmpty
      val lat0 = (latReal == 0 && !uncerLat).asBool
      val latN = (latReal >  0 && !uncerLat).asBool

      val fuVldVec = (fu.io.in.valid && latN) +: Seq.fill(latReal)(RegInit(false.B))
      val fuRdyVec = Seq.fill(latReal)(Wire(Bool())) :+ fu.io.out.ready

      for (i <- 0 until latReal) {
        fuRdyVec(i) := !fuVldVec(i + 1) || fuRdyVec(i + 1)
      }

      for (i <- 1 to latReal) {
        when(fuRdyVec(i - 1) && fuVldVec(i - 1)) {
          fuVldVec(i) := fuVldVec(i - 1)
        }.elsewhen(fuRdyVec(i)) {
          fuVldVec(i) := false.B
        }
      }
      fuVld_en := fuVldVec.map(v => v).reduce(_ || _)
      fuVld_en_reg := fuVld_en

      val releaseUncertain = if (vdotElastic &&
        (cfg.fuType == FuType.vidiv || cfg.fuType == FuType.vfdiv)) {
        // The old hold bit still supplies the cancellation edge. Clear it for
        // the following idle cycle; unrelated redirects must keep DIV running.
        fu.io.out.fire || elasticDivCancelled.get
      } else fu.io.out.fire
      when(uncerLat.asBool && fu.io.in.fire) {
        uncer_en_reg := true.B
      }.elsewhen(uncerLat.asBool && releaseUncertain) {
        uncer_en_reg := false.B
      }

      when(lat0 && fu.io.in.fire) {
        clk_en := true.B
      }.elsewhen(latN && fuVld_en || fuVld_en_reg) {
        clk_en := true.B
      }.elsewhen(uncerLat.asBool && fu.io.in.fire || uncer_en_reg) {
        clk_en := true.B
      }

      if (vdotElastic && cfg.fuType == FuType.vdot) {
        // These are actual, unmasked slot registers. Keep the clearing edge
        // even when this cycle's redirect kills every slot. Reset also opens
        // an empty, previously gated FU without relying on clock-test enable.
        clk_en := elasticVDotOccupied.get || fu.io.in.fire || reset.asBool
      }

      if (cfg.ckAlwaysEn) {
        clk_en := true.B
      }

      if (latReal != 0 || uncerLat) {
        fu.clock := ClockGate(ClockGate.genTeSink.cgen, clk_en, clock)
      }
      XSPerfAccumulate(s"clock_gate_en_${fu.cfg.name}", clk_en)
    }
  }

  // Only DIV uses a single transaction/ROB register in O2. A vdot response
  // or redirect cannot release another vdot still held by the other slot.
  private val elasticDivOccupied = if (vdotElastic) {
    val divUnits = funcUnits.filter(_.cfg.fuType != FuType.vdot)
    val divBusy = RegInit(false.B)
    val divAccept = io.in.fire && io.in.bits.fuType =/= FuType.vdot.U
    val divRobIdx = RegEnable(io.in.bits.robIdx, divAccept)
    val divOutValid = divUnits.map(_.io.out.valid).reduce(_ || _)
    val divOutFire = divUnits.map(_.io.out.fire).reduce(_ || _)
    val divReady = divUnits.map(_.io.in.ready).reduce(_ && _)
    val divCancelled = divBusy && divRobIdx.needFlush(io.flush)
    elasticDivCancelled.get := divCancelled
    when(divCancelled) {
      divBusy := false.B
    }.elsewhen(divOutFire) {
      divBusy := false.B
    }.elsewhen(divAccept) {
      divBusy := true.B
    }
    // Existing DIV cancellation need not withdraw out.valid combinationally.
    // Wait for the physical output to disappear and the actual DIVs to return
    // ready; neither cancellation nor completion permits same-cycle switching.
    Some(divBusy || divOutValid || !divReady)
  } else None

  val busy = if (vdotElastic) {
    WireDefault(elasticVDotOccupied.get || elasticDivOccupied.get)
  } else RegInit(false.B)
  if (vdotElastic) {
    // busy is derived from the real two-slot state plus independent DIV state.
  } else if (exuParams.latencyCertain){
    busy := false.B
  }
  else {
    val robIdx = RegEnable(io.in.bits.robIdx, io.in.fire)
    if (vdotHandoff) {
      when(io.in.fire && io.in.bits.robIdx.needFlush(io.flush)) {
        busy := false.B
      }.elsewhen(busy && robIdx.needFlush(io.flush)) {
        busy := false.B
      }.elsewhen(io.in.fire) {
        // A response and a new request can coincide: the NEW request remains busy.
        busy := true.B
      }.elsewhen(io.out.fire) {
        busy := false.B
      }
    } else {
      when(io.in.fire && io.in.bits.robIdx.needFlush(io.flush)) {
        busy := false.B
      }.elsewhen(busy && robIdx.needFlush(io.flush)) {
        busy := false.B
      }.elsewhen(io.out.fire) {
        busy := false.B
      }.elsewhen(io.in.fire) {
        busy := true.B
      }
    }
  }

  exuParams.wbPortConfigs.map{
    x => x match {
      case IntWB(port, priority) => assert(priority >= 0 && priority <= 2,
        s"${exuParams.name}: WbPort must priority=0 or priority=1")
      case FpWB(port, priority) => assert(priority >= 0 && priority <= 2,
        s"${exuParams.name}: WbPort must priority=0 or priority=1")
      case VfWB (port, priority) => assert(priority >= 0 && priority <= 2,
        s"${exuParams.name}: WbPort must priority=0 or priority=1")
      case _ =>
    }
  }
  val intWbPort = exuParams.getIntWBPort
  if (intWbPort.isDefined){
    val sameIntPortExuParam = backendParams.allExuParams.filter(_.getIntWBPort.isDefined)
      .filter(_.getIntWBPort.get.port == intWbPort.get.port)
    val samePortOneCertainOneUncertain = sameIntPortExuParam.map(_.latencyCertain).contains(true) && sameIntPortExuParam.map(_.latencyCertain).contains(false)
    if (samePortOneCertainOneUncertain) sameIntPortExuParam.map(samePort =>
      samePort.wbPortConfigs.map(
        x => x match {
          case IntWB(port, priority) => {
            if (!samePort.latencyCertain) assert(priority == sameIntPortExuParam.size - 1,
              s"${samePort.name}: IntWbPort $port must latencyCertain priority=0 or latencyUnCertain priority=max(${sameIntPortExuParam.size - 1})")
            // Certain latency can be handled by WbBusyTable, so there is no need to limit the exu's WB priority
          }
          case _ =>
        }
      )
    )
  }
  val fpWbPort = exuParams.getFpWBPort
  if (fpWbPort.isDefined) {
    val sameFpPortExuParam = backendParams.allExuParams.filter(_.getFpWBPort.isDefined)
      .filter(_.getFpWBPort.get.port == fpWbPort.get.port)
    val samePortOneCertainOneUncertain = sameFpPortExuParam.map(_.latencyCertain).contains(true) && sameFpPortExuParam.map(_.latencyCertain).contains(false)
    if (samePortOneCertainOneUncertain) sameFpPortExuParam.map(samePort =>
      samePort.wbPortConfigs.map(
        x => x match {
          case FpWB(port, priority) => {
            if (!samePort.latencyCertain) assert(priority == sameFpPortExuParam.size - 1,
              s"${samePort.name}: FpWbPort $port must latencyCertain priority=0 or latencyUnCertain priority=max(${sameFpPortExuParam.size - 1})")
            // Certain latency can be handled by WbBusyTable, so there is no need to limit the exu's WB priority
          }
          case _ =>
        }
      )
    )
  }
  val vfWbPort = exuParams.getVfWBPort
  if (vfWbPort.isDefined) {
    val sameVfPortExuParam = backendParams.allExuParams.filter(_.getVfWBPort.isDefined)
      .filter(_.getVfWBPort.get.port == vfWbPort.get.port)
    val samePortOneCertainOneUncertain = sameVfPortExuParam.map(_.latencyCertain).contains(true) && sameVfPortExuParam.map(_.latencyCertain).contains(false)
    if (samePortOneCertainOneUncertain)  sameVfPortExuParam.map(samePort =>
      samePort.wbPortConfigs.map(
        x => x match {
          case VfWB(port, priority) => {
            if (!samePort.latencyCertain) assert(priority == sameVfPortExuParam.size - 1,
              s"${samePort.name}: VfWbPort $port must latencyCertain priority=0 or latencyUnCertain priority=max(${sameVfPortExuParam.size - 1})")
            // Certain latency can be handled by WbBusyTable, so there is no need to limit the exu's WB priority
          }
          case _ =>
        }
      )
    )
  }
  if(backendParams.debugEn) {
    dontTouch(io.out.ready)
  }
  // rob flush --> funcUnits
  funcUnits.zipWithIndex.foreach { case (fu, i) =>
    fu.io.flush <> io.flush
  }

  def acceptCond(input: ExuInput): Seq[Bool] = {
    input.params.fuConfigs.map(_.fuSel(input))
  }

  val dispatchedInputs = if (vdotElastic) {
    // Local selected-ready dispatch: the generic Dispatcher ANDs every ready,
    // while each valid is independent of that AND. Reusing it here could let
    // a child accept without the parent accepting when another FU is busy.
    val sources = Wire(Vec(funcUnits.length, DecoupledIO(new ExuInput(exuParams))))
    val selected = VecInit(acceptCond(io.in.bits))
    val newIsVDot = io.in.bits.fuType === FuType.vdot.U
    val allowInput = !elasticDivOccupied.get &&
      (newIsVDot || !elasticVDotOccupied.get) &&
      !io.flush.valid && !reset.asBool
    val selectedReady = Mux1H(selected, funcUnits.map(_.io.in.ready))
    io.in.ready := allowInput && selectedReady
    sources.zipWithIndex.foreach { case (source, i) =>
      source.bits := io.in.bits
      source.valid := io.in.valid && allowInput && selected(i)
    }
    when(io.in.valid && !reset.asBool) {
      assert(PopCount(selected) === 1.U, "O2 input must select exactly one VFEX4 FU")
    }
    val childFires = funcUnits.map(_.io.in.fire)
    assert(io.in.fire === childFires.reduce(_ || _),
      "O2 parent and selected child acceptance disagree")
    assert(PopCount(childFires) <= 1.U, "O2 dispatched one request to multiple FUs")
    childFires.zipWithIndex.foreach { case (fire, i) =>
      when(fire) {
        assert(io.in.fire && selected(i), "O2 unselected child accepted a request")
      }
    }
    when(io.in.fire && !newIsVDot) {
      assert(!elasticVDotOccupied.get && !elasticDivOccupied.get,
        "O2 switched to DIV before the previous FU drained")
    }
    assert(PopCount(funcUnits.map(_.io.out.valid)) <= 1.U,
      "O2 VFEX4 output must remain one-hot")
    sources
  } else {
    val in1ToN = Module(new Dispatcher(new ExuInput(exuParams), funcUnits.length, acceptCond))

    // ExeUnit.in <---> Dispatcher.in
    if (vdotHandoff) {
      require(exuParams.name == "VFEX4" && !exuParams.latencyCertain,
        "O1 handoff is restricted to the current uncertain-latency VFEX4")
      require(fuCfgs.count(_.fuType == FuType.vdot) == 1)
      val vdotIndex = fuCfgs.indexWhere(_.fuType == FuType.vdot)
      val vdotFu = funcUnits(vdotIndex)
      val activeIsVDot = RegInit(false.B)
      when(io.in.fire) { activeIsVDot := io.in.bits.fuType === FuType.vdot.U }
      val newIsVDot = io.in.bits.fuType === FuType.vdot.U
      // The shared output remains one-hot; neither div->vdot nor vdot->div overlaps.
      val handoff = busy && activeIsVDot && newIsVDot && vdotFu.io.out.valid && io.out.ready &&
        !io.flush.valid && !reset.asBool
      val allowInput = (!busy || handoff) && !io.flush.valid && !reset.asBool
      in1ToN.io.in.valid := io.in.valid && allowInput
      in1ToN.io.in.bits := io.in.bits
      io.in.ready := allowInput && in1ToN.io.in.ready
      when(io.in.fire && busy) {
        assert(handoff && vdotFu.io.out.fire && io.out.fire,
          "O1 accepted into a busy EXU without retiring the old vdot response")
      }
      // Dispatcher ANDs every FU's ready; detect any parent/selected-FU mismatch.
      assert(vdotFu.io.in.fire === (io.in.fire && newIsVDot))
    } else {
      in1ToN.io.in.valid := io.in.valid && !busy
      in1ToN.io.in.bits := io.in.bits
      io.in.ready := !busy && in1ToN.io.in.ready
    }
    in1ToN.io.out
  }

  if (sys.env.get("VDOT_T12_TRACE").contains("1") && fuCfgs.contains(xiangshan.backend.fu.FuConfig.VDotCfg)) {
    // Instantiate outside when: GTimer is a local register, not a global read.
    require(!p(xiangshan.DebugOptionsKey).ResetGen, "T12 trace requires the common simulation reset")
    val t12Cycle = GTimer()
    when(io.in.fire) {
      printf(p"T12_VFEX4_ACCEPT cycle=${t12Cycle} rob=${io.in.bits.robIdx.flag}:${io.in.bits.robIdx.value} fu=0x${Hexadecimal(io.in.bits.fuType)}\n")
    }
    when(io.in.valid && !io.in.ready) {
      printf(p"T12_VFEX4_WAIT cycle=${t12Cycle} rob=${io.in.bits.robIdx.flag}:${io.in.bits.robIdx.value} fu=0x${Hexadecimal(io.in.bits.fuType)} busy=${busy}\n")
    }
  }

  if (xiangshan.backend.fu.wrapper.VDotHandoff.traceEnabled &&
      fuCfgs.contains(xiangshan.backend.fu.FuConfig.VDotCfg)) {
    require(exuParams.name == "VFEX4" && !exuParams.latencyCertain,
      "O1 trace requires the current uncertain-latency VFEX4")
    require(!p(xiangshan.DebugOptionsKey).ResetGen,
      "O1 trace requires the common simulation reset")
    require(fuCfgs.count(_.fuType == FuType.vdot) == 1)
    val observedVDot = funcUnits(fuCfgs.indexWhere(_.fuType == FuType.vdot))
      .asInstanceOf[xiangshan.backend.fu.wrapper.VDot]
    // Every timestamp and sequence register is on the ungated parent clock.
    // Child I/O is read directly; private expressions are tapped without feedback.
    val o1Cycle = GTimer()
    val o1NextSeq = RegInit(0.U(64.W))
    val o1ActiveVDotSeq = RegInit(0.U(64.W))
    val o1SchemaPrinted = RegInit(false.B)
    val o1Killed = tapAndRead(observedVDot.o1ObservedKilled)
    val o1State = tapAndRead(observedVDot.o1ObservedState)
    val o1IllegalInput = tapAndRead(observedVDot.o1ObservedIllegalInput)
    val o1Vl = tapAndRead(observedVDot.o1ObservedVl)
    val o1In = observedVDot.io.in.bits.ctrl
    // DataHoldBypass outCtrl exposes the NEW request during a handoff. These
    // actual registered output fields continue to identify the OLD response.
    val o1Out = observedVDot.io.out.bits.ctrl
    val o1Data = observedVDot.io.out.bits.res.data
    val o1Exception = o1Out.exceptionVec.get.asUInt
    val o1Illegal = o1Out.exceptionVec.get(xiangshan.ExceptionNO.illegalInstr)
    when(io.in.fire) { o1NextSeq := o1NextSeq + 1.U }
    when(observedVDot.io.in.fire) { o1ActiveVDotSeq := o1NextSeq }
    when(!reset.asBool) {
      when(!o1SchemaPrinted) {
        printf(p"O1_SCHEMA version=1 clock=global latency=2 rob_size=${RobSize.U} ftq_size=${FtqSize.U} vlen=${VLEN.U} handoff=${vdotHandoff.B.asUInt}\n")
        o1SchemaPrinted := true.B
      }
      when(io.in.fire) {
        printf(p"O1_VFEX4_ACCEPT cycle=${o1Cycle} seq=${o1NextSeq} rob=${io.in.bits.robIdx.flag}:${io.in.bits.robIdx.value} fu=0x${Hexadecimal(io.in.bits.fuType)} pdest=${io.in.bits.pdest}\n")
      }
      when(io.in.valid && !io.in.ready) {
        printf(p"O1_VFEX4_WAIT cycle=${o1Cycle} rob=${io.in.bits.robIdx.flag}:${io.in.bits.robIdx.value} fu=0x${Hexadecimal(io.in.bits.fuType)} busy=${busy}\n")
      }
      // CtrlBlock registers the ROB redirect once before delivering this flush.
      // Log both boundaries instead of inferring the parent flush from ROB time.
      when(io.flush.valid) {
        printf(p"O1_VFEX4_REDIRECT cycle=${o1Cycle} rob=${io.flush.bits.robIdx.flag}:${io.flush.bits.robIdx.value} self=${io.flush.bits.flushItself()}\n")
      }
      when(observedVDot.io.in.fire) {
        printf(p"O1_ACCEPT cycle=${o1Cycle} seq=${o1NextSeq} rob=${o1In.robIdx.flag}:${o1In.robIdx.value} pdest=${o1In.pdest} vl=${o1Vl} illegal=${o1IllegalInput} vecwen=${o1In.vecWen.get} v0wen=${o1In.v0Wen.get}\n")
      }
      when(o1Killed) {
        printf(p"O1_KILL cycle=${o1Cycle} seq=${o1ActiveVDotSeq} rob=${o1Out.robIdx.flag}:${o1Out.robIdx.value} pdest=${o1Out.pdest} redirect=${io.flush.bits.robIdx.flag}:${io.flush.bits.robIdx.value} self=${io.flush.bits.flushItself()} state=${o1State}\n")
      }
      when(observedVDot.io.out.valid && !observedVDot.io.out.ready) {
        printf(p"O1_STALL cycle=${o1Cycle} seq=${o1ActiveVDotSeq} rob=${o1Out.robIdx.flag}:${o1Out.robIdx.value} pdest=${o1Out.pdest} illegal=${o1Illegal} data=0x${Hexadecimal(o1Data)} vecwen=${o1Out.vecWen.get} v0wen=${o1Out.v0Wen.get} exception=0x${Hexadecimal(o1Exception)}\n")
      }
      when(observedVDot.io.out.fire) {
        printf(p"O1_RESPONSE cycle=${o1Cycle} seq=${o1ActiveVDotSeq} rob=${o1Out.robIdx.flag}:${o1Out.robIdx.value} pdest=${o1Out.pdest} illegal=${o1Illegal} data=0x${Hexadecimal(o1Data)} vecwen=${o1Out.vecWen.get} v0wen=${o1Out.v0Wen.get} exception=0x${Hexadecimal(o1Exception)}\n")
      }
      when(observedVDot.io.out.fire && observedVDot.io.in.fire) {
        printf(p"O1_HANDOFF cycle=${o1Cycle} oldseq=${o1ActiveVDotSeq} newseq=${o1NextSeq} oldrob=${o1Out.robIdx.flag}:${o1Out.robIdx.value} newrob=${o1In.robIdx.flag}:${o1In.robIdx.value} oldpdest=${o1Out.pdest} newpdest=${o1In.pdest} busy=${busy}\n")
      }
    }
  }

  if (xiangshan.backend.fu.wrapper.VDotO2.traceEnabled &&
      fuCfgs.contains(xiangshan.backend.fu.FuConfig.VDotCfg)) {
    require(vdotElastic && exuParams.name == "VFEX4" && !exuParams.latencyCertain,
      "O2 trace requires the elastic, uncertain-latency VFEX4")
    require(!p(xiangshan.DebugOptionsKey).ResetGen,
      "O2 trace requires the common simulation reset")
    val observedVDot = elasticVDot.get
    // All timestamps, sequence tags and shadow DIV lifecycle are observations
    // on the ungated parent clock. No trace state drives functional logic.
    val o2Cycle = GTimer()
    val o2NextSeq = RegInit(0.U(64.W))
    val o2PSeq = RegInit(0.U(64.W))
    val o2RSeq = RegInit(0.U(64.W))
    val o2SchemaPrinted = RegInit(false.B)
    val o2P = tapAndRead(observedVDot.o2ObservedPCtrl)
    val o2PPerf = tapAndRead(observedVDot.o2ObservedPPerf)
    val o2R = observedVDot.io.out.bits.ctrl
    val o2PValid = observedVDot.pipelineStatus.pValid
    val o2RValid = observedVDot.pipelineStatus.rValid
    val o2KillP = tapAndRead(observedVDot.o2ObservedKillP)
    val o2KillR = tapAndRead(observedVDot.o2ObservedKillR)
    val o2Move = tapAndRead(observedVDot.o2ObservedMove)
    val o2IllegalInput = tapAndRead(observedVDot.o2ObservedIllegalInput)
    val o2Vl = tapAndRead(observedVDot.o2ObservedVl)
    val o2In = observedVDot.io.in.bits.ctrl
    val o2Out = observedVDot.io.out
    val o2DivAccept = io.in.fire && io.in.bits.fuType =/= FuType.vdot.U
    val o2DivActive = RegInit(false.B)
    val o2DivSeq = RegInit(0.U(64.W))
    val o2DivRob = Reg(chiselTypeOf(io.in.bits.robIdx))
    val o2DivFu = Reg(chiselTypeOf(io.in.bits.fuType))
    val o2DivPdest = Reg(chiselTypeOf(io.in.bits.pdest))
    val o2DivKill = o2DivActive && o2DivRob.needFlush(io.flush) && !reset.asBool
    val o2DivUnits = funcUnits.filter(_.cfg.fuType != FuType.vdot)
    val o2DivFire = o2DivUnits.map(_.io.out.fire).reduce(_ || _)

    when(io.in.fire) { o2NextSeq := o2NextSeq + 1.U }
    when(observedVDot.io.in.fire) { o2PSeq := o2NextSeq }
    // Old P transfers even when a different new request replaces P this edge.
    when(o2Move) { o2RSeq := o2PSeq }
    when(o2DivAccept) {
      o2DivActive := true.B
      o2DivSeq := o2NextSeq
      o2DivRob := io.in.bits.robIdx
      o2DivFu := io.in.bits.fuType
      o2DivPdest := io.in.bits.pdest
    }.elsewhen(o2DivKill || o2DivFire) {
      o2DivActive := false.B
    }

    val o2Activity = o2PValid || o2RValid || elasticDivOccupied.get ||
      io.in.valid || io.flush.valid
    val o2PreviousActivity = RegNext(o2Activity, false.B)
    when(reset.asBool && o2SchemaPrinted) {
      // Runtime reset ends this epoch. G3's complete-run checker rejects
      // multiple epochs; the initial simulation reset emits no such record.
      // printf normally suppresses itself during reset; this diagnostic must
      // use only the explicit outer reset condition to record the old epoch.
      withReset(false.B) {
        printf(p"O2_RESET cycle=${o2Cycle} pvalid=${o2PValid} pseq=${o2PSeq} rvalid=${o2RValid} rseq=${o2RSeq} divactive=${o2DivActive} divseq=${o2DivSeq}\n")
      }
    }
    when(!reset.asBool) {
      when(!o2SchemaPrinted) {
        printf(p"O2_SCHEMA version=1 clock=global latency=2 slots=2 rob_size=${RobSize.U} ftq_size=${FtqSize.U} vlen=${VLEN.U} vpu_width=${o2In.vpu.get.getWidth.U} perf_width=${observedVDot.io.in.bits.perfDebugInfo.getWidth.U}\n")
        o2SchemaPrinted := true.B
      }
      when(o2Activity || o2PreviousActivity || !o2SchemaPrinted) {
        printf(p"O2_STATE cycle=${o2Cycle} pvalid=${o2PValid} pseq=${o2PSeq} prob=${o2P.robIdx.flag}:${o2P.robIdx.value} ppdest=${o2P.pdest} rvalid=${o2RValid} rseq=${o2RSeq} rrob=${o2R.robIdx.flag}:${o2R.robIdx.value} rpdest=${o2R.pdest} occupancy=${observedVDot.pipelineStatus.occupancy} invalid=${io.in.valid} inready=${io.in.ready} vready=${observedVDot.io.in.ready} outvalid=${o2Out.valid} outready=${o2Out.ready} move=${o2Move} killp=${o2KillP} killr=${o2KillR} divactive=${o2DivActive} divseq=${o2DivSeq} divoccupied=${elasticDivOccupied.get} busy=${busy}\n")
      }
      when(io.in.fire) {
        printf(p"O2_VFEX4_ACCEPT cycle=${o2Cycle} seq=${o2NextSeq} rob=${io.in.bits.robIdx.flag}:${io.in.bits.robIdx.value} fu=0x${Hexadecimal(io.in.bits.fuType)} pdest=${io.in.bits.pdest}\n")
      }
      when(io.in.valid && !io.in.ready) {
        printf(p"O2_VFEX4_WAIT cycle=${o2Cycle} rob=${io.in.bits.robIdx.flag}:${io.in.bits.robIdx.value} fu=0x${Hexadecimal(io.in.bits.fuType)} busy=${busy}\n")
      }
      // The actual VFEX4 flush is a registered stage later than ROB redirect.
      when(io.flush.valid) {
        printf(p"O2_VFEX4_REDIRECT cycle=${o2Cycle} rob=${io.flush.bits.robIdx.flag}:${io.flush.bits.robIdx.value} self=${io.flush.bits.flushItself()}\n")
      }
      when(observedVDot.io.in.fire) {
        printf(p"O2_ACCEPT cycle=${o2Cycle} seq=${o2NextSeq} rob=${o2In.robIdx.flag}:${o2In.robIdx.value} pdest=${o2In.pdest} vl=${o2Vl} illegal=${o2IllegalInput} vecwen=${o2In.vecWen.get} v0wen=${o2In.v0Wen.get} vpu=0x${Hexadecimal(o2In.vpu.get.asUInt)} perf=0x${Hexadecimal(observedVDot.io.in.bits.perfDebugInfo.asUInt)} vs1=0x${Hexadecimal(observedVDot.io.in.bits.data.src(0))} vs2=0x${Hexadecimal(observedVDot.io.in.bits.data.src(1))}\n")
      }
      when(o2Move) {
        printf(p"O2_MOVE cycle=${o2Cycle} seq=${o2PSeq} rob=${o2P.robIdx.flag}:${o2P.robIdx.value} pdest=${o2P.pdest} illegal=${o2P.exceptionVec.get(xiangshan.ExceptionNO.illegalInstr)} vecwen=${o2P.vecWen.get} v0wen=${o2P.v0Wen.get} exception=0x${Hexadecimal(o2P.exceptionVec.get.asUInt)} vpu=0x${Hexadecimal(o2P.vpu.get.asUInt)} perf=0x${Hexadecimal(o2PPerf.asUInt)}\n")
      }
      when(o2KillP) {
        printf(p"O2_KILL cycle=${o2Cycle} seq=${o2PSeq} slot=P rob=${o2P.robIdx.flag}:${o2P.robIdx.value} pdest=${o2P.pdest} redirect=${io.flush.bits.robIdx.flag}:${io.flush.bits.robIdx.value} self=${io.flush.bits.flushItself()}\n")
      }
      when(o2KillR) {
        printf(p"O2_KILL cycle=${o2Cycle} seq=${o2RSeq} slot=R rob=${o2R.robIdx.flag}:${o2R.robIdx.value} pdest=${o2R.pdest} redirect=${io.flush.bits.robIdx.flag}:${io.flush.bits.robIdx.value} self=${io.flush.bits.flushItself()}\n")
      }
      when(o2Out.valid && !o2Out.ready) {
        printf(p"O2_STALL cycle=${o2Cycle} seq=${o2RSeq} rob=${o2R.robIdx.flag}:${o2R.robIdx.value} pdest=${o2R.pdest} illegal=${o2R.exceptionVec.get(xiangshan.ExceptionNO.illegalInstr)} data=0x${Hexadecimal(o2Out.bits.res.data)} vecwen=${o2R.vecWen.get} v0wen=${o2R.v0Wen.get} exception=0x${Hexadecimal(o2R.exceptionVec.get.asUInt)} vpu=0x${Hexadecimal(o2R.vpu.get.asUInt)} perf=0x${Hexadecimal(o2Out.bits.perfDebugInfo.asUInt)}\n")
      }
      when(o2Out.fire) {
        printf(p"O2_RESPONSE cycle=${o2Cycle} seq=${o2RSeq} rob=${o2R.robIdx.flag}:${o2R.robIdx.value} pdest=${o2R.pdest} illegal=${o2R.exceptionVec.get(xiangshan.ExceptionNO.illegalInstr)} data=0x${Hexadecimal(o2Out.bits.res.data)} vecwen=${o2R.vecWen.get} v0wen=${o2R.v0Wen.get} exception=0x${Hexadecimal(o2R.exceptionVec.get.asUInt)} vpu=0x${Hexadecimal(o2R.vpu.get.asUInt)} perf=0x${Hexadecimal(o2Out.bits.perfDebugInfo.asUInt)}\n")
      }
      when(o2DivAccept) {
        printf(p"O2_DIV_ACCEPT cycle=${o2Cycle} seq=${o2NextSeq} rob=${io.in.bits.robIdx.flag}:${io.in.bits.robIdx.value} fu=0x${Hexadecimal(io.in.bits.fuType)} pdest=${io.in.bits.pdest}\n")
      }
      when(o2DivKill) {
        printf(p"O2_DIV_KILL cycle=${o2Cycle} seq=${o2DivSeq} rob=${o2DivRob.flag}:${o2DivRob.value} fu=0x${Hexadecimal(o2DivFu)} pdest=${o2DivPdest} redirect=${io.flush.bits.robIdx.flag}:${io.flush.bits.robIdx.value} self=${io.flush.bits.flushItself()}\n")
      }
      o2DivUnits.foreach { fu =>
        val ctrl = fu.io.out.bits.ctrl
        when(fu.io.out.valid) {
          // Retain the last DIV seq after logical kill until physical output
          // disappears. Output identity always comes from the real child.
          printf(p"O2_DIV_OUTPUT cycle=${o2Cycle} seq=${o2DivSeq} rob=${ctrl.robIdx.flag}:${ctrl.robIdx.value} fu=0x${Hexadecimal(fu.cfg.fuType.U)} pdest=${ctrl.pdest} ready=${fu.io.out.ready} cancelled=${!o2DivActive || o2DivKill}\n")
        }
      }
    }
  }

  def pipelineReg(init: ExuInput, valid: Bool, latency: Int, flush: ValidIO[Redirect]): (Seq[ExuInput], Seq[Bool]) = {
    val validVec = valid +: Seq.fill(latency)(RegInit(false.B))
    val inVec = init +: Seq.fill(latency)(Reg(new ExuInput(exuParams)))
    val robIdxVec = inVec.map(_.robIdx)
    // if flush(0), valid 0 will not given, so set flushVec(0) to false.B
    val flushVec = validVec.zip(robIdxVec).map(x => x._1 && x._2.needFlush(flush))
    for (i <- 1 to latency) {
      validVec(i) := validVec(i - 1) && !flushVec(i - 1)
      inVec(i) := inVec(i - 1)
    }
    (inVec, validVec)
  }
  val latencyMax = fuCfgs.map(_.latency.latencyVal.getOrElse(0)).max
  val inPipe = pipelineReg(io.in.bits, io.in.valid, latencyMax, io.flush)
  // Dispatcher.out <---> FunctionUnits
  dispatchedInputs.zip(funcUnits.map(_.io.in)).foreach {
    case (source: DecoupledIO[ExuInput], sink: DecoupledIO[FuncUnitInput]) =>
      sink.valid := source.valid
      source.ready := sink.ready

      sink.bits.data.pc          .foreach(x => x := source.bits.pc.get)
      sink.bits.data.nextPcOffset.foreach(x => x := source.bits.nextPcOffset.get)
      sink.bits.data.imm         := source.bits.imm
      sink.bits.ctrl.fuOpType    := source.bits.fuOpType
      sink.bits.ctrl.robIdx      := source.bits.robIdx
      sink.bits.ctrl.pdest       := source.bits.pdest
      sink.bits.ctrl.rfWen       .foreach(x => x := source.bits.rfWen.get)
      sink.bits.ctrl.fpWen       .foreach(x => x := source.bits.fpWen.get)
      sink.bits.ctrl.vecWen      .foreach(x => x := source.bits.vecWen.get)
      sink.bits.ctrl.v0Wen       .foreach(x => x := source.bits.v0Wen.get)
      sink.bits.ctrl.vlWen       .foreach(x => x := source.bits.vlWen.get)
      sink.bits.ctrl.flushPipe   .foreach(x => x := source.bits.flushPipe.get)
      sink.bits.ctrl.preDecode   .foreach(x => x := source.bits.preDecode.get)
      sink.bits.ctrl.ftqIdx      .foreach(x => x := source.bits.ftqIdx.get)
      sink.bits.ctrl.ftqOffset   .foreach(x => x := source.bits.ftqOffset.get)
      sink.bits.ctrl.predictInfo .foreach(x => x := source.bits.predictInfo.get)
      sink.bits.ctrl.fpu         .foreach(x => x := source.bits.fpu.get)
      sink.bits.ctrl.vpu         .foreach(x => x := source.bits.vpu.get)
      sink.bits.ctrl.vpu         .foreach(x => x.fpu.isFpToVecInst := 0.U)
      sink.bits.ctrl.vpu         .foreach(x => x.fpu.isFP32Instr   := 0.U)
      sink.bits.ctrl.vpu         .foreach(x => x.fpu.isFP64Instr   := 0.U)
      sink.bits.perfDebugInfo    := source.bits.perfDebugInfo
  }
  funcUnits.filter(_.cfg.latency.latencyVal.nonEmpty).map{ fu =>
    val latency = fu.cfg.latency.latencyVal.getOrElse(0)
    for (i <- 0 until (latency+1)) {
      val sink = fu.io.in.bits.ctrlPipe.get(i)
      val source = inPipe._1(i)
      fu.io.in.bits.validPipe.get(i) := inPipe._2(i)
      sink.fuOpType := source.fuOpType
      sink.robIdx := source.robIdx
      sink.pdest := source.pdest
      sink.rfWen.foreach(x => x := source.rfWen.get)
      sink.fpWen.foreach(x => x := source.fpWen.get)
      sink.vecWen.foreach(x => x := source.vecWen.get)
      sink.v0Wen.foreach(x => x := source.v0Wen.get)
      sink.vlWen.foreach(x => x := source.vlWen.get)
      sink.flushPipe.foreach(x => x := source.flushPipe.get)
      sink.preDecode.foreach(x => x := source.preDecode.get)
      sink.ftqIdx.foreach(x => x := source.ftqIdx.get)
      sink.ftqOffset.foreach(x => x := source.ftqOffset.get)
      sink.predictInfo.foreach(x => x := source.predictInfo.get)
      sink.fpu.foreach(x => x := source.fpu.get)
      sink.vpu.foreach(x => x := source.vpu.get)
      sink.vpu.foreach(x => x.fpu.isFpToVecInst := 0.U)
      sink.vpu.foreach(x => x.fpu.isFP32Instr := 0.U)
      sink.vpu.foreach(x => x.fpu.isFP64Instr := 0.U)
      val sinkData = fu.io.in.bits.dataPipe.get(i)
      val sourceData = inPipe._1(i)
      sinkData.src.zip(sourceData.src).foreach { case (fuSrc, exuSrc) => fuSrc := exuSrc }
      sinkData.pc.foreach(x => x := sourceData.pc.get)
      sinkData.nextPcOffset.foreach(x => x := sourceData.nextPcOffset.get)
      sinkData.imm := sourceData.imm
    }
  }

  funcUnits.zip(exuParams.idxCopySrc).map{ case(fu, idx) =>
    (fu.io.in.bits.data.src).zip(io.in.bits.src).foreach { case(fuSrc, exuSrc) => fuSrc := exuSrc }
    if(fu.cfg.srcNeedCopy) {
      (fu.io.in.bits.data.src).zip(io.in.bits.copySrc.get(idx)).foreach { case(fuSrc, copySrc) => fuSrc := copySrc }
    }
  }

  private val OutresVecs = funcUnits.map { fu =>
    def latDiff :Int = fu.cfg.latency.extraLatencyVal.getOrElse(0)
    val OutresVec = fu.io.out.bits.res +: Seq.fill(latDiff)(Reg(chiselTypeOf(fu.io.out.bits.res)))
    for (i <- 1 to latDiff) {
      OutresVec(i) := OutresVec(i - 1)
    }
    OutresVec
  }
  OutresVecs.foreach(vec => vec.foreach(res =>dontTouch(res)))

  private val fuOutValidOH = funcUnits.map(_.io.out.valid)
  XSError(PopCount(fuOutValidOH) > 1.U, p"fuOutValidOH ${Binary(VecInit(fuOutValidOH).asUInt)} should be one-hot)\n")
  private val fuOutBitsVec = funcUnits.map(_.io.out.bits)
  private val fuOutresVec = OutresVecs.map(_.last)
  private val fuRedirectVec: Seq[Option[ValidIO[Redirect]]] = fuOutresVec.map(_.redirect)

  // Assume that one fu can only write int or fp or vec,
  // otherwise, wenVec should be assigned to wen in fu.
  private val fuIntWenVec = funcUnits.map(x => x.cfg.needIntWen.B && x.io.out.bits.ctrl.rfWen.getOrElse(false.B))
  private val fuFpWenVec  = funcUnits.map( x => x.cfg.needFpWen.B  && x.io.out.bits.ctrl.fpWen.getOrElse(false.B))
  private val fuVecWenVec = funcUnits.map(x => x.cfg.needVecWen.B && x.io.out.bits.ctrl.vecWen.getOrElse(false.B))
  private val fuV0WenVec = funcUnits.map(x => x.cfg.needV0Wen.B && x.io.out.bits.ctrl.v0Wen.getOrElse(false.B))
  private val fuVlWenVec = funcUnits.map(x => x.cfg.needVlWen.B && x.io.out.bits.ctrl.vlWen.getOrElse(false.B))
  // FunctionUnits <---> ExeUnit.out

  private val outDataVec = Seq(
    Some(fuOutresVec.map(_.data)),
    Option.when(funcUnits.exists(_.cfg.writeIntRf))
      (funcUnits.zip(fuOutresVec).filter{ case (fu, _) => fu.cfg.writeIntRf}.map{ case(_, fuout) => fuout.data}),
    Option.when(funcUnits.exists(_.cfg.writeFpRf))
      (funcUnits.zip(fuOutresVec).filter{ case (fu, _) => fu.cfg.writeFpRf}.map{ case(_, fuout) => fuout.data}),
    Option.when(funcUnits.exists(_.cfg.writeVecRf))
      (funcUnits.zip(fuOutresVec).filter{ case (fu, _) => fu.cfg.writeVecRf}.map{ case(_, fuout) => fuout.data}),
    Option.when(funcUnits.exists(_.cfg.writeV0Rf))
      (funcUnits.zip(fuOutresVec).filter{ case (fu, _) => fu.cfg.writeV0Rf}.map{ case(_, fuout) => fuout.data}),
    Option.when(funcUnits.exists(_.cfg.writeVlRf))
      (funcUnits.zip(fuOutresVec).filter{ case (fu, _) => fu.cfg.writeVlRf}.map{ case(_, fuout) => fuout.data}),
  ).flatten
  private val outDataValidOH = Seq(
    Some(fuOutValidOH),
    Option.when(funcUnits.exists(_.cfg.writeIntRf))
      (funcUnits.zip(fuOutValidOH).filter{ case (fu, _) => fu.cfg.writeIntRf}.map{ case(_, fuoutOH) => fuoutOH}),
    Option.when(funcUnits.exists(_.cfg.writeFpRf))
      (funcUnits.zip(fuOutValidOH).filter{ case (fu, _) => fu.cfg.writeFpRf}.map{ case(_, fuoutOH) => fuoutOH}),
    Option.when(funcUnits.exists(_.cfg.writeVecRf))
      (funcUnits.zip(fuOutValidOH).filter{ case (fu, _) => fu.cfg.writeVecRf}.map{ case(_, fuoutOH) => fuoutOH}),
    Option.when(funcUnits.exists(_.cfg.writeV0Rf))
      (funcUnits.zip(fuOutValidOH).filter{ case (fu, _) => fu.cfg.writeV0Rf}.map{ case(_, fuoutOH) => fuoutOH}),
    Option.when(funcUnits.exists(_.cfg.writeVlRf))
      (funcUnits.zip(fuOutValidOH).filter{ case (fu, _) => fu.cfg.writeVlRf}.map{ case(_, fuoutOH) => fuoutOH}),
  ).flatten

  val criticalErrors = funcUnits.filter(fu => fu.cfg.needCriticalErrors).flatMap(fu => fu.getCriticalErrors)
  generateCriticalErrors()

  io.out.valid := Cat(fuOutValidOH).orR
  funcUnits.foreach(fu => fu.io.out.ready := io.out.ready)

  // select one fu's result
  io.out.bits.data := VecInit(outDataVec.zip(outDataValidOH).map{ case(data, validOH) => Mux1H(validOH, data)})
  io.out.bits.robIdx := Mux1H(fuOutValidOH, fuOutBitsVec.map(_.ctrl.robIdx))
  io.out.bits.pdest := Mux1H(fuOutValidOH, fuOutBitsVec.map(_.ctrl.pdest))
  io.out.bits.intWen.foreach(x => x := Mux1H(fuOutValidOH, fuIntWenVec))
  io.out.bits.fpWen.foreach(x => x := Mux1H(fuOutValidOH, fuFpWenVec))
  io.out.bits.vecWen.foreach(x => x := Mux1H(fuOutValidOH, fuVecWenVec))
  io.out.bits.v0Wen.foreach(x => x := Mux1H(fuOutValidOH, fuV0WenVec))
  io.out.bits.vlWen.foreach(x => x := Mux1H(fuOutValidOH, fuVlWenVec))
  io.out.bits.redirect.foreach(x => x := Mux1H((fuOutValidOH zip fuRedirectVec).filter(_._2.isDefined).map(x => (x._1, x._2.get))))
  io.out.bits.fflags.foreach(x => x := Mux1H(fuOutValidOH, fuOutresVec.map(_.fflags.getOrElse(0.U.asTypeOf(io.out.bits.fflags.get)))))
  io.out.bits.wflags.foreach(x => x := Mux1H(fuOutValidOH, fuOutBitsVec.map(_.ctrl.fpu.getOrElse(0.U.asTypeOf(new FPUCtrlSignals)).wflags)))
  io.out.bits.vxsat.foreach(x => x := Mux1H(fuOutValidOH, fuOutresVec.map(_.vxsat.getOrElse(0.U.asTypeOf(io.out.bits.vxsat.get)))))
  io.out.bits.exceptionVec.foreach(x => x := Mux1H(fuOutValidOH, fuOutBitsVec.map(_.ctrl.exceptionVec.getOrElse(0.U.asTypeOf(io.out.bits.exceptionVec.get)))))
  io.out.bits.flushPipe.foreach(x => x := Mux1H(fuOutValidOH, fuOutBitsVec.map(_.ctrl.flushPipe.getOrElse(0.U.asTypeOf(io.out.bits.flushPipe.get)))))
  io.out.bits.replay.foreach(x => x := Mux1H(fuOutValidOH, fuOutBitsVec.map(_.ctrl.replay.getOrElse(0.U.asTypeOf(io.out.bits.replay.get)))))
  io.out.bits.predecodeInfo.foreach(x => x := Mux1H(fuOutValidOH, fuOutBitsVec.map(_.ctrl.preDecode.getOrElse(0.U.asTypeOf(io.out.bits.predecodeInfo.get)))))

  io.csrio.foreach(exuio => funcUnits.foreach(fu => fu.io.csrio.foreach{
    fuio =>
      exuio <> fuio
      fuio.exception := DelayN(exuio.exception, 2)
      fuio.robDeqPtr := DelayN(exuio.robDeqPtr, 2)
  }))
  io.csrin.foreach(exuio => funcUnits.foreach(fu => fu.io.csrin.foreach{fuio => fuio := exuio}))
  io.csrToDecode.foreach(toDecode => funcUnits.foreach(fu => fu.io.csrToDecode.foreach(fuOut => toDecode := fuOut)))

  io.vtype.foreach(exuio => funcUnits.foreach(fu => fu.io.vtype.foreach(fuio => exuio := fuio)))
  io.fenceio.foreach(exuio => funcUnits.foreach(fu => fu.io.fenceio.foreach(fuio => fuio <> exuio)))
  io.frm.foreach(exuio => funcUnits.foreach(fu => fu.io.frm.foreach(fuio => fuio <> exuio)))
  io.vxrm.foreach(exuio => funcUnits.foreach(fu => fu.io.vxrm.foreach(fuio => fuio <> exuio)))
  io.vlIsZero.foreach(exuio => funcUnits.foreach(fu => fu.io.vlIsZero.foreach(fuio => exuio := fuio)))
  io.vlIsVlmax.foreach(exuio => funcUnits.foreach(fu => fu.io.vlIsVlmax.foreach(fuio => exuio := fuio)))
  io.instrAddrTransType.foreach(exuio => funcUnits.foreach(fu => fu.io.instrAddrTransType.foreach(fuio => fuio := exuio)))

  // debug info
  io.out.bits.debug     := 0.U.asTypeOf(io.out.bits.debug)
  io.out.bits.debug.isPerfCnt := funcUnits.map(_.io.csrio.map(_.isPerfCnt)).map(_.getOrElse(false.B)).reduce(_ || _)
  io.out.bits.debugInfo := Mux1H(fuOutValidOH, fuOutBitsVec.map(_.perfDebugInfo))
}

class DispatcherIO[T <: Data](private val gen: T, n: Int) extends Bundle {
  val in = Flipped(DecoupledIO(gen))

  val out = Vec(n, DecoupledIO(gen))
}

class Dispatcher[T <: Data](private val gen: T, n: Int, acceptCond: T => Seq[Bool])
  (implicit p: Parameters)
  extends Module {

  val io = IO(new DispatcherIO(gen, n))

  private val acceptVec: Vec[Bool] = VecInit(acceptCond(io.in.bits))

  XSError(io.in.valid && PopCount(acceptVec) > 1.U, p"[ExeUnit] accept vec should no more than 1, ${Binary(acceptVec.asUInt)} ")
  XSError(io.in.valid && PopCount(acceptVec) === 0.U, "[ExeUnit] there is a inst not dispatched to any fu")

  io.out.zipWithIndex.foreach { case (out, i) =>
    out.valid := acceptVec(i) && io.in.valid
    out.bits := io.in.bits
  }

  io.in.ready := Cat(io.out.map(_.ready)).andR
}

class MemExeUnitIO (implicit p: Parameters) extends XSBundle {
  val flush = Flipped(ValidIO(new Redirect()))
  val in = Flipped(DecoupledIO(new MemExuInput()))
  val out = DecoupledIO(new MemExuOutput())
}

class MemExeUnit(exuParams: ExeUnitParams)(implicit p: Parameters) extends XSModule {
  val io = IO(new MemExeUnitIO)
  val fu = exuParams.fuConfigs.head.fuGen(p, exuParams.fuConfigs.head)
  fu.io.flush             := io.flush
  fu.io.in.valid          := io.in.valid
  io.in.ready             := fu.io.in.ready

  fu.io.in.bits.ctrl.robIdx    := io.in.bits.uop.robIdx
  fu.io.in.bits.ctrl.pdest     := io.in.bits.uop.pdest
  fu.io.in.bits.ctrl.fuOpType  := io.in.bits.uop.fuOpType
  fu.io.in.bits.data.imm       := io.in.bits.uop.imm
  fu.io.in.bits.data.src.zip(io.in.bits.src).foreach(x => x._1 := x._2)
  fu.io.in.bits.perfDebugInfo := io.in.bits.uop.debugInfo

  io.out.valid            := fu.io.out.valid
  fu.io.out.ready         := io.out.ready

  io.out.bits             := 0.U.asTypeOf(io.out.bits) // dontCare other fields
  io.out.bits.data        := fu.io.out.bits.res.data
  io.out.bits.uop.robIdx  := fu.io.out.bits.ctrl.robIdx
  io.out.bits.uop.pdest   := fu.io.out.bits.ctrl.pdest
  io.out.bits.uop.fuType  := io.in.bits.uop.fuType
  io.out.bits.uop.fuOpType:= io.in.bits.uop.fuOpType
  io.out.bits.uop.sqIdx   := io.in.bits.uop.sqIdx
  io.out.bits.uop.debugInfo := fu.io.out.bits.perfDebugInfo

  io.out.bits.debug       := 0.U.asTypeOf(io.out.bits.debug)
}
