package xiangshan.backend.fu.wrapper

/** Simulation-only observer. It never controls ready, valid, data or clock gates. */
object VDotO1Trace {
  private def selected: Boolean = {
    val selected = sys.env.get("VDOT_O1_TRACE") match {
      case None | Some("0") => false
      case Some("1") => true
      case _ => throw new IllegalArgumentException("VDOT_O1_TRACE must be 0 or 1")
    }
    require(Set("events", "frames").contains(profile),
      "VDOT_O1_TRACE_PROFILE must be events or frames")
    if (selected && profile == "frames") {
      require(!sys.env.get("VDOT_T12_TRACE").contains("1") &&
        !sys.env.get("VDOT_T13_TRACE").contains("1"),
        "O1 trace cannot be mixed with the frozen T12/T13 observer schema")
    }
    selected
  }

  private def profile: String = sys.env.getOrElse("VDOT_O1_TRACE_PROFILE", "events")

  // The latest upstream event schema is the default. Historical frame traces
  // remain available explicitly, never alongside the event protocol.
  def eventEnabled: Boolean = selected && profile == "events"
  def enabled: Boolean = selected && profile == "frames"

  def mode: Int = if (VDotHandoff.enabled) 2 else {
    sys.env.get("VDOT_T14_FUSED_INPUT") match {
      case None | Some("0") => 0
      case Some("1") => 1
      case _ => throw new IllegalArgumentException("VDOT_T14_FUSED_INPUT must be 0 or 1")
    }
  }
}
