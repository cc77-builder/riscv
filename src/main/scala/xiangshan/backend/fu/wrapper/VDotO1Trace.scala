package xiangshan.backend.fu.wrapper

/** Simulation-only observer. It never controls ready, valid, data or clock gates. */
object VDotO1Trace {
  def enabled: Boolean = {
    val selected = sys.env.get("VDOT_O1_TRACE") match {
      case None | Some("0") => false
      case Some("1") => true
      case _ => throw new IllegalArgumentException("VDOT_O1_TRACE must be 0 or 1")
    }
    if (selected) {
      require(!sys.env.get("VDOT_T12_TRACE").contains("1") &&
        !sys.env.get("VDOT_T13_TRACE").contains("1"),
        "O1 trace cannot be mixed with the frozen T12/T13 observer schema")
    }
    selected
  }

  def mode: Int = if (VDotHandoff.enabled) 2 else {
    sys.env.get("VDOT_T14_FUSED_INPUT") match {
      case None | Some("0") => 0
      case Some("1") => 1
      case _ => throw new IllegalArgumentException("VDOT_T14_FUSED_INPUT must be 0 or 1")
    }
  }
}
