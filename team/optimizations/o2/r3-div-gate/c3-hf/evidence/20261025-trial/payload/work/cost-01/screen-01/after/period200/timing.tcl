fconfigure stdout -buffering line
read_liberty /home/riscv/riscv-lab/o4-cost-20261020/library/NangateOpenCellLibrary_typical.lib
set_cmd_units -time ns -capacitance fF
set_wire_load_mode top
set_wire_load_model -name 5K_hvratio_1_1
read_verilog /home/riscv/riscv-lab/o2-c3-hf-20261025/cost-01/parent-sta-01/sta-canonical.v
link_design CommonParentCostTop
set inputs {}
foreach p [all_inputs] {if {[get_full_name $p] ne "clock"} {lappend inputs $p}}
set outputs [all_outputs]
create_clock -name core_clk -period 2.0 [get_ports clock]
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
report_checks -to [get_pins {c198090/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-c3-hf-20261025/cost-01/screen-01/after/period200/state0.rpt
report_checks -to [get_pins {c198098/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-c3-hf-20261025/cost-01/screen-01/after/period200/state1.rpt
report_checks -to [get_pins {c198097/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-c3-hf-20261025/cost-01/screen-01/after/period200/state2.rpt
report_checks -to [get_pins {c203764/E}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-c3-hf-20261025/cost-01/screen-01/after/period200/icg0.rpt
report_checks -to [get_pins {c203765/E}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-c3-hf-20261025/cost-01/screen-01/after/period200/icg1.rpt
report_checks -to [get_pins {c203766/E}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-c3-hf-20261025/cost-01/screen-01/after/period200/icg2.rpt
puts "C3_HF_CONTROL_STA_COMPLETE"
exit
