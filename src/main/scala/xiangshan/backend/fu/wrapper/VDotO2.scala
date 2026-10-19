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
    require(!flag("VDOT_O2_TRACE") || selected,
      "VDOT_O2_TRACE=1 requires VDOT_O2_ELASTIC=1")
    if (selected) {
      require(flag("VDOT_T14_FUSED_INPUT"),
        "VDOT_O2_ELASTIC=1 requires VDOT_T14_FUSED_INPUT=1")
      require(!flag("VDOT_O1_HANDOFF"),
        "VDOT_O2_ELASTIC cannot be combined with VDOT_O1_HANDOFF")
      require(!flag("VDOT_T12_TRACE") && !flag("VDOT_O1_TRACE"),
        "O2 cannot use the frozen T12 or single-outstanding O1 observer")
      // T13 retains its original global ROB/CSR stream. It can coexist only
      // with the separate O2 protocol which accounts for both elastic slots.
      require(!flag("VDOT_T13_TRACE") || flag("VDOT_O2_TRACE"),
        "O2 T13 tracing requires VDOT_O2_TRACE=1")
    }
    selected
  }

  def traceEnabled: Boolean = {
    val selected = flag("VDOT_O2_TRACE")
    if (selected) {
      require(enabled, "VDOT_O2_TRACE=1 requires elastic mode")
    }
    selected
  }
}
