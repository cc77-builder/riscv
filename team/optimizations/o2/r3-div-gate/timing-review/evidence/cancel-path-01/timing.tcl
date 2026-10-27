fconfigure stdout -buffering line
read_liberty /home/riscv/riscv-lab/o4-cost-20261020/library/NangateOpenCellLibrary_typical.lib
set_cmd_units -time ns -capacitance fF
set_wire_load_mode top
set_wire_load_model -name 5K_hvratio_1_1
read_verilog /home/riscv/riscv-lab/o2-r3-div-gate-cost-20261025/parent-sta-01/sta-canonical.v
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
report_checks -from [get_pins {c197348/Q c197342/Q c197343/Q c197344/Q c197345/Q c197346/Q c197347/Q}] -to [get_pins {c197351/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/cancel-path-01/float_hold_rob.rpt
report_checks -from [get_pins {c197349/Q}] -to [get_pins {c197351/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/cancel-path-01/float_hold_divbusy.rpt
report_checks -from [get_ports {io_flush_bits_robIdx*}] -to [get_pins {c197351/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/cancel-path-01/float_hold_flush_index.rpt
report_checks -from [get_ports io_flush_bits_level] -to [get_pins {c197351/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/cancel-path-01/float_hold_flush_level.rpt
report_checks -from [get_pins {c197351/Q}] -to [get_pins {c197351/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/cancel-path-01/float_hold_self.rpt
report_checks -from [get_pins {c197348/Q c197342/Q c197343/Q c197344/Q c197345/Q c197346/Q c197347/Q}] -to [get_pins {c197350/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/cancel-path-01/int_hold_rob.rpt
report_checks -from [get_pins {c197349/Q}] -to [get_pins {c197350/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/cancel-path-01/int_hold_divbusy.rpt
report_checks -from [get_ports {io_flush_bits_robIdx*}] -to [get_pins {c197350/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/cancel-path-01/int_hold_flush_index.rpt
report_checks -from [get_ports io_flush_bits_level] -to [get_pins {c197350/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/cancel-path-01/int_hold_flush_level.rpt
report_checks -from [get_pins {c197350/Q}] -to [get_pins {c197350/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/cancel-path-01/int_hold_self.rpt
puts "R3_CANCEL_PROBE_COMPLETE"
exit
