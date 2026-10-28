fconfigure stdout -buffering line
read_liberty /home/riscv/riscv-lab/o4-cost-20261020/library/NangateOpenCellLibrary_typical.lib
set_cmd_units -time ns -capacitance fF
set_wire_load_mode top
set_wire_load_model -name 5K_hvratio_1_1
read_verilog /home/riscv/riscv-lab/o2-c1-owner-20261025/parent-sta-01/sta-canonical.v
link_design CommonParentCostTop
set inputs {}
foreach p [all_inputs] {if {[get_full_name $p] ne "clock"} {lappend inputs $p}}
set outputs [all_outputs]
create_clock -name core_clk -period 1.0 [get_ports clock]
set_clock_uncertainty 0.05 [get_clocks core_clk]
set_clock_transition 0.05 [get_clocks core_clk]
set_input_delay -max 0.1 -clock core_clk $inputs
set_output_delay -max 0.1 -clock core_clk $outputs
set_input_transition 0.05 $inputs
set_load 5 $outputs
puts "O4_CMD_UNITS time=ns capacitance=fF (explicit set_cmd_units accepted)"
puts "O4_CONSTRAINED_INPUT_BITS [llength $inputs]"
puts "O4_CONSTRAINED_OUTPUT_BITS [llength $outputs]"
puts "O4_REGISTER_CELLS [llength [all_registers -cells]]"
set_case_analysis 0 [get_ports testEnable]
report_clock_properties [get_clocks core_clk]
report_checks -to [get_pins {c202799/E}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-c2-attribution-20261025/fixed-sta-01/after/icg_all.rpt
report_checks -from [get_pins {c190553/Q}] -to [get_pins {c202799/E}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-c2-attribution-20261025/fixed-sta-01/after/icg_from_fpready.rpt
report_checks -from [get_pins {c192127/Q}] -to [get_pins {c202799/E}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-c2-attribution-20261025/fixed-sta-01/after/icg_from_busy.rpt
report_checks -from [get_pins {c192128/Q}] -to [get_pins {c202799/E}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-c2-attribution-20261025/fixed-sta-01/after/icg_from_hold_or_owner.rpt
report_checks -from [get_ports io_in_valid] -to [get_pins {c202799/E}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-c2-attribution-20261025/fixed-sta-01/after/icg_from_valid.rpt
report_checks -from [get_ports io_flush_valid] -to [get_pins {c202799/E}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-c2-attribution-20261025/fixed-sta-01/after/icg_from_flush.rpt
report_checks -from [get_ports reset] -to [get_pins {c202799/E}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-c2-attribution-20261025/fixed-sta-01/after/icg_from_reset.rpt
report_checks -from [get_pins {c198455/Q}] -to [get_pins {c197779/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-c2-attribution-20261025/fixed-sta-01/after/vdot_lane4.rpt
report_checks -from [get_pins {c198423/Q}] -to [get_pins {c197779/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-c2-attribution-20261025/fixed-sta-01/after/vdot_lane6.rpt
report_checks -from [get_ports io_out_ready] -to [get_ports io_in_ready] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-c2-attribution-20261025/fixed-sta-01/after/ready_fixed.rpt
puts "C2_READ_ONLY_STA_COMPLETE"
exit
