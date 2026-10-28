module ClockGate(input TE, E, CK, output Q);
  CLKGATETST_X1 impl(.CK(CK), .E(E), .SE(TE), .GCK(Q));
endmodule
