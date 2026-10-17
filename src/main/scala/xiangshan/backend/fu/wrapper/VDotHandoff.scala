package xiangshan.backend.fu.wrapper

/** Experimental, elaboration-only O1 switch. No global cached environment value. */
object VDotHandoff {
  def enabled: Boolean = {
    val selected = sys.env.get("VDOT_O1_HANDOFF") match {
      case None | Some("0") => false
      case Some("1") => true
      case _ => throw new IllegalArgumentException("VDOT_O1_HANDOFF must be 0 or 1")
    }
    if (selected) {
      require(sys.env.get("VDOT_T14_FUSED_INPUT").contains("1"),
        "VDOT_O1_HANDOFF=1 requires VDOT_T14_FUSED_INPUT=1")
      // Old observers/mappers assume one request ends before the next accept.
      // Refuse ambiguous T12/T13 evidence until an O1-aware trace schema is validated.
      require(!sys.env.get("VDOT_T12_TRACE").contains("1") &&
        !sys.env.get("VDOT_T13_TRACE").contains("1"),
        "O1 handoff cannot use the frozen T12/T13 observer schema")
    }
    selected
  }
}
