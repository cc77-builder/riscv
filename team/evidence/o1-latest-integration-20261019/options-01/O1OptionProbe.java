import xiangshan.backend.fu.wrapper.VDotHandoff;
import xiangshan.backend.fu.wrapper.VDotO1Trace;
class O1OptionProbe {
  public static void main(String[] args) {
    try {
      boolean trace = VDotHandoff.traceEnabled();
      boolean frames = VDotO1Trace.enabled();
      boolean handoff = VDotHandoff.enabled();
      if (trace && frames) throw new IllegalArgumentException("both observers selected");
      System.out.println("O1_OPTIONS_ALLOW handoff=" + (handoff ? 1 : 0) + " trace=" + (trace ? 1 : 0) + " frames=" + (frames ? 1 : 0));
    } catch (IllegalArgumentException error) {
      System.out.println("O1_OPTIONS_REJECT " + error.getMessage());
      System.exit(10);
    }
  }
}
