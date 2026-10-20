import xiangshan.backend.fu.wrapper.*;
public class O2OptionProbe { public static void main(String[] args) {
try {
 boolean o1=VDotHandoff.enabled(),o2=VDotO2.enabled(),e=VDotHandoff.traceEnabled(),f=VDotO1Trace.enabled(),t=VDotO2.traceEnabled();
 if ((e&&f)||(o2&&(e||f||o1))) throw new IllegalArgumentException("mixed mode or observers");
 System.out.println("ALLOW "+o1+" "+o2+" "+e+" "+f+" "+t);
} catch(IllegalArgumentException error) { System.out.println("REJECT "+error.getMessage());System.exit(10); }
}}