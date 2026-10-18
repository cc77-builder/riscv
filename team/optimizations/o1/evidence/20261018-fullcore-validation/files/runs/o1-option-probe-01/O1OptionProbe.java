import xiangshan.backend.fu.wrapper.VDotHandoff;
class O1OptionProbe {
  public static void main(String[] args) {
    try {
      boolean trace = VDotHandoff.traceEnabled();
      boolean handoff = VDotHandoff.enabled();
      System.out.println("O1_OPTIONS_ALLOW handoff=" + (handoff ? 1 : 0) + " trace=" + (trace ? 1 : 0));
    } catch (IllegalArgumentException error) {
      System.out.println("O1_OPTIONS_REJECT " + error.getMessage());
      System.exit(10);
    }
  }
}
