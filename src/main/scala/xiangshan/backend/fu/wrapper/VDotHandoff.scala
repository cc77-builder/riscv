package xiangshan.backend.fu.wrapper

/** Experimental, elaboration-only O1 switches. No global cached environment value. */
object VDotHandoff {
  def traceEnabled: Boolean = {
    val selected = VDotO1Trace.eventEnabled
    if (selected) {
      require(sys.env.get("VDOT_T14_FUSED_INPUT").contains("1"),
        "VDOT_O1_TRACE=1 requires VDOT_T14_FUSED_INPUT=1 (schema v1 latency=2)")
      require(!sys.env.get("VDOT_T12_TRACE").contains("1"),
        "VDOT_O1_TRACE cannot be combined with the frozen T12 observer schema")
    }
    selected
  }

  def enabled: Boolean = {
    val selected = sys.env.get("VDOT_O1_HANDOFF") match {
      case None | Some("0") => false
      case Some("1") => true
      case _ => throw new IllegalArgumentException("VDOT_O1_HANDOFF must be 0 or 1")
    }
    val o1Trace = traceEnabled
    if (selected) {
      require(sys.env.get("VDOT_T14_FUSED_INPUT").contains("1"),
        "VDOT_O1_HANDOFF=1 requires VDOT_T14_FUSED_INPUT=1")
      // T12's gated-child clock mapper cannot represent a same-cycle handoff.
      // T13 uses only global ROB/CSR clocks; permit its unchanged records when
      // the independent O1 observer is present and the old T12 schema is off.
      require(!sys.env.get("VDOT_T12_TRACE").contains("1") &&
        (!sys.env.get("VDOT_T13_TRACE").contains("1") || o1Trace),
        "O1 handoff cannot use T12; T13 requires VDOT_O1_TRACE=1 with T12 disabled")
    }
    selected
  }
}
