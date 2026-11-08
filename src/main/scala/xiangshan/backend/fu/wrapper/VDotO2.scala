package xiangshan.backend.fu.wrapper

/** O2 is an elaboration-only experiment; no run-time selector or cached flags. */
object VDotO2 {
  private def flag(name: String): Boolean = sys.env.get(name) match {
    case None | Some("0") => false
    case Some("1") => true
    case _ => throw new IllegalArgumentException(s"$name must be 0 or 1")
  }

  def enabled: Boolean = {
    val selected = flag("VDOT_O2_ELASTIC")
    val shortLatency = flag("VDOT_P4_ONE_CYCLE")
    val sp1Trace = flag("VDOT_SP1_TRACE")
    require(!sp1Trace || (selected && shortLatency),
      "VDOT_SP1_TRACE=1 requires O2 and P4 one-cycle mode")
    require(!sp1Trace || !flag("VDOT_O2_TRACE"),
      "VDOT_SP1_TRACE and VDOT_O2_TRACE are mutually exclusive")
    require(!shortLatency || selected,
      "VDOT_P4_ONE_CYCLE=1 requires VDOT_O2_ELASTIC=1")
    require(!shortLatency || !flag("VDOT_O2_TRACE"),
      "VDOT_P4_ONE_CYCLE cannot use the frozen two-cycle O2 observer")
    require(!flag("VDOT_O2_TRACE") || selected,
      "VDOT_O2_TRACE=1 requires VDOT_O2_ELASTIC=1")
    if (selected) {
      require(flag("VDOT_T14_FUSED_INPUT"),
        "VDOT_O2_ELASTIC=1 requires VDOT_T14_FUSED_INPUT=1")
      require(!flag("VDOT_O1_HANDOFF"),
        "VDOT_O2_ELASTIC cannot be combined with VDOT_O1_HANDOFF")
      require(!flag("VDOT_T12_TRACE") && !flag("VDOT_O1_TRACE"),
        "O2 cannot use the frozen T12 or single-outstanding O1 observer")
      // T13 retains its original global ROB/CSR stream. Each arithmetic mode
      // requires its matching elastic-slot observation protocol.
      require(!flag("VDOT_T13_TRACE") ||
        (if (shortLatency) sp1Trace else flag("VDOT_O2_TRACE")),
        "T13 requires the matching O2 or SP1 observer")
    }
    selected
  }

  // Compile-time only. Default-off keeps the frozen two-stage implementation.
  def oneCycle: Boolean = {
    val selected = flag("VDOT_P4_ONE_CYCLE")
    require(!selected || enabled,
      "VDOT_P4_ONE_CYCLE=1 requires elastic mode")
    selected
  }

  def traceEnabled: Boolean = {
    val selected = flag("VDOT_O2_TRACE")
    if (selected) {
      require(enabled, "VDOT_O2_TRACE=1 requires elastic mode")
    }
    selected
  }

  // Compile-time, default-off. Observation never selects the datapath.
  def sp1TraceEnabled: Boolean = {
    val selected = flag("VDOT_SP1_TRACE")
    if (selected) require(enabled && oneCycle,
      "VDOT_SP1_TRACE=1 requires P4 elastic mode")
    selected
  }
}
